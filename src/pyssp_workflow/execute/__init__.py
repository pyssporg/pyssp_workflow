"""Package a study scenario into an exported SSP, and compare result CSVs.

The study SSV and SSM are the standardized interchange artifacts. Packaging
copies them into the exported SSP and adds one root-level parameter binding, so
the build output is a self-contained, runnable SSP. The scenario SSV and SSM
are never rewritten.

``package_scenario`` is the external SSV+SSM form that a study descriptor names.
The other forms are the remaining SSP parameter-binding shapes a fixture may
choose: no scenario, one inline root set, an external SSV keyed by the mapped
target names, an inline set with an external SSM resource, and per-component
inline sets. Every form mutates through ``pyssp_standard``; this module only
decides which binding gets written.

``compare_result_csvs`` composes one comparison: it loads two result CSVs,
measures the candidate against the reference with ``pyssp_vv.measure``, writes
``<out_dir>/metrics.csv``, and returns a record. Thresholds, verdicts, manifests,
and artifact layout stay with the caller.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from pyssp_simulate import read_result_csv
from pyssp_standard import SSP, SSV, ParameterMappingReference
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

from pyssp_workflow.params import (
    StudyDescriptor,
    scenario_targets,
    scenario_values,
)

#: A packaging form: apply a study descriptor to an exported SSP root in place.
PackageStep = Callable[[Path, StudyDescriptor], None]


@dataclass(frozen=True)
class StudyBuild:
    """One study to build, with the fixture's packaging form.

    ``package=None`` uses the default external SSV+SSM packaging. A study with
    no scenario passes ``package_nothing``.
    """

    name: str
    package: PackageStep | None = None


def package_scenario(
    exported_ssp_root: Path | str,
    scenario_ssv: Path | str,
    scenario_ssm: Path | str | None = None,
    *,
    target_ssd: str = "SystemStructure.ssd",
) -> Path:
    """Package the standard SSV/SSM into the exported SSP as one root binding.

    Returns the SSP root. The exported SSP is the artifact being produced, not
    an input; it is modified in place. Callers that need a copy make one first.
    """
    root = Path(exported_ssp_root)
    ssv_path = Path(scenario_ssv)
    ssm_path = Path(scenario_ssm) if scenario_ssm is not None else None
    if not root.is_dir():
        raise NotADirectoryError(f"Exported SSP root is not a directory: {root}")
    if target_ssd != "SystemStructure.ssd":
        raise ValueError(
            "pyssp_standard.SSP.add_external_parameterset targets "
            f"SystemStructure.ssd, not '{target_ssd}'"
        )

    with SSP(root, mode="a") as ssp:
        with ssp.system_structure() as ssd:
            system = ssd.xml.system
            if system is None:
                raise ValueError(f"Runtime SSD has no system: {ssd.path}")
            if system.parameter_bindings:
                raise ValueError(
                    f"Exported SSP already has root parameter bindings: {ssd.path}"
                )

        ssp.add_external_parameterset(
            ssv_path,
            mapping_path=ssm_path,
            resource_name=ssv_path.name,
            mapping_resource_name=ssm_path.name if ssm_path is not None else None,
        )

    return root


def package_nothing(
    exported_ssp_root: Path | str, descriptor: StudyDescriptor
) -> None:
    """Leave the exported SSP as-is; the fixture applies no study scenario.

    The exported SSP is the artifact being produced, not an input.
    """
    return None


def package_inline_root(
    exported_ssp_root: Path | str, descriptor: StudyDescriptor
) -> None:
    """Apply the scenario as one inline root parameter set keyed by target name.

    The exported SSP is the artifact being produced, not an input; it is
    modified in place. Raises ``ValueError`` when the descriptor names no
    scenario.
    """
    values = scenario_targets(descriptor)
    with SSP(Path(exported_ssp_root), mode="a") as ssp:
        with ssp.system_structure() as ssd:
            ssd.extend_system_parameterset(values, binding_name=descriptor.set_name)


def package_external_target_named(
    exported_ssp_root: Path | str, descriptor: StudyDescriptor
) -> None:
    """Apply the scenario as an external SSV whose names are the SSP targets.

    This is the no-mapping form: the parameter names are the hierarchical
    targets, so the binding needs no ``.ssm``. The exported SSP is the artifact
    being produced, not an input; it is modified in place. Raises
    ``ValueError`` when the descriptor names no scenario.
    """
    values = scenario_targets(descriptor)
    with tempfile.TemporaryDirectory(prefix=f"{descriptor.set_name}_") as temp_dir:
        ssv_path = Path(temp_dir) / f"{descriptor.set_name}.ssv"
        with SSV(ssv_path, mode="w") as ssv:
            ssv.xml.name = descriptor.set_name
            for name, value in values.items():
                ssv.xml.add_parameter(parname=name, ptype="Real", value=value)
        with SSP(Path(exported_ssp_root), mode="a") as ssp:
            ssp.add_external_parameterset(ssv_path)


def _resolve_system(root_system, path_parts: list[str]):
    system = root_system
    for name in path_parts:
        element = next(
            (candidate for candidate in system.elements if candidate.name == name),
            None,
        )
        if element is None:
            raise KeyError(f"No element '{name}' under '{system.name}'")
        system = element
    return system


def apply_inline_components(
    exported_ssp_root: Path | str,
    descriptor: StudyDescriptor,
    *,
    only: set[str] | None = None,
) -> None:
    """Apply the scenario as inline parameter sets on the mapped components.

    Each mapped target is ``<component path>.<parameter>``; the component path
    may cross nested systems. ``only`` limits application to the given
    component paths. The exported SSP is the artifact being produced, not an
    input; it is modified in place. Raises ``ValueError`` when the descriptor
    names no scenario and ``KeyError`` for a component path the SSP does not
    contain.
    """
    targets = scenario_targets(descriptor)
    with SSP(Path(exported_ssp_root), mode="a") as ssp:
        with ssp.system_structure() as ssd:
            root = ssd.xml.system
            for target, value in targets.items():
                *component_path, parameter = target.split(".")
                component_name = ".".join(component_path)
                if only is not None and component_name not in only:
                    continue
                component = _resolve_system(root, component_path)
                component.extend_inline_parameterset({parameter: value})


def package_inline_with_mapping(
    exported_ssp_root: Path | str, descriptor: StudyDescriptor
) -> None:
    """Apply the scenario inline, with an external SSM resource for the mapping.

    The exported SSP is the artifact being produced, not an input; it is
    modified in place. Raises ``ValueError`` when the descriptor names no
    scenario or no SSM.
    """
    values = scenario_values(descriptor)
    if descriptor.ssm_path is None:
        raise ValueError(
            f"Study descriptor '{descriptor.path}' names no scenario SSM"
        )
    mapping_name = descriptor.ssm_path.name
    with SSP(Path(exported_ssp_root), mode="a") as ssp:
        with ssp.system_structure() as ssd:
            ssd.extend_system_parameterset(values, binding_name=descriptor.set_name)
            binding = next(
                candidate
                for candidate in ssd.xml.system.parameter_bindings
                if candidate.source is None and candidate.parameter_set is not None
            )
            binding.parameter_mapping = ParameterMappingReference(
                source=f"resources/{mapping_name}"
            )
        ssp.add_resource(descriptor.ssm_path)


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
    "PackageStep",
    "ResultRef",
    "StudyBuild",
    "apply_inline_components",
    "compare_result_csvs",
    "package_external_target_named",
    "package_inline_root",
    "package_inline_with_mapping",
    "package_nothing",
    "package_scenario",
]
