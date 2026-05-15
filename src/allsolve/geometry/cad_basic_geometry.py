# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from allsolve.geometry.cad_geometry_element import CadGeometryElement
from allsolve.geometry.cad_geometry_type import CadGeometryType
from allsolve.util import prevent_deleted
from allsolve.region import Region
import allsolve_rawapi as rawapi
from typing_extensions import Self

from .cad_utils import (
    create_distance,
    create_angle,
    create_vector,
    create_vector_2d,
    create_euler_angles,
    from_distance,
    from_angle,
    from_vector,
    from_euler_angles,
    from_vector_2d,
)


class CadPoint:
    """
    CadPoint is a class for representing a CAD point.
    """

    _tag: int | None
    _name: str | None

    @classmethod
    def from_region(cls, region: Region) -> Self:
        """Create a CadPoint from a Region. Region must contain exactly one point entity tag."""
        if region.entity_type != Region.POINT:
            raise ValueError("Region is not a point")
        if len(region.entity_tags) != 1:
            raise ValueError("Region must have exactly one entity tag")
        return cls(tag=region.entity_tags[0])

    @classmethod
    def _from_rawapi(cls, rawapi_point: rawapi.CadEntity | None) -> Self:
        if rawapi_point is None:
            return cls(tag=None, name=None)
        return cls(tag=rawapi_point.tag, name=rawapi_point.name)

    def __init__(self, tag: int | None = None, name: str | None = None):
        """Create a CadPoint from a point entity tag or point CAD name.
        Tag and name cannot be set at the same time.
        Tag can be created from a Region.
        """
        if tag is None and name is None:
            raise ValueError("Tag or name must be set")
        if tag is not None and name is not None:
            raise ValueError("Tag and name cannot be set at the same time")
        self._tag = tag
        self._name = name

    @property
    def tag(self) -> int | None:
        return self._tag

    @property
    def name(self) -> str | None:
        return self._name

    def _to_rawapi(self) -> rawapi.CadEntity:
        return rawapi.CadEntity(tag=self._tag, name=self._name)


class CadBox(CadGeometryElement):
    """
    Box represents a rectangular box geometry.
    """

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:

        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.geo_type is None:
            raise ValueError("CAD geometry element type is not set")
        if cad_element.geo_type.box is not None:
            box = cad_element.geo_type.box
            if cad_element.name is None:
                raise ValueError("Box name must be set")
            if box.position is None:
                raise ValueError("Box position must be set")
            if box.size is None:
                raise ValueError("Box size must be set")
            cad_object = cls(
                name=cad_element.name,
                position=from_vector(box.position),
                size=from_vector(box.size),
                rotation=from_euler_angles(box.rotation),
                alignment=box.alignment,
            )
            cls._initialize_from_rawapi(
                cad_object, rawapi_element, cad_element, project_id
            )
            return cad_object
        else:
            raise ValueError("Unsupported CAD geometry element type")

    def __init__(
        self,
        name: str,
        position: tuple[float | str, float | str, float | str],
        size: tuple[float | str, float | str, float | str],
        rotation: tuple[float | str, float | str, float | str] | None = None,
        alignment: rawapi.CadAlignment | None = None,
        enabled: str | bool | None = None,
    ) -> None:
        """
        Create a new box geometry.

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
        """
        super().__init__(name, enabled)
        self._position = position
        self._size = size
        self._rotation = rotation
        self._alignment = alignment

    def _require_box(self) -> rawapi.CadBox:
        cad_elem = self._require_cad_elem()
        if cad_elem.geo_type is None:
            raise ValueError("CAD geometry element type is not set")
        if cad_elem.geo_type.box is None:
            raise ValueError("Box is not set")
        return cad_elem.geo_type.box

    @property
    @prevent_deleted
    def position(
        self,
    ) -> tuple[float | str, float | str, float | str]:
        """Get the position of the box."""
        return self._position

    @position.setter
    @prevent_deleted
    def position(
        self,
        position: tuple[float | str, float | str, float | str],
    ) -> None:
        """Set the position of the box."""
        self._require_box().position = create_vector(position)

    @property
    @prevent_deleted
    def size(
        self,
    ) -> tuple[float | str, float | str, float | str]:
        """Get the size of the box."""
        return self._size

    @size.setter
    @prevent_deleted
    def size(
        self,
        size: tuple[float | str, float | str, float | str],
    ) -> None:
        """Set the size of the box."""
        self._require_box().size = create_vector(size)

    @property
    @prevent_deleted
    def rotation(self) -> tuple[float | str, float | str, float | str] | None:
        """Get the rotation of the box."""
        return self._rotation

    @rotation.setter
    @prevent_deleted
    def rotation(
        self, rotation: tuple[float | str, float | str, float | str] | None
    ) -> None:
        """Set the rotation of the box."""
        self._require_box().rotation = (
            create_euler_angles(rotation) if rotation is not None else None
        )

    @property
    @prevent_deleted
    def alignment(self) -> rawapi.CadAlignment | None:
        """Get the alignment of the box."""
        return self._alignment

    @alignment.setter
    @prevent_deleted
    def alignment(self, alignment: rawapi.CadAlignment | None) -> None:
        """Set the alignment of the box."""
        self._require_box().alignment = alignment

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.BOX

    @prevent_deleted
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:

        position_vec = create_vector(self._position)
        size_vec = create_vector(self._size)

        rotation_angles = None
        if self._rotation is not None:
            rotation_angles = create_euler_angles(self._rotation)

        cad_box = rawapi.CadBox(
            position=position_vec,
            size=size_vec,
            rotation=rotation_angles,
            alignment=self._alignment,
        )

        basic_geometry = rawapi.CadBasicGeometry(box=cad_box)

        cad_element = rawapi.CadGeometryElement(
            geoType=basic_geometry,
            name=self._name,
        )

        cad_element.name = self._name

        return cad_element

    def __str__(self) -> str:
        return (
            f"Box(position={self._position}, size={self._size}, "
            f"rotation={self._rotation}, alignment={self._alignment}, "
            f"name={self._name})"
        )


