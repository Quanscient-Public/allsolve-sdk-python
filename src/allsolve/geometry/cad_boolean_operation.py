# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from allsolve.geometry.cad_path import CadPath
from allsolve.geometry.cad_geometry_element import CadGeometryElement
from allsolve.geometry.cad_geometry_type import CadGeometryType
from allsolve.geometry.cad_utils import (
    create_cad_entities_from_lists,
    extract_entities_from_elements,
    to_str_list,
    validate_entity_set,
)
from allsolve.util import prevent_deleted
import allsolve_rawapi as rawapi
from typing_extensions import Self
import abc


class _CadBinaryBooleanOperation(CadGeometryElement, abc.ABC):
    """
    Base class for binary boolean operations (Difference, Intersection, Fragments).
    These operations have two sets of entities: object (set 1) and tool (set 2).
    """

    @classmethod
    @abc.abstractmethod
    def _get_operation_type(cls) -> rawapi.CadBooleanOperationType:
        """Return the CadBooleanOperationType for this operation."""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def _get_operation_name(cls) -> str:
        """Return the operation name for error messages."""
        raise NotImplementedError

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:
        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.boolean_operation is None:
            raise ValueError("Boolean operation is not set")
        expected_type = cls._get_operation_type()
        if cad_element.boolean_operation.type != expected_type:
            operation_name = cls._get_operation_name()
            raise ValueError(f"Boolean operation type is not {operation_name}")
        if cad_element.name is None:
            operation_name = cls._get_operation_name()
            raise ValueError(f"{operation_name} name must be set")
        if cad_element.boolean_operation.object is None:
            raise ValueError("Boolean operation object is not set")
        if cad_element.boolean_operation.object.elements is None:
            raise ValueError("Boolean operation object elements is not set")

        entity_tags_1, cad_names_1, cad_paths_1 = extract_entities_from_elements(
            cad_element.boolean_operation.object.elements
        )

        entity_tags_2: list[int] | None = None
        cad_names_2: list[str] | None = None
        cad_paths_2: list[CadPath] | None = None
        delete_tool: bool = False
        if cad_element.boolean_operation.tool is not None:
            if cad_element.boolean_operation.tool.elements is not None:
                entity_tags_2, cad_names_2, cad_paths_2 = (
                    extract_entities_from_elements(
                        cad_element.boolean_operation.tool.elements
                    )
                )
            if (
                hasattr(cad_element.boolean_operation.tool, "delete")
                and cad_element.boolean_operation.tool.delete is not None
            ):
                delete_tool = cad_element.boolean_operation.tool.delete

        cad_object = cls(
            name=cad_element.name,
            entity_tags_1=entity_tags_1 if entity_tags_1 else None,
            cad_names_1=cad_names_1 if cad_names_1 else None,
            cad_paths_1=cad_paths_1 if cad_paths_1 else None,
            entity_tags_2=entity_tags_2 if entity_tags_2 else None,
            cad_names_2=cad_names_2 if cad_names_2 else None,
            cad_paths_2=cad_paths_2 if cad_paths_2 else None,
            delete_tool=delete_tool,
        )
        cls._initialize_from_rawapi(cad_object, rawapi_element, cad_element, project_id)
        return cad_object

    def __init__(
        self,
        name: str,
        entity_tags_1: list[int] | None = None,
        cad_names_1: list[str] | None = None,
        cad_paths_1: list[CadPath] | None = None,
        entity_tags_2: list[int] | None = None,
        cad_names_2: list[str] | None = None,
        cad_paths_2: list[CadPath] | None = None,
        delete_tool: bool = True,
        enabled: str | bool | None = None,
    ) -> None:
        """
        Create a new binary boolean operation of two or more CAD geometry elements.
        At least one of entity tags, CAD names, or CAD paths must be set for both sets.

        Parameters:
            name: Name for the geometry element.
            entity_tags_1: The list of entity tags for the first set.
            cad_names_1: The list of CAD names for the first set.
            cad_paths_1: The list of CAD paths for the first set.
            entity_tags_2: The list of entity tags for the second set.
            cad_names_2: The list of CAD names for the second set.
            cad_paths_2: The list of CAD paths for the second set.
            delete_tool: Boolean flag to delete the tool entities after the operation. Default is True.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.
        """
        super().__init__(name, enabled)
        self._entity_tags_1 = entity_tags_1
        self._cad_names_1 = to_str_list(cad_names_1)
        self._cad_paths_1 = cad_paths_1
        self._entity_tags_2 = entity_tags_2
        self._cad_names_2 = to_str_list(cad_names_2)
        self._cad_paths_2 = cad_paths_2
        self._delete_tool = delete_tool

        operation_name = self._get_operation_name()
        validate_entity_set(
            entity_tags_1, cad_names_1, cad_paths_1, "first set", operation_name
        )

        if isinstance(self, CadFragments):
            # For fragments operation force delete tool to True
            # and allow empty second set.
            self._delete_tool = True
            if (
                entity_tags_2 is not None
                or cad_names_2 is not None
                or cad_paths_2 is not None
            ):
                validate_entity_set(
                    entity_tags_2,
                    cad_names_2,
                    cad_paths_2,
                    "second set",
                    operation_name,
                )
        else:
            validate_entity_set(
                entity_tags_2, cad_names_2, cad_paths_2, "second set", operation_name
            )

    def _require_boolean_op(self) -> rawapi.CadBooleanOperation:
        cad_elem = self._require_cad_elem()
        if cad_elem.boolean_operation is None:
            raise ValueError("Boolean operation is not set")
        return cad_elem.boolean_operation

    @property
    @prevent_deleted
    def entity_tags_1(self) -> list[int] | None:
        """Get the entity tags of the first set."""
        return self._entity_tags_1

    @entity_tags_1.setter
    @prevent_deleted
    def entity_tags_1(self, entity_tags_1: list[int] | None) -> None:
        """Set the entity tags of the first set."""
        operation_name = self._get_operation_name()
        validate_entity_set(
            entity_tags_1,
            self._cad_names_1,
            self._cad_paths_1,
            "first set",
            operation_name,
        )
        self._entity_tags_1 = entity_tags_1
        self._update_rawapi_boolean_operation()

    @property
    @prevent_deleted
    def cad_names_1(self) -> list[str] | None:
        """Get the CAD names of the first set."""
        return self._cad_names_1

    @cad_names_1.setter
    @prevent_deleted
    def cad_names_1(self, cad_names_1: list[str] | None) -> None:
        """Set the CAD names of the first set."""
        operation_name = self._get_operation_name()
        validate_entity_set(
            self._entity_tags_1,
            cad_names_1,
            self._cad_paths_1,
            "first set",
            operation_name,
        )
        self._cad_names_1 = cad_names_1
        self._update_rawapi_boolean_operation()

    @property
    @prevent_deleted
    def cad_paths_1(self) -> list[CadPath] | None:
        """Get the CAD paths of the first set."""
        return self._cad_paths_1

    @cad_paths_1.setter
    @prevent_deleted
    def cad_paths_1(self, cad_paths_1: list[CadPath] | None) -> None:
        """Set the CAD paths of the first set."""
        operation_name = self._get_operation_name()
        validate_entity_set(
            self._entity_tags_1,
            self._cad_names_1,
            cad_paths_1,
            "first set",
            operation_name,
        )
        self._cad_paths_1 = cad_paths_1
        self._update_rawapi_boolean_operation()

    @property
    @prevent_deleted
    def entity_tags_2(self) -> list[int] | None:
        """Get the entity tags of the second set."""
        return self._entity_tags_2

    @entity_tags_2.setter
    @prevent_deleted
    def entity_tags_2(self, entity_tags_2: list[int] | None) -> None:
        """Set the entity tags of the second set."""
        operation_name = self._get_operation_name()
        validate_entity_set(
            entity_tags_2,
            self._cad_names_2,
            self._cad_paths_2,
            "second set",
            operation_name,
        )
        self._entity_tags_2 = entity_tags_2
        self._update_rawapi_boolean_operation()

    @property
    @prevent_deleted
    def cad_names_2(self) -> list[str] | None:
        """Get the CAD names of the second set."""
        return self._cad_names_2

    @cad_names_2.setter
    @prevent_deleted
    def cad_names_2(self, cad_names_2: list[str] | None) -> None:
        """Set the CAD names of the second set."""
        operation_name = self._get_operation_name()
        validate_entity_set(
            self._entity_tags_2,
            cad_names_2,
            self._cad_paths_2,
            "second set",
            operation_name,
        )
        self._cad_names_2 = cad_names_2
        self._update_rawapi_boolean_operation()

    @property
    @prevent_deleted
    def cad_paths_2(self) -> list[CadPath] | None:
        """Get the CAD paths of the second set."""
        return self._cad_paths_2

    @cad_paths_2.setter
    @prevent_deleted
    def cad_paths_2(self, cad_paths_2: list[CadPath] | None) -> None:
        """Set the CAD paths of the second set."""
        operation_name = self._get_operation_name()
        validate_entity_set(
            self._entity_tags_2,
            self._cad_names_2,
            cad_paths_2,
            "second set",
            operation_name,
        )
        self._cad_paths_2 = cad_paths_2
        self._update_rawapi_boolean_operation()

    @property
    @prevent_deleted
    def delete_tool(self) -> bool:
        """Get the delete tool flag."""
        return self._delete_tool

    @delete_tool.setter
    @prevent_deleted
    def delete_tool(self, delete_tool: bool) -> None:
        """Set the delete tool flag."""
        self._delete_tool = delete_tool
        self._update_rawapi_boolean_operation()

    def _update_rawapi_boolean_operation(self) -> None:
        """Update the rawapi boolean operation structure."""
        boolean_op = self._require_boolean_op()

        elements = create_cad_entities_from_lists(
            self._entity_tags_1, self._cad_names_1, self._cad_paths_1
        )
        boolean_elements = rawapi.CadBooleanElements(elements=elements)
        boolean_op.object = boolean_elements

        tool_elements: list[rawapi.CadEntity] | None = None
        if (
            self._entity_tags_2 is not None
            or self._cad_names_2 is not None
            or self._cad_paths_2 is not None
        ):
            tool_elements = create_cad_entities_from_lists(
                self._entity_tags_2, self._cad_names_2, self._cad_paths_2
            )

        tool: rawapi.CadBooleanElements | None = None
        if tool_elements is not None or self._delete_tool:
            tool = rawapi.CadBooleanElements(
                elements=tool_elements if tool_elements else [],
            )
            if self._delete_tool:
                tool.delete = self._delete_tool
        boolean_op.tool = tool

    @prevent_deleted
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:
        elements = create_cad_entities_from_lists(
            self._entity_tags_1, self._cad_names_1, self._cad_paths_1
        )
        boolean_elements = rawapi.CadBooleanElements(elements=elements)

        tool_elements: list[rawapi.CadEntity] | None = None
        if (
            self._entity_tags_2 is not None
            or self._cad_names_2 is not None
            or self._cad_paths_2 is not None
        ):
            tool_elements = create_cad_entities_from_lists(
                self._entity_tags_2, self._cad_names_2, self._cad_paths_2
            )

        tool: rawapi.CadBooleanElements | None = None
        if tool_elements is not None or self._delete_tool:
            tool = rawapi.CadBooleanElements(
                elements=tool_elements if tool_elements else [],
            )
            tool.delete = self._delete_tool

        boolean_operation = rawapi.CadBooleanOperation(
            type=self._get_operation_type(),
            object=boolean_elements,
            tool=tool,
        )

        cad_element = rawapi.CadGeometryElement(
            booleanOperation=boolean_operation,
            name=self._name,
        )

        cad_element.name = self._name

        return cad_element


