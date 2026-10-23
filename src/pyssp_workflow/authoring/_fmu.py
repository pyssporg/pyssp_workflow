"""FMU model-exchange metadata helpers shared by the authoring build steps."""

from __future__ import annotations

from pathlib import Path

from pyssp_standard import FMU


def strip_model_exchange(root: Path) -> None:
    """Strip model-exchange metadata from every FMU directory under ``root``."""
    for description in sorted(root.rglob("modelDescription.xml")):
        with FMU(description.parent, mode="a") as fmu:
            with fmu.model_description as model_description:
                model_description.strip_model_exchange()


def strip_fmu(path: Path) -> None:
    """Strip model-exchange metadata from the FMU directory ``path``."""
    with FMU(path, mode="a") as fmu:
        with fmu.model_description as model_description:
            model_description.strip_model_exchange()


__all__ = ["strip_fmu", "strip_model_exchange"]
