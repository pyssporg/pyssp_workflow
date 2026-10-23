# AGENTS

## Vision first (required)

Before you read code, edit files, or plan a change, read the project vision:

**`docs/breakdown/00-intent/intent.md`**

It states why this repository exists, what it commits to, and what it refuses to
become. It is the first document to read, not a reference of last resort.

- Read it in full before making any change to code, tests, docs, or artifacts.
- Judge every proposed change against it. If a change conflicts with the vision,
  its commitments, goals, or non-goals, stop and surface the conflict; do not
  implement it silently.
- If the work shows the long-term direction is wrong, change the vision
  deliberately first, then the code. Never let the repository drift away from
  its stated intent.

## Rules

1. **Don't assume. Surface tradeoffs.** If a contract is ambiguous, stop and say
   so rather than picking a behaviour silently.
2. **Minimum code that solves the problem.** Nothing speculative.
3. **Touch only what you must.** Clean up only your own mess.
4. **Define success criteria and verify.**

## Repository Focus

`pyssp_workflow` makes the V&V capabilities usable as workflows. It composes
build, run, compare, verify, and validate steps into plain functions and
node-ready work units, and owns the decisions that only exist at that level:
what runs, in what order, where artifacts go, and what counts as one unit of
retry. It does not implement the capabilities it composes.

- Plain functions cover authoring, parameters, execution, planning, and
  reporting; `nodes` adds scheduling policy and `cli` exposes the command line.
- The capabilities live in the `3rd_party/` submodules; this package calls them.

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

## Code guidelines

- Keep functions plain and importable; scheduling belongs to `nodes`.
- Prefer small modules with clear responsibilities over growing a general
  orchestration layer.
- Avoid abstraction for its own sake; the composition layer should stay thin.

## Conventions

- `docs/breakdown/` holds intent, architecture, catalog, and decisions.
- Decision records use `ADR-<NNN>.md` architecture, `DD-<NNN>-<slug>.md`
  implementation, and `ED-<NNN>-<slug>.md` evolution; existing records live in
  `docs/breakdown/<layer>/decisions/`.

## Environment

- Python >= 3.10; the node layer needs Python 3.11+ (`requirements-flow.txt`).
- Development: create `.venv`, then `pip install -r requirements-dev.txt` and
  `pip install -e ".[dev]"`; add `requirements-flow.txt` for the node layer.
- Tests: `python -m pytest` (pyproject sets `pythonpath`); lint with
  `ruff check src tests`.
