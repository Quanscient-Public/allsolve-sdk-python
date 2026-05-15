# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from allsolve.geometry.cad_path import CadPath
from allsolve.geometry.cad_geometry_element import CadGeometryElement
from allsolve.geometry.cad_geometry_type import CadGeometryType
from allsolve.geometry.cad_utils import (
    create_cad_entities_from_lists,
    create_vector,
    extract_entities_from_elements,
    from_vector,
    create_angle,
    from_angle,
    to_str_list,
    validate_entity_set,
)
from allsolve.util import prevent_deleted
import allsolve_rawapi as rawapi
from typing_extensions import Self


class CadTranslate(CadGeometryElement):
    """
    CadTranslate represents a translate of a CAD geometry element.
    """

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:

        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.transform_operation is None:
            raise ValueError("Transform operation is not set")
        if cad_element.transform_operation.translate is None:
            raise ValueError("Translate is not set")
        if cad_element.name is None:
            raise ValueError("Translate name must be set")
        if cad_element.transform_operation.translate.translation is None:
            raise ValueError("Transform operation object is not set")
        if cad_element.transform_operation.target is None:
            raise ValueError("Transform operation object elements is not set")
        entity_tags, cad_names, cad_paths = extract_entities_from_elements(
            cad_element.transform_operation.target
        )
        translation = from_vector(cad_element.transform_operation.translate.translation)
        copy_object = (
            cad_element.transform_operation.translate.copy_object
            if cad_element.transform_operation.translate.copy_object is not None
            else False
        )
        repeat: int | str | None = None
        if cad_element.transform_operation.translate.repeat is not None:
            if cad_element.transform_operation.translate.repeat.value is not None:
                repeat = cad_element.transform_operation.translate.repeat.value
            elif (
                cad_element.transform_operation.translate.repeat.expression is not None
            ):
                repeat = cad_element.transform_operation.translate.repeat.expression
        cad_object = cls(
            name=cad_element.name,
            translation=translation,
            entity_tags=entity_tags if entity_tags else None,
            cad_names=cad_names if cad_names else None,
            cad_paths=cad_paths if cad_paths else None,
            copy_object=copy_object,
            repeat=repeat,
        )
        cls._initialize_from_rawapi(cad_object, rawapi_element, cad_element, project_id)
        return cad_object

    def __init__(
        self,
        name: str,
        translation: tuple[float | str, float | str, float | str],
        entity_tags: list[int] | None = None,
        cad_names: list[str] | None = None,
        cad_paths: list[CadPath] | None = None,
        copy_object: bool = False,
        repeat: int | str | None = None,
        enabled: str | bool | None = None,
    ) -> None:
        """
        Create a new translate of a CAD geometry element.
        At least one of entity tags, CAD names, or CAD paths must be set.

        Parameters:
            name: Name for the geometry element.
            entity_tags: The list of entity tags to translate.
            cad_names: The list of CAD names to translate.
            cad_paths: The list of CAD paths to translate.
            translation: The translation vector.
            copy_object: Copy the object instead of translating. Default is False.
            repeat: Number of times to repeat the translation. Default is None.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.
        """
        super().__init__(name, enabled)
        self._translation = translation
        self._entity_tags = entity_tags
        self._cad_names = to_str_list(cad_names)
        self._cad_paths = cad_paths
        self._copy_object = copy_object
        self._repeat = repeat

        validate_entity_set(entity_tags, cad_names, cad_paths, "target", "Translate")

    def _require_transform_op(self) -> rawapi.CadTransformOperation:
        cad_elem = self._require_cad_elem()
        if cad_elem.transform_operation is None:
            raise ValueError("Transform operation is not set")
        return cad_elem.transform_operation

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.TRANSLATE

    @property
    @prevent_deleted
    def entity_tags(self) -> list[int] | None:
        """Get the entity tags of the translate."""
        return self._entity_tags

    @entity_tags.setter
    @prevent_deleted
    def entity_tags(self, entity_tags: list[int] | None) -> None:
        """Set the entity tags of the translate."""
        validate_entity_set(
            entity_tags, self._cad_names, self._cad_paths, "target", "Translate"
        )
        self._entity_tags = entity_tags
        self._update_rawapi_transform_operation()

    @property
    @prevent_deleted
    def cad_names(self) -> list[str] | None:
        """Get the CAD names of the union."""
        return self._cad_names

    @cad_names.setter
    @prevent_deleted
    def cad_names(self, cad_names: list[str] | None) -> None:
        """Set the CAD names of the translate."""
        validate_entity_set(
            self._entity_tags, cad_names, self._cad_paths, "target", "Translate"
        )
        self._cad_names = cad_names
        self._update_rawapi_transform_operation()

    @property
    @prevent_deleted
    def cad_paths(self) -> list[CadPath] | None:
        """Get the CAD paths of the translate."""
        return self._cad_paths

    @cad_paths.setter
    @prevent_deleted
    def cad_paths(self, cad_paths: list[CadPath] | None) -> None:
        """Set the CAD paths of the translate."""
        validate_entity_set(
            self._entity_tags, self._cad_names, cad_paths, "target", "Translate"
        )
        self._cad_paths = cad_paths
        self._update_rawapi_transform_operation()

    @property
    @prevent_deleted
    def translation(self) -> tuple[float | str, float | str, float | str] | None:
        """Get the translation vector."""
        return self._translation

    @translation.setter
    @prevent_deleted
    def translation(
        self, translation: tuple[float | str, float | str, float | str]
    ) -> None:
        """Set the translation vector."""
        self._translation = translation
        self._update_rawapi_transform_operation()

    @property
    @prevent_deleted
    def copy_object(self) -> bool:
        """Get the copy_object flag."""
        return self._copy_object

    @copy_object.setter
    @prevent_deleted
    def copy_object(self, copy_object: bool) -> None:
        """Set the copy_object flag."""
        self._copy_object = copy_object
        self._update_rawapi_transform_operation()

    @property
    @prevent_deleted
    def repeat(self) -> int | str | None:
        """Get the repeat count."""
        return self._repeat

    @repeat.setter
    @prevent_deleted
    def repeat(self, repeat: int | str | None) -> None:
        """Set the repeat count."""
        self._repeat = repeat
        self._update_rawapi_transform_operation()

    def _update_rawapi_transform_operation(self) -> None:
        """Update the rawapi transform operation structure."""
        transform_op = self._require_transform_op()
        if transform_op.translate is None:
            raise ValueError("Translate is not set")

        elements = create_cad_entities_from_lists(
            self._entity_tags, self._cad_names, self._cad_paths
        )
        transform_op.target = elements

        repeat_obj = None
        if self._repeat is not None:
            repeat_obj = rawapi.CadPositiveInteger(expression=str(self._repeat))

        transform_op.translate.translation = create_vector(self._translation)
        transform_op.translate.copy_object = (
            self._copy_object if self._copy_object else None
        )
        transform_op.translate.repeat = repeat_obj

    @prevent_deleted
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:

        elements = create_cad_entities_from_lists(
            self._entity_tags, self._cad_names, self._cad_paths
        )

        repeat_obj = None
        if self._repeat is not None:
            repeat_obj = rawapi.CadPositiveInteger(expression=str(self._repeat))

        translation_obj = rawapi.CadTranslateParameters(
            translation=create_vector(self._translation),
            copyObject=self._copy_object if self._copy_object else None,
            repeat=repeat_obj,
        )
        transform_operation = rawapi.CadTransformOperation(
            translate=translation_obj,
            target=elements,
        )
        cad_element = rawapi.CadGeometryElement(
            name=self._name,
            transformOperation=transform_operation,
        )
        return cad_element

    def __str__(self) -> str:
        return (
            f"Translate(translation={self._translation}, "
            f"entity_tags={self._entity_tags}, "
            f"cad_names={self._cad_names}, cad_paths={self._cad_paths}, "
            f"copy_object={self._copy_object}, repeat={self._repeat}, "
            f"name={self._name})"
        )


