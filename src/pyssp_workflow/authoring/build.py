"""Study and model SSP build steps."""

from __future__ import annotations

import tempfile
from collections.abc import Sequence
from pathlib import Path

from pyssp_standard import unpack_archive

from pyssp_workflow import fixture
from pyssp_workflow.authoring._dirs import reset_dir
from pyssp_workflow.authoring._fmu import strip_model_exchange
from pyssp_workflow.authoring.derive import (
    DEFAULT_TIMEOUT_SECONDS,
    derive_ssp_from_sysml,
    derive_study_from_sysml,
)
from pyssp_workflow.study import read_study_descriptor


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
    reset_dir(study)
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
    reset_dir(model)
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
    strip_model_exchange(model)
    return model


def _build_one(
    *,
    model_dir: Path | str,
    repo_root: Path | str,
    model_name: str | None = None,
    composition: str = "System",
    study: str,
    build_name: str = "model",
    artifacts_root: Path | str | None = None,
    validate_fmus: bool = True,
    pyssp: str | Path | None = None,
) -> fixture.BuiltFixture:
    """Build one study and its exported model SSP; packaging is not applied."""
    model = Path(model_dir)
    name = model_name or model.name
    artifacts = fixture.artifacts_root(repo_root, artifacts_root)
    architecture_dir = model / "architecture"
    study_dir = fixture.study_dir(artifacts, name, study)
    model_build_dir = fixture.model_dir(artifacts, name, study, build_name)

    build_study(
        architecture_dir,
        study_dir,
        study,
        name,
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
    return fixture.BuiltFixture(
        model_name=name,
        study=study,
        study_dir=study_dir,
        model_dir=model_build_dir,
        descriptor=descriptor,
    )


def build_fixture(
    *,
    model_dir: Path | str,
    repo_root: Path | str,
    model_name: str | None = None,
    composition: str = "System",
    studies: Sequence[str],
    build_name: str = "model",
    artifacts_root: Path | str | None = None,
    validate_fmus: bool = True,
    pyssp: str | Path | None = None,
) -> dict[str, fixture.BuiltFixture]:
    """Build one study and exported model SSP per study, keyed by study name.

    ``artifacts_root`` defaults to ``repo_root / "artifacts"``; it is never
    discovered from the working directory. Study artifacts land in
    ``<artifacts_root>/studies/<model>/<study>`` and the model SSP in
    ``<artifacts_root>/models/<model>/<study>/<build_name>``. ``model_dir`` is
    the fixture directory and is read-only. Packaging is the caller's step.
    """
    return {
        study: _build_one(
            model_dir=model_dir,
            repo_root=repo_root,
            model_name=model_name,
            composition=composition,
            study=study,
            build_name=build_name,
            artifacts_root=artifacts_root,
            validate_fmus=validate_fmus,
            pyssp=pyssp,
        )
        for study in studies
    }


__all__ = ["build_fixture", "build_model", "build_study"]
