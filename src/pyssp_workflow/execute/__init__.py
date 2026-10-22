"""Simulation execution, delegated to ``pyssp_simulate``.

Contract (not yet implemented): run one case and return the paths it wrote.
Engine execution happens in a child process, because a thread cannot be
preempted and a native engine abort would otherwise take the caller down.
"""
