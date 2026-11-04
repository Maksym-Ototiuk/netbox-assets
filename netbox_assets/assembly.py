"""
Cable assemblies (DAC, AOC, breakout cables).

A cable assembly is one physical asset whose ends are separate NetBox modules.
Its topology is defined by a Module Type Profile: a profile is an assembly
profile if its JSON schema has the properties `side`, `a_ends` and `b_ends`.

- `a_ends` / `b_ends` hold the number of ends on side A and side B as a single
  integer value in `enum`, e.g. {"type": "integer", "enum": [4], "default": 4}.
- `side` is an attribute of each module type: "A", "B" or "both" (the same
  module type is used for both sides of a symmetric assembly).
- The optional top-level key `x-end-names` sets the names of the ends, e.g.
  {"A": ["QSFP+ A"], "B": ["SFP+ B1", "SFP+ B2", "SFP+ B3", "SFP+ B4"]}.
  Without it the ends are named A / B, or A1..An / B1..Bn.

Cable: when ends on both sides are installed, the plugin connects them with one
NetBox cable. Its type and length are the module type attributes `cable_type`
(a NetBox cable type, e.g. "Direct Attach Copper (Passive)" or "dac-passive",
see CABLE_TYPE_LABELS) and `length` (in meters). The NetBox cable profile
follows from the topology (1 + 1 ends: single 1C1P, 1 + N ends: 1CNP:NC1P
breakout) or is set with the optional top-level key `x-cable-profile`.
"""

from collections import namedtuple

from django.db.models import Q

from dcim.choices import CableProfileChoices, CableTypeChoices

__all__ = (
    'ASSEMBLY_PROPERTIES',
    'CABLE_PROFILE_KEY',
    'CABLE_TYPE_LABELS',
    'END_LABEL_MAX_LENGTH',
    'END_NAMES_KEY',
    'SIDE_A',
    'SIDE_B',
    'SIDE_BOTH',
    'AssemblySlot',
    'AssemblySpec',
    'assembly_module_type_q',
    'get_assembly_spec',
    'get_cable_type',
    'get_module_type_side',
    'is_assembly_module_type',
    'is_assembly_schema',
    'validate_assembly_schema',
)

ASSEMBLY_PROPERTIES = ('side', 'a_ends', 'b_ends')
END_NAMES_KEY = 'x-end-names'
CABLE_PROFILE_KEY = 'x-cable-profile'
END_LABEL_MAX_LENGTH = 32

SIDE_A = 'A'
SIDE_B = 'B'
SIDE_BOTH = 'both'
SIDES = (SIDE_A, SIDE_B, SIDE_BOTH)

AssemblySlot = namedtuple('AssemblySlot', ('label', 'side'))

# Labels of the NetBox cable types for the `cable_type` attribute. NetBox shows
# the `enum` values of a profile property as they are in the module type form,
# so profiles list these labels, and the plugin maps them to the NetBox cable
# type. The NetBox values (e.g. "dac-passive") are accepted too. The labels are
# copied from dcim.choices.CableTypeChoices (NetBox 4.7.4) and kept here, so
# that module types keep working if NetBox renames a label.
CABLE_TYPE_LABELS = {
    'cat3': 'CAT3',
    'cat5': 'CAT5',
    'cat5e': 'CAT5e',
    'cat6': 'CAT6',
    'cat6a': 'CAT6a',
    'cat7': 'CAT7',
    'cat7a': 'CAT7a',
    'cat8': 'CAT8',
    'mrj21-trunk': 'MRJ21 Trunk',
    'dac-active': 'Direct Attach Copper (Active)',
    'dac-passive': 'Direct Attach Copper (Passive)',
    'coaxial': 'Coaxial',
    'rg-6': 'RG-6',
    'rg-8': 'RG-8',
    'rg-11': 'RG-11',
    'rg-59': 'RG-59',
    'rg-62': 'RG-62',
    'rg-213': 'RG-213',
    'lmr-100': 'LMR-100',
    'lmr-200': 'LMR-200',
    'lmr-400': 'LMR-400',
    'mmf': 'Multimode Fiber',
    'mmf-om1': 'Multimode Fiber (OM1)',
    'mmf-om2': 'Multimode Fiber (OM2)',
    'mmf-om3': 'Multimode Fiber (OM3)',
    'mmf-om4': 'Multimode Fiber (OM4)',
    'mmf-om5': 'Multimode Fiber (OM5)',
    'smf': 'Single-mode Fiber',
    'smf-os1': 'Single-mode Fiber (OS1)',
    'smf-os2': 'Single-mode Fiber (OS2)',
    'aoc': 'Active Optical Cabling (AOC)',
    'power': 'Power',
    'usb': 'USB',
}
_CABLE_TYPES_BY_LABEL = {label: value for value, label in CABLE_TYPE_LABELS.items()}


