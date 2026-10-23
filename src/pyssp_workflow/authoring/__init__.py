"""SysML authoring through the external ``pyssp`` CLI.

This module owns the command boundary only. It invokes ``pyssp_sysml2`` as a
subprocess and exchanges SysML and generated artifacts. It never imports
``pyssp_sysml2`` or ``pyssp_vv``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_TIMEOUT_SECONDS = 1800.0


def _pyssp_executable(pyssp: str | Path | None) -> str:
    if pyssp is not None:
        return str(pyssp)
    configured = os.environ.get("PYSSP")
    if configured:
        return configured
    sibling = Path(sys.executable).with_name("pyssp")
    if sibling.is_file():
        return str(sibling)
    found = shutil.which("pyssp")
    if found is None:
        raise FileNotFoundError(
            "pyssp executable not found; install pyssp_sysml2 or pass pyssp="
        )
    return found


def _run(
    *,
    pyssp: str | Path | None,
    arguments: list[str],
    timeout: float,
) -> str:
    command = [_pyssp_executable(pyssp), *arguments]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"{' '.join(command)} failed with exit code {completed.returncode}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed.stdout


def derive_ssd_from_sysml(
    architecture_path: Path | str,
    output_path: Path | str,
    composition: str,
    *,
    pyssp: str | Path | None = None,
    parameter_set_prefix: str = "parameter_sets",
    type_check: bool = True,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> Path:
    """Generate ``SystemStructure.ssd`` from a SysML architecture."""
    output = Path(output_path)
    arguments = [
        "generate",
        "ssd",
        "--architecture",
        str(Path(architecture_path)),
        "--composition",
        composition,
        "--output",
        str(output),
        "--parameter-set-prefix",
        parameter_set_prefix,
    ]
    if not type_check:
        arguments.append("--skip_type_check")
    _run(pyssp=pyssp, arguments=arguments, timeout=timeout)
    return output


def derive_ssp_from_sysml(
    architecture_path: Path | str,
    output_path: Path | str,
    composition: str,
    *,
    pyssp: str | Path | None = None,
    fmu_root: Path | str | None = None,
    parameter_set_prefix: str = "resources/parameter_sets",
    validate_fmus: bool = True,
    allow_missing_fmus: bool = False,
    type_check: bool = True,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> Path:
    """Export one ``SspModel`` composition as an SSP archive."""
    output = Path(output_path)
    arguments = [
        "generate",
        "ssp",
        "--architecture",
        str(Path(architecture_path)),
        "--composition",
        composition,
        "--output",
        str(output),
        "--parameter-set-prefix",
        parameter_set_prefix,
    ]
    if fmu_root is not None:
        arguments.extend(["--fmu-root", str(Path(fmu_root))])
    if not validate_fmus:
        arguments.append("--skip-fmu-validation")
    if allow_missing_fmus:
        arguments.append("--allow-missing-fmus")
    if not type_check:
        arguments.append("--skip_type_check")
    _run(pyssp=pyssp, arguments=arguments, timeout=timeout)
    return output


def derive_study_from_sysml(
    architecture_path: Path | str,
    output_dir: Path | str,
    composition: str,
    *,
    model_name: str,
    pyssp: str | Path | None = None,
    target_ssd: str = "SystemStructure.ssd",
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> Path:
    """Generate study SSV, SSM, and ``study.json``; never an SSP.

    Returns the descriptor path. The descriptor names the SSV and SSM; callers
    that need them read the same ``study.json`` contract as the simulator.
    """
    output = Path(output_dir)
    arguments = [
        "generate",
        "study",
        "--architecture",
        str(Path(architecture_path)),
        "--composition",
        composition,
        "--output-dir",
        str(output),
        "--model",
        model_name,
        "--target-ssd",
        target_ssd,
    ]
    _run(pyssp=pyssp, arguments=arguments, timeout=timeout)

    descriptor = output / "study.json"
    if not descriptor.is_file():
        raise RuntimeError(f"pyssp study generation did not write {descriptor}")
    return descriptor
