# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

import copy
from enum import Enum
import pathlib
import sys
import warnings
from typing import List, TextIO
from typing_extensions import Self

from allsolve.override import VariableOverrides
from allsolve_rawapi.models.expression_vector import ExpressionVector
from allsolve_rawapi.models.extrusion_overlap_mode import ExtrusionOverlapMode
from allsolve_rawapi.models.mesh_extrusion_type import MeshExtrusionType

from .util import prevent_deleted, JobError
from .job_mixin import JobMixin
import allsolve_rawapi as rawapi
from .api import (
    check_for_project_api_key,
    get_allow_insecure_http,
    get_api,
    get_auth,
    get_http_session,
)
from .http_transfer import CONNECT_TIMEOUT_S, TRANSFER_TIMEOUT_S, validate_url_scheme
from .job import Job, OnError
from .region import Region


class ExtrusionLayerDefinition:
    """
    A layer definition for SlantedExtrusion, PathExtrusion and
    FlattenAndRebuildExtrusion.

    Args:
        relative_height: The relative height of the layer.
        sublayer_count: The number of sublayers in the layer.
    """

    def __init__(
        self,
        relative_height: str | int | float,
        sublayer_count: str | int,
    ):
        self.relative_height: str = str(relative_height)
        self.sublayer_count: str = str(sublayer_count)


class MeshRefinement:
    """
    A refinement for a mesh.

    Args:
        max_size: The maximum size of the refinement.
        region: The region to refine.
        tags: Optional geometry tags to refine. Either this or ``region`` must be provided but not both.
        entity_type: Optional entity type for tag-based refinement.
            (allsolve.Region.VOLUME, allsolve.Region.SURFACE, or allsolve.Region.CURVE).
            Required when using ``tags``.
    """

    def __init__(
        self,
        *,
        max_size: float | str,
        region: Region | None = None,
        tags: List[int] | None = None,
        entity_type: rawapi.EntityType | None = None,
    ):
        if region is not None and tags is not None:
            raise ValueError("Provide either 'region' or 'tags', not both")
        if region is None and tags is None:
            raise ValueError("Either 'region' or 'tags' must be provided")
        if tags is not None and entity_type is None:
            raise ValueError("'entity_type' is required when using 'tags'")
        self.region: Region | None = region
        self.max_size: str = str(max_size)
        self.tags: List[int] | None = tags
        self.entity_type: rawapi.EntityType | None = entity_type


class AutoTransfiniteGroup:
    """A single auto-transfinite meshing group.

    Pairs anisotropic target element sizes (in meters) with a target
    entity selection.

    Args:
        hx: Target element size along the X-axis (meters).
        hy: Target element size along the Y-axis (meters).
        hz: Target element size along the Z-axis (meters). Optional for 2D.
        region: A Region to target. Mutually exclusive with ``tags``.
        tags: Entity tags to target. Mutually exclusive with ``region``.
        entity_type: Required when using ``tags``
            (allsolve.Region.VOLUME, allsolve.Region.SURFACE, or allsolve.Region.CURVE).
    """

    def __init__(
        self,
        *,
        hx: float | int | str,
        hy: float | int | str,
        hz: float | int | str | None = None,
        region: Region | None = None,
        tags: List[int] | None = None,
        entity_type: rawapi.EntityType | None = None,
    ):
        if region is not None and tags is not None:
            raise ValueError("Provide either 'region' or 'tags', not both")
        if region is None and tags is None:
            raise ValueError("Either 'region' or 'tags' must be provided")
        if tags is not None and entity_type is None:
            raise ValueError("'entity_type' is required when using 'tags'")
        self.hx: str = str(hx)
        self.hy: str = str(hy)
        self.hz: str | None = str(hz) if hz is not None else None
        self.region: Region | None = region
        self.tags: List[int] | None = tags
        self.entity_type: rawapi.EntityType | None = entity_type


class SlantedExtrusion:
    """
    A slanted extrusion for a mesh.

    Args:
        volumes: The volume regions to extrude.
        from_surfaces: The surface regions to extrude from.
        to_surfaces: The surface regions to extrude to.
        layers: The layers of the extrusion.
        quadrangles: Whether to use quadrangles for the extrusion.
        volume_entity_ids: Optional geometry entity IDs for volumes to extrude.
            If provided, ``volumes`` must be ``None``.
        from_surface_entity_ids: Optional geometry entity IDs for from-surfaces to extrude from.
            If provided, ``from_surfaces`` must be ``None``.
        to_surface_entity_ids: Optional geometry entity IDs for to-surfaces to extrude to.
            If provided, ``to_surfaces`` must be ``None``.
    """

    def __init__(
        self,
        volumes: List[Region] | None = None,
        from_surfaces: List[Region] | None = None,
        to_surfaces: List[Region] | None = None,
        layers: List[ExtrusionLayerDefinition] | None = None,
        quadrangles: bool = False,
        volume_entity_ids: List[int] | None = None,
        from_surface_entity_ids: List[int] | None = None,
        to_surface_entity_ids: List[int] | None = None,
    ):
        if volumes is not None and volume_entity_ids is not None:
            raise ValueError(
                "Provide either 'volumes' or 'volume_entity_ids', not both"
            )
        if from_surfaces is not None and from_surface_entity_ids is not None:
            raise ValueError(
                "Provide either 'from_surfaces' or 'from_surface_entity_ids', not both"
            )
        if to_surfaces is not None and to_surface_entity_ids is not None:
            raise ValueError(
                "Provide either 'to_surfaces' or 'to_surface_entity_ids', not both"
            )
        self.volumes: List[Region] | None = volumes
        self.from_surfaces: List[Region] | None = from_surfaces
        self.to_surfaces: List[Region] | None = to_surfaces
        self.layers: List[ExtrusionLayerDefinition] = layers or []
        self.quadrangles: bool = quadrangles
        self.volume_entity_ids: List[int] | None = volume_entity_ids
        self.from_surface_entity_ids: List[int] | None = from_surface_entity_ids
        self.to_surface_entity_ids: List[int] | None = to_surface_entity_ids


class PathExtrusion:
    """
    A path extrusion for a mesh.

    Args:
        volumes: The volume regions to extrude.
        from_surfaces: The surface regions to extrude from.
        to_surfaces: The surface regions to extrude to.
        layers: The layers of the extrusion.
        quadrangles: Whether to use quadrangles for the extrusion.
        volume_entity_ids: Optional geometry entity IDs for volumes to extrude.
            If provided, ``volumes`` must be ``None``.
        from_surface_entity_ids: Optional geometry entity IDs for from-surfaces to extrude from.
            If provided, ``from_surfaces`` must be ``None``.
        to_surface_entity_ids: Optional geometry entity IDs for to-surfaces to extrude to.
            If provided, ``to_surfaces`` must be ``None``.
    """

    def __init__(
        self,
        volumes: List[Region] | None = None,
        from_surfaces: List[Region] | None = None,
        to_surfaces: List[Region] | None = None,
        layers: List[ExtrusionLayerDefinition] | None = None,
        quadrangles: bool = False,
        volume_entity_ids: List[int] | None = None,
        from_surface_entity_ids: List[int] | None = None,
        to_surface_entity_ids: List[int] | None = None,
    ):
        if volumes is not None and volume_entity_ids is not None:
            raise ValueError(
                "Provide either 'volumes' or 'volume_entity_ids', not both"
            )
        if from_surfaces is not None and from_surface_entity_ids is not None:
            raise ValueError(
                "Provide either 'from_surfaces' or 'from_surface_entity_ids', not both"
            )
        if to_surfaces is not None and to_surface_entity_ids is not None:
            raise ValueError(
                "Provide either 'to_surfaces' or 'to_surface_entity_ids', not both"
            )
        self.volumes: List[Region] | None = volumes
        self.from_surfaces: List[Region] | None = from_surfaces
        self.to_surfaces: List[Region] | None = to_surfaces
        self.layers: List[ExtrusionLayerDefinition] = layers or []
        self.quadrangles: bool = quadrangles
        self.volume_entity_ids: List[int] | None = volume_entity_ids
        self.from_surface_entity_ids: List[int] | None = from_surface_entity_ids
        self.to_surface_entity_ids: List[int] | None = to_surface_entity_ids


