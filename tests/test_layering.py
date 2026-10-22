"""Import-graph rules that keep the core independent.

These are architecture constraints, not style preferences. If one of these
fails, fix the code rather than the test.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "pyssp_vv"

#: Layers whose imports must resolve to the standard library or pyssp_vv.
STDLIB_ONLY = ("spec", "evidence", "plan")

#: The only layer allowed to import a flow engine.
FLOW_LAYER = "nodes"

#: Layers that must never be able to reach the model authoring tool.
NO_AUTHORING = ("spec", "evidence", "plan", "oracle", "compare", "execute")

#: Only the node layer may depend on the node layer's contents from outside.
LEAF_LAYER = "nodes"


def _module_name(path: Path) -> str:
    parts = list(path.relative_to(SRC).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(["pyssp_vv", *parts]) if parts else "pyssp_vv"


def _layer(module: str) -> str:
    parts = module.split(".")
    return parts[1] if len(parts) > 1 else ""


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.append(node.module)
    return names


def _walk():
    for path in sorted(SRC.rglob("*.py")):
        yield path, _module_name(path), _imports(path)


def test_stdlib_only_layers_have_no_third_party_imports():
    allowed = set(sys.stdlib_module_names) | {"__future__"}
    violations = []
    for _path, module, imports in _walk():
        if _layer(module) not in STDLIB_ONLY:
            continue
        for name in imports:
            top = name.split(".")[0]
            if top != "pyssp_vv" and top not in allowed:
                violations.append(f"{module} imports {name}")
    assert not violations, "stdlib-only layer leaked a dependency:\n" + "\n".join(violations)


def test_flow_engine_is_confined_to_the_node_layer():
    violations = [
        f"{module} imports {name}"
        for _path, module, imports in _walk()
        for name in imports
        if name.split(".")[0] == "sequence_extensions" and _layer(module) != FLOW_LAYER
    ]
    assert not violations, "flow engine leaked outside pyssp_vv.nodes:\n" + "\n".join(violations)


def test_verification_layers_cannot_import_authoring():
    violations = [
        f"{module} imports {name}"
        for _path, module, imports in _walk()
        for name in imports
        if _layer(module) in NO_AUTHORING and name.startswith("pyssp_vv.authoring")
    ]
    assert not violations, (
        "verification code reached into the authoring tool; the verifier must not "
        "be able to see how the model was produced:\n" + "\n".join(violations)
    )


def test_node_layer_is_a_leaf():
    violations = [
        f"{module} imports {name}"
        for _path, module, imports in _walk()
        for name in imports
        if _layer(module) != LEAF_LAYER and name.startswith("pyssp_vv.nodes")
    ]
    assert not violations, "a non-node module depends on the node layer:\n" + "\n".join(violations)
