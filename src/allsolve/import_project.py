# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

"""
Contains a PoC of a convenience import format parser.
"""

import json
import yaml
import csv
from typing import Any

from pathlib import Path

from allsolve.geometry.cad_basic_geometry import (
    CadBox,
    CadCylinder,
    CadSphere,
    CadCone,
    CadTorus,
    CadSurfaceRectangle,
    CadDisk,
    CadRectangle,
    CadPoint,
)
from allsolve.geometry.cad_file_import import (
    CadStepFile,
    CadIgesFile,
    CadSatFile,
    CadBrepFile,
    CadGds2File,
    CadGdsLayer,
    CadGdsExtrudeParameters,
)
from allsolve.geometry.cad_path import CadGlob, CadPath
from allsolve.geometry.cad_utils import create_distance_unit
from allsolve.geometry.cad_boolean_operation import (
    CadUnion,
    CadDifference,
    CadIntersection,
    CadFragments,
    CadFragmentAll,
)
from allsolve.geometry.cad_simple_operation import (
    CadTranslate,
    CadRotate,
    CadGrid,
    CadRemove,
)
from .material import Material, MaterialProperty
from .project import Project, GeometryPipelineVersion
from .job import Job, OnError
from .mesh import (
    MeshSettings,
    MeshRefinement,
    AutoTransfiniteGroup,
    MeshExtrusion,
    PathExtrusion,
    SlantedExtrusion,
    FlattenAndRebuildExtrusion,
    ExtrusionLayerDefinition,
)
from .region import KeyValueAttributePath, RegionOperation, Region
from allsolve_rawapi.models.expression_bounding_box import (
    ExpressionBoundingBox,
    ExpressionVector,
)
from allsolve_rawapi.models.cad_alignment import CadAlignment
from allsolve_rawapi.models.cad_distance_unit import CadDistanceUnit
from allsolve_rawapi.models.cad_gds_unify_layer_discretizations import (
    CadGdsUnifyLayerDiscretizations,
)
from allsolve_rawapi.models.cad_spline_method import CadSplineMethod
from allsolve_rawapi.models.entity_type import EntityType as RawEntityType
from allsolve_rawapi.models.field_initialization_type import FieldInitializationType
from allsolve_rawapi.models.custom_script_section_name import CustomScriptSectionName
from allsolve_rawapi.models.disabled_script_section import DisabledScriptSection
from .simulation import (
    Script,
    FieldInitialization,
    Runtime,
    CPU,
    SolverMode,
    TimestepAlgorithm,
    AnalysisType,
    Simulation,
    DisableableSection,
    CustomSection,
)
from .physics import Physic
from allsolve.export_format import (
    OUTPUT_TYPE_ALIASES as _OUTPUT_TYPE_ALIASES,
    OUTPUT_PARAM_ALIASES as _OUTPUT_PARAM_ALIASES,
)
from .physics.interaction import Interaction, InteractionParameter, OutputInteraction
from .physics.generated.registries import (
    get_interaction_class,
    get_interaction_parameter_defaults,
    get_output_class,
    get_output_parameter_defaults,
    get_physics_class,
)
from .physics.conversions import boolean_to_str


def _resolve_path(
    filepath: str,
    base_path: Path | None,
    *,
    allow_paths_outside_project: bool = False,
) -> str:
    """
    Resolve a file path against the import bundle directory (YAML parent's folder).

    If *base_path* is ``None`` (dict import with no on-disk file), *filepath* is
    returned unchanged.

    When *base_path* is set, relative paths are resolved under the base. Absolute
    paths must also resolve to a path inside the base unless
    *allow_paths_outside_project* is ``True`` (insecure: use only for trusted
    import data that must reference files outside the project tree).

    Raises:
        ValueError: If a path escapes the base directory when that check applies.
    """
    if base_path is None:
        return filepath
    path = Path(filepath)
    if allow_paths_outside_project and path.is_absolute():
        return filepath
    base_resolved = base_path.resolve()
    if path.is_absolute():
        resolved = path.resolve()
    else:
        resolved = (base_path / filepath).resolve()
    try:
        resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise ValueError(
            f"Path {filepath!r} resolves outside the base directory "
            f"{base_resolved}. This may indicate a path traversal attempt."
        ) from exc
    return str(resolved)


def _validate_import_input_files_exist(
    import_data: dict,
    yaml_file_path: Path | None,
    *,
    allow_paths_outside_project: bool = False,
) -> None:
    """
    Ensure every local file referenced by the import data exists before mutating the project.

    Uses the same path resolution as the import steps. For dict imports (no YAML path),
    relative paths are checked against the process working directory, matching ``open()`` behavior.
    """
    missing: list[tuple[str, str]] = []

    def record_if_missing(context: str, raw_path: str) -> None:
        resolved = _resolve_path(
            raw_path,
            yaml_file_path,
            allow_paths_outside_project=allow_paths_outside_project,
        )
        if not Path(resolved).is_file():
            missing.append((context, resolved))

    geometries = import_data.get("geometries")
    if geometries is not None:
        for idx, geometry in enumerate(geometries):
            if not isinstance(geometry, dict):
                continue
            if "filepath" in geometry:
                gtype = geometry.get("type", "?")
                record_if_missing(f"geometries[{idx}] ({gtype})", geometry["filepath"])

    if "geometry" in import_data:
        geometry = import_data["geometry"]
        if isinstance(geometry, dict) and "filename" in geometry:
            gtype = geometry.get("type", "?")
            record_if_missing(f"geometry ({gtype})", geometry["filename"])

    for idx, function in enumerate(import_data.get("functions", [])):
        if not isinstance(function, dict):
            continue
        if function.get("type") == "interpolated" and "fromCsv" in function:
            fname = function.get("name", "?")
            record_if_missing(
                f"functions[{idx}] '{fname}' (fromCsv)", function["fromCsv"]
            )

    for sidx, simulation_data in enumerate(import_data.get("simulations", [])):
        if not isinstance(simulation_data, dict):
            continue
        sim_name = simulation_data.get("name", "?")
        for j, script_data in enumerate(simulation_data.get("scripts", [])):
            if isinstance(script_data, dict) and "filepath" in script_data:
                record_if_missing(
                    f"simulations[{sidx}] '{sim_name}' scripts[{j}]",
                    script_data["filepath"],
                )

    if missing:
        lines = "\n".join(f"  - {ctx}: {path}" for ctx, path in missing)
        raise ValueError(f"Missing files required for import:\n{lines}")


def import_project(
    file_or_data: str | dict,
    project_to_modify: Project | None = None,
    verbose: bool | None = None,
    run_meshes_and_simulations: bool = True,
    *,
    allow_paths_outside_project: bool = False,
) -> Project:
    """
    Import a project from a file or a dictionary.

    Takes a file in YAML or JSON format, an example with all supported fields etc.
    is given in example/import_project/project-format.yaml.

    Args:
        file_or_data: The path to the file to import or a dictionary.
        project_to_modify: The project to modify. If not provided, a new project is created.
        verbose: When true, print progress messages and stream logs to the
            console during import. When ``None``, use the ``verbose`` field from the import
            data (YAML/JSON or dict).
        run_meshes_and_simulations: When ``False``, skip running all meshes and simulations
            after import. Defaults to ``True``. To skip individual meshes or simulations instead,
            set ``createOnly: true`` on the corresponding entry in the import data.
        allow_paths_outside_project: When ``False`` (default), every file path in the
            import (relative or absolute) must resolve under the project directory
            (the parent folder of a YAML/JSON file). Set to ``True`` only for trusted
            import data that must use absolute paths to files outside that directory
            (e.g. shared assets on a secure host). **Do not** use for untrusted bundles.

    Returns:
        The imported project object.

    Before creating or updating the project, referenced input files (CAD paths, CSV data for
    interpolated functions, simulation script paths) are checked on disk; if any are missing,
    ``ValueError`` is raised immediately.
    """

    yaml_file_path: Path | None = None
    if isinstance(file_or_data, str):
        yaml_file_path = Path(file_or_data).parent.resolve()
        with open(file_or_data, "r") as f:
            try:
                import_data = yaml.safe_load(f)
            except yaml.YAMLError:
                import_data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Failed to parse given file {file_or_data}, it needs to be valid JSON or YAML. Error: {e}"
                )
    else:
        import_data = file_or_data

    effective_verbose = (
        import_data.get("verbose", False) if verbose is None else verbose
    )

    _validate_import_input_files_exist(
        import_data,
        yaml_file_path,
        allow_paths_outside_project=allow_paths_outside_project,
    )

    project = None
    try:
        if project_to_modify:
            project = project_to_modify
        else:
            project = Project.create(
                name=import_data["name"],
                description=import_data.get("description", ""),
                labels=import_data.get("labels", []),
                geometry_pipeline_version=GeometryPipelineVersion.V2,
                dimension=import_data.get("dimension", 3),
                geometry_no_implicit_fragment=import_data.get(
                    "geometryNoImplicitFragment", False
                ),
            )

        pml_settings = import_data.get("pmlSettings")
        if pml_settings is not None:
            if pml_settings.get("numLayers") is not None:
                project.pml_num_layers = pml_settings["numLayers"]
            if pml_settings.get("thickness") is not None:
                project.pml_thickness = pml_settings["thickness"]
            project.save()

        variables = import_variables(
            project,
            import_data.get("variables", []),
            verbose=effective_verbose,
        )

        if "geometries" in import_data:
            import_cad_geometries(
                project,
                import_data["geometries"],
                yaml_file_path=yaml_file_path,
                verbose=effective_verbose,
                allow_paths_outside_project=allow_paths_outside_project,
            )

        if "geometry" in import_data:
            import_geometry(
                project,
                import_data["geometry"],
                yaml_file_path=yaml_file_path,
                verbose=effective_verbose,
                allow_paths_outside_project=allow_paths_outside_project,
            )

        import_functions(
            project,
            import_data.get("functions", []),
            yaml_file_path=yaml_file_path,
            verbose=effective_verbose,
            allow_paths_outside_project=allow_paths_outside_project,
        )

        regions = import_regions(
            project,
            import_data.get("regions", []),
            verbose=effective_verbose,
        )

        import_materials(
            project,
            import_data.get("materials", []),
            regions,
            verbose=effective_verbose,
        )

        import_physics_and_interactions(
            project,
            import_data.get("physics", []),
            regions,
            verbose=effective_verbose,
        )

        variables_overrides = import_variable_overrides(
            project,
            import_data.get("variableOverrides", []),
            variables,
            verbose=effective_verbose,
        )

        imported_meshes = import_meshes(
            project,
            import_data.get("meshes", []),
            regions,
            variables_overrides,
            verbose=effective_verbose,
        )

        imported_simulations = import_simulations(
            project,
            import_data.get("simulations", []),
            imported_meshes,
            variables_overrides,
            yaml_file_path=yaml_file_path,
            regions=regions,
            verbose=effective_verbose,
            allow_paths_outside_project=allow_paths_outside_project,
        )

        if run_meshes_and_simulations:
            run_imported_meshes(
                import_data.get("meshes", []),
                imported_meshes,
                variables_overrides,
                verbose=effective_verbose,
            )
            run_imported_simulations(
                import_data.get("simulations", []),
                imported_simulations,
                verbose=effective_verbose,
            )

    except Exception as e:
        if project is not None:
            # project.delete()
            pass
        if isinstance(file_or_data, str):
            raise ValueError(f"Failed to import project from {file_or_data}: {e}")
        else:
            raise ValueError(f"Failed to import project: {e}")

    return project


