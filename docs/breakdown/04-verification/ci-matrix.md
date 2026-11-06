---
id: TEST-004
type: test
title: CI matrix
summary: "One ubuntu-latest job runs pytest on Python 3.10, 3.11, and 3.12, with capabilities installed from their release assets."
date: 2026-10-27
status: current
---

# CI matrix

`.github/workflows/ci.yml` defines one workflow and one job.

## Trigger

- Workflow name: `ci`.
- Push to `main`.
- Every pull request.

## Job

- Job `test` runs on `ubuntu-latest`.
- `fail-fast: false`.
- Python matrix: `3.10`, `3.11`, `3.12`.

## Steps

- `actions/checkout@v4` (no submodules; capabilities come from release assets).
- `actions/setup-python@v5` with the matrix version.
- Install: upgrade pip, install `-e ".[dev]"` (pulls the capability release
  wheels as base dependencies).
- Tests: `python -m pytest`.
- Capability gate: the "No capability creep" step (`TEST-002`).

## Observed gaps

- `ruff>=0.6` is in the `dev` extra.
- No lint step runs in CI.
- No matrix entry excludes the node layer; `test_nodes_import.py` covers the
  optional node layer's import failure.

## Owns

- The CI job shape: runner, Python versions, checkout depth, install and test
  commands.

## Excludes

- Test contents: `TEST-001`, `TEST-003`.
- Install layout for developers: `INFO-004`.