class FlattenAndRebuildExtrusion:
    """
    A flatten and rebuild extrusion for a mesh.

    Args:
        volumes: The volume regions to extrude.
        layers: The layers of the extrusion.
        quadrangles: Whether to use quadrangles for the extrusion.
        direction_vector: The direction vector for the extrusion.
        volume_entity_ids: Geometry entity IDs for volumes.
            If provided, ``volumes`` must be ``None``.
    """

    def __init__(
        self,
        volumes: List[Region] | None = None,
        layers: List[List[ExtrusionLayerDefinition]] | None = None,
        quadrangles: bool = False,
        direction_vector: ExpressionVector | None = None,
        volume_entity_ids: List[int] | None = None,
    ):
        if volumes is not None and volume_entity_ids is not None:
            raise ValueError(
                "Provide either 'volumes' or 'volume_entity_ids', not both"
            )
        self.volumes: List[Region] | None = volumes
        self.layers: List[List[ExtrusionLayerDefinition]] = layers or []
        self.quadrangles: bool = quadrangles
        self.direction_vector: ExpressionVector | None = direction_vector
        self.volume_entity_ids: List[int] | None = volume_entity_ids


class MeshExtrusion:
    """
    A simple extrusion for a mesh.

    Args:
        regions: The regions to extrude.
        sub_layer_counts: The number of sublayers for each layer.
        extrusion_overlap_mode: The overlap mode for the extrusion.
        volume_ids: Optional geometry volume IDs to extrude.
            If provided, ``regions`` must be ``None``.
    """

    def __init__(
        self,
        regions: List[Region] | None = None,
        sub_layer_counts: List[int | str] | None = None,
        extrusion_overlap_mode: ExtrusionOverlapMode = ExtrusionOverlapMode.PREVENT,
        volume_ids: List[int] | None = None,
    ):
        if regions is not None and volume_ids is not None:
            raise ValueError("Provide either 'regions' or 'volume_ids', not both")
        self.regions: List[Region] | None = regions
        self.sub_layer_counts: List[int | str] = sub_layer_counts or []
        self.extrusion_overlap_mode: ExtrusionOverlapMode = extrusion_overlap_mode
        self.type: MeshExtrusionType = MeshExtrusionType.COLLAPSE_AND_GROW
        self.volume_ids: List[int] | None = volume_ids


class MeshDensity(Enum):
    """
    Preset density level controlling how finely the geometry is meshed.

    Higher density produces more elements and better accuracy at the cost of
    longer meshing and solve times.  Use :attr:`USERDEFINED` to supply custom
    element-size parameters instead of a preset.
    """

    DEFAULT = rawapi.MeshDensity.DEFAULT
    """Platform default — a balanced trade-off between accuracy and speed."""

    COARSE = rawapi.MeshDensity.COARSE
    """Fewer, larger elements — faster meshing and solving."""

    FINE = rawapi.MeshDensity.FINE
    """More, smaller elements — higher accuracy."""

    USERDEFINED = rawapi.MeshDensity.USERDEFINED
    """Custom element sizes defined via mesh settings."""


class MeshQuality(Enum):
    """
    Enum for the quality of a mesh.
    @deprecated: Use MeshDensity instead.
    """

    DEFAULT = rawapi.MeshDensity.DEFAULT
    COARSE = rawapi.MeshDensity.COARSE
    FINE = rawapi.MeshDensity.FINE
    USERDEFINED = rawapi.MeshDensity.USERDEFINED