def parse_tuple(
    value: dict | tuple | list | None, expected_dimensions: int = 3
) -> tuple[float | str, ...] | None:
    """
    Parse a tuple value from YAML/JSON dictionary format.
    Accepts dictionary format with x, y, z keys (or x, y for 2D).
    """
    if value is None:
        return None

    if isinstance(value, (tuple, list)):
        return tuple(value)

    if isinstance(value, dict):
        if expected_dimensions == 2:
            if "x" not in value or "y" not in value:
                raise ValueError(
                    f"Expected dictionary with 'x' and 'y' keys, got: {list(value.keys())}"
                )
            return (value["x"], value["y"])
        elif expected_dimensions == 3:
            if "x" not in value or "y" not in value or "z" not in value:
                raise ValueError(
                    f"Expected dictionary with 'x', 'y', and 'z' keys, got: {list(value.keys())}"
                )
            return (value["x"], value["y"], value["z"])
        else:
            raise ValueError(
                f"Unsupported expected_dimensions: {expected_dimensions}. Only 2 and 3 are supported."
            )

    raise ValueError(
        f"Expected dict, tuple, list, or None, got {type(value).__name__}: {value}"
    )


def _get_first_present(mapping: dict, *keys: str) -> Any:
    """Return the first present key value from mapping (even if falsy)."""
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def _parse_value_with_unit(value: Any) -> Any:
    """Accept {value, unit} or [value, unit] for unit-bearing inputs."""
    if isinstance(value, dict) and "value" in value and "unit" in value:
        return (value["value"], value["unit"])
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return (value[0], value[1])
    return value


def _parse_gds_unify_layer_discretizations(
    value: Any,
) -> CadGdsUnifyLayerDiscretizations | None:
    if value is None:
        return None
    if isinstance(value, CadGdsUnifyLayerDiscretizations):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        for member in CadGdsUnifyLayerDiscretizations:
            if normalized == member.value.lower() or normalized == member.name.lower():
                return member
    raise ValueError(f"Invalid unify layer discretizations value: {value}")


def _parse_gds_spline_method(value: Any) -> CadSplineMethod | None:
    if value is None:
        return None
    if isinstance(value, CadSplineMethod):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        for member in CadSplineMethod:
            if normalized == member.value.lower() or normalized == member.name.lower():
                return member
    raise ValueError(f"Invalid spline method value: {value}")


def _parse_gds_extrude_parameters(
    extrude_data: Any,
) -> CadGdsExtrudeParameters | None:
    if extrude_data is None:
        return None
    if isinstance(extrude_data, CadGdsExtrudeParameters):
        return extrude_data
    if not isinstance(extrude_data, dict):
        raise ValueError("GDS2 extrudeParameters must be a dictionary")

    unify_layer_discretizations = _parse_gds_unify_layer_discretizations(
        _get_first_present(
            extrude_data,
            "unifyLayerDiscretizations",
            "unify_layer_discretizations",
        )
    )
    fuzzy_value = _parse_value_with_unit(
        _get_first_present(extrude_data, "fuzzyValue", "fuzzy_value")
    )
    feature_angle_threshold = _parse_value_with_unit(
        _get_first_present(
            extrude_data,
            "featureAngleThreshold",
            "feature_angle_threshold",
        )
    )
    length_ratio_threshold = _get_first_present(
        extrude_data,
        "lengthRatioThreshold",
        "length_ratio_threshold",
    )
    spline_method = _parse_gds_spline_method(
        _get_first_present(extrude_data, "splineMethod", "spline_method")
    )
    spline_tolerance = _parse_value_with_unit(
        _get_first_present(extrude_data, "splineTolerance", "spline_tolerance")
    )
    circle_max_arc_angle_per_segment = _parse_value_with_unit(
        _get_first_present(
            extrude_data,
            "circleMaxArcAnglePerSegment",
            "circle_max_arc_angle_per_segment",
        )
    )
    circle_fit_tolerance_fraction = _get_first_present(
        extrude_data,
        "circleFitToleranceFraction",
        "circle_fit_tolerance_fraction",
    )
    iterative_max_iterations = _get_first_present(
        extrude_data,
        "iterativeMaxIterations",
        "iterative_max_iterations",
    )

    if all(
        value is None
        for value in (
            unify_layer_discretizations,
            fuzzy_value,
            feature_angle_threshold,
            length_ratio_threshold,
            spline_method,
            spline_tolerance,
            circle_max_arc_angle_per_segment,
            circle_fit_tolerance_fraction,
            iterative_max_iterations,
        )
    ):
        return None

    return CadGdsExtrudeParameters(
        unify_layer_discretizations=unify_layer_discretizations,
        fuzzy_value=fuzzy_value,
        feature_angle_threshold=feature_angle_threshold,
        length_ratio_threshold=length_ratio_threshold,
        spline_method=spline_method,
        spline_tolerance=spline_tolerance,
        circle_max_arc_angle_per_segment=circle_max_arc_angle_per_segment,
        circle_fit_tolerance_fraction=circle_fit_tolerance_fraction,
        iterative_max_iterations=iterative_max_iterations,
    )


def _parse_cad_path_segment(segment: Any) -> str | tuple[str, str] | CadGlob:
    """Parse a single CAD path segment from YAML data."""
    if isinstance(segment, str):
        if segment == "*":
            return CadGlob.STAR
        elif segment == "**":
            return CadGlob.DOUBLESTAR
        return segment
    elif isinstance(segment, dict):
        if "key" in segment and "value" in segment:
            return (segment["key"], segment["value"])
        raise ValueError(
            f"CAD path attribute segment must have 'key' and 'value': {segment}"
        )
    raise ValueError(f"Invalid CAD path segment: {segment}")


def _parse_cad_paths(
    geometry: dict,
    camel_key: str = "cadPaths",
    snake_key: str = "cad_paths",
) -> list[CadPath] | None:
    """Parse cadPaths/cad_paths from a geometry dict into a list of CadPath."""
    raw = geometry.get(camel_key) or geometry.get(snake_key)
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise ValueError(
            f"Expected a list for {camel_key}/{snake_key}, got {type(raw)}"
        )
    cad_paths: list[CadPath] = []
    for path_data in raw:
        if isinstance(path_data, list):
            cad_paths.append([_parse_cad_path_segment(seg) for seg in path_data])
        elif isinstance(path_data, str):
            cad_paths.append([_parse_cad_path_segment(path_data)])
        else:
            raise ValueError(
                f"Each CAD path must be a list of segments or a string, got {type(path_data)}"
            )
    return cad_paths if cad_paths else None


