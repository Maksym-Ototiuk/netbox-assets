from django import forms
from django.utils.translation import gettext as _

from dcim.models import (
    Device,
    DeviceRole,
    DeviceType,
    Location,
    Manufacturer,
    ModuleType,
    Rack,
    RackRole,
    RackType,
    Site,
)
from netbox.forms import NestedGroupModelFilterSetForm, PrimaryModelFilterSetForm
from tenancy.models import Contact, ContactGroup, Tenant
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES
from utilities.forms.fields import DynamicModelMultipleChoiceField, TagFilterField
from utilities.forms.rendering import FieldSet

from ..choices import AssetStatusChoices, HardwareKindChoices
from ..models import *

__all__ = (
    'AssetFilterForm',
    'AssetRoleFilterForm',
)


#
# Asset roles
#


class AssetRoleFilterForm(NestedGroupModelFilterSetForm):
    model = AssetRole
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet(
            'parent_id',
            'name',
            'color',
            'description',
            name='Attributes',
        ),
        FieldSet('owner_group_id', 'owner_id', name='Ownership'),
    )
    parent_id = DynamicModelMultipleChoiceField(
        queryset=AssetRole.objects.all(),
        required=False,
        null_option='None',
        label='Parent',
    )
    name = forms.CharField(
        required=False,
        label=_('Name'),
    )
    color = forms.CharField(
        required=False,
        label=_('Color'),
    )
    description = forms.CharField(
        required=False,
        label=_('Description'),
    )
    tag = TagFilterField(model)


#
# Assets
#


class AssetFilterForm(PrimaryModelFilterSetForm):
    model = Asset
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet(
            'status',
            'name',
            'role_id',
            'description',
            'asset_tag',
            name='Attributes',
        ),
        FieldSet(
            'serial',
            'kind',
            'manufacturer_id',
            'device_type_id',
            'device_role_id',
            'module_type_id',
            'rack_type_id',
            'rack_role_id',
            'is_assigned',
            name='Hardware',
        ),
        FieldSet(
            'owning_tenant_id',
            'tenant_id',
            'contact_group_id',
            'contact_id',
            name='Tenancy',
        ),
        FieldSet(
            'storage_site_id',
            'storage_location_id',
            'installed_site_id',
            'installed_location_id',
            'installed_rack_id',
            'installed_device_id',
            'located_site_id',
            'located_location_id',
            name='Location',
        ),
        FieldSet('owner_group_id', 'owner_id', name='Ownership'),
    )

    status = forms.MultipleChoiceField(
        choices=AssetStatusChoices,
        required=False,
    )
    name = forms.CharField(
        required=False,
        label=_('Name'),
    )
    description = forms.CharField(
        required=False,
        label=_('Description'),
    )
    asset_tag = forms.CharField(
        required=False,
        label=_('Asset tag'),
    )
    serial = forms.CharField(
        required=False,
        label=_('Serial number'),
    )
    role_id = DynamicModelMultipleChoiceField(
        queryset=AssetRole.objects.all(),
        required=False,
        null_option='None',
        label='Asset role',
    )
    kind = forms.MultipleChoiceField(
        choices=HardwareKindChoices,
        required=False,
        help_text='Type of hardware',
    )
    manufacturer_id = DynamicModelMultipleChoiceField(
        queryset=Manufacturer.objects.all(),
        required=False,
        label='Manufacturer',
    )
    device_type_id = DynamicModelMultipleChoiceField(
        queryset=DeviceType.objects.all(),
        required=False,
        query_params={
            'manufacturer_id': '$manufacturer_id',
        },
        label='Device type',
    )
    device_role_id = DynamicModelMultipleChoiceField(
        queryset=DeviceRole.objects.all(),
        required=False,
        label='Device role',
    )
    module_type_id = DynamicModelMultipleChoiceField(
        queryset=ModuleType.objects.all(),
        required=False,
        query_params={
            'manufacturer_id': '$manufacturer_id',
        },
        label='Module type',
    )
    rack_type_id = DynamicModelMultipleChoiceField(
        queryset=RackType.objects.all(),
        required=False,
        query_params={
            'manufacturer_id': '$manufacturer_id',
        },
        label='Rack type',
    )
    rack_role_id = DynamicModelMultipleChoiceField(
        queryset=RackRole.objects.all(),
        required=False,
        label='Rack role',
    )
    is_assigned = forms.NullBooleanField(
        required=False,
        label='Is assigned to hardware',
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    tenant_id = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        null_option='None',
        label='Tenant',
    )
    contact_group_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        null_option='None',
        label='Contact Group',
    )
    contact_id = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        null_option='None',
        query_params={
            'group_id': '$contact_group_id',
        },
        label='Contact',
    )
    owning_tenant_id = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        null_option='None',
        label='Owning tenant',
    )
    storage_site_id = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(),
        required=False,
        label='Storage site',
        help_text='When not in use asset is stored here',
    )
    storage_location_id = DynamicModelMultipleChoiceField(
        queryset=Location.objects.all(),
        required=False,
        null_option='None',
        query_params={
            'site_id': '$storage_site_id',
        },
        label='Storage location',
        help_text='When not in use asset is stored here',
    )
    installed_site_id = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(),
        required=False,
        label='Installed at site',
        help_text='Currently installed here',
    )
    installed_location_id = DynamicModelMultipleChoiceField(
        queryset=Location.objects.all(),
        required=False,
        query_params={
            'site_id': '$installed_site_id',
        },
        label='Installed at location',
        help_text='Currently installed here',
    )
    installed_rack_id = DynamicModelMultipleChoiceField(
        queryset=Rack.objects.all(),
        required=False,
        query_params={
            'site_id': '$installed_site_id',
            'location_id': '$installed_location_id',
        },
        label='Installed in rack',
        help_text='Currently installed here',
    )
    installed_device_id = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required=False,
        query_params={
            'site_id': '$installed_site_id',
            'location_id': '$installed_location_id',
            'rack_id': '$installed_rack_id',
        },
        label='Installed in device',
    )
    located_site_id = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(),
        required=False,
        label='Located at site',
        help_text='Currently installed or stored here',
    )
    located_location_id = DynamicModelMultipleChoiceField(
        queryset=Location.objects.all(),
        required=False,
        query_params={
            'site_id': '$located_site_id',
        },
        label='Located at location',
        help_text='Currently installed or stored here',
    )
    tag = TagFilterField(model)
