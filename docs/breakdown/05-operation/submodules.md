# Submodules

All capabilities this package composes are linked under `3rd_party/`. Each
gitlink in the parent commit pins the revision the package was tested with.

| Path | Upstream | Used by |
| --- | --- | --- |
| `3rd_party/pyssp_standard` | `jkCXf9X4/pyssp_standard` | `build`, `params` |
| `3rd_party/pyssp_simulate` | `pyssporg/pyssp_simulate` | `execute` |
| `3rd_party/pyssp_sysml2` | `pyssporg/pyssp_sysml2` | `authoring` (CLI only) |
| `3rd_party/pyssp_vv` | `pyssporg/pyssp_vv` | `measure`, `judge`, `evidence` |
| `3rd_party/sequence_extensions` | `jkCXf9X4/sequence_extensions` | `nodes` |

`pyssp_standard` is pinned to a revision on its `architecture_review` branch,
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
- `requirements-sysml.txt` installs `pyssp_sysml2` into a CLI-only environment.

## Updating one

```bash
git -C 3rd_party/pyssp_vv fetch
git -C 3rd_party/pyssp_vv checkout <revision>
git add 3rd_party/pyssp_vv
```

Run the submodule's tests and this package's tests before recording the new
gitlink. Change a URL only with `git submodule set-url 3rd_party/<name> <url>`;
editing `.gitmodules` by hand risks breaking `git submodule sync`.
