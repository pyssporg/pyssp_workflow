---
id: TEST-003
type: test
title: Module test coverage
summary: "Per-module pytest files exercise the public surfaces; no coverage tool or coverage threshold is configured."
date: 2026-10-27
status: current
---

# Module test coverage

`tests/` holds seven files and 57 test functions. Each public module has a
matching file.

## Files

- `test_authoring_build.py`: 13 tests. Fixture builds per analysis, artifact roots,
  explicit packaging, build report, legacy SSP builds, Modelica FMU build.
- `test_binding.py`: 17 tests. The four placements, `set_name`, component
  selection, rejected combinations, typed parameter preservation.
- `test_compare.py`: 6 tests. Metric table, record round-trip, legacy
  status/error ignored, missing out dir, missing signal, reference and result
  prefixes.
- `test_fixture.py`: 5 tests. Artifact root default and override, analysis and
  model directories, their distinctness.
- `test_layering.py`: 7 tests. Import graph and capability markers (`TEST-001`).
- `test_nodes_import.py`: 2 tests. The flow extra is required; `write_bundle`
  is exported.
- `test_analysis.py`: 7 tests. Descriptor reading, standard artifact decoding,
  scenario targets and rejected mappings.

## Configuration

- `pyproject.toml` sets `pythonpath = ["src"]`.
- `testpaths = ["tests"]`.
- `xfail_strict = true`.
- `addopts = "-q"`.
- CI runs `python -m pytest`.

## Gap

- No coverage tool is configured.
- No coverage threshold exists.
- Coverage of a module is asserted by its file, not measured.

## Owns

- Which test file covers which public module, and the pytest configuration.

## Excludes

- The import-graph assertions: `TEST-001`.
- The CI job that runs the suite: `TEST-004`.