class CadRotate(CadGeometryElement):
    """
    CadRotate represents a rotation of a CAD geometry element.
    """

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:

        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.transform_operation is None:
            raise ValueError("Transform operation is not set")
        if cad_element.transform_operation.rotate is None:
            raise ValueError("Rotate is not set")
        if cad_element.name is None:
            raise ValueError("Rotate name must be set")
        if cad_element.transform_operation.rotate.axis is None:
            raise ValueError("Rotate axis is not set")
        if cad_element.transform_operation.rotate.center is None:
            raise ValueError("Rotate center is not set")
        if cad_element.transform_operation.rotate.angle is None:
            raise ValueError("Rotate angle is not set")
        if cad_element.transform_operation.target is None:
            raise ValueError("Transform operation target is not set")
        entity_tags, cad_names, cad_paths = extract_entities_from_elements(
            cad_element.transform_operation.target
        )
        axis = from_vector(cad_element.transform_operation.rotate.axis)
        center = from_vector(cad_element.transform_operation.rotate.center)
        angle = from_angle(cad_element.transform_operation.rotate.angle)
        copy_object = (
            cad_element.transform_operation.rotate.copy_object
            if cad_element.transform_operation.rotate.copy_object is not None
            else False
        )
        repeat: int | str | None = None
        if cad_element.transform_operation.rotate.repeat is not None:
            if cad_element.transform_operation.rotate.repeat.value is not None:
                repeat = cad_element.transform_operation.rotate.repeat.value
            elif cad_element.transform_operation.rotate.repeat.expression is not None:
                repeat = cad_element.transform_operation.rotate.repeat.expression
        cad_object = cls(
            name=cad_element.name,
            axis=axis,
            center=center,
            angle=angle,
            entity_tags=entity_tags if entity_tags else None,
            cad_names=cad_names if cad_names else None,
            cad_paths=cad_paths if cad_paths else None,
            copy_object=copy_object,
            repeat=repeat,
        )
        cls._initialize_from_rawapi(cad_object, rawapi_element, cad_element, project_id)
        return cad_object

    def __init__(
        self,
        name: str,
        axis: tuple[float | str, float | str, float | str],
        center: tuple[float | str, float | str, float | str],
        angle: float | str,
        entity_tags: list[int] | None = None,
        cad_names: list[str] | None = None,
        cad_paths: list[CadPath] | None = None,
        copy_object: bool = False,
        repeat: int | str | None = None,
        enabled: str | bool | None = None,
    ) -> None:
        """
        Create a new rotation of a CAD geometry element.
        At least one of entity tags, CAD names, or CAD paths must be set.

        Parameters:
            name: Name for the geometry element.
            axis: The rotation axis vector.
            center: The center point for rotation.
            angle: The rotation angle.
            entity_tags: The list of entity tags to rotate.
            cad_names: The list of CAD names to rotate.
            cad_paths: The list of CAD paths to rotate.
            copy_object: Copy the object instead of rotating. Default is False.
            repeat: Number of times to repeat the rotation. Default is None.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.
        """
        super().__init__(name, enabled)
        self._axis = axis
        self._center = center
        self._angle = angle
        self._entity_tags = entity_tags
        self._cad_names = to_str_list(cad_names)
        self._cad_paths = cad_paths
        self._copy_object = copy_object
        self._repeat = repeat

        validate_entity_set(entity_tags, cad_names, cad_paths, "target", "Rotate")

    def _require_transform_op(self) -> rawapi.CadTransformOperation:
        cad_elem = self._require_cad_elem()
        if cad_elem.transform_operation is None:
            raise ValueError("Transform operation is not set")
        return cad_elem.transform_operation

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.ROTATE

    @property
    @prevent_deleted
    def entity_tags(self) -> list[int] | None:
        """Get the entity tags of the rotate."""
        return self._entity_tags

    @entity_tags.setter
    @prevent_deleted
    def entity_tags(self, entity_tags: list[int] | None) -> None:
        """Set the entity tags of the rotate."""
        validate_entity_set(
            entity_tags, self._cad_names, self._cad_paths, "target", "Rotate"
        )
        self._entity_tags = entity_tags
        self._update_rawapi_transform_operation()

    @property
    @prevent_deleted
    def cad_names(self) -> list[str] | None:
        """Get the CAD names of the rotate."""
        return self._cad_names

    @cad_names.setter
    @prevent_deleted
    def cad_names(self, cad_names: list[str] | None) -> None:
        """Set the CAD names of the rotate."""
        validate_entity_set(
            self._entity_tags, cad_names, self._cad_paths, "target", "Rotate"
        )
        self._cad_names = cad_names
        self._update_rawapi_transform_operation()

    @property
    @prevent_deleted
    def cad_paths(self) -> list[CadPath] | None:
        """Get the CAD paths of the rotate."""
        return self._cad_paths

    @cad_paths.setter
    @prevent_deleted
    def cad_paths(self, cad_paths: list[CadPath] | None) -> None:
        """Set the CAD paths of the rotate."""
        validate_entity_set(
            self._entity_tags, self._cad_names, cad_paths, "target", "Rotate"
        )
        self._cad_paths = cad_paths
        self._update_rawapi_transform_operation()

    @property
    @prevent_deleted
    def axis(self) -> tuple[float | str, float | str, float | str]:
        """Get the rotation axis vector."""
        return self._axis

    @axis.setter
    @prevent_deleted
    def axis(self, axis: tuple[float | str, float | str, float | str]) -> None:
        """Set the rotation axis vector."""
        self._axis = axis
        self._update_rawapi_transform_operation()

    @property
    @prevent_deleted
    def center(self) -> tuple[float | str, float | str, float | str]:
        """Get the center point for rotation."""
        return self._center

    @center.setter
    @prevent_deleted
    def center(self, center: tuple[float | str, float | str, float | str]) -> None:
        """Set the center point for rotation."""
        self._center = center
        self._update_rawapi_transform_operation()

    @property
    @prevent_deleted
    def angle(self) -> float | str:
        """Get the rotation angle."""
        return self._angle

    @angle.setter
    @prevent_deleted
    def angle(self, angle: float | str) -> None:
        """Set the rotation angle."""
        self._angle = angle
        self._update_rawapi_transform_operation()

    @property
    @prevent_deleted
    def copy_object(self) -> bool:
        """Get the copy_object flag."""
        return self._copy_object

    @copy_object.setter
    @prevent_deleted
    def copy_object(self, copy_object: bool) -> None:
        """Set the copy_object flag."""
        self._copy_object = copy_object
        self._update_rawapi_transform_operation()

    @property
    @prevent_deleted
    def repeat(self) -> int | str | None:
        """Get the repeat count."""
        return self._repeat

    @repeat.setter
    @prevent_deleted
    def repeat(self, repeat: int | str | None) -> None:
        """Set the repeat count."""
        self._repeat = repeat
        self._update_rawapi_transform_operation()

    def _update_rawapi_transform_operation(self) -> None:
        """Update the rawapi transform operation structure."""
        transform_op = self._require_transform_op()
        if transform_op.rotate is None:
            raise ValueError("Rotate is not set")

        elements = create_cad_entities_from_lists(
            self._entity_tags, self._cad_names, self._cad_paths
        )
        transform_op.target = elements

        repeat_obj = None
        if self._repeat is not None:
            repeat_obj = rawapi.CadPositiveInteger(expression=str(self._repeat))

        transform_op.rotate.axis = create_vector(self._axis)
        transform_op.rotate.center = create_vector(self._center)
        transform_op.rotate.angle = create_angle(self._angle)
        transform_op.rotate.copy_object = (
            self._copy_object if self._copy_object else None
        )
        transform_op.rotate.repeat = repeat_obj

    @prevent_deleted
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:

        elements = create_cad_entities_from_lists(
            self._entity_tags, self._cad_names, self._cad_paths
        )

        repeat_obj = None
        if self._repeat is not None:
            repeat_obj = rawapi.CadPositiveInteger(expression=str(self._repeat))

        rotate_obj = rawapi.CadRotateParameters(
            axis=create_vector(self._axis),
            center=create_vector(self._center),
            angle=create_angle(self._angle),
            copyObject=self._copy_object if self._copy_object else None,
            repeat=repeat_obj,
        )
        transform_operation = rawapi.CadTransformOperation(
            rotate=rotate_obj,
            target=elements,
        )
        cad_element = rawapi.CadGeometryElement(
            name=self._name,
            transformOperation=transform_operation,
        )
        return cad_element

    def __str__(self) -> str:
        return (
            f"Rotate(axis={self._axis}, center={self._center}, "
            f"angle={self._angle}, entity_tags={self._entity_tags}, "
            f"cad_names={self._cad_names}, cad_paths={self._cad_paths}, "
            f"copy_object={self._copy_object}, repeat={self._repeat}, "
            f"name={self._name})"
        )