class CadCylinder(CadGeometryElement):
    """
    Cylinder represents a cylindrical geometry.
    """

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:

        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.geo_type is None:
            raise ValueError("CAD geometry element type is not set")
        if cad_element.geo_type.cylinder is not None:
            cylinder = cad_element.geo_type.cylinder
            if cad_element.name is None:
                raise ValueError("Cylinder name must be set")
            if cylinder.position is None:
                raise ValueError("Cylinder position must be set")
            if cylinder.axis is None:
                raise ValueError("Cylinder axis must be set")
            if cylinder.radius is None:
                raise ValueError("Cylinder radius must be set")

            inner_radius = None
            if cylinder.inner_radius is not None:
                inner_radius = from_distance(cylinder.inner_radius)

            angle1 = None
            if cylinder.angle1 is not None:
                angle1 = from_angle(cylinder.angle1)

            angle2 = None
            if cylinder.angle2 is not None:
                angle2 = from_angle(cylinder.angle2)

            rotation = None
            if cylinder.rotation is not None:
                rotation = from_euler_angles(cylinder.rotation)

            cad_object = cls(
                name=cad_element.name,
                position=from_vector(cylinder.position),
                axis=from_vector(cylinder.axis),
                radius=from_distance(cylinder.radius),
                inner_radius=inner_radius,
                angle1=angle1,
                angle2=angle2,
                rotation=rotation,
                alignment=cylinder.alignment,
            )
            cls._initialize_from_rawapi(
                cad_object, rawapi_element, cad_element, project_id
            )
            return cad_object
        else:
            raise ValueError("Unsupported CAD geometry element type")

    def __init__(
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
    ) -> None:
        """
        Create a new cylinder geometry.

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
        """
        super().__init__(name, enabled)
        self._position = position
        self._axis = axis
        self._radius = radius
        self._inner_radius = inner_radius
        self._angle1 = angle1
        self._angle2 = angle2
        self._rotation = rotation
        self._alignment = alignment

    def _require_cylinder(self) -> rawapi.CadCylinder:
        cad_elem = self._require_cad_elem()
        if cad_elem.geo_type is None:
            raise ValueError("CAD geometry element type is not set")
        if cad_elem.geo_type.cylinder is None:
            raise ValueError("Cylinder is not set")
        return cad_elem.geo_type.cylinder

    @property
    @prevent_deleted
    def position(
        self,
    ) -> tuple[float | str, float | str, float | str]:
        """Get the position of the cylinder."""
        return self._position

    @position.setter
    @prevent_deleted
    def position(
        self,
        position: tuple[float | str, float | str, float | str],
    ) -> None:
        """Set the position of the cylinder."""
        self._require_cylinder().position = create_vector(position)

    @property
    @prevent_deleted
    def axis(
        self,
    ) -> tuple[float | str, float | str, float | str]:
        """Get the axis of the cylinder."""
        return self._axis

    @axis.setter
    @prevent_deleted
    def axis(
        self,
        axis: tuple[float | str, float | str, float | str],
    ) -> None:
        """Set the axis of the cylinder."""
        self._require_cylinder().axis = create_vector(axis)

    @property
    @prevent_deleted
    def radius(self) -> float | str:
        """Get the radius of the cylinder."""
        return self._radius

    @radius.setter
    @prevent_deleted
    def radius(self, radius: float | str) -> None:
        """Set the radius of the cylinder."""
        self._require_cylinder().radius = create_distance(radius)

    @property
    @prevent_deleted
    def inner_radius(self) -> float | str | None:
        """Get the inner radius of the cylinder."""
        return self._inner_radius

    @inner_radius.setter
    @prevent_deleted
    def inner_radius(self, inner_radius: float | str | None) -> None:
        """Set the inner radius of the cylinder."""
        self._require_cylinder().inner_radius = (
            create_distance(inner_radius) if inner_radius is not None else None
        )

    @property
    @prevent_deleted
    def angle1(self) -> float | str | None:
        """Get the first angle of the cylinder."""
        return self._angle1

    @angle1.setter
    @prevent_deleted
    def angle1(self, angle1: float | str | None) -> None:
        """Set the first angle of the cylinder."""
        self._require_cylinder().angle1 = (
            create_angle(angle1) if angle1 is not None else None
        )

    @property
    @prevent_deleted
    def angle2(self) -> float | str | None:
        """Get the second angle of the cylinder."""
        return self._angle2

    @angle2.setter
    @prevent_deleted
    def angle2(self, angle2: float | str | None) -> None:
        """Set the second angle of the cylinder."""
        self._require_cylinder().angle2 = (
            create_angle(angle2) if angle2 is not None else None
        )

    @property
    @prevent_deleted
    def rotation(self) -> tuple[float | str, float | str, float | str] | None:
        """Get the rotation of the cylinder."""
        return self._rotation

    @rotation.setter
    @prevent_deleted
    def rotation(
        self, rotation: tuple[float | str, float | str, float | str] | None
    ) -> None:
        """Set the rotation of the cylinder."""
        self._require_cylinder().rotation = (
            create_euler_angles(rotation) if rotation is not None else None
        )

    @property
    @prevent_deleted
    def alignment(self) -> rawapi.CadAlignment | None:
        """Get the alignment of the cylinder."""
        return self._alignment

    @alignment.setter
    @prevent_deleted
    def alignment(self, alignment: rawapi.CadAlignment | None) -> None:
        """Set the alignment of the cylinder."""
        self._require_cylinder().alignment = alignment

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.CYLINDER

    @prevent_deleted
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:

        position_vec = create_vector(self._position)
        axis_vec = create_vector(self._axis)
        radius_dist = create_distance(self._radius)

        inner_radius_dist = None
        if self._inner_radius is not None:
            inner_radius_dist = create_distance(self._inner_radius)

        angle1_obj = None
        if self._angle1 is not None:
            angle1_obj = create_angle(self._angle1)

        angle2_obj = None
        if self._angle2 is not None:
            angle2_obj = create_angle(self._angle2)

        rotation_angles = None
        if self._rotation is not None:
            rotation_angles = create_euler_angles(self._rotation)

        cad_cylinder = rawapi.CadCylinder(
            position=position_vec,
            axis=axis_vec,
            radius=radius_dist,
            innerRadius=inner_radius_dist,
            angle1=angle1_obj,
            angle2=angle2_obj,
            rotation=rotation_angles,
            alignment=self._alignment,
        )

        basic_geometry = rawapi.CadBasicGeometry(cylinder=cad_cylinder)

        cad_element = rawapi.CadGeometryElement(
            geoType=basic_geometry,
            name=self._name,
        )

        return cad_element

    def __str__(self) -> str:
        return (
            f"Cylinder(position={self._position}, axis={self._axis}, "
            f"radius={self._radius}, inner_radius={self._inner_radius}, "
            f"angle1={self._angle1}, angle2={self._angle2}, "
            f"rotation={self._rotation}, alignment={self._alignment}, "
            f"name={self._name})"
        )


