"""The verdict vocabulary shared by every oracle.

``invalid`` is not a failure. It means the comparison was not legal: the held
factors differ between runs, an input is missing, or the artifacts are not
comparable. Collapsing ``invalid`` into ``fail`` is what makes uncontrolled
comparisons look like engine defects.

``blocked`` means the run could not produce evidence at all (engine missing,
timeout, crash). ``waived`` means a failure is known and accepted, with a
recorded reason and owner.
"""

from __future__ import annotations

from enum import Enum


class Verdict(str, Enum):
    """Outcome of one oracle evaluation."""

    PASS = "pass"
    FAIL = "fail"
    INVALID = "invalid"
    BLOCKED = "blocked"
    WAIVED = "waived"

    def __str__(self) -> str:  # keeps JSON and f-strings consistent
        return self.value
