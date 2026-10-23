"""Apply a study scenario to a built SSP as one root or component binding.

The study SSV and SSM are the standardized interchange artifacts. Packaging
copies them into the built SSP and adds parameter bindings, so the build output
is a self-contained, runnable SSP. The scenario SSV and SSM are never rewritten.

``apply_external_ssv_ssm`` is the external SSV+SSM form that a study descriptor
names. The other forms are the remaining SSP parameter-binding shapes a fixture
may choose: one inline root set, an external SSV keyed by the mapped target
names, an inline set with an external SSM resource, and per-component inline
sets. Every form mutates the built SSP through ``pyssp_standard``; this module
only decides which binding gets written.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from pyssp_standard import SSP, SSV, ParameterMappingReference

from pyssp_workflow.authoring import FixtureBuild
from pyssp_workflow.params import scenario_targets, scenario_values


def apply_external_ssv_ssm(build: FixtureBuild) -> None:
    """Package the descriptor's standard SSV/SSM into the built SSP root.

    The built SSP is the artifact being produced, not an input; it is modified
    in place. Raises ``ValueError`` when the descriptor names no scenario SSV.
    """
    root = build.model_dir
    descriptor = build.descriptor
    if descriptor.ssv_path is None:
        raise ValueError(f"Study descriptor '{descriptor.path}' names no scenario SSV")
    ssv_path = descriptor.ssv_path
    ssm_path = descriptor.ssm_path
    if not root.is_dir():
        raise NotADirectoryError(f"Exported SSP root is not a directory: {root}")
    if descriptor.target_ssd != "SystemStructure.ssd":
        raise ValueError(
            "pyssp_standard.SSP.add_external_parameterset targets "
            f"SystemStructure.ssd, not '{descriptor.target_ssd}'"
        )

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
            ssv_path,
            mapping_path=ssm_path,
            resource_name=ssv_path.name,
            mapping_resource_name=ssm_path.name if ssm_path is not None else None,
        )


def apply_inline_root(build: FixtureBuild) -> None:
    """Apply the scenario as one inline root parameter set keyed by target name.

    The built SSP is the artifact being produced, not an input; it is modified
    in place. Raises ``ValueError`` when the descriptor names no scenario.
    """
    descriptor = build.descriptor
    values = scenario_targets(descriptor)
    with SSP(Path(build.model_dir), mode="a") as ssp:
        with ssp.system_structure() as ssd:
            ssd.extend_system_parameterset(values, binding_name=descriptor.set_name)


def apply_target_named_external(build: FixtureBuild) -> None:
    """Apply the scenario as an external SSV whose names are the SSP targets.

    This is the no-mapping form: the parameter names are the hierarchical
    targets, so the binding needs no ``.ssm``. The built SSP is the artifact
    being produced, not an input; it is modified in place. Raises
    ``ValueError`` when the descriptor names no scenario.
    """
    descriptor = build.descriptor
    values = scenario_targets(descriptor)
    with tempfile.TemporaryDirectory(prefix=f"{descriptor.set_name}_") as temp_dir:
        ssv_path = Path(temp_dir) / f"{descriptor.set_name}.ssv"
        with SSV(ssv_path, mode="w") as ssv:
            ssv.xml.name = descriptor.set_name
            for name, value in values.items():
                ssv.xml.add_parameter(parname=name, ptype="Real", value=value)
        with SSP(Path(build.model_dir), mode="a") as ssp:
            ssp.add_external_parameterset(ssv_path)


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


def apply_inline_components(
    build: FixtureBuild,
    *,
    only: set[str] | None = None,
) -> None:
    """Apply the scenario as inline parameter sets on the mapped components.

    Each mapped target is ``<component path>.<parameter>``; the component path
    may cross nested systems. ``only`` limits application to the given
    component paths. The built SSP is the artifact being produced, not an
    input; it is modified in place. Raises ``ValueError`` when the descriptor
    names no scenario and ``KeyError`` for a component path the SSP does not
    contain.
    """
    targets = scenario_targets(build.descriptor)
    with SSP(Path(build.model_dir), mode="a") as ssp:
        with ssp.system_structure() as ssd:
            root = ssd.xml.system
            for target, value in targets.items():
                *component_path, parameter = target.split(".")
                component_name = ".".join(component_path)
                if only is not None and component_name not in only:
                    continue
                component = _resolve_system(root, component_path)
                component.extend_inline_parameterset({parameter: value})


def apply_inline_with_mapping(build: FixtureBuild) -> None:
    """Apply the scenario inline, with an external SSM resource for the mapping.

    The built SSP is the artifact being produced, not an input; it is modified
    in place. Raises ``ValueError`` when the descriptor names no scenario or no
    SSM.
    """
    descriptor = build.descriptor
    values = scenario_values(descriptor)
    if descriptor.ssm_path is None:
        raise ValueError(
            f"Study descriptor '{descriptor.path}' names no scenario SSM"
        )
    mapping_name = descriptor.ssm_path.name
    with SSP(Path(build.model_dir), mode="a") as ssp:
        with ssp.system_structure() as ssd:
            ssd.extend_system_parameterset(values, binding_name=descriptor.set_name)
            binding = next(
                candidate
                for candidate in ssd.xml.system.parameter_bindings
                if candidate.source is None and candidate.parameter_set is not None
            )
            binding.parameter_mapping = ParameterMappingReference(
                source=f"resources/{mapping_name}"
            )
        ssp.add_resource(descriptor.ssm_path)


__all__ = [
    "apply_external_ssv_ssm",
    "apply_inline_components",
    "apply_inline_root",
    "apply_inline_with_mapping",
    "apply_target_named_external",
]