class CadSphere(CadGeometryElement):
    """
    Sphere represents a spherical geometry.
    """

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:

        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.geo_type is None:
            raise ValueError("CAD geometry element type is not set")
        if cad_element.geo_type.sphere is not None:
            sphere = cad_element.geo_type.sphere
            if cad_element.name is None:
                raise ValueError("Sphere name must be set")
            if sphere.position is None:
                raise ValueError("Sphere position must be set")
            if sphere.radius is None:
                raise ValueError("Sphere radius must be set")

            inner_radius = None
            if sphere.inner_radius is not None:
                inner_radius = from_distance(sphere.inner_radius)

            angle1 = None
            if sphere.angle1 is not None:
                angle1 = from_angle(sphere.angle1)

            angle2 = None
            if sphere.angle2 is not None:
                angle2 = from_angle(sphere.angle2)

            rotation = None
            if sphere.rotation is not None:
                rotation = from_euler_angles(sphere.rotation)

            cad_object = cls(
                name=cad_element.name,
                position=from_vector(sphere.position),
                radius=from_distance(sphere.radius),
                inner_radius=inner_radius,
                angle1=angle1,
                angle2=angle2,
                rotation=rotation,
            )
            cls._initialize_from_rawapi(
                cad_object, rawapi_element, cad_element, project_id
            )
            return cad_object
        else:
            raise ValueError("Unsupported CAD geometry element type")

    def __init__(
        self,
        name: str,
        position: tuple[float | str, float | str, float | str],
        radius: float | str,
        inner_radius: float | str | None = None,
        angle1: float | str | None = None,
        angle2: float | str | None = None,
        rotation: tuple[float | str, float | str, float | str] | None = None,
        enabled: str | bool | None = None,
    ) -> None:
        """
        Create a new sphere geometry.

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
        """
        super().__init__(name, enabled)
        self._position = position
        self._radius = radius
        self._inner_radius = inner_radius
        self._angle1 = angle1
        self._angle2 = angle2
        self._rotation = rotation

    def _require_sphere(self) -> rawapi.CadSphere:
        cad_elem = self._require_cad_elem()
        if cad_elem.geo_type is None:
            raise ValueError("CAD geometry element type is not set")
        if cad_elem.geo_type.sphere is None:
            raise ValueError("Sphere is not set")
        return cad_elem.geo_type.sphere

    @property
    @prevent_deleted
    def position(
        self,
    ) -> tuple[float | str, float | str, float | str]:
        """Get the position of the sphere."""
        return self._position

    @position.setter
    @prevent_deleted
    def position(
        self,
        position: tuple[float | str, float | str, float | str],
    ) -> None:
        """Set the position of the sphere."""
        self._require_sphere().position = create_vector(position)

    @property
    @prevent_deleted
    def radius(self) -> float | str:
        """Get the radius of the sphere."""
        return self._radius

    @radius.setter
    @prevent_deleted
    def radius(self, radius: float | str) -> None:
        """Set the radius of the sphere."""
        self._require_sphere().radius = create_distance(radius)

    @property
    @prevent_deleted
    def inner_radius(self) -> float | str | None:
        """Get the inner radius of the sphere."""
        return self._inner_radius

    @inner_radius.setter
    @prevent_deleted
    def inner_radius(self, inner_radius: float | str | None) -> None:
        """Set the inner radius of the sphere."""
        self._require_sphere().inner_radius = (
            create_distance(inner_radius) if inner_radius is not None else None
        )

    @property
    @prevent_deleted
    def angle1(self) -> float | str | None:
        """Get the first angle of the sphere."""
        return self._angle1

    @angle1.setter
    @prevent_deleted
    def angle1(self, angle1: float | str | None) -> None:
        """Set the first angle of the sphere."""
        self._require_sphere().angle1 = (
            create_angle(angle1) if angle1 is not None else None
        )

    @property
    @prevent_deleted
    def angle2(self) -> float | str | None:
        """Get the second angle of the sphere."""
        return self._angle2

    @angle2.setter
    @prevent_deleted
    def angle2(self, angle2: float | str | None) -> None:
        """Set the second angle of the sphere."""
        self._require_sphere().angle2 = (
            create_angle(angle2) if angle2 is not None else None
        )

    @property
    @prevent_deleted
    def rotation(self) -> tuple[float | str, float | str, float | str] | None:
        """Get the rotation of the sphere."""
        return self._rotation

    @rotation.setter
    @prevent_deleted
    def rotation(
        self, rotation: tuple[float | str, float | str, float | str] | None
    ) -> None:
        """Set the rotation of the sphere."""
        self._require_sphere().rotation = (
            create_euler_angles(rotation) if rotation is not None else None
        )

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.SPHERE

    @prevent_deleted
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:

        position_vec = create_vector(self._position)
        radius_dist = create_distance(self._radius)

        inner_radius_dist = None
        if self._inner_radius is not None:
            inner_radius_dist = create_distance(self._inner_radius)

        angle1_obj = None
        if self._angle1 is not None:
            angle1_obj = create_angle(self._angle1)

        angle2_obj = None
        if self._angle2 is not None:
            angle2_obj = create_angle(self._angle2)

        rotation_angles = None
        if self._rotation is not None:
            rotation_angles = create_euler_angles(self._rotation)

        cad_sphere = rawapi.CadSphere(
            position=position_vec,
            radius=radius_dist,
            innerRadius=inner_radius_dist,
            angle1=angle1_obj,
            angle2=angle2_obj,
            rotation=rotation_angles,
        )

        basic_geometry = rawapi.CadBasicGeometry(sphere=cad_sphere)

        cad_element = rawapi.CadGeometryElement(
            geoType=basic_geometry,
            name=self._name,
        )

        return cad_element

    def __str__(self) -> str:
        return (
            f"Sphere(position={self._position}, radius={self._radius}, "
            f"inner_radius={self._inner_radius}, angle1={self._angle1}, "
            f"angle2={self._angle2}, rotation={self._rotation}, "
            f"name={self._name})"
        )


