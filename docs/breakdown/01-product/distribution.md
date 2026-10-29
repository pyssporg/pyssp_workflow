---
id: CP-003
type: capability
title: Distribution
summary: "Package identity, dependency-free install, reserved extras, and the development install from 3rd_party gitlinks."
date: 2026-10-27
status: current
---

# Distribution

The package ships as `pyssp-workflow`, pre-alpha `0.1.0`.

## Package identity

- Name: `pyssp-workflow`.
- Version: `0.1.0`.
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

- `dependencies = []`: the wheel declares no runtime dependency.
- Measurement, judgment, and evidence come from `pyssp_vv`.
- Capabilities are linked under `3rd_party/` and installed from
  `requirements-dev.txt` during development, so `pip install -e .` stays
  offline.
- The names are reserved for the first PyPI release (see `AD-003`).

## Extras

- `flow`: `sequence-extensions-flow>=3`.
- `build`: empty.
- `simulate`: empty.
- `all`: `sequence-extensions-flow>=3`.
- `dev`: `pytest>=8`, `ruff>=0.6`.

## Status

- Pre-alpha `0.1.0`.
- Module surfaces, dependency rules, node contract, and catalog are
  established.
- `authoring`, `binding`, `compare`, `analysis`, `fixture` are implemented.
- The optional node layer wraps SysML derivation and evidence writing.

## Owns

- What a consumer can install and which extras exist today.

## Excludes

- Capability installation: `INFO-004`.
- Module surfaces: `INFO-005`.
