# DD-001: Figures Are Derived Artifacts

**Status:** Accepted
**Layer:** implementation-decision

---

## Context

Plotting was briefly treated as a reporting adapter to be added after the
pipeline worked. That inverts the development loop: during development the figure
is the instrument used to decide whether a model bug, an engine difference, or an
inappropriate tolerance is being observed.

At the same time a figure cannot be evidence. Matplotlib output is not stable
across versions, fonts, and backends, and a picture is not a measurable claim.

## Decision

- The **figure specification** — overlay, residual panel, criterion band, gap
  shading, shift indicator — is defined in `pyssp_vv.measure.figures`, next to
  the measurements and the policy it displays.
- This package owns the **rendering workflow**: choosing signals for a view,
  owning the output directory, writing the plot manifest.
- Figures are never hashed into evidence. The plot manifest records input
  digests and the renderer version so a figure can be traced back.
- A comparison figure draws the criterion band on the same axes as the data.
- Plot signals are chosen independently of gate signals; neither inherits the
  other's list.

## Consequences

- The development path works before a bundle exists: figures can be rendered
  from a comparison, not only from evidence.
- Reproducibility claims apply to evidence, not to pixels.
- Matplotlib stays behind an extra of `pyssp_vv`, not a dependency of the
  workflow layer.
