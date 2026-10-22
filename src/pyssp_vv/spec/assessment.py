"""What is being claimed, and how it will be judged.

An assessment is the unit of controlled comparison. It declares exactly one
independent *factor*, the factors held constant across the levels of that
factor, and the oracles that render verdicts.

It is data: JSON round-trippable, no callables, no open handles. Unknown keys
are rejected so a typo in a hand-written assessment fails loudly instead of
silently disabling a declaration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from pyssp_vv.spec.verdict import Verdict
from pyssp_vv.spec.version import SCHEMA_VERSION


def _reject_unknown(data: Mapping[str, Any], allowed: set[str], where: str) -> None:
    unknown = set(data) - allowed
    if unknown:
        raise ValueError(f"Unknown {where} keys: {sorted(unknown)}")


@dataclass(frozen=True)
class Tolerance:
    """Acceptance tolerance for one oracle.

    ``shift_samples`` is the symmetric search window used when comparing two
    trajectories that may differ only by scheduling skew. It is not a
    correction: the reported metrics stay pointwise.
    """

    atol: float
    rtol: float = 0.0
    shift_samples: int = 0

    def __post_init__(self) -> None:
        if self.atol < 0 or self.rtol < 0:
            raise ValueError("Tolerance values must be non-negative")
        if self.shift_samples < 0:
            raise ValueError("shift_samples must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "atol": self.atol,
            "rtol": self.rtol,
            "shift_samples": self.shift_samples,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Tolerance":
        _reject_unknown(data, {"atol", "rtol", "shift_samples"}, "tolerance")
        return cls(
            atol=float(data["atol"]),
            rtol=float(data.get("rtol", 0.0)),
            shift_samples=int(data.get("shift_samples", 0)),
        )


@dataclass(frozen=True)
class Factor:
    """The single independent variable of an assessment.

    Comparing the outcomes across ``levels`` is only interpretable when every
    entry in :attr:`Assessment.held` is identical for all runs.
    """

    name: str
    levels: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Factor name must not be empty")
        if not self.levels:
            raise ValueError("Factor must declare at least one level")
        if len(set(self.levels)) != len(self.levels):
            raise ValueError(f"Factor {self.name!r} has duplicate levels")

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "levels": list(self.levels)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Factor":
        _reject_unknown(data, {"name", "levels"}, "factor")
        return cls(name=str(data["name"]), levels=tuple(data["levels"]))


@dataclass(frozen=True)
class OracleRef:
    """A named judgment to apply, plus the tolerance it judges against.

    ``kind`` is one of ``cross_engine``, ``reference_csv``, ``analytic``,
    ``invariant``, ``metamorphic``, ``measurement``. The oracle implementation
    is resolved by the runner; this record is the declaration.
    """

    oracle_id: str
    kind: str
    tolerance: Tolerance
    params: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "oracle_id": self.oracle_id,
            "kind": self.kind,
            "tolerance": self.tolerance.to_dict(),
            "params": dict(self.params),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "OracleRef":
        _reject_unknown(data, {"oracle_id", "kind", "tolerance", "params"}, "oracle")
        return cls(
            oracle_id=str(data["oracle_id"]),
            kind=str(data["kind"]),
            tolerance=Tolerance.from_dict(data["tolerance"]),
            params=dict(data.get("params", {})),
        )


@dataclass(frozen=True)
class Disposition:
    """A decision to accept a known outcome instead of treating it as new.

    A disposition is only valid for a named assessment and oracle. It records
    who accepted it and when it must be revisited, so a waiver cannot become a
    silent permanent exemption.
    """

    assessment_id: str
    oracle_id: str
    verdict: Verdict
    reason: str
    owner: str
    expires: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "oracle_id": self.oracle_id,
            "verdict": Verdict(self.verdict).value,
            "reason": self.reason,
            "owner": self.owner,
            "expires": self.expires,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Disposition":
        _reject_unknown(
            data,
            {"assessment_id", "oracle_id", "verdict", "reason", "owner", "expires"},
            "disposition",
        )
        return cls(
            assessment_id=str(data["assessment_id"]),
            oracle_id=str(data["oracle_id"]),
            verdict=Verdict(data["verdict"]),
            reason=str(data["reason"]),
            owner=str(data["owner"]),
            expires=data.get("expires"),
        )


@dataclass(frozen=True)
class Assessment:
    """One controlled comparison: a factor, its held constants, and oracles."""

    assessment_id: str
    model: str
    case: str
    factor: Factor
    held: tuple[str, ...]
    oracles: tuple[OracleRef, ...]
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.assessment_id:
            raise ValueError("assessment_id must not be empty")
        if not self.model or not self.case:
            raise ValueError("model and case must not be empty")
        if not self.oracles:
            raise ValueError("An assessment must declare at least one oracle")
        if self.factor.name in self.held:
            raise ValueError(
                f"{self.factor.name!r} is both the independent factor and a held "
                "factor; a comparison cannot vary and hold the same thing"
            )
        if len(set(self.held)) != len(self.held):
            raise ValueError("held factors must be unique")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "assessment_id": self.assessment_id,
            "model": self.model,
            "case": self.case,
            "factor": self.factor.to_dict(),
            "held": list(self.held),
            "oracles": [oracle.to_dict() for oracle in self.oracles],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Assessment":
        _reject_unknown(
            data,
            {
                "schema_version",
                "assessment_id",
                "model",
                "case",
                "factor",
                "held",
                "oracles",
            },
            "assessment",
        )
        return cls(
            assessment_id=str(data["assessment_id"]),
            model=str(data["model"]),
            case=str(data["case"]),
            factor=Factor.from_dict(data["factor"]),
            held=tuple(data["held"]),
            oracles=tuple(OracleRef.from_dict(item) for item in data["oracles"]),
            schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
        )
