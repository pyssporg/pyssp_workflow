---
id: INFO-004
type: info
title: Install model
summary: Capabilities installed from release assets; cross-repo development in a flat ecosystem checkout.
date: 2026-10-23
status: current
---

# Install model

This package no longer vendors its compiled capabilities under `3rd_party/`.
They are declared as **base dependencies in `pyproject.toml`**, each a PEP 508
direct reference to that capability's release asset, and installed without any
submodules or local checkout.

| Distribution | Upstream | Used by |
| --- | --- | --- |
| `experimental-pyssp-standard` | `pyssporg/experimental_pyssp_standard` | `authoring`, `analysis`, `binding` |
| `pycps-sysml2` | `pyssporg/pycps_sysml2` | base dependency, not imported |
| `pyfmi-sysml2` | `pyssporg/pyfmi_sysml2` | base dependency, not imported |
| `pyssp-simulate` | `pyssporg/pyssp_simulate` | `compare` |
| `pyssp-sysml2` | `pyssporg/pyssp_sysml2` | `authoring` (CLI only) |
| `pyssp-vv` | `pyssporg/pyssp_vv` | `compare` (measure, evidence), `nodes` (judge, evidence) |
| `sequence-extensions-flow` | `pyssporg/sequence_extensions` | `nodes` |

The checkout is the experimental `pyssp_standard` fork
(`pyssporg/experimental_pyssp_standard`); the import package stays
`pyssp_standard`. Its release asset is built from its `alpha` branch.

## Development layout

```bash
git clone <this repository>
cd pyssp_workflow
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

The editable install brings the whole capability set from the release wheels.
`requirements-dev.txt` (a single `-e ".[dev]"` line) pulls the same set from
the dependencies declared in `pyproject.toml`, including `sequence_extensions`
(the node/flow engine, Python 3.11+) and the SysML tool plus the dialect and
FMI artifact libraries (`pycps_sysml2`, `pyfmi_sysml2`), CLI only.

For **cross-repo development** of several capability trees at once, do not add
vendored submodules here. Check all of the repositories out side by side (for
example in the `pyssp_dev` ecosystem workspace) and install each tree
editable. Bump a capability the normal way: release it, then update the
`@ <url>` direct reference in this `pyproject.toml` to the new asset.