class CadGrid(CadGeometryElement):
    """
    CadGrid represents a grid pattern of CAD geometry elements.
    """

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:

        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.transform_operation is None:
            raise ValueError("Transform operation is not set")
        if cad_element.transform_operation.grid is None:
            raise ValueError("Grid is not set")
        if cad_element.name is None:
            raise ValueError("Grid name must be set")
        if cad_element.transform_operation.grid.translation is None:
            raise ValueError("Grid translation is not set")
        if cad_element.transform_operation.grid.size_x is None:
            raise ValueError("Grid size_x is not set")
        if cad_element.transform_operation.grid.size_y is None:
            raise ValueError("Grid size_y is not set")
        if cad_element.transform_operation.grid.size_z is None:
            raise ValueError("Grid size_z is not set")
        if cad_element.transform_operation.target is None:
            raise ValueError("Transform operation target is not set")
        entity_tags, cad_names, cad_paths = extract_entities_from_elements(
            cad_element.transform_operation.target
        )
        translation = from_vector(cad_element.transform_operation.grid.translation)

        size_x: int | str | None = None
        if cad_element.transform_operation.grid.size_x.expression is not None:
            size_x = cad_element.transform_operation.grid.size_x.expression

        size_y: int | str | None = None
        if cad_element.transform_operation.grid.size_y.expression is not None:
            size_y = cad_element.transform_operation.grid.size_y.expression

        size_z: int | str | None = None
        if cad_element.transform_operation.grid.size_z.expression is not None:
            size_z = cad_element.transform_operation.grid.size_z.expression

        if size_x is None or size_y is None or size_z is None:
            raise ValueError("Grid size components must be set")

        size = (size_x, size_y, size_z)

        cad_object = cls(
            name=cad_element.name,
            translation=translation,
            size=size,
            entity_tags=entity_tags if entity_tags else None,
            cad_names=cad_names if cad_names else None,
            cad_paths=cad_paths if cad_paths else None,
        )
        cls._initialize_from_rawapi(cad_object, rawapi_element, cad_element, project_id)
        return cad_object

    def __init__(
        self,
        name: str,
        translation: tuple[float | str, float | str, float | str],
        size: tuple[int | str, int | str, int | str],
        entity_tags: list[int] | None = None,
        cad_names: list[str] | None = None,
        cad_paths: list[CadPath] | None = None,
        enabled: str | bool | None = None,
    ) -> None:
        """
        Create a new grid pattern of CAD geometry elements.
        At least one of entity tags, CAD names, or CAD paths must be set.

        Parameters:
            name: Name for the geometry element.
            translation: The translation vector for grid spacing.
            size: The grid size as a tuple of 3 positive integers (x, y, z).
            entity_tags: The list of entity tags to create grid from.
            cad_names: The list of CAD names to create grid from.
            cad_paths: The list of CAD paths to create grid from.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.
        """
        super().__init__(name, enabled)
        self._translation = translation
        self._size = size
        self._entity_tags = entity_tags
        self._cad_names = to_str_list(cad_names)
        self._cad_paths = cad_paths
        validate_entity_set(entity_tags, cad_names, cad_paths, "target", "Grid")

    def _require_transform_op(self) -> rawapi.CadTransformOperation:
        cad_elem = self._require_cad_elem()
        if cad_elem.transform_operation is None:
            raise ValueError("Transform operation is not set")
        return cad_elem.transform_operation

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.GRID

    @property
    @prevent_deleted
    def entity_tags(self) -> list[int] | None:
        """Get the entity tags of the grid."""
        return self._entity_tags

    @entity_tags.setter
    @prevent_deleted
    def entity_tags(self, entity_tags: list[int] | None) -> None:
        """Set the entity tags of the grid."""
        validate_entity_set(
            entity_tags, self._cad_names, self._cad_paths, "target", "Grid"
        )
        self._entity_tags = entity_tags
        self._update_rawapi_transform_operation()

    @property
    @prevent_deleted
    def cad_names(self) -> list[str] | None:
        """Get the CAD names of the grid."""
        return self._cad_names

    @cad_names.setter
    @prevent_deleted
    def cad_names(self, cad_names: list[str] | None) -> None:
        """Set the CAD names of the grid."""
        validate_entity_set(
            self._entity_tags, cad_names, self._cad_paths, "target", "Grid"
        )
        self._cad_names = cad_names
        self._update_rawapi_transform_operation()

    @property
    @prevent_deleted
    def cad_paths(self) -> list[CadPath] | None:
        """Get the CAD paths of the grid."""
        return self._cad_paths

    @cad_paths.setter
    @prevent_deleted
    def cad_paths(self, cad_paths: list[CadPath] | None) -> None:
        """Set the CAD paths of the grid."""
        validate_entity_set(
            self._entity_tags, self._cad_names, cad_paths, "target", "Grid"
        )
        self._cad_paths = cad_paths
        self._update_rawapi_transform_operation()

    @property
    @prevent_deleted
    def translation(self) -> tuple[float | str, float | str, float | str]:
        """Get the translation vector for grid spacing."""
        return self._translation

    @translation.setter
    @prevent_deleted
    def translation(
        self, translation: tuple[float | str, float | str, float | str]
    ) -> None:
        """Set the translation vector for grid spacing."""
        self._translation = translation
        self._update_rawapi_transform_operation()

    @property
    @prevent_deleted
    def size(self) -> tuple[int | str, int | str, int | str]:
        """Get the grid size as a tuple of 3 positive integers (x, y, z)."""
        return self._size

    @size.setter
    @prevent_deleted
    def size(self, size: tuple[int | str, int | str, int | str]) -> None:
        """Set the grid size as a tuple of 3 positive integers (x, y, z)."""
        self._size = size
        self._update_rawapi_transform_operation()

    def _update_rawapi_transform_operation(self) -> None:
        """Update the rawapi transform operation structure."""
        transform_op = self._require_transform_op()
        if transform_op.grid is None:
            raise ValueError("Grid is not set")

        elements = create_cad_entities_from_lists(
            self._entity_tags,
            self._cad_names,
            self._cad_paths,
        )
        transform_op.target = elements

        size_x, size_y, size_z = self._size
        size_x_obj = rawapi.CadPositiveInteger(expression=str(size_x))
        size_y_obj = rawapi.CadPositiveInteger(expression=str(size_y))
        size_z_obj = rawapi.CadPositiveInteger(expression=str(size_z))

        transform_op.grid.translation = create_vector(self._translation)
        transform_op.grid.size_x = size_x_obj
        transform_op.grid.size_y = size_y_obj
        transform_op.grid.size_z = size_z_obj

    @prevent_deleted
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:

        elements = create_cad_entities_from_lists(
            self._entity_tags, self._cad_names, self._cad_paths
        )

        size_x, size_y, size_z = self._size

        size_x_obj = rawapi.CadPositiveInteger(expression=str(size_x))
        size_y_obj = rawapi.CadPositiveInteger(expression=str(size_y))
        size_z_obj = rawapi.CadPositiveInteger(expression=str(size_z))

        grid_obj = rawapi.CadGridParameters(
            translation=create_vector(self._translation),
            sizeX=size_x_obj,
            sizeY=size_y_obj,
            sizeZ=size_z_obj,
        )
        transform_operation = rawapi.CadTransformOperation(
            grid=grid_obj,
            target=elements,
        )
        cad_element = rawapi.CadGeometryElement(
            name=self._name,
            transformOperation=transform_operation,
        )
        return cad_element

    def __str__(self) -> str:
        return (
            f"Grid(translation={self._translation}, size={self._size}, "
            f"entity_tags={self._entity_tags}, "
            f"cad_names={self._cad_names}, cad_paths={self._cad_paths}, "
            f"name={self._name})"
        )


