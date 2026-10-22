# AGENTS

## Rules

1. **Don't assume. Surface tradeoffs.** If a contract is ambiguous, stop and
   say so rather than picking a behaviour silently.
2. **Minimum code that solves the problem.** Nothing speculative. Empty
   modules with a contract docstring are preferred over guessed implementations.
3. **Touch only what you must.** Clean up only your own mess.
4. **Define success criteria and verify.** A change is done when the stated
   check passes, not when it looks right.

## Hard constraints

- **Core is standard-library only.** `pyssp_vv/spec`, `pyssp_vv/evidence`, and
  `pyssp_vv/plan` may import stdlib and `pyssp_vv` only.
- **No flow engine outside `pyssp_vv/nodes`.** `sequence_extensions` may be
  imported there and nowhere else.
- **Oracles never import authoring.** `pyssp_vv.oracle`, `pyssp_vv.compare`,
  and `pyssp_vv.evidence` must not import `pyssp_vv.authoring`. Verification
  must not be able to reach into the thing that produced the model.
- **Explicit paths.** Public functions take paths and return paths or plain
  data. No ambient working-directory lookups, no open handles, no context
  objects with live state.
- **No upstream types in public signatures.** `pyssp_standard`,
  `pyssp_simulate`, `pyssp_sysml2`, and `sequence_extensions` objects stay
  behind their adapter module.
- **No auto-remediation.** The library may not modify a model, parameter set,
  or tolerance to make a case pass.

`tests/test_layering.py` enforces the import rules. If it fails, fix the code,
not the test.

## Conventions

- `product-breakdown/` holds intent, architecture, schemas, and decisions.
- ADRs are `ADR-<NNN>.md`; design decisions are `DD-<NNN>-<slug>.md`.
- Documentation states the contract; the docstring states the local rule.
