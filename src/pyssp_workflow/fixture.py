"""Built fixture record and the artifact paths a fixture owns.

A fixture is one model analysis: the analysis artifacts and the exported model SSP
under the repository's artifacts root. The paths are derived from explicit
inputs, never from the working directory.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pyssp_workflow.analysis import AnalysisDescriptor

ARTIFACTS_DIRNAME = "artifacts"
ANALYSES_DIRNAME = "analyses"
MODELS_DIRNAME = "models"


@dataclass(frozen=True)
class BuiltFixture:
    """One built analysis and its exported model SSP, before binding."""

    model_name: str
    analysis: str
    analysis_dir: Path
    model_dir: Path
    descriptor: AnalysisDescriptor


def artifacts_root(
    repo_root: Path | str,
    artifacts_root: Path | str | None = None,
) -> Path:
    """``artifacts_root`` when given, else ``repo_root / "artifacts"``."""
    return (
        Path(artifacts_root)
        if artifacts_root is not None
        else Path(repo_root) / ARTIFACTS_DIRNAME
    )


def analysis_dir(root: Path, model_name: str, analysis: str) -> Path:
    """``<root>/analyses/<model>/<analysis>``."""
    return Path(root) / ANALYSES_DIRNAME / model_name / analysis


def model_dir(
    root: Path,
    model_name: str,
    analysis: str,
    build_name: str = "model",
) -> Path:
    """``<root>/models/<model>/<analysis>/<build_name>``."""
    return Path(root) / MODELS_DIRNAME / model_name / analysis / build_name


__all__ = [
    "ARTIFACTS_DIRNAME",
    "MODELS_DIRNAME",
    "ANALYSES_DIRNAME",
    "BuiltFixture",
    "artifacts_root",
    "model_dir",
    "analysis_dir",
]
