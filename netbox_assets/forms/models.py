from django import forms
from django.core.exceptions import ValidationError

from dcim.models import (
    Device,
    DeviceType,
    Location,
    Manufacturer,
    Module,
    ModuleBay,
    ModuleType,
    RackType,
    Site,
)
from netbox.context import current_request
from netbox.forms import NestedGroupModelForm, NetBoxModelForm, PrimaryModelForm
from tenancy.models import Contact, ContactGroup, Tenant
from utilities.forms import add_blank_choice
from utilities.forms.fields import DynamicModelChoiceField
from utilities.forms.rendering import FieldSet

from ..assembly import (
    SIDE_A,
    SIDE_B,
    SIDE_BOTH,
    assembly_module_type_q,
    get_module_type_side,
)
from ..choices import HardwareKindChoices
from ..models import *
from ..utils import get_plugin_setting

__all__ = (
    'AssetRoleForm',
    'AssetForm',
    'AssetModuleEndForm',
)


#
# Asset roles
#


class AssetRoleForm(NestedGroupModelForm):
    parent = DynamicModelChoiceField(
        queryset=AssetRole.objects.all(),
        required=False,
        label='Parent',
    )

    fieldsets = (
        FieldSet(
            'name',
            'slug',
            'parent',
            'color',
            'description',
            'tags',
            name='Asset Role',
        ),
    )

    class Meta:
        model = AssetRole
        fields = (
            'name',
            'slug',
            'parent',
            'color',
            'description',
            'owner',
            'tags',
            'comments',
        )


#
# Assets
#


