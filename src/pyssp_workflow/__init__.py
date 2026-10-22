"""Composable workflows for building, running, comparing, and judging SSP models.

This package composes capabilities; it owns none of them. Measurement and
judgment live in ``pyssp_vv``, simulation in ``pyssp_simulate``, SSP assembly in
``pyssp_standard``, and scheduling in ``sequence_extensions``.

Public modules that do not require optional capabilities may be imported
directly, for example ``pyssp_workflow.params`` and
``pyssp_workflow.authoring``. The package itself keeps its top-level import
dependency-free so the optional capability extras stay optional.
"""

__version__ = "0.1.0"
