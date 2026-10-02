from unittest import mock

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from django.urls import reverse

from netbox_assets import __version__
from netbox_assets.tests.custom import APITestCase


class NetBoxAssetsVersionTestCase(SimpleTestCase):
    """
    Test for netbox_assets package
    """

    def test_version(self):
        assert __version__ == '1.1.2'


class CoexistenceGuardTestCase(SimpleTestCase):
    """
    netbox-assets must refuse to start when netbox-inventory is installed
    """

    def test_netbox_inventory_installed(self):
        config = apps.get_app_config('netbox_assets')
        with mock.patch.object(
            apps,
            'is_installed',
            side_effect=lambda name: name == 'netbox_inventory',
        ):
            with self.assertRaisesMessage(ImproperlyConfigured, 'netbox_inventory'):
                config.ready()


class AppTest(APITestCase):
    """
    Test the availability of the plugin API root
    """

    def test_root(self):
        url = reverse('plugins-api:netbox_assets-api:api-root')
        response = self.client.get(f'{url}?format=api', **self.header)

        self.assertEqual(response.status_code, 200)
