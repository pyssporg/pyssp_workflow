# Tests

Run from the package root:

```bash
python -m pytest
```

The package sets `pythonpath = ["src", "tests"]`, so tests import the package
under test and the `support` / `fixture_guard` helpers directly.

## Layout

| Path | Contents |
|---|---|
| `tests/test_*.py` | the suite, one file per subject |
| `tests/support.py` | shared scenario builder and the file-to-level table |
| `tests/fixture_guard.py` | session-start/finish digest check over the test tree |
| `tests/conftest.py` | level markers and guard hooks |

## Fixture policy

- **This suite commits no data files.** `support.write_scenario` builds
  scenarios into `tmp_path` from the public facades (`pyssp_standard.SSV`,
  `pyssp_standard.SSM`, and `analysis.json`); model files and result CSVs are
  written by small `_write_*` helpers into the caller's `tmp_path` tree.
- **A test never writes into the checkout.** Every write target is derived
  from a `tmp_path` argument. `tests/test_fixture_policy.py` parses the test
  modules and fails on a literal-path write, on a write in a function with no
  `tmp_path` argument, and on any `tmp_path`-free write that is not listed
  there with a reason.
- If data is ever shared by two tests, it becomes `tests/fixtures/<case>/`
  with `input.<ext>` and a `case.md` (see the sibling `pyssp_simulate` suite
  for the case-record shape). Do not add loose data files.

## Guard

`tests/fixture_guard.py` digests the whole `tests/` tree at session start and
again at session finish (excluding `__pycache__` and `*.pyc`). If a test wrote
a `.ssd`, `.ssv`, `.json`, or any other file next to the tests instead of into
`tmp_path`, the session exits non-zero and lists the changed paths.

## Levels

Every test carries exactly one level marker. `tests/conftest.py` applies the
file default from `FILE_LEVELS` in `tests/support.py`; `tests/test_markers.py`
asserts the invariant. A test declares its own marker only to override the
file default.

| Level | Command |
|---|---|
| static | `python -m pytest -m level_static` |
| unit | `python -m pytest -m level_unit` |
| component | `python -m pytest -m level_component` |
| contract | `python -m pytest -m level_contract` |
| integration | `python -m pytest -m level_integration` |
| system | `python -m pytest -m level_system` |
| acceptance | `python -m pytest -m level_acceptance` |
| slow (opt-in) | `python -m pytest -m slow` |

## Adding a test file

Add the file to `FILE_LEVELS` in `tests/support.py` so its tests receive the
file's level; the marker test fails otherwise. Lint with `ruff check tests`.
