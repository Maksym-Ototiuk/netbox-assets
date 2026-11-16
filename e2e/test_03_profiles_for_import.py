"""
"Profiles for import" of docs/cable-assembly-profiles.md: every profile and
module type block can be imported, and every product can be installed.

Runs after the guides (test_01, test_02): the products they installed are
only compared with their blocks.
"""

from itertools import count

import guide
from checks import assert_cable, assert_module_type, cable_summary

PROFILES = (
    'DAC SFP+ - SFP+', 'DAC SFP28 - SFP28', 'DAC QSFP28 - QSFP28', 'AOC QSFP28 - QSFP28',
    'Breakout QSFP+ - 4xSFP+', 'Breakout QSFP28 - 4xSFP28',
)


def test_profile_blocks_are_identical():
    """A profile shown in several blocks (guide and Profiles for import) is the same everywhere."""
    blocks = guide.profile_blocks()
    assert sorted(blocks) == sorted(PROFILES)
    for name, texts in blocks.items():
        assert all(text == texts[0] for text in texts), f'The blocks of {name} differ'


def import_missing(nb, blocks):
    """Import the profiles and module type blocks that the guides did not import."""
    for name in PROFILES:
        if not nb.api_list('dcim/module-type-profiles', name=name):
            nb.import_yaml('/dcim/module-type-profiles/', guide.profile(name))
    for block, docs in blocks:
        existing = [d for d in docs if nb.api_list('dcim/module-types', model=d['model'])]
        if not existing:
            nb.import_yaml('/dcim/module-types/', block)
        else:
            assert len(existing) == len(docs), f'Only some module types of {docs[0]["model"]} exist'
        for data in docs:
            assert_module_type(nb, data)


def side_b_module_types(blocks):
    """{(profile, manufacturer): [side B models]} of all products of the guide."""
    side_b = {}
    for _block, docs in blocks:
        for data in docs:
            if data['attribute_data']['side'] == 'B':
                side_b.setdefault((data['profile'], data['manufacturer']), []).append(data['model'])
    return side_b


class Devices:
    """The spare devices of e2e/seed.py, each used once."""

    def __init__(self):
        self.dac = (f'v-dac-{i}' for i in count(1))
        self.switches = (f'v-sw-{i}' for i in count(1))
        self.servers = (f'v-srv-{i}' for i in count(1))


def install_dac(nb, asset_url, ends, docs, devices):
    a = docs[0]
    assert a['attribute_data']['side'] == 'both' and len(docs) == 1
    pair = [next(devices.dac), next(devices.dac)]
    for end, device in zip(ends, pair):
        nb.install(asset_url, end, device, 'Ethernet1/1', preselected=a['model'])
    return [f'{pair[0]} Ethernet1/1'], [f'{pair[1]} Ethernet1/1']


def install_breakout(nb, asset_url, ends, docs, devices, side_b):
    a, b = docs
    assert [d['attribute_data']['side'] for d in docs] == ['A', 'B']
    alone = len(side_b[(b['profile'], b['manufacturer'])]) == 1
    switch = next(devices.switches)
    nb.install(asset_url, ends[0], switch, 'Ethernet1/49', preselected=a['model'])
    servers = [next(devices.servers) for _ in ends[1:]]
    for end, server in zip(ends[1:], servers):
        if alone:
            nb.install(asset_url, end, server, 'eth0', preselected=b['model'])
        else:
            # several products of this profile: the user chooses the side B type
            nb.install(asset_url, end, server, 'eth0', preselected='', module_type=b['model'])
    return [f'{switch} Ethernet1/49'], [f'{s} eth0' for s in servers]


def assert_traced(nb, model, a_ends, b_ends):
    """Each end of side B is traced to side A (to its channel for a breakout cable)."""
    for i, far in enumerate(b_ends, start=1):
        device, interface = far.split(' ')
        near = nb.trace_far_ends(nb.interface(device, interface)['id'])
        expected = a_ends[0] if len(b_ends) == 1 else f'{a_ends[0]}:{i}'
        assert near == [expected], (model, far, near)


def test_profiles_for_import(nb):
    blocks = guide.module_type_blocks()
    import_missing(nb, blocks)
    side_b = side_b_module_types(blocks)
    devices = Devices()
    installed = 0
    for n, (_block, docs) in enumerate(blocks, start=1):
        a = docs[0]
        attrs = a['attribute_data']
        module_type = nb.api_one('dcim/module-types', model=a['model'])
        if nb.api_list('plugins/assets/assets', module_type_id=module_type['id']):
            continue  # installed by a guide
        name, serial = f'P{n}', f'SNP{n:04}'
        asset_url = nb.create_asset(a['model'], serial, name=name)
        _summary, rows, _warnings = nb.ends_panel(asset_url)
        ends = [r[0] for r in rows]
        if attrs['b_ends'] == 1:
            a_ends, b_ends = install_dac(nb, asset_url, ends, docs, devices)
        else:
            a_ends, b_ends = install_breakout(nb, asset_url, ends, docs, devices, side_b)

        summary, _rows, warnings = nb.ends_panel(asset_url)
        assert summary == cable_summary(name, serial, attrs, attrs['b_ends']), a['model']
        assert not warnings
        assert nb.asset_status(asset_url) == 'Used'
        assert_cable(nb, f'{name} [{serial}]', attrs, a_ends, b_ends)
        assert_traced(nb, a['model'], a_ends, b_ends)
        installed += 1

    assert installed == len(blocks) - 2, 'Every product except those of the guides was installed'
