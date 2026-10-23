"""SysML derivation steps: SSD, SSP, and study descriptors."""

from __future__ import annotations

from pathlib import Path

from pyssp_workflow.authoring._process import find_executable, run

DEFAULT_TIMEOUT_SECONDS = 1800.0


def _run_pyssp(
    pyssp: str | Path | None,
    arguments: list[str],
    timeout: float,
) -> str:
    executable = find_executable(
        "pyssp",
        pyssp,
        hint="install pyssp_sysml2 or pass pyssp=",
        env_var="PYSSP",
    )
    return run([executable, *arguments], timeout=timeout)


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
    _run_pyssp(pyssp, arguments, timeout)
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
    _run_pyssp(pyssp, arguments, timeout)
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
    _run_pyssp(pyssp, arguments, timeout)

    descriptor = output / "study.json"
    if not descriptor.is_file():
        raise RuntimeError(f"pyssp study generation did not write {descriptor}")
    return descriptor


__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "derive_ssd_from_sysml",
    "derive_ssp_from_sysml",
    "derive_study_from_sysml",
]
