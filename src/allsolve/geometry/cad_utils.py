# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

"""
Utility functions for converting between Python types and CAD geometry API types.

This module provides conversion functions for creating and extracting values
from raw API CAD geometry objects.
"""

from allsolve.geometry.cad_path import CadGlob, CadPath
import allsolve_rawapi as rawapi


def to_str_list(value: str | list[str] | None) -> list[str] | None:
    """Python runtime allows for a single string to be passed as a list of strings.
    This function converts a single string to a list of strings.
    """
    if value is None:
        return None
    return [value] if isinstance(value, str) else value


def extract_entities_from_elements(
    elements: list[rawapi.CadEntity],
) -> tuple[list[int], list[str], list[CadPath]]:
    """Extract entity_tags, cad_names from rawapi CadEntity elements."""
    entity_tags: list[int] = []
    cad_names: list[str] = []
    cad_paths: list[CadPath] = []
    for entity in elements:
        if entity.tag is not None:
            entity_tags.append(entity.tag)
        if entity.name is not None:
            cad_names.append(entity.name)
        if entity.path is not None:
            cad_path: CadPath = []
            for segment in entity.path:
                if isinstance(segment, rawapi.CadPathSegment):
                    if (
                        segment.attribute is not None
                        and segment.attribute.key is not None
                        and segment.attribute.value is not None
                    ):
                        cad_path.append(
                            (segment.attribute.key, segment.attribute.value)
                        )
                    elif segment.glob is not None:
                        cad_path.append(CadGlob(segment.glob.value))
                    elif segment.name is not None:
                        cad_path.append(segment.name)
            if len(cad_path) > 0:
                cad_paths.append(cad_path)
    return entity_tags, cad_names, cad_paths


def validate_cad_path(cad_path: CadPath) -> None:
    """Validate a CAD path."""
    if len(cad_path) == 0:
        raise ValueError("CAD path is empty")

    # Check usage of CadGlob.DOUBLESTAR next to other CadGlob
    for i in range(len(cad_path) - 1):
        if isinstance(cad_path[i], CadGlob) and isinstance(cad_path[i + 1], CadGlob):
            if (
                cad_path[i] == CadGlob.DOUBLESTAR
                or cad_path[i + 1] == CadGlob.DOUBLESTAR
            ):
                raise ValueError(f"Found {cad_path[i]} / {cad_path[i + 1]} in CAD path")


def validate_entity_set(
    entity_tags: list[int] | None,
    cad_names: list[str] | None,
    cad_paths: list[CadPath] | None,
    set_name: str,
    operation_name: str,
) -> None:
    """Validate that at least one entity set is provided and non-empty."""
    if entity_tags is None and cad_names is None and cad_paths is None:
        if set_name:
            raise ValueError(
                f"At least one of entity tags, CAD names, or CAD paths must be set for the {set_name}"
            )
        else:
            raise ValueError(
                "At least one of entity tags, CAD names, or CAD paths must be set"
            )
    count = 0
    if entity_tags is not None:
        count += len(entity_tags)
    if cad_names is not None:
        count += len(cad_names)
    if cad_paths is not None:
        for cad_path in cad_paths:
            validate_cad_path(cad_path)
        count += len(cad_paths)
    if count < 1:
        if set_name:
            raise ValueError(f"{operation_name} has no entities in the {set_name}")
        else:
            raise ValueError(f"{operation_name} has no entities")


