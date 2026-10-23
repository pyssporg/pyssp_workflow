"""OpenModelica FMU build step."""

from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path
from zipfile import ZipFile

from pyssp_workflow.authoring._fmu import strip_fmu
from pyssp_workflow.authoring._process import find_executable, run
from pyssp_workflow.authoring.derive import DEFAULT_TIMEOUT_SECONDS


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

    strip_fmu(fmu_dir)


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
    omc_executable = find_executable(
        "omc",
        omc,
        hint="install OpenModelica or pass omc=",
    )

    with tempfile.TemporaryDirectory(prefix=f"{prefix}_") as temp_dir:
        work_dir = Path(temp_dir)
        mos_path = _write_mos(work_dir, source, class_name, prefix)
        run([omc_executable, str(mos_path)], cwd=work_dir, timeout=timeout)

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


__all__ = ["build_fmu_from_modelica"]
