# `pyssp_workflow`

Composable workflows for building, running, comparing, verifying, and validating
SSP models — as plain functions and as node-ready work units.

This package **composes capabilities and owns none of them**:

| Concern | Owner |
| --- | --- |
| SSP assembly | `pyssp_standard` |
| Simulation execution | `pyssp_simulate` |
| Measurement, judgment, evidence | `pyssp_vv` |
| SysML derivation | `pyssp_sysml2`, via its CLI |
| Scheduling, retries, timeouts | `sequence_extensions` |
| Composition, paths, order of work | **this package** |

The last row is the whole scope. If a function here computes a metric, a
criterion, or a verdict, it is in the wrong repository.

## Shape

```text
authoring ──> build ──> params ──> simulate ──> measure ──> judge ──> evidence
   (CLI)     (standard)            (simulate)   (pyssp_vv)  (pyssp_vv)
```

Each step is a plain, importable function. `pyssp_workflow.nodes` adds scheduling
policy — retries, timeouts, parallelism — without the domain layer depending on a
flow engine.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pip install -e "../pyssp_vv[measure]"   # sibling checkout; see requirements-dev.txt
pip install -e ".[dev,flow]"        # node wrappers (Python 3.11+)
```

## Status

Pre-alpha (`0.1.0`). The layer boundaries, node contract, and catalog are
established; the modules are named empty contracts except for one evidence node.

## Documentation

- [Intent](docs/breakdown/00-intent/intent.md)
- [Architecture and dependency rules](docs/breakdown/02-architecture/architecture.md)
- [Node catalog](docs/breakdown/02-architecture/node-catalog.md)
- [Submodules](docs/breakdown/05-operation/submodules.md)
