# Changelog

All notable changes to netbox-assets. The versions follow
[semantic versioning](https://semver.org/).

## 1.2.3 (2026-11-24)

### Changed

- Tested with NetBox 4.7.6; no code changes.

## 1.2.2 (2026-11-16)

### Added

- New NetBox releases are tested automatically every day. A new patch
  release of a supported NetBox version is added to the Compatibility table
  and released with a new plugin version when all tests pass; a new minor or
  major version gets a pull request, a failure an issue.
- End-to-end tests that follow the cable assemblies guide in the NetBox web
  interface: they import its YAML blocks, create the module types and assets,
  install the ends and check the cables and their traces.
- The tests compare the cable type labels of the plugin with every tested
  NetBox version.

### Changed

- Tested with NetBox 4.7.5.
- A release is published to PyPI only after the lint and all tests pass, and
  the GitHub Release is published right away with its CHANGELOG section.

### Documentation

- The README describes the problems the plugin solves (hardware that is not
  installed, cable assemblies as one item) and how to keep suppliers,
  warranty and similar information in custom fields. Links and images in the
  README are absolute, so they work on PyPI.
- [Cable assemblies](https://github.com/Maksym-Ototiuk/netbox-assets/blob/main/docs/cable-assembly-profiles.md) is rewritten:
  step-by-step guides with screenshots (a 10G SFP+ DAC, and a 40G QSFP+ to
  4x 10G SFP+ breakout cable, from the profile to the traced cable), complete
  import blocks for the profiles and module types of 10G, 25G and 100G DAC,
  100G AOC and 40G and 100G breakout cables, and the reference moved from the
  README.

## 1.2.1 (2026-11-04)

### Added

- Explanations of the primary end of a cable assembly: tooltips in the
  *Assembly Ends* panel (*Primary* column, *Make primary* button), on the
  *Primary End* row of the asset page, on the page of an end and in the
  *Cable Assembly* panel of a module, and a help text in the Install form.
- A warning in the *Assembly Ends* panel and in the Install form when a
  breakout cable has no side B module type, with a link to the module type
  form, prefilled with the profile, the manufacturer and the attributes.
- Documentation of the module types of cable assemblies (one module type for
  a symmetric assembly, two with the same manufacturer for a breakout
  cable), the attributes in the module type form, the interface templates,
  and a troubleshooting section for the common errors.

### Changed

- The module type attribute `cable_type` of cable assemblies takes the label
  of a NetBox cable type (for example `Direct Attach Copper (Passive)`), so
  the module type form shows readable cable types. The plugin keeps its own
  table of the labels (from NetBox 4.7.4) and maps them to the NetBox cable
  types; the NetBox values (`dac-passive`) are accepted too. The example
  profiles use the labels.
- The label of a new cable of a cable assembly is `<name> [<serial>]`: the
  asset name (or the profile name if the asset has no name) and the serial
  number, instead of the asset tag. It is still set only when the cable is
  created.
- Side B ends must be modules of a side B module type with the same profile
  and the same manufacturer as the asset's module type (before: the same
  profile). The error for a wrong module type names the module type, its
  profile, side and manufacturer, and lists the matching module types.

### Removed

- The *Assembly Ends* menu item. The ends of a cable assembly are managed in
  the *Assembly Ends* panel of the asset page; the list of all ends and its
  import are still available at `/plugins/assets/assembly-ends/`.

### Fixed

- Installing an end in an empty module bay failed with a server error when
  the device already had an interface with the name of the new module's
  interface, or when the module bay had no position for `{module}`. The
  Install form now shows an error, as the NetBox module form does.

## 1.2.0 (not released, included in 1.2.1)

### Added

- Cable assemblies (DAC, AOC, breakout cables): an asset whose module type
  has a cable assembly profile is installed as several modules, its ends.
  The ends are defined by the Module Type Profile (properties `side`,
  `a_ends`, `b_ends` and the optional key `x-end-names`).
- New model `AssetModuleEnd` with list, detail, install, uninstall, import
  and bulk delete views, and an *Assembly Ends* menu item.
- *Assembly Ends* panel on the asset page (install, uninstall, make primary,
  interfaces and cables of each end) and a *Cable Assembly* panel on module
  pages.
- Status, primary end and serial / asset tag synchronization for cable
  assemblies.
- The NetBox cable of a cable assembly is created, updated and deleted
  automatically when ends are installed or uninstalled: type and length from
  the module type (`cable_type`, `length`), cable profile from the topology
  (`1C1P`, `1CNP:NC1P breakout`) or the profile key `x-cable-profile`. Only
  label, description, color, status, tenancy, ownership, comments, tags and
  custom fields of this cable can be changed by users.
- Protection of module types, Module Type Profiles and modules used by cable
  assemblies.
- REST API endpoint `/api/plugins/assets/assembly-ends/`, asset fields
  `is_assembly` and `assembly_cable`, filter `is_assembly`, GraphQL queries
  `assembly_end` and `assembly_end_list` and the asset fields `ends` and
  `assembly_cable`.
- [Cable assembly profiles](docs/cable-assembly-profiles.md): six
  ready-to-use profiles with module types and installation examples.

### Changed

- Minimum NetBox version is 4.7.4 (it saves integer `enum` values of Module
  Type Profile attributes correctly).
- The asset filters `is_assigned`, `installed_*`, `located_*` and the search
  include cable assemblies by their installed ends.

## 1.1.2 (2026-10-02)

### Fixed

- The active hardware type tab of the asset form when an asset is cloned.

## 1.1.1 (2026-10-01)

### Fixed

- Lint error in the tests. No functional changes.

## 1.1.0 (2026-10-01)

### Added

- The reassign form (*Edit Assignment* on a device, module or rack page) has
  a storage site and location for the old asset, prefilled with the current
  location of the hardware.

## 1.0.0 (2026-09-30)

### Changed

- Minimum NetBox version is 4.7.2. NetBox 4.7.0 is not supported
  ([netbox#23130](https://github.com/netbox-community/netbox/issues/23130)).

## 0.1.0 (2026-09-30)

- First release: a stripped-down fork of
  [netbox-inventory](https://github.com/ArnesSI/netbox-inventory) v2.7.0
  with assets and hierarchical asset roles only.
