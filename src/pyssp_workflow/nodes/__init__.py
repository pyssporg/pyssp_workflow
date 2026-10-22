"""Node wrappers for flow engines (optional ``flow`` extra).

Domain work lives elsewhere: measurement and judgment in ``pyssp_vv``,
simulation in ``pyssp_simulate``. Nodes only add scheduling policy. Importing
this package requires ``sequence-extensions-flow``.
"""

try:
    from sequence_extensions.flow import node  # noqa: F401  (fail early, clearly)
except ImportError as exc:  # pragma: no cover - depends on the extra
    raise ImportError(
        "pyssp_workflow.nodes requires the 'flow' extra: "
        "pip install 'pyssp-workflow[flow]'"
    ) from exc

from pyssp_workflow.nodes.evidence import write_bundle

__all__ = ["write_bundle"]