class AssetForm(PrimaryModelForm):
    manufacturer = DynamicModelChoiceField(
        queryset=Manufacturer.objects.all(),
        required=False,
        initial_params={
            'device_types': '$device_type',
            'module_types': '$module_type',
            'rack_types': '$rack_type',
        },
    )
    device_type = DynamicModelChoiceField(
        queryset=DeviceType.objects.all(),
        required=False,
        query_params={
            'manufacturer_id': '$manufacturer',
        },
    )
    module_type = DynamicModelChoiceField(
        queryset=ModuleType.objects.all(),
        required=False,
        query_params={
            'manufacturer_id': '$manufacturer',
        },
    )
    rack_type = DynamicModelChoiceField(
        queryset=RackType.objects.all(),
        required=False,
        query_params={
            'manufacturer_id': '$manufacturer',
        },
    )
    owning_tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.all(),
        help_text=Asset._meta.get_field('owning_tenant').help_text,
        required=not Asset._meta.get_field('owning_tenant').blank,
    )
    tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.all(),
        help_text=Asset._meta.get_field('tenant').help_text,
        required=not Asset._meta.get_field('tenant').blank,
    )
    contact_group = DynamicModelChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        null_option='None',
        label='Contact Group',
        help_text='Filter contacts by group',
        initial_params={
            'contact': '$contact',
        },
    )
    contact = DynamicModelChoiceField(
        queryset=Contact.objects.all(),
        help_text=Asset._meta.get_field('contact').help_text,
        required=not Asset._meta.get_field('contact').blank,
        query_params={
            'group_id': '$contact_group',
        },
    )
    storage_site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        required=False,
        initial_params={
            'locations': '$storage_location',
        },
    )
    storage_location = DynamicModelChoiceField(
        queryset=Location.objects.all(),
        help_text=Asset._meta.get_field('storage_location').help_text,
        required=False,
        query_params={
            'site_id': '$storage_site',
        },
    )
    role = DynamicModelChoiceField(
        queryset=AssetRole.objects.all(),
        required=False,
        null_option='None',
        label='Role',
    )

    fieldsets = (
        FieldSet(
            'name', 'asset_tag', 'description', 'tags', 'status', 'role', name='General'
        ),
        FieldSet(
            'serial',
            'manufacturer',
            'device_type',
            'module_type',
            'rack_type',
            name='Hardware',
        ),
        FieldSet('owning_tenant', 'tenant', 'contact_group', 'contact', name='Tenancy'),
        FieldSet('storage_site', 'storage_location', name='Location'),
    )

    class Meta:
        model = Asset
        fields = (
            'name',
            'asset_tag',
            'serial',
            'status',
            'manufacturer',
            'role',
            'device_type',
            'module_type',
            'rack_type',
            'storage_location',
            'owning_tenant',
            'tenant',
            'contact_group',
            'contact',
            'tags',
            'owner',
            'description',
            'comments',
            'storage_site',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Used for picking the default active tab for hardware type selection.
        # Check initial data (not instance) so cloned assets, which pass the
        # hardware type via GET params, get the right tab too.
        self.no_hardware_type = not any(
            self.initial.get(f'{kind}_type')
            for kind in HardwareKindChoices.values()
        )

        # if assigned to device/module/... (or ends of a cable assembly are
        # installed) we can't change device_type/...
        if (
            self.instance.device
            or self.instance.module
            or self.instance.rack
            or (self.instance.pk and self.instance.ends.exists())
        ):
            self.fields['manufacturer'].disabled = True
            for kind in HardwareKindChoices.values():
                self.fields[f'{kind}_type'].disabled = True


#
# Cable assembly ends
#


class AssetModuleEndForm(NetBoxModelForm):
    """
    Install an end of a cable assembly in a module bay. If a module is already
    installed in the bay, it becomes the end. If the bay is empty, a new module
    is created.
    """

    asset = DynamicModelChoiceField(
        queryset=Asset.objects.filter(assembly_module_type_q()),
        query_params={'is_assembly': True},
        label='Cable assembly',
    )
    label = forms.CharField(
        required=False,
        label='End',
        help_text=AssetModuleEnd._meta.get_field('label').help_text,
    )
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        selector=True,
        label='Device',
    )
    module_bay = DynamicModelChoiceField(
        queryset=ModuleBay.objects.all(),
        query_params={'device_id': '$device'},
        label='Module bay',
        help_text='Module bay where the end is plugged in. If no module is '
        'installed in the bay, a new module is created.',
    )
    module_type = DynamicModelChoiceField(
        queryset=ModuleType.objects.all(),
        required=False,
        label='Module type',
        help_text='Module type of the new module, used only if the module bay is empty.',
    )

    fieldsets = (
        FieldSet('asset', 'label', 'is_primary', 'tags', name='Cable Assembly End'),
        FieldSet('device', 'module_bay', 'module_type', name='Installed In'),
    )

    class Meta:
        model = AssetModuleEnd
        fields = ('asset', 'label', 'is_primary', 'tags')
        help_texts = {
            'is_primary': 'Primary end of the cable assembly. The assembly is shown where '
            'its primary end is installed: the Installed Location and the Primary End '
            'on the asset page, and the Hardware, Installed Site, Installed Device, … '
            'columns (and their sorting) in the asset list. Filters such as installed '
            'site or installed device match any installed end. If '
            '<code>sync_hardware_serial_asset_tag</code> is enabled, the serial number '
            'is written to the modules of all ends, and the asset tag only to the '
            'module of the primary end (asset tags of modules are unique in NetBox); '
            'if it is disabled, nothing is written to the modules. If not checked, '
            'the first installed end and the end in the first side A slot become '
            'primary automatically.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_module = None

        module = self.instance._get_module()
        if module is not None:
            self.initial.setdefault('device', module.device_id)
            self.initial.setdefault('module_bay', module.module_bay_id)
            self.initial.setdefault('module_type', module.module_type_id)

        asset = self._get_asset()
        spec = asset.assembly_spec if asset else None
        if spec is None:
            return

        # offer the ends of the assembly that are not installed yet
        used = set(
            asset.ends.exclude(pk=self.instance.pk).values_list('label', flat=True)
        )
        self.fields['label'] = forms.ChoiceField(
            choices=add_blank_choice(
                [
                    (slot.label, f'{slot.label} (side {slot.side})')
                    for slot in spec.slots
                    if slot.label not in used
                ]
            ),
            required=False,
            label='End',
            help_text=self.fields['label'].help_text,
        )

        # module type of a new module: the asset's module type for side A
        # ends (and both ends of a symmetric assembly), otherwise a side B
        # module type with the same profile
        module_type = asset.module_type
        self.fields['module_type'].queryset = ModuleType.objects.filter(
            profile=module_type.profile_id
        )
        query_params = {'profile_id': module_type.profile_id}
        slot = spec.get_slot(self.initial.get('label') or self.instance.label)
        if slot and (slot.side == SIDE_A or get_module_type_side(module_type) == SIDE_BOTH):
            self.initial.setdefault('module_type', module_type.pk)
        elif slot and slot.side == SIDE_B:
            query_params.update(
                {'attr_side': SIDE_B, 'manufacturer_id': module_type.manufacturer_id}
            )
            candidates = ModuleType.objects.filter(
                profile=module_type.profile_id,
                manufacturer=module_type.manufacturer_id,
                attribute_data__side=SIDE_B,
            )
            if len(candidates[:2]) == 1:
                self.initial.setdefault('module_type', candidates[0].pk)
        self.fields['module_type'].widget.add_query_params(query_params)

    def _get_asset(self):
        value = self.data.get('asset') if self.is_bound else None
        value = value or self.initial.get('asset') or self.instance.asset_id
        if not value:
            return None
        try:
            return Asset.objects.select_related('module_type__profile').get(pk=value)
        except (Asset.DoesNotExist, ValueError, TypeError):
            return None

    def clean(self):
        super().clean()
        asset = self.cleaned_data.get('asset')
        device = self.cleaned_data.get('device')
        module_bay = self.cleaned_data.get('module_bay')
        if not asset or not module_bay:
            return self.cleaned_data
        if device and module_bay.device_id != device.pk:
            raise ValidationError(
                {'module_bay': f'Module bay {module_bay} does not belong to device {device}.'}
            )
        module_type = self.cleaned_data.get('module_type')
        try:
            module = module_bay.installed_module
        except Module.DoesNotExist:
            module = self._build_module(asset, module_bay, module_type)
        else:
            if module_type and module.module_type != module_type:
                raise ValidationError(
                    {
                        'module_type': f'Module {module} of type {module.module_type} '
                        f'is already installed in module bay {module_bay}.'
                    }
                )
        self.instance.module = module
        return self.cleaned_data

    def _build_module(self, asset, module_bay, module_type):
        """New module for the end, validated now and saved in save()."""
        if module_type is None:
            raise ValidationError(
                {'module_type': 'Module bay is empty. Select the module type of the new module.'}
            )
        request = current_request.get()
        if request is not None and not request.user.has_perm('dcim.add_module'):
            raise ValidationError(
                {'module_bay': 'Module bay is empty and you are not allowed to create modules.'}
            )
        module = Module(
            device=module_bay.device,
            module_bay=module_bay,
            module_type=module_type,
        )
        if get_plugin_setting('sync_hardware_serial_asset_tag'):
            module.serial = asset.serial or ''
        try:
            module.full_clean()
        except ValidationError as e:
            raise ValidationError(
                {'module_bay': [f'Cannot create module: {m}' for m in e.messages]}
            )
        self.new_module = module
        return module

    def save(self, *args, **kwargs):
        if self.new_module is not None:
            self.new_module.save()
            self.instance.module = self.new_module
        return super().save(*args, **kwargs)
