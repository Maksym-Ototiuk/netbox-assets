from django import forms

from dcim.models import DeviceType, Location, ModuleType, RackType
from netbox.forms import NestedGroupModelBulkEditForm, PrimaryModelBulkEditForm
from tenancy.models import Contact, ContactGroup, Tenant
from utilities.forms import add_blank_choice
from utilities.forms.fields import ColorField, DynamicModelChoiceField
from utilities.forms.rendering import FieldSet

from ..choices import AssetStatusChoices
from ..models import *

__all__ = (
    'AssetBulkEditForm',
    'AssetRoleBulkEditForm',
)


#
# Asset roles
#


class AssetRoleBulkEditForm(NestedGroupModelBulkEditForm):
    parent = DynamicModelChoiceField(
        queryset=AssetRole.objects.all(),
        required=False,
        label='Parent',
    )
    color = ColorField(
        required=False,
        label='Color',
    )

    model = AssetRole
    fieldsets = (FieldSet('parent', 'color', 'description'),)
    nullable_fields = ('parent', 'color', 'description', 'comments')


#
# Assets
#


class AssetBulkEditForm(PrimaryModelBulkEditForm):
    name = forms.CharField(
        required=False,
    )
    status = forms.ChoiceField(
        choices=add_blank_choice(AssetStatusChoices),
        required=False,
        initial='',
    )
    role = DynamicModelChoiceField(
        queryset=AssetRole.objects.all(),
        required=False,
        label='Role',
    )
    device_type = DynamicModelChoiceField(
        queryset=DeviceType.objects.all(),
        required=False,
        label='Device type',
    )
    # FIXME figure out how to only show set null checkbox
    device = forms.CharField(
        disabled=True,
        required=False,
    )
    module_type = DynamicModelChoiceField(
        queryset=ModuleType.objects.all(),
        required=False,
        label='Module type',
    )
    # FIXME figure out how to only show set null checkbox
    module = forms.CharField(
        disabled=True,
        required=False,
    )
    rack_type = DynamicModelChoiceField(
        queryset=RackType.objects.all(),
        required=False,
        label='Rack type',
    )
    # FIXME figure out how to only show set null checkbox
    rack = forms.CharField(
        disabled=True,
        required=False,
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
    )
    contact = DynamicModelChoiceField(
        queryset=Contact.objects.all(),
        help_text=Asset._meta.get_field('contact').help_text,
        required=not Asset._meta.get_field('contact').blank,
        query_params={
            'group_id': '$contact_group',
        },
    )
    storage_location = DynamicModelChoiceField(
        queryset=Location.objects.all(),
        help_text=Asset._meta.get_field('storage_location').help_text,
        required=False,
    )

    model = Asset
    fieldsets = (
        FieldSet(
            'name',
            'status',
            'role',
            'description',
            name='General',
        ),
        FieldSet(
            'device_type',
            'device',
            'module_type',
            'module',
            'rack_type',
            'rack',
            name='Hardware',
        ),
        FieldSet(
            'owning_tenant',
            'tenant',
            'contact_group',
            'contact',
            name='Tenancy',
        ),
        FieldSet(
            'storage_location',
            name='Location',
        ),
    )
    nullable_fields = (
        'name',
        'role',
        'description',
        'device',
        'module',
        'rack',
        'owning_tenant',
        'tenant',
        'contact',
        'storage_location',
    )
