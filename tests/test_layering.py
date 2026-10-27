"""Import-graph rules that keep this package a composition layer."""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "pyssp_workflow"
PROJECT = Path(__file__).resolve().parents[1]
TESTS = PROJECT / "tests"

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

#: Raw document fields that the SSD facade replaces with a neutral read path.
FORBIDDEN_XML_FIELDS = ("xml.system", "xml.version")


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


def _import_sites(path: Path) -> list[tuple[str, int]]:
    """Every imported module name with the line it appears on.

    Relative imports keep their leading dots; ``from pyssp_workflow import
    fixture`` also names the submodule it imports.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    sites: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            sites.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level
            if node.module:
                sites.append((prefix + node.module, node.lineno))
                if node.module == "pyssp_workflow":
                    # ``from pyssp_workflow import fixture`` names a submodule.
                    for alias in node.names:
                        candidate = SRC / alias.name
                        if candidate.with_suffix(".py").exists() or candidate.is_dir():
                            sites.append((f"{node.module}.{alias.name}", node.lineno))
            elif node.level:
                sites.extend(
                    (prefix + alias.name, node.lineno)
                    for alias in node.names
                    if alias.name == "pyssp_standard"
                    or alias.name.startswith("pyssp_standard.")
                )
    return sites


def _imports(path: Path) -> list[str]:
    return [name for name, _line in _import_sites(path)]


def _walk():
    for path in sorted(SRC.rglob("*.py")):
        yield path, _module_name(path), _imports(path)


def _pyssp_standard_submodule_sites(path: Path) -> list[str]:
    """Import sites that reach past the ``pyssp_standard`` public surface."""
    violations: list[str] = []
    for name, line in _import_sites(path):
        target = name.lstrip(".")
        if target.startswith("pyssp_standard.") or (
            name.startswith(".") and target == "pyssp_standard"
        ):
            violations.append(f"{path.relative_to(PROJECT)}:{line} imports {name}")
    return violations


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


def test_pyssp_standard_is_only_imported_through_its_public_surface():
    violations = [
        violation
        for root in (SRC, TESTS)
        for path in sorted(root.rglob("*.py"))
        for violation in _pyssp_standard_submodule_sites(path)
    ]
    assert not violations, (
        "a module imported a pyssp_standard submodule instead of the package "
        "top level:\n" + "\n".join(violations)
    )


def test_the_ssd_tree_is_read_through_the_facade():
    # The rule module names the forbidden fields itself.
    this_file = Path(__file__).resolve()
    violations = [
        f"{path.relative_to(PROJECT)}:{number} uses {field}"
        for root in (SRC, TESTS)
        for path in sorted(root.rglob("*.py"))
        if path.resolve() != this_file
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        )
        for field in FORBIDDEN_XML_FIELDS
        if field in line
    ]
    assert not violations, (
        "a module reached past the SSD facade into the raw document:\n"
        + "\n".join(violations)
    )
