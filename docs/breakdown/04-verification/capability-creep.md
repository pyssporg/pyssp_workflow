---
id: TEST-002
type: test
title: Capability creep gate
summary: "CI and a layering test fail when measurement or judgment symbols appear in the workflow source."
date: 2026-10-27
status: current
---

# Capability creep gate

Two surfaces reject a capability implemented in this repository.

## CI step

- Step name: "No capability creep" in `.github/workflows/ci.yml`.
- It scans every `src/**/*.py` file.
- Forbidden strings: `passed(`, `def compare(`, `def judge(`.
- Any hit fails the job.
- Failure message: "capability leaked into the workflow layer", followed by the
  hit list.

## Test counterpart

- `tests/test_layering.py::test_no_capability_is_reimplemented_here`.
- Markers: `def compare(`, `def judge(`, `def passed(`, `passed(`.
- It reports `path contains marker` for every hit.

## Scope

- The gate reads source text only; it does not run behavior.
- Measurement and judgment stay in `pyssp_vv` (`CP-002`).
- The layering test file as a whole: `TEST-001`.

## Owns

- The rejection rule against capability code entering `src/`.

## Excludes

- Measurement and judgment implementations: `pyssp_vv`.
- Module import rules: `INFO-002`.
