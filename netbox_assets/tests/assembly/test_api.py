from rest_framework import status

from core.models import ObjectType
from users.models import ObjectPermission
from utilities.testing import APIViewTestCases

from netbox_assets.models import Asset, AssetModuleEnd
from netbox_assets.tests.assembly.utils import AssemblyFixtures
from netbox_assets.tests.custom import APITestCase


class AssetModuleEndTest(
    AssemblyFixtures, APITestCase, APIViewTestCases.APIViewTestCase
):
    """
    REST API and GraphQL tests for cable assembly ends
    """

    model = AssetModuleEnd
    brief_fields = ['display', 'id', 'is_primary', 'label', 'url']
    user_permissions = ('netbox_assets.view_asset', 'dcim.view_module')
    update_data = {
        'label': 'SFP+ B',
    }
    bulk_update_data = {
        'label': 'SFP+ B',
    }

    @classmethod
    def setUpTestData(cls):
        cls.create_assembly_fixtures()
        assets = [cls.create_assembly(serial=f'DAC00{i}') for i in range(1, 7)]
        for i in range(3):
            AssetModuleEnd.objects.create(
                asset=assets[i],
                module=cls.create_module(cls.device1, i + 1, cls.dac_type),
                label='SFP+ A',
            )
        cls.create_data = [
            {
                'asset': assets[i + 3].pk,
                'module': cls.create_module(cls.device2, i + 1, cls.dac_type).pk,
                'label': label,
            }
            # the end is chosen automatically if the label is empty
            for i, label in enumerate(('SFP+ A', 'SFP+ B', ''))
        ]

    def test_create_object(self):
        super().test_create_object()
        end = AssetModuleEnd.objects.get(module_id=self.create_data[0]['module'])
        self.assertEqual(end.asset.status, 'used')
        self.assertTrue(end.is_primary)

    def test_side_in_response(self):
        self.add_permissions('netbox_assets.view_assetmoduleend')
        end = AssetModuleEnd.objects.first()
        response = self.client.get(self._get_detail_url(end), **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['side'], 'A')
        self.assertEqual(response.data['label'], 'SFP+ A')

    def test_invalid_module_type(self):
        self.add_permissions('netbox_assets.add_assetmoduleend')
        asset = self.create_assembly(serial='DAC100')
        module = self.create_module(self.device2, 6, self.plain_module_type)
        data = {'asset': asset.pk, 'module': module.pk, 'label': 'SFP+ A'}
        response = self.client.post(
            self._get_list_url(), data, format='json', **self.header
        )
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)


class AssemblyAssetAPITest(AssemblyFixtures, APITestCase):
    """
    Cable assemblies in the assets REST API
    """

    model = Asset

    def setUp(self):
        super().setUp()
        self.create_assembly_fixtures()
        obj_perm = ObjectPermission(
            name='Test permission', actions=['view', 'add', 'change']
        )
        obj_perm.save()
        obj_perm.users.add(self.user)
        obj_perm.object_types.add(ObjectType.objects.get_for_model(Asset))

    def test_is_assembly(self):
        assembly = self.create_assembly()
        plain = Asset.objects.create(
            module_type=self.plain_module_type, status='stored'
        )
        response = self.client.get(self._get_detail_url(assembly), **self.header)
        self.assertTrue(response.data['is_assembly'])
        response = self.client.get(self._get_detail_url(plain), **self.header)
        self.assertFalse(response.data['is_assembly'])

    def test_assign_module_to_assembly(self):
        assembly = self.create_assembly()
        module = self.create_module(self.device1, 1, self.dac_type)
        response = self.client.patch(
            self._get_detail_url(assembly),
            {'module': module.pk},
            format='json',
            **self.header,
        )
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Install its ends instead', str(response.data))

    def test_filter_is_assembly(self):
        assembly = self.create_assembly()
        Asset.objects.create(module_type=self.plain_module_type, status='stored')
        response = self.client.get(
            f'{self._get_list_url()}?is_assembly=true', **self.header
        )
        self.assertEqual([a['id'] for a in response.data['results']], [assembly.pk])
