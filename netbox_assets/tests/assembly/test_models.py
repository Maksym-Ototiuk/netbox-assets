from copy import deepcopy
from urllib.parse import parse_qs, urlsplit

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from dcim.models import Manufacturer, Module
from utilities.exceptions import AbortRequest

from netbox_assets.assembly import AssemblySpec, validate_assembly_schema
from netbox_assets.filtersets import AssetFilterSet, ModuleAssetFilterSet
from netbox_assets.models import Asset, AssetModuleEnd
from netbox_assets.tests.assembly.utils import (
    BREAKOUT_SCHEMA,
    DAC_SCHEMA,
    AssemblyFixtures,
)
from netbox_assets.tests.settings import CONFIG_SYNC_OFF, CONFIG_SYNC_ON


class AssemblySchemaTestCase(SimpleTestCase):
    def test_end_names_from_profile(self):
        spec = AssemblySpec.from_schema(DAC_SCHEMA)
        self.assertEqual(spec.labels, ['SFP+ A', 'SFP+ B'])
        self.assertEqual((spec.a_ends, spec.b_ends), (1, 1))

    def test_default_end_names(self):
        spec = AssemblySpec.from_schema(BREAKOUT_SCHEMA)
        self.assertEqual(spec.labels, ['A', 'B1', 'B2', 'B3', 'B4'])
        self.assertEqual(spec.get_slot('B3').side, 'B')

    def test_not_an_assembly(self):
        self.assertIsNone(AssemblySpec.from_schema({'properties': {'side': {}}}))
        self.assertIsNone(AssemblySpec.from_schema(None))
        self.assertEqual(validate_assembly_schema({'properties': {}}), [])

    def test_valid_schemas(self):
        self.assertEqual(validate_assembly_schema(DAC_SCHEMA), [])
        self.assertEqual(validate_assembly_schema(BREAKOUT_SCHEMA), [])

    def test_end_count_must_be_fixed(self):
        schema = deepcopy(BREAKOUT_SCHEMA)
        schema['properties']['b_ends'] = {'type': 'integer', 'enum': [2, 4]}
        self.assertEqual(len(validate_assembly_schema(schema)), 1)
        schema['properties']['b_ends'] = {'type': 'integer', 'default': 4}
        self.assertEqual(len(validate_assembly_schema(schema)), 1)
        schema['properties']['b_ends'] = {'type': 'integer', 'enum': [0]}
        self.assertEqual(len(validate_assembly_schema(schema)), 1)

    def test_default_must_match_enum(self):
        schema = deepcopy(BREAKOUT_SCHEMA)
        schema['properties']['b_ends']['default'] = 2
        self.assertEqual(len(validate_assembly_schema(schema)), 1)

    def test_end_names(self):
        schema = deepcopy(BREAKOUT_SCHEMA)
        schema['x-end-names'] = {'B': ['B1', 'B2']}
        self.assertIn('has 2 names', validate_assembly_schema(schema)[0])
        schema['x-end-names'] = {'A': ['X'], 'B': ['X', 'B2', 'B3', 'B4']}
        self.assertIn('unique', validate_assembly_schema(schema)[0])
        schema['x-end-names'] = {'C': ['X']}
        self.assertEqual(len(validate_assembly_schema(schema)), 1)
        schema['x-end-names'] = {'A': ['x' * 33]}
        self.assertIn('longer', validate_assembly_schema(schema)[0])