class MeshSettings:
    """
    Container for settings that can be configured when creating a mesh.
    """

    def __init__(
        self,
        name: str | None = None,
        density: MeshDensity | None = None,
        # Mesh quality is deprecated, use density instead
        quality: MeshQuality | None = None,
        node_type: str | None = None,
        max_run_time_minutes: int | None = None,
        use_mesh_refiner: bool = False,
        mesh_size_min: float | int | str | None = None,
        mesh_size_max: float | int | str | None = None,
        scale_factor: float | int | str | None = None,
        curvature_enhancement: float | int | str | None = None,
        curved_mesh: bool = False,
        target_width_to_height_ratio: float | int | str | None = None,
        refinements: List[MeshRefinement] | None = None,
        extrusion: MeshExtrusion | None = None,
        variable_overrides: List[VariableOverrides] | None = None,
        slanted_extrusions: List[SlantedExtrusion] | None = None,
        path_extrusions: List[PathExtrusion] | None = None,
        flatten_and_rebuild_extrusions: List[FlattenAndRebuildExtrusion] | None = None,
        auto_transfinite: List[AutoTransfiniteGroup] | None = None,
    ):
        self.name: str | None = name
        self.quality: rawapi.MeshDensity = (
            quality.value if quality is not None else rawapi.MeshDensity.DEFAULT
        )
        self.density: rawapi.MeshDensity = (
            density.value if density is not None else self.quality
        )
        self.max_run_time_minutes: int | None = max_run_time_minutes
        self.node_type: str | None = node_type
        self.parameters: rawapi.MeshParameters | None = None
        self.support_data: rawapi.MeshSupportData | None = None
        self.refinements: List[MeshRefinement] | None = refinements
        self.extrusion: MeshExtrusion | None = extrusion
        self.variable_overrides: List[VariableOverrides] | None = variable_overrides
        self.slanted_extrusions: List[SlantedExtrusion] | None = slanted_extrusions
        self.path_extrusions: List[PathExtrusion] | None = path_extrusions
        self.flatten_and_rebuild_extrusions: List[FlattenAndRebuildExtrusion] | None = (
            flatten_and_rebuild_extrusions
        )
        self.auto_transfinite: List[AutoTransfiniteGroup] | None = auto_transfinite

        if (
            use_mesh_refiner is True
            or mesh_size_min is not None
            or mesh_size_max is not None
            or scale_factor is not None
            or curvature_enhancement is not None
            or curved_mesh is True
            or target_width_to_height_ratio is not None
            or (refinements is not None and len(refinements) > 0)
            or extrusion is not None
            or slanted_extrusions is not None
            or path_extrusions is not None
            or flatten_and_rebuild_extrusions is not None
            or (auto_transfinite is not None and len(auto_transfinite) > 0)
        ):
            self.density = rawapi.MeshDensity.USERDEFINED
            self.parameters = rawapi.MeshParameters(
                meshAlgorithm=(
                    rawapi.MeshAlgorithm.MESH_MINUS_REFINER
                    if use_mesh_refiner
                    else rawapi.MeshAlgorithm.GMSH
                ),
                minSizeFactor=None,
                maxSizeFactor=None,
                scaleFactor=str(scale_factor) if scale_factor is not None else None,
                curvatureEnhancement=(
                    str(curvature_enhancement)
                    if curvature_enhancement is not None
                    else None
                ),
                targetWidthToHeightRatio=(
                    str(target_width_to_height_ratio)
                    if target_width_to_height_ratio is not None
                    else None
                ),
                meshSizeMin=str(mesh_size_min) if mesh_size_min is not None else None,
                meshSizeMax=str(mesh_size_max) if mesh_size_max is not None else None,
                curvedMesh=curved_mesh,
                selectiveRefinement=None,
                structuredMeshing=None,
                meshExtrusion=None,
            )

        self._parse_refinements()
        self._parse_extrusion()
        self._parse_simple_extrusion()
        self._parse_auto_transfinite()

    @staticmethod
    def _build_entity_selection(
        regions: List[Region] | None,
        entity_ids: List[int] | None,
    ) -> rawapi.EntitySelection:
        """Build an EntitySelection from either region objects or raw entity IDs."""
        return rawapi.EntitySelection(
            regionIds=[r.id for r in regions] if regions is not None else None,
            entityIds=entity_ids,
        )

    def _parse_refinements(self):
        if self.refinements is None or len(self.refinements) == 0:
            return
        if self.parameters is None:
            self.parameters = rawapi.MeshParameters()
        if self.parameters.selective_refinement is None:
            self.parameters.selective_refinement = rawapi.SelectiveMeshRefinement()
        for refinement in self.refinements:
            if refinement.tags is not None:
                refinement_item = rawapi.SelectiveMeshRefinementItem(
                    tags=refinement.tags,
                    absoluteRefinement=refinement.max_size,
                )
                entity_type = refinement.entity_type
            elif refinement.region is not None:
                refinement_item = rawapi.SelectiveMeshRefinementItem(
                    regions=[refinement.region.id],
                    absoluteRefinement=refinement.max_size,
                )
                entity_type = refinement.region.entity_type
            else:
                raise ValueError("Either 'tags' or 'region' must be provided")

            if entity_type == rawapi.EntityType.VOLUME:
                if self.parameters.selective_refinement.volumes is None:
                    self.parameters.selective_refinement.volumes = [refinement_item]
                else:
                    self.parameters.selective_refinement.volumes.append(refinement_item)
            elif entity_type == rawapi.EntityType.SURFACE:
                if self.parameters.selective_refinement.surfaces is None:
                    self.parameters.selective_refinement.surfaces = [refinement_item]
                else:
                    self.parameters.selective_refinement.surfaces.append(
                        refinement_item
                    )
            elif entity_type == rawapi.EntityType.CURVE:
                if self.parameters.selective_refinement.curves is None:
                    self.parameters.selective_refinement.curves = [refinement_item]
                else:
                    self.parameters.selective_refinement.curves.append(refinement_item)

    def _parse_simple_extrusion(self):
        if self.extrusion is None:
            return
        if self.parameters is None:
            self.parameters = rawapi.MeshParameters()
        if self.parameters.mesh_extrusion is None:
            self.parameters.mesh_extrusion = rawapi.MeshExtrusion(
                extrusionOverlapMode=self.extrusion.extrusion_overlap_mode,
                volumeRegions=(
                    [region.id for region in self.extrusion.regions]
                    if self.extrusion.regions is not None
                    else None
                ),
                volumeIds=self.extrusion.volume_ids,
                sublayers=[
                    str(sub_layer_count)
                    for sub_layer_count in self.extrusion.sub_layer_counts
                ],
                type=self.extrusion.type,
            )

    def _parse_extrusion(self) -> None:
        if (
            (self.slanted_extrusions is None or len(self.slanted_extrusions) == 0)
            and (self.path_extrusions is None or len(self.path_extrusions) == 0)
            and (
                self.flatten_and_rebuild_extrusions is None
                or len(self.flatten_and_rebuild_extrusions) == 0
            )
        ):
            return
        if self.parameters is None:
            self.parameters = rawapi.MeshParameters()
        if self.parameters.structured_mesh_definitions is None:
            self.parameters.structured_mesh_definitions = (
                rawapi.StructuredMeshDefinitions()
            )
        if self.slanted_extrusions is not None:
            slanted_extrusions: List[rawapi.SlantedExtrusion] = []
            for slanted_extrusion in self.slanted_extrusions:
                parsed_slanted_extrusion = rawapi.SlantedExtrusion(
                    toSurfaces=self._build_entity_selection(
                        slanted_extrusion.to_surfaces,
                        slanted_extrusion.to_surface_entity_ids,
                    ),
                    fromSurfaces=self._build_entity_selection(
                        slanted_extrusion.from_surfaces,
                        slanted_extrusion.from_surface_entity_ids,
                    ),
                    layers=[
                        rawapi.ExtrusionLayerDefinition(
                            sublayerCount=str(layer.sublayer_count),
                            relativeHeight=str(layer.relative_height),
                        )
                        for layer in slanted_extrusion.layers
                    ],
                    quadrangles=slanted_extrusion.quadrangles,
                    volumes=self._build_entity_selection(
                        slanted_extrusion.volumes,
                        slanted_extrusion.volume_entity_ids,
                    ),
                )
                slanted_extrusions.append(parsed_slanted_extrusion)
            self.parameters.structured_mesh_definitions.slanted_extrusions = (
                slanted_extrusions
            )
        if self.path_extrusions is not None:
            path_extrusions: List[rawapi.PathExtrusion] = []
            for path_extrusion in self.path_extrusions:
                parsed_path_extrusion = rawapi.PathExtrusion(
                    toSurfaces=self._build_entity_selection(
                        path_extrusion.to_surfaces,
                        path_extrusion.to_surface_entity_ids,
                    ),
                    fromSurfaces=self._build_entity_selection(
                        path_extrusion.from_surfaces,
                        path_extrusion.from_surface_entity_ids,
                    ),
                    layers=[
                        rawapi.ExtrusionLayerDefinition(
                            sublayerCount=str(layer.sublayer_count),
                            relativeHeight=str(layer.relative_height),
                        )
                        for layer in path_extrusion.layers
                    ],
                    quadrangles=path_extrusion.quadrangles,
                    volumes=self._build_entity_selection(
                        path_extrusion.volumes,
                        path_extrusion.volume_entity_ids,
                    ),
                )
                path_extrusions.append(parsed_path_extrusion)
            self.parameters.structured_mesh_definitions.path_extrusions = (
                path_extrusions
            )

        if self.flatten_and_rebuild_extrusions is not None:
            flatten_and_rebuild_extrusions: List[rawapi.FlattenAndRebuildExtrusion] = []
            for flatten_and_rebuild_extrusion in self.flatten_and_rebuild_extrusions:
                layers = []
                for layer in flatten_and_rebuild_extrusion.layers:
                    sublayers = []
                    for sublayer in layer:
                        if sublayer is None:
                            continue
                        sublayers.append(
                            rawapi.ExtrusionLayerDefinition(
                                sublayerCount=str(sublayer.sublayer_count),
                                relativeHeight=str(sublayer.relative_height),
                            )
                        )
                    if len(sublayers) > 0:
                        layers.append(sublayers)

                parsed_flatten_and_rebuild_extrusion = (
                    rawapi.FlattenAndRebuildExtrusion(
                        volumes=self._build_entity_selection(
                            flatten_and_rebuild_extrusion.volumes,
                            flatten_and_rebuild_extrusion.volume_entity_ids,
                        ),
                        layers=layers,
                        quadrangles=flatten_and_rebuild_extrusion.quadrangles,
                        directionVector=flatten_and_rebuild_extrusion.direction_vector,
                    )
                )
                flatten_and_rebuild_extrusions.append(
                    parsed_flatten_and_rebuild_extrusion
                )
            self.parameters.structured_mesh_definitions.flatten_and_rebuild_extrusions = (
                flatten_and_rebuild_extrusions
            )

    def _parse_auto_transfinite(self) -> None:
        if self.auto_transfinite is None or len(self.auto_transfinite) == 0:
            return
        if self.parameters is None:
            self.parameters = rawapi.MeshParameters()

        entries: List[rawapi.AutoTransfiniteEntry] = []
        for group in self.auto_transfinite:
            element_sizes = rawapi.AutoTransfiniteElementSizes(
                hx=group.hx,
                hy=group.hy,
                hz=group.hz,
            )

            if group.tags is not None:
                target = rawapi.EntitySelection(entityIds=group.tags)
                entity_type = group.entity_type
            elif group.region is not None:
                target = rawapi.EntitySelection(regionIds=[group.region.id])
                entity_type = group.region.entity_type
            else:
                raise ValueError("Either 'region' or 'tags' must be provided")

            if entity_type is None:
                raise ValueError(
                    "'entity_type' must be provided for auto_transfinite entries"
                )

            entries.append(
                rawapi.AutoTransfiniteEntry(
                    elementSizes=element_sizes,
                    target=target,
                    entityType=entity_type,
                )
            )

        self.parameters.auto_transfinite_meshing = entries


class _MockJob(Job):
    """
    A Job implementation that never queries the backend.

    Used when the backend reports that meshing is not needed (no-op),
    but callers still expect a successful job state.
    """

    def __init__(self, project_id: str, status: str, status_reason: str = "") -> None:
        super().__init__(project_id=project_id, job_id="")
        self._static_status = status
        self._static_status_reason = status_reason

    def abort(self) -> None:
        return

    def get_status(self) -> str | None:
        return self._static_status

    def refresh_status(self, delay_s: float = 0) -> str | None:
        return self._static_status

    def is_running(self, refresh_delay_s: float | None = None) -> bool:
        return False

    def get_logs(self, limit: int = 100) -> List[str]:
        return []

    def print_new_loglines(self, file: TextIO = sys.stdout, limit: int = 100) -> None:
        return

    def get_status_reason(self) -> str | None:
        return self._static_status_reason


