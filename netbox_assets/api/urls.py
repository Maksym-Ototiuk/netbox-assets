from netbox.api.routers import NetBoxRouter

from . import views

app_name = 'netbox_assets'

router = NetBoxRouter()
router.APIRootView = views.NetBoxAssetsRootView

# Assets
router.register('assets', views.AssetViewSet)
router.register('asset-roles', views.AssetRoleViewSet)
router.register('assembly-ends', views.AssetModuleEndViewSet)

# NetBox devices and modules with an additional has_asset_assigned filter
# (used by the asset assignment forms)
router.register('dcim/devices', views.DeviceAssetViewSet)
router.register('dcim/modules', views.ModuleAssetViewSet)

urlpatterns = router.urls
