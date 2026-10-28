"""Every collected test declares exactly one test level."""

from __future__ import annotations

import pytest
from support import LEVEL_MARKERS

pytestmark = pytest.mark.level_static


def test_every_collected_test_carries_exactly_one_level_marker(
    request: pytest.FixtureRequest,
) -> None:
    unmarked: list[str] = []
    duplicated: list[str] = []
    for item in request.session.items:
        levels = [
            marker.name
            for marker in item.iter_markers()
            if marker.name in LEVEL_MARKERS
        ]
        if not levels:
            unmarked.append(item.nodeid)
        elif len(levels) > 1:
            duplicated.append(item.nodeid)

    assert not unmarked, "tests without a level marker:\n" + "\n".join(unmarked)
    assert not duplicated, "tests with several level markers:\n" + "\n".join(
        duplicated
    )
