from __future__ import annotations

import json
from pathlib import Path

import pytest
from pyssp_standard import SSD, SSM, SSV
from pyssp_standard.ssd import ParameterBinding, Ssd1Component, System

from pyssp_workflow.execute import (
    StudyBuild,
    apply_inline_components,
    package_external_target_named,
    package_inline_root,
    package_inline_with_mapping,
    package_nothing,
    package_scenario,
)
from pyssp_workflow.params import (
    read_study_descriptor,
    scenario_mappings,
    scenario_targets,
    scenario_values,
)


def _write_scenario(
    study_dir: Path,
    *,
    with_scenario: bool = True,
    model_source: str | None = None,
    values: dict[str, float] | None = None,
    mappings: tuple[tuple[str, str], ...] | None = None,
) -> Path:
    study_dir.mkdir()
    values = values or {"height": 2.0, "k": 3.0}
    mappings = mappings or (("height", "step.height"), ("k", "gain.k"))
    if with_scenario:
        with SSV(study_dir / "Scenario.ssv", mode="w") as ssv:
            ssv.xml.name = "Scenario"
            for name, value in values.items():
                ssv.xml.add_parameter(name, ptype="Real", value=value)
        with SSM(study_dir / "test_baseline.ssm", mode="w") as ssm:
            for source, target in mappings:
                ssm.xml.add_mapping(source, target)
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


def _write_model(model_dir: Path, *, nested: bool = False) -> None:
    model_dir.mkdir()
    elements: list[Ssd1Component | System] = []
    if nested:
        elements.append(Ssd1Component(name="step"))
        elements.append(
            System(
                name="inner",
                elements=[
                    Ssd1Component(name="gain"),
                    Ssd1Component(name="sine"),
                ],
            )
        )
    with SSD(model_dir / "SystemStructure.ssd", mode="w") as ssd:
        ssd.xml.system = System(name="System", elements=elements)


def _inline_values(binding: ParameterBinding) -> dict[str, str]:
    assert binding.parameter_set is not None
    return {
        parameter.name: parameter.attributes["value"]
        for parameter in binding.parameter_set.parameters
    }


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


def test_study_build_records_the_packaging_form(tmp_path: Path) -> None:
    build = StudyBuild("baseline", package_nothing)

    assert build.name == "baseline"
    assert build.package is package_nothing
    assert StudyBuild("baseline").package is None


def test_package_nothing_leaves_the_ssp_unchanged(tmp_path: Path) -> None:
    descriptor = _write_scenario(tmp_path / "study")
    study = read_study_descriptor(descriptor)
    model = tmp_path / "model"
    _write_model(model)
    before = (model / "SystemStructure.ssd").read_bytes()

    assert package_nothing(model, study) is None

    assert (model / "SystemStructure.ssd").read_bytes() == before
    assert not (model / "resources").exists()


def test_package_inline_root_writes_one_target_named_root_binding(
    tmp_path: Path,
) -> None:
    descriptor = _write_scenario(tmp_path / "study")
    study = read_study_descriptor(descriptor)
    model = tmp_path / "model"
    _write_model(model)

    package_inline_root(model, study)

    with SSD(model / "SystemStructure.ssd", mode="r") as ssd:
        bindings = ssd.xml.system.parameter_bindings
        assert len(bindings) == 1
        binding = bindings[0]
        assert binding.source is None
        assert _inline_values(binding) == {"step.height": "2.0", "gain.k": "3.0"}
    assert list((model / "resources").glob("*.ssv")) == []


def test_package_external_target_named_writes_an_ssv_without_mapping(
    tmp_path: Path,
) -> None:
    descriptor = _write_scenario(tmp_path / "study")
    study = read_study_descriptor(descriptor)
    model = tmp_path / "model"
    _write_model(model)

    package_external_target_named(model, study)

    ssv_path = model / "resources" / "Scenario.ssv"
    assert ssv_path.is_file()
    with SSD(model / "SystemStructure.ssd", mode="r") as ssd:
        bindings = ssd.xml.system.parameter_bindings
        assert len(bindings) == 1
        binding = bindings[0]
        assert binding.source == "resources/Scenario.ssv"
        assert binding.parameter_mapping is None
    with SSV(ssv_path, mode="r") as ssv:
        assert {
            parameter.name: parameter.attributes["value"]
            for parameter in ssv.xml.parameters
        } == {"step.height": "2.0", "gain.k": "3.0"}


