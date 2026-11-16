"""
Compare CABLE_TYPE_LABELS (netbox_assets/assembly.py) with the cable types of
the installed NetBox, as CLAUDE.md requires for every supported NetBox
version. Exits with 1 if there is any difference.

Run from the NetBox root directory, with the plugin installed:

    python netbox/manage.py shell --no-startup --no-imports --interface python < scripts/cable-type-labels.py
"""

import sys

from dcim.choices import CableTypeChoices
from utilities.choices import unpack_grouped_choices

from netbox_assets.assembly import CABLE_TYPE_LABELS

netbox = {value: str(label) for value, label in unpack_grouped_choices(CableTypeChoices)}
diff = [
    value
    for value in sorted(netbox.keys() | CABLE_TYPE_LABELS.keys())
    if netbox.get(value) != CABLE_TYPE_LABELS.get(value)
]
for value in diff:
    print(f'{value}: NetBox={netbox.get(value)!r} plugin={CABLE_TYPE_LABELS.get(value)!r}')
print('differences:', len(diff))
if diff:
    print('See "Cable types of cable assemblies" in CLAUDE.md before changing anything.')
    sys.exit(1)
