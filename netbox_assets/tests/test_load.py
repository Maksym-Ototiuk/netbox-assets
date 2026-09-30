from django.test import SimpleTestCase
from django.urls import reverse

from netbox_assets import __version__
from netbox_assets.tests.custom import APITestCase


class NetboxInventoryVersionTestCase(SimpleTestCase):
    """
    Test for netbox_assets package
    """

    def test_version(self):
        assert __version__ == '0.1.0'


class AppTest(APITestCase):
    """
    Test the availability of the plugin API root
    """

    def test_root(self):
        url = reverse('plugins-api:netbox_assets-api:api-root')
        response = self.client.get(f'{url}?format=api', **self.header)

        self.assertEqual(response.status_code, 200)