def _resolve_region_id(target: str, regions: dict[str, Region]) -> str:
    """
    Allow `target` to be given as a region name (from import file) or as a raw region id.
    """
    if target in regions:
        return regions[target].id
    return target


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _resolve_interaction_targets(
    interaction_class: type[Interaction],
    interaction_entry: dict[str, Any],
    regions: dict[str, Region],
) -> tuple[dict[str, Region | str | None], set[str]]:
    """
    Resolve interaction targets from YAML using class metadata.

    Supports:
    - interactions with targets via ``target`` (single), ``targets`` (dict/list),
      or direct top-level keys matching class target parameter names
    - targetless interactions (no target fields required)
    - camelCase and snake_case target dict keys
    - optional targets that may be omitted
    """

    consumed_keys: set[str] = {"target", "targets"}
    target_definition_ids = dict(
        getattr(interaction_class, "target_definition_ids", {}) or {}
    )

    if target_definition_ids:
        resolved_targets: dict[str, Region | str | None] = {}
        expected_keys = list(target_definition_ids.keys())
        optional_keys: set[str] = getattr(
            interaction_class, "optional_target_definition_ids", set()
        )
        required_keys = [k for k in expected_keys if k not in optional_keys]

        # Accept both camelCase and snake_case in targets dict
        key_lookup: dict[str, str] = {}
        for key in expected_keys:
            key_lookup[key] = key
            key_lookup[_snake_to_camel(key)] = key

        raw_targets = interaction_entry.get("targets")
        if raw_targets is not None:
            if isinstance(raw_targets, dict):
                for raw_key in raw_targets:
                    if raw_key not in key_lookup:
                        raise ValueError(
                            f"Unknown target key '{raw_key}' for interaction "
                            f"'{interaction_entry.get('type')}'. "
                            f"Expected keys: {expected_keys}"
                        )
                for raw_key, value in raw_targets.items():
                    if value is None:
                        continue
                    internal_key = key_lookup[raw_key]
                    resolved_targets[internal_key] = _resolve_region_id(
                        str(value), regions
                    )
            elif isinstance(raw_targets, list):
                if len(raw_targets) != len(expected_keys):
                    raise ValueError(
                        f"Interaction '{interaction_entry.get('type')}' expects "
                        f"{len(expected_keys)} targets, got {len(raw_targets)}"
                    )
                for key, value in zip(expected_keys, raw_targets):
                    if value is None:
                        continue
                    resolved_targets[key] = _resolve_region_id(str(value), regions)
            else:
                raise ValueError(
                    f"Interaction 'targets' must be an object or list, "
                    f"got {type(raw_targets).__name__}: {raw_targets}"
                )

        # Also allow direct top-level target keys (snake_case and camelCase).
        for key in expected_keys:
            consumed_keys.add(key)
            camel_key = _snake_to_camel(key)
            consumed_keys.add(camel_key)
            for k in (key, camel_key):
                if k in interaction_entry and interaction_entry[k] is not None:
                    resolved_targets[key] = _resolve_region_id(
                        str(interaction_entry[k]), regions
                    )

        # Shorthand: "target" maps to the single required key.
        if interaction_entry.get("target") is not None:
            if len(required_keys) == 1 and required_keys[0] not in resolved_targets:
                resolved_targets[required_keys[0]] = _resolve_region_id(
                    str(interaction_entry["target"]), regions
                )
            elif len(required_keys) > 1:
                raise ValueError(
                    f"Interaction '{interaction_entry.get('type')}' has multiple "
                    "required targets; provide targets via 'targets' or explicit "
                    "target keys"
                )

        if not resolved_targets:
            raise ValueError(
                f"Interaction '{interaction_entry.get('type')}' is missing targets. "
                f"Expected keys: {expected_keys}"
            )

        missing_keys = [
            key
            for key in expected_keys
            if key not in resolved_targets and key not in optional_keys
        ]
        if missing_keys:
            raise ValueError(
                f"Interaction '{interaction_entry.get('type')}' is missing "
                f"required target keys: {missing_keys}"
            )

        auto_determined: set[str] = getattr(
            interaction_class, "auto_determined_targets", set()
        )
        for key in auto_determined:
            if key in resolved_targets:
                import warnings

                warnings.warn(
                    f"Interaction '{interaction_entry.get('name') or interaction_entry.get('type')}': "
                    f"target '{_snake_to_camel(key)}' is auto-determined by the "
                    f"solver and may be ignored.",
                    stacklevel=2,
                )

        return resolved_targets, consumed_keys

    # Targetless interaction
    if interaction_entry.get("target") is not None or interaction_entry.get(
        "targets"
    ) not in (
        None,
        {},
        [],
    ):
        raise ValueError(
            f"Interaction '{interaction_entry.get('type')}' does not accept targets"
        )
    return {}, consumed_keys


def import_physics_and_interactions(
    project: Project,
    physics_list: list[dict] | None,
    regions: dict[str, Region],
    verbose: bool = False,
):
    """
    Import physics and nested interactions.

    Expected format:
      physics:
        - type: solidMechanics  # or solid_mechanics
          target: cubes         # region name or id
          interactions:
            - type: load
              name: Load
              target: some_surface_region
              force: \"[0; 0; -1000]\"
    """
    if not physics_list:
        return

    if not isinstance(physics_list, list):
        raise ValueError(f"'physics' must be a list, got {type(physics_list).__name__}")

    if verbose:
        print("Importing physics...")

    if project.id is None:
        raise ValueError("Project must have an id before importing physics")

    # Create all physics
    physics_with_interactions: list[tuple] = []
    for p in physics_list:
        if not isinstance(p, dict):
            raise ValueError(
                f"Each physics entry must be an object, got {type(p).__name__}: {p}"
            )
        ptype = p.get("type") or p.get("definition")
        if not ptype:
            raise ValueError(f"Physics entry missing 'type': {p}")

        physics_class = get_physics_class(str(ptype))
        if physics_class is None:
            raise ValueError(
                f"Unknown physics type '{ptype}': no matching Physics class found"
            )
        target = p.get("target")
        target_id = _resolve_region_id(str(target), regions) if target else None
        physic = project.add_physics(physics_class(target=target_id))

        interactions = p.get("interactions", [])
        if interactions is None:
            interactions = []
        if interactions:
            if not isinstance(interactions, list):
                raise ValueError(
                    f"Physics 'interactions' must be a list, got {type(interactions).__name__}: {interactions}"
                )
            physics_with_interactions.append((physic, interactions))

    # Import interactions for each physics
    for physic, interactions in physics_with_interactions:
        import_interactions_for_physics(
            project=project,
            physic=physic,
            interactions=interactions,
            regions=regions,
            verbose=verbose,
        )


def import_interactions_for_physics(
    project: Project,
    physic: Physic,
    interactions: list[dict],
    regions: dict[str, Region],
    verbose: bool = False,
):
    """
    Import interactions nested under a physics entry.

    Parameters are provided at the top level of each interaction entry (camelCase or snake_case keys).
    """
    if verbose:
        print("Importing physics interactions...")

    if project.id is None:
        raise ValueError("Project must have an id before importing interactions")

    if not isinstance(interactions, list):
        raise ValueError(
            f"Physics 'interactions' must be a list, got {type(interactions).__name__}: {interactions}"
        )

    top_level_skip_base = {"type", "definition", "name", "enabled", "namespace"}

    specs = []
    for i in interactions:
        if not isinstance(i, dict):
            raise ValueError(
                f"Each interaction entry must be an object, got {type(i).__name__}: {i}"
            )
        itype = i.get("type") or i.get("definition")
        if not itype:
            raise ValueError(f"Interaction entry missing 'type': {i}")

        interaction_class = get_interaction_class(physic.definition, str(itype))
        if interaction_class is None:
            raise ValueError(
                f"Unknown interaction type '{itype}' for physics '{physic.definition}'"
            )

        name = i.get("name") or str(itype)

        target_ids, target_skip_keys = _resolve_interaction_targets(
            interaction_class=interaction_class,
            interaction_entry=i,
            regions=regions,
        )
        top_level_skip = top_level_skip_base | target_skip_keys

        enabled_raw = i.get("enabled")
        enabled = boolean_to_str(enabled_raw) if enabled_raw is not None else None

        # Build InteractionParameter list from top-level keys
        parameters: list[InteractionParameter] = []
        provided_keys: set[str] = set()
        for k, v in i.items():
            if k in top_level_skip:
                continue
            if v is None:
                continue
            provided_keys.add(k)
            str_val = boolean_to_str(v)
            if str_val.startswith(k):
                parameters.append(
                    InteractionParameter(definition=str(k), ascii_value=str_val)
                )
            else:
                parameters.append(
                    InteractionParameter(definition=str(k), value=str_val)
                )
        # Fill in defaults for parameters not provided in the YAML
        for param_id, default_val in get_interaction_parameter_defaults(
            str(itype)
        ).items():
            if param_id not in provided_keys:
                if default_val.startswith(param_id):
                    parameters.append(
                        InteractionParameter(
                            definition=param_id, ascii_value=default_val
                        )
                    )
                else:
                    parameters.append(
                        InteractionParameter(definition=param_id, value=default_val)
                    )
        namespace_raw = i.get("namespace")
        namespace = str(namespace_raw) if namespace_raw is not None else None

        # Bypass the generated subclass __init__ (which uses typed kwargs)
        # and call the base Interaction.__init__ which accepts parameters directly.
        instance = interaction_class.__new__(interaction_class)
        Interaction.__init__(
            instance,
            name=str(name),
            targets=target_ids if target_ids else None,
            enabled=enabled,
            namespace=namespace,
            parameters=parameters,
        )
        specs.append(instance)

    if specs:
        physic.add_interactions(specs)


def _expand_output_filter(
    otype: str,
    filter_spec: dict,
) -> tuple[list[InteractionParameter], set[str]]:
    """Expand a user-friendly filter dict into raw InteractionParameters.

    Supported YAML syntax::

        filter:
          type: EveryNthStep
          value: 5

    The ``type`` maps to ``{otype}FilterType{type}`` and the optional
    ``value`` maps to ``{otype}Filter{type}``.  When ``type`` is omitted
    it defaults to ``"None"`` (output every step).
    """

    filter_type_name = filter_spec.get("type", "None")

    filter_type_param_id = f"{otype}FilterType"
    filter_type_option_id = f"{otype}FilterType{filter_type_name}"

    params = [
        InteractionParameter(
            definition=filter_type_param_id, ascii_value=filter_type_option_id
        )
    ]
    keys = {filter_type_param_id}

    value = filter_spec.get("value")
    if value is not None:
        value_param_id = f"{otype}Filter{filter_type_name}"
        params.append(InteractionParameter(definition=value_param_id, value=str(value)))
        keys.add(value_param_id)

    return params, keys


def _resolve_output_alias(otype: str, key: str) -> str:
    """Map a friendly YAML key to the raw parameter ID, or return as-is."""
    pattern = _OUTPUT_PARAM_ALIASES.get(key)
    if pattern is not None:
        return pattern.replace("{otype}", otype)
    return key


