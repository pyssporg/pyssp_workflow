"""SysML <-> SSP derivation.

Contract (not yet implemented): invoke the external ``pyssp`` CLI as a
subprocess and exchange only SysML and SSD artifacts. Never import
``pyssp_sysml2`` here. Emit a provenance map from derived SSP elements back to
their SysML source so the derivation is auditable.

``pyssp_vv.oracle`` and ``pyssp_vv.evidence`` must never import this module.
"""
