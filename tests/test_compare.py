from __future__ import annotations

from pathlib import Path

import pytest
from pyssp_vv.evidence import read_metric_csv, summarize_rows

from pyssp_workflow.compare import (
    ComparisonRecord,
    ComparisonRequest,
    ResultRef,
    compare_csvs,
)


def _write_result_csv(path: Path, columns: dict[str, list[float]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = list(columns)
    lines = [",".join(names)]
    lines.extend(
        ",".join(repr(columns[name][index]) for name in names)
        for index in range(len(columns[names[0]]))
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _comparison_request(reference: Path, candidate: Path, out_dir: Path) -> ComparisonRequest:
    return ComparisonRequest(
        reference=ResultRef(reference, "reference"),
        candidate=ResultRef(candidate, "fmpy"),
        out_dir=out_dir,
        signals=("x",),
        start_time=0.0,
        stop_time=1.0,
        step_size=0.5,
    )


def test_compare_csvs_writes_one_metric_table(tmp_path: Path) -> None:
    reference = _write_result_csv(
        tmp_path / "reference" / "result.csv",
        {"time": [0.0, 0.5, 1.0], "x": [0.0, 1.0, 2.0]},
    )
    candidate = _write_result_csv(
        tmp_path / "candidate" / "result.csv",
        {"time": [0.0, 0.5, 1.0], "x": [0.0, 1.5, 2.0]},
    )
    out_dir = tmp_path / "out"
    request = _comparison_request(reference, candidate, out_dir)

    record = compare_csvs(request)

    metrics = out_dir / "metrics.csv"
    assert record.metrics_csv == metrics
    assert record.reference_label == "reference"
    assert record.candidate_label == "fmpy"
    assert [path.name for path in out_dir.iterdir()] == ["metrics.csv"]

    rows = read_metric_csv(metrics)
    assert [row.signal for row in rows] == ["x"]
    assert record.summary == summarize_rows(rows, time_points=3)
    assert record.summary.time_points == 3
    assert record.summary.max_abs_error == pytest.approx(0.5)


def test_comparison_record_round_trips_through_its_dict(tmp_path: Path) -> None:
    reference = _write_result_csv(
        tmp_path / "reference" / "result.csv", {"time": [0.0, 1.0], "x": [0.0, 1.0]}
    )
    candidate = _write_result_csv(
        tmp_path / "candidate" / "result.csv", {"time": [0.0, 1.0], "x": [0.0, 2.0]}
    )
    out_dir = tmp_path / "out"
    record = compare_csvs(_comparison_request(reference, candidate, out_dir))

    data = record.to_dict(out_dir)

    assert set(data) == {"reference_label", "candidate_label", "metrics", "summary"}
    assert data["metrics"] == "metrics.csv"
    assert data["summary"] == record.summary.to_dict()
    assert ComparisonRecord.from_dict(data, base_dir=out_dir) == record
    assert record.to_dict(tmp_path)["metrics"] == "out/metrics.csv"


def test_comparison_record_from_dict_ignores_legacy_status_and_error(
    tmp_path: Path,
) -> None:
    reference = _write_result_csv(
        tmp_path / "reference" / "result.csv", {"time": [0.0, 1.0], "x": [0.0, 1.0]}
    )
    candidate = _write_result_csv(
        tmp_path / "candidate" / "result.csv", {"time": [0.0, 1.0], "x": [0.0, 2.0]}
    )
    out_dir = tmp_path / "out"
    record = compare_csvs(_comparison_request(reference, candidate, out_dir))

    legacy = record.to_dict(out_dir) | {"status": "completed", "error": None}

    parsed = ComparisonRecord.from_dict(legacy, base_dir=out_dir)

    assert parsed == record
    assert parsed.metrics_csv == out_dir / "metrics.csv"


def test_compare_csvs_creates_a_missing_out_dir(tmp_path: Path) -> None:
    reference = _write_result_csv(
        tmp_path / "reference" / "result.csv", {"time": [0.0, 1.0], "x": [0.0, 1.0]}
    )
    candidate = _write_result_csv(
        tmp_path / "candidate" / "result.csv", {"time": [0.0, 1.0], "x": [0.0, 1.0]}
    )
    out_dir = tmp_path / "nested" / "out"
    request = _comparison_request(reference, candidate, out_dir)

    compare_csvs(request)

    assert (out_dir / "metrics.csv").is_file()


def test_compare_csvs_rejects_a_signal_one_csv_lacks(tmp_path: Path) -> None:
    reference = _write_result_csv(
        tmp_path / "reference" / "result.csv", {"time": [0.0, 1.0], "x": [0.0, 1.0]}
    )
    candidate = _write_result_csv(
        tmp_path / "candidate" / "result.csv", {"time": [0.0, 1.0], "x": [0.0, 1.0]}
    )
    out_dir = tmp_path / "out"
    request = ComparisonRequest(
        reference=ResultRef(reference, "reference"),
        candidate=ResultRef(candidate, "fmpy"),
        out_dir=out_dir,
        signals=("x", "missing"),
        start_time=0.0,
        stop_time=1.0,
        step_size=0.5,
    )

    with pytest.raises(KeyError, match="missing"):
        compare_csvs(request)

    assert not out_dir.exists()


def test_compare_csvs_applies_the_reference_and_result_prefixes(
    tmp_path: Path,
) -> None:
    reference = _write_result_csv(
        tmp_path / "reference" / "result.csv",
        {"default.example.time": [0.0, 1.0], "default.example.x": [0.0, 1.0]},
    )
    candidate = _write_result_csv(
        tmp_path / "candidate" / "result.csv",
        {"fmu.time": [0.0, 1.0], "fmu.x": [0.0, 2.0]},
    )
    out_dir = tmp_path / "out"
    request = ComparisonRequest(
        reference=ResultRef(reference, "reference"),
        candidate=ResultRef(candidate, "fmpy"),
        out_dir=out_dir,
        signals=("x",),
        start_time=0.0,
        stop_time=1.0,
        step_size=0.5,
        reference_prefix="default.example.",
        result_prefix="fmu.",
    )

    record = compare_csvs(request)

    assert [row.signal for row in read_metric_csv(record.metrics_csv)] == ["x"]
    assert record.summary.max_abs_error == pytest.approx(1.0)
