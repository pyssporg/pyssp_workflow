"""The oracle protocol: how a candidate is judged.

Provenance is part of the contract, not documentation. ``AGREEMENT`` is
engine-versus-engine comparison; it records that two implementations differ (or
do not), never that either is correct, because shared bugs are invisible to it.
Only ``REFERENCE``, ``ANALYTIC``, ``INVARIANT``, ``METAMORPHIC``, and
``MEASUREMENT`` oracles make a claim about behaviour.

An oracle receives paths and read-only context. It may not import
``pyssp_vv.authoring`` and may not write outside its own result directory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Mapping, Protocol, runtime_checkable

from pyssp_vv.spec.verdict import Verdict


class Provenance(str, Enum):
    """Where the expectation being judged comes from."""

    AGREEMENT = "agreement"
    REFERENCE = "reference"
    ANALYTIC = "analytic"
    INVARIANT = "invariant"
    METAMORPHIC = "metamorphic"
    MEASUREMENT = "measurement"


@dataclass(frozen=True)
class Candidate:
    """One simulation output, addressed by path.

    ``result_csv`` is the normalized trajectory; ``run_dir`` gives an oracle
    access to the run manifest and diagnostic logs when it needs them.
    """

    run_dir: Path
    result_csv: Path


@dataclass(frozen=True)
class OracleContext:
    """Assessment-level facts an oracle may read.

    Deliberately closed: no builder, no engine handle, no configuration object
    that could be mutated to influence the outcome.
    """

    assessment_id: str
    held_factors: Mapping[str, str]
    reference: Path | None = None


@dataclass(frozen=True)
class OracleResult:
    """The single return value of an oracle."""

    oracle_id: str
    verdict: Verdict
    metrics: Mapping[str, float] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()


@runtime_checkable
class Oracle(Protocol):
    """Structural interface every oracle satisfies."""

    kind: str
    provenance: Provenance

    def evaluate(self, candidate: Candidate, context: OracleContext) -> OracleResult:
        """Render one verdict for ``candidate``."""
