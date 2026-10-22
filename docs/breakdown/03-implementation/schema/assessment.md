# Assessment Schema (`0.1.0`)

An assessment declares one controlled comparison. It is the only place where
tolerance, factor, and oracle choices are stated.

## Fields

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `schema_version` | string | no | defaults to the package schema version |
| `assessment_id` | string | yes | stable, human-readable; used to derive output paths |
| `model` | string | yes | model or system under verification |
| `case` | string | yes | named scenario within the model |
| `factor` | object | yes | exactly one independent variable |
| `held` | list of string | yes | factors claimed constant across all levels; unique |
| `oracles` | list of object | yes | at least one |

Unknown keys are rejected at every level.

## `factor`

| Field | Type | Rule |
| --- | --- | --- |
| `name` | string | must not appear in `held` |
| `levels` | list of string | at least one, no duplicates |

Two or more levels are required for a comparison. One level is a single
observation and cannot produce a comparative verdict.

## `oracles[]`

| Field | Type | Rule |
| --- | --- | --- |
| `oracle_id` | string | unique within the assessment |
| `kind` | string | `cross_engine`, `reference_csv`, `analytic`, `invariant`, `metamorphic`, `measurement` |
| `tolerance` | object | see below |
| `params` | object | oracle-specific, JSON-safe |

## `tolerance`

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `atol` | number | — | absolute allowance, non-negative |
| `rtol` | number | `0.0` | relative allowance, non-negative |
| `shift_samples` | integer | `0` | symmetric search window for scheduling skew |

`shift_samples` searches for a better alignment; it does not rewrite the
trajectory. Pointwise metrics are always reported at the original grid.

## Example

```json
{
  "schema_version": "0.1.0",
  "assessment_id": "BouncingBall/baseline",
  "model": "BouncingBall",
  "case": "baseline",
  "factor": { "name": "engine", "levels": ["ssp4sim", "omsimulator"] },
  "held": ["window", "step_size", "param_set"],
  "oracles": [
    {
      "oracle_id": "engine-agreement",
      "kind": "cross_engine",
      "tolerance": { "atol": 0.001, "rtol": 0.01, "shift_samples": 2 },
      "params": {}
    }
  ]
}
```

## Rules that are not obvious

- A `cross_engine` oracle measures *agreement*. A `pass` means two
  implementations behave alike, not that either is correct.
- A `measurement` oracle must carry a pre-registered acceptance criterion in
  `params` before it may return `pass` or `fail`. Until that policy is decided,
  it returns a discrepancy record (see architecture open questions).
- Tolerances are part of the claim. Changing one changes the evidence, so it is
  recorded in the bundle by provenance, not by convention.
