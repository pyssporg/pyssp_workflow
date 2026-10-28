"""Collection hooks: apply each test file's level marker and guard ``tests/``."""

from __future__ import annotations

from pathlib import Path

import pytest
from fixture_guard import check, snapshot
from support import FILE_LEVELS, LEVEL_MARKERS


def pytest_sessionstart(session: pytest.Session) -> None:
    """Snapshot the test tree before any test runs."""
    snapshot()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Fail the run when a test wrote into the test tree."""
    check(session)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if any(item.get_closest_marker(name) for name in LEVEL_MARKERS):
            continue
        level = FILE_LEVELS.get(Path(str(item.path)).name)
        if level is not None:
            item.add_marker(getattr(pytest.mark, level))
