---
id: CP-003
type: capability
title: Distribution
summary: "Package identity, dependency-free install, reserved extras, and the development install from 3rd_party gitlinks."
date: 2026-10-27
status: current
---

# Distribution

The package ships as `pyssp-workflow`, pre-alpha `0.1.1`.

## Package identity

- Name: `pyssp-workflow`.
- Version: `0.1.1`.
- Description: "Composable build, run, compare, and verify workflows for SSP
  models."
- Requires Python `>=3.10`.
- License: MIT.
- Authors: pyssporg contributors.
- Keywords: ssp, fmi, simulation, workflow, verification.
- Classifier: Development Status 2 - Pre-Alpha.
- Classifier: Intended Audience Science/Research.
- Classifier: MIT License.
- Classifier: Python 3, 3.10, 3.11, 3.12.
- Classifier: Topic Scientific/Engineering.

## Install

```bash
git clone --recurse-submodules git@github.com:pyssporg/pyssp_workflow.git
cd pyssp_workflow
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e ".[dev]"
pip install -r requirements-flow.txt   # node layer, Python 3.11+
```

## Dependencies

- `dependencies`: the three capability siblings the wheel imports
  unconditionally, as PEP 508 direct references to their release assets:
  `experimental-pyssp-standard` `v0.9.2.dev0`, `pyssp-simulate` `v0.2.0`,
  `pyssp-vv[measure]` `v0.1.0`.
- `pyssp-sysml2` is a CLI dependency, never an import: it is pinned to
  `v0.4.0` in the `build` and `all` extras.
- Sibling tags must exist before this package is released; an unreleased tag
  makes the wheel uninstallable (see the `pyproject.toml` dependency comment).
- During development the same capabilities are linked under `3rd_party/` and
  installed from `requirements-dev.txt`, so `pip install -e .` stays offline.
- The names are reserved for the first PyPI release (see `AD-003`).

## Extras

- `flow`: `sequence-extensions-flow` `v3.0.0` (direct reference).
- `build`: `pyssp-sysml2` `v0.4.0` (direct reference).
- `all`: `flow` plus `build`.
- `dev`: `pytest>=8`, `ruff>=0.6`.

## Release assets

Each `v<version>` release carries `pyssp_workflow-<version>-py3-none-any.whl`
and `pyssp_workflow-<version>.tar.gz`; the sdist excludes the `3rd_party/`
checkouts, which belong to their own repositories.

## Status

- Pre-alpha `0.1.1`.
- Module surfaces, dependency rules, node contract, and catalog are
  established.
- `authoring`, `binding`, `compare`, `analysis`, `fixture` are implemented.
- The optional node layer wraps SysML derivation and evidence writing.

## Owns

- What a consumer can install and which extras exist today.

## Excludes

- Capability installation: `INFO-004`.
- Module surfaces: `INFO-005`.
