# Submodules

Both packages are declared as submodules and **not linked** in this repository's
working tree until development on them stabilises. `.gitmodules` lists the
intended dependency set; no gitlink exists for the unlinked entries.

| Path | Upstream | Used by |
| --- | --- | --- |
| `3rd_party/pyssp_standard` | `pyssporg/pyssp_standard` | `build`, `params` |
| `3rd_party/pyssp_simulate` | `pyssporg/pyssp_simulate` | `execute` |
| `3rd_party/pyssp_sysml2` | `pyssporg/pyssp_sysml2` | `authoring` (CLI only) |
| `3rd_party/pyssp_vv` | `pyssporg/pyssp_vv` | `measure`, `judge`, `evidence` |
| `3rd_party/sequence_extensions` | `jkCXf9X4/sequence_extensions` | `nodes` |

## Development layout

`pyssp_workflow` and `pyssp_vv` are sibling checkouts. Install the capability
first:

```bash
pip install -r requirements-dev.txt   # -e ../pyssp_vv
pip install -e ".[dev]"
```

## Linking one

```bash
git submodule add -b main https://github.com/pyssporg/pyssp_vv.git \
  3rd_party/pyssp_vv
```

This reuses the existing `.gitmodules` section; do not rewrite it. Review the
submodule's local diff before updating it, and run both repositories' tests
before recording a new gitlink.
