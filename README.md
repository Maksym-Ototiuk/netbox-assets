# NetBox Assets

A [NetBox](https://github.com/netbox-community/netbox) plugin for simple asset
tracking: keep a record of hardware (devices, modules and racks) that is **not
currently installed**, for example spare parts and equipment in storage.

> **This project is a stripped-down fork of
> [netbox-inventory](https://github.com/ArnesSI/netbox-inventory)** by Arnes.
> It is based on upstream commit
> [`e749f6f`](https://github.com/ArnesSI/netbox-inventory/commit/e749f6fd0aa2494746218537deb5c8727a0fe04a)
> (v2.7.0). All credit for the original design and code goes to the upstream
> authors. If you need the full feature set (inventory item types and groups,
> suppliers, purchases, deliveries, warranty tracking, audit flows), use the
> original plugin.

## Purpose

NetBox documents what is installed in your network. netbox-assets adds a
place for hardware that is not installed yet, or not any more: what it is,
its serial number and asset tag, and where it is stored. When an asset is
installed, you link it to the device, module or rack that represents it in
NetBox.

The goal is simple record keeping, not full inventory management.

## Differences from netbox-inventory

| Feature                           | netbox-inventory              | netbox-assets                                    |
| --------------------------------- | ----------------------------- | ------------------------------------------------ |
| Assets                            | Yes                           | Yes                                              |
| Asset roles (hierarchical)        | Yes (django-mptt)             | Yes (PostgreSQL `ltree`, native to NetBox 4.7)   |
| Asset kinds: device, module, rack | Yes                           | Yes                                              |
| Asset kind: inventory item        | Yes                           | Removed (inventory items are deprecated in NetBox since v4.3) |
| Inventory item types and groups   | Yes                           | Removed                                          |
| Suppliers, purchases, deliveries  | Yes                           | Removed                                          |
| Warranty tracking                 | Yes                           | Removed                                          |
| Audit flows and audit trails      | Yes                           | Removed                                          |
| Navigation menu                   | "Inventory" (configurable)    | Always a top-level "Assets" menu                 |

## Limitations

- **Cannot be installed together with netbox-inventory.** Both plugins define
  the same relations on NetBox core models (for example
  `Device.assigned_asset`) and the same GraphQL type names. netbox-assets
  refuses to start if `netbox_inventory` is also enabled. This is a
  deliberate simplification.
- **No data migration from netbox-inventory.** netbox-assets is meant for a
  clean installation. It ships its own fresh database migrations and does not
  read or convert netbox-inventory data.

## Compatibility

| NetBox           | netbox-assets |
| ---------------- | ------------- |
| 4.7.4 and later  | 1.2.x         |
| 4.7.2 to 4.7.3   | 1.1.x         |

NetBox 4.7 requires Python 3.12 or later, PostgreSQL 15 or later with the
`ltree` extension, and Redis 6 or later.

NetBox 4.7.0 is not supported: the database triggers that maintain
hierarchical paths could not be restored from a database dump in that release
([netbox#23130](https://github.com/netbox-community/netbox/issues/23130)).

## Features

- Assets with name, asset tag, serial number, status, role, description,
  comments, tags, custom fields and images.
- Each asset has exactly one hardware type: a device type, a module type or a
  rack type.
- Assign an asset to a device, module or rack, reassign it or unassign it.
- Cable assemblies (DAC, AOC, breakout cables): one asset whose ends are
  installed as separate modules, see
  [Cable assemblies](#cable-assemblies-dac--aoc--breakout).
- Create a new device, module or rack directly from an asset.
- Storage location, tenant, owning tenant and contact for each asset.
- Automatic status: `stored` when an asset is unassigned, `used` when it is
  assigned (configurable).
- Optional synchronization of serial number and asset tag between an asset and
  the hardware it is assigned to.
- Bulk add with an asset tag pattern, for example `ASSET-[001-010]`.
- Bulk import, export, edit and delete.
- Hierarchical asset roles (for example Optics → SFP) with cumulative asset
  counts.
- Asset information on Device, Module and Rack pages, and asset counts on
  Site, Location, Rack, Tenant, Contact and Manufacturer pages.
- Global search, REST API and GraphQL API.

## Usage

1. **Create an asset.** In *Assets → Assets*, click *Add* and choose the
   hardware type (a device type, module type or rack type). Fill in the serial
   number, asset tag, storage location and so on. This form describes *what*
   the hardware is. It does not link the asset to a particular device.
2. **Assign the asset to hardware.** Use one of these buttons:
   - *Edit Assignment* in the *Assigned To* panel on the asset page;
   - *Edit Assignment* in the *Asset* panel on a device, module or rack page;
   - *Create Device* (or *Create Module*, *Create Rack*) on the asset page, to
     create the hardware and assign the asset in one step.

   When an asset is assigned, its status changes to `used`. When it is
   unassigned, its status changes to `stored` (see [Settings](#settings)).

Assets are displayed as `<manufacturer> <model> <name>`, for example
`Cisco ASR edge-01`, or as `<manufacturer> <model>` when the asset has no
name. Unnamed assets of the same model look the same in lists and selection
fields, so give assets a name if you need to tell them apart.

## Cable assemblies (DAC / AOC / breakout)

DAC, AOC and breakout cables are **one physical asset** (one serial number,
one asset tag), but in NetBox each end is a separate **module**: following the
NetBox practice for pluggable transceivers, every port is a module bay, and
the plug of the cable is a module installed in it. A breakout cable such as
QSFP+ to 4x SFP+ has five ends. netbox-assets lets one asset be installed as
several modules, the **ends** of the cable assembly.

### Concept

- The **topology** of a cable assembly is defined by a NetBox **Module Type
  Profile**, one profile per topology (not per product or length), for
  example `DAC SFP+ - SFP+` or `Breakout QSFP+ - 4xSFP+`.
- A profile is a **cable assembly profile** if its JSON schema has the
  properties `side`, `a_ends` and `b_ends`. No plugin setting is needed.
- `a_ends` and `b_ends` are the numbers of ends on side A and side B. They are
  fixed in the profile (one integer value in `enum`) and the plugin reads them
  from the profile.
- The optional top-level schema key `x-end-names` sets the names of the ends,
  for example `SFP+ A`, `SFP+ B`. Without it the ends are named `A` / `B`, or
  `A1`…`An` / `B1`…`Bn`.
- Each **module type** of the profile is a product (for example one length)
  and has the attribute `side`: `A`, `B`, or `both` for symmetric assemblies
  where both ends are the same (DAC SFP+ - SFP+).
- An asset whose module type has a cable assembly profile is a **cable
  assembly**. Its module type is the side `A` or `both` module type.
- Installing an end links one end of the asset to a module (model
  `AssetModuleEnd`). A cable assembly is never assigned to a module directly.
- When ends on both sides are installed, the plugin **creates the NetBox
  cable** between their interfaces, with the cable type (`cable_type`) and the
  length (`length`) of the module type. A breakout cable is one cable with
  one side A and up to four side B terminations.

Example profile for a breakout cable:

```json
{
  "type": "object",
  "x-end-names": {"A": ["QSFP+ A"], "B": ["SFP+ B1", "SFP+ B2", "SFP+ B3", "SFP+ B4"]},
  "properties": {
    "side":   {"type": "string",  "title": "Assembly side", "enum": ["A", "B"]},
    "a_ends": {"type": "integer", "title": "A-side ends",   "enum": [1], "default": 1},
    "b_ends": {"type": "integer", "title": "B-side ends",   "enum": [4], "default": 4},
    "cable_type": {"type": "string", "title": "Cable type", "enum": ["Direct Attach Copper (Passive)", "Direct Attach Copper (Active)", "Active Optical Cabling (AOC)"]},
    "length": {"type": "number",  "title": "Length (m)", "minimum": 0}
  },
  "required": ["side", "cable_type", "length"]
}
```

**[Cable assembly profiles](docs/cable-assembly-profiles.md)** has six
ready-to-use profiles (DAC SFP+, DAC SFP28, DAC QSFP28, AOC QSFP28, breakout
QSFP+ to 4x SFP+ and QSFP28 to 4x SFP28) with an import block, module types
and installation examples, and the rules for writing your own profiles.

### Setup and usage

1. Create the profiles: *Devices → Module Type Profiles* (or import them from
   the [examples](docs/cable-assembly-profiles.md#import-all-profiles)).
2. Create the module types with the profile and the attributes `side`,
   `cable_type` and `length`: one `both` module type for a symmetric
   assembly, or a side `A` and a side `B` module type for a breakout cable.
   Add one interface template for the port (for a breakout QSFP end: a
   channelized interface with its channel subinterfaces).
3. Create the asset with the side `A` (or `both`) module type. It is
   `stored`.
4. On the asset page, the **Assembly Ends** panel lists all ends of the
   profile. Click **Install** next to an end and select the device and module
   bay. If a module is installed in the bay, it becomes the end; if the bay is
   empty, the plugin creates the module. **Uninstall** removes the end; the
   module stays in NetBox.
5. When ends on both sides are installed, the plugin creates the NetBox
   cable, see [Cable](#cable).

The panel shows for each end the device, module bay, module, its interfaces
and the connected cable, and which end is the primary end. A module page
shows the cable assembly and the end for modules that are ends. The list of
all ends is not in the menu; open `/plugins/assets/assembly-ends/` (or the
*Assembly Ends* breadcrumb on the page of an end) to filter, export and
delete ends in bulk, and `/plugins/assets/assembly-ends/import/` to import
them.

### Rules

An end can be installed only if:

- the asset is a cable assembly;
- the end exists in the profile and is not installed yet;
- the module has the right module type: side A ends (and both ends of a
  symmetric assembly) must be modules of the asset's module type; side B ends
  must be modules of a side `B` module type with the same profile;
- the module is not assigned to another asset (and an end module cannot be
  assigned to another asset).

The number of ends in the profile is a maximum: a cable assembly can have no
ends installed (in storage) or only some of them.

To keep existing cable assemblies valid, the plugin refuses:

- to change the module type of an asset or a module that has ends installed;
- to change the profile or the `side` of a module type used by cable
  assemblies, or to set a cable assembly profile on a module type whose assets
  are assigned to modules;
- to save an invalid cable assembly profile, to remove `side`, `a_ends` or
  `b_ends` from a profile that is in use, or to remove an end that is
  installed.

### Status, primary end and synchronization

- **Status:** a cable assembly becomes `used` when its first end is installed
  and `stored` when its last end is removed (the same settings as for other
  assets, see [Settings](#settings)).
- **Primary end:** the end in the first side A slot is the primary end. If it
  is not installed, the first installed end (in the order of the profile) is
  the primary end. You can make another end primary (*Make primary* button);
  if the primary end is removed, the next end becomes primary.
- **Location:** a cable assembly is shown where its primary end is installed
  (`installed_site`, `installed_device` and so on). Filters for the installed
  site, location, rack and device match any installed end.
- **Synchronization** (when `sync_hardware_serial_asset_tag` is enabled): the
  serial number is copied to the modules of all ends, the asset tag only to
  the module of the primary end (asset tags of modules are unique in NetBox).
  Serial and asset tag can then be changed only on the asset. They are
  cleared from a module when its end is uninstalled. When the asset itself is
  deleted, the values stay on the modules, as for other assets.
- **Deleted modules:** when the module of an end is deleted (or the device of
  the module), the end is removed and the status and primary end are updated.

### Cable

The plugin keeps one NetBox cable per cable assembly (shown in the *Assembly
Ends* panel and as `assembly_cable` in the API):

- **Created** when at least one end on side A and one end on side B are
  installed, between the interfaces of their modules (the only interface of
  the module that is not a channel subinterface; for a breakout QSFP end, the
  channelized interface).
- **Type and length** come from the module type of the asset: `cable_type`,
  the label of a NetBox cable type such as `Direct Attach Copper (Passive)`
  (the module type form shows the values of the profile as they are, so
  profiles list the labels; the NetBox value `dac-passive` works too), and
  `length` in meters. The status is `connected` and the label is the asset
  tag (or the name) when the cable is created.
- **Cable profile:** `1C1P` for 1 + 1 ends, `1CNP:NC1P breakout` for 1 + N
  ends (or the profile key `x-cable-profile`). Side B ends are terminated in
  the order of the slots, so NetBox traces each channel of a breakout cable
  to its end. NetBox assigns connectors by the order of the terminations: if
  the installed side B ends have a gap (B1 and B3 without B2), the cable has
  no cable profile and the panel shows a warning, until the gap is closed.
- **Updated** when an end is installed or uninstalled, and when `cable_type`,
  `length` or the cable profile of the module type or profile change.
  Uninstalling a side B end of a breakout cable removes only this end from
  the cable.
- **Deleted** when no end is left on one side: uninstalling the side A end, or
  the last side B end, or the only other end of a DAC. The same happens when
  the module or the device of an end is deleted.
- When the asset is deleted, the cable stays as a normal NetBox cable.

Only label, description, color, status, tenancy, ownership, comments, tags
and custom fields of an assembly cable can be changed in NetBox. Its type,
profile, length and terminations cannot be changed, and it cannot be deleted
directly: install or uninstall the ends of the assembly instead.

Installing an end is refused if the interface of the module already has
another cable (delete it first), if the module does not have exactly one
interface for the cable, or if the user is not allowed to add, change or
delete cables (whatever installing or uninstalling the end does to the
cable).

### Limitations
- Only modules can be ends. Module bay types are not checked by the plugin;
  use NetBox module bay types (NetBox 4.7) if ends must fit certain bays
  only.
- An end module can be moved to another module bay with NetBox, the end moves
  with it. NetBox does not move modules between devices while their
  interfaces are cabled.
- The REST API installs ends on existing modules only; the creation of a
  module in an empty module bay is available in the web form.

## Installation

Activate the NetBox virtual environment and install the package:

```shell
source /opt/netbox/venv/bin/activate
pip install netbox-assets
```

To keep the plugin installed after NetBox upgrades, add it to
`local_requirements.txt`:

```shell
echo netbox-assets >> /opt/netbox/local_requirements.txt
```

Enable the plugin in `/opt/netbox/netbox/netbox/configuration.py`:

```python
PLUGINS = [
    'netbox_assets',
]

PLUGINS_CONFIG = {
    'netbox_assets': {},
}
```

Apply the database migrations, update the search index and restart NetBox:

```shell
cd /opt/netbox/netbox
python3 manage.py migrate netbox_assets
python3 manage.py reindex --lazy
sudo systemctl restart netbox netbox-rq
```

## Settings

Override the defaults in `PLUGINS_CONFIG`:

```python
PLUGINS_CONFIG = {
    'netbox_assets': {
        'used_status_name': 'used',
        'stored_status_name': 'stored',
        'sync_hardware_serial_asset_tag': True,
    },
}
```

| Setting                              | Default         | Description |
| ------------------------------------ | --------------- | ----------- |
| `used_status_name`                   | `'used'`        | Status set when an asset is assigned to a device, module or rack. |
| `used_additional_status_names`       | `[]`            | Other statuses that also mean "in use". |
| `stored_status_name`                 | `'stored'`      | Status set when an asset is unassigned. |
| `stored_additional_status_names`     | `['retired']`   | Other statuses that also mean "not in use". |
| `sync_hardware_serial_asset_tag`     | `False`         | Keep serial number and asset tag of the assigned device, module or rack in sync with the asset. The device type, module type or rack type is updated as well. |
| `asset_import_create_device_type`    | `False`         | When importing assets, create a missing manufacturer and device type. |
| `asset_import_create_module_type`    | `False`         | When importing assets, create a missing manufacturer and module type. |
| `asset_import_create_rack_type`      | `False`         | When importing assets, create a missing manufacturer and rack type. |
| `asset_import_create_tenant`         | `False`         | When importing assets, create a missing tenant (for the tenant and owning tenant fields). |
| `asset_custom_fields_search_filters` | `{}`            | Custom fields and lookups to add to the asset search filters, for example `{'asset_mac': ['icontains', 'exact']}`. |

To disable automatic status changes, set both `used_status_name` and
`stored_status_name` to `None`.

### Asset statuses

The default statuses are `stored`, `used` and `retired`. You can add your own
with the NetBox
[`FIELD_CHOICES`](https://netboxlabs.com/docs/netbox/configuration/data-validation/#field_choices)
setting:

```python
FIELD_CHOICES = {
    'netbox_assets.Asset.status+': (
        ('repair', 'In repair', 'orange'),
    ),
}
```

If you add statuses, also review `used_additional_status_names` and
`stored_additional_status_names`.

## REST API and GraphQL

REST API endpoints:

| Endpoint                                | Description |
| --------------------------------------- | ----------- |
| `/api/plugins/assets/assets/`           | Assets |
| `/api/plugins/assets/asset-roles/`      | Asset roles |
| `/api/plugins/assets/assembly-ends/`    | Installed ends of cable assemblies |
| `/api/plugins/assets/dcim/devices/`     | NetBox devices with an extra `has_asset_assigned` filter |
| `/api/plugins/assets/dcim/modules/`     | NetBox modules with an extra `has_asset_assigned` filter |

Assets have the read-only fields `is_assembly` and `assembly_cable` (the
cable of a cable assembly) and the filter `is_assembly=true|false`. An end is created with the `asset` and `module`
IDs and the `label` of the end; if `label` is empty, the first free end that
matches the module type is used. The read-only field `side` shows the side of
the end.

GraphQL queries: `asset`, `asset_list`, `asset_role`, `asset_role_list`,
`assembly_end`, `assembly_end_list`. Assets have the fields `ends` and
`assembly_cable`.

To import ends (`/plugins/assets/assembly-ends/import/`), use the columns
`asset` (asset ID), `device` (device name), `module_bay` (module bay name), and
optionally `label` and `is_primary`. A module must be installed in the module
bay.

## Development

The tests use the NetBox test framework. They need a NetBox 4.7 installation
with PostgreSQL and Redis, and a database user that is allowed to create the
test database. Install the plugin into the NetBox virtual environment in
editable mode (`pip install -e .`) and run:

```shell
cd /opt/netbox/netbox
python3 manage.py test netbox_assets.tests --keepdb --parallel 4
```

NetBox compares the number of database queries of list views with
`netbox_assets/tests/query_counts.json`. If you change a list view or an API
serializer on purpose, update the file (this does not work with `--parallel`):

```shell
UPDATE_QUERY_COUNTS=1 python3 manage.py test netbox_assets.tests --keepdb
```

GitHub Actions run `ruff` and the test suite against NetBox 4.7.4 on every
push and pull request.

## Version history

See [CHANGELOG.md](CHANGELOG.md).

## Links

- Source code and documentation: <https://github.com/Maksym-Ototiuk/netbox-assets>
- Issues: <https://github.com/Maksym-Ototiuk/netbox-assets/issues>
- PyPI: <https://pypi.org/project/netbox-assets/>

## License

MIT License, see [LICENSE](LICENSE).

- Copyright (c) 2022 Arnes (original netbox-inventory code)
- Copyright (c) 2026 Maksym Ototiuk (changes in this fork)

You may use, copy, modify and distribute this software for any purpose. It is
provided "as is", without warranty of any kind, and the authors are not liable
for any damage caused by its use.
