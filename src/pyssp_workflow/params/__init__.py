"""Read the study descriptor that points at standardized scenario artifacts.

The scenario SSV and SSM are the interchange artifacts. This module only reads
the repository-internal ``study.json`` that names them and carries the
experiment window. It never rewrites the SSV or SSM.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


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


__all__ = [
    "Experiment",
    "StudyDescriptor",
    "read_study_descriptor",
]
