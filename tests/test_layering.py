"""Import-graph rules that keep this package a composition layer."""

from __future__ import annotations

import ast
import textwrap
from collections.abc import Iterable
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


def _resolve_relative(module: str, path: Path, level: int, target: str) -> str:
    """Resolve a relative import target against the importing module's package."""
    package = module if path.name == "__init__.py" else module.rpartition(".")[0]
    parts = package.split(".") if package else []
    drop = level - 1
    if drop:
        parts = parts[:-drop] if drop <= len(parts) else []
    if target:
        parts.extend(target.split("."))
    return ".".join(part for part in parts if part)


def _submodule(base: str, name: str) -> str | None:
    """``base.name`` when that internal module exists, so the layer is visible."""
    if base != "pyssp_workflow" and not base.startswith("pyssp_workflow."):
        return None
    candidate = SRC.joinpath(*base.split(".")[1:], name)
    if candidate.with_suffix(".py").exists() or candidate.is_dir():
        return f"{base}.{name}"
    return None


def _dynamic_import(node: ast.Call) -> str | None:
    """The literal name handed to ``importlib.import_module`` / ``__import__``."""
    func = node.func
    if isinstance(func, ast.Name):
        if func.id not in ("__import__", "import_module"):
            return None
    elif isinstance(func, ast.Attribute):
        if func.attr != "import_module":
            return None
    else:
        return None
    if not node.args:
        return None
    argument = node.args[0]
    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
        return argument.value
    return None


def _import_sites(path: Path, module: str | None = None) -> list[tuple[str, int]]:
    """Every imported module name with the line it appears on.

    Relative imports are resolved against the importing module's package and
    literal arguments of ``importlib.import_module`` / ``__import__`` count as
    imports, so neither form can slip past the rules.
    """
    try:
        module = module or _module_name(path)
    except ValueError:  # a test module lives outside the package
        module = ""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    sites: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            sites.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                base = _resolve_relative(module, path, node.level, base)
            if base:
                sites.append((base, node.lineno))
            for alias in node.names:
                imported = _submodule(base, alias.name) if alias.name != "*" else None
                if imported:
                    sites.append((imported, node.lineno))
        elif isinstance(node, ast.Call):
            target = _dynamic_import(node)
            if target is not None:
                sites.append((target, node.lineno))
    return sites


def _imports(path: Path, module: str | None = None) -> list[str]:
    return [name for name, _line in _import_sites(path, module)]


def _walk():
    for path in sorted(SRC.rglob("*.py")):
        yield path, _module_name(path), _imports(path)


def _layer_violations(entries: Iterable[tuple[str, Iterable[str]]]) -> list[str]:
    violations: list[str] = []
    for module, imports in entries:
        layer = _layer(module)
        allowed = INTERNAL_DEPENDENCIES.get(layer, frozenset())
        for name in imports:
            target = _internal_layer(name)
            if target is None or target in ("", layer):
                continue
            if target not in allowed:
                violations.append(f"{module} (layer {layer or 'package'}) imports {name}")
    return violations


def _flow_violations(entries: Iterable[tuple[str, Iterable[str]]]) -> list[str]:
    return [
        f"{module} imports {name}"
        for module, imports in entries
        for name in imports
        if name.split(".")[0] == "sequence_extensions" and _layer(module) != FLOW_LAYER
    ]


def _judgment_violations(entries: Iterable[tuple[str, Iterable[str]]]) -> list[str]:
    return [
        f"{module} imports {name}"
        for module, imports in entries
        if _layer(module) not in JUDGE_ALLOWED
        for name in imports
        if name.startswith("pyssp_vv.judge")
    ]


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
    violations = _layer_violations(
        (module, imports) for _path, module, imports in _walk()
    )
    assert not violations, (
        "an internal module imported a layer it must not depend on:\n"
        + "\n".join(violations)
    )


def test_flow_engine_is_confined_to_the_node_layer():
    violations = _flow_violations((module, imports) for _path, module, imports in _walk())
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
    violations = _judgment_violations(
        (module, imports) for _path, module, imports in _walk()
    )
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


def _probe(tmp_path: Path, source: str, *, module: str) -> list[str]:
    """Import names of a synthetic module, resolved as if it lived in ``module``."""
    path = tmp_path.joinpath(*module.split(".")).with_suffix(".py")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    return _imports(path, module)


def test_relative_imports_are_resolved_against_the_importing_package(tmp_path: Path):
    imports = _probe(
        tmp_path,
        """
        from .. import compare
        from ..compare import compare_csvs
        from ..nodes import evidence
        """,
        module="pyssp_workflow.authoring._probe",
    )

    assert "pyssp_workflow.compare" in imports
    assert "pyssp_workflow.nodes" in imports
    assert "pyssp_workflow.nodes.evidence" in imports
    # The layer table now sees the bypass: authoring may not import compare.
    assert _layer_violations([("pyssp_workflow.authoring._probe", imports)])


def test_a_relative_import_of_a_forbidden_layer_fails_the_rule(tmp_path: Path):
    imports = _probe(
        tmp_path,
        "from ..compare import compare_csvs\n",
        module="pyssp_workflow.authoring._probe",
    )

    violations = _layer_violations([("pyssp_workflow.authoring._probe", imports)])

    assert len(violations) == 1
    assert "pyssp_workflow.compare" in violations[0]


def test_a_dynamic_judgment_import_fails_the_judgment_rule(tmp_path: Path):
    imports = _probe(
        tmp_path,
        """
        import importlib
        importlib.import_module("pyssp_vv.judge")
        """,
        module="pyssp_workflow.compare._probe",
    )

    violations = _judgment_violations([("pyssp_workflow.compare._probe", imports)])

    assert violations == ["pyssp_workflow.compare._probe imports pyssp_vv.judge"]


def test_a_dunder_import_of_the_flow_engine_fails_the_confinement_rule(tmp_path: Path):
    imports = _probe(
        tmp_path,
        '__import__("sequence_extensions.flow")\n',
        module="pyssp_workflow.compare._probe",
    )

    violations = _flow_violations([("pyssp_workflow.compare._probe", imports)])

    assert violations == [
        "pyssp_workflow.compare._probe imports sequence_extensions.flow"
    ]
