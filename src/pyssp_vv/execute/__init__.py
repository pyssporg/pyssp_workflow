"""Simulation execution.

Contract (not yet implemented): run one simulation case and return the paths it
wrote. Engine execution happens in a child process, because a thread cannot be
preempted and a native engine abort would otherwise take the caller down.
"""
