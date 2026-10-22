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
    tolerance: float


@dataclass(frozen=True)
class StudyDescriptor:
    path: Path
    model: str
    composition: str
    sut: str
    target_ssd: str
    study: str
    experiment: Experiment
    set_name: str
    ssv_path: Path
    ssm_path: Path


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else base / candidate


def read_study_descriptor(path: Path | str) -> StudyDescriptor:
    descriptor_path = Path(path)
    data = json.loads(descriptor_path.read_text(encoding="utf-8"))
    experiment_data = data["experiment"]
    scenario = data["scenario"]
    base = descriptor_path.parent
    return StudyDescriptor(
        path=descriptor_path,
        model=str(data["model"]),
        composition=str(data["composition"]),
        sut=str(data["sut"]),
        target_ssd=str(data.get("target_ssd", "SystemStructure.ssd")),
        study=str(data["study"]),
        experiment=Experiment(
            name=str(experiment_data["name"]),
            start_time=float(experiment_data["start_time"]),
            stop_time=float(experiment_data["stop_time"]),
            step_size=float(experiment_data["step_size"]),
            tolerance=float(experiment_data["tolerance"]),
        ),
        set_name=str(scenario["set"]),
        ssv_path=_resolve(base, str(scenario["ssv"])),
        ssm_path=_resolve(base, str(scenario["ssm"])),
    )


__all__ = [
    "Experiment",
    "StudyDescriptor",
    "read_study_descriptor",
]
