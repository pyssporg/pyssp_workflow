"""Import-graph rules that keep this package a composition layer."""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "pyssp_workflow"

FLOW_LAYER = "nodes"

#: The internal modules each layer may import, from the bottom up.
INTERNAL_DEPENDENCIES = {
    "fixture": frozenset({"study"}),
    "study": frozenset(),
    "authoring": frozenset({"fixture", "study"}),
    "binding": frozenset({"fixture", "study"}),
    "compare": frozenset(),
    "nodes": frozenset({"fixture", "study", "authoring", "binding", "compare"}),
}

#: Only the node layer may decide acceptability; there is no CLI layer.
JUDGE_ALLOWED = ("nodes",)
AUTHORING_MUST_NOT_IMPORT = ("pyssp_vv",)

#: The V&V modules the comparison layer may compose: measurement and the
#: stdlib-only evidence schema. Judgment and policy are not composable there.
COMPARE_MAY_IMPORT = ("pyssp_vv.measure", "pyssp_vv.evidence")

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


def _internal_layer(name: str) -> str | None:
    parts = name.split(".")
    if parts[0] != "pyssp_workflow":
        return None
    return parts[1] if len(parts) > 1 else ""


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.append(node.module)
            if node.module == "pyssp_workflow":
                # ``from pyssp_workflow import fixture`` names a submodule.
                for alias in node.names:
                    candidate = SRC / alias.name
                    if candidate.with_suffix(".py").exists() or candidate.is_dir():
                        names.append(f"{node.module}.{alias.name}")
    return names


def _walk():
    for path in sorted(SRC.rglob("*.py")):
        yield path, _module_name(path), _imports(path)


def test_every_internal_layer_is_in_the_dependency_table():
    layers = {_layer(module) for _path, module, _imports_ in _walk()} - {""}
    undeclared = sorted(layers - set(INTERNAL_DEPENDENCIES))
    assert not undeclared, (
        "an internal layer has no declared dependencies:\n" + "\n".join(undeclared)
    )


def test_internal_modules_only_import_from_their_allowed_layers():
    violations = []
    for _path, module, imports in _walk():
        layer = _layer(module)
        allowed = INTERNAL_DEPENDENCIES.get(layer, frozenset())
        for name in imports:
            target = _internal_layer(name)
            if target is None or target in ("", layer):
                continue
            if target not in allowed:
                violations.append(f"{module} (layer {layer or 'package'}) imports {name}")
    assert not violations, (
        "an internal module imported a layer it must not depend on:\n"
        + "\n".join(violations)
    )


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


def test_judgment_is_only_reachable_from_the_node_layer():
    violations = [
        f"{module} imports {name}"
        for _path, module, imports in _walk()
        if _layer(module) not in JUDGE_ALLOWED
        for name in imports
        if name.startswith("pyssp_vv.judge")
    ]
    assert not violations, (
        "a module outside the node layer decides acceptability:\n" + "\n".join(violations)
    )


def test_compare_composes_measurement_without_reaching_judgment():
    violations = [
        f"{module} imports {name}"
        for _path, module, imports in _walk()
        if _layer(module) == "compare"
        for name in imports
        if name.startswith("pyssp_vv") and name not in COMPARE_MAY_IMPORT
    ]
    assert not violations, (
        "the comparison layer imported a V&V module it must not compose:\n"
        + "\n".join(violations)
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
