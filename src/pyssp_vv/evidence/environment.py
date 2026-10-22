"""Fingerprint of the environment that produced evidence.

Versions matter: a verdict produced by FMPy 0.3.35 is not the same claim as one
produced by 0.3.40. Names that are not installed are recorded as absent rather
than omitted, so a later reader can tell "same version" from "not checked".
"""

from __future__ import annotations

import platform
import sys
from importlib import metadata
from typing import Iterable

#: Distributions that can change a verdict. Extend deliberately.
DEFAULT_DISTRIBUTIONS = (
    "pyssp-standard",
    "pyssp-simulate",
    "pyssp-sysml2",
    "sequence-extensions-flow",
    "fmpy",
    "OMSimulator",
    "ssp4sim",
)


def fingerprint(distributions: Iterable[str] | None = None) -> dict[str, object]:
    """Return a JSON-able description of the running environment."""
    names = tuple(distributions if distributions is not None else DEFAULT_DISTRIBUTIONS)
    versions: dict[str, str | None] = {}
    for name in names:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "executable": sys.executable,
        "distributions": versions,
    }
