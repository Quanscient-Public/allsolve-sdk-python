# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

"""
Export project data to a dictionary format compatible with import_project().

This module provides functionality to export project data including:
- Project metadata (name, description, dimension, labels)
- Variables and functions
- Geometries (CAD elements)
- Regions (basic, computed, region rules)
- Materials
- Physics (with nested interactions)
- Variable overrides
- Meshes
- Simulations (with output interactions)

Note:
    CAD file paths and shared file paths are exported as placeholders unless
    ``download_geometries=True`` is used (geometry CAD files only; see export_project_data).
    When re-importing without downloaded files, provide the actual files at those paths.
"""

from __future__ import annotations

import warnings
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict


from allsolve.util import FileOverwriteMode

from allsolve.geometry.cad_basic_geometry import (
    CadBox,
    CadCone,
    CadCylinder,
    CadDisk,
    CadRectangle,
    CadSphere,
    CadSurfaceRectangle,
    CadTorus,
)
from allsolve.geometry.cad_path import CadGlob
from allsolve.geometry.cad_boolean_operation import (
    CadDifference,
    CadFragmentAll,
    CadFragments,
    CadIntersection,
    CadUnion,
)
from allsolve.geometry.cad_file_import import (
    CadBrepFile,
    CadFileImport,
    CadGds2File,
    CadGdsExtrudeParameters,
    CadIgesFile,
    CadSatFile,
    CadStepFile,
)
from allsolve.geometry.cad_simple_operation import (
    CadGrid,
    CadRemove,
    CadRotate,
    CadTranslate,
)
from allsolve.physics.generated.registries import (
    get_interaction_parameter_defaults,
    get_output_parameter_defaults,
)
from allsolve.region import Region, RegionOperation
from allsolve.simulation import CPU, FieldInitialization

import allsolve_rawapi as rawapi

from allsolve.expression import Variable
from allsolve.physics.physic import Physic
from allsolve.project import Project
from allsolve.simulation import Simulation
from allsolve.export_format import (
    OUTPUT_PARAM_REVERSE as _OUTPUT_PARAM_REVERSE,
    OUTPUT_BOOL_ALIASES as _OUTPUT_BOOL_ALIASES,
)


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _tuple_to_dict(
    value: tuple[float | str, ...] | None, dimensions: int = 3
) -> dict | None:
    """Convert a tuple to a dictionary with x, y, z keys."""
    if value is None:
        return None
    if dimensions == 2:
        return {"x": value[0], "y": value[1]}
    return {"x": value[0], "y": value[1], "z": value[2]}


def _clean_dict(d: dict) -> dict:
    """Remove None values from a dictionary."""
    return {k: v for k, v in d.items() if v is not None}


def _build_id_to_name_map(
    items: list, id_attr: str = "id", name_attr: str = "name"
) -> dict[str, str]:
    """Build a mapping from item ID to item name."""
    return {getattr(item, id_attr): getattr(item, name_attr) for item in items}


def _topological_sort_variables(variables: list[Variable]) -> list[Variable]:
    """
    Topologically sort variables so that variables that depend on others come after them.

    This ensures that when re-importing, dependent variables are created after
    their dependencies.
    """
    # Build name to variable mapping
    name_to_var = {v.name: v for v in variables}
    var_names = set(name_to_var.keys())

    # Build dependency graph by parsing expressions
    # A variable depends on another if its expression contains the other's name
    dependencies: dict[str, set[str]] = defaultdict(set)

    for var in variables:
        expr = var.expression or ""
        # Check which other variable names appear in this expression
        for other_name in var_names:
            if other_name != var.name and other_name in expr:
                # This variable depends on other_name
                dependencies[var.name].add(other_name)

    # Kahn's algorithm for topological sort
    in_degree: dict[str, int] = {v.name: 0 for v in variables}
    for var_name, deps in dependencies.items():
        in_degree[var_name] = len(deps)

    # Start with variables that have no dependencies
    queue = [name for name, degree in in_degree.items() if degree == 0]
    sorted_vars = []

    while queue:
        current = queue.pop(0)
        sorted_vars.append(name_to_var[current])

        # Reduce in-degree for variables that depend on current
        for var_name, deps in dependencies.items():
            if current in deps:
                in_degree[var_name] -= 1
                if in_degree[var_name] == 0:
                    queue.append(var_name)

    # If we couldn't sort all variables, there's a cycle - just return original order
    if len(sorted_vars) != len(variables):
        return variables

    return sorted_vars


def _export_variables(project: Project) -> list[dict]:
    """Export all variables from a project."""
    variables = project.get_variables()
    sorted_variables = _topological_sort_variables(variables)

    result = []
    for var in sorted_variables:
        var_dict = {
            "name": var.name,
            "expression": var.expression,
        }
        if var.description:
            var_dict["description"] = var.description
        result.append(var_dict)

    return result


def _export_functions(project: Project) -> list[dict]:
    """Export all functions (regular and interpolated) from a project."""
    result = []

    # Export regular functions
    functions = project.get_functions()
    for func in functions:
        func_dict = {
            "name": func.name,
            "type": "regular",
            "args": [{"name": arg.name} for arg in (func.args or [])],
            "expression": func.expression,
        }
        if func.description:
            func_dict["description"] = func.description
        result.append(func_dict)

    # Export interpolated functions
    interp_functions = project.get_interpolated_functions()
    for func in interp_functions:
        func_dict = {
            "name": func.name,
            "type": "interpolated",
            "args": [
                {"name": arg.name, "values": arg.values} for arg in (func.args or [])
            ],
            "values": func.values,
        }
        if func.description:
            func_dict["description"] = func.description
        if func.cubic_interpolation is not None:
            func_dict["cubicInterpolation"] = func.cubic_interpolation
        result.append(func_dict)

    return result


def _entity_type_to_string(entity_type: Any) -> str:
    """Convert region entity type constant to string."""
    entity_type_map = {
        Region.VOLUME: "volume",
        Region.SURFACE: "surface",
        Region.CURVE: "curve",
        Region.POINT: "point",
    }
    result = entity_type_map.get(entity_type)
    if result is None:
        warnings.warn(
            f"Unknown region entity type {entity_type!r}, falling back to 'volume'",
            stacklevel=2,
        )
        return "volume"
    return result


def _operation_to_string(
    operation: "RegionOperation | rawapi.RegionRuleOperation",
) -> str:
    """Convert RegionOperation or rawapi.RegionRuleOperation to string."""
    if isinstance(operation, RegionOperation):
        operation = operation.value

    operation_map: dict[rawapi.RegionRuleOperation, str] = {
        rawapi.RegionRuleOperation.UNION: "union",
        rawapi.RegionRuleOperation.INTERSECTION: "intersection",
        rawapi.RegionRuleOperation.DIFFERENCE: "difference",
        rawapi.RegionRuleOperation.SYMMETRIC_DIFFERENCE: "symmetricDifference",
        rawapi.RegionRuleOperation.BOUNDARY: "boundary",
        rawapi.RegionRuleOperation.COMPLEMENT: "complement",
    }
    result = operation_map.get(operation)
    if result is None:
        warnings.warn(
            f"Unknown region operation {operation!r}, falling back to 'union'",
            stacklevel=2,
        )
        return "union"
    return result


def _get_region_sources(region: Region) -> list[str]:
    """Get source region IDs for a computed region."""
    raw_region = region._region
    region_rule = getattr(raw_region, "region_rule", None)
    if region_rule is None:
        return []
    return getattr(region_rule, "sources", []) or []


