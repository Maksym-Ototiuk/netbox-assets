"""
Create the devices that the end-to-end tests install cable assemblies in.

Run in a fresh NetBox with netbox-assets installed:

    python netbox/manage.py shell --no-startup --no-imports --interface python < e2e/seed.py

The devices are those of docs/cable-assembly-profiles.md (switch-1 and switch-2
for the DAC guide, switch-3 and server-1 to server-4 for the breakout guide)
and spare devices (v-*) for the products of "Profiles for import". Each device
type has one module bay whose position is the interface name, as the guide
describes.
"""

from dcim.models import (
    Device,
    DeviceRole,
    DeviceType,
    Manufacturer,
    ModuleBayTemplate,
    Site,
)

site, _ = Site.objects.get_or_create(name='DC1', defaults={'slug': 'dc1'})
manufacturer, _ = Manufacturer.objects.get_or_create(name='Generic', defaults={'slug': 'generic'})
roles = {
    name: DeviceRole.objects.get_or_create(name=name, defaults={'slug': name.lower(), 'color': color})[0]
    for name, color in (('Switch', '2196f3'), ('Server', '4caf50'))
}

DEVICE_TYPES = (
    # model, module bay (name = position), role, devices
    ('Test Switch', 'Ethernet1/1', 'Switch',
     ['switch-1', 'switch-2'] + [f'v-dac-{i}' for i in range(1, 13)]),
    ('Test Switch QSFP', 'Ethernet1/49', 'Switch',
     ['switch-3'] + [f'v-sw-{i}' for i in range(1, 5)]),
    ('Test Server', 'eth0', 'Server',
     [f'server-{i}' for i in range(1, 5)] + [f'v-srv-{i}' for i in range(1, 17)]),
)

for model, bay, role, names in DEVICE_TYPES:
    slug = model.lower().replace(' ', '-')
    device_type, _ = DeviceType.objects.get_or_create(
        manufacturer=manufacturer, model=model, defaults={'slug': slug}
    )
    ModuleBayTemplate.objects.get_or_create(
        device_type=device_type, name=bay, defaults={'position': bay}
    )
    for name in names:
        if not Device.objects.filter(name=name).exists():
            device = Device(name=name, site=site, role=roles[role], device_type=device_type)
            device.full_clean()
            device.save()

print(f'Seeded {Device.objects.count()} devices')
