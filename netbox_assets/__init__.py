from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from netbox.plugins import PluginConfig

from .version import __version__

# Plugins that cannot be enabled together with netbox-assets. They define the
# same reverse relations on NetBox core models (e.g. Device.assigned_asset) and
# the same GraphQL type names, so NetBox would fail with confusing errors.
INCOMPATIBLE_PLUGINS = ('netbox_inventory',)


class NetBoxAssetsConfig(PluginConfig):
    name = 'netbox_assets'
    verbose_name = 'NetBox Assets'
    version = __version__
    description = (
        'Simple asset tracking for NetBox. A stripped-down fork of netbox-inventory.'
    )
    author = 'Maksym Ototiuk'
    author_email = 'pypi@masik.slmail.me'
    base_url = 'assets'
    min_version = '4.7.1'
    default_settings = {
        'used_status_name': 'used',
        'used_additional_status_names': [],
        'stored_status_name': 'stored',
        'stored_additional_status_names': [
            'retired',
        ],
        'sync_hardware_serial_asset_tag': False,
        'asset_import_create_device_type': False,
        'asset_import_create_module_type': False,
        'asset_import_create_rack_type': False,
        'asset_import_create_tenant': False,
        'asset_custom_fields_search_filters': {},
    }

    def ready(self):
        conflicts = [name for name in INCOMPATIBLE_PLUGINS if apps.is_installed(name)]
        if conflicts:
            raise ImproperlyConfigured(
                f'netbox_assets cannot be enabled together with: {", ".join(conflicts)}. '
                f'Remove one of the plugins from PLUGINS in configuration.py.'
            )
        super().ready()
        from . import signals  # noqa: F401


config = NetBoxAssetsConfig
