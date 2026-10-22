"""Parameter-set resolution: SSV defaults plus explicit overrides.

Contract (not yet implemented): produce one immutable resolved record from the
SSP's parameter set and any scenario overrides, and fail loudly on a missing or
ambiguous parameter name. Resolution never mutates the SSP on disk.
"""
