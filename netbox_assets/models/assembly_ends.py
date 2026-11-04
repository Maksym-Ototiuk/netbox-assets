from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models, router, transaction

from dcim.models import Module
from netbox.models import NetBoxModel

from ..assembly import (
    END_LABEL_MAX_LENGTH,
    SIDE_A,
    SIDE_BOTH,
    get_module_type_side,
)

__all__ = ('AssetModuleEnd',)

PRIMARY_CONSTRAINT = 'netbox_assets_assetmoduleend_asset_primary'


class AssetModuleEnd(NetBoxModel):
    """
    An installed end of a cable assembly (DAC, AOC, breakout cable).

    A cable assembly is one Asset whose ends are separate NetBox modules. The
    ends (slots) are defined by the assembly profile of the asset's module
    type. An AssetModuleEnd links one slot (`label`) to the module that
    represents this end in NetBox.
    """

    asset = models.ForeignKey(
        to='netbox_assets.Asset',
        on_delete=models.CASCADE,
        related_name='ends',
        verbose_name='Asset',
    )
    module = models.OneToOneField(
        to='dcim.Module',
        on_delete=models.CASCADE,
        related_name='assembly_end',
        verbose_name='Module',
    )
    label = models.CharField(
        max_length=END_LABEL_MAX_LENGTH,
        blank=True,
        verbose_name='End',
        help_text='End of the cable assembly as defined by its profile. '
        'Leave empty to use the first free end that matches the module type.',
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name='Primary',
        help_text='The cable assembly is shown where its primary end is installed. '
        'If serial and asset tag sync is enabled, the asset tag is written to the '
        'module of the primary end only.',
    )

    clone_fields = ('asset',)

    class Meta:
        ordering = ('asset', 'label')
        constraints = (
            models.UniqueConstraint(
                fields=('asset', 'label'),
                name='%(app_label)s_%(class)s_asset_label',
                violation_error_message='This end of the cable assembly is already installed.',
            ),
            models.UniqueConstraint(
                fields=('asset',),
                condition=models.Q(is_primary=True),
                name='%(app_label)s_%(class)s_asset_primary',
                violation_error_message='A cable assembly can have only one primary end.',
            ),
        )
        verbose_name = 'assembly end'
        verbose_name_plural = 'assembly ends'

    def __str__(self):
        asset = self._get_asset()
        return f'{asset}: {self.label}' if asset else self.label

    def _get_asset(self):
        # the asset can be missing if the user is not allowed to view it
        # (e.g. in GraphQL, where related objects are restricted)
        try:
            return self.asset
        except ObjectDoesNotExist:
            return None

    @property
    def slot(self):
        asset = self._get_asset()
        spec = asset.assembly_spec if asset else None
        return spec.get_slot(self.label) if spec else None

    @property
    def side(self):
        slot = self.slot
        return slot.side if slot else None

    def _get_module(self):
        # the module may be a new, unsaved Module (created by the install form)
        try:
            return self.module
        except Module.DoesNotExist:
            return None

    def get_constraints(self):
        # The primary flag is moved from the previous primary end in save(),
        # so the "one primary end" constraint is not validated here
        return [
            (model, [c for c in constraints if c.name != PRIMARY_CONSTRAINT])
            for model, constraints in super().get_constraints()
        ]

    def clean(self):
        super().clean()
        if not self.asset_id:
            return
        asset = self.asset
        spec = asset.assembly_spec
        if spec is None:
            raise ValidationError(
                {
                    'asset': f'{asset} is not a cable assembly: its module type '
                    f'must have a valid cable assembly profile.'
                }
            )
        module = self._get_module()
        if not self.label and module is not None:
            self.label = self.get_free_label(asset, spec, module) or ''
            if not self.label:
                raise ValidationError(
                    f'All ends of {asset} that match module type '
                    f'{module.module_type} are already installed.'
                )
        slot = spec.get_slot(self.label)
        if slot is None:
            raise ValidationError(
                {
                    'label': f'Unknown end "{self.label}". Ends of {asset}: '
                    f'{", ".join(spec.labels)}.'
                }
            )
        if module is not None:
            self.validate_module(asset, slot, module)
        if not self._state.adding and not self.is_primary:
            if AssetModuleEnd.objects.filter(
                pk=self.pk, asset_id=self.asset_id, is_primary=True
            ).exists():
                raise ValidationError(
                    {'is_primary': 'Mark another end as primary instead.'}
                )

    def validate_module(self, asset, slot, module):
        """
        Side A ends (and both ends of a symmetric assembly) must be modules of
        the asset's module type. Side B ends must be modules of a side B
        module type with the same profile and manufacturer.
        """
        module_type = module.module_type
        symmetric = get_module_type_side(asset.module_type) == SIDE_BOTH
        if slot.side == SIDE_A or symmetric:
            if module_type.pk != asset.module_type_id:
                raise ValidationError(
                    f'End {slot.label} of {asset} must be a module of type '
                    f'{asset.module_type}, not {module_type}.'
                    f'{self._installed_module_hint(module)}'
                )
        elif not asset.is_side_b_module_type(module_type):
            raise ValidationError(self._side_b_module_type_error(asset, slot, module))
        if module.pk:
            from .assets import Asset

            assigned = Asset.objects.filter(module=module).first()
            if assigned is not None:
                raise ValidationError(
                    f'Module {module} is already assigned to asset {assigned}.'
                )
        self.validate_module_interface(asset, module)

    @staticmethod
    def _installed_module_hint(module):
        # an existing module: the module bay is not empty
        if not module.pk:
            return ''
        return (
            f' Module bay {module.module_bay} already has a module of type '
            f'{module.module_type}: use an empty module bay or a module of the '
            f'right type.'
        )

    def _side_b_module_type_error(self, asset, slot, module):
        """Error for a side B end whose module has a wrong module type."""
        module_type = module.module_type
        profile = asset.module_type.profile
        manufacturer = asset.module_type.manufacturer
        message = (
            f'End {slot.label} of {asset} must be a module of a side B module '
            f'type with profile {profile} and manufacturer {manufacturer}, not '
            f'{module_type} (profile {module_type.profile or "none"}, side '
            f'{get_module_type_side(module_type) or "none"}, manufacturer '
            f'{module_type.manufacturer}).'
        )
        matching = [str(m) for m in asset.get_side_b_module_types()]
        if matching:
            message += f' Side B module types: {", ".join(matching)}.'
        else:
            message += (
                ' There is no such module type: create one with this profile '
                'and manufacturer and the attribute side B.'
            )
        return message + self._installed_module_hint(module)

    def validate_module_interface(self, asset, module):
        """
        The cable of the assembly is connected to the only interface of the end
        module that is not a channel subinterface, so there must be exactly one
        such interface, and it must not have a cable of something else.
        """
        from ..cables import count_end_interfaces, get_end_interface

        if count_end_interfaces(module) != 1:
            raise ValidationError(
                f'Module type {module.module_type} must have exactly one interface '
                f'(not counting channel subinterfaces) to connect the cable of the '
                f'assembly.'
            )
        interface = get_end_interface(module) if module.pk else None
        if interface is None or interface.cable_id is None:
            return
        # the assembly's own cable (or the cable of the assembly the end is
        # moved from) is fine
        own_cables = {asset.assembly_cable_id}
        if not self._state.adding:
            own_cables |= set(
                AssetModuleEnd.objects.filter(pk=self.pk).values_list(
                    'asset__assembly_cable', flat=True
                )
            )
        if interface.cable_id not in own_cables:
            raise ValidationError(
                f'Interface {interface} of module {module} already has cable '
                f'{interface.cable}. Delete the cable first.'
            )

    def get_free_label(self, asset, spec, module):
        """First free end that matches the module type of the module."""
        used = set(asset.ends.exclude(pk=self.pk).values_list('label', flat=True))
        if get_module_type_side(asset.module_type) == SIDE_BOTH:
            sides = None
        elif module.module_type_id == asset.module_type_id:
            sides = (SIDE_A,)
        else:
            sides = (get_module_type_side(module.module_type),)
        for slot in spec.slots:
            if slot.label not in used and (sides is None or slot.side in sides):
                return slot.label
        return None

    def get_default_primary(self, asset):
        """
        A new end becomes the primary end if the assembly has no primary end
        yet, or if it is the end in the first side A slot.
        """
        if not asset.ends.filter(is_primary=True).exists():
            return True
        spec = asset.assembly_spec
        return bool(spec and spec.slots) and spec.slots[0].label == self.label

    def save(self, *args, **kwargs):
        from .assets import Asset

        with transaction.atomic(using=router.db_for_write(AssetModuleEnd)):
            previous = None
            if not self._state.adding:
                previous = (
                    AssetModuleEnd.objects.filter(pk=self.pk)
                    .select_related('module')
                    .first()
                )
            # an end can be moved to another cable assembly
            moved = previous is not None and previous.asset_id != self.asset_id
            # serialize concurrent changes of the same cable assemblies
            asset_ids = {self.asset_id, previous.asset_id if moved else self.asset_id}
            assets = {
                asset.pk: asset
                for asset in Asset.objects.select_for_update(of=('self',))
                .filter(pk__in=asset_ids)
                .order_by('pk')
            }
            asset = assets[self.asset_id]
            added = self._state.adding or moved
            installed = asset.ends.exclude(pk=self.pk).count()

            if added and not self.is_primary:
                self.is_primary = self.get_default_primary(asset)
            if self.is_primary:
                # unset the old primary end first, this also clears the asset
                # tag of its module (asset tags of modules are unique)
                for other in asset.ends.filter(is_primary=True).exclude(pk=self.pk):
                    other.snapshot()
                    other.is_primary = False
                    other.skip_cable_sync = True
                    other.save()

            super().save(*args, **kwargs)

            if previous and previous.module_id != self.module_id:
                asset.clear_assembly_end_module(previous.module)
            asset.sync_assembly_end(self)
            if moved:
                assets[previous.asset_id].update_assembly_after_end_removed()
            if added and installed == 0:
                asset.set_assembly_status('used')

            if not getattr(self, 'skip_cable_sync', False):
                if moved:
                    # release the interface from the old assembly's cable first
                    assets[previous.asset_id].sync_assembly_cable()
                asset.sync_assembly_cable()
