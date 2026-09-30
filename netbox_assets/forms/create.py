import logging

from dcim.forms import DeviceForm, ModuleForm, RackForm
from dcim.models import Device
from utilities.forms.fields import DynamicModelChoiceField

__all__ = (
    'AssetDeviceCreateForm',
    'AssetModuleCreateForm',
    'AssetRackCreateForm',
)

logger = logging.getLogger('netbox.netbox_assets.forms.create')


class AssetCreateMixin:
    def update_hardware_fields(self, kind_type):
        """
        Pre-populate and disable hardware related fields from asset data
        """
        if self.instance.assigned_asset:
            asset = self.instance.assigned_asset
            self.fields['serial'].disabled = True
            self.fields['asset_tag'].disabled = True
            self.fields[kind_type].disabled = True
            self.initial['serial'] = asset.serial
            self.initial['asset_tag'] = asset.asset_tag if asset.asset_tag else None
            self.initial[kind_type] = asset.hardware_type.id

    def save(self, *args):
        """
        After we save new hardware (Device, Module, Rack), we must update
        asset.device/.module/.rack to refer to this new hardware instance
        """
        asset = self.instance.assigned_asset
        instance = super().save(*args)
        asset.snapshot()
        setattr(asset, asset.kind, instance)
        asset.full_clean()
        asset.save()
        logger.info(f'Assigned newly created hardware ({instance}) to asset {asset}')
        return instance


class AssetDeviceCreateForm(AssetCreateMixin, DeviceForm):
    """
    Populates and disables editing of asset and devcie_type fields
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_hardware_fields('device_type')

    def clean_device_type(self):
        # no mattter what was POSTed, device_type cannot be changed/missing...
        return self.instance.assigned_asset.device_type


class AssetModuleCreateForm(AssetCreateMixin, ModuleForm):
    """
    Populates and disables editing of asset and module_type fields
    """

    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        selector=True,
        initial_params={'modulebays': '$module_bay'},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_hardware_fields('module_type')

    def clean_module_type(self):
        return self.instance.assigned_asset.module_type


class AssetRackCreateForm(AssetCreateMixin, RackForm):
    """
    Populates and disables editing of asset and rack_type fields
    """

    def __init__(self, *args, **kwargs):
        # Set rack_type on the new rack before RackForm.__init__() runs. RackForm
        # then hides the fields that are defined by the rack type, the same way
        # as when a user selects a rack type in NetBox.
        instance = kwargs.get('instance')
        if instance is not None and getattr(instance, 'assigned_asset', None):
            instance.rack_type = instance.assigned_asset.rack_type
        super().__init__(*args, **kwargs)
        self.update_hardware_fields('rack_type')

    def clean_rack_type(self):
        # no matter what was POSTed, rack_type cannot be changed/missing...
        return self.instance.assigned_asset.rack_type
