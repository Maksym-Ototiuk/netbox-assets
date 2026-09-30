from django.urls import include, path

from utilities.urls import get_model_urls

from . import views

urlpatterns = (
    # Assets
    path(
        'assets/',
        include(get_model_urls('netbox_assets', 'asset', detail=False)),
    ),
    path(
        'assets/<int:pk>/',
        include(get_model_urls('netbox_assets', 'asset')),
    ),
    path(
        'assets/<int:pk>/assign/',
        views.AssetAssignView.as_view(),
        name='asset_assign',
    ),
    path(
        'assets/device/create/',
        views.AssetDeviceCreateView.as_view(),
        name='asset_device_create',
    ),
    path(
        'assets/module/create/',
        views.AssetModuleCreateView.as_view(),
        name='asset_module_create',
    ),
    path(
        'assets/rack/create/',
        views.AssetRackCreateView.as_view(),
        name='asset_rack_create',
    ),
    path(
        'assets/device/<int:pk>/reassign/',
        views.AssetDeviceReassignView.as_view(),
        name='asset_device_reassign',
    ),
    path(
        'assets/module/<int:pk>/reassign/',
        views.AssetModuleReassignView.as_view(),
        name='asset_module_reassign',
    ),
    path(
        'assets/rack/<int:pk>/reassign/',
        views.AssetRackReassignView.as_view(),
        name='asset_rack_reassign',
    ),
    # Asset Roles
    path(
        'asset-roles/',
        include(get_model_urls('netbox_assets', 'assetrole', detail=False)),
    ),
    path(
        'asset-roles/<int:pk>/',
        include(get_model_urls('netbox_assets', 'assetrole')),
    ),
)
