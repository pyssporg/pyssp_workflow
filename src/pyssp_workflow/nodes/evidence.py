"""Evidence nodes."""

from __future__ import annotations

from pathlib import Path

from pyssp_vv.evidence.bundle import EvidenceBundle
from sequence_extensions.flow import node


@node(retries=0, timeout=60.0)
def write_bundle(bundle: EvidenceBundle, out_dir: str) -> str:
    """Persist one bundle under ``out_dir`` and return its absolute path.

    Explicit-path contract: this node owns exactly ``<out_dir>/evidence.json``,
    creates the directory if needed, and never consults the working directory.
    Its arguments and return value are picklable, so it survives a process pool.
    """
    return str(bundle.write(Path(out_dir) / "evidence.json"))
