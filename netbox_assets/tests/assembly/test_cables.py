from copy import deepcopy
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import SimpleTestCase
from django.urls import reverse

from dcim.choices import CableTypeChoices
from dcim.models import Cable, Interface, ModuleType
from utilities.exceptions import AbortRequest
from utilities.testing import TestCase

from netbox_assets.assembly import (
    CABLE_TYPE_LABELS,
    AssemblySpec,
    get_cable_type,
    validate_assembly_schema,
)
from netbox_assets.models import Asset, AssetModuleEnd
from netbox_assets.tests.assembly.utils import (
    BREAKOUT_SCHEMA,
    DAC_SCHEMA,
    AssemblyFixtures,
)


class CableSchemaTestCase(SimpleTestCase):
    def test_default_cable_profile(self):
        self.assertEqual(AssemblySpec.from_schema(DAC_SCHEMA).cable_profile, 'single-1c1p')
        self.assertEqual(
            AssemblySpec.from_schema(BREAKOUT_SCHEMA).cable_profile, 'breakout-1c4p-4c1p'
        )
        schema = deepcopy(BREAKOUT_SCHEMA)
        schema['properties']['b_ends'] = {'type': 'integer', 'enum': [3]}
        self.assertEqual(AssemblySpec.from_schema(schema).cable_profile, '')

    def test_cable_profile_key(self):
        schema = deepcopy(BREAKOUT_SCHEMA)
        schema['x-cable-profile'] = 'single-1c4p'
        errors = validate_assembly_schema(schema)
        self.assertIn('too few connectors', errors[0])
        schema['x-cable-profile'] = 'unknown'
        self.assertIn('unknown NetBox cable profile', validate_assembly_schema(schema)[0])
        schema['x-cable-profile'] = 'breakout-1c8p-8c1p'
        self.assertEqual(validate_assembly_schema(schema), [])
        self.assertEqual(AssemblySpec.from_schema(schema).cable_profile, 'breakout-1c8p-8c1p')

    def test_cable_type(self):
        schema = deepcopy(DAC_SCHEMA)
        schema['properties']['cable_type']['enum'] = ['dac-passive', 'copper-dac']
        self.assertIn('copper-dac', validate_assembly_schema(schema)[0])
        # labels, values and both mixed
        for enum in (
            ['Direct Attach Copper (Passive)', 'Active Optical Cabling (AOC)'],
            ['dac-passive', 'aoc'],
            ['Direct Attach Copper (Active)', 'dac-passive'],
        ):
            schema['properties']['cable_type']['enum'] = enum
            self.assertEqual(validate_assembly_schema(schema), [])

    def test_get_cable_type(self):
        self.assertEqual(get_cable_type('Direct Attach Copper (Passive)'), 'dac-passive')
        self.assertEqual(get_cable_type('Direct Attach Copper (Active)'), 'dac-active')
        self.assertEqual(get_cable_type('Active Optical Cabling (AOC)'), 'aoc')
        self.assertEqual(get_cable_type('dac-passive'), 'dac-passive')
        for name in ('DAC (Passive)', 'direct attach copper (passive)', '', None, 1):
            self.assertIsNone(get_cable_type(name))

    def test_cable_type_labels(self):
        # every cable type of the plugin must exist in NetBox (see CLAUDE.md)
        self.assertEqual(
            set(CABLE_TYPE_LABELS) - set(CableTypeChoices.values()), set()
        )


