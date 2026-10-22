"""Merge one study scenario into a runtime copy of an exported SSP.

The study SSV and SSM are the standardized interchange artifacts. This module
copies the exported SSP, then uses ``pyssp_standard.SSP`` to add those same
artifacts and one root-level parameter binding. It never rewrites the scenario
SSV or SSM.
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from pyssp_standard import SSP


@contextmanager
def inject_scenario(
    exported_ssp_root: Path | str,
    scenario_ssv: Path | str,
    scenario_ssm: Path | str | None = None,
    *,
    target_ssd: str = "SystemStructure.ssd",
) -> Iterator[Path]:
    """Yield a runtime SSP copy with the standard SSV/SSM merged into it."""
    source = Path(exported_ssp_root)
    ssv_path = Path(scenario_ssv)
    ssm_path = Path(scenario_ssm) if scenario_ssm is not None else None
    if not source.is_dir():
        raise NotADirectoryError(f"Exported SSP root is not a directory: {source}")
    if target_ssd != "SystemStructure.ssd":
        raise ValueError(
            "pyssp_standard.SSP.add_external_parameterset targets "
            f"SystemStructure.ssd, not '{target_ssd}'"
        )

    with tempfile.TemporaryDirectory(prefix=f"pyssp_{ssv_path.stem}_") as temp_dir:
        root = Path(temp_dir) / "ssp"
        shutil.copytree(source, root)

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

        yield root
