from netbox.plugins import PluginTemplateExtension

from .models import Asset
from .utils import query_located

#
# Assets
#


class AssetInfoExtension(PluginTemplateExtension):
    def left_page(self):
        object = self.context.get('object')
        asset = Asset.objects.filter(**{self.kind: object}).first()
        context = {'asset': asset}
        return self.render('netbox_assets/inc/asset_info.html', extra_context=context)


class AssetLocationCounts(PluginTemplateExtension):
    def right_page(self):
        object = self.context.get('object')
        user = self.context['request'].user
        assets_qs = Asset.objects.restrict(user, 'view')
        count_installed = query_located(
            assets_qs, self.location_type, [object.pk], assets_shown='installed'
        ).count()
        count_stored = query_located(
            assets_qs, self.location_type, [object.pk], assets_shown='stored'
        ).count()
        context = {
            'asset_stats': [
                {
                    'label': 'Installed',
                    'filter_field': f'installed_{self.location_type}_id',
                    'count': count_installed,
                },
                {
                    'label': 'Stored',
                    'filter_field': f'storage_{self.location_type}_id',
                    'count': count_stored,
                },
                {
                    'label': 'Total',
                    'filter_field': f'located_{self.location_type}_id',
                    'count': count_installed + count_stored,
                },
            ],
        }
        return self.render(
            'netbox_assets/inc/asset_stats_counts.html', extra_context=context
        )


class DeviceAssetInfo(AssetInfoExtension):
    models = ['dcim.device']
    kind = 'device'


class ModuleAssetInfo(AssetInfoExtension):
    models = ['dcim.module']
    kind = 'module'


class RackAssetInfo(AssetInfoExtension):
    models = ['dcim.rack']
    kind = 'rack'


class ManufacturerAssetCounts(PluginTemplateExtension):
    models = ['dcim.manufacturer']

    def right_page(self):
        object = self.context.get('object')
        user = self.context['request'].user
        assets_qs = Asset.objects.restrict(user, 'view')
        counts = {
            kind: assets_qs.filter(**{f'{kind}_type__manufacturer': object}).count()
            for kind in ('device', 'module', 'rack')
        }
        context = {
            'asset_stats': [
                {
                    'label': 'Device',
                    'filter_field': 'manufacturer_id',
                    'extra_filter': '&kind=device',
                    'count': counts['device'],
                },
                {
                    'label': 'Module',
                    'filter_field': 'manufacturer_id',
                    'extra_filter': '&kind=module',
                    'count': counts['module'],
                },
                {
                    'label': 'Rack',
                    'filter_field': 'manufacturer_id',
                    'extra_filter': '&kind=rack',
                    'count': counts['rack'],
                },
                {
                    'label': 'Total',
                    'filter_field': 'manufacturer_id',
                    'count': sum(counts.values()),
                },
            ],
        }
        return self.render(
            'netbox_assets/inc/asset_stats_counts.html', extra_context=context
        )


class SiteAssetCounts(AssetLocationCounts):
    models = ['dcim.site']
    location_type = 'site'


class LocationAssetCounts(AssetLocationCounts):
    models = ['dcim.location']
    location_type = 'location'


class RackAssetCounts(PluginTemplateExtension):
    # rack cannot have stored assets so we can't use AssetLocationStats
    models = ['dcim.rack']

    def right_page(self):
        object = self.context.get('object')
        user = self.context['request'].user
        assets_qs = Asset.objects.restrict(user, 'view')
        assets_qs = query_located(assets_qs, 'rack', [object.pk])
        context = {
            'asset_stats': [
                {
                    'label': 'Installed',
                    'filter_field': 'installed_rack_id',
                    'count': assets_qs.count(),
                },
            ],
        }
        return self.render(
            'netbox_assets/inc/asset_stats_counts.html', extra_context=context
        )


class TenantAssetCounts(PluginTemplateExtension):
    models = ['tenancy.tenant']

    def right_page(self):
        object = self.context.get('object')
        user = self.context['request'].user
        context = {
            'asset_stats': [
                {
                    'label': 'Assigned',
                    'filter_field': 'tenant_id',
                    'count': Asset.objects.restrict(user, 'view')
                    .filter(tenant=object)
                    .count(),
                },
                {
                    'label': 'Owned',
                    'filter_field': 'owning_tenant_id',
                    'count': Asset.objects.restrict(user, 'view')
                    .filter(owning_tenant=object)
                    .count(),
                },
            ],
        }
        return self.render(
            'netbox_assets/inc/asset_stats_counts.html', extra_context=context
        )


class ContactAssetCounts(PluginTemplateExtension):
    models = ['tenancy.contact']

    def right_page(self):
        object = self.context.get('object')
        user = self.context['request'].user
        context = {
            'asset_stats': [
                {
                    'label': 'Assigned',
                    'filter_field': 'contact_id',
                    'count': Asset.objects.restrict(user, 'view')
                    .filter(contact=object)
                    .count(),
                },
            ],
        }
        return self.render(
            'netbox_assets/inc/asset_stats_counts.html', extra_context=context
        )


template_extensions = (
    DeviceAssetInfo,
    ModuleAssetInfo,
    RackAssetInfo,
    ManufacturerAssetCounts,
    SiteAssetCounts,
    LocationAssetCounts,
    RackAssetCounts,
    TenantAssetCounts,
    ContactAssetCounts,
)