def _topological_sort_regions(
    regions: list[Region], id_to_name: dict[str, str]
) -> list[Region]:
    """
    Topologically sort regions so that computed regions come after their source regions.
    """
    # Build ID to region mapping
    id_to_region = {r.id: r for r in regions}

    # Build dependency graph for computed regions
    dependencies: dict[str, set[str]] = defaultdict(set)

    for region in regions:
        sources = _get_region_sources(region)
        for source_id in sources:
            if source_id in id_to_region:
                dependencies[region.id].add(source_id)

    # Kahn's algorithm for topological sort
    in_degree: dict[str, int] = {
        r.id: len(dependencies.get(r.id, set())) for r in regions
    }

    queue = [rid for rid, degree in in_degree.items() if degree == 0]
    sorted_regions = []

    while queue:
        current_id = queue.pop(0)
        sorted_regions.append(id_to_region[current_id])

        # Reduce in-degree for regions that depend on current
        for region_id, deps in dependencies.items():
            if current_id in deps:
                in_degree[region_id] -= 1
                if in_degree[region_id] == 0:
                    queue.append(region_id)

    # If we couldn't sort all regions, there's a cycle - just return original order
    if len(sorted_regions) != len(regions):
        return regions

    return sorted_regions


def _determine_region_type(region: Region) -> tuple[str, Any]:
    """
    Determine the type of a region from its raw data.

    Returns:
        Tuple of (type_string, region_rule_data or None)
    """
    # Access the raw region data
    raw_region = region._region
    region_rule = getattr(raw_region, "region_rule", None)

    if region_rule is None:
        return "basic", None

    operation = getattr(region_rule, "operation", None)
    if operation is None:
        return "basic", None

    if operation == rawapi.RegionRuleOperation.SELECTOR:
        return "regionRule", region_rule
    elif operation in (
        rawapi.RegionRuleOperation.UNION,
        rawapi.RegionRuleOperation.INTERSECTION,
        rawapi.RegionRuleOperation.DIFFERENCE,
        rawapi.RegionRuleOperation.SYMMETRIC_DIFFERENCE,
        rawapi.RegionRuleOperation.BOUNDARY,
        rawapi.RegionRuleOperation.COMPLEMENT,
    ):
        return "computed", region_rule

    return "basic", None


def _export_regions(project: Project) -> tuple[list[dict], dict[str, str]]:
    """
    Export all regions from a project.

    Returns:
        Tuple of (list of region dicts, id_to_name mapping)
    """
    regions = project.get_regions()
    id_to_name = _build_id_to_name_map(regions)

    # Sort regions so computed regions come after their dependencies
    sorted_regions = _topological_sort_regions(regions, id_to_name)

    result = []
    for region in sorted_regions:
        region_type, region_rule = _determine_region_type(region)

        region_dict: dict[str, Any] = {
            "name": region.name,
            "entityType": _entity_type_to_string(region.entity_type),
        }

        if not region.shared:
            region_dict["shared"] = False

        if region_type == "basic":
            region_dict["type"] = "basic"
            region_dict["entityTags"] = (
                list(region.entity_tags) if region.entity_tags else []
            )
            result.append(region_dict)

        elif region_type == "regionRule" and region_rule is not None:
            selector = getattr(region_rule, "selector", None)

            if selector:
                attr_path = getattr(selector, "attribute_path", None)
                attr_items = (
                    getattr(attr_path, "path", None) if attr_path is not None else None
                )
                has_attribute_path = bool(attr_items)
                region_dict["type"] = (
                    "regionRule" if has_attribute_path else "geometrySelector"
                )

                if attr_items:
                    region_dict["attributePath"] = [
                        {"key": item.name, "value": item.value} for item in attr_items
                    ]

                bounding_box = getattr(selector, "bounding_box", None)
                if bounding_box:
                    region_dict["boundingBox"] = {
                        "min": {
                            "x": bounding_box.min.x,
                            "y": bounding_box.min.y,
                            "z": bounding_box.min.z,
                        },
                        "max": {
                            "x": bounding_box.max.x,
                            "y": bounding_box.max.y,
                            "z": bounding_box.max.z,
                        },
                    }
                max_size = getattr(selector, "max_size", None)
                if max_size:
                    region_dict["maxSize"] = {
                        "x": max_size.x,
                        "y": max_size.y,
                        "z": max_size.z,
                    }
                min_size = getattr(selector, "min_size", None)
                if min_size:
                    region_dict["minSize"] = {
                        "x": min_size.x,
                        "y": min_size.y,
                        "z": min_size.z,
                    }
            else:
                region_dict["type"] = "regionRule"
                region_dict["attributePath"] = []

            result.append(region_dict)

        elif region_type == "computed" and region_rule is not None:
            sources = getattr(region_rule, "sources", []) or []
            source_names = [id_to_name.get(sid, sid) for sid in sources]

            region_dict["type"] = "computed"
            region_dict["operation"] = _operation_to_string(region_rule.operation)
            region_dict["regions"] = source_names
            result.append(region_dict)

        else:
            # Fallback to basic
            region_dict["type"] = "basic"
            region_dict["entityTags"] = (
                list(region.entity_tags) if region.entity_tags else []
            )
            result.append(region_dict)

    return result, id_to_name


def _export_gds_extrude_parameters(
    ep: CadGdsExtrudeParameters,
) -> dict[str, Any]:
    """Export CadGdsExtrudeParameters to a dictionary."""
    result: dict[str, Any] = {}
    if ep.unify_layer_discretizations is not None:
        result["unifyLayerDiscretizations"] = ep.unify_layer_discretizations.value
    if ep.fuzzy_value is not None:
        result["fuzzyValue"] = ep.fuzzy_value
    if ep.feature_angle_threshold is not None:
        result["featureAngleThreshold"] = ep.feature_angle_threshold
    if ep.length_ratio_threshold is not None:
        result["lengthRatioThreshold"] = ep.length_ratio_threshold
    if ep.circle_max_arc_angle_per_segment is not None:
        result["circleMaxArcAnglePerSegment"] = ep.circle_max_arc_angle_per_segment
    if ep.circle_fit_tolerance_fraction is not None:
        result["circleFitToleranceFraction"] = ep.circle_fit_tolerance_fraction
    if ep.spline_method is not None:
        result["splineMethod"] = ep.spline_method.value
    if ep.spline_tolerance is not None:
        result["splineTolerance"] = ep.spline_tolerance
    if ep.iterative_max_iterations is not None:
        result["iterativeMaxIterations"] = ep.iterative_max_iterations
    return result


def _export_cad_point(point) -> dict | None:
    """Export a CadPoint to dictionary."""
    if point is None:
        return None
    if point.tag is not None:
        return {"tag": point.tag}
    if point.name is not None:
        return {"name": point.name}
    return None


def _export_cad_path(path: list | None) -> list | None:
    """Export a CadPath to a YAML-serializable list of segments."""
    if path is None:
        return None
    result: list = []
    for segment in path:
        if isinstance(segment, CadGlob):
            result.append("*" if segment == CadGlob.STAR else "**")
        elif isinstance(segment, tuple):
            result.append({"key": segment[0], "value": segment[1]})
        else:
            result.append(segment)
    return result


def _apply_geometry_file_download(
    elem: CadFileImport,
    geo_dict: dict[str, Any],
    out_dir: Path,
    downloaded_basenames: set[str],
    preexisting_skip_printed: set[str],
    file_overwrite_mode: FileOverwriteMode = FileOverwriteMode.SKIP,
) -> None:
    """
    Optionally download CAD file import geometry into out_dir (flat layout).

    See export_project_data(..., download_geometries=True) for rules on duplicates
    and pre-existing files on disk.
    """
    basename = Path(elem.filepath).name
    rel_fp = basename
    target = out_dir / basename

    if basename in downloaded_basenames:
        geo_dict["filepath"] = rel_fp
        return

    if target.exists():
        if file_overwrite_mode is FileOverwriteMode.ERROR:
            raise FileExistsError(
                f"File already exists: {target}. "
                "Use file_overwrite_mode=FileOverwriteMode.OVERWRITE to replace "
                "or FileOverwriteMode.SKIP to skip."
            )
        if file_overwrite_mode is FileOverwriteMode.SKIP:
            if basename not in preexisting_skip_printed:
                print(
                    "allsolve export: skipping geometry download for "
                    f"'{elem.name}' ({basename!r}): file already exists at {target}"
                )
                preexisting_skip_printed.add(basename)
            geo_dict["filepath"] = rel_fp
            return

    elem.download(output_dir=str(out_dir))
    downloaded_basenames.add(basename)
    geo_dict["filepath"] = rel_fp


