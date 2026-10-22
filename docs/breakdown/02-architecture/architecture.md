# Architecture

## Shape

```text
        spec/          assessments, verdicts, tolerances, dispositions   (stdlib)
        evidence/      bundles, digests, environment fingerprint         (stdlib)
        plan/          inert execution plans                             (stdlib)
           |
           v
        params/ build/ execute/ compare/ oracle/ report/                 (extras)
           |
           v
        nodes/                                                        (flow extra)
           |
           v
        sequence_extensions flows (not part of this package)
```

`authoring/` is a sibling branch, not a stage of the verification path. It is
invoked as a subprocess and exchanges only SysML and SSD artifacts.

## Layers and allowed imports

| Layer | May import | Must not import |
| --- | --- | --- |
| `spec`, `evidence`, `plan` | stdlib, `pyssp_vv` | anything third-party |
| `oracle`, `compare`, `execute` | stdlib, `pyssp_vv.spec`, `.evidence`, `.compare` | `authoring`, `nodes` |
| `params`, `build` | stdlib, `pyssp_vv`, adapter for `pyssp_standard` | `authoring`, `nodes` |
| `authoring` | stdlib, subprocess to `pyssp` CLI | `oracle`, `compare`, `evidence` |
| `nodes` | `sequence_extensions`, `pyssp_vv` domain functions | — |

These rules are enforced by `tests/test_layering.py`. They are the machine-
checkable form of two commitments: the core is installable everywhere, and the
verifier cannot reach into the author.

## Verbs and nouns

Nodes are verbs; evidence is the noun. A node schedules work and returns paths.
It does not return trajectories, engine handles, frames, or figures. This is
what keeps node arguments picklable (process pools), bundles small, and
plotting out of the core.

## Verdicts

| Verdict | Meaning |
| --- | --- |
| `pass` | The oracle's expectation was met within tolerance |
| `fail` | The expectation was not met |
| `invalid` | The comparison was not legal: held factors differ, inputs missing, artifacts not comparable |
| `blocked` | No evidence could be produced: engine unavailable, timeout, crash |
| `waived` | A known outcome accepted by a recorded disposition |

`invalid` is load-bearing. Without it, an uncontrolled comparison looks like an
engine defect, and the first response is to loosen a tolerance.

## Execution model

- One node owns exactly one output path, derived from the assessment id.
- Outputs are written to a temporary location and renamed into place.
- Engine execution happens in a child process. A Python thread cannot be
  preempted, so a timed-out node is abandoned, not stopped; and a native engine
  abort would otherwise take the calling process with it.
- Retries are permitted only for nodes that are deterministic and atomic.
- Each node returns the absolute paths it wrote; manifests store paths relative
  to themselves.

## Oracle independence

Every oracle declares its provenance:

| Provenance | Claim |
| --- | --- |
| `agreement` | Two implementations behave alike; says nothing about correctness |
| `reference` | Matches a trusted trajectory |
| `analytic` | Matches a closed-form expectation |
| `invariant` | A property holds (bounds, conservation, monotonicity) |
| `metamorphic` | A known transformation of the input produces the expected transformation of the output |
| `measurement` | Matches measured data within a pre-registered criterion |

An oracle may read the built artifact and its own reference data. It may not
read authoring intermediates, and it may not modify inputs.

The policy that carries these choices — alignment, metrics, criterion,
sufficiency limits — and the four judgment steps that apply it are specified in
[ED-001](../06-evolution/ED-001-judgment-under-policy.md).

## Validation path

Verification oracles compare a candidate against an expectation that shares its
form: another simulation, a formula, a property. Validation compares a model
against the world, which introduces channel mapping, unit conversion, irregular
sampling, gaps, and measurement uncertainty.

Two consequences:

- `compare_measurement` is asymmetric and configurable. It cannot reuse the
  engine-to-engine metric set unchanged, because one side is an estimate and the
  other is an observation with a validity range.
- A validation verdict requires an intended-use statement and a criterion fixed
  in advance. Without both, the result is a discrepancy record, not a verdict.

The oracle protocol itself does not change: `measurement` is a provenance and
the assessment already carries the tolerance. What is missing is the
intended-use field and the measured-data contract.

## Reporting and diagnosis

Plotting is how a failing verdict becomes an explanation, so `report` is a
first-class stage. It has two entry points because it is used at two different
moments:

| Use | Input | Output |
| --- | --- | --- |
| Development | run directory or bundle, chosen signals | in-memory series and tables; a figure only if asked |
| Report | bundle path, `out_dir` | figures plus a plot manifest |

Rules:

- **Data first.** The data layer returns series and tables without importing
  matplotlib. Rendering is a separate adapter behind the `report` extra, so the
  development path works in a notebook with no figure backend.
- **Draw the criterion.** A comparison figure shows the tolerance band or
  acceptance criterion on the same axes as the data. A plot that shows only two
  curves leaves the reader to guess what was judged.
- **Derived, not evidence.** Figures are regenerable and are never hashed into a
  bundle: matplotlib output is not byte-stable across versions, fonts, or
  backends. The plot manifest records input digests so a figure can be traced to
  the bundle it came from.
- **One node, one output directory.** A reporting node owns `<out_dir>/plots/`
  and writes its manifest there.

See [DD-001](../03-implementation/decisions/DD-001-derived-plots.md).

## Packaging

| Extra | Provides |
| --- | --- |
| — | `spec`, `evidence`, `plan`, oracle protocol |
| `build` | `pyssp_standard`-backed SSP assembly (placeholder until submodules are linked) |
| `simulate` | `pyssp_simulate`-backed execution (placeholder) |
| `flow` | `pyssp_vv.nodes` (Python 3.11+, `sequence-extensions-flow`) |
| `analysis` | trajectory comparison (numpy/pandas) |
| `report` | plotting adapter (matplotlib) |

## Open questions

1. **Intended-use record.** Validation requires an intended-use statement and an
   operating envelope. Is that a new `Assessment` field, or a separate document
   referenced by id? This decides whether the schema takes a major bump before
   `compare_measurement` exists.
2. **Measurement verdicts.** Given an intended-use record and a criterion fixed
   in advance, does `compare_measurement` return `pass`/`fail`, or always a
   discrepancy record plus the criterion's outcome? Decision needed before its
   signature is fixed.
3. **Verdict composition.** When an assessment declares several oracles, is the
   bundle-level outcome all-must-pass, a scored aggregate, or a per-oracle
   report with no aggregate? Field reserved; policy not decided.
4. **Disposition storage.** Per-project data file versus per-assessment file.
   Both are explicit paths; the choice affects how waivers are reviewed.