class CadCone(CadGeometryElement):
    """
    Cone represents a conical geometry.
    """

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:

        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.geo_type is None:
            raise ValueError("CAD geometry element type is not set")
        if cad_element.geo_type.cone is not None:
            cone = cad_element.geo_type.cone
            if cad_element.name is None:
                raise ValueError("Cone name must be set")
            if cone.position is None:
                raise ValueError("Cone position must be set")
            if cone.axis is None:
                raise ValueError("Cone axis must be set")
            if cone.radius1 is None:
                raise ValueError("Cone radius1 must be set")
            if cone.radius2 is None:
                raise ValueError("Cone radius2 must be set")

            angle1 = None
            if cone.angle1 is not None:
                angle1 = from_angle(cone.angle1)

            angle2 = None
            if cone.angle2 is not None:
                angle2 = from_angle(cone.angle2)

            rotation = None
            if cone.rotation is not None:
                rotation = from_euler_angles(cone.rotation)

            cad_object = cls(
                name=cad_element.name,
                position=from_vector(cone.position),
                axis=from_vector(cone.axis),
                radius1=from_distance(cone.radius1),
                radius2=from_distance(cone.radius2),
                angle1=angle1,
                angle2=angle2,
                rotation=rotation,
                alignment=cone.alignment,
            )
            cls._initialize_from_rawapi(
                cad_object, rawapi_element, cad_element, project_id
            )
            return cad_object
        else:
            raise ValueError("Unsupported CAD geometry element type")

    def __init__(
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
    ) -> None:
        """
        Create a new cone geometry.

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
        """
        super().__init__(name, enabled)
        self._position = position
        self._axis = axis
        self._radius1 = radius1
        self._radius2 = radius2
        self._angle1 = angle1
        self._angle2 = angle2
        self._rotation = rotation
        self._alignment = alignment

    def _require_cone(self) -> rawapi.CadCone:
        cad_elem = self._require_cad_elem()
        if cad_elem.geo_type is None:
            raise ValueError("CAD geometry element type is not set")
        if cad_elem.geo_type.cone is None:
            raise ValueError("Cone is not set")
        return cad_elem.geo_type.cone

    @property
    @prevent_deleted
    def position(
        self,
    ) -> tuple[float | str, float | str, float | str]:
        """Get the position of the cone."""
        return self._position

    @position.setter
    @prevent_deleted
    def position(
        self,
        position: tuple[float | str, float | str, float | str],
    ) -> None:
        """Set the position of the cone."""
        self._require_cone().position = create_vector(position)

    @property
    @prevent_deleted
    def axis(
        self,
    ) -> tuple[float | str, float | str, float | str]:
        """Get the axis of the cone."""
        return self._axis

    @axis.setter
    @prevent_deleted
    def axis(
        self,
        axis: tuple[float | str, float | str, float | str],
    ) -> None:
        """Set the axis of the cone."""
        self._require_cone().axis = create_vector(axis)

    @property
    @prevent_deleted
    def radius1(self) -> float | str:
        """Get the base radius of the cone."""
        return self._radius1

    @radius1.setter
    @prevent_deleted
    def radius1(self, radius1: float | str) -> None:
        """Set the base radius of the cone."""
        self._require_cone().radius1 = create_distance(radius1)

    @property
    @prevent_deleted
    def radius2(self) -> float | str:
        """Get the top radius of the cone."""
        return self._radius2

    @radius2.setter
    @prevent_deleted
    def radius2(self, radius2: float | str) -> None:
        """Set the top radius of the cone."""
        self._require_cone().radius2 = create_distance(radius2)

    @property
    @prevent_deleted
    def angle1(self) -> float | str | None:
        """Get the first angle of the cone."""
        return self._angle1

    @angle1.setter
    @prevent_deleted
    def angle1(self, angle1: float | str | None) -> None:
        """Set the first angle of the cone."""
        self._require_cone().angle1 = (
            create_angle(angle1) if angle1 is not None else None
        )

    @property
    @prevent_deleted
    def angle2(self) -> float | str | None:
        """Get the second angle of the cone."""
        return self._angle2

    @angle2.setter
    @prevent_deleted
    def angle2(self, angle2: float | str | None) -> None:
        """Set the second angle of the cone."""
        self._require_cone().angle2 = (
            create_angle(angle2) if angle2 is not None else None
        )

    @property
    @prevent_deleted
    def rotation(self) -> tuple[float | str, float | str, float | str] | None:
        """Get the rotation of the cone."""
        return self._rotation

    @rotation.setter
    @prevent_deleted
    def rotation(
        self, rotation: tuple[float | str, float | str, float | str] | None
    ) -> None:
        """Set the rotation of the cone."""
        self._require_cone().rotation = (
            create_euler_angles(rotation) if rotation is not None else None
        )

    @property
    @prevent_deleted
    def alignment(self) -> rawapi.CadAlignment | None:
        """Get the alignment of the cone."""
        return self._alignment

    @alignment.setter
    @prevent_deleted
    def alignment(self, alignment: rawapi.CadAlignment | None) -> None:
        """Set the alignment of the cone."""
        self._require_cone().alignment = alignment

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.CONE

    @prevent_deleted
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:

        position_vec = create_vector(self._position)
        axis_vec = create_vector(self._axis)
        radius1_dist = create_distance(self._radius1)
        radius2_dist = create_distance(self._radius2)

        angle1_obj = None
        if self._angle1 is not None:
            angle1_obj = create_angle(self._angle1)

        angle2_obj = None
        if self._angle2 is not None:
            angle2_obj = create_angle(self._angle2)

        rotation_angles = None
        if self._rotation is not None:
            rotation_angles = create_euler_angles(self._rotation)

        cad_cone = rawapi.CadCone(
            position=position_vec,
            axis=axis_vec,
            radius1=radius1_dist,
            radius2=radius2_dist,
            angle1=angle1_obj,
            angle2=angle2_obj,
            rotation=rotation_angles,
            alignment=self._alignment,
        )

        basic_geometry = rawapi.CadBasicGeometry(cone=cad_cone)

        cad_element = rawapi.CadGeometryElement(
            geoType=basic_geometry,
            name=self._name,
        )

        return cad_element

    def __str__(self) -> str:
        return (
            f"Cone(position={self._position}, axis={self._axis}, "
            f"radius1={self._radius1}, radius2={self._radius2}, "
            f"angle1={self._angle1}, angle2={self._angle2}, "
            f"rotation={self._rotation}, alignment={self._alignment}, "
            f"name={self._name})"
        )