class CadRemove(CadGeometryElement):
    """
    CadRemove represents a removal of CAD geometry elements.
    """

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:

        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.remove_entity_operation is None:
            raise ValueError("Remove entity operation is not set")
        if cad_element.name is None:
            raise ValueError("Remove name must be set")
        if cad_element.remove_entity_operation.target is None:
            raise ValueError("Remove entity operation target is not set")
        entity_tags, cad_names, cad_paths = extract_entities_from_elements(
            cad_element.remove_entity_operation.target
        )

        cad_object = cls(
            name=cad_element.name,
            entity_tags=entity_tags if entity_tags else None,
            cad_names=cad_names if cad_names else None,
            cad_paths=cad_paths if cad_paths else None,
        )
        cls._initialize_from_rawapi(cad_object, rawapi_element, cad_element, project_id)
        return cad_object

    def __init__(
        self,
        name: str,
        entity_tags: list[int] | None = None,
        cad_names: list[str] | None = None,
        cad_paths: list[CadPath] | None = None,
        enabled: str | bool | None = None,
    ) -> None:
        """
        Create a new removal of CAD geometry elements.
        At least one of entity tags, CAD names, or CAD paths must be set.

        Parameters:
            name: Name for the geometry element.
            entity_tags: The list of entity tags to remove.
            cad_names: The list of CAD names to remove.
            cad_paths: The list of CAD paths to remove.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.
        """
        super().__init__(name, enabled)
        self._entity_tags = entity_tags
        self._cad_names = to_str_list(cad_names)
        self._cad_paths = cad_paths
        validate_entity_set(entity_tags, cad_names, cad_paths, "target", "Remove")

    def _require_remove_op(self) -> rawapi.CadRemoveEntityOperation:
        cad_elem = self._require_cad_elem()
        if cad_elem.remove_entity_operation is None:
            raise ValueError("Remove entity operation is not set")
        return cad_elem.remove_entity_operation

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.REMOVE

    @property
    @prevent_deleted
    def entity_tags(self) -> list[int] | None:
        """Get the entity tags of the remove."""
        return self._entity_tags

    @entity_tags.setter
    @prevent_deleted
    def entity_tags(self, entity_tags: list[int] | None) -> None:
        """Set the entity tags of the remove."""
        validate_entity_set(
            entity_tags, self._cad_names, self._cad_paths, "target", "Remove"
        )
        self._entity_tags = entity_tags
        self._update_rawapi_remove_operation()

    @property
    @prevent_deleted
    def cad_names(self) -> list[str] | None:
        """Get the CAD names of the remove."""
        return self._cad_names

    @cad_names.setter
    @prevent_deleted
    def cad_names(self, cad_names: list[str] | None) -> None:
        """Set the CAD names of the remove."""
        validate_entity_set(
            self._entity_tags, cad_names, self._cad_paths, "target", "Remove"
        )
        self._cad_names = cad_names
        self._update_rawapi_remove_operation()

    @property
    @prevent_deleted
    def cad_paths(self) -> list[CadPath] | None:
        """Get the CAD paths of the remove."""
        return self._cad_paths

    @cad_paths.setter
    @prevent_deleted
    def cad_paths(self, cad_paths: list[CadPath] | None) -> None:
        """Set the CAD paths of the remove."""
        validate_entity_set(
            self._entity_tags, self._cad_names, cad_paths, "target", "Remove"
        )
        self._cad_paths = cad_paths
        self._update_rawapi_remove_operation()

    def _update_rawapi_remove_operation(self) -> None:
        """Update the rawapi remove operation structure."""
        elements = create_cad_entities_from_lists(
            self._entity_tags, self._cad_names, self._cad_paths
        )
        self._require_remove_op().target = elements

    @prevent_deleted
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:

        elements = create_cad_entities_from_lists(
            self._entity_tags, self._cad_names, self._cad_paths
        )

        remove_entity_operation = rawapi.CadRemoveEntityOperation(
            target=elements,
        )
        cad_element = rawapi.CadGeometryElement(
            name=self._name,
            removeEntityOperation=remove_entity_operation,
        )
        return cad_element

    def __str__(self) -> str:
        return (
            f"Remove(entity_tags={self._entity_tags}, "
            f"cad_names={self._cad_names}, cad_paths={self._cad_paths}, "
            f"name={self._name})"
        )
