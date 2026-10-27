---
id: INFO-005
type: info
title: Module surface
summary: "Public module surfaces, the bind signature and its four placements, and the plain records they return."
date: 2026-10-27
status: current
---

# Module surface

The package exposes six module surfaces. Each returns plain records or paths.

## Modules

- **`authoring`**: SysML derivation through the `pyssp` CLI, study, model, and
  fixture builds, legacy checked-in SSP builds, Modelica FMU build, build
  reporting.
- **`binding`**: `bind`, which dispatches one scenario binding into a built SSP
  through `SSP.bind_parameters` and returns a `BindingResult`.
- **`compare`**: `ResultRef`, `ComparisonRequest`, `ComparisonRecord`,
  `compare_csvs`.
- **`study`**: `Experiment`, `StudyDescriptor`, `read_study_descriptor`,
  `Scenario`, `read_scenario`, `scenario_targets`.
- **`fixture`**: `BuiltFixture` and the `artifacts_root`, `study_dir`,
  `model_dir` path helpers.
- **`nodes`**: optional scheduling wrappers `derive_ssd`, `derive_ssp`,
  `derive_study`, `write_bundle`.

## Data at the borders

- `compare` reads result CSVs by path.
- `study` reads the descriptor and scenario artifacts by path.
- Both return plain records.
- `binding` reads the scenario SSV and SSM as read-only inputs.
- Measurement and judgment stay in `pyssp_vv`.
- Simulation stays in `pyssp_simulate`.
- SSP assembly stays in `pyssp_standard`.

## Bind signature

```text
bind(build, ssv, *, set_name=None, mode="external"|"inline", ssm=None,
     mapping="attach"|"flatten", components=None) -> BindingResult
```

- `mode` places the parameter set externally or inline.
- `mapping` keeps SSV member names (`attach`) or resolves them to SSP target
  names through the optional SSM (`flatten`).
- `bind` is a dispatcher: every placement delegates to `SSP.bind_parameters`.
  Resource names, tree walks, and SSV writing live in `pyssp_standard`; the
  workflow keeps the allowed combinations, the root-binding and target-SSD
  gates, and the per-component filtering.
- External attached copies SSV and, when given, SSM as resources.
- External flattened writes a generated target-keyed SSV.
- Inline attached writes a root set plus the attached mapping.
- Inline flattened writes a root set, or per-component sets when `components`
  is given.
- `BindingResult` reports the SSP, mode, mapping, parameter set, resources,
  written components, and parameter count.
- Parameters keep their SSV type: Boolean, Integer, Real, String.
- Value reading and mapping resolution come from `pyssp_standard`
  (`SSV.parameters_by_name`, `SSM.resolve`).

## Owns

- The public module boundaries, names, and value shapes promised to callers.

## Excludes

- Module dependency rules: `INFO-002`.
- Node names and output ownership: `INFO-003`.
- Promised capability flow: `CP-001`.