def test_package_inline_with_mapping_adds_the_ssm_resource(
    tmp_path: Path,
) -> None:
    descriptor = _write_scenario(tmp_path / "study")
    study = read_study_descriptor(descriptor)
    model = tmp_path / "model"
    _write_model(model)

    package_inline_with_mapping(model, study)

    assert (model / "resources" / "test_baseline.ssm").is_file()
    with SSD(model / "SystemStructure.ssd", mode="r") as ssd:
        bindings = ssd.xml.system.parameter_bindings
        assert len(bindings) == 1
        binding = bindings[0]
        assert binding.source is None
        assert binding.parameter_mapping is not None
        assert binding.parameter_mapping.source == "resources/test_baseline.ssm"
        assert _inline_values(binding) == {"height": "2.0", "k": "3.0"}


def test_apply_inline_components_writes_per_component_sets(tmp_path: Path) -> None:
    descriptor = _write_scenario(
        tmp_path / "study",
        mappings=(
            ("height", "step.height"),
            ("k", "inner.gain.k"),
            ("amp", "inner.sine.amplitude"),
        ),
        values={"height": 2.0, "k": 3.0, "amp": 4.0},
    )
    study = read_study_descriptor(descriptor)
    model = tmp_path / "model"
    _write_model(model, nested=True)

    apply_inline_components(model, study)

    with SSD(model / "SystemStructure.ssd", mode="r") as ssd:
        root = ssd.xml.system
        step = next(element for element in root.elements if element.name == "step")
        inner = next(element for element in root.elements if element.name == "inner")
        gain = next(element for element in inner.elements if element.name == "gain")
        sine = next(element for element in inner.elements if element.name == "sine")
        assert [_inline_values(binding) for binding in step.parameter_bindings] == [
            {"height": "2.0"}
        ]
        assert [_inline_values(binding) for binding in gain.parameter_bindings] == [
            {"k": "3.0"}
        ]
        assert [_inline_values(binding) for binding in sine.parameter_bindings] == [
            {"amplitude": "4.0"}
        ]


def test_apply_inline_components_only_limits_the_components(tmp_path: Path) -> None:
    descriptor = _write_scenario(
        tmp_path / "study",
        mappings=(
            ("height", "step.height"),
            ("k", "inner.gain.k"),
        ),
    )
    study = read_study_descriptor(descriptor)
    model = tmp_path / "model"
    _write_model(model, nested=True)

    apply_inline_components(model, study, only={"step"})

    with SSD(model / "SystemStructure.ssd", mode="r") as ssd:
        root = ssd.xml.system
        step = next(element for element in root.elements if element.name == "step")
        inner = next(element for element in root.elements if element.name == "inner")
        assert step.parameter_bindings
        assert inner.parameter_bindings == []


def test_apply_inline_components_rejects_an_unknown_component(
    tmp_path: Path,
) -> None:
    descriptor = _write_scenario(
        tmp_path / "study",
        mappings=(("height", "missing.value"),),
    )
    study = read_study_descriptor(descriptor)
    model = tmp_path / "model"
    _write_model(model, nested=True)

    with pytest.raises(KeyError, match="missing"):
        apply_inline_components(model, study)


def test_scenario_readers_decode_the_standard_artifacts(tmp_path: Path) -> None:
    descriptor = _write_scenario(tmp_path / "study")
    study = read_study_descriptor(descriptor)

    assert scenario_values(study) == {"height": 2.0, "k": 3.0}
    assert scenario_mappings(study) == (
        ("height", "step.height"),
        ("k", "gain.k"),
    )
    assert scenario_targets(study) == {"step.height": 2.0, "gain.k": 3.0}


def test_scenario_readers_reject_a_descriptor_without_a_scenario(
    tmp_path: Path,
) -> None:
    descriptor = _write_scenario(tmp_path / "study", with_scenario=False)
    study = read_study_descriptor(descriptor)

    for reader in (scenario_values, scenario_mappings, scenario_targets):
        with pytest.raises(ValueError, match="names no scenario"):
            reader(study)
