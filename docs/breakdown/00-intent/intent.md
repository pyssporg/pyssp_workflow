---
id: INFO-001
type: info
title: Intent
summary: "Why pyssp_workflow exists: composition of build, run, compare, verify, and validate steps, and what it refuses to own."
date: 2026-10-26
status: current
---

# Intent

## Purpose

`pyssp_workflow` makes the V&V capabilities usable as workflows. It composes
build, run, compare, verify, and validate steps into plain functions and
node-ready work units, and it owns the decisions that only exist at that level:
what runs, in what order, where artifacts go, and what counts as one unit of
retry.

It does **not** contain the core of any of those capabilities.

## Scope

| Belongs here | Belongs elsewhere |
| --- | --- |
| node wrappers and scheduling policy | metrics and criteria (`pyssp_vv`) |
| study records, binding results, and comparison records as plain data | engine calls (`pyssp_simulate`) |
| artifact paths and ownership | SSP XML (`pyssp_standard`) |
| adapter calls to external CLIs | SysML conversion (`pyssp_sysml2`) |

## Commitments

- **Composition only.** If a function computes a metric, a criterion, or a
  verdict, it lives in `pyssp_vv`. If it parses an SSD, it lives in
  `pyssp_standard`.
- **Standard artifacts first at library borders.** Pass SSP/SSD/SSV/SSM/LS-REF
  or result CSV by path. If no standard covers the need, pass only a type that
  is explicitly part of the producer's public API; never pass internal modules,
  private objects, or adapter-only structures.
- **One node owns one output path**, derived from the assessment id, never from
  the working directory.
- **Engine execution happens in a child process.** A thread cannot be
  preempted, and a native engine abort would otherwise take the calling process
  down.
- **Retries only on deterministic, atomic nodes.**
- **The authoring path is independent of the judging path.** `authoring` cannot
  import `pyssp_vv`.
- **Nodes are optional.** The package installs without a flow engine; the
  `flow` extra adds it.
- **Public modules are explicit.** `authoring`, `binding`, `compare`, `study`,
  `fixture`, and the optional `nodes` layer are the public module surfaces. The
  package top-level import stays dependency-free so optional capabilities remain
  optional.

## Non-goals

- **Not a measurement library.** No resampling, metric families, coverage, or
  normalisation here.
- **Not a judgment library.** No criteria, sufficiency checks, verdicts, or
  dispositions here.
- **Not an engine.** No simulation semantics.
- **Not a scheduler.** `sequence_extensions` schedules; this package only
  declares the units of work.