def import_outputs_for_simulation(
    project: Project,
    simulation: Simulation,
    outputs: list[dict] | None,
    regions: dict[str, "Region"] | None = None,
    verbose: bool = False,
):
    """
    Import simulation output interactions (e.g. fieldOutput) nested under a simulation entry.

    Output parameters are provided at the top level (camelCase or snake_case keys).
    Friendly aliases are supported::

        expression  → {outputType}            (e.g. fieldOutput)
        skinOnly    → {outputType}SkinOnly    (e.g. fieldOutputSkinOnly)
        deformedMesh→ {outputType}DeformedMesh(e.g. fieldOutputDeformedMesh)

    A ``filter`` key is expanded into the raw filter parameters; see
    :func:`_expand_output_filter`.
    """
    if not outputs:
        return

    if not isinstance(outputs, list):
        raise ValueError(
            f"Simulation 'outputs' must be a list, got {type(outputs).__name__}"
        )

    if verbose:
        print("Importing simulation outputs...")

    if project.id is None:
        raise ValueError("Project must have an id before importing outputs")
    if simulation.id is None:
        raise ValueError("Simulation must have an id before importing outputs")

    top_level_skip = {
        "type",
        "args",
        "definition",
        "name",
        "enabled",
        "filter",
        "target",
    }

    specs = []
    for o in outputs:
        if not isinstance(o, dict):
            raise ValueError(
                f"Each output entry must be an object, got {type(o).__name__}: {o}"
            )

        otype = o.get("type") or o.get("definition")
        if not otype:
            raise ValueError(f"Output entry missing 'type': {o}")
        otype = _OUTPUT_TYPE_ALIASES.get(str(otype), str(otype))

        name = o.get("name") or str(otype)

        enabled = o.get("enabled", True)

        # Build InteractionParameter list from top-level keys
        parameters: list[InteractionParameter] = []
        args = o.get("args")
        if args not in (None, {}):
            raise ValueError(
                "Output 'args' is not supported; provide parameters at the top level"
            )
        provided_keys: set[str] = set()
        filter_spec = o.get("filter")
        if filter_spec is not None:
            if not isinstance(filter_spec, dict):
                raise ValueError(
                    f"Output 'filter' must be an object, got {type(filter_spec).__name__}"
                )
            filter_params, filter_keys = _expand_output_filter(str(otype), filter_spec)
            parameters.extend(filter_params)
            provided_keys.update(filter_keys)
        for k, v in o.items():
            if k in top_level_skip:
                continue
            if v is None:
                continue
            param_id = _resolve_output_alias(str(otype), k)
            provided_keys.add(param_id)
            parameters.append(InteractionParameter(definition=param_id, value=str(v)))
        # Fill in defaults for parameters not provided in the YAML
        for param_id, default_val in get_output_parameter_defaults(str(otype)).items():
            if param_id not in provided_keys:
                if default_val.startswith(param_id):
                    parameters.append(
                        InteractionParameter(
                            definition=param_id, ascii_value=default_val
                        )
                    )
                else:
                    parameters.append(
                        InteractionParameter(definition=param_id, value=default_val)
                    )
        output_class = get_output_class(str(otype))
        if output_class is None:
            raise ValueError(f"Unknown output type '{otype}'")

        targets: dict[str, Region | str | None] | None = None
        raw_target = o.get("target")
        if raw_target is not None and regions:
            targets = {"target": _resolve_region_id(str(raw_target), regions)}

        instance = output_class.__new__(output_class)
        OutputInteraction.__init__(
            instance,
            name=str(name),
            targets=targets,
            enabled=enabled,
            parameters=parameters,
        )
        specs.append(instance)

    if specs:
        simulation.add_outputs(specs)