class CadTorus(CadGeometryElement):
    """
    Torus represents a toroidal geometry.
    """

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:

        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.geo_type is None:
            raise ValueError("CAD geometry element type is not set")
        if cad_element.geo_type.torus is not None:
            torus = cad_element.geo_type.torus
            if cad_element.name is None:
                raise ValueError("Torus name must be set")
            if torus.position is None:
                raise ValueError("Torus position must be set")
            if torus.radius1 is None:
                raise ValueError("Torus radius1 must be set")
            if torus.radius2 is None:
                raise ValueError("Torus radius2 must be set")

            inner_radius = None
            if torus.inner_radius is not None:
                inner_radius = from_distance(torus.inner_radius)

            angle1 = None
            if torus.angle1 is not None:
                angle1 = from_angle(torus.angle1)

            angle2 = None
            if torus.angle2 is not None:
                angle2 = from_angle(torus.angle2)

            rotation = None
            if torus.rotation is not None:
                rotation = from_euler_angles(torus.rotation)

            cad_object = cls(
                name=cad_element.name,
                position=from_vector(torus.position),
                radius1=from_distance(torus.radius1),
                radius2=from_distance(torus.radius2),
                inner_radius=inner_radius,
                angle1=angle1,
                angle2=angle2,
                rotation=rotation,
            )
            cls._initialize_from_rawapi(
                cad_object, rawapi_element, cad_element, project_id
            )
            return cad_object
        else:
            raise ValueError("Unsupported CAD geometry element type")

    def __init__(
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
    ) -> None:
        """
        Create a new torus geometry.

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
        """
        super().__init__(name, enabled)
        self._position = position
        self._radius1 = radius1
        self._radius2 = radius2
        self._inner_radius = inner_radius
        self._angle1 = angle1
        self._angle2 = angle2
        self._rotation = rotation

    def _require_torus(self) -> rawapi.CadTorus:
        cad_elem = self._require_cad_elem()
        if cad_elem.geo_type is None:
            raise ValueError("CAD geometry element type is not set")
        if cad_elem.geo_type.torus is None:
            raise ValueError("Torus is not set")
        return cad_elem.geo_type.torus

    @property
    @prevent_deleted
    def position(
        self,
    ) -> tuple[float | str, float | str, float | str]:
        """Get the position of the torus."""
        return self._position

    @position.setter
    @prevent_deleted
    def position(
        self,
        position: tuple[float | str, float | str, float | str],
    ) -> None:
        """Set the position of the torus."""
        self._require_torus().position = create_vector(position)

    @property
    @prevent_deleted
    def radius1(self) -> float | str:
        """Get the outer radius of the torus."""
        return self._radius1

    @radius1.setter
    @prevent_deleted
    def radius1(self, radius1: float | str) -> None:
        """Set the outer radius of the torus."""
        self._require_torus().radius1 = create_distance(radius1)

    @property
    @prevent_deleted
    def radius2(self) -> float | str:
        """Get the width of the torus ring."""
        return self._radius2

    @radius2.setter
    @prevent_deleted
    def radius2(self, radius2: float | str) -> None:
        """Set the width of the torus ring."""
        self._require_torus().radius2 = create_distance(radius2)

    @property
    @prevent_deleted
    def inner_radius(self) -> float | str | None:
        """Get the inner radius of the torus."""
        return self._inner_radius

    @inner_radius.setter
    @prevent_deleted
    def inner_radius(self, inner_radius: float | str | None) -> None:
        """Set the inner radius of the torus."""
        self._require_torus().inner_radius = (
            create_distance(inner_radius) if inner_radius is not None else None
        )

    @property
    @prevent_deleted
    def angle1(self) -> float | str | None:
        """Get the first angle of the torus."""
        return self._angle1

    @angle1.setter
    @prevent_deleted
    def angle1(self, angle1: float | str | None) -> None:
        """Set the first angle of the torus."""
        self._require_torus().angle1 = (
            create_angle(angle1) if angle1 is not None else None
        )

    @property
    @prevent_deleted
    def angle2(self) -> float | str | None:
        """Get the second angle of the torus."""
        return self._angle2

    @angle2.setter
    @prevent_deleted
    def angle2(self, angle2: float | str | None) -> None:
        """Set the second angle of the torus."""
        self._require_torus().angle2 = (
            create_angle(angle2) if angle2 is not None else None
        )

    @property
    @prevent_deleted
    def rotation(self) -> tuple[float | str, float | str, float | str] | None:
        """Get the rotation of the torus."""
        return self._rotation

    @rotation.setter
    @prevent_deleted
    def rotation(
        self, rotation: tuple[float | str, float | str, float | str] | None
    ) -> None:
        """Set the rotation of the torus."""
        self._require_torus().rotation = (
            create_euler_angles(rotation) if rotation is not None else None
        )

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.TORUS

    @prevent_deleted
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:

        position_vec = create_vector(self._position)
        radius1_dist = create_distance(self._radius1)
        radius2_dist = create_distance(self._radius2)

        inner_radius_dist = None
        if self._inner_radius is not None:
            inner_radius_dist = create_distance(self._inner_radius)

        angle1_obj = None
        if self._angle1 is not None:
            angle1_obj = create_angle(self._angle1)

        angle2_obj = None
        if self._angle2 is not None:
            angle2_obj = create_angle(self._angle2)

        rotation_angles = None
        if self._rotation is not None:
            rotation_angles = create_euler_angles(self._rotation)

        cad_torus = rawapi.CadTorus(
            position=position_vec,
            radius1=radius1_dist,
            radius2=radius2_dist,
            innerRadius=inner_radius_dist,
            angle1=angle1_obj,
            angle2=angle2_obj,
            rotation=rotation_angles,
        )

        basic_geometry = rawapi.CadBasicGeometry(torus=cad_torus)

        cad_element = rawapi.CadGeometryElement(
            geoType=basic_geometry,
            name=self._name,
        )

        return cad_element

    def __str__(self) -> str:
        return (
            f"Torus(position={self._position}, radius1={self._radius1}, "
            f"radius2={self._radius2}, inner_radius={self._inner_radius}, "
            f"angle1={self._angle1}, angle2={self._angle2}, "
            f"rotation={self._rotation}, name={self._name})"
        )