class CadUnion(CadGeometryElement):
    """
    CadUnion represents a union of two or more CAD geometry elements.
    """

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:
        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.boolean_operation is None:
            raise ValueError("Boolean operation is not set")
        if cad_element.boolean_operation.type != rawapi.CadBooleanOperationType.UNION:
            raise ValueError("Boolean operation type is not UNION")
        if cad_element.name is None:
            raise ValueError("Union name must be set")
        if cad_element.boolean_operation.object is None:
            raise ValueError("Boolean operation object is not set")
        if cad_element.boolean_operation.object.elements is None:
            raise ValueError("Boolean operation object elements is not set")

        entity_tags, cad_names, cad_paths = extract_entities_from_elements(
            cad_element.boolean_operation.object.elements
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
        Create a new union of two or more CAD geometry elements.
        At least one of entity tags, CAD names, or CAD paths must be set.

        Parameters:
            name: Name for the geometry element.
            entity_tags: The list of entity tags to union.
            cad_names: The list of CAD names to union.
            cad_paths: The list of CAD paths to union.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.
        """
        super().__init__(name, enabled)
        self._entity_tags = entity_tags
        self._cad_names = to_str_list(cad_names)
        self._cad_paths = cad_paths
        validate_entity_set(entity_tags, cad_names, cad_paths, "Set 1", "Union")

    def _require_boolean_op(self) -> rawapi.CadBooleanOperation:
        cad_elem = self._require_cad_elem()
        if cad_elem.boolean_operation is None:
            raise ValueError("Boolean operation is not set")
        return cad_elem.boolean_operation

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.UNION

    @property
    @prevent_deleted
    def entity_tags(self) -> list[int] | None:
        """Get the entity tags of the union."""
        return self._entity_tags

    @entity_tags.setter
    @prevent_deleted
    def entity_tags(self, entity_tags: list[int] | None) -> None:
        """Set the entity tags of the union."""
        validate_entity_set(
            entity_tags, self._cad_names, self._cad_paths, "Set 1", "Union"
        )
        self._entity_tags = entity_tags
        self._update_rawapi_boolean_operation()

    @property
    @prevent_deleted
    def cad_names(self) -> list[str] | None:
        """Get the CAD names of the union."""
        return self._cad_names

    @cad_names.setter
    @prevent_deleted
    def cad_names(self, cad_names: list[str] | None) -> None:
        """Set the CAD names of the union."""
        validate_entity_set(
            self._entity_tags, cad_names, self._cad_paths, "Set 1", "Union"
        )
        self._cad_names = cad_names
        self._update_rawapi_boolean_operation()

    @property
    @prevent_deleted
    def cad_paths(self) -> list[CadPath] | None:
        """Get the CAD paths of the union."""
        return self._cad_paths

    @cad_paths.setter
    @prevent_deleted
    def cad_paths(self, cad_paths: list[CadPath] | None) -> None:
        """Set the CAD paths of the union."""
        validate_entity_set(
            self._entity_tags, self._cad_names, cad_paths, "Set 1", "Union"
        )
        self._cad_paths = cad_paths
        self._update_rawapi_boolean_operation()

    def _update_rawapi_boolean_operation(self) -> None:
        """Update the rawapi boolean operation structure."""
        boolean_op = self._require_boolean_op()

        elements = create_cad_entities_from_lists(
            self._entity_tags, self._cad_names, self._cad_paths
        )
        boolean_elements = rawapi.CadBooleanElements(elements=elements)
        boolean_op.object = boolean_elements

    @prevent_deleted
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:
        elements = create_cad_entities_from_lists(
            self._entity_tags, self._cad_names, self._cad_paths
        )
        boolean_elements = rawapi.CadBooleanElements(elements=elements)

        boolean_operation = rawapi.CadBooleanOperation(
            type=rawapi.CadBooleanOperationType.UNION,
            object=boolean_elements,
        )

        cad_element = rawapi.CadGeometryElement(
            booleanOperation=boolean_operation,
            name=self._name,
        )

        cad_element.name = self._name

        return cad_element

    def __str__(self) -> str:
        return (
            f"Union(entity_tags={self._entity_tags}, "
            f"cad_names={self._cad_names}, cad_paths={self._cad_paths}, "
            f"name={self._name})"
        )


class CadDifference(_CadBinaryBooleanOperation):
    """
    CadDifference represents a difference of two or more CAD geometry elements.
    """

    @classmethod
    def _get_operation_type(cls) -> rawapi.CadBooleanOperationType:
        """Return the CadBooleanOperationType for this operation."""
        return rawapi.CadBooleanOperationType.DIFFERENCE

    @classmethod
    def _get_operation_name(cls) -> str:
        """Return the operation name for error messages."""
        return "Difference"

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.DIFFERENCE

    def __str__(self) -> str:
        return (
            f"DifferenceOperation("
            f"entity_tags_1={self._entity_tags_1}, "
            f"cad_names_1={self._cad_names_1}, "
            f"cad_paths_1={self._cad_paths_1}, "
            f"entity_tags_2={self._entity_tags_2}, "
            f"cad_names_2={self._cad_names_2}, "
            f"cad_paths_2={self._cad_paths_2}, "
            f"delete_tool={self._delete_tool}, name={self._name})"
        )


class CadIntersection(_CadBinaryBooleanOperation):
    """
    CadIntersectionOperation represents an intersection of two or more CAD geometry elements.
    """

    @classmethod
    def _get_operation_type(cls) -> rawapi.CadBooleanOperationType:
        """Return the CadBooleanOperationType for this operation."""
        return rawapi.CadBooleanOperationType.INTERSECTION

    @classmethod
    def _get_operation_name(cls) -> str:
        """Return the operation name for error messages."""
        return "Intersection"

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.INTERSECTION

    def __str__(self) -> str:
        return (
            f"IntersectionOperation("
            f"entity_tags_1={self._entity_tags_1}, "
            f"cad_names_1={self._cad_names_1}, "
            f"cad_paths_1={self._cad_paths_1}, "
            f"entity_tags_2={self._entity_tags_2}, "
            f"cad_names_2={self._cad_names_2}, "
            f"cad_paths_2={self._cad_paths_2}, "
            f"delete_tool={self._delete_tool}, name={self._name})"
        )


class CadFragments(_CadBinaryBooleanOperation):
    """
    CadFragments represents a fragments operation of two or more CAD geometry elements.
    """

    @classmethod
    def _get_operation_type(cls) -> rawapi.CadBooleanOperationType:
        """Return the CadBooleanOperationType for this operation."""
        return rawapi.CadBooleanOperationType.FRAGMENTS

    @classmethod
    def _get_operation_name(cls) -> str:
        """Return the operation name for error messages."""
        return "Fragments"

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.FRAGMENTS

    def __str__(self) -> str:
        return (
            f"Fragments("
            f"entity_tags_1={self._entity_tags_1}, "
            f"cad_names_1={self._cad_names_1}, "
            f"cad_paths_1={self._cad_paths_1}, "
            f"entity_tags_2={self._entity_tags_2}, "
            f"cad_names_2={self._cad_names_2}, "
            f"cad_paths_2={self._cad_paths_2}, "
            f"delete_tool={self._delete_tool}, name={self._name})"
        )


class CadFragmentAll(CadGeometryElement):
    """
    CadFragmentAll represents a fragment all operation that fragments all CAD geometry elements.
    """

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:
        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.boolean_operation is None:
            raise ValueError("Boolean operation is not set")
        if (
            cad_element.boolean_operation.type
            != rawapi.CadBooleanOperationType.FRAGMENTALL
        ):
            raise ValueError("Boolean operation type is not FRAGMENTALL")
        if cad_element.name is None:
            raise ValueError("FragmentAll name must be set")

        cad_object = cls(name=cad_element.name)
        cls._initialize_from_rawapi(cad_object, rawapi_element, cad_element, project_id)
        return cad_object

    def __init__(
        self,
        name: str,
        enabled: str | bool | None = None,
    ) -> None:
        """
        Create a new fragment all operation that fragments all CAD geometry elements.

        Parameters:
            name: Name for the geometry element.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.
        """
        super().__init__(name, enabled)

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.FRAGMENT_ALL

    @prevent_deleted
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:
        boolean_elements = rawapi.CadBooleanElements(elements=[])

        boolean_operation = rawapi.CadBooleanOperation(
            type=rawapi.CadBooleanOperationType.FRAGMENTALL,
            object=boolean_elements,
        )

        cad_element = rawapi.CadGeometryElement(
            booleanOperation=boolean_operation,
            name=self._name,
        )

        cad_element.name = self._name

        return cad_element

    def __str__(self) -> str:
        return f"FragmentAll(name={self._name})"
