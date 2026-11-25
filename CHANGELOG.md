# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-11-24

### Changed

- Replace the `pyfmi-sysml2` distribution with `pyfmi-interfaces` on the
  dependency surface; the SysML sibling ships as `pyssp-sysml` v0.7.0
  (2026-11-22).
- Require Python >= 3.11; Python 3.10 is no longer supported.
- Refresh sibling pins: `pyssp-simulate` v0.4.0, `pyssp-vv` v0.3.0,
  `sequence-extensions-flow` v3.2.0, `pyssp-sysml` v0.7.0, and
  `pyfmi-interfaces` v0.5.3; `experimental-pyssp-standard` stays at
  v0.9.4.dev0.

## [0.3.0] - 2026-11-09

### Added

- Multi-file Modelica sources in `build_fmu_from_modelica` (a `source_files`
  keyword for multi-file `package.mo` loads).

### Changed

- Pick up the package-scoped IR, the single-parse loader, the `FmuModel`
  marker and direct FMU export, and the `pyfmi_sysml2` C header extraction from
  the sibling packages.
- Fold the sysml and flow bundles into the base dependencies.
- Remove the vendored `3rd_party` submodules; capabilities now install from
  their release assets.
- Bump sibling pins: `experimental-pyssp-standard` v0.9.3.dev0,
  `pyssp-simulate` v0.3.0, `pyssp-vv` v0.2.0, `pyssp-sysml` v0.5.0, and
  `pyfmi-sysml2` v0.2.0.