def _export_geometries(
    project: Project,
    *,
    download_geometries: bool = False,
    files_output_dir: Path | None = None,
    file_overwrite_mode: FileOverwriteMode = FileOverwriteMode.SKIP,
) -> list[dict]:
    """Export all CAD geometries from a project."""
    result: list[dict[str, Any]] = []
    try:
        geometry_builder = project.geometry_builder()
    except ValueError:
        return result
    elements = geometry_builder.get_elements()

    downloaded_basenames: set[str] = set()
    preexisting_skip_printed: set[str] = set()
    out_dir = (
        files_output_dir
        if download_geometries and files_output_dir is not None
        else None
    )

    for elem in elements:
        geo_dict: dict[str, Any] = {"name": elem.name}

        # Check enabled state
        if elem.enabled is not None and elem.enabled is not True:
            geo_dict["enabled"] = elem.enabled

        if isinstance(elem, CadBox):
            geo_dict["type"] = "box"
            geo_dict["position"] = _tuple_to_dict(elem.position)
            geo_dict["size"] = _tuple_to_dict(elem.size)
            if elem.rotation:
                geo_dict["rotation"] = _tuple_to_dict(elem.rotation)
            if elem.alignment:
                geo_dict["alignment"] = elem.alignment.value

        elif isinstance(elem, CadCylinder):
            geo_dict["type"] = "cylinder"
            geo_dict["position"] = _tuple_to_dict(elem.position)
            geo_dict["axis"] = _tuple_to_dict(elem.axis)
            geo_dict["radius"] = elem.radius
            if elem.inner_radius is not None:
                geo_dict["innerRadius"] = elem.inner_radius
            if elem.angle1:
                geo_dict["angle1"] = elem.angle1
            if elem.angle2:
                geo_dict["angle2"] = elem.angle2
            if elem.rotation:
                geo_dict["rotation"] = _tuple_to_dict(elem.rotation)
            if elem.alignment:
                geo_dict["alignment"] = elem.alignment.value

        elif isinstance(elem, CadSphere):
            geo_dict["type"] = "sphere"
            geo_dict["position"] = _tuple_to_dict(elem.position)
            geo_dict["radius"] = elem.radius
            if elem.inner_radius is not None:
                geo_dict["innerRadius"] = elem.inner_radius
            if elem.angle1:
                geo_dict["angle1"] = elem.angle1
            if elem.angle2:
                geo_dict["angle2"] = elem.angle2
            if elem.rotation:
                geo_dict["rotation"] = _tuple_to_dict(elem.rotation)

        elif isinstance(elem, CadCone):
            geo_dict["type"] = "cone"
            geo_dict["position"] = _tuple_to_dict(elem.position)
            geo_dict["axis"] = _tuple_to_dict(elem.axis)
            geo_dict["radius1"] = elem.radius1
            geo_dict["radius2"] = elem.radius2
            if elem.angle1:
                geo_dict["angle1"] = elem.angle1
            if elem.angle2:
                geo_dict["angle2"] = elem.angle2
            if elem.rotation:
                geo_dict["rotation"] = _tuple_to_dict(elem.rotation)
            if elem.alignment:
                geo_dict["alignment"] = elem.alignment.value

        elif isinstance(elem, CadTorus):
            geo_dict["type"] = "torus"
            geo_dict["position"] = _tuple_to_dict(elem.position)
            geo_dict["radius1"] = elem.radius1
            geo_dict["radius2"] = elem.radius2
            if elem.inner_radius is not None:
                geo_dict["innerRadius"] = elem.inner_radius
            if elem.angle1:
                geo_dict["angle1"] = elem.angle1
            if elem.angle2:
                geo_dict["angle2"] = elem.angle2
            if elem.rotation:
                geo_dict["rotation"] = _tuple_to_dict(elem.rotation)

        elif isinstance(elem, CadDisk):
            geo_dict["type"] = "disk"
            geo_dict["position"] = _tuple_to_dict(elem.position, dimensions=2)
            geo_dict["radius"] = elem.radius
            if elem.inner_radius is not None:
                geo_dict["innerRadius"] = elem.inner_radius
            if elem.angle1:
                geo_dict["angle1"] = elem.angle1
            if elem.angle2:
                geo_dict["angle2"] = elem.angle2
            if elem.rotation:
                geo_dict["rotation"] = _tuple_to_dict(elem.rotation)

        elif isinstance(elem, CadRectangle):
            geo_dict["type"] = "rectangle"
            geo_dict["position"] = _tuple_to_dict(elem.position, dimensions=2)
            geo_dict["size"] = _tuple_to_dict(elem.size, dimensions=2)
            if elem.rotation:
                geo_dict["rotation"] = _tuple_to_dict(elem.rotation)
            if elem.alignment:
                geo_dict["alignment"] = elem.alignment.value

        elif isinstance(elem, CadSurfaceRectangle):
            geo_dict["type"] = "surfaceRectangle"
            geo_dict["size"] = _tuple_to_dict(elem.size, dimensions=2)
            geo_dict["offset"] = _tuple_to_dict(elem.offset)
            geo_dict["originPoint"] = _export_cad_point(elem.origin_point)
            geo_dict["mainAxisPoint"] = _export_cad_point(elem.main_axis_point)
            geo_dict["secondaryAxisPoint"] = _export_cad_point(
                elem.secondary_axis_point
            )

        elif isinstance(elem, CadStepFile):
            geo_dict["type"] = "step"
            geo_dict["filepath"] = elem.filepath
            geo_dict["cleanup"] = elem.cleanup

        elif isinstance(elem, CadIgesFile):
            geo_dict["type"] = "iges"
            geo_dict["filepath"] = elem.filepath
            geo_dict["cleanup"] = elem.cleanup

        elif isinstance(elem, CadSatFile):
            geo_dict["type"] = "sat"
            geo_dict["filepath"] = elem.filepath
            geo_dict["cleanup"] = elem.cleanup

        elif isinstance(elem, CadBrepFile):
            geo_dict["type"] = "brep"
            geo_dict["filepath"] = elem.filepath
            geo_dict["cleanup"] = elem.cleanup

        elif isinstance(elem, CadGds2File):
            geo_dict["type"] = "gds2"
            geo_dict["filepath"] = elem.filepath
            geo_dict["cleanup"] = elem.cleanup
            geo_dict["unit"] = elem.unit.value
            geo_dict["layers"] = [
                _clean_dict(
                    {
                        "layer": layer.layer,
                        "type": layer.type,
                        "absoluteZ0": layer.absolute_z0,
                        "thickness": layer.thickness,
                        "previousLayerIndex": layer.previous_layer_index,
                        "name": layer.name,
                    }
                )
                for layer in elem.layers
            ]
            if elem.extrude_parameters is not None:
                ep_dict = _export_gds_extrude_parameters(elem.extrude_parameters)
                if ep_dict:
                    geo_dict["extrudeParameters"] = ep_dict

        # Boolean operations
        elif isinstance(elem, CadUnion):
            geo_dict["type"] = "union"
            if elem.entity_tags:
                geo_dict["entityTags"] = elem.entity_tags
            if elem.cad_names:
                geo_dict["cadNames"] = elem.cad_names
            if elem.cad_paths:
                geo_dict["cadPaths"] = [_export_cad_path(p) for p in elem.cad_paths]

        elif isinstance(elem, CadDifference):
            geo_dict["type"] = "difference"
            if elem.entity_tags_1:
                geo_dict["entityTags1"] = elem.entity_tags_1
            if elem.cad_names_1:
                geo_dict["cadNames1"] = elem.cad_names_1
            if elem.cad_paths_1:
                geo_dict["cadPaths1"] = [_export_cad_path(p) for p in elem.cad_paths_1]
            if elem.entity_tags_2:
                geo_dict["entityTags2"] = elem.entity_tags_2
            if elem.cad_names_2:
                geo_dict["cadNames2"] = elem.cad_names_2
            if elem.cad_paths_2:
                geo_dict["cadPaths2"] = [_export_cad_path(p) for p in elem.cad_paths_2]
            geo_dict["deleteTool"] = elem.delete_tool

        elif isinstance(elem, CadIntersection):
            geo_dict["type"] = "intersection"
            if elem.entity_tags_1:
                geo_dict["entityTags1"] = elem.entity_tags_1
            if elem.cad_names_1:
                geo_dict["cadNames1"] = elem.cad_names_1
            if elem.cad_paths_1:
                geo_dict["cadPaths1"] = [_export_cad_path(p) for p in elem.cad_paths_1]
            if elem.entity_tags_2:
                geo_dict["entityTags2"] = elem.entity_tags_2
            if elem.cad_names_2:
                geo_dict["cadNames2"] = elem.cad_names_2
            if elem.cad_paths_2:
                geo_dict["cadPaths2"] = [_export_cad_path(p) for p in elem.cad_paths_2]
            geo_dict["deleteTool"] = elem.delete_tool

        elif isinstance(elem, CadFragments):
            geo_dict["type"] = "fragments"
            if elem.entity_tags_1:
                geo_dict["entityTags1"] = elem.entity_tags_1
            if elem.cad_names_1:
                geo_dict["cadNames1"] = elem.cad_names_1
            if elem.cad_paths_1:
                geo_dict["cadPaths1"] = [_export_cad_path(p) for p in elem.cad_paths_1]
            if elem.entity_tags_2:
                geo_dict["entityTags2"] = elem.entity_tags_2
            if elem.cad_names_2:
                geo_dict["cadNames2"] = elem.cad_names_2
            if elem.cad_paths_2:
                geo_dict["cadPaths2"] = [_export_cad_path(p) for p in elem.cad_paths_2]
            geo_dict["deleteTool"] = elem.delete_tool

        elif isinstance(elem, CadFragmentAll):
            geo_dict["type"] = "fragmentAll"

        # Simple operations
        elif isinstance(elem, CadTranslate):
            geo_dict["type"] = "translate"
            geo_dict["translation"] = _tuple_to_dict(elem.translation)
            if elem.entity_tags:
                geo_dict["entityTags"] = elem.entity_tags
            if elem.cad_names:
                geo_dict["cadNames"] = elem.cad_names
            if elem.cad_paths:
                geo_dict["cadPaths"] = [_export_cad_path(p) for p in elem.cad_paths]
            if elem.copy_object:
                geo_dict["copyObject"] = elem.copy_object
            if elem.repeat:
                geo_dict["repeat"] = elem.repeat

        elif isinstance(elem, CadRotate):
            geo_dict["type"] = "rotate"
            geo_dict["axis"] = _tuple_to_dict(elem.axis)
            geo_dict["center"] = _tuple_to_dict(elem.center)
            geo_dict["angle"] = elem.angle
            if elem.entity_tags:
                geo_dict["entityTags"] = elem.entity_tags
            if elem.cad_names:
                geo_dict["cadNames"] = elem.cad_names
            if elem.cad_paths:
                geo_dict["cadPaths"] = [_export_cad_path(p) for p in elem.cad_paths]
            if elem.copy_object:
                geo_dict["copyObject"] = elem.copy_object
            if elem.repeat:
                geo_dict["repeat"] = elem.repeat

        elif isinstance(elem, CadGrid):
            geo_dict["type"] = "grid"
            geo_dict["translation"] = _tuple_to_dict(elem.translation)
            geo_dict["size"] = _tuple_to_dict(elem.size)
            if elem.entity_tags:
                geo_dict["entityTags"] = elem.entity_tags
            if elem.cad_names:
                geo_dict["cadNames"] = elem.cad_names
            if elem.cad_paths:
                geo_dict["cadPaths"] = [_export_cad_path(p) for p in elem.cad_paths]

        elif isinstance(elem, CadRemove):
            geo_dict["type"] = "remove"
            if elem.entity_tags:
                geo_dict["entityTags"] = elem.entity_tags
            if elem.cad_names:
                geo_dict["cadNames"] = elem.cad_names
            if elem.cad_paths:
                geo_dict["cadPaths"] = [_export_cad_path(p) for p in elem.cad_paths]

        else:
            # Unknown geometry type - skip or add minimal info
            geo_dict["type"] = "unknown"
            geo_dict["_warning"] = f"Unknown geometry type: {type(elem).__name__}"

        if (
            out_dir is not None
            and isinstance(elem, CadFileImport)
            and "filepath" in geo_dict
        ):
            _apply_geometry_file_download(
                elem,
                geo_dict,
                out_dir,
                downloaded_basenames,
                preexisting_skip_printed,
                file_overwrite_mode=file_overwrite_mode,
            )

        result.append(geo_dict)

    return result


