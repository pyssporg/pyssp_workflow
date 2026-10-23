from __future__ import annotations

import json
import shutil
from pathlib import Path
from zipfile import ZipFile

import pytest
from pyssp_standard import SSD, SSM, SSV
from pyssp_standard.ssd import Ssd1Component, System

from pyssp_workflow import authoring
from pyssp_workflow.authoring import (
    build_fixture,
    build_fmu_from_modelica,
    build_legacy_model,
    build_studies,
    run_fixture,
)
from pyssp_workflow.execute import package_nothing

OMC = shutil.which("omc")


def _write_study_artifacts(study_dir: Path) -> None:
    study_dir.mkdir(parents=True, exist_ok=True)
    with SSV(study_dir / "Scenario.ssv", mode="w") as ssv:
        ssv.xml.name = "Scenario"
        ssv.xml.add_parameter("height", ptype="Real", value=2.0)
    with SSM(study_dir / "test_baseline.ssm", mode="w") as ssm:
        ssm.xml.add_mapping("height", "step.height")
    (study_dir / "study.json").write_text(
        json.dumps(
            {
                "model": "demo",
                "composition": "System",
                "sut": "sut",
                "study": "test_baseline",
                "experiment": {
                    "name": "baseline",
                    "start_time": 0.0,
                    "stop_time": 1.0,
                    "step_size": 0.1,
                },
                "scenario": {
                    "set": "Scenario",
                    "ssv": "Scenario.ssv",
                    "ssm": "test_baseline.ssm",
                },
            }
        ),
        encoding="utf-8",
    )


