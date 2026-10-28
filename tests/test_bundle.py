"""The evidence bundle writer owns exactly ``<out_dir>/evidence.json``."""

from __future__ import annotations

from pathlib import Path

import pytest
from pyssp_vv.evidence import EvidenceBundle

from pyssp_workflow.nodes import write_bundle

pytestmark = pytest.mark.level_component


def test_write_bundle_persists_evidence_json_under_out_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = EvidenceBundle(
        assessment_id="assessment",
        inputs=(),
        verdicts=(),
        environment={},
    )
    out_dir = tmp_path / "nested" / "out"
    monkeypatch.chdir(tmp_path)

    written = write_bundle(bundle, str(out_dir))

    target = out_dir / "evidence.json"
    assert target.is_file()
    assert written == str(target.resolve())
    assert not (tmp_path / "evidence.json").exists()
