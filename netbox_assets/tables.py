import django_tables2 as tables
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

from dcim.tables import (
    DeviceTypeTable,
    LocationTable,
    ModuleTypeTable,
    RackTypeTable,
)
from netbox.tables import (
    NestedGroupModelTable,
    NetBoxTable,
    PrimaryModelTable,
    columns,
)
from utilities.tables import register_table_column

from .models import *

__all__ = (
    'AssetRoleTable',
    'AssetTable',
)


#
# Asset roles
#


class AssetRoleTable(NestedGroupModelTable):
    asset_count = columns.LinkedCountColumn(
        viewname='plugins:netbox_assets:asset_list',
        url_params={'role_id': 'pk'},
        verbose_name=_('Assets'),
    )
    color = columns.ColorColumn()
    tags = columns.TagColumn(
        url_name='plugins:netbox_assets:assetrole_list',
    )

    class Meta(NestedGroupModelTable.Meta):
        model = AssetRole
        fields = (
            'pk',
            'id',
            'name',
            'parent',
            'asset_count',
            'color',
            'description',
            'slug',
            'owner_group',
            'owner',
            'comments',
            'tags',
            'actions',
            'created',
            'last_updated',
        )
        default_columns = (
            'pk',
            'name',
            'asset_count',
            'color',
            'description',
        )


#
# Assets
#


class AssetTable(PrimaryModelTable):
    name = tables.Column(
        linkify=True,
    )
    serial = tables.Column(
        linkify=True,
    )
    kind = tables.Column(
        accessor='get_kind_display',
        orderable=False,
    )
    manufacturer = tables.Column(
        accessor='hardware_type__manufacturer',
        linkify=True,
    )
    hardware_type = tables.Column(
        linkify=True,
        verbose_name='Hardware Type',
    )
    status = columns.ChoiceFieldColumn()
    hardware = tables.Column(
        linkify=True,
        order_by=('device', 'module', 'rack'),
    )
    role = columns.ColoredLabelColumn(
        verbose_name=_('Role'),
    )
    hardware_role = tables.Column(
        accessor=columns.Accessor('hardware__role'),
        linkify=True,
        verbose_name='Hardware Role',
    )
    installed_site = tables.Column(
        linkify=True,
        verbose_name='Installed Site',
    )
    installed_location = tables.Column(
        linkify=True,
        verbose_name='Installed Location',
    )
    installed_rack = tables.Column(
        linkify=True,
        verbose_name='Installed Rack',
    )
    installed_device = tables.Column(
        linkify=True,
        verbose_name='Installed Device',
    )
    tenant = tables.Column(
        linkify=True,
    )
    contact = tables.Column(
        linkify=True,
    )
    storage_location = tables.Column(
        linkify=True,
    )
    owning_tenant = tables.Column(
        linkify=True,
    )
    current_site = tables.Column(
        linkify=True,
        verbose_name='Current Site',
        orderable=False,
    )
    current_location = tables.Column(
        linkify=True,
        verbose_name='Current Location',
        orderable=False,
    )
    tags = columns.TagColumn(
        url_name='plugins:netbox_assets:asset_list',
    )
    actions = columns.ActionsColumn(
        extra_buttons="""
            {% if record.hardware %}
            <a href="#" class="btn btn-sm btn-outline-dark disabled">
                <i class="mdi mdi-vector-difference-ba" aria-hidden="true"></i>
            </a>
            {% else %}
            <a href="{% url 'plugins:netbox_assets:asset_'|add:record.kind|add:'_create' %}?asset_id={{ record.pk }}" class="btn btn-sm btn-green" title="Create hardware from asset">
                <i class="mdi mdi-vector-difference-ba"></i>
            </a>
            {% endif %}
            <a href="{% url 'plugins:netbox_assets:asset_assign' record.pk %}" class="btn btn-sm btn-orange" title="Edit hardware assignment">
                <i class="mdi mdi-vector-link"></i>
            </a>
        """
    )

    def order_manufacturer(self, queryset, is_descending):
        queryset = queryset.annotate(
            manufacturer=Coalesce(
                'device_type__manufacturer',
                'module_type__manufacturer',
                'rack_type__manufacturer',
            )
        ).order_by(
            ('-' if is_descending else '') + 'manufacturer',
            ('-' if is_descending else '') + 'serial',
        )
        return (queryset, True)

    def order_hardware_type(self, queryset, is_descending):
        queryset, _ = self.order_manufacturer(queryset, is_descending)
        queryset = queryset.annotate(
            model=Coalesce(
                'device_type__model',
                'module_type__model',
                'rack_type__model',
            )
        ).order_by(
            ('-' if is_descending else '') + 'manufacturer',
            ('-' if is_descending else '') + 'model',
            ('-' if is_descending else '') + 'serial',
        )
        return (queryset, True)

    def order_hardware(self, queryset, is_descending):
        queryset = queryset.annotate(
            hw=Coalesce(
                'device__name',
                'module__device__name',
                'rack__name',
            )
        ).order_by(
            ('-' if is_descending else '') + 'hw',
            ('-' if is_descending else '') + 'module__module_bay',
            ('-' if is_descending else '') + 'serial',
        )
        return (queryset, True)

    def order_hardware_role(self, queryset, is_descending):
        queryset = queryset.annotate(
            role_name=Coalesce(
                'device__role__name',
                'rack__role__name',
            )
        ).order_by(
            ('-' if is_descending else '') + 'role_name',
            ('-' if is_descending else '') + 'serial',
        )
        return (queryset, True)

    def _order_annotate_installed(self, queryset):
        return queryset.annotate(
            site_name=Coalesce(
                'device__site__name',
                'module__device__site__name',
                'rack__site__name',
            ),
            location_name=Coalesce(
                'device__location__name',
                'module__device__location__name',
                'rack__location__name',
            ),
            rack_name=Coalesce(
                'device__rack__name',
                'module__device__rack__name',
                'rack__name',
            ),
            device_name=Coalesce('device__name', 'module__device__name'),
        )

    def order_installed_site(self, queryset, is_descending):
        queryset = self._order_annotate_installed(queryset).order_by(
            ('-' if is_descending else '') + 'site_name',
            ('-' if is_descending else '') + 'device_name',
            ('-' if is_descending else '') + 'module__module_bay',
            ('-' if is_descending else '') + 'serial',
        )
        return (queryset, True)

    def order_installed_location(self, queryset, is_descending):
        queryset = self._order_annotate_installed(queryset).order_by(
            ('-' if is_descending else '') + 'site_name',
            ('-' if is_descending else '') + 'location_name',
            ('-' if is_descending else '') + 'device_name',
            ('-' if is_descending else '') + 'module__module_bay',
            ('-' if is_descending else '') + 'serial',
        )
        return (queryset, True)

    def order_installed_rack(self, queryset, is_descending):
        queryset = self._order_annotate_installed(queryset).order_by(
            ('-' if is_descending else '') + 'site_name',
            ('-' if is_descending else '') + 'location_name',
            ('-' if is_descending else '') + 'rack_name',
            ('-' if is_descending else '') + 'device_name',
            ('-' if is_descending else '') + 'module__module_bay',
            ('-' if is_descending else '') + 'serial',
        )
        return (queryset, True)

    def order_installed_device(self, queryset, is_descending):
        queryset = self._order_annotate_installed(queryset).order_by(
            ('-' if is_descending else '') + 'device_name',
            ('-' if is_descending else '') + 'module__module_bay',
            ('-' if is_descending else '') + 'serial',
        )
        return (queryset, True)

    class Meta(NetBoxTable.Meta):
        model = Asset
        fields = (
            'pk',
            'id',
            'name',
            'role',
            'asset_tag',
            'serial',
            'status',
            'kind',
            'manufacturer',
            'hardware_type',
            'hardware',
            'hardware_role',
            'installed_site',
            'installed_location',
            'installed_rack',
            'installed_device',
            'tenant',
            'contact',
            'storage_site',
            'storage_location',
            'current_site',
            'current_location',
            'owning_tenant',
            'owner_group',
            'owner',
            'description',
            'comments',
            'tags',
            'created',
            'last_updated',
            'actions',
        )
        default_columns = (
            'id',
            'name',
            'serial',
            'kind',
            'role',
            'manufacturer',
            'hardware_type',
            'asset_tag',
            'status',
            'hardware',
            'tags',
        )


