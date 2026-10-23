"""Build reporting."""

from __future__ import annotations

from collections.abc import Mapping

from pyssp_workflow import fixture


def report_builds(builds: Mapping[str, fixture.BuiltFixture]) -> int:
    """Print one ``Built <model> <study>: <path>`` line per build; return 0."""
    for build in builds.values():
        print(f"Built {build.model_name} {build.study}: {build.model_dir}")
    return 0


__all__ = ["report_builds"]
