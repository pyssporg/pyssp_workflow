"""Bind a scenario SSV to a built SSP in one of four placements.

``mode`` places the set externally or inline; ``mapping`` keeps SSV member names
(``attach``) or resolves them to SSP target names (``flatten``). All assembly is
delegated to :meth:`pyssp_standard.SSP.bind_parameters`; this module keeps the
workflow policy: allowed combinations, the root-binding and target-SSD gates,
and the per-component filtering. Values keep their SSV type, the SSV and SSM
are read-only inputs, and only ``build.model_dir`` is mutated.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pyssp_standard import SSM, SSP, SSV, Parameter

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

    ``set_name`` overrides the SSV's own name; only ``build.model_dir`` is mutated.
    """
    if components is not None and mode != "inline":
        raise ValueError("components is only valid with mode='inline'")
    if components is not None and mapping != "flatten":
        raise ValueError("components is only valid with mapping='flatten'")

    root = build.model_dir
    if not root.is_dir():
        raise NotADirectoryError(f"Exported SSP root is not a directory: {root}")
    if build.descriptor.target_ssd != "SystemStructure.ssd":
        raise ValueError(
            "pyssp_standard.SSP.bind_parameters edits "
            f"SystemStructure.ssd, not '{build.descriptor.target_ssd}'"
        )
    if mode == "inline" and mapping == "attach" and ssm is None:
        raise ValueError(f"Study scenario '{ssv}' names no scenario SSM")

    with SSV(ssv, mode="r") as document:
        name = set_name if set_name is not None else document.name or ssv.stem
        values = document.parameters_by_name()
        # Raw list length: duplicates stay in an attached SSV, while
        # ``parameters_by_name`` would collapse them.
        parameter_count = len(document.xml.parameters)

    if components is not None:
        return _bind_components(root, ssm, name, values, components)

    with SSP(root, mode="a") as ssp:
        if mapping == "attach":
            with ssp.system_structure() as ssd:
                if ssd.system is None:
                    raise ValueError(f"Runtime SSD has no system: {ssd.path}")
                if ssd.system.parameter_bindings:
                    raise ValueError(
                        f"Exported SSP already has root parameter bindings: {ssd.path}"
                    )
        binding = ssp.bind_parameters(
            ssv, mapping=ssm, placement=mode,
            resolve_mapping=mapping == "flatten", name=set_name,
        )

    if mapping == "flatten" and ssm is not None:
        # The written set holds the mapping targets rather than the source names.
        with SSM(ssm, mode="r") as document:
            parameter_count = len(document.resolve(values))

    reference = binding.parameter_mapping
    return BindingResult(
        ssp=root,
        mode=mode,
        mapping=mapping,
        parameter_set=name,
        ssv_resource=_resource_name(binding.source),
        ssm_resource=_resource_name(reference.source if reference else None),
        components=(),
        parameters=parameter_count,
    )


def _bind_components(
    root: Path,
    ssm: Path | None,
    name: str,
    values: dict[str, Parameter],
    components: frozenset[str],
) -> BindingResult:
    """Resolve once, keep the listed component prefixes, bind each component."""
    targets = values
    if ssm is not None:
        with SSM(ssm, mode="r") as mapping:
            targets = mapping.resolve(values)

    grouped: dict[str, dict[str, Parameter]] = {}
    for target, parameter in targets.items():
        component, _, parameter_name = target.rpartition(".")
        if component in components:
            grouped.setdefault(component, {})[parameter_name] = parameter.renamed(
                parameter_name
            )

    with SSP(root, mode="a") as ssp:
        for component in sorted(grouped):
            ssp.bind_parameters(grouped[component], target=component, placement="inline")

    return BindingResult(
        ssp=root,
        mode="inline",
        mapping="flatten",
        parameter_set=name,
        ssv_resource=None,
        ssm_resource=None,
        components=tuple(sorted(grouped)),
        parameters=sum(len(group) for group in grouped.values()),
    )


def _resource_name(source: str | None) -> str | None:
    """The bare resource name behind a binding reference, if there is one."""
    return Path(source).name if source is not None else None


__all__ = ["BindingResult", "bind"]
