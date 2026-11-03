from dcim.models import (
    Device,
    DeviceRole,
    DeviceType,
    InterfaceTemplate,
    Manufacturer,
    Module,
    ModuleBay,
    ModuleType,
    ModuleTypeProfile,
    Site,
)

from netbox_assets.models import Asset

# Symmetric DAC: the same module type on both sides, end names from the profile
DAC_SCHEMA = {
    'type': 'object',
    'x-end-names': {'A': ['SFP+ A'], 'B': ['SFP+ B']},
    'properties': {
        'side': {
            'type': 'string',
            'title': 'Assembly side',
            'enum': ['both'],
            'default': 'both',
        },
        'a_ends': {
            'type': 'integer',
            'title': 'A-side ends',
            'enum': [1],
            'default': 1,
        },
        'b_ends': {
            'type': 'integer',
            'title': 'B-side ends',
            'enum': [1],
            'default': 1,
        },
        'cable_type': {
            'type': 'string',
            'title': 'Cable type',
            'enum': ['dac-passive', 'dac-active'],
        },
        'length': {'type': 'number', 'title': 'Length (m)', 'minimum': 0},
    },
    'required': ['side', 'cable_type'],
}

# Breakout 1 -> 4: separate module types for side A and side B, default names
BREAKOUT_SCHEMA = {
    'type': 'object',
    'properties': {
        'side': {'type': 'string', 'title': 'Assembly side', 'enum': ['A', 'B']},
        'a_ends': {
            'type': 'integer',
            'title': 'A-side ends',
            'enum': [1],
            'default': 1,
        },
        'b_ends': {
            'type': 'integer',
            'title': 'B-side ends',
            'enum': [4],
            'default': 4,
        },
        'cable_type': {'type': 'string', 'title': 'Cable type'},
        'length': {'type': 'number', 'title': 'Length (m)', 'minimum': 0},
    },
    'required': ['side'],
}


class AssemblyFixtures:
    """
    Creates profiles, module types and devices with module bays for cable
    assembly tests. Call create_assembly_fixtures() from setUp() or
    setUpTestData().
    """

    @classmethod
    def create_assembly_fixtures(cls):
        cls.manufacturer = Manufacturer.objects.create(
            name='Cables Inc', slug='cables-inc'
        )
        cls.dac_profile = ModuleTypeProfile.objects.create(
            name='DAC SFP+ - SFP+', schema=DAC_SCHEMA
        )
        cls.breakout_profile = ModuleTypeProfile.objects.create(
            name='Breakout QSFP+ - 4xSFP+', schema=BREAKOUT_SCHEMA
        )
        cls.dac_type = cls.create_module_type(
            'DAC-1M', cls.dac_profile, 'both', '10gbase-x-sfpp'
        )
        cls.breakout_a_type = cls.create_module_type(
            'BRK-1M-A', cls.breakout_profile, 'A', '40gbase-x-qsfpp', channels=4
        )
        cls.breakout_b_type = cls.create_module_type(
            'BRK-1M-B', cls.breakout_profile, 'B', '10gbase-x-sfpp'
        )
        cls.plain_module_type = ModuleType.objects.create(
            manufacturer=cls.manufacturer, model='SFP-10G-SR'
        )

        cls.site = Site.objects.create(name='site1', slug='site1')
        cls.device_type = DeviceType.objects.create(
            manufacturer=cls.manufacturer, model='switch', slug='switch'
        )
        cls.device_role = DeviceRole.objects.create(name='switch', slug='switch')
        cls.device1 = cls.create_device('switch1')
        cls.device2 = cls.create_device('switch2')

    @classmethod
    def create_module_type(cls, model, profile, side, interface_type, channels=None):
        module_type = ModuleType.objects.create(
            manufacturer=cls.manufacturer,
            model=model,
            profile=profile,
            attribute_data={'side': side, 'cable_type': 'dac-passive', 'length': 1},
        )
        parent = InterfaceTemplate.objects.create(
            module_type=module_type,
            name='Port {module}',
            type=interface_type,
            channels=channels,
        )
        # channel subinterfaces of a channelized (breakout) interface
        for channel in range(1, (channels or 0) + 1):
            InterfaceTemplate.objects.create(
                module_type=module_type,
                name=f'Port {{module}}:{channel}',
                type='10gbase-x-sfpp',
                parent=parent,
                channel_id=channel,
            )
        return module_type

    @classmethod
    def create_device(cls, name, bays=6):
        device = Device.objects.create(
            name=name,
            site=cls.site,
            device_type=cls.device_type,
            role=cls.device_role,
        )
        for i in range(1, bays + 1):
            ModuleBay.objects.create(device=device, name=f'Bay {i}', position=str(i))
        return device

    @staticmethod
    def get_bay(device, number):
        return device.modulebays.get(name=f'Bay {number}')

    @classmethod
    def create_module(cls, device, bay_number, module_type):
        return Module.objects.create(
            device=device,
            module_bay=cls.get_bay(device, bay_number),
            module_type=module_type,
        )

    @classmethod
    def create_assembly(cls, module_type=None, **kwargs):
        kwargs.setdefault('status', 'stored')
        return Asset.objects.create(module_type=module_type or cls.dac_type, **kwargs)
