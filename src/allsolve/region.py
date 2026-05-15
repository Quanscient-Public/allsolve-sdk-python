# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

import allsolve_rawapi as rawapi
from .util import prevent_deleted
from .api import get_api, get_auth, check_for_project_api_key

from enum import Enum
from typing import List, Sequence
from typing_extensions import Self


def _coerce_expression_vector(
    value: (
        rawapi.ExpressionVector
        | tuple[str | int | float, str | int | float, str | int | float]
    ),
) -> rawapi.ExpressionVector:
    if isinstance(value, rawapi.ExpressionVector):
        return value
    if isinstance(value, tuple) and len(value) == 3:
        x, y, z = value
        return rawapi.ExpressionVector(x=str(x), y=str(y), z=str(z))
    raise TypeError(
        "Expected ExpressionVector or a (x, y, z) tuple of str | int | float, "
        f"got {type(value).__name__!r}"
    )


def _coerce_expression_bounding_box(
    value: (
        rawapi.ExpressionBoundingBox
        | tuple[
            rawapi.ExpressionVector
            | tuple[str | int | float, str | int | float, str | int | float],
            rawapi.ExpressionVector
            | tuple[str | int | float, str | int | float, str | int | float],
        ]
    ),
) -> rawapi.ExpressionBoundingBox:
    if isinstance(value, rawapi.ExpressionBoundingBox):
        return value
    if isinstance(value, tuple) and len(value) == 2:
        min_corner, max_corner = value
        return rawapi.ExpressionBoundingBox(
            min=_coerce_expression_vector(min_corner),
            max=_coerce_expression_vector(max_corner),
        )
    raise TypeError(
        "Expected ExpressionBoundingBox or ((min_x, min_y, min_z), (max_x, max_y, max_z)), "
        f"got {type(value).__name__!r}"
    )


class RegionOperation(Enum):
    """
    Boolean / set operation used to combine geometry volumes into a region.

    Regions are defined by applying these operations to selected geometry
    entities via region rules.
    """

    UNION = rawapi.RegionRuleOperation.UNION
    """Combine all selected volumes."""

    INTERSECTION = rawapi.RegionRuleOperation.INTERSECTION
    """Keep only the overlapping volume."""

    DIFFERENCE = rawapi.RegionRuleOperation.DIFFERENCE
    """Subtract the second volume from the first."""

    SYMMETRIC_DIFFERENCE = rawapi.RegionRuleOperation.SYMMETRIC_DIFFERENCE
    """Keep volumes that belong to exactly one operand."""

    BOUNDARY = rawapi.RegionRuleOperation.BOUNDARY
    """Select the boundary surfaces of the operand volumes."""

    COMPLEMENT = rawapi.RegionRuleOperation.COMPLEMENT
    """Select everything outside the operand volumes."""


class Region:
    """
    Region of a geometry.
    """

    POINT = rawapi.EntityType.POINT
    CURVE = rawapi.EntityType.CURVE
    SURFACE = rawapi.EntityType.SURFACE
    VOLUME = rawapi.EntityType.VOLUME

    @classmethod
    def get_all(cls, project_id: str | None = None) -> List[Self]:
        """
        Get all regions in the project.

        Parameters:
            project_id: The ID of the project. Can be omitted if project API key is used.

        Returns:
            A list of Region objects.
        """
        project_id = check_for_project_api_key(project_id)
        with get_api() as api:
            return [
                cls(project_id, r)
                for r in api.get_regions(
                    authorization=get_auth(), project_id=project_id
                )
            ]

    @classmethod
    def create(
        cls,
        name: str,
        entity_type: rawapi.EntityType,
        entity_tags: List[int],
        region_rule: rawapi.RegionRule | None = None,
        project_id: str | None = None,
        *,
        shared: bool = True,
    ) -> Self:
        """
        Create a region in the project.

        Parameters:
            name: The name of the region.
            entity_type: The type of the entity.
            entity_tags: The tags of the entity.
            region_rule: Optional region rule of the region.
            project_id: The ID of the project. Can be omitted if project API key is used.
        Returns:
            The created region.
        """
        project_id = check_for_project_api_key(project_id)
        with get_api() as api:
            region = api.create_region(
                new_region=rawapi.NewRegion(
                    name=name,
                    entityType=entity_type,
                    entityTags=entity_tags,
                    regionRule=region_rule,
                    shared=shared,
                ),
                authorization=get_auth(),
                project_id=project_id,
            )
            return cls(project_id, region)

    def __init__(self, project_id: str, region: rawapi.Region) -> None:
        self._project_id = project_id
        self._region = region
        self._deleted = False

    @property
    @prevent_deleted
    def id(self) -> str:
        """Get the ID of the region."""
        return self._region.id

    @property
    @prevent_deleted
    def name(self) -> str:
        """Get the name of the region."""
        return self._region.name

    @property
    @prevent_deleted
    def entity_tags(self) -> List[int]:
        """Get the entity tags of the region."""
        return self._region.entity_tags

    @property
    @prevent_deleted
    def entity_type(self) -> rawapi.EntityType:
        """Get the entity type of the region."""
        return self._region.entity_type

    @property
    @prevent_deleted
    def shared(self) -> bool:
        """Is region a shared region within the project."""
        return self._region.shared

    @prevent_deleted
    def delete(self) -> None:
        """Delete the region."""
        with get_api() as api:
            api.delete_region(
                authorization=get_auth(), project_id=self._project_id, region_id=self.id
            )
            self._deleted = True

    def __str__(self) -> str:
        return f"Region(id={self.id}, name={self.name}, entityTags={self.entity_tags}, entityType={self.entity_type})"


