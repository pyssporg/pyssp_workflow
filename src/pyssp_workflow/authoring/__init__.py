"""Authoring: SysML derivation, fixture build steps, and Modelica FMU build.

This module owns the command and build composition only. It invokes
``pyssp_sysml2`` and ``omc`` as subprocesses and exchanges SysML, SSP, SSV,
SSM, and FMU artifacts with ``pyssp_standard``. It never imports
``pyssp_sysml2`` or ``pyssp_vv``.

The build steps reset their output directory and leave their inputs untouched:
``architecture_dir`` and the legacy ``source_dir`` are read-only.
"""

from pyssp_workflow.authoring.build import build_analysis, build_fixture, build_model
from pyssp_workflow.authoring.derive import (
    DEFAULT_TIMEOUT_SECONDS,
    derive_analysis_from_sysml,
    derive_ssd_from_sysml,
    derive_ssp_from_sysml,
)
from pyssp_workflow.authoring.fmu import build_fmu_from_modelica
from pyssp_workflow.authoring.legacy import build_legacy_fixture, build_legacy_model
from pyssp_workflow.authoring.report import report_builds

__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "build_fixture",
    "build_fmu_from_modelica",
    "build_legacy_fixture",
    "build_legacy_model",
    "build_model",
    "build_analysis",
    "derive_ssd_from_sysml",
    "derive_ssp_from_sysml",
    "derive_analysis_from_sysml",
    "report_builds",
]
