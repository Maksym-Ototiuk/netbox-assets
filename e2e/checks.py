"""Checks shared by the end-to-end tests."""

CABLE_PROFILE = {1: ('single-1c1p', '1C1P'), 4: ('breakout-1c4p-4c1p', '1C4P:4C1P breakout')}
# NetBox cable type of each cable_type label used in the guide
CABLE_TYPE = {
    'Direct Attach Copper (Passive)': 'dac-passive',
    'Direct Attach Copper (Active)': 'dac-active',
    'Active Optical Cabling (AOC)': 'aoc',
}


def value(choice):
    return choice['value'] if isinstance(choice, dict) else choice


def termination_names(terminations):
    names = []
    for termination in terminations:
        obj = termination.get('object', termination)
        names.append(f'{obj["device"]["name"]} {obj["name"]}')
    return names


def assert_module_type(nb, data):
    """The module type in NetBox matches a module type of the guide (YAML data)."""
    module_type = nb.api_one('dcim/module-types', model=data['model'])
    assert module_type['manufacturer']['name'] == data['manufacturer']
    assert module_type['profile']['name'] == data['profile']
    assert (module_type['part_number'] or None) == data.get('part_number')
    assert module_type['attributes'] == data['attribute_data'], data['model']
    templates = nb.api_list('dcim/interface-templates', module_type_id=module_type['id'])
    actual = sorted(
        (
            t['name'],
            value(t['type']),
            t.get('channels'),
            t.get('channel_id'),
            t['parent']['name'] if t.get('parent') else None,
        )
        for t in templates
    )
    expected = sorted(
        (i['name'], i['type'], i.get('channels'), i.get('channel_id'), i.get('parent'))
        for i in data['interfaces']
    )
    assert actual == expected, f'Interface templates of {data["model"]}'
    return module_type


def assert_cable(nb, label, attrs, a_ends, b_ends):
    """The assembly cable has the type, length, profile and terminations of the guide."""
    cable = nb.api_one('dcim/cables', label=label)
    profile_value, _profile_label = CABLE_PROFILE[len(b_ends)]
    assert value(cable['type']) == CABLE_TYPE[attrs['cable_type']], cable['type']
    assert float(cable['length']) == float(attrs['length'])
    assert value(cable['length_unit']) == 'm'
    assert value(cable['profile']) == profile_value, cable['profile']
    assert value(cable['status']) == 'connected'
    assert termination_names(cable['a_terminations']) == a_ends
    assert termination_names(cable['b_terminations']) == b_ends
    return cable


def cable_summary(name, serial, attrs, b_ends):
    """The cable line of the Assembly Ends panel, as in the guide's screenshots."""
    return (
        f'Cable: {name} [{serial}] ({attrs["cable_type"]}, {attrs["length"]:g} m, '
        f'{CABLE_PROFILE[b_ends][1]})'
    )
