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
installed); it prints the differences and exits with 1 if there are any:

```bash
python netbox/manage.py shell --no-startup --no-imports --interface python < /path/to/netbox-assets/scripts/cable-type-labels.py
```

GitHub Actions run this check in `test.yml` for every tested NetBox version,
so a difference fails the tests (and the daily test of a new NetBox release).
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

## End-to-end tests and the cable assemblies guide

The tests in `e2e/` follow `docs/cable-assembly-profiles.md` in the NetBox web
interface (Playwright): they read the YAML blocks from the guide, and the
values they use (asset names, serial numbers, devices, cable summaries) are
those of the guide, checked with `guide.assert_documented()`. Change the guide
and the end-to-end tests together: a guide that no longer matches NetBox or
the plugin must fail the tests. How to run them: *Development* in `README.md`.

The screenshots of the guide (`docs/images/`) are not checked by the tests.

The end-to-end job of `test.yml` runs on a fixed runner image (`ubuntu-26.04`),
not `ubuntu-latest`: `playwright install --with-deps` supports only the Ubuntu
versions that the Playwright release knows (Playwright 1.55 failed on Ubuntu
26.04). Change the image and the Playwright version of `e2e/requirements.txt`
together.

## Supporting a new NetBox version

`supported-netbox-versions.json` lists the tested NetBox versions; the test
matrix is built from it, and the Compatibility table of `README.md` must list
the same versions (`python scripts/netbox-versions.py check`, run by
`lint.yml`).

New NetBox releases are checked automatically every day by
`.github/workflows/netbox-latest.yml`; the tests run only when the latest
release is not in the list yet. A new patch release of the newest supported
minor version (e.g. 4.7.5) is added and released to PyPI without a human when
all tests pass. A new minor or major version (e.g. 4.8.0 or 5.0.0) gets a pull
request instead, and a failure gets an issue. A manual run of the workflow is
a dry run by default. For a pull request, an issue or a manual update, do all
of the following:

1. Run `python scripts/netbox-versions.py add vX.Y.Z`: it adds the version to
   `supported-netbox-versions.json` and the README table, bumps the PATCH
   version and adds a CHANGELOG entry (changes under `## Unreleased` become
   part of that release).
2. Run the tests against that version: the unit tests, the cable type labels
   check (see above) and the end-to-end tests.
3. Read the NetBox release notes for changes to module types and module type
   profiles, modules and module bays, interfaces and channels, cables, cable
   profiles and cable paths (tracing), the import forms and `netbox.ui`.
4. Compare the screenshots of `docs/cable-assembly-profiles.md` with the
   NetBox web interface; take them again if it changed.
5. Update `min_version` / `max_version` in `netbox_assets/__init__.py` if
   needed; if code changes were necessary, describe them in `CHANGELOG.md` and
   bump MINOR or PATCH as appropriate instead of the PATCH bump of step 1.

Report every failing check to the user before changing code.

Automatic releases push to `main` with `GITHUB_TOKEN` and start
`publish.yaml` with `gh workflow run`, because a tag pushed with
`GITHUB_TOKEN` does not trigger workflows. `publish.yaml` publishes only after
the version check, the lint and all tests pass.
