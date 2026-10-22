# Intent

## Purpose

`pyssp_vv` provides reusable, composable work units for verification of SSP
models by simulation. A verification claim is expressed as an *assessment*: one
independent factor, the factors held constant, and one or more oracles that
render a verdict. Running an assessment produces an *evidence bundle* that can
be archived, diffed, and reviewed.

The library is consumed in two ways:

- as plain functions, for scripts, notebooks, and tests;
- as nodes, for parallel and audited flows built with `sequence_extensions`.

## Commitments

- **Evidence is the deliverable.** A run that produces numbers but no bundle
  has not produced a verification result.
- **Comparisons are controlled or invalid.** A verdict is attributable to the
  declared factor, or it is reported as `invalid`. It is never silently reported
  as a failure.
- **Inputs are addressed by path and identified by digest.** Evidence names what
  it was computed from, and the environment that computed it.
- **The verifier is independent of the author.** Verification code cannot import
  the SysML authoring tool. One package must not be able to quietly accommodate
  the other.
- **Reproducible by construction.** Identical inputs and an identical output
  directory produce identical evidence.

## Non-goals

- **Not validation.** The library does not establish fitness for an intended
  use, does not represent stakeholder intent, and does not certify an engine as
  correct. Engine-to-engine agreement is recorded as agreement.
- **Not an engine and not an integrator.** Simulation semantics belong to the
  engines behind `pyssp_simulate`.
- **Not a model editor.** No auto-remediation: the library may never modify a
  model, parameter set, or tolerance to make a case pass.
- **Not a plotting product.** Plots are diagnostic output, not acceptance
  criteria.
- **Not a workflow engine.** Scheduling belongs to `sequence_extensions`; this
  library only declares nodes and inert plans.

## Open scope question

Measured-data comparison is in scope as a *verification against pre-registered
acceptance criteria*. Whether a measurement comparison should be able to return
`pass`/`fail` before such a criterion exists is deliberately unresolved; see
[architecture, open questions](../02-architecture/architecture.md#open-questions).