class KeyValueAttributePath(rawapi.AttributePath):
    """
    KeyValueAttributePath.
    """

    def __init__(self, path: list[tuple[str, str]]) -> None:
        super().__init__(
            path=[
                rawapi.AttributePathItem(name=key, value=value) for key, value in path
            ]
        )


class RegionRule(Region):
    """
    RegionRule.
    """

    @classmethod
    def create(  # type: ignore[override]
        cls,
        name: str,
        entity_type: rawapi.EntityType,
        attribute_path: rawapi.AttributePath | list[tuple[str, str]] | None = None,
        bounding_box: (
            rawapi.ExpressionBoundingBox
            | tuple[
                rawapi.ExpressionVector
                | tuple[str | int | float, str | int | float, str | int | float],
                rawapi.ExpressionVector
                | tuple[str | int | float, str | int | float, str | int | float],
            ]
            | None
        ) = None,
        min_size: (
            rawapi.ExpressionVector
            | tuple[str | int | float, str | int | float, str | int | float]
            | None
        ) = None,
        max_size: (
            rawapi.ExpressionVector
            | tuple[str | int | float, str | int | float, str | int | float]
            | None
        ) = None,
        project_id: str | None = None,
        *,
        shared: bool = True,
    ) -> Self:
        """
        Create a region rule in the project.

        Parameters:
            name: The name of the region.
            entity_type: The type of the entity.
            attribute_path: The attribute path of the region.
                Can be a list of tuples (key, value).
                Example: [("LayerName", "Polysilicon")]
            bounding_box: The bounding box of the region. May be an ``ExpressionBoundingBox`` or
                ``(min_corner, max_corner)``; each corner may be an ``ExpressionVector`` or a
                length-3 ``(x, y, z)`` tuple of ``str``, ``int``, or ``float`` (coerced to
                expression strings for the API).
            min_size: The minimum size of the region. May be an ``ExpressionVector`` or a length-3
                ``(x, y, z)`` tuple of ``str``, ``int``, or ``float``.
            max_size: The maximum size of the region. Same accepted shapes as ``min_size``.
            project_id: The ID of the project. Can be omitted if project API key is used.

        Returns:
            The created region rule.
        """
        if attribute_path is not None and isinstance(attribute_path, list):
            attribute_path = KeyValueAttributePath(attribute_path)

        coerced_bounding_box = (
            _coerce_expression_bounding_box(bounding_box)
            if bounding_box is not None
            else None
        )
        coerced_min_size = (
            _coerce_expression_vector(min_size) if min_size is not None else None
        )
        coerced_max_size = (
            _coerce_expression_vector(max_size) if max_size is not None else None
        )

        return super().create(
            name=name,
            entity_type=entity_type,
            entity_tags=[],
            region_rule=rawapi.RegionRule(
                operation=rawapi.RegionRuleOperation.SELECTOR,
                sources=[],
                selector=rawapi.RegionSelector(
                    attributePath=attribute_path,
                    boundingBox=coerced_bounding_box,
                    minSize=coerced_min_size,
                    maxSize=coerced_max_size,
                ),
            ),
            project_id=project_id,
            shared=shared,
        )


class ComputedRegion(Region):
    """
    ComputedRegion.
    """

    @classmethod
    def create(  # type: ignore[override]
        cls,
        name: str,
        entity_type: rawapi.EntityType,
        operation: rawapi.RegionRuleOperation,
        source_regions: "Sequence[Region | str]",
        project_id: str | None = None,
        *,
        shared: bool = True,
    ) -> Self:
        """
        Create a computed region in the project.

        Parameters:
            name: The name of the region.
            entity_type: The type of the entity.
            operation: The operation to perform on the source regions.
            source_regions: The source regions (Region objects or ID strings).
            project_id: The ID of the project. Can be omitted if project API key is used.

        Returns:
            The created computed region.
        """
        source_region_ids = [r if isinstance(r, str) else r.id for r in source_regions]
        return super().create(
            name=name,
            entity_type=entity_type,
            entity_tags=[],
            region_rule=rawapi.RegionRule(
                operation=operation,
                sources=source_region_ids,
            ),
            project_id=project_id,
            shared=shared,
        )
