# ED-001: Judgment Under a Policy

**Status:** Proposed
**Layer:** evolution-decision

---

## Context

Two proposals were on the table:

1. Extract a standalone numerical comparison and plotting library for
   simulation data.
2. Keep comparison inside the verification library and improve how results are
   judged.

Option 1 was rejected. The numerical ground is already occupied:
`pyssp_simulate.compare` provides `ComparisonWindow`, `resample`,
`compare_pair`, and `PairReport` with `max_abs_error`, `mean_abs_error`,
`rmse`, and `passed`. numpy and scipy cover the series algebra; pandas and
xarray cover ragged and labelled data; matplotlib is the plotting tool. A new
library would be mostly plumbing, its moat would be thin, and it would become a
third place where the same metrics are implemented.

The gap is not numerical. It sits between a computed metric and a defensible
verdict: what was compared, on which grid, over how much of the data, against
which criterion, and why the answer is what it is.

## Decision

**Delegate numerics. Own judgment.**

- Metric computation stays with existing libraries behind a small adapter
  protocol. This library does not define a metric it can borrow.
- The library owns a declarative **Policy** and the **judgment** that applies
  it: preconditions, sufficiency, criterion evaluation, and reason codes.
- A policy is one noun with three consumers. Metrics, judgment, and figures all
  read the same object, so a plot cannot display a different criterion than the
  one that was judged.
- The judgment core consumes a metric table, not arrays. It therefore needs no
  numeric dependency and can be tested with fabricated tables — coverage 0.5
  against a minimum of 0.9 must yield `invalid` no matter how good the RMSE
  looks.

## The policy

A policy is versioned data, not code. It is the unit a reviewer approves.

| Field | Content |
| --- | --- |
| `policy_id`, `version` | stable identity; the bundle records the resolved policy by digest |
| `signals` | channel mapping and roles: which side is the candidate, which is the expectation |
| `alignment` | grid strategy, interpolation (linear / zero-order hold / none), extrapolation rule, shift search window, gap rule |
| `metrics` | metric families and, for normalised metrics, the denominator |
| `criterion` | acceptance kind and values |
| `sufficiency` | minimum coverage, maximum shift relative to the window, degenerate-signal threshold |
| `provenance` | which input digests must be present for the judgment to count |

Two design rules follow from it:

- **Every metric row carries its policy.** A number without its grid,
  interpolation, coverage, and denominator is not evidence.
- **A criterion is not a tolerance.** The tolerance says how much difference is
  acceptable; the uncertainty says how well agreement can be known. They are
  separate fields because conflating them is the most common V&V reporting
  error.

## Judgment

Four steps, in order. A later step does not run if an earlier one fails.

### 1. Preconditions — are the two sides comparable?

| Reason code | Condition |
| --- | --- |
| `input-missing` | a declared input or signal is absent |
| `signal-unmapped` | a channel exists on one side only |
| `unit-mismatch` | declared units differ and no conversion is permitted |
| `no-time-overlap` | the windows do not intersect |
| `non-monotonic-time` | time is not strictly increasing |
| `sampling-insufficient` | the expectation has fewer samples than the policy requires |

### 2. Sufficiency — could this test have failed?

This step is the part no metrics library provides.

| Reason code | Condition |
| --- | --- |
| `coverage-below-minimum` | the comparable fraction of samples is too small |
| `degenerate-signal` | the expectation's range is near zero, so an absolute band cannot discriminate |
| `shift-at-boundary` | the best shift sits at the search edge, so the true lag may be larger |
| `identical-inputs` | candidate and expectation are byte-identical, usually a wiring bug rather than a pass |
| `at-noise-floor` | the error is below the resolution of the stored format; "indistinguishable" is not "within tolerance" |

### 3. Criterion — the declared acceptance

The criterion is evaluated against the metric table. For symmetric
engine-to-engine comparison it is a band. For comparison against measured data
it is an equivalence margin, and the margin must be declared before the data is
seen; a margin chosen afterwards is not a criterion.

