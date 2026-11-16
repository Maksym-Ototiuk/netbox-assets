"""
"Step by step: a 40G QSFP+ to 4x 10G SFP+ breakout cable, 3 m" of
docs/cable-assembly-profiles.md.
"""

import guide
from checks import assert_cable, assert_module_type, cable_summary, termination_names

PROFILE = 'Breakout QSFP+ - 4xSFP+'
MODEL_A, MODEL_B = 'BRK-QSFP-4SFP-10G-3M-A', 'BRK-QSFP-4SFP-10G-3M-B'
NAME, SERIAL, ASSET_TAG = 'BRK-1', 'SN20001', 'ASSET-0002'
SERVERS = [f'server-{i}' for i in range(1, 5)]
B_ENDS = [f'SFP+ B{i}' for i in range(1, 5)]


def test_breakout_guide(nb):
    block, docs = guide.module_type_block(MODEL_A)
    attrs = docs[0]['attribute_data']
    guide.assert_documented(
        PROFILE, MODEL_A, MODEL_B, NAME, SERIAL, ASSET_TAG, 'switch-3', 'Ethernet1/49',
        'Ethernet1/49:2', 'server-2 eth0', f'{NAME} [{SERIAL}]', '1C4P:4C1P breakout',
        'No paths found',
    )

    # Step 1. Import the breakout profile
    nb.import_yaml('/dcim/module-type-profiles/', guide.profile(PROFILE))

    # Step 2. Create the side A and side B module types (one import block)
    assert [d['model'] for d in docs] == [MODEL_A, MODEL_B]
    nb.import_yaml('/dcim/module-types/', block)
    for data in docs:
        assert_module_type(nb, data)

    # Step 3. Create the breakout asset with the side A module type: five ends
    asset_url = nb.create_asset(MODEL_A, SERIAL, name=NAME, asset_tag=ASSET_TAG)
    _summary, rows, _warnings = nb.ends_panel(asset_url)
    assert [(r[0], r[1]) for r in rows] == [('QSFP+ A', 'A')] + [(end, 'B') for end in B_ENDS]

    # Step 4. Install the QSFP+ end and the SFP+ ends; the side B type is preselected
    nb.install(asset_url, 'QSFP+ A', 'switch-3', 'Ethernet1/49', preselected=MODEL_A)
    nb.install(asset_url, 'SFP+ B1', 'server-1', 'eth0', preselected=MODEL_B)

    # a gap (B1 and B3 without B2): no cable profile and a warning
    nb.install(asset_url, 'SFP+ B3', 'server-3', 'eth0', preselected=MODEL_B)
    summary, _rows, warnings = nb.ends_panel(asset_url)
    assert summary == f'Cable: {NAME} [{SERIAL}] ({attrs["cable_type"]}, {attrs["length"]:g} m)'
    assert len(warnings) == 1 and 'gap' in warnings[0], warnings

    nb.install(asset_url, 'SFP+ B2', 'server-2', 'eth0', preselected=MODEL_B)
    nb.install(asset_url, 'SFP+ B4', 'server-4', 'eth0', preselected=MODEL_B)

    # Step 5. Check the breakout cable
    summary, rows, warnings = nb.ends_panel(asset_url)
    assert summary == cable_summary(NAME, SERIAL, attrs, 4)
    assert not warnings, warnings
    assert [r[2:4] for r in rows] == [('switch-3', 'Ethernet1/49')] + [(s, 'eth0') for s in SERVERS]
    assert_cable(
        nb, f'{NAME} [{SERIAL}]', attrs, ['switch-3 Ethernet1/49'], [f'{s} eth0' for s in SERVERS]
    )

    # the side A module created the channelized interface and its four channels
    interfaces = {i['name']: i for i in nb.api_list('dcim/interfaces', device='switch-3')}
    assert sorted(interfaces) == ['Ethernet1/49'] + [f'Ethernet1/49:{i}' for i in range(1, 5)]
    assert interfaces['Ethernet1/49']['channels'] == 4

    # each channel is traced to its SFP+ end, and back
    for i, server in enumerate(SERVERS, start=1):
        channel = interfaces[f'Ethernet1/49:{i}']
        assert channel['channel_id'] == i and channel['parent']['name'] == 'Ethernet1/49'
        assert nb.trace_far_ends(channel['id']) == [f'{server} eth0']
        assert nb.trace_far_ends(nb.interface(server, 'eth0')['id']) == [f'switch-3 Ethernet1/49:{i}']
    assert 'Trace Completed' in nb.trace_page('switch-3', 'Ethernet1/49:2')
    # the parent has no path of its own
    assert 'No paths found' in nb.trace_page('switch-3', 'Ethernet1/49')

    # Uninstall a breakout cable
    nb.uninstall(asset_url, 'SFP+ B4')
    cable = nb.api_one('dcim/cables', label=f'{NAME} [{SERIAL}]')
    assert termination_names(cable['b_terminations']) == [f'{s} eth0' for s in SERVERS[:3]]

    nb.uninstall(asset_url, 'QSFP+ A')
    assert not nb.api_list('dcim/cables', label=f'{NAME} [{SERIAL}]')
    summary, _rows, _warnings = nb.ends_panel(asset_url)
    assert 'created when ends on both sides are installed' in summary

    for end in B_ENDS[:3]:
        nb.uninstall(asset_url, end)
    assert nb.asset_status(asset_url) == 'Stored'
    # the modules stay in NetBox
    for device in ['switch-3'] + SERVERS:
        assert len(nb.api_list('dcim/modules', device=device)) == 1, device
