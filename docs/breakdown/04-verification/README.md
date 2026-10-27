# Verification

How the promised surfaces and boundaries are checked.

## Owns

- Executable checks: layering rules, capability-creep gate, test coverage, CI
  matrix.

## Excludes

- The rules under test: `INFO-002`, `CP-002`.
- The node contract: `INFO-003`.
- Build and install steps: `INFO-004`.

## Contents

<!-- pb:index:start -->
<!-- GENERATED FILE — do not edit. Regenerate with pb-registers. -->
- **TEST-001** [Layering rules](layering-rules.md) — AST import-graph tests that keep the package a composition layer and confine judgment to the node layer.
- **TEST-002** [Capability creep gate](capability-creep.md) — CI and a layering test fail when measurement or judgment symbols appear in the workflow source.
- **TEST-003** [Module test coverage](module-coverage.md) — Per-module pytest files exercise the public surfaces; no coverage tool or coverage threshold is configured.
- **TEST-004** [CI matrix](ci-matrix.md) — One ubuntu-latest job runs pytest on Python 3.10, 3.11, and 3.12 with recursive submodules installed.
<!-- pb:index:end -->
