import logging

from django.db.models import QuerySet
from django.db.models.signals import post_delete, pre_delete, pre_save
from django.dispatch import receiver

from dcim.models import Device, Module, ModuleType, ModuleTypeProfile, Rack
from utilities.exceptions import AbortRequest

from .assembly import (
    AssemblySpec,
    get_module_type_side,
    is_assembly_module_type,
    is_assembly_schema,
    validate_assembly_schema,
)
from .models import Asset, AssetModuleEnd
from .utils import get_plugin_setting, get_status_for, is_equal_none

logger = logging.getLogger('netbox.netbox_assets.signals')


@receiver(pre_save, sender=Device)
@receiver(pre_save, sender=Module)
@receiver(pre_save, sender=Rack)
def prevent_update_serial_asset_tag(instance, **kwargs):
    """
    When a hardware (Device, Module, Rack) has an Asset assigned and
    user changes serial or asset_tag on hardware, prevent that change
    and inform that change must be made on Asset instance instead.
    The same applies to a Module that is an end of a cable assembly: it has
    the serial of the assembly, and the primary end also its asset tag.

    Only enforces if `sync_hardware_serial_asset_tag` setting is true.
    """
    try:
        # will raise RelatedObjectDoesNotExist if not set
        asset = instance.assigned_asset
        asset_tag = asset.asset_tag
        what = asset.kind
    except Asset.DoesNotExist:
        if not isinstance(instance, Module):
            return
        try:
            end = instance.assembly_end
        except AssetModuleEnd.DoesNotExist:
            return
        asset = end.asset
        asset_tag = asset.asset_tag if end.is_primary else None
        what = 'cable assembly end'
    if not get_plugin_setting('sync_hardware_serial_asset_tag'):
        # don't enforce if sync not enabled
        return
    if instance.pk and (
        not is_equal_none(asset.serial, instance.serial)
        or not is_equal_none(asset_tag, instance.asset_tag)
    ):
        raise AbortRequest(
            f'Cannot change {what} serial and asset tag if asset is assigned. Please update via Assets > Asset instead.'
        )


@receiver(pre_delete, sender=Device)
@receiver(pre_delete, sender=Module)
@receiver(pre_delete, sender=Rack)
def free_assigned_asset(instance, **kwargs):
    """
    If a hardware (Device, Module, Rack) has an Asset assigned and
    that hardware is deleted, update Asset.status to stored_status.

    Netbox handles deletion in a DB transaction, so if deletion failes for any
    reason, this status change will also be reverted.
    """
    stored_status = get_status_for('stored')
    if not stored_status:
        return
    try:
        # will raise RelatedObjectDoesNotExist if not set
        asset = instance.assigned_asset
    except Asset.DoesNotExist:
        return
    asset.snapshot()
    asset.status = stored_status
    # also unassign that item from asset
    setattr(asset, asset.kind, None)
    asset.full_clean()
    asset.save(clear_old_hw=False)
    logger.info(f'Asset marked as stored {asset}')


#
# Cable assemblies
#


def _deleted_with(origin, model):
    """Was the deletion started on an instance or a queryset of model?"""
    if isinstance(origin, QuerySet):
        return issubclass(origin.model, model)
    return isinstance(origin, model)


@receiver(post_delete, sender=AssetModuleEnd)
def assembly_end_removed(instance, origin=None, **kwargs):
    """
    An end of a cable assembly was removed, either directly (uninstalled) or
    because its module (or the device of the module) was deleted.

    - uninstalled: clear serial and asset tag of the module (if synced);
    - module deleted: nothing to clear, the module is deleted as well;
    - asset deleted: nothing to do, the values stay on the modules.

    Then a new primary end is chosen and the status is updated (see
    Asset.update_assembly_after_end_removed()).
    """
    if _deleted_with(origin, Asset):
        return
    asset = Asset.objects.select_for_update().filter(pk=instance.asset_id).first()
    if asset is None:
        return
    if origin is None or _deleted_with(origin, AssetModuleEnd):
        module = Module.objects.filter(pk=instance.module_id).first()
        if module is not None:
            asset.clear_assembly_end_module(module)
    elif get_plugin_setting('sync_hardware_serial_asset_tag'):
        # The module is being deleted, but its row is deleted only after this
        # end. Release its asset tag now, so that it can be set on the module
        # of the new primary end (asset tags of modules are unique).
        Module.objects.filter(pk=instance.module_id).update(asset_tag=None)
    asset.update_assembly_after_end_removed()
    logger.info(f'Cable assembly end removed: {instance}')