def _parse_matrix_value(value_str: str) -> list | str:
    """
    Parse a matrix string like "[1, 2; 3, 4]" back to nested list.

    Returns the original string if parsing fails.
    """
    if not value_str or not value_str.startswith("[") or not value_str.endswith("]"):
        return value_str

    try:
        inner = value_str[1:-1].strip()
        if ";" in inner:
            # Matrix format
            rows = inner.split(";")
            result = []
            for row in rows:
                row = row.strip()
                if "," in row:
                    values = [v.strip() for v in row.split(",")]
                else:
                    values = row.split()
                # Try to convert to numbers
                parsed_values: list[float | str] = []
                for v in values:
                    try:
                        parsed_values.append(float(v))
                    except ValueError:
                        parsed_values.append(v)
                result.append(parsed_values)
            return result
        else:
            # Vector format like "[1; 2; 3; 4; 5; 6]"
            values = [v.strip() for v in inner.split(";")]
            parsed: list[float | str] = []
            for v in values:
                try:
                    parsed.append(float(v))
                except ValueError:
                    parsed.append(v)
            return parsed
    except Exception:
        return value_str


def _export_materials(
    project: Project, region_id_to_name: dict[str, str]
) -> list[dict]:
    """Export all materials from a project."""
    materials = project.get_materials()
    result = []

    for mat in materials:
        mat_dict: dict[str, Any] = {
            "name": mat.name,
        }

        if mat.description:
            mat_dict["description"] = mat.description
        if mat.color:
            mat_dict["color"] = mat.color
        if mat.abbreviation:
            mat_dict["abbreviation"] = mat.abbreviation
        if mat.orientation:
            mat_dict["orientation"] = mat.orientation
        if mat.enabled is not None and mat.enabled is not True:
            mat_dict["enabled"] = mat.enabled

        if mat.target and mat.target in region_id_to_name:
            mat_dict["target"] = region_id_to_name[mat.target]

        # Extract physical properties from raw properties
        if mat.properties:
            _extract_material_properties(mat.properties, mat_dict)

        result.append(mat_dict)

    return result


