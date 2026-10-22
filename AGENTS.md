# AGENTS

## Rules

1. **Don't assume. Surface tradeoffs.**
2. **Minimum code that solves the problem.** Nothing speculative.
3. **Touch only what you must.** Clean up only your own mess.
4. **Define success criteria and verify.**

## Hard constraints

- **This package owns composition, not capability.** No metric, criterion,
  verdict, SSP parsing, or engine call is implemented here. If it belongs to a
  capability, it belongs to the package that owns that capability.
- **No flow engine outside `pyssp_workflow.nodes`.** `sequence_extensions` may be
  imported there and nowhere else.
- **`authoring` must not import `pyssp_vv`.** The path that produces a model must
  not reach the judgment that evaluates it.
- **Only `nodes` and `cli` may import `pyssp_vv.judge`.** Build, execute, and
  plan are execution-side and must not decide acceptability.
- **Explicit paths.** Public functions take paths and return paths or plain
  data. No ambient working-directory lookups, no open handles.
- **No upstream types in public signatures** beyond the package that owns them.
- **Inputs are read-only.**

`tests/test_layering.py` enforces the import rules. Fix the code, not the test.

## Conventions

- `docs/breakdown/` holds intent, architecture, catalog, and decisions.
- `ADR-<NNN>.md` architecture, `DD-<NNN>-<slug>.md` implementation,
  `ED-<NNN>-<slug>.md` evolution.
