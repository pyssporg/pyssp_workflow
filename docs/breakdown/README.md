# Product Breakdown — pyssp_workflow

Current state of `pyssp_workflow`: what it is, what it promises, how it is
organized, and how those claims are checked.

## The Seven Layers

- `00-intent/` — why does the project exist, who is it for?
- `01-product/` — what is delivered, out of scope?
- `02-architecture/` — how are deliverables, evidence, and work organized?
- `03-implementation/` — with what concrete assets is it realized? (absent: no
  current-state asset leaves yet; implementation facts live in
  `02-architecture/` and `05-operation/`)
- `04-verification/` — how do we know it satisfies the requirements?
- `05-operation/` — how do authors run, maintain, release?
- `06-evolution/` — what controlled changes come next? (absent: no candidates
  are tracked here)
- the decision archive (`docs/archive/archive.zip`) — the flat, dated decision
  stream: history, never current state; read via `pb archive`, never browsed

## Boundary Rule

A document's home is the layer whose question it answers; information flows
downward only. Current state lives in the layer leaves, history in the decision
archive (`docs/archive/archive.zip`, read via `pb archive`), tracking in the
generated registers (`design-choice-log.md`, `traceability-map.md`) — this file
indexes current state only.
