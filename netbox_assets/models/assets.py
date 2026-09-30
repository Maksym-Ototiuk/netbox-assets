from django.db import models
from django.forms import ValidationError

from netbox.models import PrimaryModel
from netbox.models.features import ImageAttachmentsMixin

from ..choices import AssetStatusChoices, HardwareKindChoices
from ..managers import AssetManager
from ..utils import (
    asset_clear_old_hw,
    asset_set_new_hw,
    get_plugin_setting,
    get_prechange_field,
    get_status_for,
)

__all__ = ('Asset',)


class Asset(PrimaryModel, ImageAttachmentsMixin):
    """
    An Asset represents a piece of hardware we want to keep track of. Its make
    (model) is one of: Device Type, Module Type or Rack Type.

    An asset can have a serial number and an asset tag (inventory number). It
    must have exactly one of DeviceType, ModuleType, RackType. It can have a
    storage location (instance of Location) where it is kept when not in use.

    An asset that is in use can be assigned to a Device, Module or Rack.
    """

    objects = AssetManager()

    #
    # fields that identify asset
    #
    name = models.CharField(
        help_text='Can be used to quickly identify a particular asset',
        max_length=128,
        blank=True,
        null=False,
        default='',
    )
    asset_tag = models.CharField(
        help_text='Identifier assigned by owner',
        max_length=50,
        blank=True,
        null=True,
        default=None,
        verbose_name='Asset Tag',
    )
    serial = models.CharField(
        help_text='Identifier assigned by manufacturer',
        max_length=60,
        verbose_name='Serial Number',
        blank=True,
        null=True,
        default=None,
    )

    #
    # status fields
    #
    status = models.CharField(
        max_length=30,
        choices=AssetStatusChoices,
        help_text='Asset lifecycle status',
    )

    #
    # Asset role fields
    #
    role = models.ForeignKey(
        to='netbox_assets.AssetRole',
        on_delete=models.SET_NULL,
        related_name='assets',
        blank=True,
        null=True,
        verbose_name='Role',
        help_text='Functional role of this asset',
    )

    #
    # hardware type fields
    #
    device_type = models.ForeignKey(
        to='dcim.DeviceType',
        on_delete=models.PROTECT,
        related_name='assets',
        blank=True,
        null=True,
        verbose_name='Device Type',
    )
    module_type = models.ForeignKey(
        to='dcim.ModuleType',
        on_delete=models.PROTECT,
        related_name='assets',
        blank=True,
        null=True,
        verbose_name='Module Type',
    )
    rack_type = models.ForeignKey(
        to='dcim.RackType',
        on_delete=models.PROTECT,
        related_name='assets',
        blank=True,
        null=True,
        verbose_name='Rack Type',
    )

    #
    # used fields
    #
    device = models.OneToOneField(
        to='dcim.Device',
        on_delete=models.SET_NULL,
        related_name='assigned_asset',
        blank=True,
        null=True,
    )
    module = models.OneToOneField(
        to='dcim.Module',
        on_delete=models.SET_NULL,
        related_name='assigned_asset',
        blank=True,
        null=True,
    )
    rack = models.OneToOneField(
        to='dcim.Rack',
        on_delete=models.SET_NULL,
        related_name='assigned_asset',
        blank=True,
        null=True,
    )
    tenant = models.ForeignKey(
        help_text='Tenant using this asset',
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
    )
    contact = models.ForeignKey(
        help_text='Contact using this asset',
        to='tenancy.Contact',
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
    )

    storage_location = models.ForeignKey(
        help_text='Where is this asset stored when not in use',
        to='dcim.Location',
        on_delete=models.PROTECT,
        related_name='assets',
        blank=True,
        null=True,
        verbose_name='Storage Location',
    )

    #
    # ownership
    #
    owning_tenant = models.ForeignKey(
        help_text='Who owns this asset',
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
    )

    clone_fields = [
        'name',
        'asset_tag',
        'status',
        'role',
        'device_type',
        'module_type',
        'rack_type',
        'owning_tenant',
        'tenant',
        'contact',
        'storage_location',
        'comments',
    ]

    @property
    def kind(self):
        if self.device_type_id:
            return 'device'
        elif self.module_type_id:
            return 'module'
        elif self.rack_type_id:
            return 'rack'
        assert False, f'Invalid hardware kind detected for asset {self.pk}'

    def get_kind_display(self):
        return dict(HardwareKindChoices)[self.kind]

    @property
    def hardware_type(self):
        return self.device_type or self.module_type or self.rack_type or None

    @property
    def hardware(self):
        return self.device or self.module or self.rack or None

    @property
    def storage_site(self):
        if self.storage_location:
            return self.storage_location.site

    @property
    def installed_site(self):
        device = self.installed_device
        if device:
            return device.site
        if self.rack:
            return self.rack.site

    @property
    def installed_location(self):
        device = self.installed_device
        if device:
            return device.location
        if self.rack:
            return self.rack.location

    @property
    def installed_rack(self):
        device = self.installed_device
        if device:
            return device.rack
        if self.rack:
            return self.rack

    @property
    def installed_device(self):
        if self.kind == 'rack':
            return None
        elif self.kind == 'device':
            return self.device
        elif self.hardware:
            return self.hardware.device
        else:
            return None

    @property
    def current_site(self):
        installed = self.installed_site
        if installed:
            return installed
        return self.storage_site

    @property
    def current_location(self):
        installed = self.installed_location
        # we can have an installed site but no installed location
        # so return None in that case
        if installed or self.installed_site:
            return installed
        return self.storage_location

    def clean(self):
        self.validate_hardware_types()
        self.validate_hardware()
        self.update_status()
        return super().clean()

    def save(self, clear_old_hw=True, *args, **kwargs):
        self.update_hardware_used(clear_old_hw)
        return super().save(*args, **kwargs)

    def validate_hardware_types(self):
        """
        Ensure exactly one of device_type/module_type/rack_type is set.
        """
        hardware_types = [self.device_type, self.module_type, self.rack_type]
        if sum(map(bool, hardware_types)) > 1:
            raise ValidationError(
                'Only one of device type, module type and rack type can be set for the same asset.'
            )
        if not any(hardware_types):
            raise ValidationError(
                'One of device type, module type or rack type must be set.'
            )

    def validate_hardware(self):
        """
        Ensure only one device/module/rack is set at a time and it matches
        device/module/rack type.
        """
        kind = self.kind
        _type = getattr(self, kind + '_type')
        hw = getattr(self, kind)
        hw_others = dict(HardwareKindChoices).keys() - [kind]

        # e.g.: self.device_type and self.device.device_type must match
        # but don't check if we are reassigning asset to another device
        if not getattr(self, '_in_reassign', False):
            if hw and _type != getattr(hw, kind + '_type'):
                raise ValidationError(
                    {kind: f'{kind} type of {kind} does not match {kind} type of asset'}
                )
        # ensure only one hardware is set and that it is correct kind
        # e.g. if self.device_type is set, we cannot have self.module or self.rack set
        for hw_other in hw_others:
            if getattr(self, hw_other):
                raise ValidationError(
                    f'Cannot set {hw_other} for asset that is a {kind}'
                )

    def update_status(self):
        """
        If asset was assigned or unassigned to a particular device, module or rack
        update asset.status. Depending on plugin configuration.
        """
        old_hw = get_prechange_field(self, self.kind)
        new_hw = getattr(self, self.kind)
        old_status = get_prechange_field(self, 'status')
        stored_status = get_status_for('stored')
        used_status = get_status_for('used')
        if old_status != self.status:
            # status has also been changed manually, don't change it automatically
            return
        if used_status and new_hw and not old_hw:
            self.status = used_status
        elif stored_status and not new_hw and old_hw:
            self.status = stored_status

    def update_hardware_used(self, clear_old_hw=True):
        """
        If assigning as device, module or rack set serial and asset_tag on it.
        Also remove them if unassigning.
        """
        if not get_plugin_setting('sync_hardware_serial_asset_tag'):
            return None
        old_hw = get_prechange_field(self, self.kind)
        new_hw = getattr(self, self.kind)
        if old_hw:
            old_hw.snapshot()
        if new_hw:
            new_hw.snapshot()
        old_serial = get_prechange_field(self, 'serial')
        old_asset_tag = get_prechange_field(self, 'asset_tag')
        if not new_hw and old_hw and clear_old_hw:
            # unassigned existing asset, nothing assigned now
            asset_clear_old_hw(old_hw)
        elif new_hw and old_hw != new_hw:
            # assigned something new
            if old_hw and clear_old_hw:
                # but first clear previous hw data
                asset_clear_old_hw(old_hw)
            asset_set_new_hw(asset=self, hw=new_hw)
        elif self.serial != old_serial or self.asset_tag != old_asset_tag:
            # just changed asset's serial or asset_tag, update assigned hw
            if new_hw:
                asset_set_new_hw(asset=self, hw=new_hw)

    def get_status_color(self):
        return AssetStatusChoices.colors.get(self.status)

    def __str__(self):
        if self.serial:
            return f'{self.hardware_type} {self.serial}'
        else:
            return f'{self.hardware_type} (id:{self.id})'

    class Meta:
        ordering = (
            'device_type',
            'module_type',
            'rack_type',
            'serial',
        )
        constraints = (
            models.UniqueConstraint(
                fields=('device_type', 'serial'),
                name='%(app_label)s_%(class)s_device_type_serial',
            ),
            models.UniqueConstraint(
                fields=('module_type', 'serial'),
                name='%(app_label)s_%(class)s_module_type_serial',
            ),
            models.UniqueConstraint(
                fields=('rack_type', 'serial'),
                name='%(app_label)s_%(class)s_rack_type_serial',
            ),
            models.UniqueConstraint(
                fields=('owning_tenant', 'asset_tag'),
                name='%(app_label)s_%(class)s_owning_tenant_asset_tag',
            ),
            models.UniqueConstraint(
                'asset_tag',
                condition=models.Q(owning_tenant__isnull=True),
                name='%(app_label)s_%(class)s_asset_tag',
                violation_error_message='Asset with this Asset Tag and no Owning Tenant already exists.',
            ),
        )