def assembly_module_type_q(prefix='module_type'):
    """
    Q() that matches objects whose module type has an assembly profile.
    `prefix` is the path to the module type, e.g. 'module_type' for Asset or
    'module__module_type' for AssetModuleEnd.
    """
    return Q(
        **{f'{prefix}__profile__schema__properties__has_keys': ASSEMBLY_PROPERTIES}
    )


def is_assembly_schema(schema):
    properties = schema.get('properties') if isinstance(schema, dict) else None
    if not isinstance(properties, dict):
        return False
    return all(name in properties for name in ASSEMBLY_PROPERTIES)


def is_assembly_module_type(module_type):
    if module_type is None or module_type.profile_id is None:
        return False
    return is_assembly_schema(module_type.profile.schema)


def get_module_type_side(module_type):
    """Return side of a module type ("A", "B" or "both"), or None if not set."""
    side = (module_type.attribute_data or {}).get('side')
    return side if side in SIDES else None


def get_cable_type(name):
    """
    NetBox cable type for the value of a `cable_type` attribute: the label of
    the cable type (see CABLE_TYPE_LABELS) or its NetBox value. None if it is
    not a NetBox cable type.
    """
    if not isinstance(name, str):
        return None
    value = _CABLE_TYPES_BY_LABEL.get(name, name)
    return value if value in CableTypeChoices.values() else None


def _fixed_integer(prop):
    """Return the single integer value of a property (single-value enum)."""
    enum = prop.get('enum') if isinstance(prop, dict) else None
    if not isinstance(enum, list) or len(enum) != 1:
        return None
    value = enum[0]
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


def _default_labels(side, count):
    if count == 1:
        return [side]
    return [f'{side}{i}' for i in range(1, count + 1)]


def default_cable_profile(a_ends, b_ends):
    """NetBox cable profile for a topology, '' if there is no matching one."""
    if a_ends == 1 and b_ends == 1:
        return CableProfileChoices.SINGLE_1C1P
    profile = f'breakout-1c{b_ends}p-{b_ends}c1p'
    if a_ends == 1 and profile in CableProfileChoices.values():
        return profile
    return ''


def _cable_profile_class(profile):
    from dcim.models import Cable

    return Cable(profile=profile).profile_class


def _validate_cable(schema, counts):
    """Return errors for the cable profile and the cable_type property."""
    errors = []
    profile = schema.get(CABLE_PROFILE_KEY)
    if profile is not None:
        if profile not in CableProfileChoices.values():
            errors.append(
                f'"{CABLE_PROFILE_KEY}": unknown NetBox cable profile "{profile}".'
            )
        elif counts.keys() == {SIDE_A, SIDE_B}:
            profile_class = _cable_profile_class(profile)
            if (
                len(profile_class.a_connectors) < counts[SIDE_A]
                or len(profile_class.b_connectors) < counts[SIDE_B]
            ):
                errors.append(
                    f'"{CABLE_PROFILE_KEY}": cable profile "{profile}" has too few '
                    f'connectors for {counts[SIDE_A]} side A and {counts[SIDE_B]} '
                    f'side B ends.'
                )
    cable_types = schema['properties'].get('cable_type', {}).get('enum') or []
    if unknown := [t for t in cable_types if get_cable_type(t) is None]:
        errors.append(
            f'Property "cable_type": unknown NetBox cable types: '
            f'{", ".join(map(str, unknown))}. Use the label of a NetBox cable '
            f'type (for example "Direct Attach Copper (Passive)") or its value '
            f'("dac-passive").'
        )
    return errors


