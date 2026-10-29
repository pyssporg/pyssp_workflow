"""Shared test data: scenario descriptors and the test-level table."""

from __future__ import annotations

import json
from pathlib import Path

from pyssp_standard import SSM, SSV

LEVEL_MARKERS = (
    "level_static",
    "level_unit",
    "level_component",
    "level_contract",
    "level_integration",
    "level_system",
    "level_acceptance",
)

#: Imported by ``tests/conftest.py`` unless the module sets ``pytestmark``.
FILE_LEVELS = {
    "test_authoring_build.py": "level_component",
    "test_binding.py": "level_component",
    "test_bundle.py": "level_component",
    "test_compare.py": "level_component",
    "test_fixture.py": "level_unit",
    "test_fixture_policy.py": "level_static",
    "test_layering.py": "level_static",
    "test_markers.py": "level_static",
    "test_nodes_import.py": "level_static",
    "test_analysis.py": "level_component",
}


def write_scenario(
    analysis_dir: Path,
    *,
    with_scenario: bool = True,
    model_source: str | None = None,
    values: dict[str, object] | None = None,
    value_types: dict[str, str] | None = None,
    mappings: tuple[tuple[str, str], ...] | None = None,
    target_ssd: str = "SystemStructure.ssd",
) -> Path:
    """Write one analysis directory: ``analysis.json`` plus its optional SSV and SSM."""
    analysis_dir.mkdir()
    values = values or {"height": 2.0, "k": 3.0}
    value_types = value_types or {}
    mappings = mappings or (("height", "step.height"), ("k", "gain.k"))
    if with_scenario:
        with SSV(analysis_dir / "Scenario.ssv", mode="w") as ssv:
            ssv.xml.name = "Scenario"
            for name, value in values.items():
                ssv.xml.add_parameter(
                    name,
                    ptype=value_types.get(name, "Real"),
                    value=value,
                )
        with SSM(analysis_dir / "test_baseline.ssm", mode="w") as ssm:
            for source, target in mappings:
                ssm.xml.add_mapping(source, target)
    descriptor = {
        "model": "example",
        "composition": "System",
        "sut": "sut",
        "target_ssd": target_ssd,
        "analysis": "test_baseline",
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
    path = analysis_dir / "analysis.json"
    path.write_text(json.dumps(descriptor), encoding="utf-8")
    return path