def _extract_material_properties(properties: list, mat_dict: dict[str, Any]) -> None:
    """Extract material properties from raw API properties into the export dict."""
    # Build a lookup by definition
    props_by_def: dict[str, Any] = {}
    for prop in properties:
        if hasattr(prop, "definition") and prop.definition:
            props_by_def[prop.definition] = prop

    # Density
    if "density" in props_by_def:
        mat_dict["density"] = props_by_def["density"].value

    # Heat capacity
    if "heatCapacity" in props_by_def:
        mat_dict["heatCapacity"] = props_by_def["heatCapacity"].value

    # Speed of sound
    if "speedOfSound" in props_by_def:
        mat_dict["speedOfSound"] = props_by_def["speedOfSound"].value

    # Damping coefficients
    if "massDampingCoefficient" in props_by_def:
        mat_dict["massDampingCoefficient"] = props_by_def[
            "massDampingCoefficient"
        ].value
    if "stiffnessDampingCoefficient" in props_by_def:
        mat_dict["stiffnessDampingCoefficient"] = props_by_def[
            "stiffnessDampingCoefficient"
        ].value

    # Coefficient of thermal expansion
    if "coefficientOfThermalExpansion" in props_by_def:
        prop = props_by_def["coefficientOfThermalExpansion"]
        if hasattr(prop, "alternative"):
            if "Anisotropic" in (prop.alternative or ""):
                mat_dict["coefficientOfThermalExpansion"] = _parse_matrix_value(
                    prop.value
                )
            else:
                mat_dict["coefficientOfThermalExpansion"] = prop.value

    # Dynamic viscosity
    if "dynamicViscosity" in props_by_def:
        prop = props_by_def["dynamicViscosity"]
        if hasattr(prop, "alternative"):
            if "Anisotropic" in (prop.alternative or ""):
                mat_dict["dynamicViscosity"] = _parse_matrix_value(prop.value)
            else:
                mat_dict["dynamicViscosity"] = prop.value

    # Electric conductivity
    if "electricConductivity" in props_by_def:
        prop = props_by_def["electricConductivity"]
        if hasattr(prop, "alternative"):
            if "Anisotropic" in (prop.alternative or ""):
                mat_dict["electricConductivity"] = _parse_matrix_value(prop.value)
            else:
                mat_dict["electricConductivity"] = prop.value

    # Electric permittivity
    if "electricPermittivity" in props_by_def:
        prop = props_by_def["electricPermittivity"]
        if hasattr(prop, "alternative"):
            if "Anisotropic" in (prop.alternative or ""):
                mat_dict["electricPermittivity"] = _parse_matrix_value(prop.value)
            else:
                mat_dict["electricPermittivity"] = prop.value

    # Magnetic permeability
    if "magneticPermeability" in props_by_def:
        prop = props_by_def["magneticPermeability"]
        if hasattr(prop, "alternative"):
            if "Anisotropic" in (prop.alternative or ""):
                mat_dict["magneticPermeability"] = _parse_matrix_value(prop.value)
            else:
                mat_dict["magneticPermeability"] = prop.value

    # Thermal conductivity
    if "thermalConductivity" in props_by_def:
        prop = props_by_def["thermalConductivity"]
        if hasattr(prop, "alternative"):
            if "Anisotropic" in (prop.alternative or ""):
                mat_dict["thermalConductivity"] = _parse_matrix_value(prop.value)
            else:
                mat_dict["thermalConductivity"] = prop.value

    # Elasticity matrix - check the alternative to determine type
    if "elasticityMatrix" in props_by_def:
        prop = props_by_def["elasticityMatrix"]
        alternative = getattr(prop, "alternative", "") or ""

        if "YoungsModulusPoissonsRatio" in alternative:
            # Need youngsModulus and poissonsRatio
            elasticity_dict = {}
            if "youngsModulus" in props_by_def:
                elasticity_dict["youngsModulus"] = props_by_def["youngsModulus"].value
            if "poissonsRatio" in props_by_def:
                elasticity_dict["poissonsRatio"] = props_by_def["poissonsRatio"].value
            if elasticity_dict:
                mat_dict["elasticityMatrix"] = elasticity_dict
        elif "PressureWaveVelocity" in alternative:
            # Need pressure and shear wave velocities
            elasticity_dict = {}
            if "pressureWaveVelocity" in props_by_def:
                elasticity_dict["pressureWaveVelocity"] = props_by_def[
                    "pressureWaveVelocity"
                ].value
            if "shearWaveVelocity" in props_by_def:
                elasticity_dict["shearWaveVelocity"] = props_by_def[
                    "shearWaveVelocity"
                ].value
            if elasticity_dict:
                mat_dict["elasticityMatrix"] = elasticity_dict
        elif prop.value:
            # Generic matrix
            mat_dict["elasticityMatrix"] = _parse_matrix_value(prop.value)

    # Piezoelectric coupling
    if "piezoelectricCoupling" in props_by_def:
        prop = props_by_def["piezoelectricCoupling"]
        mat_dict["piezoelectricCoupling"] = _parse_matrix_value(prop.value)

    # Prony series
    if "pronySeries" in props_by_def:
        prony_dict = {}
        if "pronyPoissonsRatio" in props_by_def:
            prony_dict["poissonsRatio"] = props_by_def["pronyPoissonsRatio"].value
        if "pronyYoungsModulus" in props_by_def:
            prony_dict["youngsModulus"] = props_by_def["pronyYoungsModulus"].value
        if "pronyRelaxationTime" in props_by_def:
            prony_dict["relaxationTime"] = props_by_def["pronyRelaxationTime"].value
        if prony_dict:
            mat_dict["pronySeries"] = prony_dict


def _export_variable_overrides(
    project: Project, variable_id_to_name: dict[str, str]
) -> tuple[list[dict], dict[str, str]]:
    """
    Export all variable overrides from a project.

    Returns:
        Tuple of (list of override dicts, id_to_name mapping)
    """
    overrides = project.get_variable_overrides()
    id_to_name = _build_id_to_name_map(overrides)

    result = []
    for override in overrides:
        override_dict: dict[str, Any] = {
            "name": override.name,
            "overrides": [],
        }

        if override.sweep_type:
            override_dict["sweepType"] = override.sweep_type.value

        if override.overrides:
            for variable, expression in override.overrides:
                var_name = variable_id_to_name.get(variable.id, variable.name)
                override_dict["overrides"].append(
                    {
                        "variable": var_name,
                        "values": expression,
                    }
                )

        result.append(override_dict)

    return result, id_to_name


def _export_entity_selection(
    target: dict[str, Any],
    key: str,
    regions: list | None,
    entity_ids: list[int] | None,
    region_id_to_name: dict[str, str],
) -> None:
    """Write either entity IDs or region names into *target[key]*."""
    if entity_ids is not None:
        target[f"{key}EntityIds"] = entity_ids
    elif regions is not None:
        target[key] = [region_id_to_name.get(r.id, r.name) for r in regions]
    else:
        warnings.warn(
            f"No regions or entity IDs specified for '{key}'; "
            f"the selection will be empty in the exported project.",
            stacklevel=2,
        )


