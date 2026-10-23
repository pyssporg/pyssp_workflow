"""Built fixture record and the artifact paths a fixture owns.

A fixture is one model study: the study artifacts and the exported model SSP
under the repository's artifacts root. The paths are derived from explicit
inputs, never from the working directory.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pyssp_workflow.study import StudyDescriptor

ARTIFACTS_DIRNAME = "artifacts"
STUDIES_DIRNAME = "studies"
MODELS_DIRNAME = "models"


@dataclass(frozen=True)
class BuiltFixture:
    """One built study and its exported model SSP, before binding."""

    model_name: str
    study: str
    study_dir: Path
    model_dir: Path
    descriptor: StudyDescriptor


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


def study_dir(root: Path, model_name: str, study: str) -> Path:
    """``<root>/studies/<model>/<study>``."""
    return Path(root) / STUDIES_DIRNAME / model_name / study


def model_dir(
    root: Path,
    model_name: str,
    study: str,
    build_name: str = "model",
) -> Path:
    """``<root>/models/<model>/<study>/<build_name>``."""
    return Path(root) / MODELS_DIRNAME / model_name / study / build_name


__all__ = [
    "ARTIFACTS_DIRNAME",
    "MODELS_DIRNAME",
    "STUDIES_DIRNAME",
    "BuiltFixture",
    "artifacts_root",
    "model_dir",
    "study_dir",
]