@receiver(pre_save, sender=Module)
def protect_assembly_end_module_type(instance, **kwargs):
    """
    The module type of a module that is an end of a cable assembly cannot be
    changed.
    """
    if not instance.pk:
        return
    end = AssetModuleEnd.objects.filter(module_id=instance.pk).first()
    if end is None:
        return
    old_module_type_id = (
        Module.objects.filter(pk=instance.pk)
        .values_list('module_type_id', flat=True)
        .first()
    )
    if old_module_type_id is not None and old_module_type_id != instance.module_type_id:
        raise AbortRequest(
            f'Cannot change the module type of module {instance}: it is end '
            f'{end.label} of cable assembly {end.asset}. Uninstall the end first.'
        )


@receiver(pre_save, sender=ModuleType)
def protect_assembly_module_type(instance, **kwargs):
    """
    The profile and the assembly side of a module type that is used by cable
    assemblies cannot be changed. A cable assembly profile cannot be set on a
    module type whose assets are assigned to modules directly.
    """
    if not instance.pk:
        return
    old = ModuleType.objects.filter(pk=instance.pk).select_related('profile').first()
    if old is None:
        return
    was_assembly = is_assembly_module_type(old)
    if not was_assembly:
        if (
            is_assembly_module_type(instance)
            and Asset.objects.filter(
                module_type=instance, module__isnull=False
            ).exists()
        ):
            raise AbortRequest(
                f'Cannot set cable assembly profile {instance.profile} on module type '
                f'{instance}: assets of this module type are assigned to modules. '
                f'Unassign them first.'
            )
        return
    if old.profile_id == instance.profile_id and get_module_type_side(
        old
    ) == get_module_type_side(instance):
        return
    if (
        Asset.objects.filter(module_type=instance).exists()
        or AssetModuleEnd.objects.filter(module__module_type=instance).exists()
    ):
        raise AbortRequest(
            f'Cannot change the profile or the assembly side of module type '
            f'{instance}: it is used by cable assemblies.'
        )


@receiver(pre_save, sender=ModuleTypeProfile)
def protect_assembly_profile(instance, **kwargs):
    """
    Validate cable assembly profiles. Changes of a profile that is used by cable
    assemblies must keep all installed ends.
    """
    errors = validate_assembly_schema(instance.schema)
    if errors:
        raise AbortRequest(
            f'Invalid cable assembly profile {instance}: {" ".join(errors)}'
        )
    if not instance.pk:
        return
    old_schema = (
        ModuleTypeProfile.objects.filter(pk=instance.pk)
        .values_list('schema', flat=True)
        .first()
    )
    if not is_assembly_schema(old_schema):
        return
    if not is_assembly_schema(instance.schema):
        if Asset.objects.filter(module_type__profile=instance).exists():
            raise AbortRequest(
                f'Profile {instance} is used by cable assemblies, its properties '
                f'"side", "a_ends" and "b_ends" cannot be removed.'
            )
        return
    labels = set(AssemblySpec.from_schema(instance.schema).labels)
    installed = set(
        AssetModuleEnd.objects.filter(asset__module_type__profile=instance).values_list(
            'label', flat=True
        )
    )
    if missing := installed - labels:
        raise AbortRequest(
            f'Cannot change profile {instance}: installed ends '
            f'{", ".join(sorted(missing))} would not exist any more. Uninstall '
            f'them first.'
        )