class AssemblyCableTestCase(AssemblyFixtures, TestCase):
    def setUp(self):
        super().setUp()
        self.create_assembly_fixtures()
        self.dac = self.create_assembly(serial='DAC001', asset_tag='T-DAC001')
        self.breakout = self.create_assembly(
            module_type=self.breakout_a_type, serial='BRK001', asset_tag='T-BRK001'
        )

    def install(self, asset, device, bay, label, module_type=None):
        if module_type is None:
            module_type = self.breakout_b_type if label.startswith('B') else asset.module_type
        end = AssetModuleEnd(
            asset=asset,
            module=self.create_module(device, bay, module_type),
            label=label,
        )
        end.full_clean()
        end.save()
        return end

    def install_breakout(self, *b_labels):
        ends = {'A': self.install(self.breakout, self.device1, 1, 'A')}
        for label in b_labels:
            ends[label] = self.install(self.breakout, self.device2, int(label[1]), label)
        return ends

    def cable_of(self, asset):
        asset.refresh_from_db()
        return asset.assembly_cable

    def interface(self, device, name):
        return Interface.objects.get(device=device, name=name)

    def terminations(self, cable):
        a, b = Cable.objects.get(pk=cable.pk).get_terminations()
        return (
            [f'{t.device}:{t.name}' for t in a],
            [f'{t.device}:{t.name}' for t in b],
        )

    def assertTrace(self, channel, device, name):
        interface = self.interface(self.device1, f'Port 1:{channel}')
        self.assertEqual(
            [(e.device, e.name) for e in interface.connected_endpoints], [(device, name)]
        )

    #
    # DAC
    #

    def test_dac_cable(self):
        self.install(self.dac, self.device1, 1, 'SFP+ A')
        self.assertIsNone(self.cable_of(self.dac))

        end_b = self.install(self.dac, self.device2, 1, 'SFP+ B')
        cable = self.cable_of(self.dac)
        # module type attribute "Direct Attach Copper (Passive)"
        self.assertEqual(cable.type, 'dac-passive')
        self.assertEqual(cable.profile, 'single-1c1p')
        self.assertEqual(cable.length, Decimal('1.00'))
        self.assertEqual(cable.length_unit, 'm')
        self.assertEqual(cable.status, 'connected')
        self.assertEqual(cable.label, 'T-DAC001')
        self.assertEqual(
            self.terminations(cable), (['switch1:Port 1'], ['switch2:Port 1'])
        )

        end_b.delete()
        self.assertIsNone(self.cable_of(self.dac))
        self.assertFalse(Cable.objects.exists())

    #
    # Breakout: one cable from the side A end to all side B ends
    #

    def test_breakout_complete(self):
        self.install_breakout('B1', 'B2', 'B3', 'B4')
        self.assertEqual(Cable.objects.count(), 1)
        cable = self.cable_of(self.breakout)
        self.assertEqual(cable.profile, 'breakout-1c4p-4c1p')
        self.assertEqual(
            self.terminations(cable),
            (
                ['switch1:Port 1'],
                [f'switch2:Port {i}' for i in range(1, 5)],
            ),
        )
        for channel in range(1, 5):
            self.assertTrace(channel, self.device2, f'Port {channel}')

    def test_breakout_installed_in_any_order(self):
        # B ends first, then A: the cable is created with all of them in slot order
        for label in ('B3', 'B1', 'B4', 'B2'):
            self.install(self.breakout, self.device2, int(label[1]), label)
        self.assertIsNone(self.cable_of(self.breakout))
        self.install(self.breakout, self.device1, 1, 'A')
        cable = self.cable_of(self.breakout)
        self.assertEqual(cable.profile, 'breakout-1c4p-4c1p')
        self.assertEqual(
            self.terminations(cable)[1], [f'switch2:Port {i}' for i in range(1, 5)]
        )
        self.assertTrace(3, self.device2, 'Port 3')

    def test_breakout_partial(self):
        self.install_breakout('B1', 'B2')
        cable = self.cable_of(self.breakout)
        self.assertEqual(cable.profile, 'breakout-1c4p-4c1p')
        self.assertTrace(2, self.device2, 'Port 2')

    def test_breakout_gap(self):
        self.install_breakout('B1', 'B3')
        cable = self.cable_of(self.breakout)
        # B3 would be mapped to connector 2, so the cable has no profile
        self.assertEqual(cable.profile, '')
        self.assertEqual(
            self.terminations(cable)[1], ['switch2:Port 1', 'switch2:Port 3']
        )

        # the gap is closed: the profile is set
        self.install(self.breakout, self.device2, 2, 'B2')
        cable = self.cable_of(self.breakout)
        self.assertEqual(cable.profile, 'breakout-1c4p-4c1p')
        self.assertTrace(3, self.device2, 'Port 3')

    def test_breakout_uninstall_middle(self):
        ends = self.install_breakout('B1', 'B2', 'B3', 'B4')
        ends['B2'].delete()
        cable = self.cable_of(self.breakout)
        self.assertEqual(cable.profile, '')
        self.assertEqual(len(self.terminations(cable)[1]), 3)

    def test_breakout_uninstall_last(self):
        ends = self.install_breakout('B1', 'B2', 'B3', 'B4')
        ends['B4'].delete()
        cable = self.cable_of(self.breakout)
        self.assertEqual(cable.profile, 'breakout-1c4p-4c1p')
        self.assertTrace(3, self.device2, 'Port 3')

    def test_breakout_uninstall_side_a(self):
        ends = self.install_breakout('B1', 'B2')
        ends['A'].delete()
        self.assertIsNone(self.cable_of(self.breakout))
        self.assertFalse(Cable.objects.exists())
        self.assertEqual(self.breakout.ends.count(), 2)

    def test_module_deleted(self):
        # the cable is updated when the deletion is committed
        ends = self.install_breakout('B1', 'B2', 'B3', 'B4')
        with self.captureOnCommitCallbacks(execute=True):
            ends['B2'].module.delete()
        cable = self.cable_of(self.breakout)
        self.assertEqual(len(self.terminations(cable)[1]), 3)
        self.assertEqual(cable.profile, '')
        with self.captureOnCommitCallbacks(execute=True):
            ends['A'].module.delete()
        self.assertIsNone(self.cable_of(self.breakout))
        self.assertFalse(Cable.objects.exists())

    def test_device_deleted(self):
        self.install_breakout('B1', 'B2')
        with self.captureOnCommitCallbacks(execute=True):
            self.device2.delete()
        self.assertIsNone(self.cable_of(self.breakout))
        self.assertFalse(Cable.objects.exists())

    def test_asset_deleted(self):
        self.install_breakout('B1')
        cable = self.cable_of(self.breakout)
        self.breakout.delete()
        # the cable stays and is a normal cable now
        cable = Cable.objects.get(pk=cable.pk)
        cable.delete()

    #
    # Installation checks
    #

    def test_interface_with_other_cable(self):
        module = self.create_module(self.device2, 1, self.dac_type)
        Interface.objects.create(device=self.device1, name='other', type='10gbase-x-sfpp')
        Cable(
            a_terminations=[module.interfaces.get()],
            b_terminations=[self.interface(self.device1, 'other')],
        ).save()
        end = AssetModuleEnd(asset=self.dac, module=module, label='SFP+ A')
        with self.assertRaisesMessage(ValidationError, 'already has cable'):
            end.full_clean()

    def test_module_type_without_interface(self):
        module_type = ModuleType.objects.create(
            manufacturer=self.manufacturer,
            model='BRK-1M-B-NOIF',
            profile=self.breakout_profile,
            attribute_data={'side': 'B'},
        )
        end = AssetModuleEnd(
            asset=self.breakout,
            module=self.create_module(self.device2, 1, module_type),
            label='B1',
        )
        with self.assertRaisesMessage(ValidationError, 'exactly one interface'):
            end.full_clean()

    #
    # Protection of the assembly cable
    #

    def test_allowed_changes(self):
        self.install_breakout('B1')
        cable = Cable.objects.get(pk=self.cable_of(self.breakout).pk)
        cable.label = 'new label'
        cable.description = 'description'
        cable.color = 'ff0000'
        cable.status = 'planned'
        cable.comments = 'comments'
        cable.save()
        # the status is not reset by the plugin
        self.install(self.breakout, self.device2, 2, 'B2')
        cable.refresh_from_db()
        self.assertEqual(cable.status, 'planned')
        self.assertEqual(cable.label, 'new label')

    def test_locked_changes(self):
        self.install_breakout('B1', 'B2')
        cable = Cable.objects.get(pk=self.cable_of(self.breakout).pk)
        cable.length = 5
        with self.assertRaisesMessage(AbortRequest, 'length'):
            cable.save()
        cable = Cable.objects.get(pk=cable.pk)
        cable.type = 'aoc'
        with self.assertRaisesMessage(AbortRequest, 'type'):
            cable.save()
        # changes of terminations and deletion abort inside a transaction (in
        # NetBox the whole request is rolled back)
        cable = Cable.objects.get(pk=cable.pk)
        cable.b_terminations = [self.interface(self.device2, 'Port 1')]
        with self.assertRaisesMessage(AbortRequest, 'terminations'):
            with transaction.atomic():
                cable.save()
        cable = Cable.objects.get(pk=cable.pk)
        with self.assertRaisesMessage(AbortRequest, 'Uninstall the ends'):
            with transaction.atomic():
                cable.delete()
        self.assertEqual(len(self.terminations(cable)[1]), 2)

    def test_module_type_changed(self):
        self.install_breakout('B1')
        module_type = ModuleType.objects.get(pk=self.breakout_a_type.pk)
        # the NetBox value of a cable type works as well as its label
        module_type.attribute_data = {'side': 'A', 'cable_type': 'aoc', 'length': 3}
        module_type.save()
        cable = self.cable_of(self.breakout)
        self.assertEqual(cable.type, 'aoc')
        self.assertEqual(cable.length, Decimal('3.00'))

    def test_profile_cable_profile_changed(self):
        self.install_breakout('B1')
        profile = self.breakout_profile
        profile.schema = deepcopy(BREAKOUT_SCHEMA)
        profile.schema['x-cable-profile'] = 'breakout-1c8p-8c1p'
        profile.save()
        self.assertEqual(self.cable_of(self.breakout).profile, 'breakout-1c8p-8c1p')


