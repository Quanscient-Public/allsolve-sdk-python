# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from typing import List, TextIO, Tuple, Union
from typing_extensions import Self
import sys

from allsolve.geometry.cad_boolean_operation import (
    CadUnion,
    CadDifference,
    CadIntersection,
    CadFragments,
    CadFragmentAll,
)
from allsolve.geometry.cad_geometry_element import (
    CadGeometryElement,
)
from allsolve.geometry.cad_simple_operation import (
    CadTranslate,
    CadRotate,
    CadGrid,
    CadRemove,
)
from .cad_geometry_type import CadGeometryType
from .cad_path import CadPath
from .cad_basic_geometry import (
    CadBox,
    CadCylinder,
    CadDisk,
    CadRectangle,
    CadSphere,
    CadCone,
    CadTorus,
    CadSurfaceRectangle,
    CadPoint,
)
from .cad_file_import import (
    CadStepFile,
    CadIgesFile,
    CadSatFile,
    CadBrepFile,
    CadMshFile,
    CadNasFile,
    CadGds2File,
    CadGdsLayer,
    CadGdsExtrudeParameters,
)
import allsolve_rawapi as rawapi
from allsolve_rawapi.exceptions import ApiException
from ..api import get_api, get_auth, check_for_project_api_key
from ..job import Job, OnError
from ..job_mixin import JobMixin
from ..util import JobError

CadElement = Union[
    CadBox,
    CadCylinder,
    CadSphere,
    CadCone,
    CadTorus,
    CadSurfaceRectangle,
    CadStepFile,
    CadIgesFile,
    CadSatFile,
    CadBrepFile,
    CadMshFile,
    CadNasFile,
    CadGds2File,
    CadUnion,
    CadDifference,
    CadIntersection,
    CadFragments,
    CadFragmentAll,
    CadTranslate,
    CadRotate,
    CadGrid,
    CadRemove,
    CadDisk,
    CadRectangle,
]


