"""The shipped metadata exposes only ``dev`` and pins the bundle in base."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.level_static

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _section(name: str) -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    section = text.split(f"[{name}]", 1)[1]
    return section.split("\n[", 1)[0]


def _groups(name: str) -> dict[str, list[str]]:
    """Return ``group -> [requirement, ...]`` for a dependency table."""
    groups: dict[str, list[str]] = {}
    current: str | None = None
    for raw in _section(name).splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            current = key.strip()
            groups[current] = re.findall(r'"([^"]*)"', value)
        elif current is not None:
            groups[current].extend(re.findall(r'"([^"]*)"', line))
    return groups


def _names(requirements: list[str]) -> set[str]:
    return {requirement.split(" @ ", 1)[0] for requirement in requirements}


def test_only_the_dev_extra_is_shipped() -> None:
    extras = _groups("project.optional-dependencies")

    assert set(extras) == {"dev"}
    assert extras["dev"] == ["pytest>=8", "ruff>=0.6"]


def test_sysml_bundle_is_pinned_once_in_base_dependencies() -> None:
    # pycps-sysml2 arrives transitively from both siblings. Listing it here
    # would give the same pin two owners and let the three drift apart.
    requirements = _groups("project")["dependencies"]

    assert {"pyssp-sysml2", "pyfmi-sysml2"} <= _names(requirements)
    assert "pycps-sysml2" not in _names(requirements)
    assert len(requirements) == len(set(requirements))