### 4. Disposition — recorded override

A waiver names the assessment, the oracle, the reason, the owner, and an
expiry. It converts a `fail` into `waived` for that case only. It never edits
the metrics.

## Verdict mapping

| Outcome | Verdict |
| --- | --- |
| Every step passes and the criterion holds | `pass` |
| Steps 1–2 pass and the criterion is exceeded | `fail` |
| Step 1 or 2 fails | `invalid` |
| The run could not produce metrics (engine missing, timeout, crash) | `blocked` |
| A disposition overrides a failure | `waived` |

Every verdict carries the reason codes that produced it. `invalid` is not a
softer `fail`: it says the comparison was not legal, and the correct response
is to fix the comparison, not the tolerance.

## Best practices incorporated

- **Equivalence testing, not null-hypothesis testing.** "The difference is
  within the margin" is an equivalence claim; the margin is fixed from intended
  use before the data is seen.
- **ASME V&V 20-2009** for model-versus-experiment judgment: comparison error
  `E = S − D`, judged against validation uncertainty `u_val`. Note the category
  error to avoid: V&V 20 does **not** apply to engine-to-engine comparison,
  which is solution verification judged against discretisation and iteration
  error, not experiment.
- **AIAA G-077-1998** and **NASA-STD-7009A** for the vocabulary of
  verification, validation, and credibility, so terms are not redefined here.
- **JCGM 100:2008 (GUM)** for keeping uncertainty and tolerance distinct and
  for stating how combined uncertainty is formed.
- **Test sensitivity.** A policy should be validated against known-bad
  perturbations: if a deliberately corrupted trajectory still passes, the
  policy is not a test. This is a property of the policy, not of the engine.
- **Metric provenance.** Coverage and normalisation denominator are printed
  beside every metric, because a good number over a small or normalised sample
  is the standard way a comparison misleads.

## Delegation

| Concern | Owner |
| --- | --- |
| Symmetric dense-grid metrics | `pyssp_simulate.compare` |
| Shift search, coverage, gaps, envelopes | adapter, only where upstream has no equivalent |
| Series algebra, ragged data | numpy, pandas, xarray |
| Units | pint (optional) |
| Figures | matplotlib, driven by the same policy (see DD-001) |
| Policy, judgment, reason codes, verdicts, evidence | this library |

## Consequences

- `pyssp_vv.compare` computes metrics and must not define a criterion or a
  verdict. Judgment belongs to `oracle`.
- No metric may be implemented here without first checking whether
  `pyssp_simulate.compare` already provides it. Duplication is the failure mode
  this decision exists to prevent.
- The judgment layer is testable without simulations, engines, or numeric
  libraries.
- Figures inherit the policy, so a plot and a gate can never disagree.

## Open decisions

1. **Policy containment.** Does an `Assessment` embed the policy, or reference
   `policy_id@version`? Referencing keeps a policy reviewable across many
   assessments; the bundle must then record the resolved policy by digest.
2. **Criterion kind.** A band is sufficient for engine-to-engine. Measurement
   comparison needs an equivalence margin. If both are supported, the policy
   must say which, and the reasons must name it.
3. **Coverage definition.** Sample fraction, time fraction, or both. A short
   high-rate gap and a long low-rate gap are not the same defect.
4. **Sufficiency verdict.** A failed sufficiency check currently maps to
   `invalid`. If reviewers need to distinguish "not comparable" from "not a
   real test", that requires a sixth verdict and a schema bump.

## Next steps

1. Policy schema v1, reviewed as data before any code.
2. `judge()` contract and the reason-code taxonomy.
3. Fabricated-table tests for every reason code and verdict transition.
4. Adapters: `numpy_dense` and `pyssp_simulate`.
5. Figure specification tied to the same policy (DD-001).

## Not in scope

Event-aware and shape metrics (a bouncing ball compared pointwise will fail at
the bounce even when both simulations are right), DTW, forecasting scores, and
interactive plotting. These are named so they are refused deliberately rather
than discovered halfway through.
