from __future__ import annotations

from pathlib import Path

import pytest
from pyssp_standard import SSD, SSM, SSV, ParameterBinding
from support import write_scenario

from pyssp_workflow.analysis import AnalysisDescriptor, read_analysis_descriptor
from pyssp_workflow.binding import bind
from pyssp_workflow.fixture import BuiltFixture


def _write_model(model_dir: Path, *, nested: bool = False) -> None:
    model_dir.mkdir()
    with SSD(model_dir / "SystemStructure.ssd", mode="w") as ssd:
        root = ssd.new_system("System")
        root.add_component("step")
        if nested:
            inner = root.add_subsystem("inner")
            inner.add_component("gain")
            inner.add_component("sine")


def _fixture_build(model_dir: Path, descriptor: AnalysisDescriptor) -> BuiltFixture:
    return BuiltFixture(
        model_name="example",
        analysis=descriptor.analysis,
        analysis_dir=descriptor.path.parent,
        model_dir=model_dir,
        descriptor=descriptor,
    )


def _analysis(
    tmp_path: Path,
    **scenario_kwargs,
) -> tuple[AnalysisDescriptor, Path, Path]:
    descriptor = write_scenario(tmp_path / "analysis", **scenario_kwargs)
    analysis = read_analysis_descriptor(descriptor)
    assert analysis.ssv_path is not None
    assert analysis.ssm_path is not None
    return analysis, analysis.ssv_path, analysis.ssm_path


def _inline_values(binding: ParameterBinding) -> dict[str, str]:
    assert binding.parameter_set is not None
    return {
        parameter.name: parameter.attributes["value"]
        for parameter in binding.parameter_set.parameters
    }


def _inline_types(binding: ParameterBinding) -> dict[str, str]:
    assert binding.parameter_set is not None
    return {
        parameter.name: parameter.type_name
        for parameter in binding.parameter_set.parameters
    }


def _root_values(model_dir: Path) -> dict[str, str]:
    with SSD(model_dir / "SystemStructure.ssd", mode="r") as ssd:
        bindings = ssd.system.parameter_bindings
        assert len(bindings) == 1
        return _inline_values(bindings[0])


def test_external_attach_copies_the_ssv_and_ssm_and_maps_them(
    tmp_path: Path,
) -> None:
    analysis, ssv, ssm = _analysis(tmp_path)
    model = tmp_path / "model"
    _write_model(model)

    result = bind(_fixture_build(model, analysis), ssv, ssm=ssm)

    assert result.ssp == model
    assert result.mode == "external"
    assert result.mapping == "attach"
    assert result.parameter_set == "Scenario"
    assert result.ssv_resource == "Scenario.ssv"
    assert result.ssm_resource == "test_baseline.ssm"
    assert result.components == ()
    assert result.parameters == 2
    assert (model / "resources" / "Scenario.ssv").is_file()
    assert (model / "resources" / "test_baseline.ssm").is_file()
    with SSD(model / "SystemStructure.ssd", mode="r") as ssd:
        bindings = ssd.system.parameter_bindings
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


def test_external_attach_without_ssm_leaves_the_mapping_unset(
    tmp_path: Path,
) -> None:
    analysis, ssv, _ = _analysis(tmp_path)
    model = tmp_path / "model"
    _write_model(model)

    result = bind(_fixture_build(model, analysis), ssv)

    assert result.ssv_resource == "Scenario.ssv"
    assert result.ssm_resource is None
    assert result.parameters == 2
    assert (model / "resources" / "Scenario.ssv").is_file()
    assert list((model / "resources").glob("*.ssm")) == []
    with SSD(model / "SystemStructure.ssd", mode="r") as ssd:
        bindings = ssd.system.parameter_bindings
        assert len(bindings) == 1
        assert bindings[0].source == "resources/Scenario.ssv"
        assert bindings[0].parameter_mapping is None