def import_cad_geometries(
    project: Project,
    geometries: dict,
    yaml_file_path: Path | None = None,
    verbose: bool = False,
    *,
    allow_paths_outside_project: bool = False,
):
    if verbose:
        print("Importing CAD geometries...")

    def _rp(fp: str) -> str:
        return _resolve_path(
            fp,
            yaml_file_path,
            allow_paths_outside_project=allow_paths_outside_project,
        )

    geometry_builder = project.geometry_builder()

    for geometry in geometries:
        if geometry["type"] == "box":
            position = parse_tuple(geometry["position"])
            size = parse_tuple(geometry["size"])
            rotation = parse_tuple(geometry.get("rotation"))
            name = geometry["name"]
            if position is None or size is None:
                raise ValueError("Box requires position and size")
            geometry_builder.add(
                CadBox(
                    position=position,  # type: ignore[arg-type]
                    size=size,  # type: ignore[arg-type]
                    rotation=rotation,  # type: ignore[arg-type]
                    alignment=(
                        CadAlignment(geometry["alignment"])
                        if geometry.get("alignment")
                        else None
                    ),
                    name=name,
                )
            )
        elif geometry["type"] == "cylinder":
            position = parse_tuple(geometry["position"])
            axis = parse_tuple(geometry["axis"])
            rotation = parse_tuple(geometry.get("rotation"))
            if position is None or axis is None:
                raise ValueError("Cylinder requires position and axis")
            geometry_builder.add(
                CadCylinder(
                    position=position,  # type: ignore[arg-type]
                    axis=axis,  # type: ignore[arg-type]
                    radius=geometry["radius"],
                    name=geometry["name"],
                    inner_radius=geometry.get("innerRadius"),
                    angle1=geometry.get("angle1"),
                    angle2=geometry.get("angle2"),
                    rotation=rotation,  # type: ignore[arg-type]
                    alignment=(
                        CadAlignment(geometry["alignment"])
                        if geometry.get("alignment")
                        else None
                    ),
                )
            )
        elif geometry["type"] == "sphere":
            position = parse_tuple(geometry["position"])
            rotation = parse_tuple(geometry.get("rotation"))
            if position is None:
                raise ValueError("Sphere requires position")
            geometry_builder.add(
                CadSphere(
                    position=position,  # type: ignore[arg-type]
                    radius=geometry["radius"],
                    name=geometry["name"],
                    inner_radius=geometry.get("innerRadius"),
                    rotation=rotation,  # type: ignore[arg-type]
                    angle1=geometry.get("angle1"),
                    angle2=geometry.get("angle2"),
                )
            )
        elif geometry["type"] == "cone":
            position = parse_tuple(geometry["position"])
            axis = parse_tuple(geometry["axis"])
            rotation = parse_tuple(geometry.get("rotation"))
            if position is None or axis is None:
                raise ValueError("Cone requires position and axis")
            geometry_builder.add(
                CadCone(
                    position=position,  # type: ignore[arg-type]
                    axis=axis,  # type: ignore[arg-type]
                    radius1=geometry["radius1"],
                    radius2=geometry["radius2"],
                    name=geometry["name"],
                    angle1=geometry.get("angle1"),
                    angle2=geometry.get("angle2"),
                    rotation=rotation,  # type: ignore[arg-type]
                    alignment=(
                        CadAlignment(geometry["alignment"])
                        if geometry.get("alignment")
                        else None
                    ),
                )
            )
        elif geometry["type"] == "torus":
            position = parse_tuple(geometry["position"])
            rotation = parse_tuple(geometry.get("rotation"))
            if position is None:
                raise ValueError("Torus requires position")
            geometry_builder.add(
                CadTorus(
                    position=position,  # type: ignore[arg-type]
                    radius1=geometry["radius1"],
                    radius2=geometry["radius2"],
                    name=geometry["name"],
                    inner_radius=geometry.get("innerRadius"),
                    angle1=geometry.get("angle1"),
                    angle2=geometry.get("angle2"),
                    rotation=rotation,  # type: ignore[arg-type]
                )
            )
        elif geometry["type"] == "disk":
            position = parse_tuple(geometry["position"], 2)
            rotation = parse_tuple(geometry.get("rotation"))
            if position is None:
                raise ValueError("Disk requires position")
            geometry_builder.add(
                CadDisk(
                    position=position,  # type: ignore[arg-type]
                    radius=geometry["radius"],
                    name=geometry["name"],
                    inner_radius=geometry.get("innerRadius"),
                    angle1=geometry.get("angle1"),
                    angle2=geometry.get("angle2"),
                    rotation=rotation,  # type: ignore[arg-type]
                )
            )
        elif geometry["type"] == "rectangle":
            position = parse_tuple(geometry["position"], 2)
            size = parse_tuple(geometry["size"], 2)
            rotation = parse_tuple(geometry.get("rotation"))
            if position is None or size is None:
                raise ValueError("Rectangle requires position and size")
            geometry_builder.add(
                CadRectangle(
                    position=position,  # type: ignore[arg-type]
                    size=size,  # type: ignore[arg-type]
                    name=geometry["name"],
                    rotation=rotation,  # type: ignore[arg-type]
                    alignment=(
                        CadAlignment(geometry["alignment"])
                        if geometry.get("alignment")
                        else None
                    ),
                )
            )
        elif geometry["type"] == "surfaceRectangle":
            # Handle CadPoint creation - support both tag (int) and name (str)
            def create_cad_point(point_data):
                if isinstance(point_data, int):
                    return CadPoint(tag=point_data)
                elif isinstance(point_data, str):
                    return CadPoint(name=point_data)
                elif isinstance(point_data, dict):
                    if "tag" in point_data:
                        return CadPoint(tag=point_data["tag"])
                    elif "name" in point_data:
                        return CadPoint(name=point_data["name"])
                    else:
                        raise ValueError("CadPoint must have either 'tag' or 'name'")
                else:
                    raise ValueError(f"Invalid CadPoint format: {point_data}")

            size = parse_tuple(geometry["size"], 2)
            offset = parse_tuple(geometry["offset"])
            if size is None or offset is None:
                raise ValueError("SurfaceRectangle requires size and offset")
            geometry_builder.add(
                CadSurfaceRectangle(
                    name=geometry["name"],
                    size=size,  # type: ignore[arg-type]
                    offset=offset,  # type: ignore[arg-type]
                    origin_point=create_cad_point(geometry["originPoint"]),
                    main_axis_point=create_cad_point(geometry["mainAxisPoint"]),
                    secondary_axis_point=create_cad_point(
                        geometry["secondaryAxisPoint"]
                    ),
                )
            )
        elif geometry["type"] == "step":
            filepath = _rp(geometry["filepath"])
            cleanup = geometry.get("cleanup", False)
            step_file = CadStepFile(
                filepath=filepath, name=geometry.get("name"), cleanup=cleanup
            )
            geometry_builder.add(step_file)
        elif geometry["type"] == "iges":
            filepath = _rp(geometry["filepath"])
            cleanup = geometry.get("cleanup", False)
            iges_file = CadIgesFile(
                filepath=filepath, name=geometry.get("name"), cleanup=cleanup
            )
            geometry_builder.add(iges_file)
        elif geometry["type"] == "sat":
            filepath = _rp(geometry["filepath"])
            cleanup = geometry.get("cleanup", False)
            sat_file = CadSatFile(
                filepath=filepath, name=geometry.get("name"), cleanup=cleanup
            )
            geometry_builder.add(sat_file)
        elif geometry["type"] == "brep":
            filepath = _rp(geometry["filepath"])
            cleanup = geometry.get("cleanup", False)
            brep_file = CadBrepFile(
                filepath=filepath, name=geometry.get("name"), cleanup=cleanup
            )
            geometry_builder.add(brep_file)
        elif geometry["type"] == "gds2":
            filepath = _rp(geometry["filepath"])
            cleanup = geometry.get("cleanup", False)
            unit = geometry.get("unit", None)
            # Parse layers
            layers = []
            for layer_data in geometry.get("layers", []):
                layers.append(
                    CadGdsLayer(
                        layer=layer_data["layer"],
                        type=layer_data["type"],
                        absolute_z0=_get_first_present(
                            layer_data, "absoluteZ0", "absolute_z0"
                        ),
                        thickness=layer_data["thickness"],
                        previous_layer_index=_get_first_present(
                            layer_data,
                            "previousLayerIndex",
                            "previous_layer_index",
                        ),
                        name=layer_data.get("name"),
                    )
                )
            if not layers:
                raise ValueError("GDS2 file requires at least one layer")
            extrude_parameters = _parse_gds_extrude_parameters(
                _get_first_present(geometry, "extrudeParameters", "extrude_parameters")
            )
            gds2_file = CadGds2File(
                filepath=filepath,
                layers=layers,
                name=geometry.get("name"),
                cleanup=cleanup,
                extrude_parameters=extrude_parameters,
                unit=create_distance_unit(unit) or CadDistanceUnit.MICROMETER,
            )
            geometry_builder.add(gds2_file)
        elif geometry["type"] == "union":
            name = geometry["name"]
            entity_tags = geometry.get("entityTags") or geometry.get("entity_tags")
            cad_names = geometry.get("cadNames") or geometry.get("cad_names")
            cad_paths = _parse_cad_paths(geometry)
            union = CadUnion(
                name=name,
                entity_tags=entity_tags,
                cad_names=cad_names,
                cad_paths=cad_paths,
            )
            geometry_builder.add(union)
        elif geometry["type"] == "difference":
            name = geometry["name"]
            entity_tags_1 = geometry.get("entityTags1") or geometry.get("entity_tags_1")
            cad_names_1 = geometry.get("cadNames1") or geometry.get("cad_names_1")
            cad_paths_1 = _parse_cad_paths(geometry, "cadPaths1", "cad_paths_1")
            entity_tags_2 = geometry.get("entityTags2") or geometry.get("entity_tags_2")
            cad_names_2 = geometry.get("cadNames2") or geometry.get("cad_names_2")
            cad_paths_2 = _parse_cad_paths(geometry, "cadPaths2", "cad_paths_2")
            delete_tool = geometry.get("deleteTool", geometry.get("delete_tool", True))
            difference = CadDifference(
                name=name,
                entity_tags_1=entity_tags_1,
                cad_names_1=cad_names_1,
                cad_paths_1=cad_paths_1,
                entity_tags_2=entity_tags_2,
                cad_names_2=cad_names_2,
                cad_paths_2=cad_paths_2,
                delete_tool=delete_tool,
            )
            geometry_builder.add(difference)
        elif geometry["type"] == "intersection":
            name = geometry["name"]
            entity_tags_1 = geometry.get("entityTags1") or geometry.get("entity_tags_1")
            cad_names_1 = geometry.get("cadNames1") or geometry.get("cad_names_1")
            cad_paths_1 = _parse_cad_paths(geometry, "cadPaths1", "cad_paths_1")
            entity_tags_2 = geometry.get("entityTags2") or geometry.get("entity_tags_2")
            cad_names_2 = geometry.get("cadNames2") or geometry.get("cad_names_2")
            cad_paths_2 = _parse_cad_paths(geometry, "cadPaths2", "cad_paths_2")
            delete_tool = geometry.get("deleteTool", geometry.get("delete_tool", True))
            intersection = CadIntersection(
                name=name,
                entity_tags_1=entity_tags_1,
                cad_names_1=cad_names_1,
                cad_paths_1=cad_paths_1,
                entity_tags_2=entity_tags_2,
                cad_names_2=cad_names_2,
                cad_paths_2=cad_paths_2,
                delete_tool=delete_tool,
            )
            geometry_builder.add(intersection)
        elif geometry["type"] == "fragments":
            name = geometry["name"]
            entity_tags_1 = geometry.get("entityTags1") or geometry.get("entity_tags_1")
            cad_names_1 = geometry.get("cadNames1") or geometry.get("cad_names_1")
            cad_paths_1 = _parse_cad_paths(geometry, "cadPaths1", "cad_paths_1")
            entity_tags_2 = geometry.get("entityTags2") or geometry.get("entity_tags_2")
            cad_names_2 = geometry.get("cadNames2") or geometry.get("cad_names_2")
            cad_paths_2 = _parse_cad_paths(geometry, "cadPaths2", "cad_paths_2")
            delete_tool = geometry.get("deleteTool", geometry.get("delete_tool", True))
            fragments = CadFragments(
                name=name,
                entity_tags_1=entity_tags_1,
                cad_names_1=cad_names_1,
                cad_paths_1=cad_paths_1,
                entity_tags_2=entity_tags_2,
                cad_names_2=cad_names_2,
                cad_paths_2=cad_paths_2,
                delete_tool=delete_tool,
            )
            geometry_builder.add(fragments)
        elif geometry["type"] == "fragmentAll" or geometry["type"] == "fragment_all":
            name = geometry["name"]
            fragment_all = CadFragmentAll(name=name)
            geometry_builder.add(fragment_all)
        elif geometry["type"] == "translate":
            name = geometry["name"]
            translation = parse_tuple(geometry["translation"])
            if translation is None:
                raise ValueError("Translate requires translation")
            entity_tags = geometry.get("entityTags") or geometry.get("entity_tags")
            cad_names = geometry.get("cadNames") or geometry.get("cad_names")
            cad_paths = _parse_cad_paths(geometry)
            copy_object = geometry.get("copyObject", geometry.get("copy_object", False))
            repeat = geometry.get("repeat")
            translate = CadTranslate(
                name=name,
                translation=translation,  # type: ignore[arg-type]
                entity_tags=entity_tags,
                cad_names=cad_names,
                cad_paths=cad_paths,
                copy_object=copy_object,
                repeat=repeat,
            )
            geometry_builder.add(translate)
        elif geometry["type"] == "rotate":
            name = geometry["name"]
            axis = parse_tuple(geometry["axis"])
            center = parse_tuple(geometry["center"])
            angle = geometry["angle"]
            if axis is None or center is None:
                raise ValueError("Rotate requires axis and center")
            entity_tags = geometry.get("entityTags") or geometry.get("entity_tags")
            cad_names = geometry.get("cadNames") or geometry.get("cad_names")
            cad_paths = _parse_cad_paths(geometry)
            copy_object = geometry.get("copyObject", geometry.get("copy_object", False))
            repeat = geometry.get("repeat")
            rotate = CadRotate(
                name=name,
                axis=axis,  # type: ignore[arg-type]
                center=center,  # type: ignore[arg-type]
                angle=angle,
                entity_tags=entity_tags,
                cad_names=cad_names,
                cad_paths=cad_paths,
                copy_object=copy_object,
                repeat=repeat,
            )
            geometry_builder.add(rotate)
        elif geometry["type"] == "grid":
            name = geometry["name"]
            translation = parse_tuple(geometry["translation"])
            size = parse_tuple(geometry["size"])
            if translation is None or size is None:
                raise ValueError("Grid requires translation and size")
            entity_tags = geometry.get("entityTags") or geometry.get("entity_tags")
            cad_names = geometry.get("cadNames") or geometry.get("cad_names")
            cad_paths = _parse_cad_paths(geometry)
            grid = CadGrid(
                name=name,
                translation=translation,  # type: ignore[arg-type]
                size=size,  # type: ignore[arg-type]
                entity_tags=entity_tags,
                cad_names=cad_names,
                cad_paths=cad_paths,
            )
            geometry_builder.add(grid)
        elif geometry["type"] == "remove":
            name = geometry["name"]
            entity_tags = geometry.get("entityTags") or geometry.get("entity_tags")
            cad_names = geometry.get("cadNames") or geometry.get("cad_names")
            cad_paths = _parse_cad_paths(geometry)
            remove = CadRemove(
                name=name,
                entity_tags=entity_tags,
                cad_names=cad_names,
                cad_paths=cad_paths,
            )
            geometry_builder.add(remove)
        else:
            raise ValueError(f"Unknown geometry type: {geometry['type']}")

    geometry_builder.build(print_logs=verbose, on_error=OnError.RAISE)


def import_geometry(
    project: Project,
    geometry: dict,
    yaml_file_path: Path | None = None,
    verbose: bool = False,
    *,
    allow_paths_outside_project: bool = False,
):
    if verbose:
        print(f"Importing geometry from {geometry['filename']}")

    filename = _resolve_path(
        geometry["filename"],
        yaml_file_path,
        allow_paths_outside_project=allow_paths_outside_project,
    )
    name = geometry.get("name")
    if geometry["type"] == "sat":
        geom = project.import_sat(filename, name=name)
    elif geometry["type"] == "step":
        geom = project.import_step(filename, name=name)
    elif geometry["type"] == "iges":
        geom = project.import_iges(filename, name=name)
    else:
        raise ValueError(f"Unknown geometry type: {geometry['type']}")

    geom.start()

    while geom.is_running(refresh_delay_s=1):
        if verbose:
            geom.print_new_loglines()

    if verbose:
        geom.print_new_loglines()

    if geom.get_status() != Job.SUCCESS:
        raise ValueError(f"Geometry import failed: {geom.get_status()}")


def import_variables(project: Project, variables: list[dict], verbose: bool = False):
    if verbose:
        print("Importing variables...")

    result = {}

    for variable in variables:
        result[variable["name"]] = project.create_variable(
            name=variable["name"],
            expression=variable["expression"],
            description=variable.get("description", ""),
        )

    return result


