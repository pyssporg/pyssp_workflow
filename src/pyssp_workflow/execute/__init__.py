"""Package a study scenario into an exported SSP.

The study SSV and SSM are the standardized interchange artifacts. Packaging
copies them into the exported SSP and adds one root-level parameter binding, so
the build output is a self-contained, runnable SSP. The scenario SSV and SSM
are never rewritten.
"""

from __future__ import annotations

from pathlib import Path

from pyssp_standard import SSP


def package_scenario(
    exported_ssp_root: Path | str,
    scenario_ssv: Path | str,
    scenario_ssm: Path | str | None = None,
    *,
    target_ssd: str = "SystemStructure.ssd",
) -> Path:
    """Package the standard SSV/SSM into the exported SSP as one root binding.

    Returns the SSP root. The exported SSP is modified in place; callers that
    need a copy make one first.
    """
    root = Path(exported_ssp_root)
    ssv_path = Path(scenario_ssv)
    ssm_path = Path(scenario_ssm) if scenario_ssm is not None else None
    if not root.is_dir():
        raise NotADirectoryError(f"Exported SSP root is not a directory: {root}")
    if target_ssd != "SystemStructure.ssd":
        raise ValueError(
            "pyssp_standard.SSP.add_external_parameterset targets "
            f"SystemStructure.ssd, not '{target_ssd}'"
        )

    with SSP(root, mode="a") as ssp:
        with ssp.system_structure() as ssd:
            system = ssd.xml.system
            if system is None:
                raise ValueError(f"Runtime SSD has no system: {ssd.path}")
            if system.parameter_bindings:
                raise ValueError(
                    f"Exported SSP already has root parameter bindings: {ssd.path}"
                )

        ssp.add_external_parameterset(
            ssv_path,
            mapping_path=ssm_path,
            resource_name=ssv_path.name,
            mapping_resource_name=ssm_path.name if ssm_path is not None else None,
        )

    return root


__all__ = ["package_scenario"]