class AssemblyCablePermissionTestCase(AssemblyFixtures, TestCase):
    """Installing an end that creates a cable needs the permission to add cables."""

    user_permissions = (
        'netbox_assets.view_asset',
        'netbox_assets.view_assetmoduleend',
        'netbox_assets.add_assetmoduleend',
        'dcim.view_device',
        'dcim.view_modulebay',
        'dcim.view_moduletype',
    )

    def setUp(self):
        super().setUp()
        self.create_assembly_fixtures()
        self.dac = self.create_assembly(serial='DAC001')
        AssetModuleEnd.objects.create(
            asset=self.dac,
            module=self.create_module(self.device1, 1, self.dac_type),
            label='SFP+ A',
        )
        self.create_module(self.device2, 1, self.dac_type)

    def post_install(self):
        return self.client.post(
            reverse('plugins:netbox_assets:assetmoduleend_add'),
            {
                'asset': self.dac.pk,
                'label': 'SFP+ B',
                'device': self.device2.pk,
                'module_bay': self.get_bay(self.device2, 1).pk,
            },
        )

    def test_without_cable_permission(self):
        response = self.post_install()
        self.assertHttpStatus(response, 200)
        self.assertIn('not allowed to add cables', response.content.decode())
        self.assertEqual(self.dac.ends.count(), 1)
        self.assertFalse(Cable.objects.exists())

    def test_with_cable_permission(self):
        self.add_permissions('dcim.add_cable')
        response = self.post_install()
        self.assertHttpStatus(response, 302)
        self.assertEqual(Asset.objects.get(pk=self.dac.pk).assembly_cable.type, 'dac-passive')


