# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

import abc
from allsolve.api import check_for_project_api_key, get_api, get_auth
from allsolve.geometry.cad_geometry_type import CadGeometryType
from allsolve.geometry.cad_utils import create_boolean, from_boolean
from allsolve.util import prevent_deleted
import allsolve_rawapi as rawapi


class CadGeometryElement(abc.ABC):
    """
    CadGeometryElement is a base class for creating CAD geometry programmatically.
    Subclasses provide convenient ways to create specific geometry types like boxes, cylinders, etc.
    """

    def __init__(
        self,
        name: str | None = None,
        enabled: str | bool | None = None,
    ) -> None:
        self._project_id: str | None = None
        self._id: str | None = None
        self._name: str | None = name
        self._enabled: str | bool | None = enabled
        self._geometry: rawapi.GeometryElement | None = None
        self._deleted: bool = False
        self._uncommitted_update: rawapi.GeometryElement | None = None

    @classmethod
    def _determine_type(cls, cad_element: rawapi.GeometryElement) -> CadGeometryType:
        """
        Determine the type of the CAD geometry element.
        """
        if cad_element.cad_elem is None:
            raise ValueError("CAD geometry element is not set")

        if cad_element.cad_elem.cad_file is not None:
            if cad_element.cad_elem.cad_file.type == rawapi.CadImportType.STEP:
                return CadGeometryType.STEP_FILE
            elif cad_element.cad_elem.cad_file.type == rawapi.CadImportType.IGES:
                return CadGeometryType.IGES_FILE
            elif cad_element.cad_elem.cad_file.type == rawapi.CadImportType.SAT:
                return CadGeometryType.SAT_FILE
            elif cad_element.cad_elem.cad_file.type == rawapi.CadImportType.BREP:
                return CadGeometryType.BREP_FILE
            elif cad_element.cad_elem.cad_file.type == rawapi.CadImportType.GDS2:
                return CadGeometryType.GDS2_FILE
            elif cad_element.cad_elem.cad_file.type == rawapi.CadImportType.MSH:
                return CadGeometryType.MSH_FILE
            elif cad_element.cad_elem.cad_file.type == rawapi.CadImportType.NAS:
                return CadGeometryType.NAS_FILE

        if cad_element.cad_elem.geo_type is not None:
            if cad_element.cad_elem.geo_type.box is not None:
                return CadGeometryType.BOX
            elif cad_element.cad_elem.geo_type.cylinder is not None:
                return CadGeometryType.CYLINDER
            elif cad_element.cad_elem.geo_type.sphere is not None:
                return CadGeometryType.SPHERE
            elif cad_element.cad_elem.geo_type.cone is not None:
                return CadGeometryType.CONE
            elif cad_element.cad_elem.geo_type.torus is not None:
                return CadGeometryType.TORUS
            elif cad_element.cad_elem.geo_type.surface_rectangle is not None:
                return CadGeometryType.SURFACE_RECTANGLE
            elif cad_element.cad_elem.geo_type.disk is not None:
                return CadGeometryType.DISK
            elif cad_element.cad_elem.geo_type.rectangle is not None:
                return CadGeometryType.RECTANGLE

        if cad_element.cad_elem.boolean_operation is not None:
            if (
                cad_element.cad_elem.boolean_operation.type
                == rawapi.CadBooleanOperationType.UNION
            ):
                return CadGeometryType.UNION
            elif (
                cad_element.cad_elem.boolean_operation.type
                == rawapi.CadBooleanOperationType.DIFFERENCE
            ):
                return CadGeometryType.DIFFERENCE
            elif (
                cad_element.cad_elem.boolean_operation.type
                == rawapi.CadBooleanOperationType.INTERSECTION
            ):
                return CadGeometryType.INTERSECTION
            elif (
                cad_element.cad_elem.boolean_operation.type
                == rawapi.CadBooleanOperationType.FRAGMENTS
            ):
                return CadGeometryType.FRAGMENTS
            elif (
                cad_element.cad_elem.boolean_operation.type
                == rawapi.CadBooleanOperationType.FRAGMENTALL
            ):
                return CadGeometryType.FRAGMENT_ALL

        if cad_element.cad_elem.transform_operation is not None:
            if cad_element.cad_elem.transform_operation.translate is not None:
                return CadGeometryType.TRANSLATE
            elif cad_element.cad_elem.transform_operation.rotate is not None:
                return CadGeometryType.ROTATE
            elif cad_element.cad_elem.transform_operation.grid is not None:
                return CadGeometryType.GRID

        if cad_element.cad_elem.remove_entity_operation is not None:
            return CadGeometryType.REMOVE

        raise ValueError("Unsupported CAD geometry element type")

    @classmethod
    def _initialize_from_rawapi(
        cls,
        cad_object: "CadGeometryElement",
        rawapi_element: rawapi.GeometryElement,
        cad_element: rawapi.CadGeometryElement,
        project_id: str | None,
    ) -> None:
        """
        Initialize common attributes from rawapi elements.
        This helper method is used by _from_rawapi classmethods in child classes.

        Parameters:
            cad_object: The CAD geometry object to initialize.
            rawapi_element: The rawapi GeometryElement.
            cad_element: The rawapi CadGeometryElement.
            project_id: The project ID.
        """
        cad_object._enabled = from_boolean(cad_element.enabled)
        cad_object._id = rawapi_element.id
        cad_object._name = cad_element.name
        cad_object._project_id = project_id
        cad_object._geometry = rawapi_element

    @property
    @prevent_deleted
    def id(self) -> str | None:
        """Get the ID of the geometry element."""
        return self._id

    @property
    @prevent_deleted
    def project_id(self) -> str:
        """Get the project ID of the geometry element."""
        if self._project_id is None:
            raise ValueError("Project ID is not set")
        return self._project_id

    @property
    @prevent_deleted
    def name(self) -> str | None:
        """Get the name of the geometry element."""
        return self._name

    @name.setter
    def name(self, value: str | None) -> None:
        """Set the name of the geometry element."""
        self._name = value

    @property
    @prevent_deleted
    def enabled(self) -> str | bool | None:
        """Get the enabled state of the geometry element. Can be a boolean or a string expression."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: str | bool | None) -> None:
        """Set the enabled state of the geometry element. Can be a boolean or a string expression."""
        self._enabled = value

    @property
    @abc.abstractmethod
    def type(self) -> CadGeometryType:
        """
        Get the type of the geometry element.

        Returns:
            The CadGeometryType enum value for this geometry element.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement type property"
        )

    @prevent_deleted
    def delete(self) -> None:
        """
        Delete the geometry element from the project.
        """
        project_id = check_for_project_api_key(self._project_id)
        with get_api() as api:
            api.delete_geometry_elements(
                authorization=get_auth(),
                project_id=project_id,
                element_id=self.id,
            )
        self._deleted = True

    @prevent_deleted
    def save(self) -> None:
        """
        Save the changes to the geometry element.
        Calling save() on a geometry element that is not added to the project using
        GeometryBuilder will raise a ValueError.
        """
        if self._uncommitted_update is None:
            return
        if self.id is None:
            raise ValueError("Geometry element ID is not set")
        if self.name is None:
            raise ValueError("Geometry element name is not set")
        project_id = check_for_project_api_key(self._project_id)
        geometry_element = self._current_uncommitted_update()
        if geometry_element.cad_elem is None:
            raise ValueError("CAD geometry element is not set")
        geometry_element.id = self.id
        geometry_element.name = self.name
        geometry_element.cad_elem.name = self.name
        if geometry_element.cad_elem is not None:
            geometry_element.cad_elem.enabled = create_boolean(self._enabled)

        with get_api() as api:
            api.update_geometry_element(
                authorization=get_auth(),
                project_id=project_id,
                geometry_element=geometry_element,
            )
        self._uncommitted_update = None

    @prevent_deleted
    def _to_rawapi(self) -> rawapi.GeometryElement:
        element: rawapi.GeometryElement = rawapi.GeometryElement(
            id=self._id if self._id is not None else "",
            name=self._name if self._name is not None else "",
            cadElem=self._to_rawapi_cad_element(),
        )
        if element.cad_elem is not None:
            element.cad_elem.enabled = create_boolean(self._enabled)

        return element

    @prevent_deleted
    def _to_rawapi_new_geometry_element(self) -> rawapi.NewGeometryElement:
        element: rawapi.NewGeometryElement = rawapi.NewGeometryElement(
            name=self._name if self._name is not None else "",
            cadElem=self._to_rawapi_cad_element(),
        )
        if element.cad_elem is not None:
            element.cad_elem.enabled = create_boolean(self._enabled)

        return element

    @abc.abstractmethod
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _to_rawapi_cad_element() method"
        )

    @prevent_deleted
    def _current_uncommitted_update(self) -> rawapi.GeometryElement:
        if self._uncommitted_update is None:
            self._uncommitted_update = self._to_rawapi()
        return self._uncommitted_update

    def _require_cad_elem(self) -> rawapi.CadGeometryElement:
        update = self._current_uncommitted_update()
        if update.cad_elem is None:
            raise ValueError("CAD geometry element is not set")
        return update.cad_elem

    def _is_file_import(self) -> bool:
        return False

    def _initialize_file_attributes(self) -> str:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _initialize_file_attributes() method"
        )

    def _upload(self) -> rawapi.InputFile:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _upload() method"
        )
