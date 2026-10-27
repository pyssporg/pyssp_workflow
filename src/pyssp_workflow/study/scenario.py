"""Read the standardized scenario artifacts a study descriptor names.

The SSV and SSM are the interchange artifacts; this module opens them read-only
and returns plain data. It never rewrites them.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from pyssp_standard import SSM, SSV

from pyssp_workflow.study.descriptor import StudyDescriptor


@dataclass(frozen=True)
class Scenario:
    """One study scenario: SSV values and their optional SSM mappings."""

    set_name: str
    ssv_path: Path
    ssm_path: Path | None
    values: Mapping[str, float]
    mappings: tuple[tuple[str, str], ...]


def read_scenario(descriptor: StudyDescriptor) -> Scenario:
    """The descriptor's scenario as read-only data.

    Raises ``ValueError`` when the descriptor names no scenario SSV.
    """
    if descriptor.ssv_path is None:
        raise ValueError(
            f"Study descriptor '{descriptor.path}' names no scenario SSV"
        )
    with SSV(descriptor.ssv_path, mode="r") as ssv:
        values = {
            parameter.name: float(parameter.attributes["value"])
            for parameter in ssv.xml.parameters
        }
    if descriptor.ssm_path is None:
        mappings: tuple[tuple[str, str], ...] = ()
    else:
        with SSM(descriptor.ssm_path, mode="r") as ssm:
            mappings = tuple(
                (mapping.source, mapping.target) for mapping in ssm.xml.mappings
            )
    return Scenario(
        set_name=descriptor.set_name or "",
        ssv_path=descriptor.ssv_path,
        ssm_path=descriptor.ssm_path,
        values=values,
        mappings=mappings,
    )


def scenario_targets(scenario: Scenario) -> dict[str, float]:
    """The scenario values keyed by the mapped SSP target name.

    Read-only. Raises ``ValueError`` when the scenario names no SSM; ``KeyError``
    when a mapping names a member the SSV lacks.
    """
    if scenario.ssm_path is None or not scenario.mappings:
        raise ValueError(
            f"Study scenario '{scenario.ssv_path}' names no scenario SSM"
        )
    with SSV(scenario.ssv_path, mode="r") as ssv:
        parameters = ssv.parameters_by_name()
    with SSM(scenario.ssm_path, mode="r") as ssm:
        resolved = ssm.resolve(parameters)
    return {
        target: float(parameter.attributes["value"])
        for target, parameter in resolved.items()
    }
