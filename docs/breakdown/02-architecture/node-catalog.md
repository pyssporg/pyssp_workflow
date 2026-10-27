---
id: INFO-003
type: info
title: Node Catalog
summary: "Public contract of the node layer: the four exported nodes, their inputs, outputs, and output ownership."
date: 2026-10-23
status: current
---

# Node Catalog

The catalog is the public contract of the node layer: names, inputs, outputs,
side effects. Adding a node is free; renaming one or changing its output path
is a breaking change.

Every node obeys `AD-002`: explicit paths, one owned output path, picklable
values, no engine objects or figures crossing the boundary. The import rules
live in `INFO-002` and the composition rule in `AD-001`.

## Exported nodes

`pyssp_workflow.nodes.__all__` exports four nodes.

### Authoring group

All three run the `pyssp` CLI through `pyssp_workflow.authoring` and use
`DEFAULT_TIMEOUT_SECONDS`.

- **`derive_ssd`**
  - Inputs: `architecture_path`, `output_path`, `composition`, optional
    `pyssp`.
  - Output: absolute path to the derived SSD.
  - Delegates to `derive_ssd_from_sysml`.
- **`derive_ssp`**
  - Inputs: `architecture_path`, `output_path`, `composition`, optional
    `pyssp`, optional `fmu_root`.
  - Output: absolute path to the derived SSP.
  - Delegates to `derive_ssp_from_sysml`.
- **`derive_study`**
  - Inputs: `architecture_path`, `output_dir`, `composition`, required
    keyword `model_name`, optional `pyssp`.
  - Output: absolute path to the derived study.
  - Delegates to `derive_study_from_sysml`.

### Evidence group

- **`write_bundle`**
  - Inputs: `EvidenceBundle`, `out_dir`.
  - Output: absolute path to `<out_dir>/evidence.json`.
  - Owns exactly that one path and creates `out_dir` when missing.
  - Declares `retries=0` and `timeout=60.0`.
  - Delegates to `EvidenceBundle.write`.

## Contract

- Inputs are explicit paths or plain data; no engine object crosses.
- Each invocation owns exactly one output path.
- Arguments and return values are picklable, so a process pool can run them.
- Engine work runs in a child process.
- No node writes to an input path.

## Owns

- Node names, inputs, outputs, and side effects promised to flow authors.

## Excludes

- Node contract rules as design: `INFO-002`.
- Authoring commands and build helpers: `INFO-005`.
- Scheduling engine behaviour: `sequence_extensions`.
