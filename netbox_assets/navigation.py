from netbox.plugins import (
    PluginMenu,
    PluginMenuButton,
    PluginMenuItem,
    get_plugin_config,
)

#
# Assets
#

inventoryitemgroup_buttons = [
    PluginMenuButton(
        link='plugins:netbox_assets:inventoryitemgroup_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_assets.add_inventoryitemgroup'],
    ),
    PluginMenuButton(
        link='plugins:netbox_assets:inventoryitemgroup_bulk_import',
        title='Import',
        icon_class='mdi mdi-upload',
        permissions=['netbox_assets.add_inventoryitemgroup'],
    ),
]

inventoryitemtype_buttons = [
    PluginMenuButton(
        link='plugins:netbox_assets:inventoryitemtype_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_assets.add_inventoryitemtype'],
    ),
    PluginMenuButton(
        link='plugins:netbox_assets:inventoryitemtype_bulk_import',
        title='Import',
        icon_class='mdi mdi-upload',
        permissions=['netbox_assets.add_inventoryitemtype'],
    ),
]

asset_buttons = [
    PluginMenuButton(
        link='plugins:netbox_assets:asset_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_assets.add_asset'],
    ),
    PluginMenuButton(
        link='plugins:netbox_assets:asset_bulk_import',
        title='Import',
        icon_class='mdi mdi-upload',
        permissions=['netbox_assets.add_asset'],
    ),
]

assetrole_buttons = [
    PluginMenuButton(
        link='plugins:netbox_assets:assetrole_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_assets.add_assetrole'],
    ),
    PluginMenuButton(
        link='plugins:netbox_assets:assetrole_bulk_import',
        title='Import',
        icon_class='mdi mdi-upload',
        permissions=['netbox_assets.add_assetrole'],
    ),
]

assets_items = (
    PluginMenuItem(
        link='plugins:netbox_assets:asset_list',
        link_text='Assets',
        permissions=['netbox_assets.view_asset'],
        buttons=asset_buttons,
    ),
    PluginMenuItem(
        link='plugins:netbox_assets:assetrole_list',
        link_text='Asset Roles',
        permissions=['netbox_assets.view_assetrole'],
        buttons=assetrole_buttons,
    ),
    PluginMenuItem(
        link='plugins:netbox_assets:inventoryitemtype_list',
        link_text='Inventory Item Types',
        permissions=['netbox_assets.view_inventoryitemtype'],
        buttons=inventoryitemtype_buttons,
    ),
    PluginMenuItem(
        link='plugins:netbox_assets:inventoryitemgroup_list',
        link_text='Inventory Item Groups',
        permissions=['netbox_assets.view_inventoryitemgroup'],
        buttons=inventoryitemgroup_buttons,
    ),
)


#
# Deliveries
#

supplier_buttons = [
    PluginMenuButton(
        link='plugins:netbox_assets:supplier_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_assets.add_supplier'],
    ),
    PluginMenuButton(
        link='plugins:netbox_assets:supplier_bulk_import',
        title='Import',
        icon_class='mdi mdi-upload',
        permissions=['netbox_assets.add_supplier'],
    ),
]

purchase_buttons = [
    PluginMenuButton(
        link='plugins:netbox_assets:purchase_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_assets.add_purchase'],
    ),
    PluginMenuButton(
        link='plugins:netbox_assets:purchase_bulk_import',
        title='Import',
        icon_class='mdi mdi-upload',
        permissions=['netbox_assets.add_purchase'],
    ),
]

delivery_buttons = [
    PluginMenuButton(
        link='plugins:netbox_assets:delivery_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_assets.add_delivery'],
    ),
    PluginMenuButton(
        link='plugins:netbox_assets:delivery_bulk_import',
        title='Import',
        icon_class='mdi mdi-upload',
        permissions=['netbox_assets.add_delivery'],
    ),
]

deliveries_items = (
    PluginMenuItem(
        link='plugins:netbox_assets:supplier_list',
        link_text='Suppliers',
        permissions=['netbox_assets.view_supplier'],
        buttons=supplier_buttons,
    ),
    PluginMenuItem(
        link='plugins:netbox_assets:purchase_list',
        link_text='Purchases',
        permissions=['netbox_assets.view_purchase'],
        buttons=purchase_buttons,
    ),
    PluginMenuItem(
        link='plugins:netbox_assets:delivery_list',
        link_text='Deliveries',
        permissions=['netbox_assets.view_delivery'],
        buttons=delivery_buttons,
    ),
)


#
# Audit
#

audit_admin_items = (
    PluginMenuItem(
        link='plugins:netbox_assets:auditflow_list',
        link_text='Flows',
        permissions=['netbox_assets.view_auditflow'],
        buttons=[
            PluginMenuButton(
                link='plugins:netbox_assets:auditflow_add',
                title='Add',
                icon_class='mdi mdi-plus-thick',
                permissions=['netbox_assets.add_auditflow'],
            ),
            PluginMenuButton(
                link='plugins:netbox_assets:auditflow_bulk_import',
                title='Import',
                icon_class='mdi mdi-upload',
                permissions=['netbox_assets.add_auditflow'],
            ),
        ],
    ),
    PluginMenuItem(
        link='plugins:netbox_assets:auditflowpage_list',
        link_text='Flow Pages',
        permissions=['netbox_assets.view_auditflowpage'],
        buttons=[
            PluginMenuButton(
                link='plugins:netbox_assets:auditflowpage_add',
                title='Add',
                icon_class='mdi mdi-plus-thick',
                permissions=['netbox_assets.add_auditflowpage'],
            ),
            PluginMenuButton(
                link='plugins:netbox_assets:auditflowpage_bulk_import',
                title='Import',
                icon_class='mdi mdi-upload',
                permissions=['netbox_assets.add_auditflowpage'],
            ),
        ],
    ),
    PluginMenuItem(
        link='plugins:netbox_assets:audittrail_list',
        link_text='Audit Trails',
        permissions=['netbox_assets.view_audittrail'],
        buttons=[
            PluginMenuButton(
                link='plugins:netbox_assets:audittrail_bulk_import',
                title='Import',
                icon_class='mdi mdi-upload',
                permissions=['netbox_assets.add_audittrail'],
            ),
        ],
    ),
    PluginMenuItem(
        link='plugins:netbox_assets:audittrailsource_list',
        link_text='Audit Trail Sources',
        permissions=['netbox_assets.view_audittrailsource'],
        buttons=[
            PluginMenuButton(
                link='plugins:netbox_assets:audittrailsource_add',
                title='Add',
                icon_class='mdi mdi-plus-thick',
                permissions=['netbox_assets.add_audittrailsource'],
            ),
            PluginMenuButton(
                link='plugins:netbox_assets:audittrailsource_bulk_import',
                title='Import',
                icon_class='mdi mdi-upload',
                permissions=['netbox_assets.add_audittrailsource'],
            ),
        ],
    ),
)

#
# Menu
#

if get_plugin_config('netbox_assets', 'top_level_menu'):
    # add a top level entry
    menu = PluginMenu(
        label='Inventory',
        groups=(
            ('Asset Management', assets_items),
            ('Deliveries', deliveries_items),
            ('Audit', audit_admin_items),
        ),
        icon_class='mdi mdi-clipboard-text-multiple-outline',
    )
else:
    # display under plugins
    menu_items = assets_items + deliveries_items + audit_admin_items
