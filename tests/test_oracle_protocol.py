"""Any plain object with the right attributes is an oracle."""

from __future__ import annotations

from pathlib import Path

from fakes.fake_oracle import FixedOracle

from pyssp_vv.oracle.protocol import Candidate, Oracle, OracleContext, OracleResult, Provenance
from pyssp_vv.spec.verdict import Verdict


def test_plain_object_satisfies_the_protocol():
    assert isinstance(FixedOracle(), Oracle)


def test_oracle_returns_one_result(tmp_path: Path):
    result_csv = tmp_path / "result.csv"
    result_csv.write_text("time,y\n0,0\n", encoding="utf-8")

    result = FixedOracle(Verdict.FAIL).evaluate(
        Candidate(run_dir=tmp_path, result_csv=result_csv),
        OracleContext(assessment_id="m/c", held_factors={"step_size": "0.01"}),
    )

    assert isinstance(result, OracleResult)
    assert result.verdict is Verdict.FAIL
    assert result.metrics["candidate_exists"] == 1.0


def test_agreement_is_a_distinct_provenance():
    assert Provenance.AGREEMENT.value == "agreement"
    assert Provenance.AGREEMENT is not Provenance.REFERENCE
