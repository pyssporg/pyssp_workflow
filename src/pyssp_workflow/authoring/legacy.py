"""Legacy checked-in SSP build steps."""

from __future__ import annotations

import shutil
from collections.abc import Sequence
from pathlib import Path

from pyssp_standard import SSP

from pyssp_workflow import fixture
from pyssp_workflow.analysis import read_analysis_descriptor
from pyssp_workflow.authoring._dirs import reset_dir
from pyssp_workflow.authoring._fmu import strip_fmu
from pyssp_workflow.authoring.build import build_analysis


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
        strip_fmu(path)


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
    reset_dir(model)
    shutil.copytree(source, model, dirs_exist_ok=True)
    _strip_legacy_resources(model / "resources", strip_resources)

    if flatten:
        with SSP(model, mode="a") as ssp:
            with ssp.system_structure() as ssd:
                ssd.flatten()

    return model


def build_legacy_fixture(
    model_dir: Path | str,
    *,
    repo_root: Path | str,
    analysis: str = "baseline",
    flatten: bool = False,
    strip_resources: Sequence[str] | None = None,
    artifacts_root: Path | str | None = None,
    pyssp: str | Path | None = None,
) -> fixture.BuiltFixture:
    """Build one checked-in SSP body and return its record; no packaging.

    The model's ``ssp_meta.source`` selects the checked-in body; the SysML
    analysis supplies only the experiment descriptor. ``model_dir`` is read-only.
    """
    model = Path(model_dir)
    name = model.name
    artifacts = fixture.artifacts_root(repo_root, artifacts_root)
    architecture_dir = model / "architecture"
    analysis_dir = fixture.analysis_dir(artifacts, name, analysis)
    model_build_dir = fixture.model_dir(artifacts, name, analysis)

    build_analysis(
        architecture_dir,
        analysis_dir,
        analysis,
        name,
        pyssp=pyssp,
    )
    descriptor = read_analysis_descriptor(analysis_dir / "analysis.json")

    if descriptor.model_source is None:
        raise ValueError(
            f"Analysis '{analysis}' declares no ssp_meta.source; add it to the "
            "SspModel composition to select the legacy SSP body"
        )
    source_dir = (Path(repo_root) / descriptor.model_source).resolve()
    if not (source_dir / "SystemStructure.ssd").is_file():
        raise FileNotFoundError(
            f"SSP source '{descriptor.model_source}' has no SystemStructure.ssd"
        )

    build_legacy_model(
        source_dir,
        model_build_dir,
        flatten=flatten,
        strip_resources=strip_resources,
    )
    return fixture.BuiltFixture(
        model_name=name,
        analysis=analysis,
        analysis_dir=analysis_dir,
        model_dir=model_build_dir,
        descriptor=descriptor,
    )


__all__ = ["build_legacy_fixture", "build_legacy_model"]
