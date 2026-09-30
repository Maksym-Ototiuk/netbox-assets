from django.test import override_settings

from core.models import ObjectType
from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from users.models import ObjectPermission
from utilities.testing import ViewTestCases, post_data

from netbox_assets.models import Asset
from netbox_assets.tests.custom import ModelViewTestCase
from netbox_assets.tests.settings import CONFIG_ALLOW_CREATE_DEVICE_TYPE


class AssetTestCase(
    ModelViewTestCase,
    ViewTestCases.PrimaryObjectViewTestCase,
):
    """
    UI view tests for assets
    """

    model = Asset

    @classmethod
    def setUpTestData(cls):
        Site.objects.create(
            name='site1',
            slug='site1',
            status='active',
        )
        manufacturer1 = Manufacturer.objects.create(
            name='manufacturer1',
            slug='manufacturer1',
        )
        device_type1 = DeviceType.objects.create(
            model='device_type1',
            slug='device_type1',
            manufacturer=manufacturer1,
            u_height=1,
        )
        DeviceRole.objects.create(
            name='role1',
            slug='role1',
            color='9e9e9e',
        )
        asset1 = Asset.objects.create(
            status='stored',
            serial='123',
            device_type=device_type1,
        )
        asset2 = Asset.objects.create(
            status='stored',
            serial='223',
            device_type=device_type1,
        )
        asset3 = Asset.objects.create(
            status='stored',
            serial='323',
            device_type=device_type1,
        )

        cls.form_data = {
            'status': 'stored',
            'serial': '124',
            'device_type': device_type1.pk,
        }
        cls.csv_data = (
            'serial,status,hardware_kind,manufacturer,model_name',
            'csv1,stored,device,manufacturer1,device_type1',
            'csv2,stored,device,manufacturer1,device_type1',
            'csv3,stored,device,manufacturer_csv,device_type_csv',
        )
        cls.csv_update_data = (
            'id,serial,status',
            f'{asset1.pk},133,stored',
            f'{asset2.pk},233,stored',
            f'{asset3.pk},333,stored',
        )
        cls.bulk_edit_data = {
            'status': 'retired',
        }

    @override_settings(EXEMPT_VIEW_PERMISSIONS=['*'])
    def test_assign_device_from_asset(self):
        """
        "Edit Assignment" on the asset page assigns an existing device
        """
        obj_perm = ObjectPermission(
            name='test-device-assign permission', actions=['add', 'change']
        )
        obj_perm.save()
        obj_perm.users.add(self.user)
        obj_perm.object_types.add(ObjectType.objects.get_for_model(self.model))
        obj_perm.object_types.add(ObjectType.objects.get_for_model(Device))

        asset = Asset.objects.create(
            status='stored',
            serial='123assign',
            device_type=DeviceType.objects.first(),
        )
        device = Device.objects.create(
            name='test-device-assign',
            role=DeviceRole.objects.first(),
            device_type=asset.device_type,
            site=Site.objects.first(),
            status='active',
        )

        form_data = {
            'name': 'test-device-assign',
            'device_type': asset.device_type.pk,
            'device': device.pk,
        }

        request = {
            'path': self._get_url('assign', asset),
            'data': post_data(form_data),
        }
        self.assertHttpStatus(self.client.post(**request), 302)

        device.refresh_from_db()
        self.assertEqual(device.assigned_asset, asset)
        asset.refresh_from_db()
        self.assertEqual(asset.status, 'used')

    @override_settings(PLUGINS_CONFIG=CONFIG_ALLOW_CREATE_DEVICE_TYPE)
    def test_bulk_import_objects_with_permission(self):
        return super().test_bulk_import_objects_with_permission()

    @override_settings(PLUGINS_CONFIG=CONFIG_ALLOW_CREATE_DEVICE_TYPE)
    def test_bulk_import_objects_with_constrained_permission(self):
        return super().test_bulk_import_objects_with_constrained_permission()


class AssetBulkAddTestCase(
    ModelViewTestCase,
    ViewTestCases.CreateMultipleObjectsViewTestCase,
):
    """
    Tests for /plugins/assets/assets/bulk-add/
    """

    model = Asset

    @classmethod
    def setUpTestData(cls):
        manufacturer1 = Manufacturer.objects.create(
            name='manufacturer1',
            slug='manufacturer1',
        )
        device_type1 = DeviceType.objects.create(
            model='device_type1',
            slug='device_type1',
            manufacturer=manufacturer1,
            u_height=1,
        )

        cls.bulk_create_data = {
            'count': 3,
            'status': 'stored',
            'device_type': device_type1.pk,
        }

    def _get_url(self, action, instance=None):
        # CreateMultipleObjectsViewTestCase uses the 'add' view, the plugin uses 'bulk_add'
        if action == 'add':
            action = 'bulk_add'
        return super()._get_url(action, instance)

    def test_create_multiple_objects_addanother(self):
        # NetBox 4.7.2+ treats device_type/module_type as the parent object of
        # device components. For assets it is an ordinary field, so the check
        # does not apply.
        self.skipTest('device_type is not a parent object for assets')

    def test_bulk_create_objects_with_asset_tag_pattern(self):
        obj_perm = ObjectPermission(name='test-asset-bulk-add-pattern', actions=['add'])
        obj_perm.save()
        obj_perm.users.add(self.user)
        obj_perm.object_types.add(ObjectType.objects.get_for_model(self.model))

        form_data = {
            'count': 3,
            'pattern': 'ASSET-[001-003]',
            'status': 'stored',
            'device_type': DeviceType.objects.first().pk,
        }
        request = {
            'path': self._get_url('add'),
            'data': post_data(form_data),
        }
        self.assertHttpStatus(self.client.post(**request), 302)

        self.assertEqual(
            list(
                Asset.objects.order_by('asset_tag').values_list('asset_tag', flat=True)
            ),
            ['ASSET-1', 'ASSET-2', 'ASSET-3'],
        )
