"""Compare result CSVs.

``compare_result_csvs`` composes one comparison: it loads two result CSVs,
measures the candidate against the reference with ``pyssp_vv.measure``, writes
``<out_dir>/metrics.csv``, and returns a record. Thresholds, verdicts, manifests,
and artifact layout stay with the caller.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from pyssp_simulate import read_result_csv
from pyssp_vv.evidence import (
    ComparisonSummary,
    summarize_rows,
    write_metric_csv,
)
from pyssp_vv.measure import (
    Alignment,
    Grid,
    Trajectory,
    compare,
    local_shift_errors,
    metric_rows,
)


@dataclass(frozen=True)
class ResultRef:
    """One result CSV, addressed by path and labelled for the metric table."""

    result_csv: Path
    label: str


@dataclass(frozen=True)
class ComparisonRequest:
    """Measure one candidate CSV against one reference CSV."""

    reference: ResultRef
    candidate: ResultRef
    out_dir: Path
    signals: tuple[str, ...]
    start_time: float
    stop_time: float
    step_size: float
    root_system: str | tuple[str, ...] | None = None
    reference_prefix: str | None = None
    result_prefix: str | None = None
    shift_samples: int = 0
    edge_samples: int = 0
    max_gap_samples: int | None = 0
    normalisation: str = "reference_peak"


@dataclass(frozen=True)
class ComparisonRecord:
    """The outcome of measuring one pair, addressed by paths and plain data.

    There is no gate field: whether the measured difference is acceptable is
    the caller's policy, not this layer's.
    """

    reference_label: str
    candidate_label: str
    metrics_csv: Path
    summary: ComparisonSummary
    status: str = "completed"
    error: str | None = None

    def to_dict(self, base_dir: Path | str) -> dict[str, object]:
        """Plain data; ``metrics`` is relative to ``base_dir``."""
        return {
            "reference_label": self.reference_label,
            "candidate_label": self.candidate_label,
            "metrics": Path(os.path.relpath(self.metrics_csv, start=base_dir)).as_posix(),
            "summary": self.summary.to_dict(),
            "status": self.status,
            "error": self.error,
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, object], *, base_dir: Path | str
    ) -> ComparisonRecord:
        """Rebuild the record, resolving ``metrics`` against ``base_dir``."""
        metrics_csv = Path(str(data["metrics"]))
        if not metrics_csv.is_absolute():
            metrics_csv = Path(base_dir) / metrics_csv
        summary = data["summary"]
        if not isinstance(summary, Mapping):
            raise ValueError("ComparisonRecord summary must be a mapping")
        error = data.get("error")
        return cls(
            reference_label=str(data["reference_label"]),
            candidate_label=str(data["candidate_label"]),
            metrics_csv=metrics_csv,
            summary=ComparisonSummary.from_dict(summary),
            status=str(data.get("status", "completed")),
            error=None if error is None else str(error),
        )


def _trajectory(data, *, label: str) -> Trajectory:
    """Wrap one structured result array; signal selection stays in ``measure``."""
    columns = {name: data[name] for name in data.dtype.names or ()}
    if "time" not in columns:
        raise KeyError("Both result sets must contain a time column")
    return Trajectory(
        time=columns["time"],
        channels={name: values for name, values in columns.items() if name != "time"},
        label=label,
    )


def compare_result_csvs(request: ComparisonRequest) -> ComparisonRecord:
    """Measure ``request.candidate`` against ``request.reference``.

    Reads both CSVs with ``pyssp_simulate.read_result_csv`` (root system and
    prefixes from the request), measures with ``pyssp_vv.measure``, writes
    ``<out_dir>/metrics.csv`` and returns the record. Creates ``out_dir``. The
    request declares the comparison window, so an invalid window raises
    ``ValueError`` from ``pyssp_vv.measure.Grid`` and a signal a CSV lacks
    raises ``KeyError`` from ``pyssp_vv.measure.compare``. No manifest is
    written and no verdict is produced: the caller owns both.
    """
    reference = _trajectory(
        read_result_csv(
            request.reference.result_csv,
            request.root_system,
            prefix=request.reference_prefix,
        ),
        label=request.reference.label,
    )
    candidate = _trajectory(
        read_result_csv(
            request.candidate.result_csv,
            request.root_system,
            prefix=request.result_prefix,
        ),
        label=request.candidate.label,
    )
    alignment = Alignment(
        grid=Grid(
            start_time=request.start_time,
            stop_time=request.stop_time,
            step_size=request.step_size,
        ),
        shift_samples=request.shift_samples,
        max_gap_samples=request.max_gap_samples,
    )
    comparison = compare(
        reference,
        candidate,
        signals=request.signals,
        alignment=alignment,
        normalisation=request.normalisation,
    )
    rows = metric_rows(
        comparison,
        max_shift_abs_error=local_shift_errors(
            reference,
            candidate,
            alignment=alignment,
            edge_samples=request.edge_samples,
        ),
    )
    out_dir = Path(request.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    return ComparisonRecord(
        reference_label=comparison.reference_label,
        candidate_label=comparison.candidate_label,
        metrics_csv=write_metric_csv(out_dir / "metrics.csv", rows),
        summary=summarize_rows(
            rows, time_points=int(alignment.target(reference.time).size)
        ),
    )


__all__ = [
    "ComparisonRecord",
    "ComparisonRequest",
    "ResultRef",
    "compare_result_csvs",
]
