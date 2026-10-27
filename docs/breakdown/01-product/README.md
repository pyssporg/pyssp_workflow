# Product

The promised deliverable: capabilities, module surfaces, owners, and the
installable package.

## Owns

- What a consumer can rely on: workflows, module surfaces, ownership boundary,
  distribution.

## Excludes

- Why the package exists: `INFO-001`.
- Module dependency rules: `INFO-002`.
- How the claims are checked: `TEST-001` to `TEST-004`.

## Contents

<!-- pb:index:start -->
<!-- GENERATED FILE — do not edit. Regenerate with pb-registers. -->
- **CP-001** [Capabilities](capabilities.md) — Workflow capabilities: authoring, binding, simulate, compare, and node scheduling over standard artifacts.
- **CP-002** [Capability ownership](capability-ownership.md) — The package composes capabilities and owns none: composition, paths, and order of work are its whole scope.
- **CP-003** [Distribution](distribution.md) — Package identity, dependency-free install, reserved extras, and the development install from 3rd_party gitlinks.
- **INFO-005** [Module surface](module-surface.md) — Public module surfaces, the bind signature and its four placements, and the plain records they return.
<!-- pb:index:end -->
