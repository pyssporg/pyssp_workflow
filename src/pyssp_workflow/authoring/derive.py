"""SysML derivation steps: SSD, SSP, and analysis descriptors."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from pyssp_workflow.authoring._process import find_executable, run

DEFAULT_TIMEOUT_SECONDS = 1800.0


def _selection_arguments(selections: Mapping[str, str] | None) -> list[str]:
    """Return deterministic ``--select`` pairs; empty when nothing is selected."""
    if not selections:
        return []
    arguments: list[str] = []
    for key in sorted(selections):
        arguments.extend(["--select", f"{key}={selections[key]}"])
    return arguments


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
    selections: Mapping[str, str] | None = None,
) -> Path:
    """Generate ``SystemStructure.ssd`` from a SysML architecture.

    ``selections`` resolves SysML variation points at build time only; pass the
    same selection that the analysis derivation receives so the SSD agrees with
    the SSV/SSM.
    """
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
    arguments.extend(_selection_arguments(selections))
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
    selections: Mapping[str, str] | None = None,
) -> Path:
    """Export one ``SspModel`` composition as an SSP archive.

    ``selections`` resolves SysML variation points at build time only; pass the
    same selection that the analysis derivation receives so the SSP agrees with
    the SSV/SSM.
    """
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
    arguments.extend(_selection_arguments(selections))
    _run_pyssp(pyssp, arguments, timeout)
    return output


def derive_analysis_from_sysml(
    architecture_path: Path | str,
    output_dir: Path | str,
    composition: str,
    *,
    model_name: str,
    pyssp: str | Path | None = None,
    target_ssd: str = "SystemStructure.ssd",
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    selections: Mapping[str, str] | None = None,
) -> Path:
    """Generate analysis SSV, SSM, and ``analysis.json``; never an SSP.

    Returns the descriptor path. The descriptor names the SSV and SSM; callers
    that need them read the same ``analysis.json`` contract as the simulator.
    ``selections`` resolves SysML variation points at build time only; pass the
    same selection that the model derivation receives so the SSV/SSM agree
    with the SSD.
    """
    output = Path(output_dir)
    arguments = [
        "generate",
        "analysis",
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
    arguments.extend(_selection_arguments(selections))
    _run_pyssp(pyssp, arguments, timeout)

    descriptor = output / "analysis.json"
    if not descriptor.is_file():
        raise RuntimeError(f"pyssp analysis generation did not write {descriptor}")
    return descriptor


__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "derive_ssd_from_sysml",
    "derive_ssp_from_sysml",
    "derive_analysis_from_sysml",
]