def test_external_flatten_writes_a_target_named_ssv(tmp_path: Path) -> None:
    analysis, ssv, ssm = _analysis(tmp_path)
    model = tmp_path / "model"
    _write_model(model)

    result = bind(
        _fixture_build(model, analysis),
        ssv,
        ssm=ssm,
        mapping="flatten",
    )

    assert result.mode == "external"
    assert result.mapping == "flatten"
    assert result.parameter_set == "Scenario"
    assert result.ssv_resource == "Scenario.ssv"
    assert result.ssm_resource is None
    assert result.components == ()
    assert result.parameters == 2
    assert list((model / "resources").glob("*.ssm")) == []
    with SSD(model / "SystemStructure.ssd", mode="r") as ssd:
        bindings = ssd.system.parameter_bindings
        assert len(bindings) == 1
        assert bindings[0].source == "resources/Scenario.ssv"
        assert bindings[0].parameter_mapping is None
    with SSV(model / "resources" / "Scenario.ssv", mode="r") as generated:
        assert generated.xml.name == "Scenario"
        assert {
            parameter.name: parameter.attributes["value"]
            for parameter in generated.xml.parameters
        } == {"step.height": "2.0", "gain.k": "3.0"}


def test_external_flatten_uses_the_ssv_name_by_default(tmp_path: Path) -> None:
    analysis, ssv, ssm = _analysis(tmp_path)
    model = tmp_path / "model"
    _write_model(model)

    result = bind(
        _fixture_build(model, analysis),
        ssv,
        ssm=ssm,
        mapping="flatten",
    )

    assert result.parameter_set == "Scenario"
    assert result.ssv_resource == "Scenario.ssv"


def test_external_flatten_honours_an_explicit_set_name(tmp_path: Path) -> None:
    analysis, ssv, ssm = _analysis(tmp_path)
    model = tmp_path / "model"
    _write_model(model)

    result = bind(
        _fixture_build(model, analysis),
        ssv,
        ssm=ssm,
        set_name="Calibration",
        mapping="flatten",
    )

    assert result.parameter_set == "Calibration"
    assert result.ssv_resource == "Calibration.ssv"
    assert (model / "resources" / "Calibration.ssv").is_file()
    with SSV(model / "resources" / "Calibration.ssv", mode="r") as generated:
        assert generated.xml.name == "Calibration"


def test_inline_attach_writes_member_named_values(tmp_path: Path) -> None:
    analysis, ssv, ssm = _analysis(tmp_path)
    model = tmp_path / "model"
    _write_model(model)

    result = bind(
        _fixture_build(model, analysis),
        ssv,
        mode="inline",
        ssm=ssm,
    )

    assert result.mode == "inline"
    assert result.mapping == "attach"
    assert result.parameter_set == "Scenario"
    assert result.ssv_resource is None
    assert result.ssm_resource == "test_baseline.ssm"
    assert result.components == ()
    assert result.parameters == 2
    assert (model / "resources" / "test_baseline.ssm").is_file()
    with SSD(model / "SystemStructure.ssd", mode="r") as ssd:
        bindings = ssd.system.parameter_bindings
        assert len(bindings) == 1
        binding = bindings[0]
        assert binding.source is None
        assert binding.parameter_mapping is not None
        assert binding.parameter_mapping.source == "resources/test_baseline.ssm"
        assert _inline_values(binding) == {"height": "2.0", "k": "3.0"}


def test_inline_attach_requires_an_ssm(tmp_path: Path) -> None:
    analysis, ssv, _ = _analysis(tmp_path)
    model = tmp_path / "model"
    _write_model(model)

    with pytest.raises(ValueError, match="names no scenario SSM"):
        bind(_fixture_build(model, analysis), ssv, mode="inline")


def test_inline_flatten_writes_a_target_named_root_set(tmp_path: Path) -> None:
    analysis, ssv, ssm = _analysis(tmp_path)
    model = tmp_path / "model"
    _write_model(model)

    result = bind(
        _fixture_build(model, analysis),
        ssv,
        mode="inline",
        ssm=ssm,
        mapping="flatten",
    )

    assert result.mode == "inline"
    assert result.mapping == "flatten"
    assert result.parameter_set == "Scenario"
    assert result.ssv_resource is None
    assert result.ssm_resource is None
    assert result.components == ()
    assert result.parameters == 2
    assert not (model / "resources" / "test_baseline.ssm").exists()
    assert _root_values(model) == {"step.height": "2.0", "gain.k": "3.0"}