class AssemblyModelTestCase(AssemblyFixtures, TestCase):
    def setUp(self):
        self.create_assembly_fixtures()
        self.dac = self.create_assembly(serial='DAC001', asset_tag='T-DAC001')
        self.breakout = self.create_assembly(
            module_type=self.breakout_a_type, serial='BRK001', asset_tag='T-BRK001'
        )

    def install(self, asset, module, label='', **kwargs):
        end = AssetModuleEnd(asset=asset, module=module, label=label, **kwargs)
        end.full_clean()
        end.save()
        return end

    def refresh(self, *objects):
        for obj in objects:
            obj.refresh_from_db()

    #
    # Asset validation
    #

    def test_is_assembly(self):
        self.assertTrue(self.dac.is_assembly)
        self.assertTrue(self.breakout.is_assembly)
        plain = Asset(module_type=self.plain_module_type, status='stored')
        self.assertFalse(plain.is_assembly)
        self.assertIsNone(plain.assembly_spec)

    def test_asset_must_be_side_a_type(self):
        asset = Asset(module_type=self.breakout_b_type, status='stored')
        with self.assertRaisesMessage(ValidationError, 'side "A" or "both"'):
            asset.full_clean()

    def test_asset_cannot_be_assigned_to_module(self):
        module = self.create_module(self.device1, 1, self.dac_type)
        self.dac.module = module
        with self.assertRaisesMessage(ValidationError, 'Install its ends instead'):
            self.dac.full_clean()

    def test_end_module_cannot_be_assigned_to_other_asset(self):
        module = self.create_module(self.device1, 1, self.dac_type)
        self.install(self.dac, module)
        other = Asset(module_type=self.plain_module_type, status='stored')
        other.module = module
        # skip the module type check, as when an asset is reassigned
        other._in_reassign = True
        with self.assertRaisesMessage(ValidationError, 'end of a cable assembly'):
            other.full_clean()

    def test_cannot_change_module_type_with_ends(self):
        self.install(self.dac, self.create_module(self.device1, 1, self.dac_type))
        self.dac.module_type = self.breakout_a_type
        with self.assertRaisesMessage(ValidationError, 'Cannot change the module type'):
            self.dac.full_clean()

    #
    # End validation
    #

    def test_end_of_non_assembly_asset(self):
        asset = Asset.objects.create(
            module_type=self.plain_module_type, status='stored'
        )
        module = self.create_module(self.device1, 1, self.plain_module_type)
        with self.assertRaisesMessage(ValidationError, 'is not a cable assembly'):
            self.install(asset, module, label='A')

    def test_unknown_end(self):
        module = self.create_module(self.device1, 1, self.dac_type)
        with self.assertRaisesMessage(ValidationError, 'Unknown end'):
            self.install(self.dac, module, label='B9')

    def test_side_a_end_must_be_asset_module_type(self):
        module = self.create_module(self.device1, 1, self.breakout_b_type)
        with self.assertRaisesMessage(ValidationError, 'must be a module of type'):
            self.install(self.breakout, module, label='A')

    def test_side_b_end_must_be_side_b_type(self):
        module = self.create_module(self.device1, 1, self.breakout_a_type)
        with self.assertRaisesMessage(ValidationError, 'side B module type'):
            self.install(self.breakout, module, label='B1')

    def test_side_b_end_error(self):
        # the error explains the module type and lists the side B module types
        module = self.create_module(self.device1, 1, self.breakout_a_type)
        with self.assertRaises(ValidationError) as cm:
            self.install(self.breakout, module, label='B1')
        message = cm.exception.messages[0]
        self.assertIn(
            'must be a module of a side B module type with profile Breakout '
            'QSFP+ - 4xSFP+ and manufacturer Cables Inc, not BRK-1M-A (profile '
            'Breakout QSFP+ - 4xSFP+, side A, manufacturer Cables Inc).',
            message,
        )
        self.assertIn('Side B module types: BRK-1M-B.', message)
        self.assertIn('Module bay Bay 1 already has a module of type BRK-1M-A', message)

    def test_side_b_end_must_have_same_manufacturer(self):
        manufacturer = Manufacturer.objects.create(name='Other', slug='other')
        module_type = self.create_module_type(
            'OTHER-B',
            self.breakout_profile,
            'B',
            '10gbase-x-sfpp',
            manufacturer=manufacturer,
        )
        self.assertFalse(self.breakout.is_side_b_module_type(module_type))
        self.assertTrue(self.breakout.is_side_b_module_type(self.breakout_b_type))
        module = self.create_module(self.device1, 1, module_type)
        with self.assertRaisesMessage(ValidationError, 'side B, manufacturer Other)'):
            self.install(self.breakout, module, label='B1')

    def test_side_b_module_type_missing(self):
        asset = self.create_other_breakout()
        self.assertFalse(asset.get_side_b_module_types().exists())
        module = self.create_module(self.device1, 1, self.breakout_b_type)
        with self.assertRaisesMessage(ValidationError, 'There is no such module type'):
            self.install(asset, module, label='B1')

    def test_side_b_module_type_add_url(self):
        url = urlsplit(self.breakout.get_side_b_module_type_add_url())
        self.assertEqual(url.path, reverse('dcim:moduletype_add'))
        self.assertEqual(
            parse_qs(url.query),
            {
                'profile': [str(self.breakout_profile.pk)],
                'manufacturer': [str(self.manufacturer.pk)],
                'attr_side': ['B'],
                'attr_cable_type': ['Direct Attach Copper (Passive)'],
                'attr_length': ['1'],
            },
        )

    def test_symmetric_end_must_be_asset_module_type(self):
        module = self.create_module(self.device1, 1, self.breakout_b_type)
        with self.assertRaisesMessage(ValidationError, 'must be a module of type'):
            self.install(self.dac, module, label='SFP+ B')

    def test_module_assigned_to_other_asset(self):
        module = self.create_module(self.device1, 1, self.dac_type)
        # data that the plugin prevents, e.g. created before the module type
        # got its cable assembly profile
        Asset.objects.create(module_type=self.dac_type, module=module, status='used')
        with self.assertRaisesMessage(ValidationError, 'already assigned to asset'):
            self.install(self.dac, module, label='SFP+ A')

    def test_end_installed_twice(self):
        self.install(
            self.dac, self.create_module(self.device1, 1, self.dac_type), 'SFP+ A'
        )
        module = self.create_module(self.device1, 2, self.dac_type)
        with self.assertRaisesMessage(ValidationError, 'already installed'):
            self.install(self.dac, module, label='SFP+ A')

    def test_free_end_is_chosen(self):
        a = self.install(
            self.breakout, self.create_module(self.device1, 1, self.breakout_a_type)
        )
        b1 = self.install(
            self.breakout, self.create_module(self.device2, 1, self.breakout_b_type)
        )
        b2 = self.install(
            self.breakout, self.create_module(self.device2, 2, self.breakout_b_type)
        )
        self.assertEqual((a.label, b1.label, b2.label), ('A', 'B1', 'B2'))
        dac_a = self.install(
            self.dac, self.create_module(self.device1, 3, self.dac_type)
        )
        dac_b = self.install(
            self.dac, self.create_module(self.device2, 3, self.dac_type)
        )
        self.assertEqual((dac_a.label, dac_b.label), ('SFP+ A', 'SFP+ B'))

    def test_all_ends_installed(self):
        self.install(
            self.breakout, self.create_module(self.device1, 1, self.breakout_a_type)
        )
        module = self.create_module(self.device1, 2, self.breakout_a_type)
        with self.assertRaisesMessage(ValidationError, 'already installed'):
            self.install(self.breakout, module)

    #
    # Primary end
    #

    def test_first_end_is_primary(self):
        b1 = self.install(
            self.breakout, self.create_module(self.device2, 1, self.breakout_b_type)
        )
        self.assertTrue(b1.is_primary)
        b2 = self.install(
            self.breakout, self.create_module(self.device2, 2, self.breakout_b_type)
        )
        self.assertFalse(b2.is_primary)

    def test_side_a_end_becomes_primary(self):
        b1 = self.install(
            self.breakout, self.create_module(self.device2, 1, self.breakout_b_type)
        )
        a = self.install(
            self.breakout, self.create_module(self.device1, 1, self.breakout_a_type)
        )
        self.refresh(b1)
        self.assertTrue(a.is_primary)
        self.assertFalse(b1.is_primary)

    def test_set_primary(self):
        a = self.install(
            self.breakout, self.create_module(self.device1, 1, self.breakout_a_type)
        )
        b1 = self.install(
            self.breakout, self.create_module(self.device2, 1, self.breakout_b_type)
        )
        b1.snapshot()
        b1.is_primary = True
        b1.full_clean()
        b1.save()
        self.refresh(a)
        self.assertFalse(a.is_primary)
        self.assertEqual(self.breakout.primary_end, b1)

    def test_cannot_unset_primary(self):
        a = self.install(self.dac, self.create_module(self.device1, 1, self.dac_type))
        a.is_primary = False
        with self.assertRaisesMessage(ValidationError, 'Mark another end'):
            a.full_clean()

    def test_primary_end_removed(self):
        a = self.install(
            self.breakout, self.create_module(self.device1, 1, self.breakout_a_type)
        )
        b2 = self.install(
            self.breakout,
            self.create_module(self.device2, 2, self.breakout_b_type),
            'B2',
        )
        b1 = self.install(
            self.breakout,
            self.create_module(self.device2, 1, self.breakout_b_type),
            'B1',
        )
        a.delete()
        self.refresh(b1, b2)
        # first remaining end in the order of the slots
        self.assertTrue(b1.is_primary)
        self.assertFalse(b2.is_primary)

    #
    # Status
    #

    def test_status(self):
        a = self.install(self.dac, self.create_module(self.device1, 1, self.dac_type))
        self.refresh(self.dac)
        self.assertEqual(self.dac.status, 'used')
        b = self.install(self.dac, self.create_module(self.device2, 1, self.dac_type))
        a.delete()
        self.refresh(self.dac)
        self.assertEqual(self.dac.status, 'used')
        b.delete()
        self.refresh(self.dac)
        self.assertEqual(self.dac.status, 'stored')

    def test_module_deleted(self):
        module = self.create_module(self.device1, 1, self.dac_type)
        self.install(self.dac, module)
        module.delete()
        self.refresh(self.dac)
        self.assertEqual(self.dac.status, 'stored')
        self.assertFalse(self.dac.ends.exists())

    def test_device_with_both_ends_deleted(self):
        self.install(self.dac, self.create_module(self.device1, 1, self.dac_type))
        self.install(self.dac, self.create_module(self.device1, 2, self.dac_type))
        self.device1.delete()
        self.refresh(self.dac)
        self.assertEqual(self.dac.status, 'stored')
        self.assertFalse(self.dac.ends.exists())

    def test_end_moved_to_other_assembly(self):
        other = self.create_assembly(serial='DAC002')
        end = self.install(self.dac, self.create_module(self.device1, 1, self.dac_type))
        end.snapshot()
        end.asset = other
        end.full_clean()
        end.save()
        self.refresh(self.dac, other, end)
        self.assertEqual(self.dac.status, 'stored')
        self.assertEqual(other.status, 'used')
        self.assertTrue(end.is_primary)

    #
    # Serial and asset tag synchronization
    #

    @override_settings(PLUGINS_CONFIG=CONFIG_SYNC_ON)
    def test_sync(self):
        module_a = self.create_module(self.device1, 1, self.breakout_a_type)
        module_b1 = self.create_module(self.device2, 1, self.breakout_b_type)
        self.install(self.breakout, module_b1)
        self.install(self.breakout, module_a)
        self.refresh(module_a, module_b1)
        # serial on all ends, asset tag on the primary (side A) end only
        self.assertEqual(module_a.serial, 'BRK001')
        self.assertEqual(module_b1.serial, 'BRK001')
        self.assertEqual(module_a.asset_tag, 'T-BRK001')
        self.assertIsNone(module_b1.asset_tag)

        # asset serial and asset tag changes
        self.refresh(self.breakout)
        self.breakout.snapshot()
        self.breakout.serial = 'BRK002'
        self.breakout.asset_tag = 'T-BRK002'
        self.breakout.full_clean()
        self.breakout.save()
        self.refresh(module_a, module_b1)
        self.assertEqual(module_b1.serial, 'BRK002')
        self.assertEqual(module_a.asset_tag, 'T-BRK002')

    @override_settings(PLUGINS_CONFIG=CONFIG_SYNC_ON)
    def test_sync_primary_change(self):
        module_a = self.create_module(self.device1, 1, self.dac_type)
        module_b = self.create_module(self.device2, 1, self.dac_type)
        self.install(self.dac, module_a)
        end_b = self.install(self.dac, module_b)
        end_b.snapshot()
        end_b.is_primary = True
        end_b.save()
        self.refresh(module_a, module_b)
        self.assertIsNone(module_a.asset_tag)
        self.assertEqual(module_b.asset_tag, 'T-DAC001')

    @override_settings(PLUGINS_CONFIG=CONFIG_SYNC_ON)
    def test_sync_uninstall(self):
        module_a = self.create_module(self.device1, 1, self.dac_type)
        module_b = self.create_module(self.device2, 1, self.dac_type)
        end_a = self.install(self.dac, module_a)
        self.install(self.dac, module_b)
        end_a.delete()
        self.refresh(module_a, module_b)
        # uninstalled module is cleared, the tag moves to the new primary end
        self.assertEqual(module_a.serial, '')
        self.assertIsNone(module_a.asset_tag)
        self.assertEqual(module_b.asset_tag, 'T-DAC001')

    @override_settings(PLUGINS_CONFIG=CONFIG_SYNC_ON)
    def test_sync_primary_module_deleted(self):
        module_a = self.create_module(self.device1, 1, self.dac_type)
        module_b = self.create_module(self.device2, 1, self.dac_type)
        self.install(self.dac, module_a)
        self.install(self.dac, module_b)
        module_a.delete()
        self.refresh(module_b)
        self.assertEqual(module_b.asset_tag, 'T-DAC001')

    @override_settings(PLUGINS_CONFIG=CONFIG_SYNC_ON)
    def test_sync_asset_deleted(self):
        module = self.create_module(self.device1, 1, self.dac_type)
        self.install(self.dac, module)
        self.dac.delete()
        module.refresh_from_db()
        # values are not cleared when the asset is deleted
        self.assertEqual(module.serial, 'DAC001')
        self.assertEqual(module.asset_tag, 'T-DAC001')

    @override_settings(PLUGINS_CONFIG=CONFIG_SYNC_ON)
    def test_prevent_update_end_module(self):
        module = self.create_module(self.device1, 1, self.dac_type)
        self.install(self.dac, module)
        module = Module.objects.get(pk=module.pk)
        module.serial = 'other'
        with self.assertRaises(AbortRequest):
            module.save()

    @override_settings(PLUGINS_CONFIG=CONFIG_SYNC_OFF)
    def test_sync_off(self):
        module = self.create_module(self.device1, 1, self.dac_type)
        self.install(self.dac, module)
        module.refresh_from_db()
        self.assertEqual(module.serial, '')
        self.assertIsNone(module.asset_tag)
        module.serial = 'other'
        module.save()

    #
    # Protection of NetBox objects used by cable assemblies
    #

    def test_protect_end_module_type(self):
        module = self.create_module(self.device1, 1, self.dac_type)
        self.install(self.dac, module)
        module = Module.objects.get(pk=module.pk)
        module.module_type = self.plain_module_type
        with self.assertRaisesMessage(AbortRequest, 'Uninstall the end first'):
            module.save()

    def test_protect_module_type(self):
        self.dac_type.attribute_data = {'side': 'A', 'cable_type': 'dac-passive', 'length': 1}
        with self.assertRaisesMessage(AbortRequest, 'used by cable assemblies'):
            self.dac_type.save()
        self.dac_type.refresh_from_db()
        self.dac_type.profile = None
        with self.assertRaisesMessage(AbortRequest, 'used by cable assemblies'):
            self.dac_type.save()

    def test_protect_module_type_assigned_assets(self):
        module = self.create_module(self.device1, 1, self.plain_module_type)
        Asset.objects.create(
            module_type=self.plain_module_type, module=module, status='used'
        )
        self.plain_module_type.profile = self.dac_profile
        self.plain_module_type.attribute_data = {'side': 'both', 'cable_type': 'dac-passive'}
        with self.assertRaisesMessage(AbortRequest, 'are assigned to modules'):
            self.plain_module_type.save()

    def test_protect_profile(self):
        self.install(
            self.breakout, self.create_module(self.device1, 1, self.breakout_a_type)
        )
        self.install(
            self.breakout,
            self.create_module(self.device2, 4, self.breakout_b_type),
            'B4',
        )
        profile = self.breakout_profile
        # invalid assembly schema
        profile.schema = deepcopy(BREAKOUT_SCHEMA)
        profile.schema['properties']['b_ends'] = {'type': 'integer', 'enum': [2, 4]}
        with self.assertRaisesMessage(AbortRequest, 'Invalid cable assembly profile'):
            profile.save()
        # end B4 would not exist any more
        profile.schema['properties']['b_ends'] = {'type': 'integer', 'enum': [2]}
        with self.assertRaisesMessage(AbortRequest, 'B4'):
            profile.save()
        # not an assembly profile any more
        profile.schema = {'properties': {}}
        with self.assertRaisesMessage(AbortRequest, 'cannot be removed'):
            profile.save()
        # more ends are fine
        profile.schema = deepcopy(BREAKOUT_SCHEMA)
        profile.schema['properties']['b_ends'] = {'type': 'integer', 'enum': [8]}
        profile.save()

    #
    # Filters
    #

    def test_filters(self):
        self.install(self.dac, self.create_module(self.device1, 1, self.dac_type))
        plain = Asset.objects.create(
            module_type=self.plain_module_type, status='stored'
        )
        assets = Asset.objects.all()

        def filtered(**params):
            return set(AssetFilterSet(params, assets).qs)

        self.assertEqual(filtered(is_assembly=True), {self.dac, self.breakout})
        self.assertEqual(filtered(is_assembly=False), {plain})
        self.assertEqual(filtered(is_assigned=True), {self.dac})
        self.assertEqual(filtered(is_assigned=False), {self.breakout, plain})
        self.assertEqual(filtered(installed_device_id=[self.device1.pk]), {self.dac})
        self.assertEqual(filtered(installed_site_id=[self.site.pk]), {self.dac})
        self.assertEqual(filtered(q='switch1'), {self.dac})

        modules = Module.objects.all()
        self.assertEqual(
            ModuleAssetFilterSet({'has_asset_assigned': False}, modules).qs.count(), 0
        )

    def test_installed_location(self):
        self.install(self.dac, self.create_module(self.device1, 1, self.dac_type))
        self.install(self.dac, self.create_module(self.device2, 1, self.dac_type))
        self.refresh(self.dac)
        # an assembly is installed where its primary end is
        self.assertEqual(self.dac.installed_device, self.device1)
        self.assertEqual(self.dac.installed_site, self.site)
        self.assertEqual(self.dac.hardware, self.dac.primary_end.module)
