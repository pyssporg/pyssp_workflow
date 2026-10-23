"""Read the study descriptor that points at standardized scenario artifacts.

The scenario SSV and SSM are the interchange artifacts. This module only reads
the repository-internal ``study.json`` that names them and carries the
experiment window. It never rewrites the SSV or SSM.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pyssp_standard import SSM, SSV


@dataclass(frozen=True)
class Experiment:
    name: str
    start_time: float
    stop_time: float
    step_size: float


@dataclass(frozen=True)
class StudyDescriptor:
    path: Path
    model: str
    composition: str
    sut: str
    target_ssd: str
    study: str
    model_source: str | None
    experiment: Experiment
    set_name: str | None
    ssv_path: Path | None
    ssm_path: Path | None
    description: str | None = None


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else base / candidate


def read_study_descriptor(path: Path | str) -> StudyDescriptor:
    descriptor_path = Path(path)
    data = json.loads(descriptor_path.read_text(encoding="utf-8"))
    experiment_data = data["experiment"]
    scenario = data.get("scenario")
    base = descriptor_path.parent
    if scenario is None:
        set_name: str | None = None
        ssv_path: Path | None = None
        ssm_path: Path | None = None
    else:
        set_name = str(scenario["set"])
        ssv_path = _resolve(base, str(scenario["ssv"]))
        ssm_path = _resolve(base, str(scenario["ssm"]))
    return StudyDescriptor(
        path=descriptor_path,
        model=str(data["model"]),
        composition=str(data["composition"]),
        sut=str(data["sut"]),
        target_ssd=str(data.get("target_ssd", "SystemStructure.ssd")),
        study=str(data["study"]),
        model_source=(
            str(data["model_source"])
            if data.get("model_source") is not None
            else None
        ),
        experiment=Experiment(
            name=str(experiment_data["name"]),
            start_time=float(experiment_data["start_time"]),
            stop_time=float(experiment_data["stop_time"]),
            step_size=float(experiment_data["step_size"]),
        ),
        set_name=set_name,
        ssv_path=ssv_path,
        ssm_path=ssm_path,
        description=(
            str(data["description"])
            if data.get("description") is not None
            else None
        ),
    )


def _require(path: Path | None, kind: str, descriptor: StudyDescriptor) -> Path:
    if path is None:
        raise ValueError(f"Study descriptor '{descriptor.path}' names no scenario {kind}")
    return path


def scenario_values(descriptor: StudyDescriptor) -> dict[str, float]:
    """The study scenario as ``{ssv member name: value}``.

    Read-only: the SSV is opened, never rewritten. Raises ``ValueError`` when
    the descriptor names no scenario SSV.
    """
    ssv_path = _require(descriptor.ssv_path, "SSV", descriptor)
    with SSV(ssv_path, mode="r") as ssv:
        return {
            parameter.name: float(parameter.attributes["value"])
            for parameter in ssv.xml.parameters
        }


def scenario_mappings(descriptor: StudyDescriptor) -> tuple[tuple[str, str], ...]:
    """The study ``(member name, target)`` mapping pairs.

    Read-only: the SSM is opened, never rewritten. Raises ``ValueError`` when
    the descriptor names no scenario SSM.
    """
    ssm_path = _require(descriptor.ssm_path, "SSM", descriptor)
    with SSM(ssm_path, mode="r") as ssm:
        return tuple(
            (mapping.source, mapping.target) for mapping in ssm.xml.mappings
        )


def scenario_targets(descriptor: StudyDescriptor) -> dict[str, float]:
    """The study scenario keyed by the mapped SSP target name.

    Read-only. Raises ``ValueError`` when the descriptor names no scenario
    SSV or SSM; ``KeyError`` when a mapping names a member the SSV lacks.
    """
    values = scenario_values(descriptor)
    return {target: values[source] for source, target in scenario_mappings(descriptor)}


__all__ = [
    "Experiment",
    "StudyDescriptor",
    "read_study_descriptor",
    "scenario_mappings",
    "scenario_targets",
    "scenario_values",
]
