from django.test import override_settings
from django.urls import reverse

from dcim.models import Module
from utilities.testing import TestCase, ViewTestCases, create_tags

from netbox_assets.models import AssetModuleEnd
from netbox_assets.tests.assembly.utils import AssemblyFixtures
from netbox_assets.tests.custom import ModelViewTestCase
from netbox_assets.tests.settings import CONFIG_SYNC_ON


class AssetModuleEndTestCase(
    AssemblyFixtures,
    ModelViewTestCase,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkImportObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    """
    UI view tests for cable assembly ends
    """

    model = AssetModuleEnd

    @classmethod
    def setUpTestData(cls):
        cls.create_assembly_fixtures()
        assets = [cls.create_assembly(serial=f'DAC00{i}') for i in range(1, 8)]
        ends = [
            AssetModuleEnd.objects.create(
                asset=assets[i],
                module=cls.create_module(cls.device1, i + 1, cls.dac_type),
                label='SFP+ A',
            )
            for i in range(3)
        ]
        # modules for the bulk import and the form
        for bay in range(1, 5):
            cls.create_module(cls.device2, bay, cls.dac_type)
        tags = create_tags('Alpha', 'Bravo', 'Charlie')

        cls.form_data = {
            'asset': assets[3].pk,
            'label': 'SFP+ B',
            'device': cls.device2.pk,
            'module_bay': cls.get_bay(cls.device2, 4).pk,
            'is_primary': True,
            'tags': [t.pk for t in tags],
        }
        cls.csv_data = (
            'asset,device,module_bay,label',
            f'{assets[4].pk},switch2,Bay 1,SFP+ A',
            f'{assets[5].pk},switch2,Bay 2,SFP+ B',
            f'{assets[6].pk},switch2,Bay 3,',
        )
        cls.csv_update_data = (
            'id,label',
            *(f'{end.pk},SFP+ B' for end in ends),
        )


class AssemblyViewsTestCase(AssemblyFixtures, TestCase):
    """
    Asset and module pages of cable assemblies, install and set primary actions
    """

    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.create_assembly_fixtures()
        self.breakout = self.create_assembly(
            module_type=self.breakout_a_type, serial='BRK001', asset_tag='T-BRK001'
        )

    def test_asset_page(self):
        module = self.create_module(self.device1, 1, self.breakout_a_type)
        AssetModuleEnd.objects.create(asset=self.breakout, module=module, label='A')
        response = self.client.get(self.breakout.get_absolute_url())
        self.assertHttpStatus(response, 200)
        content = response.content.decode()
        self.assertIn('Assembly Ends', content)
        self.assertIn('Uninstall', content)
        # four side B ends are not installed yet
        self.assertEqual(content.count('Not installed'), 4)
        self.assertIn('label=B4', content)
        self.assertIn('Port 1', content)

    def test_module_page(self):
        module = self.create_module(self.device1, 1, self.breakout_a_type)
        AssetModuleEnd.objects.create(asset=self.breakout, module=module, label='A')
        response = self.client.get(module.get_absolute_url())
        self.assertHttpStatus(response, 200)
        self.assertIn('Cable Assembly', response.content.decode())

    def test_install_form(self):
        url = reverse('plugins:netbox_assets:assetmoduleend_add')
        response = self.client.get(f'{url}?asset={self.breakout.pk}&label=B2')
        self.assertHttpStatus(response, 200)
        # module type of side B ends is preselected
        self.assertRegex(
            response.content.decode(),
            rf'value="{self.breakout_b_type.pk}"\s+selected',
        )

    @override_settings(PLUGINS_CONFIG=CONFIG_SYNC_ON)
    def test_install_creates_module(self):
        bay = self.get_bay(self.device2, 1)
        response = self.client.post(
            reverse('plugins:netbox_assets:assetmoduleend_add'),
            {
                'asset': self.breakout.pk,
                'label': 'B2',
                'device': self.device2.pk,
                'module_bay': bay.pk,
                'module_type': self.breakout_b_type.pk,
            },
        )
        self.assertHttpStatus(response, 302)
        module = Module.objects.get(module_bay=bay)
        self.assertEqual(module.module_type, self.breakout_b_type)
        self.assertEqual(module.serial, 'BRK001')
        self.assertEqual(module.asset_tag, 'T-BRK001')
        self.assertEqual(module.assembly_end.label, 'B2')
        self.assertEqual(module.interfaces.count(), 1)
        self.breakout.refresh_from_db()
        self.assertEqual(self.breakout.status, 'used')

    def test_install_empty_bay_requires_module_type(self):
        response = self.client.post(
            reverse('plugins:netbox_assets:assetmoduleend_add'),
            {
                'asset': self.breakout.pk,
                'label': 'A',
                'device': self.device2.pk,
                'module_bay': self.get_bay(self.device2, 1).pk,
            },
        )
        self.assertHttpStatus(response, 200)
        self.assertFalse(AssetModuleEnd.objects.exists())

    def test_set_primary(self):
        end_a = AssetModuleEnd.objects.create(
            asset=self.breakout,
            module=self.create_module(self.device1, 1, self.breakout_a_type),
            label='A',
        )
        end_b = AssetModuleEnd.objects.create(
            asset=self.breakout,
            module=self.create_module(self.device2, 1, self.breakout_b_type),
            label='B1',
        )
        url = reverse(
            'plugins:netbox_assets:assetmoduleend_set_primary', kwargs={'pk': end_b.pk}
        )
        response = self.client.post(url)
        self.assertHttpStatus(response, 302)
        end_a.refresh_from_db()
        end_b.refresh_from_db()
        self.assertTrue(end_b.is_primary)
        self.assertFalse(end_a.is_primary)

    def test_assign_redirects(self):
        url = reverse(
            'plugins:netbox_assets:asset_assign', kwargs={'pk': self.breakout.pk}
        )
        response = self.client.get(url)
        self.assertRedirects(
            response,
            f'{self.breakout.get_absolute_url()}#assembly-ends',
            fetch_redirect_response=False,
        )