def _validate_end_counts(properties):
    """Return (counts by side, errors) for the a_ends and b_ends properties."""
    counts = {}
    errors = []
    for side, name in ((SIDE_A, 'a_ends'), (SIDE_B, 'b_ends')):
        prop = properties[name]
        value = _fixed_integer(prop)
        if value is None:
            errors.append(
                f'Property "{name}" must have exactly one integer value of 1 or '
                f'more in "enum", for example {{"type": "integer", "enum": [1], "default": 1}}.'
            )
            continue
        if 'default' in prop and prop['default'] != value:
            errors.append(
                f'Property "{name}": "default" must be the same as the value in "enum" ({value}).'
            )
        counts[side] = value
    return counts, errors


def _validate_end_names(names, counts):
    """Return errors for the optional x-end-names key."""
    if not isinstance(names, dict) or set(names) - {SIDE_A, SIDE_B}:
        return [
            f'"{END_NAMES_KEY}" must be an object with the keys "A" and "B", '
            f'each a list of end names.'
        ]
    errors = []
    all_labels = []
    for side in (SIDE_A, SIDE_B):
        labels = names.get(side)
        if labels is None:
            continue
        if not isinstance(labels, list) or not all(
            isinstance(label, str) and label.strip() for label in labels
        ):
            errors.append(
                f'"{END_NAMES_KEY}.{side}" must be a list of non-empty strings.'
            )
            continue
        if side in counts and len(labels) != counts[side]:
            errors.append(
                f'"{END_NAMES_KEY}.{side}" has {len(labels)} names, but the '
                f'profile defines {counts[side]} side {side} ends.'
            )
        all_labels.extend(labels)
    too_long = [label for label in all_labels if len(label) > END_LABEL_MAX_LENGTH]
    if too_long:
        errors.append(
            f'End names cannot be longer than {END_LABEL_MAX_LENGTH} '
            f'characters: {", ".join(too_long)}'
        )
    duplicates = sorted({label for label in all_labels if all_labels.count(label) > 1})
    if duplicates:
        errors.append(f'End names must be unique: {", ".join(duplicates)}')
    return errors


def validate_assembly_schema(schema):
    """
    Return a list of error messages for an assembly profile schema. An empty
    list means the schema is valid (or is not an assembly schema at all).
    """
    if not is_assembly_schema(schema):
        return []
    counts, errors = _validate_end_counts(schema['properties'])
    if schema.get(END_NAMES_KEY) is not None:
        errors += _validate_end_names(schema[END_NAMES_KEY], counts)
    errors += _validate_cable(schema, counts)
    return errors


class AssemblySpec:
    """
    Ends (slots) of a cable assembly as defined by its profile: side A slots
    first, then side B slots.
    """

    def __init__(self, a_labels, b_labels, cable_profile=None):
        self.slots = [AssemblySlot(label, SIDE_A) for label in a_labels] + [
            AssemblySlot(label, SIDE_B) for label in b_labels
        ]
        if cable_profile is None:
            cable_profile = default_cable_profile(len(a_labels), len(b_labels))
        # NetBox cable profile of the assembly cable ('' for none)
        self.cable_profile = cable_profile

    @classmethod
    def from_schema(cls, schema):
        """Return AssemblySpec for a valid assembly schema, otherwise None."""
        if not is_assembly_schema(schema) or validate_assembly_schema(schema):
            return None
        properties = schema['properties']
        a_ends = _fixed_integer(properties['a_ends'])
        b_ends = _fixed_integer(properties['b_ends'])
        names = schema.get(END_NAMES_KEY) or {}
        return cls(
            names.get(SIDE_A) or _default_labels(SIDE_A, a_ends),
            names.get(SIDE_B) or _default_labels(SIDE_B, b_ends),
            schema.get(CABLE_PROFILE_KEY),
        )

    @property
    def labels(self):
        return [slot.label for slot in self.slots]

    @property
    def a_ends(self):
        return sum(1 for slot in self.slots if slot.side == SIDE_A)

    @property
    def b_ends(self):
        return sum(1 for slot in self.slots if slot.side == SIDE_B)

    def side_labels(self, side):
        return [slot.label for slot in self.slots if slot.side == side]

    def get_slot(self, label):
        for slot in self.slots:
            if slot.label == label:
                return slot
        return None

    def index(self, label):
        """Position of a slot, used to sort ends in slot order."""
        try:
            return self.labels.index(label)
        except ValueError:
            return len(self.slots)


def get_assembly_spec(module_type):
    """Return AssemblySpec of a module type, or None if it is not an assembly."""
    if not is_assembly_module_type(module_type):
        return None
    return AssemblySpec.from_schema(module_type.profile.schema)
