"""Bind a scenario SSV to a built SSP in one of four placements.

``mode`` chooses where the parameter set lives and ``mapping`` chooses whether
the scenario keeps its SSV member names or is resolved to SSP target names
through the SSM:

- ``external``/``attach``: copy the SSV and, when given, the SSM into
  ``resources/`` and add an external root set that references the mapping.
- ``external``/``flatten``: generate ``<set_name>.ssv`` keyed by target name
  and add it as an external root set; no SSM is attached.
- ``inline``/``attach``: write the SSV member names as one inline root set,
  attach the SSM as a resource and point the set at its mapping.
- ``inline``/``flatten``: write one inline root set keyed by target name, or
  per-component sets when ``components`` is given.

The SSV and SSM are standardized interchange artifacts and read-only inputs.
Only ``build.model_dir`` is mutated, so the built SSP is self-contained and
runnable.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pyssp_standard import SSM, SSP, SSV, ParameterMappingReference

from pyssp_workflow.fixture import BuiltFixture


@dataclass(frozen=True)
class BindingResult:
    """The binding written to ``ssp`` and where its inputs ended up."""

    ssp: Path
    mode: Literal["external", "inline"]
    mapping: Literal["attach", "flatten"]
    parameter_set: str
    ssv_resource: str | None
    ssm_resource: str | None
    components: tuple[str, ...]
    parameters: int


def bind(
    build: BuiltFixture,
    ssv: Path,
    *,
    set_name: str | None = None,
    mode: Literal["external", "inline"] = "external",
    ssm: Path | None = None,
    mapping: Literal["attach", "flatten"] = "attach",
    components: frozenset[str] | None = None,
) -> BindingResult:
    """Write one parameter binding to the built SSP and report what was written.

    ``ssv`` is read once for its values and default name; ``set_name`` overrides
    that name. ``ssm`` is read only when ``mapping="flatten"`` resolves member
    names to targets. Only ``build.model_dir`` is mutated.
    """
    if components is not None and mode != "inline":
        raise ValueError("components is only valid with mode='inline'")
    if components is not None and mapping != "flatten":
        raise ValueError("components is only valid with mapping='flatten'")

    default_name, values = _read_ssv(ssv)
    name = set_name if set_name is not None else default_name

    if mode == "external":
        if mapping == "attach":
            return _external_attach(build, ssv, ssm, name, values)
        return _external_flatten(build, ssm, name, values)
    if mapping == "attach":
        if ssm is None:
            raise ValueError(f"Study scenario '{ssv}' names no scenario SSM")
        return _inline_attach(build, ssm, name, values)
    return _inline_flatten(build, ssm, name, values, components)


def _read_ssv(path: Path) -> tuple[str, dict[str, float]]:
    """The SSV's default set name and its values, read once."""
    with SSV(path, mode="r") as ssv:
        values = {
            parameter.name: float(parameter.attributes["value"])
            for parameter in ssv.xml.parameters
        }
        name = ssv.xml.name or path.stem
    return name, values


def _read_mappings(path: Path) -> tuple[tuple[str, str], ...]:
    """The SSM's ``(member, target)`` pairs, read once."""
    with SSM(path, mode="r") as ssm:
        return tuple((mapping.source, mapping.target) for mapping in ssm.xml.mappings)


def _targets(values: dict[str, float], ssm: Path | None) -> dict[str, float]:
    """Values keyed by target name; identity when there is no SSM."""
    if ssm is None:
        return dict(values)
    return {
        target: values[source]
        for source, target in _read_mappings(ssm)
    }


