"""The node layer is optional and fails with an actionable message."""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
HINT = "pyssp-workflow[flow]"


def _shadow(tmp_path: Path, *, flow: str | None) -> Path:
    """A ``sequence_extensions`` package this test controls, before the real one."""
    shadow = tmp_path / "shadow"
    package = shadow / "sequence_extensions"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    if flow is not None:
        subpackage = package / "flow"
        subpackage.mkdir()
        (subpackage / "__init__.py").write_text(flow, encoding="utf-8")
    return shadow


def _import_nodes(shadow: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(shadow), str(SRC), environment.get("PYTHONPATH", "")]
    )
    return subprocess.run(
        [sys.executable, "-c", "import pyssp_workflow.nodes"],
        capture_output=True,
        text=True,
        cwd=shadow,
        env=environment,
    )


def test_nodes_export_the_flow_backed_work_units() -> None:
    nodes = importlib.import_module("pyssp_workflow.nodes")

    assert callable(nodes.write_bundle)
    assert callable(nodes.derive_study)


def test_nodes_require_the_flow_subpackage_not_just_its_parent(tmp_path: Path) -> None:
    result = _import_nodes(_shadow(tmp_path, flow=None))

    assert result.returncode != 0
    assert HINT in result.stderr


def test_nodes_do_not_mask_an_import_error_raised_inside_the_flow_package(
    tmp_path: Path,
) -> None:
    result = _import_nodes(_shadow(tmp_path, flow='raise ImportError("broken in flow")\n'))

    assert result.returncode != 0
    assert "broken in flow" in result.stderr
    assert HINT not in result.stderr
