from django.contrib.contenttypes.models import ContentType
from django.test import override_settings
from django.urls import reverse

from core.choices import ObjectChangeActionChoices
from core.models import ObjectChange, ObjectType
from dcim.models import (
    Device,
    DeviceRole,
    DeviceType,
    Manufacturer,
    Module,
    ModuleBay,
    ModuleType,
    Rack,
    RackType,
    Site,
)
from users.models import ObjectPermission
from utilities.testing.utils import post_data

from netbox_assets.models import Asset
from netbox_assets.tests.custom import ModelViewTestCase
from netbox_assets.tests.settings import CONFIG_SYNC_ON


class AssetReassignBase:
    """
    Base class for tests that assign another asset to hardware
    ("Edit Assignment" on a device, module or rack page)
    """

    @override_settings(PLUGINS_CONFIG=CONFIG_SYNC_ON)
    def setUp(self):
        super().setUp()

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
            manufacturer=self.manufacturer1,
            model='module_type1',
        )
        self.role1 = DeviceRole.objects.create(name='role1', slug='role1')
        self.rack_type1 = RackType.objects.create(
            manufacturer=self.manufacturer1,
            model='rack_type1',
            slug='rack_type1',
            form_factor='4-post-cabinet',
        )
        self.device1 = Device.objects.create(
            site=self.site1,
            status='active',
            device_type=self.device_type1,
            role=self.role1,
            name='device1',
        )
        self.module_bay1 = ModuleBay.objects.create(
            device=self.device1,
            name='1',
        )
        self.module1 = Module.objects.create(
            module_bay=self.module_bay1,
            device=self.device1,
            module_type=self.module_type1,
        )
        self.rack1 = Rack.objects.create(
            site=self.site1,
            status='active',
            rack_type=self.rack_type1,
            name='rack1',
        )
        self.asset_device_old = Asset.objects.create(
            asset_tag='asset_device',
            serial='asset_device',
            status='used',
            device_type=self.device_type1,
            device=self.device1,
        )
        self.asset_module_old = Asset.objects.create(
            asset_tag='asset_module',
            serial='asset_module',
            status='used',
            module_type=self.module_type1,
            module=self.module1,
        )
        self.asset_rack_old = Asset.objects.create(
            asset_tag='asset_rack',
            serial='asset_rack',
            status='used',
            rack_type=self.rack_type1,
            rack=self.rack1,
        )
        self.asset_device_new = Asset.objects.create(
            asset_tag='asset_device2',
            serial='asset_device2',
            status='stored',
            device_type=self.device_type1,
        )
        self.asset_module_new = Asset.objects.create(
            asset_tag='asset_module2',
            serial='asset_module2',
            status='stored',
            module_type=self.module_type1,
        )
        self.asset_rack_new = Asset.objects.create(
            asset_tag='asset_rack2',
            serial='asset_rack2',
            status='stored',
            rack_type=self.rack_type1,
        )

    def _get_url(self, _, instance):
        kind = self.model._meta.model_name
        return reverse(
            f'plugins:netbox_assets:asset_{kind}_reassign',
            kwargs={'pk': self.tested_hardware.pk},
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=['*'])
    @override_settings(PLUGINS_CONFIG=CONFIG_SYNC_ON)
    def test_edit_object_with_permission(self):
        instance = self.tested_hardware

        # Assign model-level permission
        obj_perm = ObjectPermission(name='Test permission', actions=['change'])
        obj_perm.save()
        obj_perm.users.add(self.user)
        obj_perm.object_types.add(ObjectType.objects.get_for_model(self.model))

        # Try GET with model-level permission
        self.assertHttpStatus(self.client.get(self._get_url('edit', instance)), 200)

        # Try POST with model-level permission
        request = {
            'path': self._get_url('edit', instance),
            'data': post_data(self.form_data),
        }
        self.assertHttpStatus(self.client.post(**request), 302)
        updated = self._get_queryset().get(pk=instance.pk)
        if self.asset_new:
            self.assertEqual(updated.asset_tag, self.asset_new.asset_tag)
            self.assertEqual(updated.serial, self.asset_new.serial)
        else:
            self.assertEqual(updated.asset_tag, None)
            self.assertEqual(updated.serial, '')

        # Verify ObjectChange creation
        objectchanges = ObjectChange.objects.filter(
            changed_object_type=ContentType.objects.get_for_model(instance),
            changed_object_id=instance.pk,
        )
        self.assertEqual(len(objectchanges), 1)
        self.assertEqual(
            objectchanges[0].action, ObjectChangeActionChoices.ACTION_UPDATE
        )

        # check for changes on asset instances
        self.asset_old.refresh_from_db()
        self.assertEqual(self.asset_old.status, 'stored')
        self.assertEqual(self.asset_old.hardware, None)
        objectchanges = ObjectChange.objects.filter(
            changed_object_type=ContentType.objects.get_for_model(self.asset_old),
            changed_object_id=self.asset_old.pk,
        )
        self.assertEqual(len(objectchanges), 1)
        self.assertEqual(
            objectchanges[0].action, ObjectChangeActionChoices.ACTION_UPDATE
        )
        if self.asset_new:
            self.asset_new.refresh_from_db()
            self.assertEqual(self.asset_new.status, 'used')
            self.assertEqual(self.asset_new.hardware, updated)
            objectchanges = ObjectChange.objects.filter(
                changed_object_type=ContentType.objects.get_for_model(self.asset_new),
                changed_object_id=self.asset_new.pk,
            )
            self.assertEqual(len(objectchanges), 1)
            self.assertEqual(
                objectchanges[0].action, ObjectChangeActionChoices.ACTION_UPDATE
            )


