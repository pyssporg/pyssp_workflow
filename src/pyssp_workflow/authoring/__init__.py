"""Authoring: SysML derivation, fixture build steps, and Modelica FMU build.

This module owns the command and build composition only. It invokes
``pyssp_sysml2`` and ``omc`` as subprocesses and exchanges SysML, SSP, SSV,
SSM, and FMU artifacts with ``pyssp_standard``. It never imports
``pyssp_sysml2`` or ``pyssp_vv``.

The build steps reset their output directory and leave their inputs untouched:
``architecture_dir`` and the legacy ``source_dir`` are read-only.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from zipfile import ZipFile

from pyssp_standard import FMU, SSP, unpack_archive

from pyssp_workflow.execute import PackageStep, StudyBuild, package_scenario
from pyssp_workflow.params import read_study_descriptor

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


def _reset_dir(path: Path) -> None:
    """Remove ``path`` if it exists and recreate it empty."""
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _strip_model_exchange(model_root: Path) -> None:
    for description in sorted(model_root.rglob("modelDescription.xml")):
        with FMU(description.parent, mode="a") as fmu:
            with fmu.model_description as model_description:
                model_description.strip_model_exchange()


def build_study(
    architecture_dir: Path | str,
    study_dir: Path | str,
    composition: str,
    model_name: str,
    *,
    pyssp: str | Path | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> Path:
    """Reset ``study_dir`` and generate its SSV, SSM, and ``study.json``.

    ``architecture_dir`` is read-only. Returns ``study_dir``.
    """
    architecture = Path(architecture_dir)
    study = Path(study_dir)
    _reset_dir(study)
    derive_study_from_sysml(
        architecture,
        study,
        composition,
        model_name=model_name,
        pyssp=pyssp,
        timeout=timeout,
    )
    return study


def build_model(
    architecture_dir: Path | str,
    model_dir: Path | str,
    composition: str,
    *,
    fmu_root: Path | str | None = None,
    validate_fmus: bool = True,
    pyssp: str | Path | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> Path:
    """Export the model SSP into ``model_dir`` and unpack its FMUs.

    ``model_dir`` is an output and is reset; ``architecture_dir`` and
    ``fmu_root`` are read-only. Model-exchange metadata is stripped from every
    unpacked FMU. Returns ``model_dir``.
    """
    architecture = Path(architecture_dir)
    model = Path(model_dir)
    fmu_base = Path(fmu_root) if fmu_root is not None else None
    _reset_dir(model)
    with tempfile.TemporaryDirectory(prefix=f"{model.name}_") as temp_dir:
        archive = Path(temp_dir) / "model.ssp"
        derive_ssp_from_sysml(
            architecture,
            archive,
            composition,
            fmu_root=fmu_base,
            validate_fmus=validate_fmus,
            pyssp=pyssp,
            timeout=timeout,
        )
        unpack_archive(
            archive,
            model,
            recursive_fmus=True,
            overwrite=True,
        )
    _strip_model_exchange(model)
    return model


def _strip_legacy_resources(
    resources_dir: Path, strip_resources: Sequence[str] | None
) -> None:
    """Strip model-exchange metadata from the legacy resource FMUs."""
    if strip_resources is None:
        candidates = sorted(
            path
            for path in resources_dir.iterdir()
            if (path / "modelDescription.xml").is_file()
        )
    else:
        candidates = []
        for name in strip_resources:
            path = resources_dir / name
            if not (path / "modelDescription.xml").is_file():
                raise FileNotFoundError(f"Missing FMU directory: {path}")
            candidates.append(path)
    for path in candidates:
        with FMU(path, mode="a") as fmu:
            with fmu.model_description as model_description:
                model_description.strip_model_exchange()


def build_legacy_model(
    source_dir: Path | str,
    model_dir: Path | str,
    *,
    flatten: bool = False,
    strip_resources: Sequence[str] | None = None,
) -> Path:
    """Copy a checked-in SSP body into ``model_dir`` and prepare it to run.

    ``source_dir`` is read-only; ``model_dir`` is an output and is reset. When
    ``strip_resources`` is given, only those resource FMUs lose their
    model-exchange metadata and a missing one raises ``FileNotFoundError``;
    ``None`` strips every resource FMU. ``flatten=True`` replaces the nested
    system hierarchy with one flat system. Returns ``model_dir``.
    """
    source = Path(source_dir)
    model = Path(model_dir)
    _reset_dir(model)
    shutil.copytree(source, model, dirs_exist_ok=True)
    _strip_legacy_resources(model / "resources", strip_resources)

    if flatten:
        with SSP(model, mode="a") as ssp:
            with ssp.system_structure() as ssd:
                ssd.flatten()

    return model


def _artifacts_root(repo_root: Path | str, artifacts_root: Path | str | None) -> Path:
    return (
        Path(artifacts_root)
        if artifacts_root is not None
        else Path(repo_root) / "artifacts"
    )


def build_fixture(
    *,
    model_dir: Path | str,
    repo_root: Path | str,
    model_name: str,
    composition: str,
    study: str,
    build_name: str = "model",
    artifacts_root: Path | str | None = None,
    package: PackageStep | None = None,
    validate_fmus: bool = True,
    pyssp: str | Path | None = None,
) -> Path:
    """Build one study, its exported model SSP, and the packaged runnable SSP.

    ``artifacts_root`` defaults to ``repo_root / "artifacts"``; it is never
    discovered from the working directory. The study artifacts land in
    ``<artifacts_root>/studies/<model>/<study>`` and the packaged SSP in
    ``<artifacts_root>/models/<model>/<study>/<build_name>``. ``model_dir`` is
    the fixture directory and is read-only.

    ``package=None`` uses ``execute.package_scenario``.
    """
    artifacts = _artifacts_root(repo_root, artifacts_root)
    architecture_dir = Path(model_dir) / "architecture"
    study_dir = artifacts / "studies" / model_name / study
    model_build_dir = artifacts / "models" / model_name / study / build_name

    build_study(
        architecture_dir,
        study_dir,
        study,
        model_name,
        pyssp=pyssp,
    )
    build_model(
        architecture_dir,
        model_build_dir,
        composition,
        fmu_root=repo_root,
        validate_fmus=validate_fmus,
        pyssp=pyssp,
    )

    descriptor = read_study_descriptor(study_dir / "study.json")
    if package is None:
        package_scenario(model_build_dir, descriptor.ssv_path, descriptor.ssm_path)
    else:
        package(model_build_dir, descriptor)

    return model_build_dir


def build_studies(
    *,
    model_dir: Path | str,
    repo_root: Path | str,
    model_name: str,
    composition: str,
    studies: Sequence[str | StudyBuild],
    build_name: str = "model",
    artifacts_root: Path | str | None = None,
    validate_fmus: bool = True,
    pyssp: str | Path | None = None,
) -> dict[str, Path]:
    """Build one runnable SSP per study, keyed by study name.

    Each study gets its own study artifacts and its own packaged model SSP.
    A plain string entry uses the default scenario packaging.
    """
    outputs: dict[str, Path] = {}
    for entry in studies:
        spec = entry if isinstance(entry, StudyBuild) else StudyBuild(entry)
        outputs[spec.name] = build_fixture(
            model_dir=model_dir,
            repo_root=repo_root,
            model_name=model_name,
            composition=composition,
            study=spec.name,
            build_name=build_name,
            artifacts_root=artifacts_root,
            package=spec.package,
            validate_fmus=validate_fmus,
            pyssp=pyssp,
        )
    return outputs


def run_fixture(
    model_dir: Path | str,
    *,
    repo_root: Path | str,
    model_name: str | None = None,
    composition: str = "System",
    studies: Sequence[str | StudyBuild] = ("baseline",),
    package: PackageStep | None = None,
    validate_fmus: bool = True,
    build_name: str = "model",
    artifacts_root: Path | str | None = None,
    pyssp: str | Path | None = None,
) -> int:
    """Build one fixture's studies from its directory and print each output.

    This is the fixture entry point, not a general library function: it prints
    one ``Built <model> <study>: <path>`` line per study and returns the
    process exit code.
    """
    model = Path(model_dir)
    name = model_name or model.name
    entries = tuple(
        StudyBuild(entry, package) if isinstance(entry, str) else entry
        for entry in studies
    )
    outputs = build_studies(
        model_dir=model,
        repo_root=repo_root,
        model_name=name,
        composition=composition,
        studies=entries,
        build_name=build_name,
        artifacts_root=artifacts_root,
        validate_fmus=validate_fmus,
        pyssp=pyssp,
    )
    for study, path in outputs.items():
        print(f"Built {name} {study}: {path}")
    return 0


def run_legacy_fixture(
    model_dir: Path | str,
    *,
    repo_root: Path | str,
    study: str = "baseline",
    flatten: bool = False,
    strip_resources: Sequence[str] | None = None,
    artifacts_root: Path | str | None = None,
    pyssp: str | Path | None = None,
) -> int:
    """Build one checked-in SSP body and print its output.

    The model's ``ssp_meta.source`` selects the checked-in body; the SysML
    study supplies only the experiment descriptor. ``model_dir`` is read-only.
    """
    model = Path(model_dir)
    name = model.name
    artifacts = _artifacts_root(repo_root, artifacts_root)
    architecture_dir = model / "architecture"
    study_dir = artifacts / "studies" / name / study
    model_build_dir = artifacts / "models" / name / study / "model"

    build_study(
        architecture_dir,
        study_dir,
        study,
        name,
        pyssp=pyssp,
    )
    descriptor = read_study_descriptor(study_dir / "study.json")

    if descriptor.model_source is None:
        raise ValueError(
            f"Study '{study}' declares no ssp_meta.source; add it to the "
            "SspModel composition to select the legacy SSP body"
        )
    source_dir = (Path(repo_root) / descriptor.model_source).resolve()
    if not (source_dir / "SystemStructure.ssd").is_file():
        raise FileNotFoundError(
            f"SSP source '{descriptor.model_source}' has no SystemStructure.ssd"
        )

    output = build_legacy_model(
        source_dir,
        model_build_dir,
        flatten=flatten,
        strip_resources=strip_resources,
    )
    print(f"Built {name} {study}: {output}")
    return 0


def _omc_executable(omc: str | Path | None) -> str:
    if omc is not None:
        return str(omc)
    found = shutil.which("omc")
    if found is None:
        raise FileNotFoundError(
            "omc executable not found; install OpenModelica or pass omc="
        )
    return found


def _write_mos(
    work_dir: Path, source_file: Path, class_name: str, file_name_prefix: str
) -> Path:
    mos_path = work_dir / "build.mos"
    mos_path.write_text(
        "\n".join(
            [
                "loadModel(Modelica);",
                f'loadFile("{source_file}");',
                'installPackage(Modelica, "4.0.0", exactMatch=false);',
                'setCommandLineOptions("--fmiFlags=s:cvode");',
                'setCommandLineOptions("--fmuRuntimeDepends=all");',
                f'buildModelFMU({class_name}, version="2.0", fmuType="cs", '
                f'platforms={{"static"}}, fileNamePrefix="{file_name_prefix}");',
                "getErrorString();",
                "",
            ]
        )
    )
    return mos_path


def _copy_archive_file(archive: ZipFile, member_name: str, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("wb") as handle:
        handle.write(archive.read(member_name))


def _sync_fmu_dir(archive_path: Path, index_html_path: Path, fmu_dir: Path) -> None:
    shutil.rmtree(fmu_dir / "binaries" / "linux64", ignore_errors=True)
    shutil.rmtree(fmu_dir / "documentation", ignore_errors=True)
    shutil.rmtree(fmu_dir / "sources", ignore_errors=True)

    fmu_dir.mkdir(parents=True, exist_ok=True)
    (fmu_dir / "binaries" / "linux64").mkdir(parents=True, exist_ok=True)
    (fmu_dir / "documentation").mkdir(parents=True, exist_ok=True)

    shutil.copy2(index_html_path, fmu_dir / "documentation" / "index.html")

    with ZipFile(archive_path) as archive:
        if "modelDescription.xml" not in archive.namelist():
            raise FileNotFoundError(f"Missing modelDescription.xml in {archive_path}")
        _copy_archive_file(
            archive, "modelDescription.xml", fmu_dir / "modelDescription.xml"
        )

        for member in archive.namelist():
            if member.startswith("binaries/linux64/") and not member.endswith("/"):
                _copy_archive_file(archive, member, fmu_dir / member)
            elif member.startswith("resources/") and not member.endswith("/"):
                _copy_archive_file(archive, member, fmu_dir / member)

    with FMU(fmu_dir, mode="a") as fmu:
        with fmu.model_description as model_description:
            model_description.strip_model_exchange()


def _sanitise_file_name_prefix(class_name: str) -> str:
    return re.sub(r"[^0-9A-Za-z_]+", "_", class_name).strip("_")


def build_fmu_from_modelica(
    *,
    source_file: Path | str,
    class_name: str,
    fmu_dir: Path | str,
    file_name_prefix: str | None = None,
    omc: str | Path | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> Path:
    """Compile ``source_file`` with omc and sync the unpacked FMU into ``fmu_dir``.

    Copies ``modelDescription.xml``, ``binaries/linux64``, ``resources``, and
    ``documentation/index.html`` into ``fmu_dir``, then strips model-exchange
    metadata. ``fmu_dir`` is an output and is partially reset; ``source_file``
    is read-only.

    ``file_name_prefix`` defaults to a sanitised ``class_name``. Raises
    ``FileNotFoundError`` for a missing omc, archive, or documentation page and
    ``RuntimeError`` with omc's output when compilation fails. Returns
    ``fmu_dir``.
    """
    source = Path(source_file).resolve()
    destination = Path(fmu_dir)
    prefix = file_name_prefix or _sanitise_file_name_prefix(class_name)
    omc_executable = _omc_executable(omc)

    with tempfile.TemporaryDirectory(prefix=f"{prefix}_") as temp_dir:
        work_dir = Path(temp_dir)
        mos_path = _write_mos(work_dir, source, class_name, prefix)
        completed = subprocess.run(
            [omc_executable, str(mos_path)],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"{omc_executable} {mos_path} failed with exit code "
                f"{completed.returncode}\nstdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}"
            )

        archive_path = work_dir / f"{prefix}.fmu"
        if not archive_path.is_file():
            raise FileNotFoundError(f"Expected FMU archive not found: {archive_path}")

        index_html_path = work_dir / "index.html"
        if not index_html_path.is_file():
            raise FileNotFoundError(
                f"Expected documentation page not found: {index_html_path}"
            )

        _sync_fmu_dir(archive_path, index_html_path, destination)

    return destination


__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "build_fixture",
    "build_fmu_from_modelica",
    "build_legacy_model",
    "build_model",
    "build_studies",
    "build_study",
    "derive_ssd_from_sysml",
    "derive_ssp_from_sysml",
    "derive_study_from_sysml",
    "run_fixture",
    "run_legacy_fixture",
]
