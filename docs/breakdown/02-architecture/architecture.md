---
id: INFO-002
type: info
title: Architecture
summary: Module boundaries, dependency rules, library border rule, and node contract for the composition layer.
date: 2026-10-26
status: current
---

# Architecture

## Position in the ecosystem

```text
                       pyssp_vv
                measure/        judge/
                       ^            ^
                       │            │
        pyssp_simulate ─────────────┤
         (run engines)              │
                                    │
                          pyssp_workflow   ← this package
                     (build/run/compare/verify flows)
                                    │
                       pyssp_standard · pyssp_sysml2 · sequence_extensions
```

Dependencies point inwards. `pyssp_workflow` imports the public surfaces of the
capabilities it composes; the capabilities import nothing from it. Only `nodes`
may import `pyssp_vv.judge`.

## Library boundary rule

A library border carries a standardized artifact first (SSP, SSD, SSV, SSM,
LS-REF, or result CSV). If no standard covers the need, only a documented
public API type may cross. Internal modules, private objects, and adapter-only
structures never cross. This package is a consumer: it imports producer public
surfaces and does not reach into producer internals.

## Modules and rules

| Module | Purpose | May import | Must not |
| --- | --- | --- | --- |
| `nodes` | scheduling policy over domain functions | `sequence_extensions`, every internal module, all of `pyssp_vv` | implement measurement or judgment |
| `authoring` | SysML derivation, study and fixture builds, Modelica FMU build | stdlib, subprocess, `pyssp_standard`, `fixture`, `study` | `pyssp_vv`, `pyssp_sysml2` |
| `binding` | `bind` writes one scenario binding, chosen by `mode`/`mapping`/`components`, into a built SSP and returns a `BindingResult` | `pyssp_standard`, `fixture` | `pyssp_vv`, `study`, reimplement SSP assembly |
| `compare` | compose one result-CSV comparison | `pyssp_simulate`, `pyssp_vv.measure`, `pyssp_vv.evidence` | `pyssp_vv.judge` |
| `fixture` | `BuiltFixture` record and artifact path helpers | `study` | perform a build or read a scenario |
| `study` | study descriptor and standardized scenario artifacts as plain data | `pyssp_standard` | `pyssp_vv`, rewrite an SSV or SSM |

Enforced by `tests/test_layering.py`.

The two rules that matter most:

1. **`authoring` cannot import `pyssp_vv`.** The path that produces a model must
   not be able to reach the layer that evaluates it.
2. **Only `nodes` may import `pyssp_vv.judge`.** Build, bind, and compare are
   execution-side; they do not decide acceptability.

## Node contract

Every node obeys:

- explicit path inputs, absolute path returns, never the working directory;
- exactly one owned output path per invocation;
- picklable arguments and return values;
- no engine object, dataframe, or figure crossing the boundary;
- atomic writes and deterministic behaviour if it declares retries.

Engine nodes shell out. A thread pool cannot contain a native engine abort, and
a timed-out thread is abandoned rather than stopped.

## Why this is a separate package from `pyssp_vv`

They have different reasons to change. `pyssp_vv` changes when measurement
practice or acceptance policy changes. `pyssp_workflow` changes when the order of
work, artifact layout, or scheduling changes. Merging them would give one
package two audiences and two release cadences.

## Open questions

None at present. The module surfaces were settled in `AD-004`.

The dependency layout is settled: capabilities are linked under `3rd_party/` and
installed from `requirements-dev.txt`. See `AD-003`.
