---
id: CP-003
type: capability
title: Distribution
summary: "Package identity, base dependencies, the dev extra, and installation of capabilities from their release assets."
date: 2026-10-27
status: current
---

# Distribution

The package ships as `pyssp-workflow`, pre-alpha `0.2.0`.

## Package identity

- Name: `pyssp-workflow`.
- Version: `0.2.0`.
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
git clone git@github.com:pyssporg/pyssp_workflow.git
cd pyssp_workflow
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e ".[dev]"
pip install -r requirements-flow.txt   # node layer, Python 3.11+
```

## Dependencies

- `dependencies`: the whole runtime set, as PEP 508 direct references to
  sibling release assets: `experimental-pyssp-standard` `v0.9.2.dev0`,
  `pyssp-simulate` `v0.2.0`, `pyssp-vv` `v0.1.0`,
  `sequence-extensions-flow` `v3.0.0`, `pyssp-sysml2` `v0.4.0`, and
  `pyfmi-sysml2` `v0.1.0`.
- `pyssp-sysml2` and `pyfmi-sysml2` are install-only, never imports;
  `pycps-sysml2` `v0.1.0` arrives transitively with one owner per pin.
- Sibling tags must exist before this package is released; an unreleased tag
  makes the wheel uninstallable (see the `pyproject.toml` dependency comment).
- During development the same capabilities are installed from their
  release assets via `requirements-dev.txt`, so no leading `-e`-offline clone of
  the dependency tree is needed.
- The names are reserved for the first PyPI release (see `AD-003`).

## Extras

Only `dev`: `pytest>=8`, `ruff>=0.6`. Every capability is a base dependency,
so no capability extra exists. The SysML siblings stay install-only: this
package never imports them (`AD-006`).

## Release assets

Each `v<version>` release carries `pyssp_workflow-<version>-py3-none-any.whl`
and `pyssp_workflow-<version>.tar.gz`; the sdist ships only this package's
sources, with the capability wheels pulled in as release-asset dependencies.

## Status

- Pre-alpha `0.2.0`.
- Module surfaces, dependency rules, node contract, and catalog are
  established.
- `authoring`, `binding`, `compare`, `analysis`, `fixture` are implemented.
- The optional node layer wraps SysML derivation and evidence writing.

## Owns

- What a consumer can install and which base dependencies and extras exist today.

## Excludes

- Capability installation: `INFO-004`.
- Module surfaces: `INFO-005`.
