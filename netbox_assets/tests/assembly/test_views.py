from django.test import override_settings
from django.urls import reverse

from dcim.models import Interface, Module, ModuleBay
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

    PRIMARY_HELP = 'Primary end of the cable assembly.'
    SIDE_B_WARNING = 'There is no side B module type with profile'

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
        module = self.create_module(self.device2, 1, self.breakout_b_type)
        AssetModuleEnd.objects.create(asset=self.breakout, module=module, label='B1')
        response = self.client.get(self.breakout.get_absolute_url())
        self.assertHttpStatus(response, 200)
        content = response.content.decode()
        self.assertIn('Assembly Ends', content)
        self.assertIn('Uninstall', content)
        # three side B ends are not installed yet
        self.assertEqual(content.count('Not installed'), 3)
        self.assertIn('label=B4', content)
        self.assertIn('Port 1', content)
        # Primary End row and Primary column, Make primary button of B1
        self.assertEqual(content.count(self.PRIMARY_HELP), 2)
        self.assertEqual(content.count('Make primary end:'), 1)
        self.assertNotIn(self.SIDE_B_WARNING, content)

    def test_asset_page_without_side_b_module_type(self):
        asset = self.create_other_breakout()
        response = self.client.get(asset.get_absolute_url())
        self.assertHttpStatus(response, 200)
        content = response.content.decode()
        self.assertIn(self.SIDE_B_WARNING, content)
        self.assertIn('Create Module Type', content)

    def test_end_page(self):
        module = self.create_module(self.device1, 1, self.breakout_a_type)
        end = AssetModuleEnd.objects.create(
            asset=self.breakout, module=module, label='A'
        )
        response = self.client.get(end.get_absolute_url())
        self.assertHttpStatus(response, 200)
        self.assertIn(self.PRIMARY_HELP, response.content.decode())

    def test_module_page(self):
        module = self.create_module(self.device1, 1, self.breakout_a_type)
        AssetModuleEnd.objects.create(asset=self.breakout, module=module, label='A')
        response = self.client.get(module.get_absolute_url())
        self.assertHttpStatus(response, 200)
        content = response.content.decode()
        self.assertIn('Cable Assembly', content)
        self.assertIn(self.PRIMARY_HELP, content)

    def test_install_form(self):
        url = reverse('plugins:netbox_assets:assetmoduleend_add')
        response = self.client.get(f'{url}?asset={self.breakout.pk}&label=B2')
        self.assertHttpStatus(response, 200)
        content = response.content.decode()
        # module type of side B ends is preselected
        self.assertRegex(content, rf'value="{self.breakout_b_type.pk}"\s+selected')
        # help text of the primary end
        self.assertIn('<code>sync_hardware_serial_asset_tag</code>', content)
        self.assertNotIn(self.SIDE_B_WARNING, content)

    def test_install_form_without_side_b_module_type(self):
        asset = self.create_other_breakout()
        url = reverse('plugins:netbox_assets:assetmoduleend_add')
        response = self.client.get(f'{url}?asset={asset.pk}&label=B2')
        self.assertHttpStatus(response, 200)
        content = response.content.decode()
        self.assertIn(self.SIDE_B_WARNING, content)
        self.assertIn('Create a side B module type', content)
        # no warning for the side A end
        response = self.client.get(f'{url}?asset={asset.pk}&label=A')
        self.assertNotIn(self.SIDE_B_WARNING, response.content.decode())

    def test_side_b_module_type_add_form(self):
        # the NetBox module type form is prefilled from the asset's module type
        response = self.client.get(self.breakout.get_side_b_module_type_add_url())
        self.assertHttpStatus(response, 200)
        content = response.content.decode()
        self.assertRegex(content, rf'value="{self.breakout_profile.pk}"\s+selected')
        self.assertRegex(content, r'value="B"\s+selected')
        self.assertIn(
            'name="attr_cable_type" value="Direct Attach Copper (Passive)"', content
        )
        self.assertIn('name="attr_length" value="1"', content)

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

    def post_install(self, bay, label='B1'):
        return self.client.post(
            reverse('plugins:netbox_assets:assetmoduleend_add'),
            {
                'asset': self.breakout.pk,
                'label': label,
                'device': self.device2.pk,
                'module_bay': bay.pk,
                'module_type': self.breakout_b_type.pk,
            },
        )

    def test_install_interface_name_exists(self):
        # the module would create interface "Port 1" ("Port {module}")
        Interface.objects.create(
            device=self.device2, name='Port 1', type='10gbase-x-sfpp'
        )
        response = self.post_install(self.get_bay(self.device2, 1))
        self.assertHttpStatus(response, 200)
        self.assertIn(
            'Cannot create module: device switch2 already has interface Port 1. '
            '{module} in the component names of module type BRK-1M-B is the '
            'position of the module bay (&quot;1&quot;).',
            response.content.decode(),
        )
        self.assertFalse(AssetModuleEnd.objects.exists())
        self.assertFalse(Module.objects.exists())

    def test_install_module_bay_without_position(self):
        bay = ModuleBay.objects.create(device=self.device2, name='Bay X')
        response = self.post_install(bay)
        self.assertHttpStatus(response, 200)
        self.assertIn('module bay Bay X has no position', response.content.decode())
        self.assertFalse(Module.objects.exists())

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
