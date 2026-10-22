# Node Catalog

The catalog is the public contract of the node layer: names, inputs, outputs,
and side effects. A node may be added freely; changing an existing node's name
or output path is a breaking change.

Every node obeys:

- explicit path inputs and path returns (absolute), never the working directory;
- exactly one owned output path per invocation;
- picklable arguments and return values;
- no engine object, dataframe, or figure crossing the boundary.

## Leaves

| Node | Group | Inputs | Outputs | Status |
| --- | --- | --- | --- | --- |
| `derive_ssp_from_sysml` | authoring | SysML model path, FMU paths, `out_dir` | SSP root path, provenance map path | later |
| `sync_ssd_to_sysml` | authoring | SSD path, `out_dir` | SysML path | later |
| `check_roundtrip` | authoring | SSD path, `out_dir` | loss report path | later |
| `build_model` | build | model dir, `out_dir` | SSP root path | later |
| `resolve_parameter_set` | params | SSP root, SSV path, overrides, `out_dir` | resolved parameter record path | later |
| `simulate` | execute | SSP root, resolved params, window, backend, `out_dir` | result CSV, run manifest | later |
| `compare_engines` | compare | two run manifests, `out_dir` | metrics CSV, comparison manifest | later |
| `compare_reference` | compare | run manifest, reference CSV, tolerance, `out_dir` | metrics CSV, comparison manifest | later |
| `compare_measurement` | compare | run manifest, measurement path, channel map, `out_dir` | discrepancy report | design blocked: intended-use contract (see open questions) |
| `evaluate_oracle` | oracle | candidate run dir, oracle ref, `out_dir` | verdict record path | later |
| `plot_runs` | report | run manifests, signal list, tolerance, `out_dir` | figure paths, plot manifest | later |
| `plot_bundle` | report | bundle path, `out_dir` | figure paths, plot manifest | later |
| `write_bundle` | evidence | `EvidenceBundle`, `out_dir` | `evidence.json` path | **implemented** |

## Composites

| Node | Fans out to | Returns |
| --- | --- | --- |
| `assess_case` | one `simulate` per factor level, then oracles, then `write_bundle` | bundle path |
| `campaign` | one `assess_case` per assessment | bundle paths, failed assessment ids |

Composites submit leaves and return a future; they do not block inside the node
body. Futures are passed as direct arguments when they form a dependency edge.

## Deliberately absent

- `fix_model`, `relax_tolerance`, `auto_accept` — no node writes to an input
  path, so there is nothing for these to do; a failing oracle yields a failing
  or invalid verdict.
