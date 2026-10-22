"""Node wrappers for flow engines (optional ``flow`` extra).

Domain functions live in the plain modules; nodes add scheduling policy only.
Importing this package requires ``sequence-extensions-flow`` so that the core
stays installable on any supported Python without a flow engine.
"""

try:
    from sequence_extensions.flow import node  # noqa: F401  (fail early, clearly)
except ImportError as exc:  # pragma: no cover - depends on the extra
    raise ImportError(
        "pyssp_vv.nodes requires the 'flow' extra: pip install 'pyssp-vv[flow]'"
    ) from exc

from pyssp_vv.nodes.evidence import write_bundle

__all__ = ["write_bundle"]