class CadSurfaceRectangle(CadGeometryElement):
    """
    CadSurfaceRectangle represents a surface rectangle geometry.
    """

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:

        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.geo_type is None:
            raise ValueError("CAD geometry element type is not set")
        if cad_element.geo_type.surface_rectangle is not None:
            surface_rect = cad_element.geo_type.surface_rectangle
            if cad_element.name is None:
                raise ValueError("Surface rectangle name must be set")
            if surface_rect.size is None:
                raise ValueError("Surface rectangle size must be set")
            if surface_rect.offset is None:
                raise ValueError("Surface rectangle offset must be set")

            cad_object = cls(
                name=cad_element.name,
                origin_point=CadPoint._from_rawapi(surface_rect.origin_point),
                main_axis_point=CadPoint._from_rawapi(surface_rect.main_axis_point),
                secondary_axis_point=CadPoint._from_rawapi(
                    surface_rect.secondary_axis_point
                ),
                size=from_vector_2d(surface_rect.size),
                offset=from_vector(surface_rect.offset),
            )
            cls._initialize_from_rawapi(
                cad_object, rawapi_element, cad_element, project_id
            )
            return cad_object
        else:
            raise ValueError("Unsupported CAD geometry element type")

    def __init__(
        self,
        name: str,
        size: tuple[float | str, float | str],
        offset: tuple[float | str, float | str, float | str],
        origin_point: CadPoint,
        main_axis_point: CadPoint,
        secondary_axis_point: CadPoint,
        enabled: str | bool | None = None,
    ) -> None:
        """
        Create a new surface rectangle geometry.

        Parameters:
            name: Name for the geometry element.
            size: The size of the rectangle as (x, y).
            offset: The offset from the origin point as (x, y, z).
            origin_point: Optional CAD entity reference for the origin point.
            main_axis_point: Optional CAD entity reference for the main axis point.
            secondary_axis_point: Optional CAD entity reference for the secondary axis point.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.
        """
        super().__init__(name, enabled)
        self._size = size
        self._offset = offset
        self._origin_point = origin_point
        self._main_axis_point = main_axis_point
        self._secondary_axis_point = secondary_axis_point

    def _require_surface_rectangle(self) -> rawapi.CadSurfaceRectangle:
        cad_elem = self._require_cad_elem()
        if cad_elem.geo_type is None:
            raise ValueError("CAD geometry element type is not set")
        if cad_elem.geo_type.surface_rectangle is None:
            raise ValueError("Surface rectangle is not set")
        return cad_elem.geo_type.surface_rectangle

    @property
    @prevent_deleted
    def size(
        self,
    ) -> tuple[float | str, float | str]:
        """Get the size of the surface rectangle."""
        return self._size

    @size.setter
    @prevent_deleted
    def size(
        self,
        size: tuple[float | str, float | str],
    ) -> None:
        """Set the size of the surface rectangle."""
        self._require_surface_rectangle().size = create_vector((size[0], size[1], 0))

    @property
    @prevent_deleted
    def offset(
        self,
    ) -> tuple[float | str, float | str, float | str]:
        """Get the offset of the surface rectangle."""
        return self._offset

    @offset.setter
    @prevent_deleted
    def offset(
        self,
        offset: tuple[float | str, float | str, float | str],
    ) -> None:
        """Set the offset of the surface rectangle."""
        self._require_surface_rectangle().offset = create_vector(offset)

    @property
    @prevent_deleted
    def origin_point(self) -> CadPoint:
        """Get the origin point CAD entity."""
        return self._origin_point

    @origin_point.setter
    @prevent_deleted
    def origin_point(self, origin_point: CadPoint) -> None:
        """Set the origin point CAD entity."""
        self._require_surface_rectangle().origin_point = origin_point._to_rawapi()

    @property
    @prevent_deleted
    def main_axis_point(self) -> CadPoint:
        """Get the main axis point CAD entity."""
        return self._main_axis_point

    @main_axis_point.setter
    @prevent_deleted
    def main_axis_point(self, main_axis_point: CadPoint) -> None:
        """Set the main axis point CAD entity."""
        self._require_surface_rectangle().main_axis_point = main_axis_point._to_rawapi()

    @property
    @prevent_deleted
    def secondary_axis_point(self) -> CadPoint:
        """Get the secondary axis point CAD entity."""
        return self._secondary_axis_point

    @secondary_axis_point.setter
    @prevent_deleted
    def secondary_axis_point(self, secondary_axis_point: CadPoint) -> None:
        """Set the secondary axis point CAD entity."""
        self._require_surface_rectangle().secondary_axis_point = (
            secondary_axis_point._to_rawapi()
        )

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.SURFACE_RECTANGLE

    @prevent_deleted
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:

        size_vec = create_vector((self._size[0], self._size[1], 0))
        offset_vec = create_vector(self._offset)

        cad_surface_rectangle = rawapi.CadSurfaceRectangle(
            originPoint=self._origin_point._to_rawapi(),
            mainAxisPoint=self._main_axis_point._to_rawapi(),
            secondaryAxisPoint=self._secondary_axis_point._to_rawapi(),
            size=size_vec,
            offset=offset_vec,
        )

        basic_geometry = rawapi.CadBasicGeometry(surfaceRectangle=cad_surface_rectangle)

        cad_element = rawapi.CadGeometryElement(
            geoType=basic_geometry,
            name=self._name,
        )

        return cad_element

    def __str__(self) -> str:
        return (
            f"SurfaceRectangle(size={self._size}, offset={self._offset}, "
            f"origin_point={self._origin_point}, "
            f"main_axis_point={self._main_axis_point}, "
            f"secondary_axis_point={self._secondary_axis_point}, "
            f"name={self._name})"
        )


