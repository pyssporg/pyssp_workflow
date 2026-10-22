# DD-001: Figures Are Derived Artifacts

**Status:** Accepted
**Layer:** design-decision

---

## Context

An earlier draft treated plotting as a reporting adapter that could be added
after the pipeline worked. That inverts the development loop: during development
the figure is not a report, it is the instrument used to decide whether a model
bug, an engine difference, or an inappropriate tolerance is being observed. A
library that only plots finished evidence is useless exactly when plotting
matters most.

At the same time, a figure cannot be evidence. Matplotlib output is not stable
across versions, font availability, and backend choice, and a picture is not a
measurable claim.

## Decision

Treat reporting as a first-class stage with two entry points.

1. **Data layer** — given run directories or a bundle and a signal selection,
   return series and tables. No matplotlib import. Usable in a notebook, a test,
   or a debugging session before any bundle exists.
2. **Render layer** — behind the `report` extra, turn the same view into figures
   plus a plot manifest.

Rules:

- A figure is derived: it can always be regenerated from its inputs.
- Figures are never hashed into an evidence bundle.
- The plot manifest records the input digests and the renderer version, so a
  figure can be traced back to the bundle it illustrates.
- A comparison figure draws the tolerance band or acceptance criterion on the
  same axes as the data.
- A reporting node owns exactly one output directory.

## Consequences

- The development path must work without a bundle, so the data layer takes run
  directories and manifests directly. This is the one place where the library
  reads partially produced artifacts on purpose.
- Reproducibility claims apply to evidence, not to pixels. Regenerating a figure
  is expected to produce a visually identical, not byte-identical, image.
- `report` is optional (`report` extra) but not peripheral: it is part of how a
  verdict is justified in review.
- Choosing signals for a plot is not the same as choosing signals for a gate.
  Compares and plots may select different sets, and neither inherits the other's
  list.