class GeometryBuilder(JobMixin):
    """
    Geometry builder for a project.
    Use with projects that have the GeometryPipelineVersion.V2
    """

    _CAD_TYPE_TO_CLASS: dict[CadGeometryType, type[CadElement]] = {
        CadGeometryType.BOX: CadBox,
        CadGeometryType.CYLINDER: CadCylinder,
        CadGeometryType.SPHERE: CadSphere,
        CadGeometryType.CONE: CadCone,
        CadGeometryType.TORUS: CadTorus,
        CadGeometryType.SURFACE_RECTANGLE: CadSurfaceRectangle,
        CadGeometryType.DISK: CadDisk,
        CadGeometryType.RECTANGLE: CadRectangle,
        CadGeometryType.UNION: CadUnion,
        CadGeometryType.DIFFERENCE: CadDifference,
        CadGeometryType.INTERSECTION: CadIntersection,
        CadGeometryType.FRAGMENTS: CadFragments,
        CadGeometryType.FRAGMENT_ALL: CadFragmentAll,
        CadGeometryType.TRANSLATE: CadTranslate,
        CadGeometryType.ROTATE: CadRotate,
        CadGeometryType.GRID: CadGrid,
        CadGeometryType.REMOVE: CadRemove,
        CadGeometryType.STEP_FILE: CadStepFile,
        CadGeometryType.IGES_FILE: CadIgesFile,
        CadGeometryType.SAT_FILE: CadSatFile,
        CadGeometryType.BREP_FILE: CadBrepFile,
        CadGeometryType.MSH_FILE: CadMshFile,
        CadGeometryType.NAS_FILE: CadNasFile,
        CadGeometryType.GDS2_FILE: CadGds2File,
    }

    def __init__(
        self,
        project_id: str,
    ) -> None:
        self._project_id: str = project_id
        self._job: Job | None = None

    def add(self, geometry: List[CadElement] | CadElement) -> Self:
        """
        Creates new geometry elements in the project.

        Parameters:
            geometry: A list of CAD geometry elements or a single CAD geometry element.

        Returns:
            The GeometryBuilder object.
        """
        if isinstance(geometry, list):
            for cad_geometry_element in geometry:
                self._create_element(cad_geometry_element)
        else:
            self._create_element(geometry)
        return self

    def add_box(
        self,
        name: str,
        position: tuple[float | str, float | str, float | str],
        size: tuple[float | str, float | str, float | str],
        rotation: tuple[float | str, float | str, float | str] | None = None,
        alignment: rawapi.CadAlignment | None = None,
        enabled: str | bool | None = None,
    ) -> Self:
        """
        Adds a box to the project.

        Parameters:
            name: Name for the geometry element.
            position: The position of the box center as (x, y, z).
            size: The size of the box as (width, height, depth).
            rotation: Optional rotation as Euler angles (x, y, z) in degrees.
            alignment: Alignment of the box relative to its position.
                CadAlignment.CENTER (center of the bounding box) or
                CadAlignment.CORNER (smallest XYZ corner of the bounding box).
                Default is center.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadBox(
                position=position,
                size=size,
                name=name,
                rotation=rotation,
                alignment=alignment,
                enabled=enabled,
            )
        )
        return self

    def add_cone(
        self,
        name: str,
        position: tuple[float | str, float | str, float | str],
        axis: tuple[float | str, float | str, float | str],
        radius1: float | str,
        radius2: float | str,
        angle1: float | str | None = None,
        angle2: float | str | None = None,
        rotation: tuple[float | str, float | str, float | str] | None = None,
        alignment: rawapi.CadAlignment | None = None,
        enabled: str | bool | None = None,
    ) -> Self:
        """
        Adds a cone to the project.

        Parameters:
            name: Name for the geometry element.
            position: The position of the cone center as (x, y, z).
            axis: The axis direction vector as (x, y, z).
            radius1: The base radius of the cone.
            radius2: The top radius of the cone (0 for pointy cone).
            angle1: Optional first angle for partial cones in degrees.
            angle2: Optional second angle for partial cones in degrees.
            rotation: Optional rotation as Euler angles (x, y, z) in degrees.
            alignment: Alignment of the cone relative to its position.
                CadAlignment.CENTER (center of the bounding box) or
                CadAlignment.BASE (bottom center for radial geometries).
                Default is center.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadCone(
                name=name,
                position=position,
                axis=axis,
                radius1=radius1,
                radius2=radius2,
                angle1=angle1,
                angle2=angle2,
                rotation=rotation,
                alignment=alignment,
                enabled=enabled,
            )
        )
        return self

    def add_cylinder(
        self,
        name: str,
        position: tuple[float | str, float | str, float | str],
        axis: tuple[float | str, float | str, float | str],
        radius: float | str,
        inner_radius: float | str | None = None,
        angle1: float | str | None = None,
        angle2: float | str | None = None,
        rotation: tuple[float | str, float | str, float | str] | None = None,
        alignment: rawapi.CadAlignment | None = None,
        enabled: str | bool | None = None,
    ) -> Self:
        """
        Adds a cylinder to the project.

        Parameters:
            name: Name for the geometry element.
            position: The position of the cylinder center as (x, y, z).
            axis: The axis direction vector as (x, y, z).
            radius: The radius of the cylinder.
            inner_radius: Optional inner radius for hollow cylinders.
            angle1: Optional first angle for partial cylinders in degrees.
            angle2: Optional second angle for partial cylinders in degrees.
            rotation: Optional rotation as Euler angles (x, y, z) in degrees.
            alignment: Alignment of the cylinder relative to its position.
                CadAlignment.CENTER (center of the bounding box) or
                CadAlignment.BASE (bottom center for radial geometries).
                Default is center.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadCylinder(
                name=name,
                position=position,
                axis=axis,
                radius=radius,
                inner_radius=inner_radius,
                angle1=angle1,
                angle2=angle2,
                rotation=rotation,
                alignment=alignment,
                enabled=enabled,
            )
        )
        return self

    def add_disk(
        self,
        name: str,
        position: tuple[float | str, float | str],
        radius: float | str,
        inner_radius: float | str | None = None,
        angle1: float | str | None = None,
        angle2: float | str | None = None,
        rotation: tuple[float | str, float | str, float | str] | None = None,
        enabled: str | bool | None = None,
    ) -> Self:
        """
        Adds a disk to the project.

        Parameters:
            name: Name for the geometry element.
            position: The position of the disk center as (x, y).
            radius: The radius of the disk.
            inner_radius: Optional inner radius for ring-shaped disks.
            angle1: Optional first angle for partial disks in degrees.
            angle2: Optional second angle for partial disks in degrees.
            rotation: Optional rotation as Euler angles (x, y, z) in degrees.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadDisk(
                name=name,
                position=position,
                radius=radius,
                inner_radius=inner_radius,
                angle1=angle1,
                angle2=angle2,
                rotation=rotation,
                enabled=enabled,
            )
        )
        return self

    def add_rectangle(
        self,
        name: str,
        position: tuple[float | str, float | str],
        size: tuple[float | str, float | str],
        rotation: tuple[float | str, float | str, float | str] | None = None,
        alignment: rawapi.CadAlignment | None = None,
        enabled: str | bool | None = None,
    ) -> Self:
        """
        Adds a rectangle to the project.

        Parameters:
            name: Name for the geometry element.
            position: The position of the rectangle center as (x, y).
            size: The size of the rectangle as (width, height).
            rotation: Optional rotation as Euler angles (x, y, z) in degrees.
            alignment: Alignment of the rectangle relative to its position.
                CadAlignment.CENTER (center of the bounding box) or
                CadAlignment.CORNER (smallest XYZ corner of the bounding box).
                Default is center.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadRectangle(
                name=name,
                position=position,
                size=size,
                rotation=rotation,
                alignment=alignment,
                enabled=enabled,
            )
        )
        return self

    def add_sphere(
        self,
        name: str,
        position: tuple[float | str, float | str, float | str],
        radius: float | str,
        inner_radius: float | str | None = None,
        angle1: float | str | None = None,
        angle2: float | str | None = None,
        rotation: tuple[float | str, float | str, float | str] | None = None,
        enabled: str | bool | None = None,
    ) -> Self:
        """
        Adds a sphere to the project.

        Parameters:
            name: Name for the geometry element.
            position: The position of the sphere center as (x, y, z).
            radius: The radius of the sphere.
            inner_radius: Optional inner radius for hollow spheres.
            angle1: Optional first angle for partial spheres in degrees.
            angle2: Optional second angle for partial spheres in degrees.
            rotation: Optional rotation as Euler angles (x, y, z) in degrees.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadSphere(
                name=name,
                position=position,
                radius=radius,
                inner_radius=inner_radius,
                angle1=angle1,
                angle2=angle2,
                rotation=rotation,
                enabled=enabled,
            )
        )
        return self

    def add_surface_rectangle(
        self,
        name: str,
        size: tuple[float | str, float | str],
        offset: tuple[float | str, float | str, float | str],
        origin_point: CadPoint,
        main_axis_point: CadPoint,
        secondary_axis_point: CadPoint,
        enabled: str | bool | None = None,
    ) -> Self:
        """
        Adds a surface rectangle to the project.

        Parameters:
            name: Name for the geometry element.
            size: The size of the rectangle as (x, y).
            offset: The offset from the origin point as (x, y, z).
            origin_point: CAD entity reference for the origin point.
            main_axis_point: CAD entity reference for the main axis point.
            secondary_axis_point: CAD entity reference for the secondary axis point.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadSurfaceRectangle(
                name=name,
                size=size,
                offset=offset,
                origin_point=origin_point,
                main_axis_point=main_axis_point,
                secondary_axis_point=secondary_axis_point,
                enabled=enabled,
            )
        )
        return self

    def add_torus(
        self,
        name: str,
        position: tuple[float | str, float | str, float | str],
        radius1: float | str,
        radius2: float | str,
        inner_radius: float | str | None = None,
        angle1: float | str | None = None,
        angle2: float | str | None = None,
        rotation: tuple[float | str, float | str, float | str] | None = None,
        enabled: str | bool | None = None,
    ) -> Self:
        """
        Adds a torus to the project.

        Parameters:
            name: Name for the geometry element.
            position: The position of the torus center as (x, y, z).
            radius1: The outer radius of the torus.
            radius2: The width of the torus ring.
            inner_radius: Optional inner radius for hollow toruses.
            angle1: Optional first angle for partial toruses in degrees.
            angle2: Optional second angle for partial toruses in degrees.
            rotation: Optional rotation as Euler angles (x, y, z) in degrees.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadTorus(
                name=name,
                position=position,
                radius1=radius1,
                radius2=radius2,
                inner_radius=inner_radius,
                angle1=angle1,
                angle2=angle2,
                rotation=rotation,
                enabled=enabled,
            )
        )
        return self

    def add_difference(
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
    ) -> Self:
        """
        Adds a difference operation to the project.

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

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadDifference(
                name=name,
                entity_tags_1=entity_tags_1,
                cad_names_1=cad_names_1,
                cad_paths_1=cad_paths_1,
                entity_tags_2=entity_tags_2,
                cad_names_2=cad_names_2,
                cad_paths_2=cad_paths_2,
                delete_tool=delete_tool,
                enabled=enabled,
            )
        )
        return self

    def add_fragment_all(
        self,
        name: str,
        enabled: str | bool | None = None,
    ) -> Self:
        """
        Adds a fragment all operation to the project.

        Parameters:
            name: Name for the geometry element.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadFragmentAll(
                name=name,
                enabled=enabled,
            )
        )
        return self

    def add_fragments(
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
    ) -> Self:
        """
        Adds a fragments operation to the project.

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

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadFragments(
                name=name,
                entity_tags_1=entity_tags_1,
                cad_names_1=cad_names_1,
                cad_paths_1=cad_paths_1,
                entity_tags_2=entity_tags_2,
                cad_names_2=cad_names_2,
                cad_paths_2=cad_paths_2,
                delete_tool=delete_tool,
                enabled=enabled,
            )
        )
        return self

    def add_intersection(
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
    ) -> Self:
        """
        Adds an intersection operation to the project.

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

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadIntersection(
                name=name,
                entity_tags_1=entity_tags_1,
                cad_names_1=cad_names_1,
                cad_paths_1=cad_paths_1,
                entity_tags_2=entity_tags_2,
                cad_names_2=cad_names_2,
                cad_paths_2=cad_paths_2,
                delete_tool=delete_tool,
                enabled=enabled,
            )
        )
        return self

    def add_union(
        self,
        name: str,
        entity_tags: list[int] | None = None,
        cad_names: list[str] | None = None,
        cad_paths: list[CadPath] | None = None,
        enabled: str | bool | None = None,
    ) -> Self:
        """
        Adds a union operation to the project.

        Parameters:
            name: Name for the geometry element.
            entity_tags: The list of entity tags to union.
            cad_names: The list of CAD names to union.
            cad_paths: The list of CAD paths to union.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadUnion(
                name=name,
                entity_tags=entity_tags,
                cad_names=cad_names,
                cad_paths=cad_paths,
                enabled=enabled,
            )
        )
        return self

    def add_grid(
        self,
        name: str,
        translation: tuple[float | str, float | str, float | str],
        size: tuple[int | str, int | str, int | str],
        entity_tags: list[int] | None = None,
        cad_names: list[str] | None = None,
        cad_paths: list[CadPath] | None = None,
        enabled: str | bool | None = None,
    ) -> Self:
        """
        Adds a grid pattern to the project.

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

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadGrid(
                name=name,
                translation=translation,
                size=size,
                entity_tags=entity_tags,
                cad_names=cad_names,
                cad_paths=cad_paths,
                enabled=enabled,
            )
        )
        return self

    def add_remove(
        self,
        name: str,
        entity_tags: list[int] | None = None,
        cad_names: list[str] | None = None,
        cad_paths: list[CadPath] | None = None,
        enabled: str | bool | None = None,
    ) -> Self:
        """
        Adds a remove operation to the project.

        Parameters:
            name: Name for the geometry element.
            entity_tags: The list of entity tags to remove.
            cad_names: The list of CAD names to remove.
            cad_paths: The list of CAD paths to remove.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadRemove(
                name=name,
                entity_tags=entity_tags,
                cad_names=cad_names,
                cad_paths=cad_paths,
                enabled=enabled,
            )
        )
        return self

    def add_rotate(
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
    ) -> Self:
        """
        Adds a rotation operation to the project.

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

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadRotate(
                name=name,
                axis=axis,
                center=center,
                angle=angle,
                entity_tags=entity_tags,
                cad_names=cad_names,
                cad_paths=cad_paths,
                copy_object=copy_object,
                repeat=repeat,
                enabled=enabled,
            )
        )
        return self

    def add_translate(
        self,
        name: str,
        translation: tuple[float | str, float | str, float | str],
        entity_tags: list[int] | None = None,
        cad_names: list[str] | None = None,
        cad_paths: list[CadPath] | None = None,
        copy_object: bool = False,
        repeat: int | str | None = None,
        enabled: str | bool | None = None,
    ) -> Self:
        """
        Adds a translate operation to the project.

        Parameters:
            name: Name for the geometry element.
            translation: The translation vector.
            entity_tags: The list of entity tags to translate.
            cad_names: The list of CAD names to translate.
            cad_paths: The list of CAD paths to translate.
            copy_object: Copy the object instead of translating. Default is False.
            repeat: Number of times to repeat the translation. Default is None.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadTranslate(
                name=name,
                translation=translation,
                entity_tags=entity_tags,
                cad_names=cad_names,
                cad_paths=cad_paths,
                copy_object=copy_object,
                repeat=repeat,
                enabled=enabled,
            )
        )
        return self

    def add_brep_file(
        self,
        filepath: str,
        name: str | None = None,
        cleanup: bool = False,
        enabled: str | bool | None = None,
    ) -> Self:
        """
        Adds a BREP file import to the project.

        Parameters:
            filepath: Path to a local BREP file. The file will be uploaded automatically.
            name: Optional name for the geometry element.
            cleanup: Whether to clean up the imported file.
                Currently not supported yet.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadBrepFile(
                filepath=filepath,
                name=name,
                cleanup=cleanup,
                enabled=enabled,
            )
        )
        return self

    def add_gds2_file(
        self,
        filepath: str,
        layers: List[CadGdsLayer] | List[Tuple[int, int, int | float, int | float]],
        name: str | None = None,
        cleanup: bool = False,
        enabled: str | bool | None = None,
        extrude_parameters: CadGdsExtrudeParameters | None = None,
        unit: rawapi.CadDistanceUnit = rawapi.CadDistanceUnit.MICROMETER,
    ) -> Self:
        """
        Adds a GDS2 file import to the project.

        Parameters:
            filepath: Path to a local GDS2 file. The file will be uploaded automatically.
            layers: List of CadGdsLayer or tuples of
                (layer number, layer type number, absolute_z0, thickness).
            name: Optional name for the geometry element.
            cleanup: Whether to clean up the imported file.
                Currently not supported yet.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.
            extrude_parameters: Optional GDS2 extrusion parameters.
            unit: Default distance unit for distance values in layers and extrude_parameters.
                Defaults to CadDistanceUnit.MICROMETER.
        Returns:
            The GeometryBuilder object.
        """
        gds_layers: list[CadGdsLayer] = []
        for layer in layers:
            if isinstance(layer, CadGdsLayer):
                gds_layers.append(layer)
            elif isinstance(layer, tuple):
                if len(layer) != 4:
                    raise ValueError(
                        "GDS2 layer tuples must be (layer, type, absolute_z0, thickness)"
                    )
                layer_id, layer_type, absolute_z0, thickness = layer
                gds_layers.append(
                    CadGdsLayer(
                        layer=layer_id,
                        type=layer_type,
                        absolute_z0=absolute_z0,
                        thickness=thickness,
                    )
                )
            else:
                raise ValueError(
                    "Layers must be CadGdsLayer or tuples of "
                    "(layer, type, absolute_z0, thickness)"
                )

        self.add(
            CadGds2File(
                filepath=filepath,
                layers=gds_layers,
                name=name,
                cleanup=cleanup,
                enabled=enabled,
                extrude_parameters=extrude_parameters,
                unit=unit,
            )
        )
        return self

    def add_iges_file(
        self,
        filepath: str,
        name: str | None = None,
        cleanup: bool = False,
        enabled: str | bool | None = None,
    ) -> Self:
        """
        Adds an IGES file import to the project.

        Parameters:
            filepath: Path to a local IGES file. The file will be uploaded automatically.
            name: Optional name for the geometry element.
            cleanup: Whether to clean up the imported file.
                Currently not supported yet.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadIgesFile(
                filepath=filepath,
                name=name,
                cleanup=cleanup,
                enabled=enabled,
            )
        )
        return self

    def add_sat_file(
        self,
        filepath: str,
        name: str | None = None,
        cleanup: bool = False,
        enabled: str | bool | None = None,
    ) -> Self:
        """
        Adds a SAT file import to the project.

        Parameters:
            filepath: Path to a local SAT file. The file will be uploaded automatically.
            name: Optional name for the geometry element.
            cleanup: Whether to clean up the imported file.
                Currently not supported yet.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadSatFile(
                filepath=filepath,
                name=name,
                cleanup=cleanup,
                enabled=enabled,
            )
        )
        return self

    def add_step_file(
        self,
        filepath: str,
        name: str | None = None,
        cleanup: bool = False,
        enabled: str | bool | None = None,
    ) -> Self:
        """
        Adds a STEP file import to the project.

        Parameters:
            filepath: Path to a local STEP file. The file will be uploaded automatically.
            name: Optional name for the geometry element.
            cleanup: Whether to clean up the imported file.
                Currently not supported yet.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.

        Returns:
            The GeometryBuilder object.
        """
        self.add(
            CadStepFile(
                filepath=filepath,
                name=name,
                cleanup=cleanup,
                enabled=enabled,
            )
        )
        return self

    def add_msh_file(
        self,
        filepath: str,
    ) -> Self:
        """
        Adds a MSH file import to the project.
        Only one MSH file can exist in a project and it cannot coexist with other
        geometry elements.

        Parameters:
            filepath: Path to a local MSH file. The file will be uploaded automatically.

        Returns:
            The GeometryBuilder object.
        """
        self.add(CadMshFile(filepath=filepath))
        return self

    def add_nas_file(
        self,
        filepath: str,
    ) -> Self:
        """
        Adds a NAS file import to the project.
        Only one NAS file can exist in a project and it cannot coexist with other
        geometry elements.

        Parameters:
            filepath: Path to a local NAS file. The file will be uploaded automatically.

        Returns:
            The GeometryBuilder object.
        """
        self.add(CadNasFile(filepath=filepath))
        return self

    def build(
        self,
        print_logs: bool = False,
        refresh_delay_s: float = 1,
        on_error: OnError = OnError.IGNORE,
    ) -> Self:
        """Processes the geometry elements in the project and returns when the processing is complete.

        Parameters:
            print_logs: If True, print logs to the console.
            refresh_delay_s: Optional delay in seconds between checking the status of the job.
            on_error: Controls error handling after the job completes.
                ``OnError.IGNORE`` (default) — never raises; use :meth:`get_status` to check.
                ``OnError.RAISE`` — raises :exc:`JobError` unless status is ``SUCCESS``.
                ``OnError.STRICT`` — same as ``RAISE`` for geometry (no partial state is usable).

        Returns:
            The GeometryBuilder object.
        """
        self.run(print_logs=print_logs, refresh_delay_s=refresh_delay_s)
        status = self.get_status()
        if on_error is not OnError.IGNORE and status != Job.SUCCESS:
            raise JobError(
                f"Geometry building failed with status: {status}", status=status
            )
        return self

    def create_element(self, geometry: CadElement) -> CadElement:
        """
        Creates new geometry elements in the project.

        Parameters:
            geometry: A list of CAD geometry elements or a single CAD geometry element.

        Returns:
            A list of created CAD geometry elements or a single created CAD geometry element.
        """
        return self._create_element(geometry)

    def create_elements(self, geometries: List[CadElement]) -> List[CadElement]:
        """
        Creates new geometry elements in the project.

        Parameters:
            geometry: A list of CAD geometry elements or a single CAD geometry element.

        Returns:
            A list of created CAD geometry elements or a single created CAD geometry element.
        """
        return [self._create_element(geometry) for geometry in geometries]

    def get_elements(self) -> List[CadElement]:
        """
        Gets the list of CAD geometry elements in the project.

        Returns:
            A list of CAD geometry elements.
        """
        project_id = check_for_project_api_key(self._project_id)
        with get_api() as api:
            response_elements: List[rawapi.GeometryElement] = api.get_geometry_elements(
                authorization=get_auth(),
                project_id=project_id,
            )
            if response_elements is None or len(response_elements) == 0:
                return []
            elements = []
            for rawapi_element in response_elements:
                cad_element = self._convert_cad_element_from_rawapi(
                    rawapi_element, project_id
                )
                elements.append(cad_element)
            return elements

    def start(self, last_element_id: str | None = None) -> None:
        """
        Starts processing the geometry elements in the project.

        Parameters:
            last_element_id: Optional last geometry element id to process in the project.
            If not provided, all geometry elements in the project will be processed.
        """
        project_id = check_for_project_api_key(self._project_id)

        with get_api() as api:
            response = api.start_processing_geometry(
                authorization=get_auth(),
                project_id=project_id,
                last_element=last_element_id,
                body={},
            )
            job_id = response.job_id
            self._job = Job(project_id, job_id)

    def run(
        self,
        print_logs: bool = False,
        refresh_delay_s: float = 1,
        last_element_id: str | None = None,
    ) -> None:
        """
        Processes the geometry elements in the project and returns when the processing is complete.
        Use get_status() to check the status of the processing after running.

        Parameters:
            print_logs: If True, print logs to the console.
            refresh_delay_s: Optional delay in seconds between checking the status of the job.
            last_element_id: Optional last geometry element id to process in the project.
            If not provided, all geometry elements in the project will be processed.
        """
        self.start(last_element_id=last_element_id)
        while self.is_running(refresh_delay_s=refresh_delay_s):
            if print_logs:
                self.print_new_loglines()
        if print_logs:
            self.print_new_loglines()

    def abort(self) -> None:
        """
        Aborts the processing of the geometry.
        """
        return super().abort()

    def get_status(self) -> str | None:
        """
        Get the status of the processing of the geometry elements in the project.

        Returns:
            The status of the processing of the geometry elements in the project.
        """
        return super().get_status()

    def is_running(self, refresh_delay_s: float | None = None) -> bool:
        """
        Check if the processing of the geometry elements in the project is running.

        Parameters:
            refresh_delay_s: Optional delay in seconds between checking the status of the job.

        Returns:
            True if the processing of the geometry file is running, False otherwise.
        """
        return super().is_running(refresh_delay_s)

    def refresh_status(self, delay_s: float = 1) -> str | None:
        """
        Refresh the status of the processing of the geometry elements in the project.

        Parameters:
            delay_s: Optional delay in seconds between checking the status of the job.

        Returns:
            The status of the processing of the geometry file.
        """
        return super().refresh_status(delay_s)

    def get_logs(self, limit: int = 100) -> List[str]:
        """
        Get the logs of the processing of the geometry elements in the project.

        Parameters:
            limit: Optional maximum number of logs to return.

        Returns:
            A list of log messages.
        """
        return super().get_logs(limit)

    def print_new_loglines(self, file: TextIO = sys.stdout, limit: int = 100) -> None:
        """
        Print the new log lines of the processing of the geometry elements in the project.

        Parameters:
            file: Optional file to print the logs to.
            limit: Optional maximum number of logs to print.
        """
        return super().print_new_loglines(file, limit)

    def delete(self, geometry: CadElement | None = None) -> None:
        """
        Deletes a geometry element in the project,
        or all geometry elements if no geometry element is provided.

        Parameters:
            geometry: Optional geometry element to delete.
            If not provided, all geometry elements in the project will be deleted.
        """
        project_id = check_for_project_api_key(self._project_id)
        element_id = geometry.id if geometry is not None else None
        with get_api() as api:
            api.delete_geometry_elements(
                authorization=get_auth(),
                project_id=project_id,
                element_id=element_id,
            )

    def _convert_cad_element_from_rawapi(
        self,
        rawapi_element: rawapi.GeometryElement,
        project_id: str,
    ) -> CadElement:
        """
        Convert a rawapi GeometryElement to the appropriate CAD element type.

        Parameters:
            rawapi_element: The rawapi GeometryElement to convert.
            project_id: The project ID.
            cad_type: The CAD geometry type.

        Returns:
            The converted CAD element.

        Raises:
            ValueError: If the CAD geometry type is not supported.
        """
        cad_type = CadGeometryElement._determine_type(rawapi_element)
        cad_class = self._CAD_TYPE_TO_CLASS.get(cad_type)
        if cad_class is None:
            raise ValueError(f"Unsupported CAD geometry element type: {cad_type}")
        return cad_class._from_rawapi(rawapi_element, project_id)

    def _create_element(self, geometry: CadElement) -> CadElement:
        """
        Create a new geometry element in the given project from a CAD geometry element.
        """
        project_id = check_for_project_api_key(self._project_id)

        if geometry._is_file_import():
            geometry._initialize_file_attributes()

        if geometry.name is None:
            raise ValueError("CAD geometry element name is required")

        with get_api() as api:
            new_element_payload = geometry._to_rawapi_new_geometry_element()
            try:
                response = api.create_geometry_element(
                    authorization=get_auth(),
                    project_id=project_id,
                    new_geometry_element=new_element_payload,
                )
            except ApiException as e:
                message = getattr(e.data, "message", None) if e.data else None
                raise ValueError(message or str(e)) from e
            geometry._id = response.id
            geometry._project_id = project_id

        # For non-file imports, convert and return immediately
        if not geometry._is_file_import():
            return self._convert_cad_element_from_rawapi(response, project_id)

        # File imports require file upload
        geometry._id = response.id
        geometry._project_id = project_id
        geometry._upload()

        # For GDS2 file imports, wait for layer generation job to finish or building geometry fails
        if geometry.type == CadGeometryType.GDS2_FILE:
            with get_api() as api:
                # Fetch elements again because GDS2 layer generation job is created after
                # the file upload is completed
                response_elements: List[rawapi.GeometryElement] = (
                    api.get_geometry_elements(
                        authorization=get_auth(),
                        project_id=project_id,
                    )
                )
                if response_elements is None or len(response_elements) == 0:
                    raise ValueError("No geometry elements found")
                # Find the GDS2 element by id
                gds2_element = next(
                    (
                        element
                        for element in response_elements
                        if element.id == geometry.id
                    ),
                    None,
                )
                if gds2_element is None:
                    raise ValueError("GDS2 element not found")
                # Get GDS2 layer generation job id
                job_id = gds2_element.job_id

            # Wait for GDS2 layer generation job to finish
            if job_id is not None:
                job = Job(project_id, job_id)
                while job.is_running(refresh_delay_s=1):
                    pass
                if job.get_status() != Job.SUCCESS:
                    raise ValueError("Failed to read layers from GDSII file")
        return geometry

    def __str__(self) -> str:
        elements = self.get_elements()
        element_names = [element.name for element in elements]
        status = self.get_status()
        # Extract status name from enum (e.g., JobStatusType.SUCCESS -> SUCCESS)
        if status is None:
            status_str = "None"
        else:
            status_str = str(status)
            if "." in status_str:
                status_str = status_str.split(".")[-1]
        return f"GeometryBuilder(elements={element_names}, job_status={status_str})"
