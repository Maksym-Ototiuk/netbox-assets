"""
The NetBox cable of a cable assembly.

When ends on both sides of a cable assembly are installed, the plugin connects
the interfaces of the end modules with one NetBox cable (Asset.assembly_cable):

- side A terminations are the interfaces of the side A ends, side B
  terminations the interfaces of the side B ends, both in the order of the
  slots (NetBox derives the cable connector from this order);
- type and length come from the module type attributes `cable_type` (the
  label or the value of a NetBox cable type) and `length` (meters);
- the cable profile is the profile of the assembly (e.g. 1C4P:4C1P breakout),
  but only if the installed ends of each side are the first slots of the side
  without a gap. With a gap (e.g. B1 and B3 installed) NetBox would map B3 to
  connector 2, so the cable has no profile until the gap is closed.

The cable is created, changed or deleted by sync_assembly_cable() whenever ends
are installed or removed. Other changes of its type, profile, length and
terminations, and its deletion, are rejected by signals (see signals.py), except
inside assembly_cable_sync().
"""

from contextlib import contextmanager
from contextvars import ContextVar
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError

from dcim.choices import CableLengthUnitChoices, LinkStatusChoices
from dcim.models import Cable
from netbox.context import current_request

from .assembly import SIDE_A, SIDE_B, get_cable_type
from .utils import abort_request

__all__ = (
    'CABLE_LOCKED_FIELDS',
    'assembly_cable_sync',
    'count_end_interfaces',
    'get_cable_values',
    'get_end_interface',
    'in_assembly_cable_sync',
    'sync_assembly_cable',
)

# fields of an assembly cable that only the plugin may change
CABLE_LOCKED_FIELDS = ('type', 'profile', 'length', 'length_unit')

_cable_sync = ContextVar('netbox_assets_assembly_cable_sync', default=False)


@contextmanager
def assembly_cable_sync():
    """Changes of assembly cables made by the plugin itself."""
    token = _cable_sync.set(True)
    try:
        yield
    finally:
        _cable_sync.reset(token)


def in_assembly_cable_sync():
    return _cable_sync.get()


def get_end_interface(module):
    """
    The interface of an end module that the cable is connected to: its only
    interface that is not a channel subinterface (for a channelized breakout
    end, the channelized parent interface). None if there is not exactly one.
    """
    interfaces = [i for i in module.interfaces.all() if i.channel_id is None]
    return interfaces[0] if len(interfaces) == 1 else None


def count_end_interfaces(module):
    """
    Number of interfaces of a module (or of a new, unsaved module, the
    interface templates of its module type) that are not channel subinterfaces.
    """
    if module.pk:
        return module.interfaces.filter(channel_id__isnull=True).count()
    return module.module_type.interfacetemplates.filter(channel_id__isnull=True).count()


def get_cable_values(asset):
    """Type and length of the cable, from the attributes of the module type."""
    data = asset.module_type.attribute_data or {}
    cable_type = get_cable_type(data.get('cable_type'))
    length = data.get('length')
    try:
        length = Decimal(str(length)).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        length = None
    if length is not None and length < 0:
        length = None
    return {
        'type': cable_type,
        'length': length,
        'length_unit': CableLengthUnitChoices.UNIT_METER
        if length is not None
        else None,
    }


def _check_permission(action, asset, check_permissions):
    request = current_request.get()
    if (
        not check_permissions
        or request is None
        or request.user.has_perm(f'dcim.{action}_cable')
    ):
        return
    raise abort_request(
        f'You are not allowed to {action} cables. Installing and uninstalling '
        f'the ends of cable assembly {asset} changes its cable.'
    )


def _save_cable(cable, asset):
    try:
        cable.full_clean()
    except ValidationError as e:
        raise abort_request(
            f'Cannot save the cable of cable assembly {asset}: {" ".join(e.messages)}'
        )
    with assembly_cable_sync():
        cable.save()


def _get_terminations(asset, spec, side):
    """
    Interfaces of the installed ends of one side in slot order, and whether the
    installed ends are the first slots of the side (no gap).
    """
    labels = spec.side_labels(side)
    ends = {
        end.label: end
        for end in asset.ends.filter(label__in=labels)
        .select_related('module')
        .prefetch_related('module__interfaces')
    }
    interfaces = []
    installed = []
    for index, label in enumerate(labels):
        end = ends.get(label)
        interface = get_end_interface(end.module) if end else None
        if interface is not None:
            interfaces.append(interface)
            installed.append(index)
    return interfaces, installed == list(range(len(installed)))


def sync_assembly_cable(asset, check_permissions=True):
    """
    Create, change or delete the cable of a cable assembly. The user needs the
    permission to add, change or delete cables, unless check_permissions is
    False (the cable is updated because a module or device was deleted).
    """
    spec = asset.assembly_spec
    if spec is None:
        return
    cable = None
    if asset.assembly_cable_id:
        cable = Cable.objects.filter(pk=asset.assembly_cable_id).first()
    a_terminations, a_complete = _get_terminations(asset, spec, SIDE_A)
    b_terminations, b_complete = _get_terminations(asset, spec, SIDE_B)

    if not a_terminations or not b_terminations:
        # a cable needs ends on both sides
        if cable is not None:
            _check_permission('delete', asset, check_permissions)
            with assembly_cable_sync():
                cable.delete()
        asset.assembly_cable = None
        return

    values = get_cable_values(asset)
    values['profile'] = spec.cable_profile if a_complete and b_complete else ''

    if cable is None:
        _check_permission('add', asset, check_permissions)
        cable = Cable(
            a_terminations=a_terminations,
            b_terminations=b_terminations,
            status=LinkStatusChoices.STATUS_CONNECTED,
            label=asset.asset_tag or asset.name or '',
            **values,
        )
        _save_cable(cable, asset)
        type(asset).objects.filter(pk=asset.pk).update(assembly_cable=cable)
        asset.assembly_cable = cable
        return

    current_a, current_b = cable.get_terminations()
    terminations_changed = [t.pk for t in current_a] != [
        t.pk for t in a_terminations
    ] or [t.pk for t in current_b] != [t.pk for t in b_terminations]
    values_changed = any(
        getattr(cable, name) != value for name, value in values.items()
    )
    if not terminations_changed and not values_changed:
        return
    _check_permission('change', asset, check_permissions)
    cable.snapshot()
    for name, value in values.items():
        setattr(cable, name, value)
    if terminations_changed:
        cable.a_terminations = a_terminations
        cable.b_terminations = b_terminations
    _save_cable(cable, asset)
