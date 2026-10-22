"""Scheduling wrappers for SysML authoring commands."""

from __future__ import annotations

from pathlib import Path

from sequence_extensions.flow import node

from pyssp_workflow.authoring import (
    derive_ssd_from_sysml,
    derive_ssp_from_sysml,
    derive_study_from_sysml,
)


@node(timeout=1800.0)
def derive_ssd(
    architecture_path: str,
    output_path: str,
    composition: str,
    *,
    pyssp: str | None = None,
) -> str:
    return str(
        derive_ssd_from_sysml(
            Path(architecture_path),
            Path(output_path),
            composition,
            pyssp=pyssp,
        )
    )


@node(timeout=1800.0)
def derive_ssp(
    architecture_path: str,
    output_path: str,
    composition: str,
    *,
    pyssp: str | None = None,
    fmu_root: str | None = None,
) -> str:
    return str(
        derive_ssp_from_sysml(
            Path(architecture_path),
            Path(output_path),
            composition,
            pyssp=pyssp,
            fmu_root=Path(fmu_root) if fmu_root is not None else None,
        )
    )


@node(timeout=1800.0)
def derive_study(
    architecture_path: str,
    output_dir: str,
    composition: str,
    *,
    model_name: str,
    pyssp: str | None = None,
) -> str:
    return str(
        derive_study_from_sysml(
            Path(architecture_path),
            Path(output_dir),
            composition,
            model_name=model_name,
            pyssp=pyssp,
        )
    )
