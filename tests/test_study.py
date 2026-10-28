from __future__ import annotations

from pathlib import Path

import pytest
from support import write_scenario

from pyssp_workflow.study import (
    Scenario,
    read_scenario,
    read_study_descriptor,
    scenario_targets,
)


def test_read_study_descriptor_points_at_standard_artifacts(tmp_path: Path) -> None:
    descriptor = write_scenario(tmp_path / "study")
    study = read_study_descriptor(descriptor)

    assert study.study == "test_baseline"
    assert study.target_ssd == "SystemStructure.ssd"
    assert study.ssv_path == descriptor.parent / "Scenario.ssv"
    assert study.ssm_path == descriptor.parent / "test_baseline.ssm"
    assert study.experiment.step_size == 0.1


def test_read_study_descriptor_without_scenario(tmp_path: Path) -> None:
    descriptor = write_scenario(tmp_path / "study", with_scenario=False)
    study = read_study_descriptor(descriptor)

    assert study.set_name is None
    assert study.ssv_path is None
    assert study.ssm_path is None
    assert study.model_source is None
    assert study.study == "test_baseline"
    assert study.experiment.name == "baseline"
    assert study.experiment.start_time == 0.0
    assert study.experiment.stop_time == 1.0
    assert study.experiment.step_size == 0.1


def test_read_study_descriptor_records_model_source(tmp_path: Path) -> None:
    descriptor = write_scenario(
        tmp_path / "study",
        with_scenario=False,
        model_source="models/ssp/example/ssp",
    )
    study = read_study_descriptor(descriptor)

    assert study.model_source == "models/ssp/example/ssp"
    assert study.set_name is None


def test_read_scenario_decodes_the_standard_artifacts(tmp_path: Path) -> None:
    descriptor = write_scenario(tmp_path / "study")
    study = read_study_descriptor(descriptor)

    scenario = read_scenario(study)

    assert scenario.set_name == "Scenario"
    assert scenario.ssv_path == descriptor.parent / "Scenario.ssv"
    assert scenario.ssm_path == descriptor.parent / "test_baseline.ssm"
    assert dict(scenario.values) == {"height": 2.0, "k": 3.0}
    assert scenario.mappings == (
        ("height", "step.height"),
        ("k", "gain.k"),
    )
    assert scenario_targets(scenario) == {"step.height": 2.0, "gain.k": 3.0}


def test_read_scenario_rejects_a_descriptor_without_a_scenario(
    tmp_path: Path,
) -> None:
    descriptor = write_scenario(tmp_path / "study", with_scenario=False)
    study = read_study_descriptor(descriptor)

    with pytest.raises(ValueError, match="names no scenario SSV"):
        read_scenario(study)


def test_scenario_targets_rejects_a_scenario_without_a_mapping(
    tmp_path: Path,
) -> None:
    scenario = Scenario(
        set_name="Scenario",
        ssv_path=tmp_path / "Scenario.ssv",
        ssm_path=None,
        values={"height": 2.0},
        mappings=(),
    )

    with pytest.raises(ValueError, match="names no scenario SSM"):
        scenario_targets(scenario)


def test_scenario_targets_rejects_a_mapping_the_ssv_lacks(tmp_path: Path) -> None:
    descriptor = write_scenario(
        tmp_path / "study",
        values={"height": 2.0},
        mappings=(("missing", "step.height"),),
    )
    study = read_study_descriptor(descriptor)

    with pytest.raises(KeyError, match="missing"):
        scenario_targets(read_scenario(study))