def create_cad_entities_from_lists(
    entity_tags: list[int] | None,
    cad_names: list[str] | None,
    cad_paths: list[CadPath] | None,
) -> list[rawapi.CadEntity]:
    """Create CadEntity list from entity_tags, cad_names, cad_paths."""
    elements: list[rawapi.CadEntity] = []
    if entity_tags is not None:
        for tag in entity_tags:
            elements.append(rawapi.CadEntity(tag=tag))
    if cad_names is not None:
        for name in cad_names:
            elements.append(rawapi.CadEntity(name=name))
    if cad_paths is not None:
        for path in cad_paths:
            path_segments = []
            for segment in path:
                if isinstance(segment, str):
                    path_segments.append(rawapi.CadPathSegment(name=segment))
                if isinstance(segment, tuple):
                    path_segments.append(
                        rawapi.CadPathSegment(
                            attribute=rawapi.CadAttribute(
                                key=segment[0], value=segment[1]
                            )
                        )
                    )
                elif isinstance(segment, CadGlob):
                    if segment == CadGlob.STAR:
                        path_segments.append(
                            rawapi.CadPathSegment(glob=rawapi.CadGlobEnum.STAR)
                        )
                    elif segment == CadGlob.DOUBLESTAR:
                        path_segments.append(
                            rawapi.CadPathSegment(glob=rawapi.CadGlobEnum.DOUBLESTAR)
                        )
                    else:
                        raise ValueError(f"Invalid CadGlob: {segment}")
            elements.append(rawapi.CadEntity(path=path_segments))
    return elements


def create_boolean(value: bool | str | None) -> rawapi.CadBoolean | None:
    """Create a CadBoolean from a boolean or string expression."""
    if value is None:
        return None
    if isinstance(value, str):
        return rawapi.CadBoolean(expression=value)
    elif isinstance(value, bool):
        return rawapi.CadBoolean(expression="1" if value else "0")


def create_scalar(value: float | str) -> rawapi.CadScalar:
    """Create a CadScalar from a numeric value or expression string."""
    if isinstance(value, str):
        return rawapi.CadScalar(expression=value)
    else:
        return rawapi.CadScalar(expression=str(value))


def create_angular_unit(unit: str | None) -> rawapi.CadAngularUnit | None:
    """
    Create a CadAngularUnit from a string.
    Allowed values are: degree, radian.
    """
    if unit is None:
        return None
    if unit not in [unit.value for unit in rawapi.CadAngularUnit.__members__.values()]:
        raise ValueError(f"Invalid angular unit: {unit}")
    return rawapi.CadAngularUnit(unit)


def create_distance_unit(unit: str | None) -> rawapi.CadDistanceUnit | None:
    """
    Create a CadDistanceUnit from a string.
    Allowed values are: m, meter, mm, millimeter, um, micrometer, nm, nanometer, yard, foot, inch.
    """
    if unit is None:
        return None

    if unit == "m":
        unit = "meter"
    elif unit == "mm":
        unit = "millimeter"
    elif unit == "um":
        unit = "micrometer"
    elif unit == "nm":
        unit = "nanometer"

    if unit not in [unit.value for unit in rawapi.CadDistanceUnit.__members__.values()]:
        raise ValueError(f"Invalid distance unit: {unit}")
    return rawapi.CadDistanceUnit(unit)


def create_distance(
    value: float | str | tuple[float | str, str],
    default_unit: str | None = None,
) -> rawapi.CadDistance:
    """Create a CadDistance from a value with optional unit."""
    if isinstance(value, tuple):
        val, unit = value
        return rawapi.CadDistance(
            value=create_scalar(val),
            unit=create_distance_unit(unit),
        )
    elif isinstance(value, str):
        return rawapi.CadDistance(
            value=create_scalar(value),
            unit=create_distance_unit(default_unit),
        )
    else:
        return rawapi.CadDistance(
            value=create_scalar(value),
            unit=create_distance_unit(default_unit),
        )


def create_angle(
    value: float | str,
    default_unit: str | None = "degree",
) -> rawapi.CadAngle:
    """Create a CadAngle from a value with optional unit."""
    if isinstance(value, str):
        return rawapi.CadAngle(
            value=create_scalar(value),
            unit=create_angular_unit(default_unit),
        )
    else:
        return rawapi.CadAngle(
            value=create_scalar(value),
            unit=create_angular_unit(default_unit),
        )


def create_vector(
    coords: tuple[float | str, float | str, float | str],
) -> rawapi.CadVector:
    """Create a CadVector from a tuple of coordinates."""
    x, y, z = coords
    return rawapi.CadVector(
        x=create_distance(x),
        y=create_distance(y),
        z=create_distance(z),
    )


