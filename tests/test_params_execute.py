from __future__ import annotations

import json
from pathlib import Path

import pytest

from pyssp_standard import SSD, SSM, SSV
from pyssp_standard.ssd import ParameterBinding, System

from pyssp_workflow.execute import package_scenario
from pyssp_workflow.params import read_study_descriptor


def _write_scenario(
    study_dir: Path,
    *,
    with_scenario: bool = True,
    model_source: str | None = None,
) -> Path:
    study_dir.mkdir()
    if with_scenario:
        with SSV(study_dir / "Scenario.ssv", mode="w") as ssv:
            ssv.xml.name = "Scenario"
            ssv.xml.add_parameter("height", ptype="Real", value=2.0)
            ssv.xml.add_parameter("k", ptype="Real", value=3.0)
        with SSM(study_dir / "test_baseline.ssm", mode="w") as ssm:
            ssm.xml.add_mapping("height", "step.height")
            ssm.xml.add_mapping("k", "gain.k")
    descriptor = {
        "model": "example",
        "composition": "System",
        "sut": "sut",
        "target_ssd": "SystemStructure.ssd",
        "study": "test_baseline",
        "experiment": {
            "name": "baseline",
            "start_time": 0.0,
            "stop_time": 1.0,
            "step_size": 0.1,
        },
    }
    if with_scenario:
        descriptor["scenario"] = {
            "set": "Scenario",
            "ssv": "Scenario.ssv",
            "ssm": "test_baseline.ssm",
        }
    if model_source is not None:
        descriptor["model_source"] = model_source
    path = study_dir / "study.json"
    path.write_text(json.dumps(descriptor), encoding="utf-8")
    return path


def _write_model(model_dir: Path) -> None:
    model_dir.mkdir()
    with SSD(model_dir / "SystemStructure.ssd", mode="w") as ssd:
        system = System(name="System")
        ssd.xml.system = system


def test_read_study_descriptor_points_at_standard_artifacts(tmp_path: Path) -> None:
    descriptor = _write_scenario(tmp_path / "study")
    study = read_study_descriptor(descriptor)

    assert study.study == "test_baseline"
    assert study.target_ssd == "SystemStructure.ssd"
    assert study.ssv_path == descriptor.parent / "Scenario.ssv"
    assert study.ssm_path == descriptor.parent / "test_baseline.ssm"
    assert study.experiment.step_size == 0.1


def test_read_study_descriptor_without_scenario(tmp_path: Path) -> None:
    descriptor = _write_scenario(tmp_path / "study", with_scenario=False)
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
    descriptor = _write_scenario(
        tmp_path / "study",
        with_scenario=False,
        model_source="models/ssp/example/ssp",
    )
    study = read_study_descriptor(descriptor)

    assert study.model_source == "models/ssp/example/ssp"
    assert study.set_name is None


def test_package_scenario_merges_standard_ssv_and_ssm(tmp_path: Path) -> None:
    descriptor = _write_scenario(tmp_path / "study")
    study = read_study_descriptor(descriptor)
    model = tmp_path / "model"
    _write_model(model)

    result = package_scenario(
        model,
        study.ssv_path,
        study.ssm_path,
        target_ssd=study.target_ssd,
    )

    assert result == model
    assert (model / "resources" / "Scenario.ssv").is_file()
    assert (model / "resources" / "test_baseline.ssm").is_file()
    with SSD(model / "SystemStructure.ssd", mode="r") as ssd:
        bindings = ssd.xml.system.parameter_bindings
        assert len(bindings) == 1
        binding = bindings[0]
        assert isinstance(binding, ParameterBinding)
        assert binding.source == "resources/Scenario.ssv"
        assert binding.parameter_mapping is not None
        assert binding.parameter_mapping.source == "resources/test_baseline.ssm"
        assert binding.parameter_mapping.mapping is None
    with SSV(model / "resources" / "Scenario.ssv", mode="r") as ssv:
        assert {
            parameter.name: parameter.attributes["value"]
            for parameter in ssv.xml.parameters
        } == {"height": "2.0", "k": "3.0"}
    with SSM(model / "resources" / "test_baseline.ssm", mode="r") as ssm:
        assert [
            (mapping.source, mapping.target)
            for mapping in ssm.xml.mappings
        ] == [
            ("height", "step.height"),
            ("k", "gain.k"),
        ]


def test_package_scenario_rejects_model_with_root_bindings(tmp_path: Path) -> None:
    descriptor = _write_scenario(tmp_path / "study")
    study = read_study_descriptor(descriptor)
    model = tmp_path / "model"
    _write_model(model)

    package_scenario(model, study.ssv_path, study.ssm_path, target_ssd=study.target_ssd)

    with pytest.raises(ValueError, match="already has root parameter bindings"):
        package_scenario(
            model,
            study.ssv_path,
            study.ssm_path,
            target_ssd=study.target_ssd,
        )
