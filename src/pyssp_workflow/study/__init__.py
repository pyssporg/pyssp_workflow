"""Study descriptors and their standardized scenario artifacts.

``StudyDescriptor`` names the scenario SSV and SSM; ``Scenario`` is those
artifacts read as plain, read-only data.
"""

from __future__ import annotations

from pyssp_workflow.study.descriptor import (
    Experiment,
    StudyDescriptor,
    read_study_descriptor,
)
from pyssp_workflow.study.scenario import (
    Scenario,
    read_scenario,
    scenario_targets,
)

__all__ = [
    "Experiment",
    "Scenario",
    "StudyDescriptor",
    "read_scenario",
    "read_study_descriptor",
    "scenario_targets",
]
