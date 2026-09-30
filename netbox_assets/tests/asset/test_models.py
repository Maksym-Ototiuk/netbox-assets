from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from dcim.models import (
    Device,
    DeviceRole,
    DeviceType,
    Manufacturer,
    ModuleType,
    Site,
)
from utilities.exceptions import AbortRequest

from netbox_assets.models import Asset
from netbox_assets.tests.settings import CONFIG_SYNC_OFF, CONFIG_SYNC_ON


class TestAssetModel(TestCase):
    def setUp(self):
        self.site1 = Site.objects.create(
            name='site1',
            slug='site1',
            status='active',
        )
        self.manufacturer1 = Manufacturer.objects.create(
            name='manufacturer1',
            slug='manufacturer1',
        )
        self.device_type1 = DeviceType.objects.create(
            manufacturer=self.manufacturer1, model='device_type1', slug='device_type1'
        )
        self.module_type1 = ModuleType.objects.create(
            manufacturer=self.manufacturer1, model='module_type1'
        )
        self.role1 = DeviceRole.objects.create(name='role1', slug='role1')
        self.asset1 = Asset.objects.create(
            asset_tag='asset1',
            serial='asset1',
            status='stored',
            device_type=self.device_type1,
        )
        self.device1 = Device.objects.create(
            site=self.site1,
            status='active',
            device_type=self.device_type1,
            role=self.role1,
            name='device1',
        )
        self.device2 = Device.objects.create(
            site=self.site1,
            status='active',
            device_type=self.device_type1,
            role=self.role1,
            name='device2',
        )

    def test_str(self):
        # "<manufacturer> <model>" without a name, "<manufacturer> <model> <name>" with it
        self.assertEqual(str(self.asset1), 'manufacturer1 device_type1')
        self.asset1.name = 'edge-01'
        self.assertEqual(str(self.asset1), 'manufacturer1 device_type1 edge-01')
        module_asset = Asset(module_type=self.module_type1, status='stored')
        self.assertEqual(str(module_asset), 'manufacturer1 module_type1')

    def test_hardware_type_required(self):
        asset = Asset(status='stored')
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_only_one_hardware_type(self):
        self.asset1.module_type = self.module_type1
        with self.assertRaises(ValidationError):
            self.asset1.full_clean()

    @override_settings(PLUGINS_CONFIG=CONFIG_SYNC_ON)
    def test_update_hardware_used_on(self):
        # assign device to asset
        self.asset1.snapshot()
        self.asset1.device = self.device1
        self.asset1.full_clean()
        self.asset1.save()
        self.assertEqual(self.device1.serial, self.asset1.serial)
        self.assertEqual(self.device1.asset_tag, self.asset1.asset_tag)

        # update asset serial updates device serial
        self.asset1.snapshot()
        self.asset1.serial = 'changed'
        self.asset1.full_clean()
        self.asset1.save()
        self.assertEqual(self.device1.serial, 'changed')

        # update device serial not allowed
        self.device1.snapshot()
        self.device1.serial = 'notallowed'
        self.device1.full_clean()
        with self.assertRaises(AbortRequest):
            self.device1.save()

        # assign different device
        self.assertEqual(self.asset1.device, self.device1)
        self.asset1.snapshot()
        self.asset1.device = self.device2
        self.asset1.full_clean()
        self.asset1.save()
        self.device1.refresh_from_db()
        self.device2.refresh_from_db()
        self.assertEqual(self.device1.serial, '')
        self.assertEqual(self.device1.asset_tag, None)
        self.assertEqual(self.device2.serial, self.asset1.serial)
        self.assertEqual(self.device2.asset_tag, self.asset1.asset_tag)

        # unassign device from asset
        self.asset1.snapshot()
        self.asset1.device = None
        self.asset1.full_clean()
        self.asset1.save()
        self.device1.refresh_from_db()
        self.device2.refresh_from_db()
        self.assertEqual(self.device1.serial, '')
        self.assertEqual(self.device1.asset_tag, None)
        self.assertEqual(self.device2.serial, '')
        self.assertEqual(self.device2.asset_tag, None)

    @override_settings(PLUGINS_CONFIG=CONFIG_SYNC_OFF)
    def test_update_hardware_used_off(self):
        # assign device to asset
        self.asset1.snapshot()
        self.asset1.device = self.device1
        self.asset1.full_clean()
        self.asset1.save()
        self.assertEqual(self.device1.serial, '')
        self.assertEqual(self.device1.asset_tag, None)

        # update asset serial does not update device serial
        self.asset1.snapshot()
        self.asset1.serial = 'changed'
        self.asset1.full_clean()
        self.asset1.save()
        self.assertEqual(self.device1.serial, '')

        # update device serial is allowed
        self.device1.snapshot()
        self.device1.serial = 'allowed'
        self.device1.full_clean()
        self.device1.save()
        self.device1.refresh_from_db()
        self.assertEqual(self.device1.serial, 'allowed')

        # assign different device
        self.assertEqual(self.asset1.device, self.device1)
        self.asset1.snapshot()
        self.asset1.device = self.device2
        self.asset1.full_clean()
        self.asset1.save()
        self.device1.refresh_from_db()
        self.device2.refresh_from_db()
        self.assertEqual(self.device1.serial, 'allowed')
        self.assertEqual(self.device1.asset_tag, None)
        self.assertEqual(self.device2.serial, '')
        self.assertEqual(self.device2.asset_tag, None)

        # unassign device from asset
        self.asset1.snapshot()
        self.asset1.device = None
        self.asset1.full_clean()
        self.asset1.save()
        self.device1.refresh_from_db()
        self.device2.refresh_from_db()
        self.assertEqual(self.device1.serial, 'allowed')
        self.assertEqual(self.device1.asset_tag, None)
        self.assertEqual(self.device2.serial, '')
        self.assertEqual(self.device2.asset_tag, None)

    def test_update_status(self):
        self.asset1.snapshot()
        self.asset1.device = self.device1
        self.asset1.full_clean()
        self.asset1.save()
        self.asset1.refresh_from_db()
        self.assertEqual(self.asset1.status, 'used')
        self.asset1.snapshot()
        self.asset1.device = None
        self.asset1.full_clean()
        self.asset1.save()
        self.assertEqual(self.asset1.status, 'stored')

    def test_status_device_deleted(self):
        self.asset1.snapshot()
        self.asset1.device = self.device1
        self.asset1.full_clean()
        self.asset1.save()
        self.assertEqual(self.asset1.status, 'used')
        self.device1.delete()
        self.asset1.refresh_from_db()
        self.assertEqual(self.asset1.status, 'stored')