class CadDisk(CadGeometryElement):
    """
    Disk represents a circular disk geometry.
    """

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:

        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.geo_type is None:
            raise ValueError("CAD geometry element type is not set")
        if cad_element.geo_type.disk is not None:
            disk = cad_element.geo_type.disk
            if cad_element.name is None:
                raise ValueError("Disk name must be set")
            if disk.position is None:
                raise ValueError("Disk position must be set")
            if disk.radius is None:
                raise ValueError("Disk radius must be set")

            inner_radius = None
            if disk.inner_radius is not None:
                inner_radius = from_distance(disk.inner_radius)

            angle1 = None
            if disk.angle1 is not None:
                angle1 = from_angle(disk.angle1)

            angle2 = None
            if disk.angle2 is not None:
                angle2 = from_angle(disk.angle2)

            rotation = None
            if disk.rotation is not None:
                rotation = from_euler_angles(disk.rotation)

            cad_object = cls(
                name=cad_element.name,
                position=from_vector_2d(disk.position),
                radius=from_distance(disk.radius),
                inner_radius=inner_radius,
                angle1=angle1,
                angle2=angle2,
                rotation=rotation,
            )
            cls._initialize_from_rawapi(
                cad_object, rawapi_element, cad_element, project_id
            )
            return cad_object
        else:
            raise ValueError("Unsupported CAD geometry element type")

    def __init__(
        self,
        name: str,
        position: tuple[float | str, float | str],
        radius: float | str,
        inner_radius: float | str | None = None,
        angle1: float | str | None = None,
        angle2: float | str | None = None,
        rotation: tuple[float | str, float | str, float | str] | None = None,
        enabled: str | bool | None = None,
    ) -> None:
        """
        Create a new disk geometry.

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
        """
        super().__init__(name, enabled)
        self._position = position
        self._radius = radius
        self._inner_radius = inner_radius
        self._angle1 = angle1
        self._angle2 = angle2
        self._rotation = rotation

    def _require_disk(self) -> rawapi.CadDisk:
        cad_elem = self._require_cad_elem()
        if cad_elem.geo_type is None:
            raise ValueError("CAD geometry element type is not set")
        if cad_elem.geo_type.disk is None:
            raise ValueError("Disk is not set")
        return cad_elem.geo_type.disk

    @property
    @prevent_deleted
    def position(
        self,
    ) -> tuple[float | str, float | str]:
        """Get the position of the disk."""
        return self._position

    @position.setter
    @prevent_deleted
    def position(
        self,
        position: tuple[float | str, float | str],
    ) -> None:
        """Set the position of the disk."""
        self._require_disk().position = create_vector_2d(position)

    @property
    @prevent_deleted
    def radius(self) -> float | str:
        """Get the radius of the disk."""
        return self._radius

    @radius.setter
    @prevent_deleted
    def radius(self, radius: float | str) -> None:
        """Set the radius of the disk."""
        self._require_disk().radius = create_distance(radius)

    @property
    @prevent_deleted
    def inner_radius(self) -> float | str | None:
        """Get the inner radius of the disk."""
        return self._inner_radius

    @inner_radius.setter
    @prevent_deleted
    def inner_radius(self, inner_radius: float | str | None) -> None:
        """Set the inner radius of the disk."""
        self._require_disk().inner_radius = (
            create_distance(inner_radius) if inner_radius is not None else None
        )

    @property
    @prevent_deleted
    def angle1(self) -> float | str | None:
        """Get the first angle of the disk."""
        return self._angle1

    @angle1.setter
    @prevent_deleted
    def angle1(self, angle1: float | str | None) -> None:
        """Set the first angle of the disk."""
        self._require_disk().angle1 = (
            create_angle(angle1) if angle1 is not None else None
        )

    @property
    @prevent_deleted
    def angle2(self) -> float | str | None:
        """Get the second angle of the disk."""
        return self._angle2

    @angle2.setter
    @prevent_deleted
    def angle2(self, angle2: float | str | None) -> None:
        """Set the second angle of the disk."""
        self._require_disk().angle2 = (
            create_angle(angle2) if angle2 is not None else None
        )

    @property
    @prevent_deleted
    def rotation(self) -> tuple[float | str, float | str, float | str] | None:
        """Get the rotation of the disk."""
        return self._rotation

    @rotation.setter
    @prevent_deleted
    def rotation(
        self, rotation: tuple[float | str, float | str, float | str] | None
    ) -> None:
        """Set the rotation of the disk."""
        self._require_disk().rotation = (
            create_euler_angles(rotation) if rotation is not None else None
        )

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.DISK

    @prevent_deleted
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:

        position_vec = create_vector_2d(self._position)
        radius_dist = create_distance(self._radius)

        inner_radius_dist = None
        if self._inner_radius is not None:
            inner_radius_dist = create_distance(self._inner_radius)

        angle1_obj = None
        if self._angle1 is not None:
            angle1_obj = create_angle(self._angle1)

        angle2_obj = None
        if self._angle2 is not None:
            angle2_obj = create_angle(self._angle2)

        rotation_angles = None
        if self._rotation is not None:
            rotation_angles = create_euler_angles(self._rotation)

        cad_disk = rawapi.CadDisk(
            position=position_vec,
            radius=radius_dist,
            innerRadius=inner_radius_dist,
            angle1=angle1_obj,
            angle2=angle2_obj,
            rotation=rotation_angles,
        )

        basic_geometry = rawapi.CadBasicGeometry(disk=cad_disk)

        cad_element = rawapi.CadGeometryElement(
            geoType=basic_geometry,
            name=self._name,
        )

        return cad_element

    def __str__(self) -> str:
        return (
            f"Disk(position={self._position}, radius={self._radius}, "
            f"inner_radius={self._inner_radius}, angle1={self._angle1}, "
            f"angle2={self._angle2}, rotation={self._rotation}, "
            f"name={self._name})"
        )


