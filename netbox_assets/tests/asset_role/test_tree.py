from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.test import TestCase

from dcim.models import DeviceType, Manufacturer

from netbox_assets.models import Asset, AssetRole


class AssetRoleTreeTestCase(TestCase):
    """
    Asset roles are stored as an ltree hierarchy (NetBox 4.7 NestedLtreeGroupModel).
    The path columns are maintained by PostgreSQL triggers installed by the
    initial migration.
    """

    @classmethod
    def setUpTestData(cls):
        cls.optics = AssetRole.objects.create(name='Optics', slug='optics')
        cls.spare = AssetRole.objects.create(name='Spare parts', slug='spare-parts')
        cls.sfp = AssetRole.objects.create(name='SFP', slug='sfp', parent=cls.optics)
        cls.qsfp = AssetRole.objects.create(name='QSFP', slug='qsfp', parent=cls.optics)
        cls.sfp_lr = AssetRole.objects.create(
            name='SFP LR', slug='sfp-lr', parent=cls.sfp
        )

    def test_ltree_triggers_installed(self):
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT tgname FROM pg_trigger '
                "WHERE tgrelid = 'netbox_assets_assetrole'::regclass "
                'AND NOT tgisinternal ORDER BY tgname'
            )
            triggers = [row[0] for row in cursor.fetchall()]
        self.assertEqual(
            triggers,
            [
                'netbox_assets_assetrole_ltree_cascade_path',
                'netbox_assets_assetrole_ltree_compute_path',
            ],
        )

    def test_path_is_computed(self):
        self.sfp_lr.refresh_from_db()
        self.assertEqual(self.sfp_lr.level, 2)
        self.assertTrue(str(self.sfp_lr.path).startswith(str(self.optics.path)))

    def test_ordering_follows_tree(self):
        self.assertEqual(
            list(AssetRole.objects.values_list('name', flat=True)),
            ['Optics', 'QSFP', 'SFP', 'SFP LR', 'Spare parts'],
        )

    def test_ancestors_and_descendants(self):
        self.assertEqual(
            [r.name for r in self.optics.get_descendants()],
            ['QSFP', 'SFP', 'SFP LR'],
        )
        self.assertEqual(
            [r.name for r in self.sfp_lr.get_ancestors()],
            ['Optics', 'SFP'],
        )

    def test_same_name_under_different_parent_allowed(self):
        role = AssetRole(name='SFP', slug='sfp', parent=self.spare)
        role.full_clean()
        role.save()

    def test_duplicate_root_name_rejected(self):
        # uniqueness works like DeviceRole: NULL parents are not distinct
        with self.assertRaises(ValidationError):
            AssetRole(name='Optics', slug='optics-2').full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            AssetRole.objects.create(name='Optics', slug='optics-2')

    def test_duplicate_slug_under_same_parent_rejected(self):
        with self.assertRaises(ValidationError):
            AssetRole(name='SFP 2', slug='sfp', parent=self.optics).full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            AssetRole.objects.create(name='SFP 2', slug='sfp', parent=self.optics)

    def test_move_subtree(self):
        self.sfp.parent = self.spare
        self.sfp.name = 'SFP moved'
        self.sfp.slug = 'sfp-moved'
        self.sfp.save()
        self.sfp_lr.refresh_from_db()
        self.assertTrue(str(self.sfp_lr.path).startswith(str(self.spare.path)))
        self.assertEqual(self.sfp_lr.sort_path, 'Spare parts\tSFP moved\tSFP LR')

    def test_cycle_rejected(self):
        self.optics.parent = self.sfp_lr
        with self.assertRaises(ValidationError):
            self.optics.full_clean()

    def test_cumulative_asset_count(self):
        manufacturer = Manufacturer.objects.create(name='M1', slug='m1')
        device_type = DeviceType.objects.create(
            manufacturer=manufacturer, model='X1', slug='x1'
        )
        Asset.objects.create(
            device_type=device_type, serial='A1', status='stored', role=self.sfp_lr
        )
        Asset.objects.create(
            device_type=device_type, serial='A2', status='stored', role=self.sfp
        )
        roles = AssetRole.objects.add_related_count(
            AssetRole.objects.all(), Asset, 'role', 'asset_count', cumulative=True
        )
        counts = {r.name: r.asset_count for r in roles}
        self.assertEqual(counts['Optics'], 2)
        self.assertEqual(counts['SFP'], 2)
        self.assertEqual(counts['SFP LR'], 1)
        self.assertEqual(counts['QSFP'], 0)
        self.assertEqual(counts['Spare parts'], 0)
