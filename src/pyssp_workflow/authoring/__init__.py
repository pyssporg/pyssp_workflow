"""SysML <-> SSP derivation as a workflow step.

Contract (not yet implemented): invoke the external ``pyssp`` CLI as a
subprocess and exchange only SysML and SSD artifacts. Never import
``pyssp_sysml2`` here, and never import ``pyssp_vv``: the authoring path must not
be able to reach the judgment layer that evaluates its output.
"""
