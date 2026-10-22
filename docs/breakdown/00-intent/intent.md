# Intent

## Purpose

`pyssp_vv` provides reusable, composable work units for the V&V of SSP models by
simulation. A claim is expressed as an *assessment*: one independent factor, the
factors held constant, and one or more oracles that render a verdict. Running an
assessment produces an *evidence bundle* that can be archived, diffed, and
reviewed.

The library is consumed in two ways:

- as plain functions, for scripts, notebooks, and tests;
- as nodes, for parallel and audited flows built with `sequence_extensions`.

## Two kinds of claim, one mechanism

| Claim | Question | Oracles |
| --- | --- | --- |
| Verification | Does the implementation behave as specified? | agreement, reference trajectory, analytic solution, invariant, metamorphic relation |
| Validation | Is the model adequate for an intended use? | measured data, judged against a criterion fixed in advance |

Verification is implemented. Validation is the direction of travel; see
[future direction](#future-direction-validation).

## Commitments

- **Evidence is the deliverable.** A run that produces numbers but no bundle has
  not produced a result.
- **Comparisons are controlled or invalid.** A verdict is attributable to the
  declared factor, or it is reported as `invalid`. It is never silently reported
  as a failure.
- **Claims are stated before evidence.** An oracle carries its acceptance
  criterion in the assessment. A threshold chosen after seeing the result is not
  a criterion.
- **Inputs are read-only and identified by digest.** Functions never write to an
  input path and never alter one to reach a verdict; evidence names inputs as
  they were found, and the environment that read them.
- **The verifier is independent of the author.** Verification code cannot import
  the SysML authoring tool. One package must not be able to quietly accommodate
  the other.
- **Reproducible by construction.** Identical inputs and an identical output
  directory produce identical evidence.

## Non-goals

- **Not an engine and not an integrator.** Simulation semantics belong to the
  engines behind `pyssp_simulate`.
- **Not a plotting product.** Plots are diagnostic output, not acceptance
  criteria.
- **Not a workflow engine.** Scheduling belongs to `sequence_extensions`; this
  library only declares nodes and inert plans.
- **Not a certifier.** A bundle supports a decision about a model; it does not
  make that decision on behalf of a programme.

## Future direction: validation

Validation needs three things verification does not:

1. **An intended-use statement.** What the model is for, and the operating
   envelope over which the claim is made.
2. **Measured data with uncertainty.** Channel mapping, units, sampling, gaps,
   and a stated validity range.
3. **A criterion fixed in advance.** What discrepancy is acceptable for that
   intended use, recorded before the comparison runs.

Until an assessment carries all three, a comparison against measurement returns
a discrepancy record rather than a verdict. The mechanism is deliberately the
same as verification: the difference is the provenance of the oracle and the
prior commitment to a criterion.

See [architecture, open questions](../02-architecture/architecture.md#open-questions).
