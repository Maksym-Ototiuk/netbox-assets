from dcim.models import DeviceType, Location, Manufacturer, ModuleType, RackType, Site
from netbox.forms import NestedGroupModelForm, PrimaryModelForm
from tenancy.models import Contact, ContactGroup, Tenant
from utilities.forms.fields import DynamicModelChoiceField
from utilities.forms.rendering import FieldSet

from ..choices import HardwareKindChoices
from ..models import *

__all__ = (
    'AssetRoleForm',
    'AssetForm',
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
        FieldSet('owning_tenant', name='Ownership'),
        FieldSet('tenant', 'contact_group', 'contact', name='Assigned to'),
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

        # Used for picking the default active tab for hardware type selection
        self.no_hardware_type = True
        if self.instance:
            if (
                self.instance.device_type
                or self.instance.module_type
                or self.instance.rack_type
            ):
                self.no_hardware_type = False

        # if assigned to device/module/... we can't change device_type/...
        if self.instance.device or self.instance.module or self.instance.rack:
            self.fields['manufacturer'].disabled = True
            for kind in HardwareKindChoices.values():
                self.fields[f'{kind}_type'].disabled = True
