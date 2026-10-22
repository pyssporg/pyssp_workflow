# `pyssp_vv`

Node-ready **verification-by-simulation** workflows for SSP models.

The library treats verification as a sequence of path-addressed work units
(*nodes*) that consume and produce artifacts:

```text
authoring ──> build ──> params ──> simulate ──> compare ──> evidence
```

Each step is a plain, importable function. `pyssp_vv.nodes` wraps the ones that
benefit from scheduling policy (retries, timeouts, parallelism) so they can be
composed into `sequence_extensions` flows without the domain layer depending on
a flow engine.

## Scope

`pyssp_vv` covers both halves of V&V. Verification is implemented; validation is
the direction of travel.

**Verification** answers whether a simulation implementation conforms to a
declared expectation: another engine's trajectory, a trusted reference, an
analytical solution, an invariant, a metamorphic relation. Agreement between
engines is recorded as *agreement*, never as *correctness*: shared bugs are
invisible to cross-engine comparison.

**Validation** answers whether a model is adequate for an intended use. The
mechanism is the same oracle protocol, but a validation claim needs an
intended-use statement, measured data with uncertainty, and a criterion fixed
before the comparison runs. Until a case carries all three, measurement
comparison returns a discrepancy record rather than a verdict. See
[future direction](docs/breakdown/00-intent/intent.md#future-direction-validation).

## Status

Pre-alpha (`0.0.1`). Only the contracts are implemented: assessment/evidence
schemas, verdict states, the oracle protocol, and one node. Everything else is a
named empty module whose contract is documented but not yet built.

## Install

```bash
pip install -e ".[dev]"          # core, standard library only
pip install -e ".[dev,flow]"     # node wrappers (Python 3.11+, sequence_extensions)
```

Extras: `build`, `simulate`, `flow`, `analysis`, `report`, `all`. The `build`
and `simulate` extras are empty placeholders until the pyssp submodules are
linked (see [submodules](docs/breakdown/05-operation/submodules.md)).

## Shape

```python
from pyssp_vv.spec.assessment import Assessment, Factor, OracleRef, Tolerance

case = Assessment(
    assessment_id="BouncingBall/baseline",
    model="BouncingBall",
    case="baseline",
    factor=Factor("engine", levels=("ssp4sim", "omsimulator")),
    held=("window", "step_size", "param_set"),
    oracles=(
        OracleRef(
            oracle_id="engine-agreement",
            kind="cross_engine",
            tolerance=Tolerance(atol=1e-3, rtol=1e-2, shift_samples=2),
        ),
    ),
)
```

The independent factor is declared explicitly; the held factors are the claim
that everything else is constant. If held factors differ between runs, the
verdict is `invalid`, not `fail`.

## Documentation

- [Intent](docs/breakdown/00-intent/intent.md)
- [Architecture and import rules](docs/breakdown/02-architecture/architecture.md)
- [Node catalog](docs/breakdown/02-architecture/node-catalog.md)
- [Assessment schema](docs/breakdown/03-implementation/schema/assessment.md)
- [Evidence schema](docs/breakdown/03-implementation/schema/evidence.md)