def import_functions(
    project: Project,
    functions: list[dict],
    yaml_file_path: Path | None = None,
    verbose: bool = False,
    *,
    allow_paths_outside_project: bool = False,
):
    if verbose:
        print("Importing functions...")

    for function in functions:
        if function["type"] == "regular":
            project.create_function(
                name=function["name"],
                args=[arg["name"] for arg in function["args"]],
                expression=function["expression"],
                description=function.get("description", ""),
            )
        elif function["type"] == "interpolated":
            if "fromCsv" in function:
                csv_path = _resolve_path(
                    function["fromCsv"],
                    yaml_file_path,
                    allow_paths_outside_project=allow_paths_outside_project,
                )
                with open(csv_path, "r") as f:
                    csv_data = csv.reader(f)
                    values = []
                    argsDict: dict[str, list[float]] = {}
                    for row in csv_data:
                        values.append(float(row[0]))
                        for i, col in enumerate(row[1:]):
                            if f"arg{i}" not in argsDict:
                                argsDict[f"arg{i}"] = []
                            argsDict[f"arg{i}"].append(float(col))
                    args = [(arg, argsDict[arg]) for arg in argsDict]
            else:
                values = function["values"]
                args = [(arg["name"], arg["values"]) for arg in function["args"]]

            project.create_interpolated_function(
                name=function["name"],
                args=args,
                values=values,
                description=function.get("description", ""),
                cubic_interpolation=function.get("cubicInterpolation"),
            )


def import_regions(project: Project, regions: list[dict], verbose: bool = False):
    if verbose:
        print("Importing regions...")

    imported_regions = {}

    for region in regions:
        shared = region.get("shared", True)

        attribute_path = None
        raw_attribute_path = region.get("attributePath")
        if raw_attribute_path:
            attribute_path = KeyValueAttributePath(
                path=[
                    (
                        attribute["key"],
                        attribute["value"],
                    )
                    for attribute in raw_attribute_path
                ],
            )

        bounding_box = None
        if "boundingBox" in region:
            bounding_box = ExpressionBoundingBox(
                min=ExpressionVector(
                    x=str(region["boundingBox"]["min"]["x"]),
                    y=str(region["boundingBox"]["min"]["y"]),
                    z=str(region["boundingBox"]["min"]["z"]),
                ),
                max=ExpressionVector(
                    x=str(region["boundingBox"]["max"]["x"]),
                    y=str(region["boundingBox"]["max"]["y"]),
                    z=str(region["boundingBox"]["max"]["z"]),
                ),
            )

        max_size = None
        if "maxSize" in region:
            max_size = ExpressionVector(
                x=str(region["maxSize"]["x"]),
                y=str(region["maxSize"]["y"]),
                z=str(region["maxSize"]["z"]),
            )

        min_size = None
        if "minSize" in region:
            min_size = ExpressionVector(
                x=str(region["minSize"]["x"]),
                y=str(region["minSize"]["y"]),
                z=str(region["minSize"]["z"]),
            )

        if region["type"] == "regionRule":
            imported_regions[region["name"]] = project.create_region_rule(
                name=region["name"],
                entity_type=region["entityType"],
                attribute_path=attribute_path,
                bounding_box=bounding_box,
                max_size=max_size,
                min_size=min_size,
                shared=shared,
            )
        elif region["type"] == "basic":
            imported_regions[region["name"]] = project.create_region_basic(
                name=region["name"],
                entity_type=region["entityType"],
                entity_tags=region["entityTags"],
                shared=shared,
            )
        elif region["type"] == "computed":
            entity_type = Region.VOLUME
            if region["entityType"] == "volume":
                entity_type = Region.VOLUME
            elif region["entityType"] == "surface":
                entity_type = Region.SURFACE
            elif region["entityType"] == "curve":
                entity_type = Region.CURVE
            elif region["entityType"] == "point":
                entity_type = Region.POINT

            operation = RegionOperation.UNION
            if region["operation"] == "union":
                operation = RegionOperation.UNION
            elif region["operation"] == "intersection":
                operation = RegionOperation.INTERSECTION
            elif region["operation"] == "difference":
                operation = RegionOperation.DIFFERENCE
            elif region["operation"] == "symmetricDifference":
                operation = RegionOperation.SYMMETRIC_DIFFERENCE
            elif region["operation"] == "boundary":
                operation = RegionOperation.BOUNDARY
            elif region["operation"] == "complement":
                operation = RegionOperation.COMPLEMENT

            imported_regions[region["name"]] = project.create_region_computed(
                name=region["name"],
                entity_type=entity_type,
                operation=operation,
                source_regions=[
                    imported_regions[region].id for region in region["regions"]
                ],
                shared=shared,
            )
        elif region["type"] == "geometrySelector":
            imported_regions[region["name"]] = project.create_region_rule(
                name=region["name"],
                entity_type=region["entityType"],
                attribute_path=attribute_path,
                bounding_box=bounding_box,
                max_size=max_size,
                min_size=min_size,
                shared=shared,
            )
        else:
            raise ValueError(f"Unknown region type: {region['type']}")

    return imported_regions


def import_materials(
    project: Project, materials: list[dict], regions: dict, verbose: bool = False
):
    if verbose:
        print("Importing materials...")

    for material in materials:
        if list(material.keys()) == ["name"]:
            Material.create_from_library(
                name=material["name"],
                project_id=project.id,
            )
            if verbose:
                print(f"  Created material from library: {material['name']}")
            continue

        # Initialize all material arguments to None
        name = None
        description = None
        color = None
        abbreviation = None
        target_region = None
        coefficientOfThermalExpansion = None
        density = None
        dynamicViscosity = None
        elasticityMatrix: (
            MaterialProperty.ElasticityMatrixYoungsModulusPoissonsRatio
            | MaterialProperty.ElasticityMatrixPressureShearVelocity
            | MaterialProperty.ElasticityMatrix
            | None
        ) = None
        electricConductivity = None
        electricPermittivity = None
        heatCapacity = None
        magneticPermeability = None
        massDampingCoefficient = None
        piezoelectricCoupling = None
        pronySeries = None
        speedOfSound = None
        stiffnessDampingCoefficient = None
        thermalConductivity = None

        # Set values from material dict if they exist
        name = material["name"]
        description = material.get("description", "")
        color = material.get("color", "#000000")
        abbreviation = material.get("abbreviation", "")
        orientation = material.get("orientation", "")
        enabled = material.get("enabled", "")

        if "target" in material:
            target_region = regions[material["target"]]

        coefficientOfThermalExpansion = material.get("coefficientOfThermalExpansion")
        density = material.get("density")
        dynamicViscosity = material.get("dynamicViscosity")

        elasticityMatrixRaw = material.get("elasticityMatrix")
        if isinstance(elasticityMatrixRaw, dict):
            youngsModulus = elasticityMatrixRaw.get("youngsModulus")
            poissonsRatio = elasticityMatrixRaw.get("poissonsRatio")
            pressureWaveVelocity = elasticityMatrixRaw.get("pressureWaveVelocity")
            shearWaveVelocity = elasticityMatrixRaw.get("shearWaveVelocity")
            if youngsModulus is not None and poissonsRatio is not None:
                elasticityMatrix = (
                    MaterialProperty.ElasticityMatrixYoungsModulusPoissonsRatio(
                        youngsModulus,
                        poissonsRatio,
                    )
                )
            elif pressureWaveVelocity is not None and shearWaveVelocity is not None:
                elasticityMatrix = (
                    MaterialProperty.ElasticityMatrixPressureShearVelocity(
                        pressureWaveVelocity, shearWaveVelocity
                    )
                )
        elif elasticityMatrixRaw is not None:
            elasticityMatrix = MaterialProperty.ElasticityMatrix(
                value=elasticityMatrixRaw
            )

        electricConductivity = material.get("electricConductivity")
        electricPermittivity = material.get("electricPermittivity")
        heatCapacity = material.get("heatCapacity")
        magneticPermeability = material.get("magneticPermeability")
        massDampingCoefficient = material.get("massDampingCoefficient")
        piezoelectricCoupling = material.get("piezoelectricCoupling")

        if material.get("pronySeries") is not None:
            pronySeries = MaterialProperty.PronySeries(
                poisson_ratio=str(material["pronySeries"]["poissonsRatio"]),
                youngs_modulus=str(material["pronySeries"]["youngsModulus"]),
                relaxation_time=str(material["pronySeries"]["relaxationTime"]),
            )
        speedOfSound = material.get("speedOfSound")
        stiffnessDampingCoefficient = material.get("stiffnessDampingCoefficient")
        thermalConductivity = material.get("thermalConductivity")

        project.create_material(
            name=name,
            description=description,
            color=color,
            abbreviation=abbreviation,
            target_region=target_region,
            coefficient_of_thermal_expansion=coefficientOfThermalExpansion,
            density=density,
            dynamic_viscosity=dynamicViscosity,
            elasticity_matrix=elasticityMatrix,
            electric_conductivity=electricConductivity,
            electric_permittivity=electricPermittivity,
            heat_capacity=heatCapacity,
            magnetic_permeability=magneticPermeability,
            mass_damping_coefficient=massDampingCoefficient,
            piezoelectric_coupling=piezoelectricCoupling,
            prony_series=pronySeries,
            speed_of_sound=speedOfSound,
            stiffness_damping_coefficient=stiffnessDampingCoefficient,
            thermal_conductivity=thermalConductivity,
            orientation=orientation,
            enabled=enabled,
        )


def import_variable_overrides(
    project: Project,
    variable_overrides: list[dict],
    variables: dict,
    verbose: bool = False,
):
    if verbose:
        print("Importing variable overrides...")

    result = {}

    for variable_override in variable_overrides:
        result[variable_override["name"]] = project.create_variable_overrides(
            name=variable_override["name"],
            overrides=[
                (variables[override["variable"]], override["values"])
                for override in variable_override["overrides"]
            ],
            sweep_type=variable_override.get("sweepType", None),
        )

    return result