class CadRectangle(CadGeometryElement):
    """
    Rectangle represents a rectangular geometry.
    """

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:

        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.geo_type is None:
            raise ValueError("CAD geometry element type is not set")
        if cad_element.geo_type.rectangle is not None:
            rectangle = cad_element.geo_type.rectangle
            if cad_element.name is None:
                raise ValueError("Rectangle name must be set")
            if rectangle.position is None:
                raise ValueError("Rectangle position must be set")
            if rectangle.size is None:
                raise ValueError("Rectangle size must be set")

            rotation = None
            if rectangle.rotation is not None:
                rotation = from_euler_angles(rectangle.rotation)

            cad_object = cls(
                name=cad_element.name,
                position=from_vector_2d(rectangle.position),
                size=from_vector_2d(rectangle.size),
                rotation=rotation,
                alignment=rectangle.alignment,
            )
            cls._initialize_from_rawapi(
                cad_object, rawapi_element, cad_element, project_id
            )
            return cad_object
        else:
            raise ValueError("Unsupported CAD geometry element type")

    def __init__(
        self,
        name: str,
        position: tuple[float | str, float | str],
        size: tuple[float | str, float | str],
        rotation: tuple[float | str, float | str, float | str] | None = None,
        alignment: rawapi.CadAlignment | None = None,
        enabled: str | bool | None = None,
    ) -> None:
        """
        Create a new rectangle geometry.

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
        """
        super().__init__(name, enabled)
        self._position = position
        self._size = size
        self._rotation = rotation
        self._alignment = alignment

    def _require_rectangle(self) -> rawapi.CadRectangle:
        cad_elem = self._require_cad_elem()
        if cad_elem.geo_type is None:
            raise ValueError("CAD geometry element type is not set")
        if cad_elem.geo_type.rectangle is None:
            raise ValueError("Rectangle is not set")
        return cad_elem.geo_type.rectangle

    @property
    @prevent_deleted
    def position(
        self,
    ) -> tuple[float | str, float | str]:
        """Get the position of the rectangle."""
        return self._position

    @position.setter
    @prevent_deleted
    def position(
        self,
        position: tuple[float | str, float | str],
    ) -> None:
        """Set the position of the rectangle."""
        self._require_rectangle().position = create_vector_2d(position)

    @property
    @prevent_deleted
    def size(
        self,
    ) -> tuple[float | str, float | str]:
        """Get the size of the rectangle."""
        return self._size

    @size.setter
    @prevent_deleted
    def size(
        self,
        size: tuple[float | str, float | str],
    ) -> None:
        """Set the size of the rectangle."""
        self._require_rectangle().size = create_vector_2d(size)

    @property
    @prevent_deleted
    def rotation(self) -> tuple[float | str, float | str, float | str] | None:
        """Get the rotation of the rectangle."""
        return self._rotation

    @rotation.setter
    @prevent_deleted
    def rotation(
        self, rotation: tuple[float | str, float | str, float | str] | None
    ) -> None:
        """Set the rotation of the rectangle."""
        self._require_rectangle().rotation = (
            create_euler_angles(rotation) if rotation is not None else None
        )

    @property
    @prevent_deleted
    def alignment(self) -> rawapi.CadAlignment | None:
        """Get the alignment of the rectangle."""
        return self._alignment

    @alignment.setter
    @prevent_deleted
    def alignment(self, alignment: rawapi.CadAlignment | None) -> None:
        """Set the alignment of the rectangle."""
        self._require_rectangle().alignment = alignment

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.RECTANGLE

    @prevent_deleted
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:

        position_vec = create_vector_2d(self._position)
        size_vec = create_vector_2d(self._size)

        rotation_angles = None
        if self._rotation is not None:
            rotation_angles = create_euler_angles(self._rotation)

        cad_rectangle = rawapi.CadRectangle(
            position=position_vec,
            size=size_vec,
            rotation=rotation_angles,
            alignment=self._alignment,
        )

        basic_geometry = rawapi.CadBasicGeometry(rectangle=cad_rectangle)

        cad_element = rawapi.CadGeometryElement(
            geoType=basic_geometry,
            name=self._name,
        )

        return cad_element

    def __str__(self) -> str:
        return (
            f"Rectangle(position={self._position}, size={self._size}, "
            f"rotation={self._rotation}, alignment={self._alignment}, "
            f"name={self._name})"
        )