def create_vector_2d(
    coords: tuple[float | str, float | str],
) -> rawapi.CadVector:
    """Create a CadVector from a 2D tuple of coordinates (z will be 0)."""
    x, y = coords
    return rawapi.CadVector(
        x=create_distance(x),
        y=create_distance(y),
        z=create_distance(0),
    )


def create_euler_angles(
    angles: tuple[float | str, float | str, float | str],
) -> rawapi.CadEulerAngles:
    """Create CadEulerAngles from a tuple of angles in degrees."""
    x, y, z = angles
    return rawapi.CadEulerAngles(
        x=create_angle(x),
        y=create_angle(y),
        z=create_angle(z),
    )


def from_boolean(boolean: rawapi.CadBoolean | None) -> bool | str | None:
    """Convert a CadBoolean to a boolean or string expression."""
    if boolean is None:
        return None
    if boolean.expression is not None:
        if boolean.expression == "1":
            return True
        elif boolean.expression == "0":
            return False
        return boolean.expression
    elif boolean.value is not None:
        return boolean.value
    else:
        return None


def from_scalar(scalar: rawapi.CadScalar) -> float | str:
    """
    Convert a CadScalar to a float or string.

    Returns:
        The numeric value if set, or the expression string if set.

    Raises:
        ValueError: If neither value nor expression is set.
    """
    if scalar.expression is not None:
        try:
            return float(scalar.expression)
        except ValueError:
            return scalar.expression
    elif scalar.value is not None:
        return float(scalar.value)
    else:
        raise ValueError("CadScalar must have either value or expression set")


def from_distance(
    distance: rawapi.CadDistance,
) -> float | str:
    """
    Convert a CadDistance to a value or expression.

    Note: Unit information is not preserved in the conversion.

    Returns:
        The numeric value if set, or the expression string if set.

    Raises:
        ValueError: If the distance value is not set.
    """
    if distance.value is None:
        raise ValueError("CadDistance.value must be set")

    return from_scalar(distance.value)


def from_angle(angle: rawapi.CadAngle) -> float | str:
    """
    Convert a CadAngle to a float or string.

    Returns:
        The numeric value if set, or the expression string if set.

    Raises:
        ValueError: If the angle value is not set.
    """
    if angle.value is None:
        raise ValueError("CadAngle.value must be set")

    return from_scalar(angle.value)


def from_vector(
    vector: rawapi.CadVector,
) -> tuple[float | str, float | str, float | str]:
    """
    Convert a CadVector to a tuple of coordinates.

    Returns:
        Tuple of (x, y, z) where each is float or str.

    Raises:
        ValueError: If any component is not set.
    """
    if vector.x is None:
        raise ValueError("CadVector.x must be set")
    if vector.y is None:
        raise ValueError("CadVector.y must be set")
    if vector.z is None:
        raise ValueError("CadVector.z must be set")

    x = from_distance(vector.x)
    y = from_distance(vector.y)
    z = from_distance(vector.z)

    return (x, y, z)


def from_vector_2d(
    vector: rawapi.CadVector,
) -> tuple[float | str, float | str]:
    """
    Convert a CadVector to a tuple of 2D coordinates.
    """
    if vector.x is None:
        raise ValueError("CadVector.x must be set")
    if vector.y is None:
        raise ValueError("CadVector.y must be set")

    x = from_distance(vector.x)
    y = from_distance(vector.y)

    return (x, y)


def from_euler_angles(
    angles: rawapi.CadEulerAngles | None,
) -> tuple[float | str, float | str, float | str] | None:
    """
    Convert CadEulerAngles to a tuple of angles.

    Returns:
        Tuple of (x, y, z) angles, or None if input is None.

    Raises:
        ValueError: If angles is not None but any component is not set.
    """
    if angles is None:
        return None

    if angles.x is None:
        raise ValueError("CadEulerAngles.x must be set")
    if angles.y is None:
        raise ValueError("CadEulerAngles.y must be set")
    if angles.z is None:
        raise ValueError("CadEulerAngles.z must be set")

    x = from_angle(angles.x)
    y = from_angle(angles.y)
    z = from_angle(angles.z)

    return (x, y, z)