def _import_entity_selection(
    data: dict,
    key: str,
    regions: dict,
) -> tuple[list | None, list[int] | None]:
    """Read either region names or entity IDs from import data.

    Returns (region_objects, entity_ids) — at most one will be non-None.
    """
    entity_ids_key = f"{key}EntityIds"
    if entity_ids_key in data:
        return None, data[entity_ids_key]
    if key in data:
        return [regions[name] for name in data[key]], None
    return None, None


def import_meshes(
    project: Project,
    meshes: list[dict],
    regions: dict,
    variables_overrides: dict,
    verbose: bool = False,
) -> dict:
    if verbose:
        print("Importing meshes...")

    imported_meshes = {}

    for mesh_data in meshes:

        if verbose:
            print(f"Creating mesh {mesh_data['name']}...")

        refinements = []
        for refinement in mesh_data.get("refinements", []):
            if "tags" in refinement:
                if "entityType" not in refinement:
                    raise ValueError(
                        "'entityType' is required for tag-based refinements"
                    )
                entity_type_str = refinement["entityType"]
                refinements.append(
                    MeshRefinement(
                        max_size=refinement["maxSize"],
                        tags=refinement["tags"],
                        entity_type=RawEntityType(entity_type_str),
                    )
                )
            else:
                refinements.append(
                    MeshRefinement(
                        max_size=refinement["maxSize"],
                        region=regions[refinement["region"]],
                    )
                )

        extrusion = None
        if "simpleExtrusion" in mesh_data:
            extrusion_data = mesh_data["simpleExtrusion"]
            extrusion = MeshExtrusion(
                sub_layer_counts=[count for count in extrusion_data["subLayerCounts"]],
                regions=(
                    [regions[region] for region in extrusion_data["regions"]]
                    if "regions" in extrusion_data
                    else None
                ),
                volume_ids=extrusion_data.get("volumeIds"),
            )

        path_extrusions = None
        if "pathExtrusions" in mesh_data:
            path_extrusions = []
            for path_extrusion_data in mesh_data["pathExtrusions"]:
                vol_regions, vol_ids = _import_entity_selection(
                    path_extrusion_data,
                    "volumes",
                    regions,
                )
                from_regions, from_ids = _import_entity_selection(
                    path_extrusion_data,
                    "fromSurfaces",
                    regions,
                )
                to_regions, to_ids = _import_entity_selection(
                    path_extrusion_data,
                    "toSurfaces",
                    regions,
                )
                path_extrusions.append(
                    PathExtrusion(
                        volumes=vol_regions,
                        from_surfaces=from_regions,
                        to_surfaces=to_regions,
                        layers=[
                            ExtrusionLayerDefinition(
                                relative_height=layer["relativeHeight"],
                                sublayer_count=layer["subLayerCount"],
                            )
                            for layer in path_extrusion_data["layers"]
                        ],
                        quadrangles=path_extrusion_data.get("useQuadrangles", False),
                        volume_entity_ids=vol_ids,
                        from_surface_entity_ids=from_ids,
                        to_surface_entity_ids=to_ids,
                    )
                )

        slanted_extrusions = None
        if "slantedExtrusions" in mesh_data:
            slanted_extrusions = []
            for slanted_extrusion_data in mesh_data["slantedExtrusions"]:
                vol_regions, vol_ids = _import_entity_selection(
                    slanted_extrusion_data,
                    "volumes",
                    regions,
                )
                from_regions, from_ids = _import_entity_selection(
                    slanted_extrusion_data,
                    "fromSurfaces",
                    regions,
                )
                to_regions, to_ids = _import_entity_selection(
                    slanted_extrusion_data,
                    "toSurfaces",
                    regions,
                )
                slanted_extrusions.append(
                    SlantedExtrusion(
                        volumes=vol_regions,
                        from_surfaces=from_regions,
                        to_surfaces=to_regions,
                        layers=[
                            ExtrusionLayerDefinition(
                                relative_height=layer["relativeHeight"],
                                sublayer_count=layer["subLayerCount"],
                            )
                            for layer in slanted_extrusion_data["layers"]
                        ],
                        quadrangles=slanted_extrusion_data.get("useQuadrangles", False),
                        volume_entity_ids=vol_ids,
                        from_surface_entity_ids=from_ids,
                        to_surface_entity_ids=to_ids,
                    )
                )

        flatten_and_rebuild_extrusions = None
        if "flattenAndRebuildExtrusions" in mesh_data:
            flatten_and_rebuild_extrusions = []
            for flatten_and_rebuild_extrusion_data in mesh_data[
                "flattenAndRebuildExtrusions"
            ]:
                vol_regions, vol_ids = _import_entity_selection(
                    flatten_and_rebuild_extrusion_data,
                    "volumes",
                    regions,
                )
                direction_vector = None
                if "directionVector" in flatten_and_rebuild_extrusion_data:
                    direction_vector = ExpressionVector(
                        x=flatten_and_rebuild_extrusion_data["directionVector"]["x"],
                        y=flatten_and_rebuild_extrusion_data["directionVector"]["y"],
                        z=flatten_and_rebuild_extrusion_data["directionVector"]["z"],
                    )
                flatten_and_rebuild_extrusions.append(
                    FlattenAndRebuildExtrusion(
                        volumes=vol_regions,
                        layers=[
                            [
                                ExtrusionLayerDefinition(
                                    relative_height=layer["relativeHeight"],
                                    sublayer_count=layer["subLayerCount"],
                                )
                                for layer in flatten_and_rebuild_extrusion_data[
                                    "layers"
                                ]
                            ]
                        ],
                        quadrangles=flatten_and_rebuild_extrusion_data.get(
                            "useQuadrangles", False
                        ),
                        direction_vector=direction_vector,
                        volume_entity_ids=vol_ids,
                    )
                )

        auto_transfinite = None
        if "autoTransfinite" in mesh_data:
            auto_transfinite = []
            for at_entry in mesh_data["autoTransfinite"]:
                if "tags" in at_entry:
                    if "entityType" not in at_entry:
                        raise ValueError(
                            "'entityType' is required for tag-based auto-transfinite groups"
                        )
                    auto_transfinite.append(
                        AutoTransfiniteGroup(
                            hx=at_entry["hx"],
                            hy=at_entry["hy"],
                            hz=at_entry.get("hz"),
                            tags=at_entry["tags"],
                            entity_type=RawEntityType(at_entry["entityType"]),
                        )
                    )
                else:
                    auto_transfinite.append(
                        AutoTransfiniteGroup(
                            hx=at_entry["hx"],
                            hy=at_entry["hy"],
                            hz=at_entry.get("hz"),
                            region=regions[at_entry["region"]],
                        )
                    )

        variable_override = None
        if "variableOverride" in mesh_data:
            variable_override = variables_overrides[mesh_data["variableOverride"]]

        mesh = project.create_mesh(
            MeshSettings(
                name=mesh_data["name"],
                use_mesh_refiner=mesh_data.get("useMeshRefiner", True),
                scale_factor=mesh_data.get("scaleFactor", 1),
                curvature_enhancement=mesh_data.get("curvatureEnhancement", 6),
                curved_mesh=mesh_data.get("curvedMesh", False),
                target_width_to_height_ratio=mesh_data.get("targetWidthToHeightRatio"),
                max_run_time_minutes=mesh_data.get("maxRunTimeMinutes", 15),
                mesh_size_max=mesh_data.get("meshSizeMax"),
                mesh_size_min=mesh_data.get("meshSizeMin"),
                refinements=refinements,
                extrusion=extrusion,
                path_extrusions=path_extrusions,
                slanted_extrusions=slanted_extrusions,
                flatten_and_rebuild_extrusions=flatten_and_rebuild_extrusions,
                auto_transfinite=auto_transfinite,
                variable_overrides=[variable_override] if variable_override else None,
            ),
        )

        imported_meshes[mesh_data["name"]] = mesh

    return imported_meshes


def run_imported_meshes(
    meshes: list[dict],
    imported_meshes: dict,
    variables_overrides: dict,
    verbose: bool = False,
) -> None:

    for mesh_data in meshes:
        variable_override = None
        if "variableOverride" in mesh_data:
            variable_override = variables_overrides[mesh_data["variableOverride"]]

        mesh = imported_meshes[mesh_data["name"]]
        create_only = mesh_data.get("createOnly", False)
        if not create_only:
            if verbose:
                print(f"Running mesh {mesh_data['name']}...")

            if variable_override is not None:
                instance = mesh.get_override(variable_override=variable_override.id)
                instance.start()
                while instance.is_running(refresh_delay_s=1):
                    if verbose:
                        instance.print_new_loglines()
                if verbose:
                    instance.print_new_loglines()
                if instance.get_status() != Job.SUCCESS:
                    raise ValueError(
                        f"Mesh {mesh_data['name']} failed: {instance.get_status()}"
                    )
                if mesh_data.get("saveMesh", False):
                    instance.save_mesh_file(filename=f"{mesh_data['name']}.msh")
            else:
                mesh.start()
                while mesh.is_running(refresh_delay_s=1):
                    if verbose:
                        mesh.print_new_loglines()
                if verbose:
                    mesh.print_new_loglines()
                if mesh.get_status() != Job.SUCCESS:
                    raise ValueError(
                        f"Mesh {mesh_data['name']} failed: {mesh.get_status()}"
                    )
                if mesh_data.get("saveMesh", False):
                    mesh.save_mesh_file(filename=f"{mesh_data['name']}.msh")
        elif mesh_data.get("saveMesh", False) and verbose:
            print(
                f"Skipping saveMesh for {mesh_data['name']} because createOnly is true."
            )


