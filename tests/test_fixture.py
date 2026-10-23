"""Artifact paths are derived from explicit roots, never the working directory."""

from __future__ import annotations

from pathlib import Path

from pyssp_workflow import fixture


def test_artifacts_root_defaults_to_the_repo_root(tmp_path: Path) -> None:
    assert fixture.artifacts_root(tmp_path) == tmp_path / "artifacts"
    assert fixture.artifacts_root(str(tmp_path)) == tmp_path / "artifacts"


def test_artifacts_root_is_overridable(tmp_path: Path) -> None:
    explicit = tmp_path / "elsewhere" / "out"

    assert fixture.artifacts_root(tmp_path, explicit) == explicit
    assert fixture.artifacts_root(tmp_path, str(explicit)) == explicit


def test_study_dir_is_the_study_artifacts_directory(tmp_path: Path) -> None:
    assert fixture.study_dir(tmp_path, "demo", "baseline") == (
        tmp_path / "studies" / "demo" / "baseline"
    )


def test_model_dir_is_the_exported_model_directory(tmp_path: Path) -> None:
    assert fixture.model_dir(tmp_path, "demo", "baseline") == (
        tmp_path / "models" / "demo" / "baseline" / "model"
    )
    assert fixture.model_dir(tmp_path, "demo", "baseline", "variant") == (
        tmp_path / "models" / "demo" / "baseline" / "variant"
    )


def test_study_and_model_dirs_are_distinct(tmp_path: Path) -> None:
    assert fixture.study_dir(tmp_path, "demo", "baseline") != fixture.model_dir(
        tmp_path, "demo", "baseline"
    )
