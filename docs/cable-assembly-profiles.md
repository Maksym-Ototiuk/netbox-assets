# Cable assembly profiles

Ready-to-use Module Type Profiles for the most common cable assemblies. See
[Cable assemblies](../README.md#cable-assemblies-dac--aoc--breakout) in the
README for the concept and the rules.

| # | Profile                    | Topology                  | Ends              |
| - | -------------------------- | ------------------------- | ----------------- |
| 1 | `DAC SFP+ - SFP+`          | 10G direct attach copper  | SFP+ A, SFP+ B    |
| 2 | `DAC SFP28 - SFP28`        | 25G direct attach copper  | SFP28 A, SFP28 B  |
| 3 | `DAC QSFP28 - QSFP28`      | 100G direct attach copper | QSFP28 A, QSFP28 B |
| 4 | `AOC QSFP28 - QSFP28`      | 100G active optical cable | QSFP28 A, QSFP28 B |
| 5 | `Breakout QSFP+ - 4xSFP+`  | 40G to 4x10G              | QSFP+ A, SFP+ B1 to B4 |
| 6 | `Breakout QSFP28 - 4xSFP28` | 100G to 4x25G            | QSFP28 A, SFP28 B1 to B4 |

Each profile describes a **topology**, not a product. Create one profile per
topology and one module type (or one pair of module types, side A and side B)
per product, for example per length.

The profiles 1 to 4 are **symmetric**: both ends are the same, so each product
needs one module type with `side: both`. The breakout profiles 5 and 6 are
**asymmetric**: each product needs a side A module type (the QSFP end) and a
side B module type (the SFP ends).

## Contents

- [Import all profiles](#import-all-profiles)
- [How the examples are installed](#how-the-examples-are-installed)
- [1. DAC SFP+ - SFP+ (10G)](#1-dac-sfp---sfp-10g)
- [2. DAC SFP28 - SFP28 (25G)](#2-dac-sfp28---sfp28-25g)
- [3. DAC QSFP28 - QSFP28 (100G)](#3-dac-qsfp28---qsfp28-100g)
- [4. AOC QSFP28 - QSFP28 (100G)](#4-aoc-qsfp28---qsfp28-100g)
- [5. Breakout QSFP+ - 4xSFP+ (40G to 4x10G)](#5-breakout-qsfp---4xsfp-40g-to-4x10g)
- [6. Breakout QSFP28 - 4xSFP28 (100G to 4x25G)](#6-breakout-qsfp28---4xsfp28-100g-to-4x25g)
- [Writing your own profile](#writing-your-own-profile)

## Import all profiles

NetBox can import Module Type Profiles. Go to *Devices → Module Type Profiles*,
click *Import*, choose the *YAML* format and paste the block below. It creates
all six profiles. You can delete the ones you do not need from the block first.

```yaml
- name: DAC SFP+ - SFP+
  description: 10G direct attach copper cable, SFP+ on both ends
  schema:
    type: object
    x-end-names:
      A: [SFP+ A]
      B: [SFP+ B]
    properties:
      side: {type: string, title: Assembly side, enum: [both], default: both}
      a_ends: {type: integer, title: A-side ends, enum: [1], default: 1}
      b_ends: {type: integer, title: B-side ends, enum: [1], default: 1}
      media: {type: string, title: Media, enum: [DAC passive, DAC active]}
      length: {type: number, title: Length (m), minimum: 0}
    required: [side, media]
- name: DAC SFP28 - SFP28
  description: 25G direct attach copper cable, SFP28 on both ends
  schema:
    type: object
    x-end-names:
      A: [SFP28 A]
      B: [SFP28 B]
    properties:
      side: {type: string, title: Assembly side, enum: [both], default: both}
      a_ends: {type: integer, title: A-side ends, enum: [1], default: 1}
      b_ends: {type: integer, title: B-side ends, enum: [1], default: 1}
      media: {type: string, title: Media, enum: [DAC passive, DAC active]}
      length: {type: number, title: Length (m), minimum: 0}
    required: [side, media]
- name: DAC QSFP28 - QSFP28
  description: 100G direct attach copper cable, QSFP28 on both ends
  schema:
    type: object
    x-end-names:
      A: [QSFP28 A]
      B: [QSFP28 B]
    properties:
      side: {type: string, title: Assembly side, enum: [both], default: both}
      a_ends: {type: integer, title: A-side ends, enum: [1], default: 1}
      b_ends: {type: integer, title: B-side ends, enum: [1], default: 1}
      media: {type: string, title: Media, enum: [DAC passive, DAC active]}
      length: {type: number, title: Length (m), minimum: 0}
    required: [side, media]
- name: AOC QSFP28 - QSFP28
  description: 100G active optical cable, QSFP28 on both ends
  schema:
    type: object
    x-end-names:
      A: [QSFP28 A]
      B: [QSFP28 B]
    properties:
      side: {type: string, title: Assembly side, enum: [both], default: both}
      a_ends: {type: integer, title: A-side ends, enum: [1], default: 1}
      b_ends: {type: integer, title: B-side ends, enum: [1], default: 1}
      media: {type: string, title: Media, enum: [AOC], default: AOC}
      length: {type: number, title: Length (m), minimum: 0}
    required: [side, media]
- name: Breakout QSFP+ - 4xSFP+
  description: 40G QSFP+ to 4x 10G SFP+ breakout cable
  schema:
    type: object
    x-end-names:
      A: [QSFP+ A]
      B: [SFP+ B1, SFP+ B2, SFP+ B3, SFP+ B4]
    properties:
      side: {type: string, title: Assembly side, enum: [A, B]}
      a_ends: {type: integer, title: A-side ends, enum: [1], default: 1}
      b_ends: {type: integer, title: B-side ends, enum: [4], default: 4}
      media: {type: string, title: Media, enum: [DAC passive, DAC active, AOC]}
      length: {type: number, title: Length (m), minimum: 0}
    required: [side, media]
- name: Breakout QSFP28 - 4xSFP28
  description: 100G QSFP28 to 4x 25G SFP28 breakout cable
  schema:
    type: object
    x-end-names:
      A: [QSFP28 A]
      B: [SFP28 B1, SFP28 B2, SFP28 B3, SFP28 B4]
    properties:
      side: {type: string, title: Assembly side, enum: [A, B]}
      a_ends: {type: integer, title: A-side ends, enum: [1], default: 1}
      b_ends: {type: integer, title: B-side ends, enum: [4], default: 4}
      media: {type: string, title: Media, enum: [DAC passive, DAC active, AOC]}
      length: {type: number, title: Length (m), minimum: 0}
    required: [side, media]
```

The module types below can be imported the same way: *Devices → Module Types
→ Import*, format *YAML*. Each module type is a separate YAML document; the
documents are separated by `---`. Create the manufacturer (here `Generic`)
first, and replace the models and part numbers with your own products.

## How the examples are installed

The examples follow the NetBox practice for pluggable transceivers: every
port of a switch or server is a **module bay**, and each end of a cable
assembly is a **module** installed in that bay. The module creates the
interface of the port.

The interface templates of the example module types are named `{module}`.
NetBox replaces `{module}` with the **position** of the module bay. Give the
module bays of your device types the interface name as the position, for
example a module bay named `Ethernet1/1` with position `Ethernet1/1`. Then the
module installed in this bay creates the interface `Ethernet1/1`.

Installing a cable assembly always has the same steps:

1. Create the asset: *Assets → Assets → Add*, choose the module type (for a
   breakout cable, the **side A** module type), enter serial number and asset
   tag. The asset is `stored`.
2. On the asset page, in the *Assembly Ends* panel, click *Install* next to an
   end. Select the device and the module bay. If the bay is empty, the plugin
   creates the module (the module type is preselected). Repeat for the other
   ends. With the first installed end the asset becomes `used`.
3. Connect the interfaces of the ends with one NetBox cable: on the interface
   of one end click *Connect*, choose the interfaces of the other ends, the
   cable type (`DAC (Passive)`, `DAC (Active)` or `AOC`), the profile and the
   length.

To remove a cable, delete the NetBox cable and click *Uninstall* next to each
end. The modules stay in NetBox; delete them if the ports are empty now.

## 1. DAC SFP+ - SFP+ (10G)

- **Profile name:** `DAC SFP+ - SFP+`
- **Description:** 10G direct attach copper cable, SFP+ on both ends
- **Ends:** `SFP+ A`, `SFP+ B` (one module type with `side: both`)

```json
{
  "type": "object",
  "x-end-names": {"A": ["SFP+ A"], "B": ["SFP+ B"]},
  "properties": {
    "side":   {"type": "string",  "title": "Assembly side", "enum": ["both"], "default": "both"},
    "a_ends": {"type": "integer", "title": "A-side ends",   "enum": [1], "default": 1},
    "b_ends": {"type": "integer", "title": "B-side ends",   "enum": [1], "default": 1},
    "media":  {"type": "string",  "title": "Media", "enum": ["DAC passive", "DAC active"]},
    "length": {"type": "number",  "title": "Length (m)", "minimum": 0}
  },
  "required": ["side", "media"]
}
```

Module types (one per length):

```yaml
profile: DAC SFP+ - SFP+
manufacturer: Generic
model: DAC-SFP-10G-1M
part_number: DAC-SFP-10G-1M
description: 10G SFP+ passive DAC, 1 m
attribute_data:
  side: both
  a_ends: 1
  b_ends: 1
  media: DAC passive
  length: 1
interfaces:
  - name: "{module}"
    type: 10gbase-x-sfpp
---
profile: DAC SFP+ - SFP+
manufacturer: Generic
model: DAC-SFP-10G-3M
part_number: DAC-SFP-10G-3M
description: 10G SFP+ passive DAC, 3 m
attribute_data:
  side: both
  a_ends: 1
  b_ends: 1
  media: DAC passive
  length: 3
interfaces:
  - name: "{module}"
    type: 10gbase-x-sfpp
```

**Example:** a 1 m DAC between `leaf1` and `leaf2`.

1. Asset with module type `DAC-SFP-10G-1M`.
2. Install `SFP+ A` in `leaf1` / module bay `Ethernet1/1`, and `SFP+ B` in
   `leaf2` / module bay `Ethernet1/1`.
3. Cable from `leaf1 Ethernet1/1` to `leaf2 Ethernet1/1`, type
   `DAC (Passive)`, profile `1C1P`, length 1 m.

## 2. DAC SFP28 - SFP28 (25G)

- **Profile name:** `DAC SFP28 - SFP28`
- **Description:** 25G direct attach copper cable, SFP28 on both ends
- **Ends:** `SFP28 A`, `SFP28 B` (one module type with `side: both`)

```json
{
  "type": "object",
  "x-end-names": {"A": ["SFP28 A"], "B": ["SFP28 B"]},
  "properties": {
    "side":   {"type": "string",  "title": "Assembly side", "enum": ["both"], "default": "both"},
    "a_ends": {"type": "integer", "title": "A-side ends",   "enum": [1], "default": 1},
    "b_ends": {"type": "integer", "title": "B-side ends",   "enum": [1], "default": 1},
    "media":  {"type": "string",  "title": "Media", "enum": ["DAC passive", "DAC active"]},
    "length": {"type": "number",  "title": "Length (m)", "minimum": 0}
  },
  "required": ["side", "media"]
}
```

Module type:

```yaml
profile: DAC SFP28 - SFP28
manufacturer: Generic
model: DAC-SFP-25G-2M
part_number: DAC-SFP-25G-2M
description: 25G SFP28 passive DAC, 2 m
attribute_data:
  side: both
  a_ends: 1
  b_ends: 1
  media: DAC passive
  length: 2
interfaces:
  - name: "{module}"
    type: 25gbase-x-sfp28
```

**Example:** a server connected to a top-of-rack switch.

1. Asset with module type `DAC-SFP-25G-2M`.
2. Install `SFP28 A` in `tor1` / module bay `Ethernet1/10`, and `SFP28 B` in
   `server10` / module bay `ens1f0`.
3. Cable from `tor1 Ethernet1/10` to `server10 ens1f0`, type `DAC (Passive)`,
   profile `1C1P`, length 2 m.

## 3. DAC QSFP28 - QSFP28 (100G)

- **Profile name:** `DAC QSFP28 - QSFP28`
- **Description:** 100G direct attach copper cable, QSFP28 on both ends
- **Ends:** `QSFP28 A`, `QSFP28 B` (one module type with `side: both`)

```json
{
  "type": "object",
  "x-end-names": {"A": ["QSFP28 A"], "B": ["QSFP28 B"]},
  "properties": {
    "side":   {"type": "string",  "title": "Assembly side", "enum": ["both"], "default": "both"},
    "a_ends": {"type": "integer", "title": "A-side ends",   "enum": [1], "default": 1},
    "b_ends": {"type": "integer", "title": "B-side ends",   "enum": [1], "default": 1},
    "media":  {"type": "string",  "title": "Media", "enum": ["DAC passive", "DAC active"]},
    "length": {"type": "number",  "title": "Length (m)", "minimum": 0}
  },
  "required": ["side", "media"]
}
```

Module type:

```yaml
profile: DAC QSFP28 - QSFP28
manufacturer: Generic
model: DAC-QSFP-100G-1M
part_number: DAC-QSFP-100G-1M
description: 100G QSFP28 passive DAC, 1 m
attribute_data:
  side: both
  a_ends: 1
  b_ends: 1
  media: DAC passive
  length: 1
interfaces:
  - name: "{module}"
    type: 100gbase-x-qsfp28
```

**Example:** an MLAG peer link between `leaf1` and `leaf2`.

1. Asset with module type `DAC-QSFP-100G-1M`.
2. Install `QSFP28 A` in `leaf1` / module bay `Ethernet1/53`, and `QSFP28 B`
   in `leaf2` / module bay `Ethernet1/53`.
3. Cable from `leaf1 Ethernet1/53` to `leaf2 Ethernet1/53`, type
   `DAC (Passive)`, profile `1C1P`, length 1 m.

## 4. AOC QSFP28 - QSFP28 (100G)

- **Profile name:** `AOC QSFP28 - QSFP28`
- **Description:** 100G active optical cable, QSFP28 on both ends
- **Ends:** `QSFP28 A`, `QSFP28 B` (one module type with `side: both`)

```json
{
  "type": "object",
  "x-end-names": {"A": ["QSFP28 A"], "B": ["QSFP28 B"]},
  "properties": {
    "side":   {"type": "string",  "title": "Assembly side", "enum": ["both"], "default": "both"},
    "a_ends": {"type": "integer", "title": "A-side ends",   "enum": [1], "default": 1},
    "b_ends": {"type": "integer", "title": "B-side ends",   "enum": [1], "default": 1},
    "media":  {"type": "string",  "title": "Media", "enum": ["AOC"], "default": "AOC"},
    "length": {"type": "number",  "title": "Length (m)", "minimum": 0}
  },
  "required": ["side", "media"]
}
```

Module type:

```yaml
profile: AOC QSFP28 - QSFP28
manufacturer: Generic
model: AOC-QSFP-100G-10M
part_number: AOC-QSFP-100G-10M
description: 100G QSFP28 active optical cable, 10 m
attribute_data:
  side: both
  a_ends: 1
  b_ends: 1
  media: AOC
  length: 10
interfaces:
  - name: "{module}"
    type: 100gbase-x-qsfp28
```

**Example:** a spine to leaf uplink between two racks.

1. Asset with module type `AOC-QSFP-100G-10M`.
2. Install `QSFP28 A` in `spine1` / module bay `Ethernet1/1`, and `QSFP28 B`
   in `leaf1` / module bay `Ethernet1/49`.
3. Cable from `spine1 Ethernet1/1` to `leaf1 Ethernet1/49`, type `AOC`,
   profile `1C1P`, length 10 m.

## 5. Breakout QSFP+ - 4xSFP+ (40G to 4x10G)

- **Profile name:** `Breakout QSFP+ - 4xSFP+`
- **Description:** 40G QSFP+ to 4x 10G SFP+ breakout cable
- **Ends:** `QSFP+ A`, `SFP+ B1`, `SFP+ B2`, `SFP+ B3`, `SFP+ B4` (a side A
  and a side B module type)

```json
{
  "type": "object",
  "x-end-names": {
    "A": ["QSFP+ A"],
    "B": ["SFP+ B1", "SFP+ B2", "SFP+ B3", "SFP+ B4"]
  },
  "properties": {
    "side":   {"type": "string",  "title": "Assembly side", "enum": ["A", "B"]},
    "a_ends": {"type": "integer", "title": "A-side ends",   "enum": [1], "default": 1},
    "b_ends": {"type": "integer", "title": "B-side ends",   "enum": [4], "default": 4},
    "media":  {"type": "string",  "title": "Media", "enum": ["DAC passive", "DAC active", "AOC"]},
    "length": {"type": "number",  "title": "Length (m)", "minimum": 0}
  },
  "required": ["side", "media"]
}
```

Module types. The QSFP+ interface of the side A end is **channelized** into
four channels; each channel is a channel subinterface (`{module}:1` to
`{module}:4`) that NetBox traces to one SFP+ end:

```yaml
profile: Breakout QSFP+ - 4xSFP+
manufacturer: Generic
model: BRK-QSFP-4SFP-10G-3M-A
part_number: BRK-QSFP-4SFP-10G-3M
description: 40G QSFP+ to 4x 10G SFP+ passive breakout, 3 m, QSFP+ end
attribute_data:
  side: A
  a_ends: 1
  b_ends: 4
  media: DAC passive
  length: 3
interfaces:
  - name: "{module}"
    type: 40gbase-x-qsfpp
    channels: 4
  - name: "{module}:1"
    type: 10gbase-x-sfpp
    parent: "{module}"
    channel_id: 1
  - name: "{module}:2"
    type: 10gbase-x-sfpp
    parent: "{module}"
    channel_id: 2
  - name: "{module}:3"
    type: 10gbase-x-sfpp
    parent: "{module}"
    channel_id: 3
  - name: "{module}:4"
    type: 10gbase-x-sfpp
    parent: "{module}"
    channel_id: 4
---
profile: Breakout QSFP+ - 4xSFP+
manufacturer: Generic
model: BRK-QSFP-4SFP-10G-3M-B
part_number: BRK-QSFP-4SFP-10G-3M
description: 40G QSFP+ to 4x 10G SFP+ passive breakout, 3 m, SFP+ end
attribute_data:
  side: B
  a_ends: 1
  b_ends: 4
  media: DAC passive
  length: 3
interfaces:
  - name: "{module}"
    type: 10gbase-x-sfpp
```

**Example:** a 40G switch port split to four servers.

1. Asset with module type `BRK-QSFP-4SFP-10G-3M-A` (the side A type).
2. Install `QSFP+ A` in `sw1` / module bay `Ethernet1/49`. Install
   `SFP+ B1` to `SFP+ B4` in `srv1` to `srv4` / module bay `eth0`; the module
   type `BRK-QSFP-4SFP-10G-3M-B` is preselected.
3. One cable: side A `sw1 Ethernet1/49`, side B `srv1 eth0`, `srv2 eth0`,
   `srv3 eth0`, `srv4 eth0` (in this order), type `DAC (Passive)`, profile
   `1C4P:4C1P breakout`, length 3 m. NetBox then traces
   `sw1 Ethernet1/49:1` to `srv1 eth0`, `Ethernet1/49:2` to `srv2 eth0` and
   so on.

## 6. Breakout QSFP28 - 4xSFP28 (100G to 4x25G)

- **Profile name:** `Breakout QSFP28 - 4xSFP28`
- **Description:** 100G QSFP28 to 4x 25G SFP28 breakout cable
- **Ends:** `QSFP28 A`, `SFP28 B1`, `SFP28 B2`, `SFP28 B3`, `SFP28 B4` (a side
  A and a side B module type)

```json
{
  "type": "object",
  "x-end-names": {
    "A": ["QSFP28 A"],
    "B": ["SFP28 B1", "SFP28 B2", "SFP28 B3", "SFP28 B4"]
  },
  "properties": {
    "side":   {"type": "string",  "title": "Assembly side", "enum": ["A", "B"]},
    "a_ends": {"type": "integer", "title": "A-side ends",   "enum": [1], "default": 1},
    "b_ends": {"type": "integer", "title": "B-side ends",   "enum": [4], "default": 4},
    "media":  {"type": "string",  "title": "Media", "enum": ["DAC passive", "DAC active", "AOC"]},
    "length": {"type": "number",  "title": "Length (m)", "minimum": 0}
  },
  "required": ["side", "media"]
}
```

Module types:

```yaml
profile: Breakout QSFP28 - 4xSFP28
manufacturer: Generic
model: BRK-QSFP-4SFP-25G-2M-A
part_number: BRK-QSFP-4SFP-25G-2M
description: 100G QSFP28 to 4x 25G SFP28 passive breakout, 2 m, QSFP28 end
attribute_data:
  side: A
  a_ends: 1
  b_ends: 4
  media: DAC passive
  length: 2
interfaces:
  - name: "{module}"
    type: 100gbase-x-qsfp28
    channels: 4
  - name: "{module}:1"
    type: 25gbase-x-sfp28
    parent: "{module}"
    channel_id: 1
  - name: "{module}:2"
    type: 25gbase-x-sfp28
    parent: "{module}"
    channel_id: 2
  - name: "{module}:3"
    type: 25gbase-x-sfp28
    parent: "{module}"
    channel_id: 3
  - name: "{module}:4"
    type: 25gbase-x-sfp28
    parent: "{module}"
    channel_id: 4
---
profile: Breakout QSFP28 - 4xSFP28
manufacturer: Generic
model: BRK-QSFP-4SFP-25G-2M-B
part_number: BRK-QSFP-4SFP-25G-2M
description: 100G QSFP28 to 4x 25G SFP28 passive breakout, 2 m, SFP28 end
attribute_data:
  side: B
  a_ends: 1
  b_ends: 4
  media: DAC passive
  length: 2
interfaces:
  - name: "{module}"
    type: 25gbase-x-sfp28
```

**Example:** a 100G leaf port split to four 25G servers.

1. Asset with module type `BRK-QSFP-4SFP-25G-2M-A` (the side A type).
2. Install `QSFP28 A` in `leaf1` / module bay `Ethernet1/50`. Install
   `SFP28 B1` to `SFP28 B4` in the servers `srv11` to `srv14` / module bay
   `ens1f0`.
3. One cable: side A `leaf1 Ethernet1/50`, side B the four `ens1f0`
   interfaces in the order B1 to B4, type `DAC (Passive)`, profile
   `1C4P:4C1P breakout`, length 2 m.

## Writing your own profile

A profile is a cable assembly profile if its schema has the properties
`side`, `a_ends` and `b_ends`. Keep these rules in mind:

- `a_ends` and `b_ends` must have **exactly one integer value** in `enum`,
  for example `{"type": "integer", "enum": [4], "default": 4}`. The plugin
  reads the number of ends from the profile, not from the module types. If
  you add `default`, it must be the same value. (NetBox 4.7.4 or later saves
  integer `enum` values from the module type form correctly.)
- `side` is set on each module type: `A`, `B` or `both`. Use `"enum": ["both"]`
  for symmetric profiles and `"enum": ["A", "B"]` for asymmetric ones.
- `x-end-names` is optional. It is an object with the keys `A` and `B`, each a
  list of end names; the lists must have `a_ends` and `b_ends` names. Names
  are unique and at most 32 characters long. Without `x-end-names` the ends
  are named `A` and `B`, or `A1`…`An` and `B1`…`Bn` when a side has more than
  one end. NetBox ignores this key, so it is not shown in the module type
  form.
- Add `"type": "object"` at the top of the schema. Otherwise NetBox accepts a
  module type without any attributes (for example created through the API),
  and the plugin cannot tell its side.
- Use only these keywords in properties: `type`, `title`, `description`,
  `default`, `enum`, `minLength`, `maxLength`, `pattern`, `format`,
  `minimum`, `maximum`, `multipleOf` and `items`. The module type form of
  NetBox fails with an error for any other keyword (for example `const` or
  `examples`).
- Other properties (`media`, `length`, …) are only informational.

The plugin rejects a cable assembly profile that breaks these rules when it is
saved. Once assets use a profile, its properties `side`, `a_ends` and
`b_ends` cannot be removed, and installed ends cannot disappear (you can add
ends, but not remove or rename installed ones).
