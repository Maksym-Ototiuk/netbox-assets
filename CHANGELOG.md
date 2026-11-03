# Changelog

All notable changes to netbox-assets. The versions follow
[semantic versioning](https://semver.org/).

## 1.2.0 (unreleased)

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
