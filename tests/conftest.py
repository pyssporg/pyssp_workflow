"""Collection hooks: apply each test file's level marker."""

from __future__ import annotations

from pathlib import Path

import pytest
from support import FILE_LEVELS, LEVEL_MARKERS


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if any(item.get_closest_marker(name) for name in LEVEL_MARKERS):
            continue
        level = FILE_LEVELS.get(Path(str(item.path)).name)
        if level is not None:
            item.add_marker(getattr(pytest.mark, level))
