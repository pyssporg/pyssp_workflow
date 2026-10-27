---
id: TEST-001
type: test
title: Layering rules
summary: "AST import-graph tests that keep the package a composition layer and confine judgment to the node layer."
date: 2026-10-27
status: current
---

# Layering rules

`tests/test_layering.py` parses every module under `src/pyssp_workflow` with
`ast` and checks the import graph. The rules it encodes are the contract in
`INFO-002`.

## Declared dependencies

- `fixture` may import `study`.
- `study` may import no internal layer.
- `authoring` may import `fixture`, `study`.
- `binding` may import `fixture`, `study`.
- `compare` may import no internal layer.
- `nodes` may import `fixture`, `study`, `authoring`, `binding`, `compare`.
- Only `nodes` may import `pyssp_vv.judge`.
- `authoring` must not import `pyssp_vv`.
- `compare` may import `pyssp_vv.measure` and `pyssp_vv.evidence` only.

## Tests

- `test_every_internal_layer_is_in_the_dependency_table`: every internal layer
  has a declared dependency set.
- `test_internal_modules_only_import_from_their_allowed_layers`: no module
  imports a layer outside its set.
- `test_flow_engine_is_confined_to_the_node_layer`: no module outside `nodes`
  imports `sequence_extensions`.
- `test_authoring_cannot_reach_the_judgment_layer`: no `authoring` module
  imports `pyssp_vv`.
- `test_judgment_is_only_reachable_from_the_node_layer`: `pyssp_vv.judge` is
  unreachable outside `nodes`.
- `test_compare_composes_measurement_without_reaching_judgment`: `compare`
  imports only the allowed V&V modules.
- `test_no_capability_is_reimplemented_here`: no `src` file contains the
  markers `def compare(`, `def judge(`, `def passed(`, `passed(`.

## Owns

- The executable form of the module dependency rules.

## Excludes

- The rules as readable state: `INFO-002`.
- The same capability-creep idea as a CI step: `TEST-002`.
