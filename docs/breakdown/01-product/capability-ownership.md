---
id: CP-002
type: capability
title: Capability ownership
summary: "The package composes capabilities and owns none: composition, paths, and order of work are its whole scope."
date: 2026-10-27
status: current
---

# Capability ownership

`pyssp_workflow` composes capabilities and owns none of them.

## Owners

- **SSP assembly**: `pyssp_standard`.
- **Simulation execution**: `pyssp_simulate`.
- **Measurement, judgment, evidence**: `pyssp_vv`.
- **SysML derivation**: `pyssp_sysml2`, via its CLI.
- **Scheduling, retries, timeouts**: `sequence_extensions`.
- **Composition, paths, order of work**: this package.

## Scope rule

- The composition row is the whole scope.
- A function here that computes a metric, a criterion, or a verdict belongs in
  another repository.
- Capability gitlinks and their update procedure: `INFO-004`.
- Import rules that keep capabilities out of this layer: `INFO-002`.

## Owns

- The ownership boundary between composition and the capabilities it calls.

## Excludes

- What each capability computes: its own repository.
- The module surfaces offered here: `INFO-005`.