# ========================
# DCIM model table columns
# ========================

asset_count = columns.LinkedCountColumn(
    viewname='plugins:netbox_assets:asset_list',
    url_params={'device_type_id': 'pk'},
    verbose_name=_('Asset Count'),
    accessor='assets__count',
    orderable=False,
)

register_table_column(asset_count, 'assets', DeviceTypeTable)


asset_count = columns.LinkedCountColumn(
    viewname='plugins:netbox_assets:asset_list',
    url_params={'module_type_id': 'pk'},
    verbose_name=_('Asset Count'),
    accessor='assets__count',
    orderable=False,
)

register_table_column(asset_count, 'assets', ModuleTypeTable)


asset_count = columns.LinkedCountColumn(
    viewname='plugins:netbox_assets:asset_list',
    url_params={'rack_type_id': 'pk'},
    verbose_name=_('Asset Count'),
    accessor='assets__count',
    orderable=False,
)

register_table_column(asset_count, 'assets', RackTypeTable)


asset_count = columns.LinkedCountColumn(
    viewname='plugins:netbox_assets:asset_list',
    url_params={'storage_location_id': 'pk'},
    verbose_name=_('Asset Count'),
    # accessor='assets__count',
    accessor=tables.A('assets__count_with_children'),
    orderable=False,
)

register_table_column(asset_count, 'assets', LocationTable)
