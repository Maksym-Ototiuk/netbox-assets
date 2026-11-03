from rest_framework.routers import APIRootView

from dcim.api.views import DeviceViewSet, ModuleViewSet
from netbox.api.viewsets import NetBoxModelViewSet

from .. import filtersets, models
from .serializers import *

__all__ = (
    'AssetModuleEndViewSet',
    'AssetRoleViewSet',
    'AssetViewSet',
    'DeviceAssetViewSet',
    'ModuleAssetViewSet',
    'NetBoxAssetsRootView',
)


class NetBoxAssetsRootView(APIRootView):
    def get_view_name(self):
        return 'Assets'


#
# Asset roles
#


class AssetRoleViewSet(NetBoxModelViewSet):
    # Asset counts include assets of all child roles (cumulative=True)
    queryset = models.AssetRole.objects.add_related_count(
        models.AssetRole.objects.all(),
        models.Asset,
        'role',
        'asset_count',
        cumulative=True,
    ).prefetch_related('tags')
    serializer_class = AssetRoleSerializer
    filterset_class = filtersets.AssetRoleFilterSet


#
# Assets
#


class AssetViewSet(NetBoxModelViewSet):
    queryset = models.Asset.objects.prefetch_related(
        'device_type',
        'device',
        'module_type__profile',
        'module',
        'assembly_cable',
        'rack_type',
        'rack',
        'role',
        'storage_location',
        'tags',
    )
    serializer_class = AssetSerializer
    filterset_class = filtersets.AssetFilterSet


class AssetModuleEndViewSet(NetBoxModelViewSet):
    queryset = models.AssetModuleEnd.objects.select_related(
        'asset__module_type__manufacturer',
        'asset__module_type__profile',
        'module__device',
        'module__module_bay',
        'module__module_type__manufacturer',
    ).prefetch_related('tags')
    serializer_class = AssetModuleEndSerializer
    filterset_class = filtersets.AssetModuleEndFilterSet


#
# NetBox devices and modules with an additional has_asset_assigned filter
#


class DeviceAssetViewSet(DeviceViewSet):
    """
    Adds option to filter on asset assignment
    """

    filterset_class = filtersets.DeviceAssetFilterSet


class ModuleAssetViewSet(ModuleViewSet):
    """
    Adds option to filter on asset assignment
    """

    filterset_class = filtersets.ModuleAssetFilterSet