def test_attach_keeps_member_names_while_flatten_uses_target_names(
    tmp_path: Path,
) -> None:
    analysis, ssv, ssm = _analysis(tmp_path)
    attached = tmp_path / "attached"
    _write_model(attached)
    flattened = tmp_path / "flattened"
    _write_model(flattened)

    bind(_fixture_build(attached, analysis), ssv, mode="inline", ssm=ssm)
    bind(
        _fixture_build(flattened, analysis),
        ssv,
        mode="inline",
        ssm=ssm,
        mapping="flatten",
    )

    assert _root_values(attached) == {"height": "2.0", "k": "3.0"}
    assert _root_values(flattened) == {"step.height": "2.0", "gain.k": "3.0"}


def test_inline_flatten_components_writes_only_listed_components(
    tmp_path: Path,
) -> None:
    analysis, ssv, ssm = _analysis(
        tmp_path,
        mappings=(
            ("height", "step.height"),
            ("k", "inner.gain.k"),
            ("amp", "inner.sine.amplitude"),
        ),
        values={"height": 2.0, "k": 3.0, "amp": 4.0},
    )
    model = tmp_path / "model"
    _write_model(model, nested=True)

    result = bind(
        _fixture_build(model, analysis),
        ssv,
        mode="inline",
        ssm=ssm,
        mapping="flatten",
        components=frozenset({"step", "inner.gain"}),
    )

    assert result.parameter_set == "Scenario"
    assert result.components == ("inner.gain", "step")
    assert result.parameters == 2
    with SSD(model / "SystemStructure.ssd", mode="r") as ssd:
        root = ssd.system
        step = next(element for element in root.elements if element.name == "step")
        inner = next(element for element in root.elements if element.name == "inner")
        gain = next(element for element in inner.elements if element.name == "gain")
        sine = next(element for element in inner.elements if element.name == "sine")
        assert root.parameter_bindings == []
        assert [_inline_values(binding) for binding in step.parameter_bindings] == [
            {"height": "2.0"}
        ]
        assert [_inline_values(binding) for binding in gain.parameter_bindings] == [
            {"k": "3.0"}
        ]
        assert sine.parameter_bindings == []


def test_inline_flatten_components_rejects_an_unknown_component(
    tmp_path: Path,
) -> None:
    analysis, ssv, ssm = _analysis(
        tmp_path,
        mappings=(("height", "missing.value"),),
    )
    model = tmp_path / "model"
    _write_model(model, nested=True)

    with pytest.raises(KeyError, match="missing"):
        bind(
            _fixture_build(model, analysis),
            ssv,
            mode="inline",
            ssm=ssm,
            mapping="flatten",
            components=frozenset({"missing"}),
        )


def test_components_are_rejected_with_external_mode(tmp_path: Path) -> None:
    analysis, ssv, ssm = _analysis(tmp_path)
    model = tmp_path / "model"
    _write_model(model)

    with pytest.raises(ValueError, match="only valid with mode='inline'"):
        bind(
            _fixture_build(model, analysis),
            ssv,
            ssm=ssm,
            mapping="flatten",
            components=frozenset({"step"}),
        )


def test_components_are_rejected_with_attach(tmp_path: Path) -> None:
    analysis, ssv, ssm = _analysis(tmp_path)
    model = tmp_path / "model"
    _write_model(model)

    with pytest.raises(ValueError, match="only valid with mapping='flatten'"):
        bind(
            _fixture_build(model, analysis),
            ssv,
            mode="inline",
            ssm=ssm,
            components=frozenset({"step"}),
        )


def test_external_attach_rejects_a_non_system_structure_target(
    tmp_path: Path,
) -> None:
    analysis, ssv, ssm = _analysis(tmp_path, target_ssd="ModelStructure.ssd")
    model = tmp_path / "model"
    _write_model(model)

    with pytest.raises(ValueError, match="SystemStructure.ssd"):
        bind(_fixture_build(model, analysis), ssv, ssm=ssm)


def test_external_attach_rejects_a_model_with_root_bindings(
    tmp_path: Path,
) -> None:
    analysis, ssv, ssm = _analysis(tmp_path)
    model = tmp_path / "model"
    _write_model(model)
    build = _fixture_build(model, analysis)

    bind(build, ssv, ssm=ssm)

    with pytest.raises(ValueError, match="already has root parameter bindings"):
        bind(build, ssv, ssm=ssm)


