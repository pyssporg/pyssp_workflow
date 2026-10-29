"""Node wrappers for flow engines (optional ``flow`` extra).

Domain work lives elsewhere: measurement and judgment in ``pyssp_vv``,
simulation in ``pyssp_simulate``. Nodes only add scheduling policy. Importing
this package requires ``sequence-extensions-flow``.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util

_FLOW_HINT = (
    "pyssp_workflow.nodes requires the 'flow' extra: "
    "pip install 'pyssp-workflow[flow]'"
)


def _flow_spec() -> importlib.machinery.ModuleSpec | None:
    """The spec of ``sequence_extensions.flow``, or ``None`` when it is absent.

    Probing the subpackage, not its parent, distinguishes a missing extra from
    an installed ``sequence_extensions`` that ships no ``flow`` package.
    """
    try:
        return importlib.util.find_spec("sequence_extensions.flow")
    except ModuleNotFoundError as exc:
        if exc.name not in ("sequence_extensions", "sequence_extensions.flow"):
            raise
        return None


if _flow_spec() is None:
    raise ImportError(_FLOW_HINT)

# An ImportError raised inside ``sequence_extensions.flow`` is not masked: the
# guard above only reports a missing extra, this import surfaces broken installs.
from sequence_extensions.flow import node  # noqa: E402,F401  (fail early, clearly)

from pyssp_workflow.nodes.authoring import derive_analysis, derive_ssd, derive_ssp  # noqa: E402
from pyssp_workflow.nodes.evidence import write_bundle  # noqa: E402

__all__ = ["derive_ssd", "derive_ssp", "derive_analysis", "write_bundle"]
