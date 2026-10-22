"""Oracles: the only place a verdict may be produced."""

from pyssp_vv.oracle.protocol import (
    Candidate,
    Oracle,
    OracleContext,
    OracleResult,
    Provenance,
)

__all__ = ["Candidate", "Oracle", "OracleContext", "OracleResult", "Provenance"]
