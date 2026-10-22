"""The assessment is data: it must survive JSON and reject typos."""

from __future__ import annotations

import json

import pytest

from pyssp_vv.spec.assessment import Assessment, Factor, OracleRef, Tolerance
from pyssp_vv.spec.verdict import Verdict


def make_assessment() -> Assessment:
    return Assessment(
        assessment_id="BouncingBall/baseline",
        model="BouncingBall",
        case="baseline",
        factor=Factor("engine", levels=("ssp4sim", "omsimulator")),
        held=("window", "step_size", "param_set"),
        oracles=(
            OracleRef(
                oracle_id="engine-agreement",
                kind="cross_engine",
                tolerance=Tolerance(atol=1e-3, rtol=1e-2, shift_samples=2),
            ),
        ),
    )


def test_roundtrip_is_lossless_and_json_safe():
    original = make_assessment()
    data = original.to_dict()
    assert json.loads(json.dumps(data)) == data
    assert Assessment.from_dict(data) == original


def test_unknown_top_level_key_is_rejected():
    data = make_assessment().to_dict()
    data["extra"] = "typo"
    with pytest.raises(ValueError, match="Unknown assessment keys"):
        Assessment.from_dict(data)


def test_unknown_oracle_key_is_rejected():
    data = make_assessment().to_dict()
    data["oracles"][0]["tolerence"] = {"atol": 1.0}
    with pytest.raises(ValueError, match="Unknown oracle keys"):
        Assessment.from_dict(data)


def test_factor_cannot_also_be_held():
    data = make_assessment().to_dict()
    data["held"] = ["engine", "window"]
    with pytest.raises(ValueError, match="both the independent factor"):
        Assessment.from_dict(data)


def test_assessment_requires_an_oracle():
    data = make_assessment().to_dict()
    data["oracles"] = []
    with pytest.raises(ValueError, match="at least one oracle"):
        Assessment.from_dict(data)


def test_duplicate_levels_are_rejected():
    with pytest.raises(ValueError, match="duplicate levels"):
        Factor("engine", levels=("ssp4sim", "ssp4sim"))


def test_negative_tolerance_is_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        Tolerance(atol=-1.0)


def test_verdict_vocabulary_is_explicit():
    assert {item.value for item in Verdict} == {
        "pass",
        "fail",
        "invalid",
        "blocked",
        "waived",
    }
    assert str(Verdict.INVALID) == "invalid"
