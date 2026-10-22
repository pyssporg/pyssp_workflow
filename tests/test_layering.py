"""Import-graph rules that keep this package a composition layer."""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "pyssp_workflow"

FLOW_LAYER = "nodes"
JUDGE_ALLOWED = ("nodes", "cli")
AUTHORING_MUST_NOT_IMPORT = ("pyssp_vv",)

#: Symbols that would mean a capability was reimplemented here.
CAPABILITY_MARKERS = ("def compare(", "def judge(", "def passed(", "passed(")


def _module_name(path: Path) -> str:
    parts = list(path.relative_to(SRC).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(["pyssp_workflow", *parts]) if parts else "pyssp_workflow"


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


def test_flow_engine_is_confined_to_the_node_layer():
    violations = [
        f"{module} imports {name}"
        for _path, module, imports in _walk()
        for name in imports
        if name.split(".")[0] == "sequence_extensions" and _layer(module) != FLOW_LAYER
    ]
    assert not violations, (
        "flow engine leaked outside pyssp_workflow.nodes:\n" + "\n".join(violations)
    )


def test_authoring_cannot_reach_the_judgment_layer():
    violations = [
        f"{module} imports {name}"
        for _path, module, imports in _walk()
        if _layer(module) == "authoring"
        for name in imports
        if name.startswith(AUTHORING_MUST_NOT_IMPORT)
    ]
    assert not violations, (
        "the authoring path can reach the V&V layer that evaluates its output:\n"
        + "\n".join(violations)
    )


def test_judgment_is_only_reachable_from_the_composition_layer():
    violations = [
        f"{module} imports {name}"
        for _path, module, imports in _walk()
        if _layer(module) not in JUDGE_ALLOWED
        for name in imports
        if name.startswith("pyssp_vv.judge")
    ]
    assert not violations, (
        "an execution-side module decides acceptability:\n" + "\n".join(violations)
    )


def test_no_capability_is_reimplemented_here():
    violations = []
    for path in sorted(SRC.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for marker in CAPABILITY_MARKERS:
            if marker in text:
                violations.append(f"{path.relative_to(SRC)} contains {marker!r}")
    assert not violations, (
        "measurement or judgment leaked into the workflow layer:\n" + "\n".join(violations)
    )
