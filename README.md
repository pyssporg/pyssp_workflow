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
authoring ──> binding ──> simulate ──> compare
 (builds)     (SSP params)  (external)   (pyssp_vv.measure)
```

A study descriptor names the scenario SSV and SSM and the experiment window.
`authoring` turns the SysML architecture into a study and an exported model SSP;
`build_fixture` returns one `BuiltFixture` per study, with the artifact paths
under `artifacts/studies/<model>/<study>` and
`artifacts/models/<model>/<study>/<build_name>`. `binding` writes the chosen
scenario binding into the built SSP, which is then run by `pyssp_simulate`.
`compare` measures one candidate result CSV against a reference and writes
`metrics.csv`; it produces no verdict.

Each step is a plain, importable function. `pyssp_workflow.nodes` adds scheduling
policy — retries, timeouts, parallelism — without the domain layer depending on a
flow engine.

## Modules

| Module | Surface |
| --- | --- |
| `authoring` | SysML derivation through the `pyssp` CLI, study/model/fixture builds, legacy checked-in SSP builds, Modelica FMU build, build reporting |
| `binding` | `bind`, which writes one scenario binding into a built SSP and returns a `BindingResult` |
| `compare` | `ResultRef`, `ComparisonRequest`, `ComparisonRecord`, and `compare_csvs` |
| `study` | `Experiment`, `StudyDescriptor`, `read_study_descriptor`, `Scenario`, `read_scenario`, `scenario_targets` |
| `fixture` | `BuiltFixture` and the `artifacts_root`, `study_dir`, and `model_dir` path helpers |
| `nodes` | optional scheduling wrappers: `derive_ssd`, `derive_ssp`, `derive_study`, `write_bundle` |

`compare` reads result CSVs by path and `study` reads the descriptor and scenario
artifacts by path; both return plain records. `binding` reads the scenario SSV
and SSM as read-only inputs. Measurement and judgment stay in `pyssp_vv`,
simulation in `pyssp_simulate`, and SSP assembly in `pyssp_standard`.

```text
bind(build, ssv, *, set_name=None, mode="external"|"inline", ssm=None,
     mapping="attach"|"flatten", components=None) -> BindingResult
```

`mode` places the parameter set externally or inline; `mapping` keeps the SSV
member names (`attach`) or resolves them to SSP target names through the
optional SSM (`flatten`). The four placements are external attached (SSV and,
when given, SSM copied as resources), external flattened (generated
target-keyed SSV), inline attached (root set plus attached mapping), and inline
flattened (root set, or per-component sets when `components` is given).
`BindingResult` reports the SSP, mode, mapping, parameter set, resources,
written components, and parameter count. Parameters keep their SSV type
(Boolean/Integer/Real/String); value reading and mapping resolution come from
`pyssp_standard` (`SSV.parameters_by_name`, `SSM.resolve`).

```python
from pyssp_workflow.binding import bind

result = bind(build, scenario_ssv, mode="inline", mapping="flatten", ssm=scenario_ssm)
```

## Install

```bash
git clone --recurse-submodules git@github.com:pyssporg/pyssp_workflow.git
cd pyssp_workflow
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e ".[dev]"
pip install -r requirements-flow.txt   # node layer, Python 3.11+
```

## Status

Pre-alpha (`0.1.0`). The module surfaces, dependency rules, node contract, and
catalog are established. `authoring`, `binding`, `compare`, `study`, and `fixture`
are implemented; the optional node layer wraps SysML derivation and evidence
writing.

## Documentation

- [Intent](docs/breakdown/00-intent/intent.md)
- [Architecture and dependency rules](docs/breakdown/02-architecture/architecture.md)
- [Node catalog](docs/breakdown/02-architecture/node-catalog.md)
- [Submodules](docs/breakdown/05-operation/submodules.md)
