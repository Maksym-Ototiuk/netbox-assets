from django.urls import include, path

from utilities.urls import get_model_urls

from . import views

urlpatterns = (
    # InventoryItemGroups
    path(
        'inventory-item-groups/',
        include(get_model_urls('netbox_assets', 'inventoryitemgroup', detail=False)),
    ),
    path(
        'inventory-item-groups/<int:pk>/',
        include(get_model_urls('netbox_assets', 'inventoryitemgroup')),
    ),
    # InventoryItemTypes
    path(
        'inventory-item-types/',
        include(get_model_urls('netbox_assets', 'inventoryitemtype', detail=False)),
    ),
    path(
        'inventory-item-types/<int:pk>/',
        include(get_model_urls('netbox_assets', 'inventoryitemtype')),
    ),
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
        'assets/inventory-item/create/',
        views.AssetInventoryItemCreateView.as_view(),
        name='asset_inventoryitem_create',
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
        'assets/inventoryitem/<int:pk>/reassign/',
        views.AssetInventoryItemReassignView.as_view(),
        name='asset_inventoryitem_reassign',
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
    # Suppliers
    path(
        'suppliers/',
        include(get_model_urls('netbox_assets', 'supplier', detail=False)),
    ),
    path(
        'suppliers/<int:pk>/',
        include(get_model_urls('netbox_assets', 'supplier')),
    ),
    # Purchases
    path(
        'purchases/',
        include(get_model_urls('netbox_assets', 'purchase', detail=False)),
    ),
    path(
        'purchases/<int:pk>/',
        include(get_model_urls('netbox_assets', 'purchase')),
    ),
    # Deliveries
    path(
        'deliveries/',
        include(get_model_urls('netbox_assets', 'delivery', detail=False)),
    ),
    path(
        'deliveries/<int:pk>/',
        include(get_model_urls('netbox_assets', 'delivery')),
    ),
    # AuditFlows (for clarity above AuditFlowPages)
    path(
        'audit-flows/',
        include(get_model_urls('netbox_assets', 'auditflow', detail=False)),
    ),
    path(
        'audit-flows/<int:pk>/',
        include(get_model_urls('netbox_assets', 'auditflow')),
    ),
    # AuditFlowPages
    path(
        'audit-flowpages/',
        include(get_model_urls('netbox_assets', 'auditflowpage', detail=False)),
    ),
    path(
        'audit-flowpages/<int:pk>/',
        include(get_model_urls('netbox_assets', 'auditflowpage')),
    ),
    # AuditFlowPageAssignments
    path(
        'audit-flowpage-assignments/',
        include(
            get_model_urls('netbox_assets', 'auditflowpageassignment', detail=False)
        ),
    ),
    path(
        'audit-flowpage-assignments/<int:pk>/',
        include(get_model_urls('netbox_assets', 'auditflowpageassignment')),
    ),
    # AuditTrailSources
    path(
        'audit-trail-sources/',
        include(get_model_urls('netbox_assets', 'audittrailsource', detail=False)),
    ),
    path(
        'audit-trail-sources/<int:pk>/',
        include(get_model_urls('netbox_assets', 'audittrailsource')),
    ),
    # AuditTrails
    path(
        'audit-trails/',
        include(get_model_urls('netbox_assets', 'audittrail', detail=False)),
    ),
    path(
        'audit-trails/<int:pk>/',
        include(get_model_urls('netbox_assets', 'audittrail')),
    ),
)
