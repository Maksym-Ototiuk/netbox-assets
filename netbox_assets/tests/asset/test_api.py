from copy import copy

from rest_framework import status

from core.models import ObjectType
from dcim.models import (
    Device,
    DeviceRole,
    DeviceType,
    Manufacturer,
    Module,
    ModuleBay,
    ModuleType,
    RackType,
    Site,
)
from users.models import ObjectPermission
from utilities.testing import APIViewTestCases, disable_warnings

from netbox_assets.models import Asset
from netbox_assets.tests.custom import APITestCase


class AssetTest(APITestCase, APIViewTestCases.APIViewTestCase):
    """
    REST API and GraphQL tests for assets
    """

    model = Asset
    brief_fields = ['description', 'display', 'id', 'name', 'serial', 'url']
    bulk_update_data = {
        'status': 'used',
    }
    bulk_update_invalid_data = {
        'status': 'invalid-status',
    }

    def _add_permission(self):
        obj_perm = ObjectPermission(
            name='Test permission', actions=['view', 'add', 'change']
        )
        obj_perm.save()
        obj_perm.users.add(self.user)
        obj_perm.object_types.add(ObjectType.objects.get_for_model(self.model))

    def _create_asset(self, data):
        response = self.client.post(
            self._get_list_url(), data, format='json', **self.header
        )
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        return self._get_queryset().get(pk=response.data['id'])

    def test_assign_device_matching_device_type(self):
        """
        assigning a device works when asset's and device's device type match
        """
        self._add_permission()
        instance = self._create_asset(self.create_data[0])
        update_data = {'device': self.device1.pk}
        response = self.client.patch(
            self._get_detail_url(instance), update_data, format='json', **self.header
        )
        self.assertHttpStatus(response, status.HTTP_200_OK)
        instance.refresh_from_db()
        self.assertEqual(instance.device, self.device1)
        self.assertEqual(instance.status, 'used')

    def test_assign_device_mismatch_device_type(self):
        """
        assigning a device fails when asset's and device's device type differ
        """
        self._add_permission()
        instance = self._create_asset(self.create_data[0])
        update_data = {'device': self.device2.pk}
        response = self.client.patch(
            self._get_detail_url(instance), update_data, format='json', **self.header
        )
        with disable_warnings('django.request'):
            self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)

    def test_assign_module_to_device_asset(self):
        """
        an asset of kind "device" cannot be assigned to a module
        """
        self._add_permission()
        instance = self._create_asset(self.create_data[0])
        update_data = {'module': self.module1.pk}
        response = self.client.patch(
            self._get_detail_url(instance), update_data, format='json', **self.header
        )
        with disable_warnings('django.request'):
            self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)

    def test_serial_asset_tag_empty(self):
        """
        empty strings for serial and asset_tag are normalized to None
        """
        self._add_permission()
        create_data = copy(self.create_data[0])
        create_data['serial'] = ''
        create_data['asset_tag'] = ''
        instance = self._create_asset(create_data)
        self.assertEqual(instance.serial, None)
        self.assertEqual(instance.asset_tag, None)

    def test_kind_and_display(self):
        """
        the read-only "kind" field and "display" name are returned
        """
        self._add_permission()
        instance = Asset.objects.get(name='Asset 1')
        response = self.client.get(self._get_detail_url(instance), **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['kind'], 'device')
        self.assertEqual(
            response.data['display'], 'Manufacturer 1 Device Type 1 Asset 1'
        )

    @classmethod
    def setUpTestData(cls):
        manufacturer = Manufacturer.objects.create(
            name='Manufacturer 1', slug='manufacturer1'
        )
        device_type1 = DeviceType.objects.create(
            model='Device Type 1', slug='devicetype1', manufacturer=manufacturer
        )
        device_type2 = DeviceType.objects.create(
            model='Device Type 2', slug='devicetype2', manufacturer=manufacturer
        )
        rack_type1 = RackType.objects.create(
            model='Rack Type 1',
            slug='racktype1',
            manufacturer=manufacturer,
            form_factor='4-post-cabinet',
        )
        module_type1 = ModuleType.objects.create(
            model='Module Type 1', manufacturer=manufacturer
        )
        site1 = Site.objects.create(name='Site 1', slug='site1')
        role1 = DeviceRole.objects.create(name='Device Role 1', slug='devicerole1')
        cls.device1 = Device.objects.create(
            name='Device 1',
            role=role1,
            device_type=device_type1,
            site=site1,
            status='active',
        )
        cls.device2 = Device.objects.create(
            name='Device 2',
            role=role1,
            device_type=device_type2,
            site=site1,
            status='active',
        )
        module_bay1 = ModuleBay.objects.create(device=cls.device1, name='Bay 1')
        cls.module1 = Module.objects.create(
            device=cls.device1, module_bay=module_bay1, module_type=module_type1
        )

        Asset.objects.create(
            name='Asset 1', serial='asset1', status='stored', device_type=device_type1
        )
        Asset.objects.create(
            name='Asset 2', serial='asset2', status='stored', device_type=device_type1
        )
        Asset.objects.create(
            name='Asset 3', serial='asset3', status='stored', rack_type=rack_type1
        )

        cls.create_data = [
            {
                'name': 'Asset 4',
                'serial': 'asset4',
                'status': 'stored',
                'device_type': device_type1.pk,
                'device': None,
            },
            {
                'name': 'Asset 5',
                'serial': 'asset5',
                'status': 'stored',
                'module_type': module_type1.pk,
                'module': None,
            },
            {
                'name': 'Asset 6',
                'serial': 'asset6',
                'status': 'stored',
                'rack_type': rack_type1.pk,
            },
        ]