def test_external_attach_requires_an_exported_ssp_root(tmp_path: Path) -> None:
    analysis, ssv, ssm = _analysis(tmp_path)
    build = _fixture_build(tmp_path / "missing", analysis)

    with pytest.raises(NotADirectoryError, match="not a directory"):
        bind(build, ssv, ssm=ssm)


def test_a_mapping_must_name_a_member_the_ssv_has(tmp_path: Path) -> None:
    analysis, ssv, ssm = _analysis(
        tmp_path,
        mappings=(("unknown", "step.height"),),
    )
    model = tmp_path / "model"
    _write_model(model)

    with pytest.raises(KeyError, match="unknown"):
        bind(
            _fixture_build(model, analysis),
            ssv,
            ssm=ssm,
            mapping="flatten",
        )


def test_flatten_and_inline_attach_preserve_typed_parameters(
    tmp_path: Path,
) -> None:
    analysis, ssv, ssm = _analysis(
        tmp_path,
        values={"enabled": True, "count": 3},
        value_types={"enabled": "Boolean", "count": "Integer"},
        mappings=(("enabled", "step.enabled"), ("count", "inner.gain.count")),
    )

    external = tmp_path / "external"
    _write_model(external, nested=True)
    bind(_fixture_build(external, analysis), ssv, ssm=ssm, mapping="flatten")
    with SSV(external / "resources" / "Scenario.ssv", mode="r") as generated:
        assert {
            parameter.name: parameter.type_name
            for parameter in generated.xml.parameters
        } == {"step.enabled": "Boolean", "inner.gain.count": "Integer"}

    inline = tmp_path / "inline"
    _write_model(inline, nested=True)
    bind(
        _fixture_build(inline, analysis),
        ssv,
        mode="inline",
        ssm=ssm,
        mapping="flatten",
    )
    with SSD(inline / "SystemStructure.ssd", mode="r") as ssd:
        assert _inline_types(ssd.system.parameter_bindings[0]) == {
            "step.enabled": "Boolean",
            "inner.gain.count": "Integer",
        }

    per_component = tmp_path / "per_component"
    _write_model(per_component, nested=True)
    bind(
        _fixture_build(per_component, analysis),
        ssv,
        mode="inline",
        ssm=ssm,
        mapping="flatten",
        components=frozenset({"step", "inner.gain"}),
    )
    with SSD(per_component / "SystemStructure.ssd", mode="r") as ssd:
        root = ssd.system
        step = next(element for element in root.elements if element.name == "step")
        inner = next(element for element in root.elements if element.name == "inner")
        gain = next(element for element in inner.elements if element.name == "gain")
        assert _inline_types(step.parameter_bindings[0]) == {
            "enabled": "Boolean"
        }
        assert _inline_types(gain.parameter_bindings[0]) == {"count": "Integer"}

    attached = tmp_path / "attached"
    _write_model(attached)
    bind(_fixture_build(attached, analysis), ssv, mode="inline", ssm=ssm)
    with SSD(attached / "SystemStructure.ssd", mode="r") as ssd:
        assert _inline_types(ssd.system.parameter_bindings[0]) == {
            "enabled": "Boolean",
            "count": "Integer",
        }


def test_inline_attach_rejects_a_non_system_structure_target(
    tmp_path: Path,
) -> None:
    analysis, ssv, ssm = _analysis(tmp_path, target_ssd="ModelStructure.ssd")
    model = tmp_path / "model"
    _write_model(model)

    with pytest.raises(ValueError, match="SystemStructure.ssd"):
        bind(_fixture_build(model, analysis), ssv, mode="inline", ssm=ssm)


def test_bind_surfaces_a_resource_collision(tmp_path: Path) -> None:
    analysis, ssv, ssm = _analysis(tmp_path)
    model = tmp_path / "model"
    _write_model(model)
    resources = model / "resources"
    resources.mkdir()
    (resources / "Scenario.ssv").write_text("different bytes", encoding="utf-8")

    with pytest.raises(FileExistsError, match="Scenario.ssv"):
        bind(_fixture_build(model, analysis), ssv, ssm=ssm)
