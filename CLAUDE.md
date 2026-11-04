# netbox-assets

## Cable types of cable assemblies

The module type attribute `cable_type` of a cable assembly holds the **label**
of a NetBox cable type (for example `Direct Attach Copper (Passive)`), because
the NetBox module type form shows the `enum` values of a profile as they are.
The plugin maps the label to the NetBox value (`dac-passive`) with its own
table `CABLE_TYPE_LABELS` in `netbox_assets/assembly.py`, copied from
`dcim.choices.CableTypeChoices` of NetBox 4.7.4. NetBox values are accepted
too.

Check that the values and labels of `CABLE_TYPE_LABELS` match NetBox for every
NetBox version the plugin supports (`min_version` / `max_version` in
`netbox_assets/__init__.py`):

- when the supported NetBox versions change or a new NetBox version is tested,
- when `CABLE_TYPE_LABELS` is changed.

Run in each NetBox version (from the NetBox root directory, with the plugin
installed):

```bash
python netbox/manage.py shell -c "
from dcim.choices import CableTypeChoices
from utilities.choices import unpack_grouped_choices
from netbox_assets.assembly import CABLE_TYPE_LABELS
netbox = {v: str(l) for v, l in unpack_grouped_choices(CableTypeChoices)}
diff = [v for v in sorted(netbox.keys() | CABLE_TYPE_LABELS.keys()) if netbox.get(v) != CABLE_TYPE_LABELS.get(v)]
for v in diff:
    print(f'{v}: NetBox={netbox.get(v)!r} plugin={CABLE_TYPE_LABELS.get(v)!r}')
print('differences:', len(diff))
"
```

The test `test_cable_type_labels` (`netbox_assets/tests/assembly/test_cables.py`)
fails if a value of `CABLE_TYPE_LABELS` does not exist in NetBox. Report every
difference to the user before changing anything:

- **NetBox renamed a label:** keep the plugin label. Module types store the
  label, so changing it breaks them. Both labels can be supported only by
  extending the mapping in `assembly.py`.
- **NetBox added a cable type:** add it with the NetBox label.
- **NetBox removed or renamed a value:** module types with this cable type get
  a cable without a type. Decide with the user how to map it.

Keep `README.md`, `docs/cable-assembly-profiles.md` and the tests in line with
`CABLE_TYPE_LABELS` (they name the NetBox version the labels come from).