def _export_meshes(
    project: Project,
    region_id_to_name: dict[str, str],
    override_id_to_name: dict[str, str],
) -> list[dict]:
    """Export all meshes from a project."""
    meshes = project.get_meshes()
    result = []

    for mesh in meshes:
        mesh_dict: dict[str, Any] = {
            "name": mesh.name,
        }

        if mesh.use_mesh_refiner is not None:
            mesh_dict["useMeshRefiner"] = mesh.use_mesh_refiner
        if mesh.scale_factor is not None:
            mesh_dict["scaleFactor"] = mesh.scale_factor
        if mesh.curvature_enhancement is not None:
            mesh_dict["curvatureEnhancement"] = mesh.curvature_enhancement
        if mesh.curved_mesh:
            mesh_dict["curvedMesh"] = mesh.curved_mesh
        if mesh.target_width_to_height_ratio is not None:
            mesh_dict["targetWidthToHeightRatio"] = mesh.target_width_to_height_ratio
        if mesh.max_run_time_minutes is not None:
            mesh_dict["maxRunTimeMinutes"] = mesh.max_run_time_minutes
        if mesh.mesh_size_max is not None:
            mesh_dict["meshSizeMax"] = mesh.mesh_size_max
        if mesh.mesh_size_min is not None:
            mesh_dict["meshSizeMin"] = mesh.mesh_size_min

        if mesh.refinements:
            mesh_dict["refinements"] = []
            for ref in mesh.refinements:
                ref_dict: dict[str, Any] = {
                    "maxSize": ref.max_size,
                }
                if ref.tags is not None:
                    ref_dict["tags"] = ref.tags
                    if ref.entity_type is not None:
                        ref_dict["entityType"] = ref.entity_type.value
                elif ref.region is not None:
                    ref_dict["region"] = region_id_to_name.get(
                        ref.region.id, ref.region.name
                    )
                mesh_dict["refinements"].append(ref_dict)

        if mesh.extrusion:
            ext = mesh.extrusion
            ext_data: dict[str, Any] = {
                "subLayerCounts": ext.sub_layer_counts,
            }
            if ext.volume_ids is not None:
                ext_data["volumeIds"] = ext.volume_ids
            elif ext.regions is not None:
                ext_data["regions"] = [
                    region_id_to_name.get(r.id, r.name) for r in ext.regions
                ]
            mesh_dict["simpleExtrusion"] = ext_data

        if mesh.path_extrusions:
            mesh_dict["pathExtrusions"] = []
            for ext in mesh.path_extrusions:
                ext_dict: dict[str, Any] = {
                    "layers": [
                        {
                            "relativeHeight": layer.relative_height,
                            "subLayerCount": layer.sublayer_count,
                        }
                        for layer in ext.layers
                    ],
                }
                _export_entity_selection(
                    ext_dict,
                    "volumes",
                    ext.volumes,
                    ext.volume_entity_ids,
                    region_id_to_name,
                )
                _export_entity_selection(
                    ext_dict,
                    "fromSurfaces",
                    ext.from_surfaces,
                    ext.from_surface_entity_ids,
                    region_id_to_name,
                )
                _export_entity_selection(
                    ext_dict,
                    "toSurfaces",
                    ext.to_surfaces,
                    ext.to_surface_entity_ids,
                    region_id_to_name,
                )
                if ext.quadrangles:
                    ext_dict["useQuadrangles"] = ext.quadrangles
                mesh_dict["pathExtrusions"].append(ext_dict)

        if mesh.slanted_extrusions:
            mesh_dict["slantedExtrusions"] = []
            for ext in mesh.slanted_extrusions:
                ext_dict = {
                    "layers": [
                        {
                            "relativeHeight": layer.relative_height,
                            "subLayerCount": layer.sublayer_count,
                        }
                        for layer in ext.layers
                    ],
                }
                _export_entity_selection(
                    ext_dict,
                    "volumes",
                    ext.volumes,
                    ext.volume_entity_ids,
                    region_id_to_name,
                )
                _export_entity_selection(
                    ext_dict,
                    "fromSurfaces",
                    ext.from_surfaces,
                    ext.from_surface_entity_ids,
                    region_id_to_name,
                )
                _export_entity_selection(
                    ext_dict,
                    "toSurfaces",
                    ext.to_surfaces,
                    ext.to_surface_entity_ids,
                    region_id_to_name,
                )
                if ext.quadrangles:
                    ext_dict["useQuadrangles"] = ext.quadrangles
                mesh_dict["slantedExtrusions"].append(ext_dict)

        if mesh.flatten_and_rebuild_extrusions:
            mesh_dict["flattenAndRebuildExtrusions"] = []
            for ext in mesh.flatten_and_rebuild_extrusions:
                ext_dict = {
                    "layers": [
                        {
                            "relativeHeight": layer.relative_height,
                            "subLayerCount": layer.sublayer_count,
                        }
                        for layer_group in ext.layers
                        for layer in layer_group
                    ],
                }
                _export_entity_selection(
                    ext_dict,
                    "volumes",
                    ext.volumes,
                    ext.volume_entity_ids,
                    region_id_to_name,
                )
                if ext.direction_vector is not None:
                    ext_dict["directionVector"] = {
                        "x": ext.direction_vector.x,
                        "y": ext.direction_vector.y,
                        "z": ext.direction_vector.z,
                    }
                if ext.quadrangles:
                    ext_dict["useQuadrangles"] = ext.quadrangles
                mesh_dict["flattenAndRebuildExtrusions"].append(ext_dict)

        if mesh.auto_transfinite:
            mesh_dict["autoTransfinite"] = []
            for group in mesh.auto_transfinite:
                group_dict: dict[str, Any] = {
                    "hx": group.hx,
                    "hy": group.hy,
                }
                if group.hz is not None:
                    group_dict["hz"] = group.hz
                if group.tags is not None:
                    group_dict["tags"] = group.tags
                    if group.entity_type is not None:
                        group_dict["entityType"] = group.entity_type.value
                elif group.region is not None:
                    group_dict["region"] = region_id_to_name.get(
                        group.region.id, group.region.name
                    )
                mesh_dict["autoTransfinite"].append(group_dict)

        if mesh.variable_overrides:
            for vo in mesh.variable_overrides:
                if vo.id in override_id_to_name:
                    mesh_dict["variableOverride"] = override_id_to_name[vo.id]
                    break  # Only use first one

        result.append(mesh_dict)

    return result


def _decode_param_value(value: str) -> str:
    """Decode a parameter value that may be an ASCII char array.

    The API stores enum-type values as ``"[102, 105, 101, ...]"`` (list of
    ASCII codes).  This function detects the format and converts it back to
    the plain string, leaving other values unchanged.
    """
    if not (value.startswith("[") and value.endswith("]")):
        return value
    inner = value[1:-1].strip()
    if not inner:
        return value
    parts = inner.split(",")
    try:
        codes = [int(p.strip()) for p in parts]
    except ValueError:
        return value
    if all(32 <= c < 127 for c in codes):
        return "".join(chr(c) for c in codes)
    return value


def _export_interactions(
    physic: Physic,
    region_id_to_name: dict[str, str],
) -> list[dict]:
    """Export all interactions for a single physic."""

    interactions = physic.interactions
    result: list[dict] = []

    for interaction in interactions:
        i_dict: dict[str, Any] = {
            "type": interaction.definition,
            "name": interaction.name,
            "enabled": interaction.enabled,
        }

        if interaction.namespace is not None:
            i_dict["namespace"] = interaction.namespace

        raw_interaction = interaction._interaction
        raw_targets = raw_interaction.targets if raw_interaction else []
        if raw_targets:
            cls_target_ids: Dict[str, str] = getattr(
                type(interaction), "target_definition_ids", {}
            )
            defn_to_param: dict[str, str] = {v: k for k, v in cls_target_ids.items()}

            if len(raw_targets) == 1 and len(cls_target_ids) <= 1:
                region_id = raw_targets[0].region
                i_dict["target"] = region_id_to_name.get(region_id, region_id)
            else:
                targets_dict: dict[str, str] = {}
                for t in raw_targets:
                    param_name = defn_to_param.get(t.definition, t.definition)
                    targets_dict[_snake_to_camel(param_name)] = region_id_to_name.get(
                        t.region, t.region
                    )
                i_dict["targets"] = targets_dict

        defaults = get_interaction_parameter_defaults(interaction.definition)
        for param in interaction.parameters:
            value = _decode_param_value(param.value)
            if defaults.get(param.definition) == value:
                continue
            i_dict[param.definition] = value

        result.append(i_dict)

    return result