class AssemblyCableViewsTestCase(AssemblyFixtures, TestCase):
    """The assembly cable in the NetBox UI and REST API"""

    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.create_assembly_fixtures()
        self.breakout = self.create_assembly(
            module_type=self.breakout_a_type, serial='BRK001', name='<b>brk</b>'
        )
        for label, device, bay, module_type in (
            ('A', self.device1, 1, self.breakout_a_type),
            ('B1', self.device2, 1, self.breakout_b_type),
            ('B3', self.device2, 3, self.breakout_b_type),
        ):
            AssetModuleEnd.objects.create(
                asset=self.breakout,
                module=self.create_module(device, bay, module_type),
                label=label,
            )
        self.breakout.refresh_from_db()
        self.cable = self.breakout.assembly_cable

    def test_asset_page(self):
        response = self.client.get(self.breakout.get_absolute_url())
        content = response.content.decode()
        self.assertIn(self.cable.get_absolute_url(), content)
        self.assertIn('have a gap', content)

    def test_api(self):
        url = reverse('dcim-api:cable-detail', kwargs={'pk': self.cable.pk})
        response = self.client.patch(
            url, {'label': 'new', 'status': 'planned'}, content_type='application/json'
        )
        self.assertHttpStatus(response, 200)
        response = self.client.patch(url, {'length': 5}, content_type='application/json')
        self.assertHttpStatus(response, 400)
        self.assertIn('length cannot be changed', response.json()['detail'])
        response = self.client.delete(url)
        self.assertHttpStatus(response, 400)
        self.assertTrue(Cable.objects.filter(pk=self.cable.pk).exists())

        url = reverse('plugins-api:netbox_assets-api:asset-detail', kwargs={'pk': self.breakout.pk})
        self.assertEqual(self.client.get(url).json()['assembly_cable']['id'], self.cable.pk)

    def test_delete_view(self):
        url = reverse('dcim:cable_delete', kwargs={'pk': self.cable.pk})
        response = self.client.post(url, {'confirm': True}, follow=True)
        content = response.content.decode()
        self.assertTrue(Cable.objects.filter(pk=self.cable.pk).exists())
        self.assertIn('Uninstall the ends of the assembly', content)
        # the message is escaped
        self.assertNotIn('<b>brk</b>', content)
