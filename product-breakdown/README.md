# Product Breakdown

The durable record of what `pyssp_vv` is, why it is shaped this way, and what
each contract promises. Code is allowed to change; these documents are the
things a change must justify.

## Layers

| Folder | Holds |
| --- | --- |
| `00-intent/` | Purpose, commitments, non-goals |
| `02-architecture/` | System shape, import rules, node catalog, ADRs |
| `03-implementation/` | Interchange schemas and design decisions |
| `05-operation/` | How to run and maintain the library |

## Naming

- `ADR-<NNN>.md` — architecture decision, bare number, title inside the file
- `DD-<NNN>-<slug>.md` — implementation decision
- Schemas are named after the artifact they describe (`assessment`, `evidence`)

## Reading order

[intent](00-intent/intent.md) → [architecture](02-architecture/architecture.md)
→ [node catalog](02-architecture/node-catalog.md) →
[assessment](03-implementation/schema/assessment.md) /
[evidence](03-implementation/schema/evidence.md) schemas.
