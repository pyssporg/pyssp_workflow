<!-- GENERATED FILE — do not edit. Regenerate with pb-registers. -->

# Decision Stream

Flat, dated history of every committed design choice. Current state lives
in the layer leaves named by each record's `state:` field.

Records live in the cold-storage archive; extract one with `pb archive read <ID>`.

## By Layer

### Architecture

- **AD-001** — Node-First Composition · accepted · 2026-10-22 · `AD-001`
  Work units are plain functions; the optional node layer applies @node only at artifact boundaries.
- **AD-002** — Explicit Path Addressing · accepted · 2026-10-22 · `AD-002`
  Every public function takes explicit input paths and an output directory; no working-directory convention.
- **AD-003** — This Repository Owns the Development Tree · accepted · 2026-10-22 · `AD-003`
  pyssp_workflow is the development tree; the five capabilities are gitlinks under 3rd_party/.
- **AD-004** — Module Surfaces Follow Responsibilities · accepted · 2026-10-23 · `AD-004`
  One module per responsibility; study, binding, compare, and fixture name the records they own.
- **AD-005** — One bind Call Instead of a Binding Record Union · accepted · 2026-10-27 · `AD-005`
  Binding is one bind call with mode, mapping, and components axes; the Binding union is gone.

### Implementation

- **IMD-001** — Figures Are Derived Artifacts · accepted · 2026-10-22 · `IMD-001`
  Figure specification lives in pyssp_vv; this package renders figures and never hashes them into evidence.
