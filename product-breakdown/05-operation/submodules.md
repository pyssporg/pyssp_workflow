# Submodules

The pyssp libraries are intended dependencies, but they are **declared and not
linked**. `.gitmodules` lists the sections so the dependency set is reviewable;
no gitlink exists, so a clone fetches nothing and `git submodule status` is
empty.

| Path | Upstream | Used by |
| --- | --- | --- |
| `3rd_party/pyssp_standard` | `pyssporg/pyssp_standard` | `build`, evidence digests of SSP XML |
| `3rd_party/pyssp_simulate` | `pyssporg/pyssp_simulate` | `execute` |
| `3rd_party/pyssp_sysml2` | `pyssporg/pyssp_sysml2` | `authoring` (via its CLI) |
| `3rd_party/sequence_extensions` | `jkCXf9X4/sequence_extensions` | `nodes` |

## Linking one

```bash
git submodule add -b main https://github.com/pyssporg/pyssp_simulate.git \
  3rd_party/pyssp_simulate
```

This reuses the existing `.gitmodules` section. Do not rewrite it.

## After linking

- Fill in the matching extra in `pyproject.toml` (`build`, `simulate`).
- Keep each upstream behind exactly one adapter module. No upstream type may
  appear in a public signature.
- Review the submodule's local diff before updating it, and run this library's
  tests plus the submodule's tests before recording the new gitlink.
- `authoring` keeps invoking `pyssp_sysml2` through the `pyssp` CLI, even when
  the submodule is present.