def import_simulations(
    project: Project,
    simulations: list[dict],
    meshes: dict,
    variables_overrides: dict,
    yaml_file_path: Path | None = None,
    regions: dict[str, "Region"] | None = None,
    verbose: bool = False,
    *,
    allow_paths_outside_project: bool = False,
) -> dict[str, Simulation]:
    if verbose:
        print("Importing simulations...")

    imported_simulations: dict[str, Simulation] = {}

    for simulation_data in simulations:
        if verbose:
            print(f"Creating simulation {simulation_data['name']}...")

        # Parse solver mode
        solver_mode_str = simulation_data.get(
            "solverMode", SolverMode.DIRECT.value
        ).lower()
        if solver_mode_str == SolverMode.DIRECT.value:
            solver_mode = SolverMode.DIRECT
        elif solver_mode_str == SolverMode.ITERATIVE.value:
            solver_mode = SolverMode.ITERATIVE
        else:
            raise ValueError(
                f"Unknown solver mode: {simulation_data.get('solverMode')}. "
                f"Must be '{SolverMode.DIRECT.value}' or '{SolverMode.ITERATIVE.value}'"
            )

        # Parse analysis type
        analysis_type = None
        if "analysisType" in simulation_data:
            at_str = simulation_data["analysisType"]
            analysis_type_map = {
                "static": AnalysisType.STATIC,
                "harmonic": AnalysisType.HARMONIC,
                "multiharmonic": AnalysisType.MULTIHARMONIC,
                "transient": AnalysisType.TRANSIENT,
                "eigenmode": AnalysisType.EIGENMODE,
            }
            if at_str not in analysis_type_map:
                raise ValueError(
                    f"Unknown analysis type: {at_str}. "
                    f"Must be one of: {', '.join(analysis_type_map.keys())}"
                )
            analysis_type = analysis_type_map[at_str]

        # Parse timestep algorithm
        timestep_algorithm = None
        if "timestepAlgorithm" in simulation_data:
            ts_str = simulation_data["timestepAlgorithm"]
            if ts_str == "implicitEuler":
                timestep_algorithm = TimestepAlgorithm.IMPLICIT_EULER
            elif ts_str == "genAlpha":
                timestep_algorithm = TimestepAlgorithm.GEN_ALPHA
            else:
                raise ValueError(
                    f"Unknown timestep algorithm: {ts_str}. Must be 'implicitEuler' or 'genAlpha'"
                )

        # Resolve mesh ID
        mesh_id = None
        if "mesh" in simulation_data:
            mesh_name = simulation_data["mesh"]
            if mesh_name in meshes:
                mesh_id = meshes[mesh_name].id
            else:
                mesh_found = False
                for mesh in project.get_meshes():
                    if mesh.name == mesh_name:
                        mesh_id = mesh.id
                        mesh_found = True
                        break
                if not mesh_found:
                    raise ValueError(
                        f"Mesh with name '{mesh_name}' not found from imported project."
                    )

        # Resolve physics IDs
        physics = None
        if "physics" in simulation_data:
            enabled_physics_defs = simulation_data["physics"]
            project_physics = project.get_physics()
            definition_to_id = {p.definition: p.id for p in project_physics}
            id_set = {p.id for p in project_physics}
            physics = []
            for ref in enabled_physics_defs:
                if ref in definition_to_id:
                    physics.append(definition_to_id[ref])
                elif ref in id_set:
                    physics.append(ref)
                else:
                    raise ValueError(
                        f"Physics reference '{ref}' not found from imported project. "
                        f"Available physics in project: {list(definition_to_id.keys())}"
                    )

        sim = project.create_simulation(
            name=simulation_data["name"],
            description=simulation_data.get("description", ""),
            max_run_time_minutes=simulation_data.get("maxRunTimeMinutes", 10),
            solver_mode=solver_mode,
            mesh_id=mesh_id,
            analysis_type=analysis_type,
            harmonics=simulation_data.get("harmonics"),
            physics=physics,
            transient_start_time=simulation_data.get("transientStartTime"),
            transient_end_time=simulation_data.get("transientEndTime"),
            transient_timestep_size=simulation_data.get("transientTimestepSize"),
            timestep_algorithm=timestep_algorithm,
            fundamental_frequency=simulation_data.get("fundamentalFrequency"),
            num_fft_samples=simulation_data.get("numFFTSamples"),
            num_requested_eigenmodes=simulation_data.get("numRequestedEigenmodes"),
            target_eigenfrequency=simulation_data.get("targetEigenfrequency"),
            eigenmode_port_analysis=simulation_data.get("eigenmodePortAnalysis"),
            solver_tolerance=simulation_data.get("solverTolerance"),
            nonlinear_solver_tolerance=simulation_data.get("nonlinearSolverTolerance"),
            nonlinear_solver_max_iterations=simulation_data.get(
                "nonlinearSolverMaxIterations"
            ),
            eigenmode_solver_tolerance=simulation_data.get("eigenmodeSolverTolerance"),
            eigenmode_solver_max_iterations=simulation_data.get(
                "eigenmodeSolverMaxIterations"
            ),
            target_frequency=simulation_data.get("targetFrequency"),
            numerical_jacobian=simulation_data.get("numericalJacobian"),
        )

        # Set variable overrides if specified (requires lookup by name)
        if "variableOverride" in simulation_data:
            var_override_name = simulation_data["variableOverride"]
            var_override_found = False
            for var_override in project.get_variable_overrides():
                if var_override.name == var_override_name:
                    sim.variable_overrides = var_override
                    var_override_found = True
                    break
            if not var_override_found:
                raise ValueError(
                    f"Variable override with name '{var_override_name}' not found"
                )

        # Set runtime if specified
        if "runtime" in simulation_data:
            runtime_data = simulation_data["runtime"]
            node_type_str = runtime_data.get("nodeType", "CORES_3_10GB_FAST_START")
            node_count = runtime_data.get("nodeCount", 1)

            try:
                node_type = CPU[node_type_str]
            except KeyError:
                raise ValueError(
                    f"Unknown node type: {node_type_str}. Must be one of: "
                    f"{', '.join([e.name for e in CPU if e.name != 'DEFAULT'])}"
                )

            sim.set_runtime(Runtime(node_type=node_type, node_count=node_count))

        # Set scripts if specified
        if "scripts" in simulation_data:
            scripts = []
            for script_data in simulation_data["scripts"]:
                filepath = _resolve_path(
                    script_data["filepath"],
                    yaml_file_path,
                    allow_paths_outside_project=allow_paths_outside_project,
                )
                is_main = script_data.get("isMain", False)
                scripts.append(Script(filepath=filepath, is_main=is_main))
            sim.set_scripts(scripts)

        if "customScripts" in simulation_data:
            custom_scripts = []
            for cs_data in simulation_data["customScripts"]:
                section_val = cs_data["sectionName"]
                if isinstance(section_val, CustomScriptSectionName):
                    section_enum = CustomSection(section_val)
                else:
                    section_enum = CustomSection(CustomScriptSectionName(section_val))
                custom_scripts.append(
                    Script(
                        name=cs_data["name"],
                        section_name=section_enum,
                        content=cs_data["content"],
                    )
                )
            sim.set_scripts(custom_scripts)

        if "fieldInitializations" in simulation_data:
            field_inits = []
            for fi in simulation_data["fieldInitializations"]:
                source_sim_name = fi.get("sourceValueSimulationName")
                if source_sim_name is None:
                    source_sim_name = fi.get("sourceValueSimulationId")
                if source_sim_name is None:
                    raise ValueError(
                        "fieldInitialization must have 'sourceValueSimulationName'"
                    )
                if source_sim_name in imported_simulations:
                    source_sim_ref = imported_simulations[source_sim_name]
                else:
                    raise ValueError(
                        f"Source simulation '{source_sim_name}' not found. "
                        f"It must be defined before the simulation that references it. "
                        f"Available simulations: {list(imported_simulations.keys())}"
                    )

                field_ref: str | None = None
                if "field" in fi:
                    field_def = fi["field"]
                    physics_def = fi.get("physics")
                    resolved = False
                    for physic in project.get_physics():
                        if physics_def is not None and physic.definition != physics_def:
                            continue
                        for field in physic.fields:
                            if field.definition == field_def:
                                field_ref = field.id
                                resolved = True
                                break
                        if resolved:
                            break
                    if not resolved:
                        raise ValueError(
                            f"Field definition '{field_def}' "
                            + (f"with physics '{physics_def}' " if physics_def else "")
                            + "not found in project physics"
                        )
                elif "fieldId" in fi:
                    field_ref = fi["fieldId"]

                field_inits.append(
                    FieldInitialization(
                        type=FieldInitializationType(fi["type"]),
                        source_simulation=source_sim_ref,
                        source_output_name=fi["sourceValueOutputName"],
                        field=field_ref,
                        source_output_specifier=fi.get("sourceValueOutputSpecifier"),
                        source_sweep_step=fi.get("sourceValueSweepStep"),
                        source_step=fi.get("sourceValueStep"),
                        harmonic=fi.get("harmonic"),
                    )
                )
            sim.set_field_initializations(field_inits)

        if "disabledScriptSections" in simulation_data:
            sim.disabled_script_sections = [
                DisableableSection(DisabledScriptSection(s))
                for s in simulation_data["disabledScriptSections"]
            ]

        # Save changes before starting
        sim.save()

        # Create output interactions (optional)
        outputs = simulation_data.get("outputs", [])
        if outputs is None:
            outputs = []
        if outputs:
            if sim.id is None:
                raise ValueError("Simulation must have an id before importing outputs")
            import_outputs_for_simulation(
                project=project,
                simulation=sim,
                outputs=outputs,
                regions=regions,
                verbose=verbose,
            )

        imported_simulations[simulation_data["name"]] = sim

    return imported_simulations


def run_imported_simulations(
    simulations: list[dict],
    imported_simulations: dict[str, Simulation],
    verbose: bool = False,
) -> None:

    for simulation_data in simulations:
        if simulation_data.get("createOnly", False):
            continue

        sim = imported_simulations[simulation_data["name"]]
        if verbose:
            print(f"Starting simulation {simulation_data['name']}...")
        sim.start()

        while sim.is_running(refresh_delay_s=1):
            if verbose:
                sim.print_new_loglines()

        if verbose:
            sim.print_new_loglines()

        if sim.get_status() != Job.SUCCESS:
            raise ValueError(
                f"Simulation {simulation_data['name']} failed: {sim.get_status()}"
            )
