"""The node layer is optional and fails with an actionable message."""

from __future__ import annotations

import importlib
import importlib.util

import pytest

FLOW_INSTALLED = importlib.util.find_spec("sequence_extensions") is not None


@pytest.mark.skipif(FLOW_INSTALLED, reason="flow extra is installed")
def test_nodes_require_the_flow_extra():
    with pytest.raises(ImportError, match="pyssp-vv\\[flow\\]"):
        importlib.import_module("pyssp_vv.nodes")


@pytest.mark.skipif(not FLOW_INSTALLED, reason="flow extra is not installed")
def test_nodes_export_write_bundle():
    nodes = importlib.import_module("pyssp_vv.nodes")
    assert callable(nodes.write_bundle)
