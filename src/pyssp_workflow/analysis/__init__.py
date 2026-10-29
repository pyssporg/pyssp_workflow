"""Analysis descriptors and their standardized scenario artifacts.

``AnalysisDescriptor`` names the scenario SSV and SSM; ``Scenario`` is those
artifacts read as plain, read-only data.
"""

from __future__ import annotations

from pyssp_workflow.analysis.descriptor import (
    AnalysisDescriptor,
    Experiment,
    read_analysis_descriptor,
)
from pyssp_workflow.analysis.scenario import (
    Scenario,
    read_scenario,
    scenario_targets,
)

__all__ = [
    "Experiment",
    "Scenario",
    "AnalysisDescriptor",
    "read_scenario",
    "read_analysis_descriptor",
    "scenario_targets",
]
