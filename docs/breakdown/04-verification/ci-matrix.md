---
id: TEST-004
type: test
title: CI matrix
summary: "One ubuntu-latest job runs pytest on Python 3.11 and 3.12, with capabilities installed from their release assets."
date: 2026-10-27
status: current
---

# CI matrix

`.github/workflows/tests.yml` defines one workflow and one job.

## Trigger

- Workflow name: `tests`.
- Push to `main`.
- Every pull request.

## Job

- Job `test` runs on `ubuntu-latest`.
- `fail-fast: false`.
- Python matrix: `3.11`, `3.12`.

## Steps

- `actions/checkout@v4` (no submodules; capabilities come from release assets).
- `actions/setup-python@v5` with the matrix version.
- Install: upgrade pip, then `pip install "OMSimulator==3.0.0.post115" -e
  ".[dev]"` (pulls the capability release wheels as base dependencies; the
  OMSimulator pin keeps a published nightly and matches `pyssp_simulate`'s
  minimum).
- Lint: `ruff check src tests`.
- Tests: `python -m pytest -m "not slow"`.
- Capability gate: the "No capability creep" step (`TEST-002`).
- Clean-checkout step: `git diff --exit-code` plus an empty `git status`.

## Observed gaps

- `ruff>=0.6` is in the `dev` extra and runs as a CI step, so the local lint
  and the gate are the same command.
- No matrix entry excludes the node layer; `test_nodes_import.py` covers the
  optional node layer's import failure.

## Owns

- The CI job shape: runner, Python versions, checkout depth, install and test
  commands.

## Excludes

- Test contents: `TEST-001`, `TEST-003`.
- Install layout for developers: `INFO-004`.