class DeviceReassignAssetTestCase(AssetReassignBase, ModelViewTestCase):
    """
    Test assigning different Asset to Device
    """

    model = Device

    def setUp(self):
        super().setUp()
        self.form_data = {
            'assigned_asset': self.asset_device_new.pk,
            'asset_status': 'stored',
        }
        self.tested_hardware = self.device1
        self.asset_new = self.asset_device_new
        self.asset_old = self.asset_device_old


class ModuleReassignAssetTestCase(AssetReassignBase, ModelViewTestCase):
    """
    Test assigning different Asset to Module
    """

    model = Module

    def setUp(self):
        super().setUp()
        self.form_data = {
            'assigned_asset': self.asset_module_new.pk,
            'asset_status': 'stored',
        }
        self.tested_hardware = self.module1
        self.asset_new = self.asset_module_new
        self.asset_old = self.asset_module_old


class RackReassignAssetTestCase(AssetReassignBase, ModelViewTestCase):
    """
    Test assigning different Asset to Rack
    """

    model = Rack

    def setUp(self):
        super().setUp()
        self.form_data = {
            'assigned_asset': self.asset_rack_new.pk,
            'asset_status': 'stored',
        }
        self.tested_hardware = self.rack1
        self.asset_new = self.asset_rack_new
        self.asset_old = self.asset_rack_old


class DeviceUnassignAssetTestCase(AssetReassignBase, ModelViewTestCase):
    """
    Test assigning no Asset to Device
    """

    model = Device

    def setUp(self):
        super().setUp()
        self.form_data = {
            'asset_status': 'stored',
        }
        self.tested_hardware = self.device1
        self.asset_new = None
        self.asset_old = self.asset_device_old


class ModuleUnassignAssetTestCase(AssetReassignBase, ModelViewTestCase):
    """
    Test assigning no Asset to Module
    """

    model = Module

    def setUp(self):
        super().setUp()
        self.form_data = {
            'asset_status': 'stored',
        }
        self.tested_hardware = self.module1
        self.asset_new = None
        self.asset_old = self.asset_module_old


class RackUnassignAssetTestCase(AssetReassignBase, ModelViewTestCase):
    """
    Test assigning no Asset to Rack
    """

    model = Rack

    def setUp(self):
        super().setUp()
        self.form_data = {
            'asset_status': 'stored',
        }
        self.tested_hardware = self.rack1
        self.asset_new = None
        self.asset_old = self.asset_rack_old