def _write_ssp_archive(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.parent / "staging"
    staging.mkdir()
    with SSD(staging / "SystemStructure.ssd", mode="w") as ssd:
        ssd.xml.system = System(
            name="System", elements=[Ssd1Component(name="step")]
        )
    with ZipFile(path, "w") as archive:
        archive.write(staging / "SystemStructure.ssd", "SystemStructure.ssd")


def _stub_derivations(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[str],
    studies_seen: list[str] | None = None,
) -> None:
    def fake_study(
        architecture_path,
        output_dir,
        composition,
        *,
        model_name,
        pyssp=None,
        target_ssd="SystemStructure.ssd",
        timeout=authoring.DEFAULT_TIMEOUT_SECONDS,
    ):
        calls.append("study")
        assert Path(architecture_path).is_dir()
        assert model_name == "demo"
        if studies_seen is not None:
            studies_seen.append(composition)
        _write_study_artifacts(Path(output_dir))
        return Path(output_dir) / "study.json"

    def fake_ssp(
        architecture_path,
        output_path,
        composition,
        *,
        pyssp=None,
        fmu_root=None,
        parameter_set_prefix="resources/parameter_sets",
        validate_fmus=True,
        allow_missing_fmus=False,
        type_check=True,
        timeout=authoring.DEFAULT_TIMEOUT_SECONDS,
    ):
        calls.append("model")
        assert Path(architecture_path).is_dir()
        assert composition == "System"
        _write_ssp_archive(Path(output_path))
        return Path(output_path)

    monkeypatch.setattr(authoring, "derive_study_from_sysml", fake_study)
    monkeypatch.setattr(authoring, "derive_ssp_from_sysml", fake_ssp)


def _fixture_dir(tmp_path: Path) -> Path:
    model_dir = tmp_path / "models" / "ssp" / "demo"
    (model_dir / "architecture").mkdir(parents=True)
    return model_dir


def test_build_fixture_runs_study_then_model_then_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    studies_seen: list[str] = []
    _stub_derivations(monkeypatch, calls, studies_seen)
    model_dir = _fixture_dir(tmp_path)

    def package(model_build_dir, descriptor) -> None:
        calls.append("package")
        assert Path(model_build_dir).is_dir()
        assert descriptor.study == "test_baseline"

    output = build_fixture(
        model_dir=model_dir,
        repo_root=tmp_path,
        model_name="demo",
        composition="System",
        study="test_baseline",
        package=package,
    )

    assert calls == ["study", "model", "package"]
    assert studies_seen == ["test_baseline"]
    assert output == (
        tmp_path
        / "artifacts"
        / "models"
        / "demo"
        / "test_baseline"
        / "model"
    )


def test_build_fixture_uses_package_scenario_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_derivations(monkeypatch, [])
    model_dir = _fixture_dir(tmp_path)

    output = build_fixture(
        model_dir=model_dir,
        repo_root=tmp_path,
        model_name="demo",
        composition="System",
        study="test_baseline",
    )

    assert (output / "resources" / "Scenario.ssv").is_file()
    assert (output / "resources" / "test_baseline.ssm").is_file()


def test_artifacts_root_defaults_to_repo_root_and_is_never_the_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_derivations(monkeypatch, [])
    model_dir = _fixture_dir(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    output = build_fixture(
        model_dir=model_dir,
        repo_root=tmp_path,
        model_name="demo",
        composition="System",
        study="test_baseline",
        package=package_nothing,
    )

    assert output == (
        tmp_path
        / "artifacts"
        / "models"
        / "demo"
        / "test_baseline"
        / "model"
    )
    assert (tmp_path / "artifacts" / "studies" / "demo" / "test_baseline").is_dir()


def test_artifacts_root_is_honoured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_derivations(monkeypatch, [])
    model_dir = _fixture_dir(tmp_path)
    artifacts = tmp_path / "out"

    output = build_fixture(
        model_dir=model_dir,
        repo_root=tmp_path,
        model_name="demo",
        composition="System",
        study="test_baseline",
        artifacts_root=artifacts,
        package=package_nothing,
    )

    assert output == artifacts / "models" / "demo" / "test_baseline" / "model"


def test_build_studies_keeps_the_per_study_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    _stub_derivations(monkeypatch, calls)
    model_dir = _fixture_dir(tmp_path)
    seen: list[str] = []

    def package(model_build_dir, descriptor) -> None:
        seen.append(descriptor.study)

    outputs = build_studies(
        model_dir=model_dir,
        repo_root=tmp_path,
        model_name="demo",
        composition="System",
        studies=("test_baseline", authoring.StudyBuild("second", package)),
    )

    assert sorted(outputs) == ["second", "test_baseline"]


def test_run_fixture_prints_one_line_per_study(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    _stub_derivations(monkeypatch, [])
    model_dir = _fixture_dir(tmp_path)

    status = run_fixture(
        model_dir,
        repo_root=tmp_path,
        model_name="demo",
        studies=("a", "b"),
        package=package_nothing,
    )

    assert status == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 2
    assert lines[0].startswith(f"Built demo a: {tmp_path / 'artifacts'}")
    assert lines[1].startswith(f"Built demo b: {tmp_path / 'artifacts'}")


def _write_model_description(path: Path, interface_type: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<fmiModelDescription fmiVersion="2.0" modelName="fmu" guid="x">',
                f'  <{interface_type} modelIdentifier="fmu"/>',
                "  <ModelVariables>",
                '    <ScalarVariable name="x" valueReference="0" '
                'causality="output" variability="continuous">',
                "      <Real/>",
                "    </ScalarVariable>",
                "  </ModelVariables>",
                "  <ModelStructure/>",
                "</fmiModelDescription>",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_legacy_source(source: Path, *, nested: bool = False) -> None:
    source.mkdir(parents=True)
    elements: list[Ssd1Component | System] = [Ssd1Component(name="step")]
    if nested:
        elements.append(
            System(name="inner", elements=[Ssd1Component(name="gain")])
        )
    with SSD(source / "SystemStructure.ssd", mode="w") as ssd:
        ssd.xml.system = System(name="System", elements=elements)
    for name in ("fmu_a", "fmu_b"):
        _write_model_description(
            source / "resources" / name / "modelDescription.xml", "ModelExchange"
        )


def test_build_legacy_model_copies_and_strips_only_named_resources(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    _write_legacy_source(source)
    model = tmp_path / "model"

    output = build_legacy_model(source, model, strip_resources=("fmu_a",))

    assert output == model
    assert (model / "SystemStructure.ssd").is_file()
    assert "CoSimulation" in (
        model / "resources" / "fmu_a" / "modelDescription.xml"
    ).read_text(encoding="utf-8")
    assert "ModelExchange" in (
        model / "resources" / "fmu_b" / "modelDescription.xml"
    ).read_text(encoding="utf-8")
    assert "ModelExchange" in (
        source / "resources" / "fmu_b" / "modelDescription.xml"
    ).read_text(encoding="utf-8")


def test_build_legacy_model_strips_every_resource_by_default(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    _write_legacy_source(source)
    model = tmp_path / "model"

    build_legacy_model(source, model)

    for name in ("fmu_a", "fmu_b"):
        assert "CoSimulation" in (
            model / "resources" / name / "modelDescription.xml"
        ).read_text(encoding="utf-8")


def test_build_legacy_model_rejects_a_missing_resource(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _write_legacy_source(source)

    with pytest.raises(FileNotFoundError, match="Missing FMU directory"):
        build_legacy_model(source, tmp_path / "model", strip_resources=("missing",))


def test_build_legacy_model_flattens_the_system(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _write_legacy_source(source, nested=True)
    model = tmp_path / "model"

    build_legacy_model(source, model, flatten=True)

    with SSD(model / "SystemStructure.ssd", mode="r") as ssd:
        root = ssd.xml.system
        assert [element.name for element in root.elements] == ["step", "inner_gain"]
        assert all(isinstance(element, Ssd1Component) for element in root.elements)


def test_build_fmu_from_modelica_requires_omc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(authoring.shutil, "which", lambda _name: None)
    source = tmp_path / "M.mo"
    source.write_text("model M end M;", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="omc"):
        build_fmu_from_modelica(
            source_file=source,
            class_name="M",
            fmu_dir=tmp_path / "fmu",
        )


@pytest.mark.skipif(OMC is None, reason="omc is not installed")
def test_build_fmu_from_modelica_syncs_the_fmu_layout(tmp_path: Path) -> None:
    source = tmp_path / "M.mo"
    source.write_text(
        "\n".join(
            [
                "model M",
                "  Real x(start=1);",
                "equation",
                "  der(x) = -x;",
                "end M;",
                "",
            ]
        ),
        encoding="utf-8",
    )
    fmu_dir = tmp_path / "fmu"

    output = build_fmu_from_modelica(
        source_file=source,
        class_name="M",
        file_name_prefix="M",
        fmu_dir=fmu_dir,
    )

    assert output == fmu_dir
    assert (fmu_dir / "modelDescription.xml").is_file()
    assert (fmu_dir / "documentation" / "index.html").is_file()
    assert any((fmu_dir / "binaries" / "linux64").iterdir())
    assert "ModelExchange" not in (
        fmu_dir / "modelDescription.xml"
    ).read_text(encoding="utf-8")

