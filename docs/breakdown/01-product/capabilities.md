---
id: CP-001
type: capability
title: Capabilities
summary: "Workflow capabilities: authoring, binding, simulate, compare, and node scheduling over standard artifacts."
date: 2026-10-27
status: current
---

# Capabilities

`pyssp_workflow` delivers composable workflows for building, running,
comparing, verifying, and validating SSP models. Each step is a plain,
importable function and a node-ready work unit.

## Flow

- `authoring` turns the SysML architecture into an analysis and an exported
  model SSP.
- `binding` writes the chosen scenario binding into the built SSP.
- `pyssp_simulate` then runs the built SSP.
- `compare` measures one candidate result CSV against a reference.
- `compare` writes `metrics.csv`; it produces no verdict.

```text
authoring ──> binding ──> simulate ──> compare
 (builds)     (SSP params)  (external)   (pyssp_vv.measure)
```

## Analysis and fixture inputs

- An analysis descriptor names the scenario SSV, the SSM, and the experiment
  window.
- `build_fixture` returns one `BuiltFixture` per analysis.
- Analysis artifacts live under `artifacts/analyses/<model>/<analysis>`.
- Model artifacts live under `artifacts/models/<model>/<analysis>/<build_name>`.

## Scheduling

- Each domain step is a plain, importable function.
- `pyssp_workflow.nodes` adds scheduling policy: retries, timeouts,
  parallelism.
- The domain layer does not depend on a flow engine.

## Owns

- The promised workflow surface: authoring, binding, compare, and the optional
  node layer.

## Excludes

- Measurement, judgment, and evidence: `CP-002`, owned by `pyssp_vv`.
- Module-level surfaces and signatures: `INFO-005`.
- Package installation and extras: `CP-003`.
