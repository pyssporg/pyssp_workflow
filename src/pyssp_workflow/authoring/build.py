"""Analysis and model SSP build steps."""

from __future__ import annotations

import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from pyssp_standard import unpack_archive

from pyssp_workflow import fixture
from pyssp_workflow.analysis import read_analysis_descriptor
from pyssp_workflow.authoring._dirs import reset_dir
from pyssp_workflow.authoring._fmu import strip_model_exchange
from pyssp_workflow.authoring.derive import (
    DEFAULT_TIMEOUT_SECONDS,
    derive_analysis_from_sysml,
    derive_ssp_from_sysml,
)

_SELECTION_SCOPES = ("analysis", "model")


def build_analysis(
    architecture_dir: Path | str,
    analysis_dir: Path | str,
    composition: str,
    model_name: str,
    *,
    pyssp: str | Path | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    selections: Mapping[str, str] | None = None,
) -> Path:
    """Reset ``analysis_dir`` and generate its SSV, SSM, and ``analysis.json``.

    ``architecture_dir`` is read-only. Returns ``analysis_dir``. ``selections``
    resolves SysML variation points in ``composition`` at build time only; the
    counterpart selection must reach :func:`build_model` so the SSV/SSM and the
    SSD agree.
    """
    architecture = Path(architecture_dir)
    analysis = Path(analysis_dir)
    reset_dir(analysis)
    derive_analysis_from_sysml(
        architecture,
        analysis,
        composition,
        model_name=model_name,
        pyssp=pyssp,
        timeout=timeout,
        selections=selections,
    )
    return analysis


def build_model(
    architecture_dir: Path | str,
    model_dir: Path | str,
    composition: str,
    *,
    fmu_root: Path | str | None = None,
    validate_fmus: bool = True,
    pyssp: str | Path | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    selections: Mapping[str, str] | None = None,
) -> Path:
    """Export the model SSP into ``model_dir`` and unpack its FMUs.

    ``model_dir`` is an output and is reset; ``architecture_dir`` and
    ``fmu_root`` are read-only. Model-exchange metadata is stripped from every
    unpacked FMU. Returns ``model_dir``. ``selections`` resolves SysML variation
    points in ``composition`` at build time only; the counterpart selection must
    reach :func:`build_analysis` so the SSD and the SSV/SSM agree.
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
            selections=selections,
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
    analysis: str,
    build_name: str = "model",
    artifacts_root: Path | str | None = None,
    validate_fmus: bool = True,
    pyssp: str | Path | None = None,
    selections: Mapping[str, Mapping[str, Mapping[str, str]]] | None = None,
) -> fixture.BuiltFixture:
    """Build one analysis and its exported model SSP; packaging is not applied.

    ``selections`` is the fixture-wide map; this analysis's ``analysis`` entry reaches
    :func:`build_analysis` and its ``model`` entry reaches :func:`build_model`.
    They differ because a selection key is resolved relative to the composition
    being generated: the analysis composes the model through ``part sut : System``,
    so a structural point is ``sut.<key>`` in the analysis and ``<key>`` in the
    model. Selection is build-time only.
    """
    model = Path(model_dir)
    name = model_name or model.name
    artifacts = fixture.artifacts_root(repo_root, artifacts_root)
    architecture_dir = model / "architecture"
    analysis_dir = fixture.analysis_dir(artifacts, name, analysis)
    model_build_dir = fixture.model_dir(artifacts, name, analysis, build_name)
    scoped = (selections or {}).get(analysis, {})

    build_analysis(
        architecture_dir,
        analysis_dir,
        analysis,
        name,
        pyssp=pyssp,
        selections=scoped.get("analysis"),
    )
    build_model(
        architecture_dir,
        model_build_dir,
        composition,
        fmu_root=repo_root,
        validate_fmus=validate_fmus,
        pyssp=pyssp,
        selections=scoped.get("model"),
    )

    descriptor = read_analysis_descriptor(analysis_dir / "analysis.json")
    return fixture.BuiltFixture(
        model_name=name,
        analysis=analysis,
        analysis_dir=analysis_dir,
        model_dir=model_build_dir,
        descriptor=descriptor,
    )


def build_fixture(
    *,
    model_dir: Path | str,
    repo_root: Path | str,
    model_name: str | None = None,
    composition: str = "System",
    analyses: Sequence[str],
    build_name: str = "model",
    artifacts_root: Path | str | None = None,
    validate_fmus: bool = True,
    pyssp: str | Path | None = None,
    selections: Mapping[str, Mapping[str, Mapping[str, str]]] | None = None,
) -> dict[str, fixture.BuiltFixture]:
    """Build one analysis and exported model SSP per analysis, keyed by analysis name.

    ``artifacts_root`` defaults to ``repo_root / "artifacts"``; it is never
    discovered from the working directory. Analysis artifacts land in
    ``<artifacts_root>/analyses/<model>/<analysis>`` and the model SSP in
    ``<artifacts_root>/models/<model>/<analysis>/<build_name>``. ``model_dir`` is
    the fixture directory and is read-only. Packaging is the caller's step.

    ``selections`` maps an analysis name to ``{"analysis": {...}, "model": {...}}``:
    the ``analysis`` entry reaches that analysis's :func:`build_analysis` and the
    ``model`` entry its :func:`build_model`. Two scopes exist because a
    selection key is resolved relative to the composition being generated — the
    analysis composes the model through ``part sut : System``, so a structural
    point is ``sut.<key>`` in the analysis and ``<key>`` in the model. The maps are
    not interchangeable. ``analyses`` remains the source of truth for which
    analyses exist; an unknown analysis name or a scope key other than ``analysis`` or
    ``model`` raises ``ValueError``. A missing scope means that build runs
    unselected. Selection is build-time only.
    """
    unknown = sorted(set(selections or ()) - set(analyses))
    if unknown:
        raise ValueError(
            "selections name analyses that are not built: " + ", ".join(unknown)
        )
    for analysis, scoped in (selections or {}).items():
        unknown_scopes = sorted(set(scoped) - set(_SELECTION_SCOPES))
        if unknown_scopes:
            raise ValueError(
                f"selections for analysis '{analysis}' name unknown scopes: "
                + ", ".join(unknown_scopes)
                + "; allowed scopes: "
                + ", ".join(_SELECTION_SCOPES)
            )
    return {
        analysis: _build_one(
            model_dir=model_dir,
            repo_root=repo_root,
            model_name=model_name,
            composition=composition,
            analysis=analysis,
            build_name=build_name,
            artifacts_root=artifacts_root,
            validate_fmus=validate_fmus,
            pyssp=pyssp,
            selections=selections,
        )
        for analysis in analyses
    }


__all__ = ["build_fixture", "build_model", "build_analysis"]
