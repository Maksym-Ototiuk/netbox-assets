from functools import reduce

import django_filters
from django.db.models import Q

from dcim.filtersets import DeviceFilterSet, ModuleFilterSet
from dcim.models import (
    Device,
    DeviceRole,
    DeviceType,
    Location,
    Module,
    ModuleType,
    Rack,
    RackRole,
    RackType,
    Site,
)
from netbox.filtersets import (
    NestedGroupModelFilterSet,
    NetBoxModelFilterSet,
    PrimaryModelFilterSet,
)
from tenancy.models import Contact, ContactGroup, Tenant
from utilities import filters
from utilities.filters import TreeNodeMultipleChoiceFilter
from utilities.filtersets import register_filterset

from .choices import AssetStatusChoices, HardwareKindChoices
from .models import *
from .utils import get_asset_custom_fields_search_filters, query_located

__all__ = (
    'AssetFilterSet',
    'AssetRoleFilterSet',
    'DeviceAssetFilterSet',
    'ModuleAssetFilterSet',
)


#
# Asset roles
#


@register_filterset
class AssetRoleFilterSet(NestedGroupModelFilterSet):
    parent_id = django_filters.ModelMultipleChoiceFilter(
        queryset=AssetRole.objects.all(),
        distinct=False,
        label='Parent asset role (ID)',
    )
    parent = django_filters.ModelMultipleChoiceFilter(
        field_name='parent__slug',
        queryset=AssetRole.objects.all(),
        distinct=False,
        to_field_name='slug',
        label='Parent asset role (slug)',
    )
    ancestor_id = TreeNodeMultipleChoiceFilter(
        queryset=AssetRole.objects.all(),
        field_name='parent',
        lookup_expr='in',
        label='Ancestor asset role (ID)',
    )
    ancestor = TreeNodeMultipleChoiceFilter(
        queryset=AssetRole.objects.all(),
        field_name='parent',
        lookup_expr='in',
        to_field_name='slug',
        label='Ancestor asset role (slug)',
    )

    class Meta:
        model = AssetRole
        fields = (
            'id',
            'name',
            'slug',
            'color',
            'description',
        )


#
# Assets
#


