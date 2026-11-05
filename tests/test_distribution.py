"""The ``sysml`` extra pins the bundle without adding a surface."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.level_static

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _extras() -> dict[str, list[str]]:
    """Return ``extra -> [requirement, ...]`` from ``pyproject.toml``."""
    text = PYPROJECT.read_text(encoding="utf-8")
    section = text.split("[project.optional-dependencies]", 1)[1]
    section = section.split("\n[", 1)[0]
    extras: dict[str, list[str]] = {}
    current: str | None = None
    for raw in section.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            current = key.strip()
            extras[current] = re.findall(r'"([^"]*)"', value)
        elif current is not None:
            extras[current].extend(re.findall(r'"([^"]*)"', line))
    return extras


def test_sysml_extra_pins_the_bundle_without_repeating_pycps() -> None:
    # pycps-sysml2 arrives transitively from both siblings. Listing it here
    # would give the same pin two owners and let the three drift apart.
    names = {
        requirement.split(" @ ", 1)[0] for requirement in _extras()["sysml"]
    }
    assert names == {"pyssp-sysml2", "pyfmi-sysml2"}
