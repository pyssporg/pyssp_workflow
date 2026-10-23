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

Dependencies point inwards. `pyssp_workflow` may import all of `pyssp_vv`;
`pyssp_vv` imports nothing from the ecosystem.

## Library boundary rule

A library border carries a standardized artifact first (SSP, SSD, SSV, SSM,
LS-REF, or result CSV). If no standard covers the need, only a documented
public API type may cross. Internal modules, private objects, and adapter-only
structures never cross. This package is a consumer: it imports producer public
surfaces and does not reach into producer internals.

## Layers and rules

| Layer | Purpose | May import | Must not |
| --- | --- | --- | --- |
| `nodes` | scheduling policy over domain functions | `sequence_extensions`, all of `pyssp_vv`, domain modules | implement measurement or judgment |
| `plan` | inert execution plans | stdlib, `pyssp_workflow` | `sequence_extensions`, `pyssp_vv.judge` |
| `authoring` | SysML/SSD and fixture builds via external CLI and `omc` | stdlib, subprocess, `pyssp_standard` | `pyssp_vv`, `pyssp_sysml2` |
| `build`, `params` | SSP assembly and parameter resolution | `pyssp_standard` adapter, `pyssp_vv.measure` if needed | `pyssp_vv.judge` |
| `packaging` | apply a study scenario to a built SSP | `pyssp_standard`, `authoring.FixtureBuild`, `params` | reimplement SSP assembly |
| `execute` | compose one result-CSV comparison | `pyssp_simulate`, `pyssp_vv.measure`, `pyssp_vv.evidence` | `pyssp_vv.judge` |
| `report` | figures from a measurement | `pyssp_vv.measure.figures`, renderer extra | define what a figure shows |
| `cli` | thin commands | all of the above | duplicate logic |

Enforced by `tests/test_layering.py`.

The two rules that matter most:

1. **`authoring` cannot import `pyssp_vv`.** The path that produces a model must
   not be able to reach the layer that evaluates it.
2. **Only `nodes` and `cli` may import `pyssp_vv.judge`.** Build, execute, and
   plan are execution-side; they do not decide acceptability.

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

1. Whether `plan` should be able to construct nodes without importing the node
   layer (currently it must not, so plans stay inert data).

The dependency layout is settled: capabilities are linked under `3rd_party/` and
installed from `requirements-dev.txt`. See [ADR-003](decisions/ADR-003.md).