@register_filterset
class AssetFilterSet(PrimaryModelFilterSet):
    status = django_filters.MultipleChoiceFilter(
        choices=AssetStatusChoices,
    )
    role_id = filters.TreeNodeMultipleChoiceFilter(
        field_name='role',
        queryset=AssetRole.objects.all(),
        lookup_expr='in',
        label='Asset role (ID)',
    )
    role = filters.MultiValueCharFilter(
        field_name='role__slug',
        lookup_expr='iexact',
        label='Asset role (slug)',
    )
    kind = filters.MultiValueCharFilter(
        method='filter_kind',
        label='Type of hardware',
    )
    manufacturer_id = filters.MultiValueCharFilter(
        method='filter_manufacturer',
        label='Manufacturer (ID)',
    )
    manufacturer_name = filters.MultiValueCharFilter(
        method='filter_manufacturer',
        label='Manufacturer (name)',
    )
    device = filters.MultiValueCharFilter(
        field_name='device__name',
        lookup_expr='iexact',
        label='Device (name)',
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='device',
        queryset=Device.objects.all(),
        label='Device (ID)',
    )
    device_type_id = django_filters.ModelMultipleChoiceFilter(
        field_name='device_type',
        queryset=DeviceType.objects.all(),
        label='Device type (ID)',
    )
    device_type = filters.MultiValueCharFilter(
        field_name='device_type__slug',
        lookup_expr='iexact',
        label='Device type (slug)',
    )
    device_type_model = filters.MultiValueCharFilter(
        field_name='device_type__model',
        lookup_expr='icontains',
        label='Device type (model)',
    )
    device_role_id = django_filters.ModelMultipleChoiceFilter(
        field_name='device__role',
        queryset=DeviceRole.objects.all(),
        label='Device role (ID)',
    )
    device_role = filters.MultiValueCharFilter(
        field_name='device__role__slug',
        lookup_expr='iexact',
        label='Device role (slug)',
    )
    module_id = django_filters.ModelMultipleChoiceFilter(
        field_name='module',
        queryset=Module.objects.all(),
        label='Module (ID)',
    )
    module_type_id = django_filters.ModelMultipleChoiceFilter(
        field_name='module_type',
        queryset=ModuleType.objects.all(),
        label='Module type (ID)',
    )
    module_type_model = filters.MultiValueCharFilter(
        field_name='module_type__model',
        lookup_expr='icontains',
        label='Module type (model)',
    )
    rack = filters.MultiValueCharFilter(
        field_name='rack__name',
        lookup_expr='iexact',
        label='Rack (name)',
    )
    rack_id = django_filters.ModelMultipleChoiceFilter(
        field_name='rack',
        queryset=Rack.objects.all(),
        label='Rack (ID)',
    )
    rack_type_id = django_filters.ModelMultipleChoiceFilter(
        field_name='rack_type',
        queryset=RackType.objects.all(),
        label='Rack type (ID)',
    )
    rack_type = filters.MultiValueCharFilter(
        field_name='rack_type__slug',
        lookup_expr='iexact',
        label='Rack type (slug)',
    )
    rack_type_model = filters.MultiValueCharFilter(
        field_name='rack_type__model',
        lookup_expr='icontains',
        label='Rack type (model)',
    )
    rack_role_id = django_filters.ModelMultipleChoiceFilter(
        field_name='rack__role',
        queryset=RackRole.objects.all(),
        label='Rack role (ID)',
    )
    rack_role = filters.MultiValueCharFilter(
        field_name='rack__role__slug',
        lookup_expr='iexact',
        label='Rack role (slug)',
    )
    is_assigned = django_filters.BooleanFilter(
        method='filter_is_assigned',
        label='Is assigned to hardware',
    )
    tenant_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Tenant.objects.all(),
        field_name='tenant',
        label='Tenant (ID)',
    )
    tenant = django_filters.ModelMultipleChoiceFilter(
        queryset=Tenant.objects.all(),
        field_name='tenant__slug',
        to_field_name='slug',
        label='Tenant (slug)',
    )
    tenant_name = filters.MultiValueCharFilter(
        field_name='tenant__name',
        lookup_expr='icontains',
        label='Tenant (name)',
    )
    contact_group_id = django_filters.ModelMultipleChoiceFilter(
        queryset=ContactGroup.objects.all(),
        field_name='contact__groups',
        label='Contact Group (ID)',
    )
    contact_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Contact.objects.all(),
        field_name='contact',
        label='Contact (ID)',
    )
    owning_tenant_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Tenant.objects.all(),
        field_name='owning_tenant',
        label='Owning tenant (ID)',
    )
    owning_tenant = django_filters.ModelMultipleChoiceFilter(
        queryset=Tenant.objects.all(),
        field_name='owning_tenant__slug',
        to_field_name='slug',
        label='Owning tenant (slug)',
    )
    owning_tenant_name = filters.MultiValueCharFilter(
        field_name='owning_tenant__name',
        lookup_expr='icontains',
        label='Owning tenant (name)',
    )
    storage_site_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Site.objects.all(),
        field_name='storage_location__site',
        label='Storage site (ID)',
    )
    storage_location_id = TreeNodeMultipleChoiceFilter(
        queryset=Location.objects.all(),
        field_name='storage_location',
        lookup_expr='in',
        label='Storage location (ID)',
    )
    installed_site_slug = filters.MultiValueCharFilter(
        method='filter_installed_site_slug',
        label='Installed site (slug)',
    )
    installed_site_id = filters.MultiValueCharFilter(
        method='filter_installed',
        field_name='site',
        label='Installed site (ID)',
    )
    installed_location_id = filters.MultiValueCharFilter(
        method='filter_installed',
        field_name='location',
        label='Installed location (ID)',
    )
    installed_rack_id = filters.MultiValueCharFilter(
        method='filter_installed',
        field_name='rack',
        label='Installed rack (ID)',
    )
    installed_device_id = filters.MultiValueCharFilter(
        method='filter_installed_device',
        field_name='id',
        label='Installed device (ID)',
    )
    installed_device_name = filters.MultiValueCharFilter(
        method='filter_installed_device',
        field_name='name',
        label='Installed device (name)',
    )
    located_site_id = filters.MultiValueCharFilter(
        method='filter_located',
        field_name='site',
        label='Located site (ID)',
    )
    located_location_id = filters.MultiValueCharFilter(
        method='filter_located',
        field_name='location',
        label='Located location (ID)',
    )
    tenant_any_id = filters.MultiValueCharFilter(
        method='filter_tenant_any',
        field_name='id',
        label='Any tenant (ID)',
    )
    tenant_any = filters.MultiValueCharFilter(
        method='filter_tenant_any',
        field_name='slug',
        label='Any tenant (slug)',
    )

    class Meta:
        model = Asset
        fields = (
            'id',
            'name',
            'serial',
            'asset_tag',
            'role',
            'role_id',
            'description',
        )

    def search(self, queryset, name, value):
        query = (
            Q(id__contains=value)
            | Q(serial__icontains=value)
            | Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(asset_tag__icontains=value)
            | Q(device_type__model__icontains=value)
            | Q(module_type__model__icontains=value)
            | Q(rack_type__model__icontains=value)
            | Q(device__name__icontains=value)
            | Q(rack__name__icontains=value)
            | Q(tenant__name__icontains=value)
            | Q(owning_tenant__name__icontains=value)
        )
        custom_field_filters = get_asset_custom_fields_search_filters()
        for custom_field_filter in custom_field_filters:
            query |= Q(**{custom_field_filter: value})

        return queryset.filter(query)

    def filter_kind(self, queryset, name, value):
        query = None
        for kind in HardwareKindChoices.values():
            if kind in value:
                q = Q(**{f'{kind}_type__isnull': False})
                if query:
                    query = query | q
                else:
                    query = q
        if query:
            return queryset.filter(query)
        else:
            return queryset

    def filter_manufacturer(self, queryset, name, value):
        if name == 'manufacturer_id':
            return queryset.filter(
                Q(device_type__manufacturer__in=value)
                | Q(module_type__manufacturer__in=value)
                | Q(rack_type__manufacturer__in=value)
            )
        elif name == 'manufacturer_name':
            # OR for every passed value and for all hardware types
            q = Q()
            for v in value:
                q |= Q(device_type__manufacturer__name__icontains=v)
                q |= Q(module_type__manufacturer__name__icontains=v)
                q |= Q(rack_type__manufacturer__name__icontains=v)
            return queryset.filter(q)

    def filter_is_assigned(self, queryset, name, value):
        if value:
            # is assigned to any hardware
            return queryset.filter(
                Q(device__isnull=False)
                | Q(module__isnull=False)
                | Q(rack__isnull=False)
            )
        else:
            # is not assigned to hardware kind
            return queryset.filter(
                Q(device__isnull=True) & Q(module__isnull=True) & Q(rack__isnull=True)
            )

    def filter_installed(self, queryset, name, value):
        return query_located(queryset, name, value, assets_shown='installed')

    def filter_installed_site_slug(self, queryset, name, value):
        return query_located(queryset, 'site__slug', value, assets_shown='installed')

    def filter_installed_device(self, queryset, name, value):
        return query_located(queryset, name, value, assets_shown='installed')

    def filter_located(self, queryset, name, value):
        return query_located(queryset, name, value)

    def filter_tenant_any(self, queryset, name, value):
        # filter OR for owning_tenant and tenant fields
        if name == 'slug':
            q_list = (
                Q(tenant__slug__iexact=n) | Q(owning_tenant__slug__iexact=n)
                for n in value
            )
        elif name == 'id':
            q_list = (Q(tenant__pk=n) | Q(owning_tenant__pk=n) for n in value)
        q_list = reduce(lambda a, b: a | b, q_list)
        return queryset.filter(q_list)


class HasAssetFilterMixin(NetBoxModelFilterSet):
    has_asset_assigned = django_filters.BooleanFilter(
        method='_has_asset_assigned',
        label='Has an asset assigned',
    )

    def _has_asset_assigned(self, queryset, name, value):
        params = Q(assigned_asset__isnull=False)
        if value:
            return queryset.filter(params)
        return queryset.exclude(params)


class DeviceAssetFilterSet(HasAssetFilterMixin, DeviceFilterSet):
    pass


class ModuleAssetFilterSet(HasAssetFilterMixin, ModuleFilterSet):
    pass
