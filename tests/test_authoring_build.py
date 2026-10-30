from __future__ import annotations

import json
import shutil
from pathlib import Path
from zipfile import ZipFile

import pytest
from pyssp_standard import SSD, SSM, SSV, Component

from pyssp_workflow import authoring
from pyssp_workflow.authoring import (
    _process,
    build_fixture,
    build_fmu_from_modelica,
    build_legacy_model,
    report_builds,
)
from pyssp_workflow.authoring import build as authoring_build
from pyssp_workflow.authoring import derive as authoring_derive
from pyssp_workflow.binding import bind
from pyssp_workflow.fixture import BuiltFixture

OMC = shutil.which("omc")


def _write_analysis_artifacts(analysis_dir: Path) -> None:
    analysis_dir.mkdir(parents=True, exist_ok=True)
    with SSV(analysis_dir / "Scenario.ssv", mode="w") as ssv:
        ssv.xml.name = "Scenario"
        ssv.xml.add_parameter("height", ptype="Real", value=2.0)
    with SSM(analysis_dir / "test_baseline.ssm", mode="w") as ssm:
        ssm.xml.add_mapping("height", "step.height")
    (analysis_dir / "analysis.json").write_text(
        json.dumps(
            {
                "model": "demo",
                "composition": "System",
                "sut": "sut",
                "analysis": "test_baseline",
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
        root = ssd.new_system("System")
        root.add_component("step")
    with ZipFile(path, "w") as archive:
        archive.write(staging / "SystemStructure.ssd", "SystemStructure.ssd")


def _stub_derivations(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[str],
    derivations_seen: list[tuple[str, str]] | None = None,
    selections_seen: list[tuple[str, dict[str, str] | None]] | None = None,
) -> None:
    def fake_analysis(
        architecture_path,
        output_dir,
        composition,
        *,
        model_name,
        pyssp=None,
        target_ssd="SystemStructure.ssd",
        timeout=authoring.DEFAULT_TIMEOUT_SECONDS,
        selections=None,
    ):
        calls.append("analysis")
        if selections_seen is not None:
            selections_seen.append(("analysis", selections))
        assert Path(architecture_path).is_dir()
        assert model_name == "demo"
        if derivations_seen is not None:
            derivations_seen.append((composition, model_name))
        _write_analysis_artifacts(Path(output_dir))
        return Path(output_dir) / "analysis.json"

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
        selections=None,
    ):
        calls.append("model")
        if selections_seen is not None:
            selections_seen.append(("model", selections))
        assert Path(architecture_path).is_dir()
        assert composition == "System"
        _write_ssp_archive(Path(output_path))
        return Path(output_path)

    monkeypatch.setattr(authoring_build, "derive_analysis_from_sysml", fake_analysis)
    monkeypatch.setattr(authoring_build, "derive_ssp_from_sysml", fake_ssp)


def _fixture_dir(tmp_path: Path) -> Path:
    model_dir = tmp_path / "models" / "ssp" / "demo"
    (model_dir / "architecture").mkdir(parents=True)
    return model_dir


def test_build_fixture_runs_analysis_then_model_without_packaging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    derivations_seen: list[str] = []
    _stub_derivations(monkeypatch, calls, derivations_seen)
    model_dir = _fixture_dir(tmp_path)

    builds = build_fixture(
        model_dir=model_dir,
        repo_root=tmp_path,
        model_name="demo",
        composition="System",
        analyses=("test_baseline",),
    )

    assert calls == ["analysis", "model"]
    assert derivations_seen == [("test_baseline", "demo")]
    build = builds["test_baseline"]
    assert isinstance(build, BuiltFixture)
    assert build.model_name == "demo"
    assert build.analysis == "test_baseline"
    assert build.analysis_dir == (
        tmp_path / "artifacts" / "analyses" / "demo" / "test_baseline"
    )
    assert build.model_dir == (
        tmp_path / "artifacts" / "models" / "demo" / "test_baseline" / "model"
    )
    assert build.descriptor.analysis == "test_baseline"
    assert not (build.model_dir / "resources").exists()


def test_bind_external_attach_packages_a_built_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_derivations(monkeypatch, [])
    model_dir = _fixture_dir(tmp_path)
    builds = build_fixture(
        model_dir=model_dir,
        repo_root=tmp_path,
        model_name="demo",
        composition="System",
        analyses=("test_baseline",),
    )

    build = builds["test_baseline"]
    bind(build, build.descriptor.ssv_path, ssm=build.descriptor.ssm_path)

    output = builds["test_baseline"].model_dir
    assert (output / "resources" / "Scenario.ssv").is_file()
    assert (output / "resources" / "test_baseline.ssm").is_file()


def test_build_fixture_builds_every_analysis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    derivations_seen: list[str] = []
    _stub_derivations(monkeypatch, calls, derivations_seen)
    model_dir = _fixture_dir(tmp_path)

    builds = build_fixture(
        model_dir=model_dir,
        repo_root=tmp_path,
        model_name="demo",
        composition="System",
        analyses=("test_baseline", "second"),
    )

    assert calls == ["analysis", "model", "analysis", "model"]
    # The analysis build derives the Analysis composition; only the model build
    # derives the SspModel composition.
    assert derivations_seen == [("test_baseline", "demo"), ("second", "demo")]
    assert sorted(builds) == ["second", "test_baseline"]
    assert builds["second"].analysis == "second"
    assert builds["second"].analysis_dir.name == "second"


def test_artifacts_root_defaults_to_repo_root_and_is_never_the_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_derivations(monkeypatch, [])
    model_dir = _fixture_dir(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    builds = build_fixture(
        model_dir=model_dir,
        repo_root=tmp_path,
        model_name="demo",
        composition="System",
        analyses=("test_baseline",),
    )

    assert builds["test_baseline"].model_dir == (
        tmp_path / "artifacts" / "models" / "demo" / "test_baseline" / "model"
    )
    assert (tmp_path / "artifacts" / "analyses" / "demo" / "test_baseline").is_dir()


def test_artifacts_root_is_honoured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_derivations(monkeypatch, [])
    model_dir = _fixture_dir(tmp_path)
    artifacts = tmp_path / "out"

    builds = build_fixture(
        model_dir=model_dir,
        repo_root=tmp_path,
        model_name="demo",
        composition="System",
        analyses=("test_baseline",),
        artifacts_root=artifacts,
    )

    assert builds["test_baseline"].model_dir == (
        artifacts / "models" / "demo" / "test_baseline" / "model"
    )


def test_each_build_record_is_packaged_explicitly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_derivations(monkeypatch, [])
    model_dir = _fixture_dir(tmp_path)

    builds = build_fixture(
        model_dir=model_dir,
        repo_root=tmp_path,
        model_name="demo",
        composition="System",
        analyses=("test_baseline", "second"),
    )
    for build in builds.values():
        bind(build, build.descriptor.ssv_path, ssm=build.descriptor.ssm_path)

    for build in builds.values():
        assert (build.model_dir / "resources" / "Scenario.ssv").is_file()
        assert (build.model_dir / "resources" / "test_baseline.ssm").is_file()


def test_report_builds_prints_one_line_per_analysis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    _stub_derivations(monkeypatch, [])
    model_dir = _fixture_dir(tmp_path)

    builds = build_fixture(
        model_dir=model_dir,
        repo_root=tmp_path,
        model_name="demo",
        composition="System",
        analyses=("a", "b"),
    )
    status = report_builds(builds)

    assert status == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 2
    assert lines[0] == (
        f"Built demo a: {tmp_path / 'artifacts' / 'models' / 'demo' / 'a' / 'model'}"
    )
    assert lines[1] == (
        f"Built demo b: {tmp_path / 'artifacts' / 'models' / 'demo' / 'b' / 'model'}"
    )


@pytest.mark.level_contract
def test_ssp_derivation_argv_carries_the_fmu_validation_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments: list[list[str]] = []

    def fake_run(pyssp, argv, timeout):
        arguments.append(list(argv))
        return ""

    monkeypatch.setattr(authoring_derive, "_run_pyssp", fake_run)
    architecture = tmp_path / "architecture"
    architecture.mkdir()

    authoring_derive.derive_ssp_from_sysml(
        architecture, tmp_path / "model.ssp", "System", validate_fmus=False
    )
    authoring_derive.derive_ssp_from_sysml(
        architecture, tmp_path / "model.ssp", "System", validate_fmus=True
    )

    assert "--composition" in arguments[0]
    assert arguments[0][arguments[0].index("--composition") + 1] == "System"
    assert "--skip-fmu-validation" in arguments[0]
    assert "--skip-fmu-validation" not in arguments[1]


def _select_pairs(argv: list[str]) -> list[str]:
    return [argv[index + 1] for index, value in enumerate(argv) if value == "--select"]


def _record_generate_argv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> list[list[str]]:
    arguments: list[list[str]] = []

    def fake_run(pyssp, argv, timeout):
        arguments.append(list(argv))
        if "analysis" in argv:
            _write_analysis_artifacts(Path(argv[argv.index("--output-dir") + 1]))
        return ""

    monkeypatch.setattr(authoring_derive, "_run_pyssp", fake_run)
    return arguments


@pytest.mark.level_contract
def test_select_pairs_are_sorted_and_omitted_when_unselected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments = _record_generate_argv(tmp_path, monkeypatch)
    architecture = tmp_path / "architecture"
    architecture.mkdir()
    selections = {"variant_b": "two", "variant_a": "one"}

    authoring_derive.derive_ssd_from_sysml(
        architecture, tmp_path / "out.ssd", "System", selections=selections
    )
    authoring_derive.derive_ssp_from_sysml(
        architecture, tmp_path / "out.ssp", "System", selections=selections
    )
    authoring_derive.derive_analysis_from_sysml(
        architecture,
        tmp_path / "analysis",
        "System",
        model_name="demo",
        selections=selections,
    )
    authoring_derive.derive_ssd_from_sysml(
        architecture, tmp_path / "plain.ssd", "System"
    )
    authoring_derive.derive_ssp_from_sysml(
        architecture, tmp_path / "plain.ssp", "System", selections={}
    )

    assert [_select_pairs(argv) for argv in arguments[:3]] == [
        ["variant_a=one", "variant_b=two"],
        ["variant_a=one", "variant_b=two"],
        ["variant_a=one", "variant_b=two"],
    ]
    assert [_select_pairs(argv) for argv in arguments[3:]] == [[], []]
    assert "--select" not in arguments[3]
    assert "--select" not in arguments[4]


def test_build_fixture_passes_each_analysis_only_its_own_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selections_seen: list[tuple[str, dict[str, str] | None]] = []
    _stub_derivations(
        monkeypatch, [], selections_seen=selections_seen
    )
    model_dir = _fixture_dir(tmp_path)
    selection = {"path.stage": "attenuateStage"}

    build_fixture(
        model_dir=model_dir,
        repo_root=tmp_path,
        model_name="demo",
        composition="System",
        analyses=("a", "b"),
        selections={"b": selection},
    )

    assert selections_seen == [
        ("analysis", None),
        ("model", None),
        ("analysis", selection),
        ("model", selection),
    ]


def test_build_fixture_passes_one_selection_map_to_both_derivations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selections_seen: list[tuple[str, dict[str, str] | None]] = []
    _stub_derivations(
        monkeypatch, [], selections_seen=selections_seen
    )
    model_dir = _fixture_dir(tmp_path)
    selection = {"path": "direct", "scenario": "baseline"}

    build_fixture(
        model_dir=model_dir,
        repo_root=tmp_path,
        model_name="demo",
        composition="System",
        analyses=("a",),
        selections={"a": selection},
    )
    assert selections_seen == [
        ("analysis", selection),
        ("model", selection),
    ]


def test_build_fixture_rejects_a_selection_for_an_unknown_analysis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_derivations(monkeypatch, [])
    model_dir = _fixture_dir(tmp_path)

    with pytest.raises(ValueError, match="unknown"):
        build_fixture(
            model_dir=model_dir,
            repo_root=tmp_path,
            model_name="demo",
            composition="System",
            analyses=("a",),
            selections={"unknown": {"variant": "two"}},
        )


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
    with SSD(source / "SystemStructure.ssd", mode="w") as ssd:
        root = ssd.new_system("System")
        root.add_component("step")
        if nested:
            inner = root.add_subsystem("inner")
            inner.add_component("gain")
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
        root = ssd.system
        assert [element.name for element in root.elements] == ["step", "inner_gain"]
        assert all(isinstance(element, Component) for element in root.elements)


def test_build_fmu_from_modelica_requires_omc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(_process.shutil, "which", lambda _name: None)
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

