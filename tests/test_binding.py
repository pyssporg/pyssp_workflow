from __future__ import annotations

import json
from pathlib import Path

import pytest
from pyssp_standard import SSD, SSM, SSV
from pyssp_standard.ssd import ParameterBinding, Ssd1Component, System

from pyssp_workflow.binding import (
    ExternalStudy,
    InlineComponents,
    InlineRoot,
    InlineWithMapping,
    TargetNamedExternal,
    apply_bindings,
)
from pyssp_workflow.fixture import BuiltFixture
from pyssp_workflow.study import read_study_descriptor


def _write_scenario(
    study_dir: Path,
    *,
    with_scenario: bool = True,
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


def _fixture_build(model_dir: Path, descriptor) -> BuiltFixture:
    return BuiltFixture(
        model_name="example",
        study=descriptor.study,
        study_dir=descriptor.path.parent,
        model_dir=model_dir,
        descriptor=descriptor,
    )


def _inline_values(binding: ParameterBinding) -> dict[str, str]:
    assert binding.parameter_set is not None
    return {
        parameter.name: parameter.attributes["value"]
        for parameter in binding.parameter_set.parameters
    }


def test_external_study_merges_standard_ssv_and_ssm(tmp_path: Path) -> None:
    descriptor = _write_scenario(tmp_path / "study")
    study = read_study_descriptor(descriptor)
    model = tmp_path / "model"
    _write_model(model)

    apply_bindings(_fixture_build(model, study), ExternalStudy())

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


def test_external_study_rejects_model_with_root_bindings(tmp_path: Path) -> None:
    descriptor = _write_scenario(tmp_path / "study")
    study = read_study_descriptor(descriptor)
    model = tmp_path / "model"
    _write_model(model)
    build = _fixture_build(model, study)

    apply_bindings(build, ExternalStudy())

    with pytest.raises(ValueError, match="already has root parameter bindings"):
        apply_bindings(build, ExternalStudy())


def test_apply_bindings_applies_each_binding_before_a_later_failure(
    tmp_path: Path,
) -> None:
    descriptor = _write_scenario(tmp_path / "study")
    study = read_study_descriptor(descriptor)
    model = tmp_path / "model"
    _write_model(model)

    with pytest.raises(ValueError, match="already has root parameter bindings"):
        apply_bindings(_fixture_build(model, study), ExternalStudy(), ExternalStudy())

    with SSD(model / "SystemStructure.ssd", mode="r") as ssd:
        assert len(ssd.xml.system.parameter_bindings) == 1


def test_external_study_rejects_a_descriptor_without_a_scenario(
    tmp_path: Path,
) -> None:
    descriptor = _write_scenario(tmp_path / "study", with_scenario=False)
    study = read_study_descriptor(descriptor)
    model = tmp_path / "model"
    _write_model(model)

    with pytest.raises(ValueError, match="names no scenario SSV"):
        apply_bindings(_fixture_build(model, study), ExternalStudy())


def test_inline_root_writes_one_target_named_root_binding(
    tmp_path: Path,
) -> None:
    descriptor = _write_scenario(tmp_path / "study")
    study = read_study_descriptor(descriptor)
    model = tmp_path / "model"
    _write_model(model)

    apply_bindings(_fixture_build(model, study), InlineRoot())

    with SSD(model / "SystemStructure.ssd", mode="r") as ssd:
        bindings = ssd.xml.system.parameter_bindings
        assert len(bindings) == 1
        binding = bindings[0]
        assert binding.source is None
        assert _inline_values(binding) == {"step.height": "2.0", "gain.k": "3.0"}
    assert list((model / "resources").glob("*.ssv")) == []


def test_target_named_external_writes_an_ssv_without_mapping(
    tmp_path: Path,
) -> None:
    descriptor = _write_scenario(tmp_path / "study")
    study = read_study_descriptor(descriptor)
    model = tmp_path / "model"
    _write_model(model)

    apply_bindings(_fixture_build(model, study), TargetNamedExternal())

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


def test_inline_with_mapping_adds_the_ssm_resource(
    tmp_path: Path,
) -> None:
    descriptor = _write_scenario(tmp_path / "study")
    study = read_study_descriptor(descriptor)
    model = tmp_path / "model"
    _write_model(model)

    apply_bindings(_fixture_build(model, study), InlineWithMapping())

    assert (model / "resources" / "test_baseline.ssm").is_file()
    with SSD(model / "SystemStructure.ssd", mode="r") as ssd:
        bindings = ssd.xml.system.parameter_bindings
        assert len(bindings) == 1
        binding = bindings[0]
        assert binding.source is None
        assert binding.parameter_mapping is not None
        assert binding.parameter_mapping.source == "resources/test_baseline.ssm"
        assert _inline_values(binding) == {"height": "2.0", "k": "3.0"}


def test_inline_components_writes_per_component_sets(tmp_path: Path) -> None:
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

    apply_bindings(_fixture_build(model, study), InlineComponents())

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


def test_inline_components_only_limits_the_components(tmp_path: Path) -> None:
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

    apply_bindings(
        _fixture_build(model, study),
        InlineComponents(only=frozenset({"step"})),
    )

    with SSD(model / "SystemStructure.ssd", mode="r") as ssd:
        root = ssd.xml.system
        step = next(element for element in root.elements if element.name == "step")
        inner = next(element for element in root.elements if element.name == "inner")
        assert step.parameter_bindings
        assert inner.parameter_bindings == []


def test_apply_bindings_applies_disjoint_component_bindings_in_order(
    tmp_path: Path,
) -> None:
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

    apply_bindings(
        _fixture_build(model, study),
        InlineComponents(only=frozenset({"step"})),
        InlineComponents(only=frozenset({"inner.gain"})),
    )

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
        assert sine.parameter_bindings == []


def test_inline_components_rejects_an_unknown_component(
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
        apply_bindings(_fixture_build(model, study), InlineComponents())