def _external_attach(
    build: BuiltFixture,
    ssv: Path,
    ssm: Path | None,
    name: str,
    values: dict[str, float],
) -> BindingResult:
    root = build.model_dir
    descriptor = build.descriptor
    if not root.is_dir():
        raise NotADirectoryError(f"Exported SSP root is not a directory: {root}")
    if descriptor.target_ssd != "SystemStructure.ssd":
        raise ValueError(
            "pyssp_standard.SSP.add_external_parameterset targets "
            f"SystemStructure.ssd, not '{descriptor.target_ssd}'"
        )
    ssm_resource = ssm.name if ssm is not None else None

    with SSP(root, mode="a") as ssp:
        with ssp.system_structure() as ssd:
            system = ssd.xml.system
            if system is None:
                raise ValueError(f"Runtime SSD has no system: {ssd.path}")
            if system.parameter_bindings:
                raise ValueError(
                    f"Exported SSP already has root parameter bindings: {ssd.path}"
                )
        ssp.add_external_parameterset(
            ssv,
            mapping_path=ssm,
            resource_name=ssv.name,
            mapping_resource_name=ssm_resource,
        )

    return BindingResult(
        ssp=root,
        mode="external",
        mapping="attach",
        parameter_set=name,
        ssv_resource=ssv.name,
        ssm_resource=ssm_resource,
        components=(),
        parameters=len(values),
    )


def _external_flatten(
    build: BuiltFixture,
    ssm: Path | None,
    name: str,
    values: dict[str, float],
) -> BindingResult:
    targets = _targets(values, ssm)
    with tempfile.TemporaryDirectory(prefix=f"{name}_") as temp_dir:
        ssv_path = Path(temp_dir) / f"{name}.ssv"
        with SSV(ssv_path, mode="w") as ssv:
            ssv.xml.name = name
            for target, value in targets.items():
                ssv.xml.add_parameter(parname=target, ptype="Real", value=value)
        with SSP(build.model_dir, mode="a") as ssp:
            ssp.add_external_parameterset(ssv_path)

    return BindingResult(
        ssp=build.model_dir,
        mode="external",
        mapping="flatten",
        parameter_set=name,
        ssv_resource=f"{name}.ssv",
        ssm_resource=None,
        components=(),
        parameters=len(targets),
    )


def _inline_attach(
    build: BuiltFixture,
    ssm: Path,
    name: str,
    values: dict[str, float],
) -> BindingResult:
    mapping_name = ssm.name
    with SSP(build.model_dir, mode="a") as ssp:
        with ssp.system_structure() as ssd:
            ssd.extend_system_parameterset(values, binding_name=name)
            binding = next(
                candidate
                for candidate in ssd.xml.system.parameter_bindings
                if candidate.source is None and candidate.parameter_set is not None
            )
            binding.parameter_mapping = ParameterMappingReference(
                source=f"resources/{mapping_name}"
            )
        ssp.add_resource(ssm)

    return BindingResult(
        ssp=build.model_dir,
        mode="inline",
        mapping="attach",
        parameter_set=name,
        ssv_resource=None,
        ssm_resource=mapping_name,
        components=(),
        parameters=len(values),
    )


def _resolve_system(root_system, path_parts: list[str]):
    system = root_system
    for name in path_parts:
        element = next(
            (candidate for candidate in system.elements if candidate.name == name),
            None,
        )
        if element is None:
            raise KeyError(f"No element '{name}' under '{system.name}'")
        system = element
    return system


def _inline_flatten(
    build: BuiltFixture,
    ssm: Path | None,
    name: str,
    values: dict[str, float],
    components: frozenset[str] | None,
) -> BindingResult:
    targets = _targets(values, ssm)
    if components is None:
        with SSP(build.model_dir, mode="a") as ssp:
            with ssp.system_structure() as ssd:
                ssd.extend_system_parameterset(targets, binding_name=name)
        return BindingResult(
            ssp=build.model_dir,
            mode="inline",
            mapping="flatten",
            parameter_set=name,
            ssv_resource=None,
            ssm_resource=None,
            components=(),
            parameters=len(targets),
        )

    written: set[str] = set()
    parameters = 0
    with SSP(build.model_dir, mode="a") as ssp:
        with ssp.system_structure() as ssd:
            root = ssd.xml.system
            for target, value in targets.items():
                *component_path, parameter = target.split(".")
                component_name = ".".join(component_path)
                if component_name not in components:
                    continue
                component = _resolve_system(root, component_path)
                component.extend_inline_parameterset({parameter: value})
                written.add(component_name)
                parameters += 1

    return BindingResult(
        ssp=build.model_dir,
        mode="inline",
        mapping="flatten",
        parameter_set=name,
        ssv_resource=None,
        ssm_resource=None,
        components=tuple(sorted(written)),
        parameters=parameters,
    )


__all__ = ["BindingResult", "bind"]
