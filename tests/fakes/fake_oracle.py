"""A trivially deterministic oracle used to exercise the protocol.

It never reads a trajectory. It exists to prove that a plain object can satisfy
:class:`pyssp_vv.oracle.Oracle` without inheriting from anything.
"""

from __future__ import annotations

from pyssp_vv.oracle.protocol import Candidate, OracleContext, OracleResult, Provenance
from pyssp_vv.spec.verdict import Verdict


class FixedOracle:
    """Return a fixed verdict regardless of the candidate."""

    kind = "invariant"
    provenance = Provenance.INVARIANT

    def __init__(self, verdict: Verdict = Verdict.PASS) -> None:
        self._verdict = verdict

    def evaluate(self, candidate: Candidate, context: OracleContext) -> OracleResult:
        return OracleResult(
            oracle_id=self.kind,
            verdict=self._verdict,
            metrics={"candidate_exists": float(candidate.result_csv.exists())},
            reasons=(f"assessment={context.assessment_id}",),
        )