class MeshInstance(JobMixin):
    """A single mesh instance bound to one variable override set.

    Returned by :meth:`Mesh.get_override` and :meth:`Mesh.create_override`.
    Used for controlling the meshing job lifecycle for the mesh instance.
    """

    def __init__(
        self,
        mesh: "Mesh",
        raw_instance: rawapi.MeshInstance,
    ) -> None:
        self._mesh: "Mesh" = mesh
        self._raw_instance: rawapi.MeshInstance = raw_instance
        self._job: Job | None = None
        if raw_instance.meshing_job is not None:
            raw_job = raw_instance.meshing_job
            job = Job(mesh._project_id, raw_job.id)
            job._job_status = rawapi.JobStatus(
                jobId=raw_job.id,
                status=raw_job.status,
                statusReason=raw_job.status_reason,
                progress=raw_job.progress,
            )
            self._job = job

    def __str__(self) -> str:
        return (
            f"MeshInstance(id={self.id!r}, "
            f"variable_override_id={self.variable_override_id!r})"
        )

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def id(self) -> str:
        """The backend mesh-instance ID."""
        return self._raw_instance.id

    @property
    def variable_override_id(self) -> str | None:
        """The variable-overrides set ID, or ``None`` for the default instance."""
        return self._raw_instance.override_set

    def start(self) -> None:
        """Start meshing for this instance."""
        self._mesh.save()
        project_id = check_for_project_api_key(self._mesh._project_id)

        with get_api() as api:
            try:
                response = api.start_meshing(
                    authorization=get_auth(),
                    project_id=project_id,
                    mesh_id=self._mesh._mesh.id,
                    mesh_instance_id=self._raw_instance.id,
                    body={},
                )
            except Exception as e:
                if getattr(e, "status", None) == 304:
                    self._job = _MockJob(
                        project_id=self._mesh._project_id,
                        status=Job.SUCCESS,
                        status_reason="mesh_not_needed",
                    )
                    return
                raise

            self._job = Job(self._mesh._project_id, response.id)

            self._mesh._mesh = api.get_mesh(
                authorization=get_auth(),
                project_id=self._mesh._project_id,
                mesh_id=self._mesh._mesh.id,
            )

    def run(
        self,
        print_logs: bool = False,
        refresh_delay_s: float = 1,
        on_error: OnError = OnError.IGNORE,
    ) -> None:
        """Process the mesh instance and return when the processing is complete.

        Parameters:
            print_logs: If True, print logs to the console.
            refresh_delay_s: Delay in seconds between status checks.
            on_error: Controls error handling after the job completes.
                ``OnError.IGNORE`` (default) — never raises; use :meth:`get_status` to check.
                ``OnError.RAISE`` — raises :exc:`JobError` unless status is ``SUCCESS`` or
                ``PARTIAL_SUCCESS``.
                ``OnError.STRICT`` — raises :exc:`JobError` unless status is exactly ``SUCCESS``.
        """
        self.start()
        while self.is_running(refresh_delay_s=refresh_delay_s):
            if print_logs:
                self.print_new_loglines()
        if print_logs:
            self.print_new_loglines()
        status = self.get_status()
        if on_error is OnError.STRICT and status != Job.SUCCESS:
            raise JobError(
                f"Mesh '{self._mesh.name}' instance {self.id} "
                f"processing failed with status: {status}",
                status=status,
            )
        elif on_error is OnError.RAISE and status not in (
            Job.SUCCESS,
            Job.PARTIAL_SUCCESS,
        ):
            raise JobError(
                f"Mesh '{self._mesh.name}' instance {self.id} "
                f"processing failed with status: {status}",
                status=status,
            )

    def save_mesh_file(
        self, output_dir: str = "./", filename: str = "mesh.msh"
    ) -> None:
        """Save this instance's mesh file to local disk.

        Parameters:
            output_dir: Directory to save to.
            filename: File name to save as.
        """
        self._mesh._save_mesh_file_for_instance(
            variable_overrides_id=self.variable_override_id,
            output_dir=output_dir,
            filename=filename,
        )


