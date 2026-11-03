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
"""

from collections import namedtuple

from django.db.models import Q

__all__ = (
    'ASSEMBLY_PROPERTIES',
    'END_LABEL_MAX_LENGTH',
    'END_NAMES_KEY',
    'SIDE_A',
    'SIDE_B',
    'SIDE_BOTH',
    'AssemblySlot',
    'AssemblySpec',
    'assembly_module_type_q',
    'get_assembly_spec',
    'get_module_type_side',
    'is_assembly_module_type',
    'is_assembly_schema',
    'validate_assembly_schema',
)

ASSEMBLY_PROPERTIES = ('side', 'a_ends', 'b_ends')
END_NAMES_KEY = 'x-end-names'
END_LABEL_MAX_LENGTH = 32

SIDE_A = 'A'
SIDE_B = 'B'
SIDE_BOTH = 'both'
SIDES = (SIDE_A, SIDE_B, SIDE_BOTH)

AssemblySlot = namedtuple('AssemblySlot', ('label', 'side'))


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
    return errors


class AssemblySpec:
    """
    Ends (slots) of a cable assembly as defined by its profile: side A slots
    first, then side B slots.
    """

    def __init__(self, a_labels, b_labels):
        self.slots = [AssemblySlot(label, SIDE_A) for label in a_labels] + [
            AssemblySlot(label, SIDE_B) for label in b_labels
        ]

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
