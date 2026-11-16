"""
"Step by step: a 10G SFP+ DAC, 1 m" of docs/cable-assembly-profiles.md,
with the module type created in the form, as in the guide.
"""

import guide
from checks import assert_cable, assert_module_type, cable_summary

PROFILE = 'DAC SFP+ - SFP+'
MODEL = 'DAC-SFP-10G-1M'
NAME, SERIAL, ASSET_TAG = 'DAC-1', 'SN10001', 'ASSET-0001'


def test_dac_guide(nb):
    page = nb.page
    _block, (data,) = guide.module_type_block(MODEL)
    attrs = data['attribute_data']
    guide.assert_documented(
        PROFILE, MODEL, NAME, SERIAL, ASSET_TAG, 'switch-1', 'switch-2', 'Ethernet1/1',
        f'{NAME} [{SERIAL}]', 'Direct Attach Copper (Passive)', '1C1P', 'SFP+ (10GE)',
        'Add Components → Interfaces',
    )

    # Step 1. Import the profile
    nb.import_yaml('/dcim/module-type-profiles/', guide.profile(PROFILE))
    nb.api_one('dcim/module-type-profiles', name=PROFILE)

    # Step 2. Create the module type: the form shows the attributes of the profile
    nb.goto('/dcim/module-types/')
    nb.click_header_button('Add')
    nb.select('manufacturer', 'Generic', search='Gen')
    page.fill('input[name="model"]', MODEL)
    page.fill('input[name="part_number"]', data['part_number'])
    page.fill('input[name="description"]', data['description'])
    nb.select('profile', PROFILE)
    page.locator('[name="attr_side"]').wait_for(state='attached')
    labels = ' '.join(page.locator('#profile-attributes label').all_inner_texts())
    for label in ('Assembly side', 'A-side ends', 'B-side ends', 'Cable type', 'Length (m)'):
        assert label in labels, f'The module type form does not show the attribute {label}'
    for field, option in (
        ('attr_side', attrs['side']),
        ('attr_a_ends', str(attrs['a_ends'])),
        ('attr_b_ends', str(attrs['b_ends'])),
        ('attr_cable_type', attrs['cable_type']),
    ):
        if nb.selected(field) != option:
            nb.select(field, option)
    page.fill('input[name="attr_length"]', str(attrs['length']))
    nb.submit()

    # Step 2.4: Add Components → Interfaces, {module} of type SFP+ (10GE)
    page.locator('.page-header button', has_text='Add Components').first.click()
    page.locator('.page-header .dropdown-menu a', has_text='Interfaces').first.click()
    page.wait_for_load_state('networkidle')
    page.fill('input[name="name"]', '{module}')
    nb.select('type', 'SFP+ (10GE)', search='SFP+ (10')
    nb.submit()

    # the form made the same module type as the import block of the guide
    assert_module_type(nb, data)

    # Step 3. Create the asset: stored, with the two ends of the profile
    asset_url = nb.create_asset(MODEL, SERIAL, name=NAME, asset_tag=ASSET_TAG)
    summary, rows, warnings = nb.ends_panel(asset_url)
    assert [(r[0], r[1]) for r in rows] == [('SFP+ A', 'A'), ('SFP+ B', 'B')]
    assert 'created when ends on both sides are installed' in summary
    assert nb.asset_status(asset_url) == 'Stored'

    # Step 4. Install the ends: the module and its interface are created
    nb.install(asset_url, 'SFP+ A', 'switch-1', 'Ethernet1/1', preselected=MODEL)
    assert nb.asset_status(asset_url) == 'Used'
    module = nb.api_one('dcim/modules', device='switch-1')
    assert module['module_type']['model'] == MODEL
    nb.interface('switch-1', 'Ethernet1/1')
    nb.install(asset_url, 'SFP+ B', 'switch-2', 'Ethernet1/1', preselected=MODEL)

    # Step 5. Check the cable: shown on the asset page, a normal cable, traced
    summary, rows, warnings = nb.ends_panel(asset_url)
    assert summary == cable_summary(NAME, SERIAL, attrs, 1)
    assert not warnings
    assert [r[2:4] for r in rows] == [('switch-1', 'Ethernet1/1'), ('switch-2', 'Ethernet1/1')]
    assert_cable(nb, f'{NAME} [{SERIAL}]', attrs, ['switch-1 Ethernet1/1'], ['switch-2 Ethernet1/1'])
    a = nb.interface('switch-1', 'Ethernet1/1')
    b = nb.interface('switch-2', 'Ethernet1/1')
    assert nb.trace_far_ends(a['id']) == ['switch-2 Ethernet1/1']
    assert nb.trace_far_ends(b['id']) == ['switch-1 Ethernet1/1']
    assert 'Trace Completed' in nb.trace_page('switch-1', 'Ethernet1/1')
