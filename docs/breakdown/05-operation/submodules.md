---
id: INFO-004
type: info
title: Submodules
summary: Capability gitlinks under 3rd_party, development install layout, and the gitlink update procedure.
date: 2026-10-23
status: current
---

# Submodules

All capabilities this package composes are linked under `3rd_party/`. Each
gitlink in the parent commit pins the revision the package was tested with.

| Path | Upstream | Used by |
| --- | --- | --- |
| `3rd_party/experimental_pyssp_standard` | `pyssporg/experimental_pyssp_standard` | `authoring`, `analysis`, `binding` |
| `3rd_party/pycps_sysml2` | `pyssporg/pycps_sysml2` | install bundle, not imported |
| `3rd_party/pyfmi_sysml2` | `pyssporg/pyfmi_sysml2` | install bundle, not imported |
| `3rd_party/pyssp_simulate` | `pyssporg/pyssp_simulate` | `compare` |
| `3rd_party/pyssp_sysml2` | `pyssporg/pyssp_sysml2` | `authoring` (CLI only) |
| `3rd_party/pyssp_vv` | `pyssporg/pyssp_vv` | `compare` (measure, evidence), `nodes` (judge, evidence) |
| `3rd_party/sequence_extensions` | `jkCXf9X4/sequence_extensions` | `nodes` |

The checkout is the experimental `pyssp_standard` fork
(`pyssporg/experimental_pyssp_standard`, directory
`3rd_party/experimental_pyssp_standard`); the import package stays
`pyssp_standard`. It is pinned to a revision on its `alpha` branch,
not `main`, so its `.gitmodules` entry has no `branch` and the checkout stays
detached. Do not add `-b main` for it.

## Development layout

```bash
git clone --recurse-submodules <this repository>
cd pyssp_workflow
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt   # standard, simulate, vv[measure]
pip install -e ".[dev]"
```

The flow engine and the SysML tool have their own files:

- `requirements-flow.txt` adds `sequence_extensions` (Python 3.11+).
- `requirements-sysml.txt` installs the SysML tool plus the two bundle libraries (`pycps_sysml2`, `pyfmi_sysml2`), CLI only.

The `sysml` extra pins the same three from release wheels; the gitlinks here pin the matching revisions for development. This package never imports any of them (`AD-006`).

## Updating one

```bash
git -C 3rd_party/pyssp_vv fetch
git -C 3rd_party/pyssp_vv checkout <revision>
git add 3rd_party/pyssp_vv
```

Run the submodule's tests and this package's tests before recording the new
gitlink. Change a URL only with `git submodule set-url 3rd_party/<name> <url>`;
editing `.gitmodules` by hand risks breaking `git submodule sync`.
