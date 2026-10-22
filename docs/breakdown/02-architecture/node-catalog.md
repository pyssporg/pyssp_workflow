# Node Catalog

The catalog is the public contract of the node layer: names, inputs, outputs,
side effects. Adding a node is free; renaming one or changing its output path is
a breaking change.

Every node obeys the rules in [ADR-002](decisions/ADR-002.md): explicit paths,
one owned output path, picklable values, no engine objects or figures crossing
the boundary.

## Leaves

| Node | Group | Inputs | Outputs | Delegates to | Status |
| --- | --- | --- | --- | --- | --- |
| `derive_ssp_from_sysml` | authoring | SysML path, FMU paths, `out_dir` | SSP root, provenance map | `pyssp` CLI | later |
| `sync_ssd_to_sysml` | authoring | SSD path, `out_dir` | SysML path | `pyssp` CLI | later |
| `check_roundtrip` | authoring | SSD path, `out_dir` | loss report | `pyssp` CLI | later |
| `build_model` | build | model dir, `out_dir` | SSP root | `pyssp_standard` | later |
| `resolve_parameter_set` | params | SSP root, SSV path, overrides, `out_dir` | resolved record | `pyssp_standard` | later |
| `simulate` | execute | SSP root, params, window, backend, `out_dir` | result CSV, run manifest | `pyssp_simulate` | later |
| `measure` | measure | two result CSVs, alignment policy, `out_dir` | metrics CSV + comparison JSON | `pyssp_vv.measure` | later |
| `judge` | judge | comparison JSON, policy, `out_dir` | judgment JSON | `pyssp_vv.judge` | later |
| `write_bundle` | evidence | `EvidenceBundle`, `out_dir` | `evidence.json` | `pyssp_vv.evidence` | **implemented** |
| `plot_runs` | report | comparison JSON, signal list, `out_dir` | figures + plot manifest | `pyssp_vv` figure spec | later |
| `plot_bundle` | report | bundle path, `out_dir` | figures + plot manifest | `pyssp_vv` figure spec | later |

## Composites

| Node | Fans out to | Returns |
| --- | --- | --- |
| `assess_case` | `simulate` per factor level, `measure`, `judge`, `write_bundle` | bundle path |
| `campaign` | `assess_case` per assessment | bundle paths, failed assessment ids |

Composites submit leaves and return a future; they do not block inside the node
body. Futures are passed as direct arguments when they form a dependency edge.

## Deliberately absent

- `compare` and `judge` as implementations. The nodes named above are thin
  wrappers; the logic is in `pyssp_vv`.
- `fix_model`, `relax_tolerance`, `auto_accept` — no node writes to an input
  path, so there is nothing for these to do.