class Mesh(JobMixin):
    """Mesh of a project geometry.

    The default (no variable overrides) mesh instance is managed directly
    on this object via :meth:`start`, :meth:`run`, :meth:`get_status`, etc.

    For variable-override instances, use :meth:`create_override` /
    :meth:`get_override` which return :class:`MeshInstance` objects that
    carry their own job lifecycle.

    Example::

        # Run the default mesh instance
        mesh = project.create_mesh()
        mesh.run()
        print(mesh.get_status())

        # Run a mesh with custom settings and refinement
        mesh = project.create_mesh(
            mesh_settings=allsolve.MeshSettings(
                mesh_size_max=0.2,
                refinements=[
                    allsolve.MeshRefinement(region=target_region, max_size=0.1),
                ],
            )
        )

        # Run a mesh with variable overrides
        mesh = project.create_mesh()
        instance = mesh.create_override(variable_override=my_variable_override)
        instance.run()
        print(instance.get_status())
    """

    @staticmethod
    def _read_entity_selection(
        selection: rawapi.EntitySelection,
        project_regions: List[Region],
    ) -> tuple[List[Region] | None, List[int] | None]:
        """Read an EntitySelection back into SDK types.

        Returns (regions, entity_ids) — at most one will be non-None.
        """
        if selection.region_ids is not None:
            regions = [
                region
                for region in project_regions
                if region.id in selection.region_ids
            ]
            return regions, None
        if selection.entity_ids is not None:
            return None, selection.entity_ids
        return None, None

    @staticmethod
    def _resolve_variable_overrides_id(
        variable_overrides: "VariableOverrides | str | None",
    ) -> str | None:
        if variable_overrides is None or isinstance(variable_overrides, str):
            return variable_overrides
        return variable_overrides.id

    @classmethod
    def create(cls, project_id: str, mesh_settings: MeshSettings | None = None) -> Self:
        """
        Create a new mesh in the project.

        Parameters:
            project_id: The ID of the project to create the mesh in.
            mesh_settings: Optional settings for the mesh.

        Returns:
            The created mesh.
        """
        project_id = check_for_project_api_key(project_id)

        mesh = None
        with get_api() as api:
            mesh_data = api.create_mesh(
                authorization=get_auth(),
                project_id=project_id,
                body={},
            )
            mesh = cls(project_id, mesh_data)
        if mesh_settings is not None:
            mesh_update = mesh._current_uncommitted_update()
            if mesh_settings.name is not None:
                mesh_update.name = mesh_settings.name
            # TODO: Quality is deprecated, use density instead
            if mesh_settings.quality is not None:
                mesh_update.density = mesh_settings.quality
            if mesh_settings.density is not None:
                mesh_update.density = mesh_settings.density
            if mesh_settings.max_run_time_minutes is not None:
                mesh_update.max_run_time_minutes = mesh_settings.max_run_time_minutes
            if mesh_settings.node_type is not None:
                mesh_update.node_type = mesh_settings.node_type
            if mesh_settings.parameters is not None:
                mesh_update.parameters = copy.deepcopy(mesh_settings.parameters)
            if mesh_settings.support_data is not None:
                mesh_update.support_data = copy.deepcopy(mesh_settings.support_data)
            if mesh_settings.variable_overrides is not None:
                mesh_update.override_sets = [
                    override_set.id for override_set in mesh_settings.variable_overrides
                ]
            mesh.save()

        return mesh

    @classmethod
    def get(cls, mesh_id: str, project_id: str | None = None) -> Self:
        """
        Get a mesh by its ID.

        Parameters:
            mesh_id: The ID of the mesh.
            project_id: The ID of the project. Can be omitted if project API key is used.

        Returns:
            The mesh.
        """
        project_id = check_for_project_api_key(project_id)
        with get_api() as api:
            mesh = api.get_mesh(
                authorization=get_auth(),
                project_id=project_id,
                mesh_id=mesh_id,
            )
            return cls(project_id, mesh)

    @classmethod
    def get_all(cls, project_id: str | None = None) -> List[Self]:
        """
        Get all meshes in the project.

        Parameters:
            project_id: The ID of the project. Can be omitted if project API key is used.

        Returns:
            A list of Mesh objects.
        """
        project_id = check_for_project_api_key(project_id)

        with get_api() as api:
            response = api.get_meshes(
                authorization=get_auth(),
                project_id=project_id,
            )
            return [
                cls(
                    project_id,
                    mesh,
                )
                for mesh in response
            ]

    def __init__(
        self,
        project_id: str,
        mesh: rawapi.Mesh,
    ):
        self._project_id: str = project_id
        self._deleted: bool = False
        self._job: Job | None = None
        self._mesh: rawapi.Mesh = mesh
        self._uncommitted_update: rawapi.MeshUpdate | None = None
        self._populate_default_job()

    def __str__(self):
        return f"Mesh(name={self._mesh.name}, id={self._mesh.id}, project_id={self._project_id!r})"

    def __repr__(self) -> str:
        return self.__str__()

    @property
    @prevent_deleted
    def id(self) -> str:
        """Get the ID of the mesh."""
        return self._mesh.id

    @property
    @prevent_deleted
    def name(self) -> str:
        """Get the name of the mesh."""
        return self._mesh.name

    @name.setter
    @prevent_deleted
    def name(self, name: str) -> None:
        """Set the name of the mesh. Use save() to commit the change."""
        self._current_uncommitted_update().name = name

    @property
    @prevent_deleted
    def quality(self) -> MeshQuality:
        """Get the quality of the mesh."""
        warnings.simplefilter("always", DeprecationWarning)
        warnings.warn(
            "Call to deprecated function quality (Use density instead).",
            category=DeprecationWarning,
            stacklevel=2,
        )
        warnings.simplefilter("default", DeprecationWarning)
        return MeshQuality(self._mesh.quality)

    @quality.setter
    @prevent_deleted
    def quality(self, quality: MeshQuality) -> None:
        """Set the quality of the mesh. Use save() to commit the change."""
        warnings.simplefilter("always", DeprecationWarning)
        warnings.warn(
            "Call to deprecated function quality (Use density instead).",
            category=DeprecationWarning,
            stacklevel=2,
        )
        warnings.simplefilter("default", DeprecationWarning)
        self._current_uncommitted_update().quality = quality.value

    @property
    @prevent_deleted
    def density(self) -> MeshDensity:
        """Get the density of the mesh."""
        return MeshDensity(self._mesh.density)

    @density.setter
    @prevent_deleted
    def density(self, density: MeshDensity) -> None:
        """Set the density of the mesh. Use save() to commit the change."""
        self._current_uncommitted_update().density = density.value

    @property
    @prevent_deleted
    def node_type(self) -> str | None:
        """Get the node type of the mesh."""
        return self._mesh.node_type

    @node_type.setter
    @prevent_deleted
    def node_type(self, node_type: str) -> None:
        """Set the node type of the mesh. Use save() to commit the change."""
        self._current_uncommitted_update().node_type = node_type

    @property
    @prevent_deleted
    def max_run_time_minutes(self) -> int:
        """Get the maximum run time of the mesh."""
        return self._mesh.max_run_time_minutes

    @max_run_time_minutes.setter
    @prevent_deleted
    def max_run_time_minutes(self, max_run_time_minutes: int) -> None:
        """Set the maximum run time of the mesh. Use save() to commit the change."""
        self._current_uncommitted_update().max_run_time_minutes = max_run_time_minutes

    @property
    @prevent_deleted
    def use_mesh_refiner(self) -> bool:
        """Get whether the mesh uses the mesh refiner."""
        if self._mesh.parameters is None:
            return False
        return (
            self._mesh.parameters.mesh_algorithm
            == rawapi.MeshAlgorithm.MESH_MINUS_REFINER
        )

    @use_mesh_refiner.setter
    @prevent_deleted
    def use_mesh_refiner(self, use_mesh_refiner: bool) -> None:
        """Set whether the mesh uses the mesh refiner. Use save() to commit the change."""
        self._on_set_parameter(set_user_defined=use_mesh_refiner is not None)
        self._current_uncommitted_update().parameters.mesh_algorithm = (
            rawapi.MeshAlgorithm.MESH_MINUS_REFINER
            if use_mesh_refiner
            else rawapi.MeshAlgorithm.GMSH
        )

    @property
    @prevent_deleted
    def mesh_size_min(self) -> str | None:
        """Get the minimum mesh size of the mesh."""
        if self._mesh.parameters is None or self._mesh.parameters.mesh_size_min is None:
            return None
        return self._mesh.parameters.mesh_size_min

    @mesh_size_min.setter
    @prevent_deleted
    def mesh_size_min(self, mesh_size_min: float | int | str) -> None:
        """Set the minimum mesh size of the mesh. Use save() to commit the change."""
        self._on_set_parameter(set_user_defined=mesh_size_min is not None)
        self._current_uncommitted_update().parameters.mesh_size_min = (
            str(mesh_size_min) if mesh_size_min is not None else None
        )

    @property
    @prevent_deleted
    def mesh_size_max(self) -> str | None:
        """Get the maximum mesh size of the mesh."""
        if self._mesh.parameters is None or self._mesh.parameters.mesh_size_max is None:
            return None
        return self._mesh.parameters.mesh_size_max

    @mesh_size_max.setter
    @prevent_deleted
    def mesh_size_max(self, mesh_size_max: float | int | str) -> None:
        """Set the maximum mesh size of the mesh. Use save() to commit the change."""
        self._on_set_parameter(set_user_defined=mesh_size_max is not None)
        self._current_uncommitted_update().parameters.mesh_size_max = (
            str(mesh_size_max) if mesh_size_max is not None else None
        )

    @property
    @prevent_deleted
    def scale_factor(self) -> str | None:
        """Get the scale factor of the mesh."""
        if self._mesh.parameters is None or self._mesh.parameters.scale_factor is None:
            return None
        return self._mesh.parameters.scale_factor

    @scale_factor.setter
    @prevent_deleted
    def scale_factor(self, scale_factor: float | int | str) -> None:
        """Set the scale factor of the mesh. Use save() to commit the change."""
        self._on_set_parameter(set_user_defined=scale_factor is not None)
        self._current_uncommitted_update().parameters.scale_factor = (
            str(scale_factor) if scale_factor is not None else None
        )

    @property
    @prevent_deleted
    def curvature_enhancement(self) -> str | None:
        """Get the curvature enhancement of the mesh."""
        if (
            self._mesh.parameters is None
            or self._mesh.parameters.curvature_enhancement is None
        ):
            return None
        return self._mesh.parameters.curvature_enhancement

    @curvature_enhancement.setter
    @prevent_deleted
    def curvature_enhancement(self, curvature_enhancement: float | int | str) -> None:
        """Set the curvature enhancement of the mesh. Use save() to commit the change."""
        self._on_set_parameter(set_user_defined=curvature_enhancement is not None)
        self._current_uncommitted_update().parameters.curvature_enhancement = (
            str(curvature_enhancement) if curvature_enhancement is not None else None
        )

    @property
    @prevent_deleted
    def curved_mesh(self) -> bool:
        """Get whether the mesh is curved."""
        if self._mesh.parameters is None or self._mesh.parameters.curved_mesh is None:
            return False
        return self._mesh.parameters.curved_mesh

    @curved_mesh.setter
    @prevent_deleted
    def curved_mesh(self, curved_mesh: bool) -> None:
        """Set whether the mesh is curved. Use save() to commit the change."""
        self._on_set_parameter(set_user_defined=curved_mesh is not None)
        self._current_uncommitted_update().parameters.curved_mesh = curved_mesh

    @property
    @prevent_deleted
    def target_width_to_height_ratio(self) -> str | None:
        """Get the target width to height ratio of the mesh."""
        if (
            self._mesh.parameters is None
            or self._mesh.parameters.target_width_to_height_ratio is None
        ):
            return None
        return self._mesh.parameters.target_width_to_height_ratio

    @target_width_to_height_ratio.setter
    @prevent_deleted
    def target_width_to_height_ratio(
        self, target_width_to_height_ratio: float | int | str
    ) -> None:
        """Set the target width to height ratio of the mesh. Use save() to commit the change."""
        self._on_set_parameter(
            set_user_defined=target_width_to_height_ratio is not None
        )
        self._current_uncommitted_update().parameters.target_width_to_height_ratio = (
            str(target_width_to_height_ratio)
            if target_width_to_height_ratio is not None
            else None
        )

    @property
    @prevent_deleted
    def auto_transfinite(self) -> List[AutoTransfiniteGroup] | None:
        """Get the auto-transfinite meshing groups."""
        if (
            self._mesh.parameters is None
            or self._mesh.parameters.auto_transfinite_meshing is None
        ):
            return None

        groups: List[AutoTransfiniteGroup] = []
        project_regions = Region.get_all(self._project_id)

        for entry in self._mesh.parameters.auto_transfinite_meshing:
            region = None
            tags = None
            entity_type = entry.entity_type

            if entry.target.region_ids is not None:
                for region_id in entry.target.region_ids:
                    found = next(
                        (r for r in project_regions if r.id == region_id), None
                    )
                    if found is None:
                        raise ValueError(f"Region {region_id} not found")
                    if region is None:
                        region = found
            elif entry.target.entity_ids is not None:
                tags = entry.target.entity_ids

            groups.append(
                AutoTransfiniteGroup(
                    hx=entry.element_sizes.hx,
                    hy=entry.element_sizes.hy,
                    hz=entry.element_sizes.hz,
                    region=region,
                    tags=tags,
                    entity_type=entity_type,
                )
            )

        return groups if groups else None

    @auto_transfinite.setter
    @prevent_deleted
    def auto_transfinite(
        self, auto_transfinite: List[AutoTransfiniteGroup] | None
    ) -> None:
        """Set the auto-transfinite meshing groups. Use save() to commit the change."""
        self._on_set_parameter(
            set_user_defined=auto_transfinite is not None and len(auto_transfinite) > 0
        )
        mesh_settings = MeshSettings(auto_transfinite=auto_transfinite)
        self._current_uncommitted_update().parameters.auto_transfinite_meshing = (
            mesh_settings.parameters.auto_transfinite_meshing
            if mesh_settings.parameters is not None
            else None
        )

    @property
    @prevent_deleted
    def refinements(self) -> List[MeshRefinement] | None:
        """Get the refinements of the mesh."""
        if (
            self._mesh.parameters is None
            or self._mesh.parameters.selective_refinement is None
        ):
            return None

        sr = self._mesh.parameters.selective_refinement
        refinement_items: List[
            tuple[rawapi.SelectiveMeshRefinementItem, rawapi.EntityType]
        ] = []
        for items, etype in [
            (sr.volumes, rawapi.EntityType.VOLUME),
            (sr.surfaces, rawapi.EntityType.SURFACE),
            (sr.curves, rawapi.EntityType.CURVE),
        ]:
            if items is not None:
                for item in items:
                    if item.regions is not None or item.tags is not None:
                        refinement_items.append((item, etype))

        if len(refinement_items) == 0:
            return None

        mesh_refinements: List[MeshRefinement] = []
        project_regions = Region.get_all(self._project_id)

        for refinement_item, etype in refinement_items:
            max_size = (
                refinement_item.absolute_refinement
                if refinement_item.absolute_refinement is not None
                else 0
            )
            if refinement_item.tags is not None:
                mesh_refinements.append(
                    MeshRefinement(
                        max_size=max_size,
                        tags=refinement_item.tags,
                        entity_type=etype,
                    )
                )
            elif refinement_item.regions is not None:
                for region_id in refinement_item.regions:
                    region = next(
                        (r for r in project_regions if r.id == region_id), None
                    )
                    if region is None:
                        raise ValueError(f"Region {region_id} not found")
                    mesh_refinements.append(
                        MeshRefinement(max_size=max_size, region=region)
                    )

        return mesh_refinements

    @refinements.setter
    @prevent_deleted
    def refinements(self, refinements: List[MeshRefinement]) -> None:
        """Set the refinements of the mesh. Use save() to commit the change."""
        self._on_set_parameter(
            set_user_defined=refinements is not None and len(refinements) > 0
        )
        mesh_settings = MeshSettings(refinements=refinements)
        if mesh_settings.parameters is None:
            raise ValueError("Error setting refinements")
        self._current_uncommitted_update().parameters.selective_refinement = (
            mesh_settings.parameters.selective_refinement
        )

    @property
    @prevent_deleted
    def extrusion(self) -> MeshExtrusion | None:
        """Get the extrusion of the mesh."""
        if (
            self._mesh.parameters is None
            or self._mesh.parameters.mesh_extrusion is None
        ):
            return None
        raw_ext = self._mesh.parameters.mesh_extrusion

        regions = None
        if raw_ext.volume_regions is not None:
            project_regions = Region.get_all(self._project_id)
            regions = [
                region
                for region in project_regions
                if region.id in raw_ext.volume_regions
            ]

        return MeshExtrusion(
            regions=regions,
            sub_layer_counts=list(raw_ext.sublayers),
            extrusion_overlap_mode=raw_ext.extrusion_overlap_mode,
            volume_ids=raw_ext.volume_ids,
        )

    @extrusion.setter
    @prevent_deleted
    def extrusion(self, extrusion: MeshExtrusion) -> None:
        """Set the extrusion of the mesh. Use save() to commit the change."""
        self._on_set_parameter(set_user_defined=extrusion is not None)
        mesh_settings = MeshSettings(extrusion=extrusion)
        if mesh_settings.parameters is None:
            raise ValueError("Error setting extrusion")
        self._current_uncommitted_update().parameters.mesh_extrusion = (
            mesh_settings.parameters.mesh_extrusion
        )

    @property
    @prevent_deleted
    def slanted_extrusions(self) -> List[SlantedExtrusion] | None:
        """Get the extrusions of the mesh."""
        if (
            self._mesh.parameters is None
            or self._mesh.parameters.structured_mesh_definitions is None
            or self._mesh.parameters.structured_mesh_definitions.slanted_extrusions
            is None
        ):
            return None
        slanted_extrusions: List[SlantedExtrusion] = []
        project_regions = Region.get_all(self._project_id)

        for (
            extrusion
        ) in self._mesh.parameters.structured_mesh_definitions.slanted_extrusions:
            volumes, volume_entity_ids = self._read_entity_selection(
                extrusion.volumes, project_regions
            )
            to_surfaces, to_surface_entity_ids = self._read_entity_selection(
                extrusion.to_surfaces, project_regions
            )
            from_surfaces, from_surface_entity_ids = self._read_entity_selection(
                extrusion.from_surfaces, project_regions
            )
            layers = [
                ExtrusionLayerDefinition(
                    relative_height=layer.relative_height,
                    sublayer_count=layer.sublayer_count,
                )
                for layer in extrusion.layers
            ]
            slanted_extrusion = SlantedExtrusion(
                volumes=volumes,
                to_surfaces=to_surfaces,
                from_surfaces=from_surfaces,
                layers=layers,
                quadrangles=extrusion.quadrangles,
                volume_entity_ids=volume_entity_ids,
                to_surface_entity_ids=to_surface_entity_ids,
                from_surface_entity_ids=from_surface_entity_ids,
            )
            slanted_extrusions.append(slanted_extrusion)
        return slanted_extrusions

    @slanted_extrusions.setter
    @prevent_deleted
    def set_slanted_extrusions(
        self, slanted_extrusions: List[SlantedExtrusion] | None
    ) -> None:
        """Set the slanted extrusions of the mesh. Use save() to commit the change."""
        self._on_set_parameter(
            set_user_defined=slanted_extrusions is not None
            and len(slanted_extrusions) > 0
        )
        mesh_settings = MeshSettings(slanted_extrusions=slanted_extrusions)
        if (
            mesh_settings.parameters is None
            or mesh_settings.parameters.structured_mesh_definitions is None
        ):
            raise ValueError("Error setting slanted extrusions")

        uncommitted_update = self._current_uncommitted_update()
        if uncommitted_update.parameters is None:
            uncommitted_update.parameters = rawapi.MeshParameters()
        if uncommitted_update.parameters.structured_mesh_definitions is None:
            uncommitted_update.parameters.structured_mesh_definitions = (
                rawapi.StructuredMeshDefinitions()
            )

        uncommitted_update.parameters.structured_mesh_definitions.slanted_extrusions = (
            mesh_settings.parameters.structured_mesh_definitions.slanted_extrusions
        )

    @property
    @prevent_deleted
    def path_extrusions(self) -> List[PathExtrusion] | None:
        """Get the path extrusions of the mesh."""
        if (
            self._mesh.parameters is None
            or self._mesh.parameters.structured_mesh_definitions is None
            or self._mesh.parameters.structured_mesh_definitions.path_extrusions is None
        ):
            return None
        path_extrusions: List[PathExtrusion] = []
        project_regions = Region.get_all(self._project_id)

        for (
            extrusion
        ) in self._mesh.parameters.structured_mesh_definitions.path_extrusions:
            volumes, volume_entity_ids = self._read_entity_selection(
                extrusion.volumes, project_regions
            )
            to_surfaces, to_surface_entity_ids = self._read_entity_selection(
                extrusion.to_surfaces, project_regions
            )
            from_surfaces, from_surface_entity_ids = self._read_entity_selection(
                extrusion.from_surfaces, project_regions
            )
            layers = [
                ExtrusionLayerDefinition(
                    relative_height=layer.relative_height,
                    sublayer_count=layer.sublayer_count,
                )
                for layer in extrusion.layers
            ]
            path_extrusion = PathExtrusion(
                volumes=volumes,
                to_surfaces=to_surfaces,
                from_surfaces=from_surfaces,
                layers=layers,
                quadrangles=extrusion.quadrangles,
                volume_entity_ids=volume_entity_ids,
                to_surface_entity_ids=to_surface_entity_ids,
                from_surface_entity_ids=from_surface_entity_ids,
            )
            path_extrusions.append(path_extrusion)
        return path_extrusions

    @path_extrusions.setter
    @prevent_deleted
    def set_path_extrusions(self, path_extrusions: List[PathExtrusion] | None) -> None:
        """Set the path extrusions of the mesh. Use save() to commit the change."""
        self._on_set_parameter(
            set_user_defined=path_extrusions is not None and len(path_extrusions) > 0
        )
        mesh_settings = MeshSettings(path_extrusions=path_extrusions)
        if (
            mesh_settings.parameters is None
            or mesh_settings.parameters.structured_mesh_definitions is None
        ):
            raise ValueError("Error setting path extrusions")

        uncommitted_update = self._current_uncommitted_update()
        if uncommitted_update.parameters is None:
            uncommitted_update.parameters = rawapi.MeshParameters()
        if uncommitted_update.parameters.structured_mesh_definitions is None:
            uncommitted_update.parameters.structured_mesh_definitions = (
                rawapi.StructuredMeshDefinitions()
            )

        uncommitted_update.parameters.structured_mesh_definitions.path_extrusions = (
            mesh_settings.parameters.structured_mesh_definitions.path_extrusions
        )

    @property
    @prevent_deleted
    def flatten_and_rebuild_extrusions(self) -> List[FlattenAndRebuildExtrusion] | None:
        """Get the flatten and rebuild extrusions of the mesh."""
        if (
            self._mesh.parameters is None
            or self._mesh.parameters.structured_mesh_definitions is None
            or self._mesh.parameters.structured_mesh_definitions.flatten_and_rebuild_extrusions
            is None
        ):
            return None
        flatten_and_rebuild_extrusions: List[FlattenAndRebuildExtrusion] = []
        project_regions = Region.get_all(self._project_id)

        for (
            extrusion
        ) in (
            self._mesh.parameters.structured_mesh_definitions.flatten_and_rebuild_extrusions
        ):
            volumes, volume_entity_ids = self._read_entity_selection(
                extrusion.volumes, project_regions
            )
            layers = []
            for layer in extrusion.layers:
                sublayers = []
                for sublayer in layer:
                    if sublayer is None:
                        continue
                    sublayers.append(
                        ExtrusionLayerDefinition(
                            relative_height=sublayer.relative_height,
                            sublayer_count=sublayer.sublayer_count,
                        )
                    )
                if len(sublayers) > 0:
                    layers.append(sublayers)
            direction_vector = None
            if extrusion.direction_vector is not None:
                direction_vector = ExpressionVector(
                    x=extrusion.direction_vector.x,
                    y=extrusion.direction_vector.y,
                    z=extrusion.direction_vector.z,
                )
            flatten_and_rebuild_extrusion = FlattenAndRebuildExtrusion(
                volumes=volumes,
                layers=layers,
                quadrangles=extrusion.quadrangles,
                direction_vector=direction_vector,
                volume_entity_ids=volume_entity_ids,
            )
            flatten_and_rebuild_extrusions.append(flatten_and_rebuild_extrusion)
        return flatten_and_rebuild_extrusions

    @flatten_and_rebuild_extrusions.setter
    @prevent_deleted
    def set_flatten_and_rebuild_extrusions(
        self, flatten_and_rebuild_extrusions: List[FlattenAndRebuildExtrusion] | None
    ) -> None:
        """Set the flatten and rebuild extrusions of the mesh. Use save() to commit the change."""
        self._on_set_parameter(
            set_user_defined=flatten_and_rebuild_extrusions is not None
            and len(flatten_and_rebuild_extrusions) > 0
        )
        mesh_settings = MeshSettings(
            flatten_and_rebuild_extrusions=flatten_and_rebuild_extrusions
        )
        if (
            mesh_settings.parameters is None
            or mesh_settings.parameters.structured_mesh_definitions is None
        ):
            raise ValueError("Error setting flatten and rebuild extrusions")

        uncommitted_update = self._current_uncommitted_update()
        if uncommitted_update.parameters is None:
            uncommitted_update.parameters = rawapi.MeshParameters()
        if uncommitted_update.parameters.structured_mesh_definitions is None:
            uncommitted_update.parameters.structured_mesh_definitions = (
                rawapi.StructuredMeshDefinitions()
            )

        uncommitted_update.parameters.structured_mesh_definitions.flatten_and_rebuild_extrusions = (
            mesh_settings.parameters.structured_mesh_definitions.flatten_and_rebuild_extrusions
        )

    @property
    @prevent_deleted
    def variable_overrides(self) -> List[VariableOverrides] | None:
        """Get the variable overrides of the mesh."""
        if self._mesh.instances is None or len(self._mesh.instances) == 0:
            return None

        override_sets = []
        for mesh_instance in self._mesh.instances:
            if mesh_instance.override_set is not None:
                override_sets.append(
                    VariableOverrides.get(
                        variable_overrides_id=mesh_instance.override_set,
                        project_id=self._project_id,
                    )
                )
        if len(override_sets) == 0:
            return None
        return override_sets

    @variable_overrides.setter
    @prevent_deleted
    def variable_overrides(
        self, variable_overrides: List[VariableOverrides] | None
    ) -> None:
        """Set the variable overrides of the mesh. Use save() to commit the change."""
        if variable_overrides is None:
            self._current_uncommitted_update().override_sets = []
            return

        self._current_uncommitted_update().override_sets = [
            variable_override.id for variable_override in variable_overrides
        ]

    @prevent_deleted
    def create_override(
        self,
        variable_override: "VariableOverrides",
    ) -> MeshInstance:
        """Add a variable-override set to this mesh and return its instance.

        Saves the mesh to the backend, then returns the corresponding
        :class:`MeshInstance`.

        Parameters:
            variable_override: The variable-overrides set to add.

        Returns:
            The newly created MeshInstance.
        """
        current = self.variable_overrides or []
        if any(vo.id == variable_override.id for vo in current):
            raise ValueError(
                f"Variable override {variable_override.id!r} already exists on this mesh"
            )
        self.variable_overrides = current + [variable_override]
        self.save()
        return self.get_override(variable_override=variable_override)

    @prevent_deleted
    def get_override(
        self,
        variable_override: "VariableOverrides | str",
    ) -> MeshInstance:
        """Return the :class:`MeshInstance` for a given variable-override set.

        Parameters:
            variable_override: A :class:`VariableOverrides` object or its ID.

        Returns:
            The matching MeshInstance.

        Raises:
            ValueError: If no instance matches.
        """
        override_id = self._resolve_variable_overrides_id(variable_override)
        for raw_inst in self._mesh.instances:
            if raw_inst.override_set == override_id:
                return MeshInstance(mesh=self, raw_instance=raw_inst)
        raise ValueError(
            f"No mesh instance found for variable override {override_id!r}"
        )

    @prevent_deleted
    def get_overrides(self) -> List[MeshInstance]:
        """Return all override :class:`MeshInstance` objects (excludes the default).

        Returns:
            List of MeshInstance objects for each variable-override set.
        """
        instances: List[MeshInstance] = []
        for raw_inst in self._mesh.instances:
            if raw_inst.override_set is not None:
                instances.append(MeshInstance(mesh=self, raw_instance=raw_inst))
        return instances

    @prevent_deleted
    def delete_override(
        self,
        variable_override: "VariableOverrides | str",
    ) -> None:
        """Remove a variable-override set from this mesh and save.

        Parameters:
            variable_override: A :class:`VariableOverrides` object or its ID.
        """
        override_id = self._resolve_variable_overrides_id(variable_override)
        current = self.variable_overrides or []
        new_overrides = [vo for vo in current if vo.id != override_id]
        if len(new_overrides) == len(current):
            raise ValueError(
                f"Variable override {override_id!r} not found on this mesh"
            )
        self.variable_overrides = new_overrides if new_overrides else None
        self.save()

    @prevent_deleted
    def save(self) -> None:
        """
        Explicitly save the changes to the cloud made by
        setting properties `name`, `quality`, `node_type`, `max_run_time_minutes`,
        `mesh_size_min`, `mesh_size_max`, `scale_factor`, `curvature_enhancement`,
        `curved_mesh`, `refinements` and `variable_overrides`.
        """
        if self._uncommitted_update is None:
            return

        project_id = check_for_project_api_key(self._project_id)
        mesh_update = self._current_uncommitted_update()

        # TODO: Quality is deprecated, use density instead
        if mesh_update.density is None:
            mesh_update.density = mesh_update.quality

        with get_api() as api:
            api.update_mesh(
                authorization=get_auth(),
                project_id=project_id,
                mesh_id=self._mesh.id,
                mesh_update=mesh_update,
            )

            self._uncommitted_update = None

            self._mesh = api.get_mesh(
                authorization=get_auth(),
                project_id=self._project_id,
                mesh_id=self._mesh.id,
            )

    @prevent_deleted
    def start(self) -> None:
        """Start processing the default mesh instance."""
        project_id = check_for_project_api_key(self._project_id)

        self.save()

        default_instance = self._find_default_instance()
        if default_instance is None:
            raise ValueError("Mesh has no default instance")

        with get_api() as api:
            try:
                response = api.start_meshing(
                    authorization=get_auth(),
                    project_id=project_id,
                    mesh_id=self._mesh.id,
                    mesh_instance_id=default_instance.id,
                    body={},
                )
            except Exception as e:
                if getattr(e, "status", None) == 304:
                    self._job = _MockJob(
                        project_id=self._project_id,
                        status=Job.SUCCESS,
                        status_reason="mesh_not_needed",
                    )
                    return
                raise

            self._job = Job(self._project_id, response.id)

            self._mesh = api.get_mesh(
                authorization=get_auth(),
                project_id=self._project_id,
                mesh_id=self._mesh.id,
            )

    @prevent_deleted
    def run(
        self,
        print_logs: bool = False,
        refresh_delay_s: float = 1,
        on_error: OnError = OnError.IGNORE,
    ) -> None:
        """Process the default mesh instance and return when the processing is complete.

        Parameters:
            print_logs: If True, print logs to the console.
            refresh_delay_s: Optional delay in seconds between checking the status of the job.
            on_error: Controls error handling after the job completes.
                ``OnError.IGNORE`` (default) — never raises; use :meth:`get_status` to check.
                ``OnError.RAISE`` — raises :exc:`JobError` unless status is ``SUCCESS`` or
                ``PARTIAL_SUCCESS``.
                ``OnError.STRICT`` — raises :exc:`JobError` unless status is exactly ``SUCCESS``.
        """
        self.start()
        while self.is_running(refresh_delay_s=refresh_delay_s):
            if print_logs:
                self.print_new_loglines()
        if print_logs:
            self.print_new_loglines()
        status = self.get_status()
        if on_error is OnError.STRICT and status != Job.SUCCESS:
            raise JobError(
                f"Mesh '{self.name}' (id={self.id}) processing failed with status: {status}",
                status=status,
            )
        elif on_error is OnError.RAISE and status not in (
            Job.SUCCESS,
            Job.PARTIAL_SUCCESS,
        ):
            raise JobError(
                f"Mesh '{self.name}' (id={self.id}) processing failed with status: {status}",
                status=status,
            )

    @prevent_deleted
    def abort(self) -> None:
        """Abort processing of the default mesh instance."""
        return super().abort()

    @prevent_deleted
    def abort_all(self) -> None:
        """Abort processing of the default mesh instance and all override instances."""
        super().abort()
        for instance in self.get_overrides():
            instance.abort()

    @prevent_deleted
    def get_status(self) -> str | None:
        """Get the status of the default mesh instance."""
        return super().get_status()

    @prevent_deleted
    def is_running(self, refresh_delay_s: float | None = None) -> bool:
        """Check if the default mesh instance is running.

        Parameters:
            refresh_delay_s: Delay in seconds between status checks.
        """
        return super().is_running(refresh_delay_s=refresh_delay_s)

    @prevent_deleted
    def refresh_status(self, delay_s: float = 1) -> str | None:
        """Refresh the status of the default mesh instance.

        Parameters:
            delay_s: Delay in seconds before refreshing.
        """
        return super().refresh_status(delay_s=delay_s)

    @prevent_deleted
    def get_logs(self, limit: int = 100) -> List[str]:
        """Get logs from the default mesh instance.

        Parameters:
            limit: Maximum number of log entries.
        """
        return super().get_logs(limit=limit)

    @prevent_deleted
    def print_new_loglines(self, file: TextIO = sys.stdout, limit: int = 100) -> None:
        """Print new log lines from the default mesh instance.

        Parameters:
            file: Output stream.
            limit: Maximum number of log entries.
        """
        return super().print_new_loglines(file=file, limit=limit)

    @prevent_deleted
    def delete(self) -> None:
        """
        Delete the mesh from the project.
        """
        with get_api() as api:
            api.delete_mesh(
                authorization=get_auth(),
                project_id=self._project_id,
                mesh_id=self._mesh.id,
            )
        self._deleted = True

    @prevent_deleted
    def copy(self, name: str | None = None) -> Self:
        """
        Copy the mesh.

        Parameters:
            name: Optional name of the new mesh.

        Returns:
            The copied mesh.
        """
        project_id = check_for_project_api_key(self._project_id)
        with get_api() as api:
            mesh_data = api.copy_mesh(
                authorization=get_auth(),
                project_id=project_id,
                mesh_id=self._mesh.id,
                copy_request=rawapi.CopyRequest(
                    name=name,
                ),
            )
            return self.__class__(
                project_id,
                mesh_data,
            )

    @prevent_deleted
    def save_mesh_file(
        self,
        output_dir: str = "./",
        filename: str = "mesh.msh",
    ) -> None:
        """Save the default mesh instance's file to local disk.

        Parameters:
            output_dir: Directory to save to.
            filename: File name to save as.
        """
        self._save_mesh_file_for_instance(
            variable_overrides_id=None,
            output_dir=output_dir,
            filename=filename,
        )

    def _save_mesh_file_for_instance(
        self,
        variable_overrides_id: str | None,
        output_dir: str = "./",
        filename: str = "mesh.msh",
    ) -> None:
        """Download a mesh file for a specific instance (default or override)."""
        filepath = self._get_filepath(output_dir, filename)

        with get_api() as api:
            mesh_data = api.get_mesh(
                authorization=get_auth(),
                project_id=self._project_id,
                mesh_id=self._mesh.id,
            )
            self._mesh = mesh_data

        mesh_file_id = None
        for mesh_instance in self._mesh.instances:
            if mesh_instance.files is None or len(mesh_instance.files) == 0:
                continue
            if variable_overrides_id is None and mesh_instance.override_set is None:
                mesh_file_id = mesh_instance.files[0].id
                break
            if (
                mesh_instance.override_set is not None
                and mesh_instance.override_set == variable_overrides_id
            ):
                mesh_file_id = mesh_instance.files[0].id
                break
        if mesh_file_id is None:
            raise ValueError("Mesh file not found")

        with get_api() as api:
            response = api.get_mesh_file_download_url(
                authorization=get_auth(),
                project_id=self._project_id,
                mesh_file_id=mesh_file_id,
            )
            url = response.download_url
            if url is None:
                raise ValueError("Failed to get mesh file download URL")
            validate_url_scheme(url, get_allow_insecure_http())
            session = get_http_session()
            with session.get(
                url,
                stream=True,
                timeout=(CONNECT_TIMEOUT_S, TRANSFER_TIMEOUT_S),
            ) as r:
                r.raise_for_status()

                with open(filepath, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

    def _get_filepath(self, output_dir: str, filename: str) -> pathlib.Path:
        """
        Get the filepath to save the mesh file to.

        Parameters:
            output_dir: The directory to save the mesh file to.

        Returns:
            The filepath to save the mesh file to.
        """

        if filename is None or filename == "":
            raise ValueError("Filename is required")

        if filename.count(".") == 0:
            raise ValueError("Filename must contain a file extension")

        path = pathlib.Path(output_dir)
        target_filename = filename

        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        i = 1
        while path.joinpath(target_filename).exists():
            target_filename = f"{filename.split('.')[0]}_({i}).{filename.split('.')[1]}"
            i += 1
        return path.joinpath(target_filename)

    @prevent_deleted
    def _current_uncommitted_update(self) -> rawapi.MeshUpdate:
        """Get the current uncommitted update for the mesh."""
        if self._mesh is None:
            raise ValueError("Mesh is not initialized")
        if self._uncommitted_update is None:
            self._uncommitted_update = rawapi.MeshUpdate(
                name=self._mesh.name,
                density=self._mesh.density,
                # TODO: Quality is deprecated, use density instead
                quality=self._mesh.quality,
                maxRunTimeMinutes=self._mesh.max_run_time_minutes,
                nodeType=self._mesh.node_type,
                parameters=copy.deepcopy(self._mesh.parameters),
                overrideSets=[
                    override_set_id
                    for mesh_instance in (self._mesh.instances or [])
                    if mesh_instance.override_set is not None
                    for override_set_id in mesh_instance.override_set
                ],
                supportData=copy.deepcopy(self._mesh.support_data),
            )

        return self._uncommitted_update

    @prevent_deleted
    def _on_set_parameter(self, set_user_defined: bool = False) -> None:
        if self._current_uncommitted_update().parameters is None:
            self._current_uncommitted_update().parameters = rawapi.MeshParameters()
        if set_user_defined:
            self._current_uncommitted_update().density = rawapi.MeshDensity.USERDEFINED

    def _populate_default_job(self) -> None:
        """Set ``_job`` from the default (non-override) backend instance."""
        default = self._find_default_instance()
        if default is None or default.meshing_job is None:
            return
        raw_job = default.meshing_job
        job = Job(self._project_id, raw_job.id)
        job._job_status = rawapi.JobStatus(
            jobId=raw_job.id,
            status=raw_job.status,
            statusReason=raw_job.status_reason,
            progress=raw_job.progress,
        )
        self._job = job

    def _find_default_instance(self) -> rawapi.MeshInstance | None:
        """Return the default mesh instance (no override set)."""
        for inst in self._mesh.instances:
            if inst.override_set is None:
                return inst
        return None