def _export_physics(
    project: Project,
    region_id_to_name: dict[str, str],
) -> list[dict]:
    """Export all physics (with nested interactions) from a project."""
    physics_list = project.get_physics()
    result: list[dict] = []

    for physic in physics_list:
        p_dict: dict[str, Any] = {"type": physic.definition}

        target_id = physic.target_region_id
        if target_id:
            p_dict["target"] = region_id_to_name.get(target_id, target_id)

        interactions = _export_interactions(physic, region_id_to_name)
        if interactions:
            p_dict["interactions"] = interactions

        result.append(p_dict)

    return result


def _collapse_output_filter(
    otype: str,
    params_by_def: dict[str, str],
) -> tuple[dict | None, set[str]]:
    """Reverse of import_project._expand_output_filter.

    Returns a friendly filter dict and the set of raw parameter IDs consumed.
    """
    filter_type_param = f"{otype}FilterType"
    raw_filter_value = params_by_def.get(filter_type_param)
    if raw_filter_value is None:
        return None, set()

    filter_type_value = _decode_param_value(raw_filter_value)

    consumed: set[str] = {filter_type_param}
    prefix = f"{otype}FilterType"
    filter_type_name = (
        filter_type_value[len(prefix) :]
        if filter_type_value.startswith(prefix)
        else filter_type_value
    )

    filter_dict: dict[str, Any] = {"type": filter_type_name}

    value_param = f"{otype}Filter{filter_type_name}"
    if value_param in params_by_def:
        filter_dict["value"] = params_by_def[value_param]
        consumed.add(value_param)

    return filter_dict, consumed


def _export_outputs(
    simulation: Simulation,
    region_id_to_name: dict[str, str],
) -> list[dict]:
    """Export output interactions for a single simulation."""
    outputs = simulation.get_outputs()
    result: list[dict] = []

    for output in outputs:
        otype = output.definition
        o_dict: dict[str, Any] = {
            "type": otype,
            "name": output.name,
            "enabled": output.enabled,
        }

        raw_interaction = output._interaction
        raw_targets = raw_interaction.targets if raw_interaction else []
        if raw_targets:
            cls_target_ids: Dict[str, str] = getattr(
                type(output), "target_definition_ids", {}
            )
            defn_to_param: dict[str, str] = {v: k for k, v in cls_target_ids.items()}

            if len(raw_targets) == 1 and len(cls_target_ids) <= 1:
                region_id = raw_targets[0].region
                o_dict["target"] = region_id_to_name.get(region_id, region_id)
            else:
                targets_dict: dict[str, str] = {}
                for t in raw_targets:
                    param_name = defn_to_param.get(t.definition, t.definition)
                    targets_dict[_snake_to_camel(param_name)] = region_id_to_name.get(
                        t.region, t.region
                    )
                o_dict["targets"] = targets_dict

        params_by_def = {p.definition: p.value for p in output.parameters}
        defaults = get_output_parameter_defaults(otype)

        # Extract filter into a friendly dict
        filter_dict, filter_consumed = _collapse_output_filter(otype, params_by_def)
        if filter_dict is not None:
            o_dict["filter"] = filter_dict

        for param in output.parameters:
            if param.definition in filter_consumed:
                continue
            value = _decode_param_value(param.value)
            if defaults.get(param.definition) == value:
                continue

            # Reverse the "expression" alias: otype param -> "expression"
            if param.definition == otype:
                o_dict["expression"] = value
                continue

            # Reverse SkinOnly / DeformedMesh aliases
            matched_alias = False
            for suffix, friendly in _OUTPUT_PARAM_REVERSE.items():
                if param.definition == f"{otype}{suffix}":
                    if friendly in _OUTPUT_BOOL_ALIASES:
                        o_dict[friendly] = value != "0"
                    else:
                        o_dict[friendly] = value
                    matched_alias = True
                    break

            if not matched_alias:
                o_dict[param.definition] = value

        result.append(o_dict)

    return result


def _export_field_initialization(
    fi: FieldInitialization,
    sim_id_to_name: dict[str, str],
    field_id_to_info: dict[str, tuple[str, str]],
) -> dict[str, object]:
    d: dict[str, object] = {
        "type": fi.type.value,
        "sourceValueSimulationName": sim_id_to_name.get(
            fi.source_simulation_id, fi.source_simulation_id
        ),
        "sourceValueOutputName": fi.source_output_name,
    }
    if fi.field_id is not None:
        info = field_id_to_info.get(fi.field_id)
        if info is not None:
            field_def, physics_def = info
            d["field"] = field_def
            d["physics"] = physics_def
        else:
            d["field"] = fi.field_id
    if fi.source_output_specifier is not None:
        d["sourceValueOutputSpecifier"] = fi.source_output_specifier
    if fi.source_sweep_step is not None:
        d["sourceValueSweepStep"] = fi.source_sweep_step
    if fi.source_step is not None:
        d["sourceValueStep"] = fi.source_step
    if fi.harmonic is not None:
        d["harmonic"] = fi.harmonic
    return d


