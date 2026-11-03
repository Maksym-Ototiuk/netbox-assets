from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem

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

assetmoduleend_buttons = [
    PluginMenuButton(
        link='plugins:netbox_assets:assetmoduleend_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_assets.add_assetmoduleend'],
    ),
    PluginMenuButton(
        link='plugins:netbox_assets:assetmoduleend_bulk_import',
        title='Import',
        icon_class='mdi mdi-upload',
        permissions=['netbox_assets.add_assetmoduleend'],
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
        link='plugins:netbox_assets:assetmoduleend_list',
        link_text='Assembly Ends',
        permissions=['netbox_assets.view_assetmoduleend'],
        buttons=assetmoduleend_buttons,
    ),
    PluginMenuItem(
        link='plugins:netbox_assets:assetrole_list',
        link_text='Asset Roles',
        permissions=['netbox_assets.view_assetrole'],
        buttons=assetrole_buttons,
    ),
)

# Top-level "Assets" menu with a single group. NetBox renders group labels in
# upper case, so the group header is shown as "ASSETS".
menu = PluginMenu(
    label='Assets',
    groups=(('Assets', assets_items),),
    icon_class='mdi mdi-clipboard-text-multiple-outline',
)