def _export_simulations(
    project: Project,
    mesh_id_to_name: dict[str, str],
    override_id_to_name: dict[str, str],
    physics_id_to_type: dict[str, str] | None = None,
    region_id_to_name: dict[str, str] | None = None,
) -> list[dict]:
    """Export all simulations from a project."""
    if physics_id_to_type is None:
        physics_id_to_type = {}

    simulations = project.get_simulations()
    sim_id_to_name: dict[str, str] = {s.id: s.name for s in simulations if s.id}
    name_counts = Counter(s.name for s in simulations)
    duplicate_names = {name for name, count in name_counts.items() if count > 1}

    field_id_to_info: dict[str, tuple[str, str]] = {}
    for physic in project.get_physics():
        for field in physic.fields:
            field_id_to_info[field.id] = (field.definition, physic.definition)

    result = []

    for sim in simulations:
        sim_dict: dict[str, Any] = {
            "name": sim.name,
            "description": sim.description or "",
            "maxRunTimeMinutes": sim.max_run_time_minutes,
        }

        sim_dict["solverMode"] = sim.solver_mode.value

        if sim.analysis_type is not None:
            _analysis_type_export_map = {
                "steadyState": "static",
            }
            at_val = sim.analysis_type.value
            sim_dict["analysisType"] = _analysis_type_export_map.get(at_val, at_val)

        if sim.harmonics is not None:
            sim_dict["harmonics"] = sim.harmonics

        if sim.mesh_id:
            sim_dict["mesh"] = mesh_id_to_name.get(sim.mesh_id, sim.mesh_id)

        vo = sim.variable_overrides
        if vo is not None:
            vo_name = override_id_to_name.get(vo.id, vo.name)
            sim_dict["variableOverride"] = vo_name

        node_type = sim.node_type
        if node_type is not None and node_type != CPU.DEFAULT:
            sim_dict["runtime"] = {
                "nodeType": node_type.name,
                "nodeCount": sim.node_count or 1,
            }

        if sim.physics:
            sim_dict["physics"] = [
                physics_id_to_type.get(pid, pid) for pid in sim.physics
            ]
        if sim.transient_start_time is not None:
            sim_dict["transientStartTime"] = sim.transient_start_time
        if sim.transient_end_time is not None:
            sim_dict["transientEndTime"] = sim.transient_end_time
        if sim.transient_timestep_size is not None:
            sim_dict["transientTimestepSize"] = sim.transient_timestep_size
        if sim.timestep_algorithm is not None:
            sim_dict["timestepAlgorithm"] = sim.timestep_algorithm.value
        if sim.fundamental_frequency is not None:
            sim_dict["fundamentalFrequency"] = sim.fundamental_frequency
        if sim.num_fft_samples is not None:
            sim_dict["numFFTSamples"] = sim.num_fft_samples
        if sim.num_requested_eigenmodes is not None:
            sim_dict["numRequestedEigenmodes"] = sim.num_requested_eigenmodes
        if sim.target_eigenfrequency is not None:
            sim_dict["targetEigenfrequency"] = sim.target_eigenfrequency
        if sim.eigenmode_port_analysis is not None:
            sim_dict["eigenmodePortAnalysis"] = sim.eigenmode_port_analysis
        if sim.solver_tolerance is not None:
            sim_dict["solverTolerance"] = sim.solver_tolerance
        if sim.nonlinear_solver_tolerance is not None:
            sim_dict["nonlinearSolverTolerance"] = sim.nonlinear_solver_tolerance
        if sim.nonlinear_solver_max_iterations is not None:
            sim_dict["nonlinearSolverMaxIterations"] = (
                sim.nonlinear_solver_max_iterations
            )
        if sim.eigenmode_solver_tolerance is not None:
            sim_dict["eigenmodeSolverTolerance"] = sim.eigenmode_solver_tolerance
        if sim.eigenmode_solver_max_iterations is not None:
            sim_dict["eigenmodeSolverMaxIterations"] = (
                sim.eigenmode_solver_max_iterations
            )
        if sim.target_frequency is not None:
            sim_dict["targetFrequency"] = sim.target_frequency
        if sim.numerical_jacobian is not None:
            sim_dict["numericalJacobian"] = sim.numerical_jacobian
        if sim.disabled_script_sections is not None:
            sim_dict["disabledScriptSections"] = [
                s.value.value for s in sim.disabled_script_sections
            ]
        if sim.field_initializations is not None:
            for fi in sim.field_initializations:
                ref_name = sim_id_to_name.get(fi.source_simulation_id)
                if ref_name and ref_name in duplicate_names:
                    warnings.warn(
                        f"Simulation '{sim.name}' has a field initialization "
                        f"referencing simulation '{ref_name}', but multiple "
                        f"simulations share that name. The reference may resolve "
                        f"to the wrong simulation on import. "
                        f"Consider using unique simulation names.",
                        stacklevel=2,
                    )
                    break
            sim_dict["fieldInitializations"] = [
                _export_field_initialization(fi, sim_id_to_name, field_id_to_info)
                for fi in sim.field_initializations
            ]

        outputs = _export_outputs(sim, region_id_to_name or {})
        if outputs:
            sim_dict["outputs"] = outputs

        custom_scripts = [s for s in sim.get_scripts() if s.section_name is not None]
        if custom_scripts:
            sim_dict["customScripts"] = [
                {
                    "name": s.name,
                    "sectionName": s.section_name.value.value,  # type: ignore[union-attr]
                    "content": s.content,
                }
                for s in custom_scripts
            ]

        result.append(sim_dict)

    return result


def export_project_data(
    project: Project,
    include_meshes: bool = True,
    *,
    download_geometries: bool = False,
    files_output_dir: str | Path = ".",
    file_overwrite_mode: FileOverwriteMode = FileOverwriteMode.SKIP,
) -> dict:
    """
    Export project data to a dictionary compatible with import_project().

    The exported dictionary contains:
    - Project metadata (name, description, dimension, labels)
    - Variables (topologically sorted)
    - Functions (regular and interpolated)
    - Geometries (CAD elements with file paths for files)
    - Regions (basic, computed, region rules)
    - Materials
    - Physics (with nested interactions)
    - Variable overrides
    - Meshes (optional)
    - Simulations (optional, with output interactions)

    Args:
        project: The project to export.
        include_meshes: Whether to include mesh definitions and simulations (default True).
            Note: Exported meshes are definitions only; mesh data is not included.
        download_geometries: If True, download geometry import files (STEP, IGES, etc.)
            into ``files_output_dir``.
        files_output_dir: Directory for downloaded geometry files when
            ``download_geometries`` is True.
            Resolved to an absolute path; created if missing.
        file_overwrite_mode: Controls behavior when a geometry file already
            exists on disk. ``FileOverwriteMode.SKIP`` (default) prints a
            message and keeps the existing file, ``FileOverwriteMode.OVERWRITE``
            replaces it, and ``FileOverwriteMode.ERROR`` raises
            ``FileExistsError``.

    Returns:
        Dictionary containing the project data, compatible with import_project().

    Note:
        When ``download_geometries`` is False (default), CAD paths are placeholders; you must
        supply files at those paths when re-importing.

        When ``download_geometries`` is True, each ``CadFileImport`` is handled in geometry
        order. The same basename may appear on multiple elements (same file imported
        multiple times): only one download runs per basename; later elements reuse the
        file and get ``filepath`` set to that basename (relative to ``files_output_dir``).
        If the target path already exists on disk before this export would write it,
        behavior depends on ``file_overwrite_mode``.

    Example:
        >>> from allsolve import Project
        >>> project = Project.get("my-project-id")
        >>> data = export_project_data(project)
        >>> # Modify as needed
        >>> data["name"] = "Modified Project"
        >>> # Re-import to new project
        >>> from allsolve import import_project
        >>> new_project = import_project(data)
    """
    result: dict[str, Any] = {}

    out_dir: Path | None = None
    if download_geometries:
        out_dir = Path(files_output_dir).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

    # Project metadata
    result["name"] = project.name
    if project.description:
        result["description"] = project.description
    result["dimension"] = project.dimension
    if project.labels:
        result["labels"] = project.labels
    if project.geometry_no_implicit_fragment:
        result["geometryNoImplicitFragment"] = project.geometry_no_implicit_fragment
    if project.pml_num_layers is not None or project.pml_thickness is not None:
        pml_dict = {}
        if project.pml_num_layers is not None:
            pml_dict["numLayers"] = project.pml_num_layers
        if project.pml_thickness is not None:
            pml_dict["thickness"] = project.pml_thickness
        result["pmlSettings"] = pml_dict

    # Variables
    variables = _export_variables(project)
    if variables:
        result["variables"] = variables

    # Build variable ID to name mapping for later use
    var_id_to_name = {v.id: v.name for v in project.get_variables()}

    # Functions
    functions = _export_functions(project)
    if functions:
        result["functions"] = functions

    # Geometries
    geometries = _export_geometries(
        project,
        download_geometries=download_geometries,
        files_output_dir=out_dir,
        file_overwrite_mode=file_overwrite_mode,
    )
    if geometries:
        result["geometries"] = geometries

    # Regions
    regions, region_id_to_name = _export_regions(project)
    if regions:
        result["regions"] = regions

    # Materials
    materials = _export_materials(project, region_id_to_name)
    if materials:
        result["materials"] = materials

    # Physics and interactions
    physics_id_to_definition: dict[str, str] = {}
    physics_list = project.get_physics()
    for p in physics_list:
        physics_id_to_definition[p.id] = p.definition

    physics = _export_physics(project, region_id_to_name)
    if physics:
        result["physics"] = physics

    # Variable overrides
    variable_overrides, override_id_to_name = _export_variable_overrides(
        project, var_id_to_name
    )
    if variable_overrides:
        result["variableOverrides"] = variable_overrides

    # Meshes and simulations (optional)
    mesh_id_to_name: dict[str, str] = {}
    if include_meshes:
        mesh_id_to_name = _build_id_to_name_map(project.get_meshes())
        meshes = _export_meshes(project, region_id_to_name, override_id_to_name)
        if meshes:
            result["meshes"] = meshes

        simulations = _export_simulations(
            project,
            mesh_id_to_name,
            override_id_to_name,
            physics_id_to_definition,
            region_id_to_name,
        )
        if simulations:
            result["simulations"] = simulations

    return result
