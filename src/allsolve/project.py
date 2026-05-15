# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from allsolve.util import FileOverwriteMode
from allsolve.physics import Physic
from allsolve.geometry.cad_file_import import (
    CadBrepFile,
    CadGds2File,
    CadGdsLayer,
    CadIgesFile,
    CadMshFile,
    CadNasFile,
    CadSatFile,
    CadStepFile,
)
from allsolve.geometry.geometry_builder import GeometryBuilder
from allsolve_rawapi.models.shared_expression_override_type import (
    SharedExpressionOverrideType,
)
import warnings

from .job import Job
from .material import Material, MaterialProperty
from .override import VariableOverrides
import allsolve_rawapi as rawapi
from .mesh import Mesh, MeshSettings
from .util import NotProjectAPIKeyError, deprecated, prevent_deleted
from .api import get_api, get_auth, get_token_payload, is_project_api_key
from .simulation import Simulation
from .file import create_file, upload_file, upload_bytes
from .expression import (
    Variable,
    Function,
    InterpolatedFunction,
)
from .geometry import Geometry, GeometryElement, GDS2ImportConfig
from .region import ComputedRegion, Region, RegionOperation, RegionRule

from typing import List, Optional, Sequence, Tuple, Union
from typing_extensions import Self
from enum import Enum

import pathlib
import json


class GeometryPipelineVersion(Enum):
    """
    Enum for the version of the geometry pipeline.
    For new projects, use V2 (default).
    V1 is deprecated.
    """

    V1 = rawapi.GeometryPipelineVersion.V1
    V2 = rawapi.GeometryPipelineVersion.V2


class Project:
    """
    A project in the AllSolve.
    """

    @classmethod
    def from_token(cls) -> Self:
        """
        Get the project associated with the project API key.

        Returns:
            The project associated with the project API key.

        Raises:
            NotProjectAPIKeyError: If not authenticated with a project API key.
        """
        project_id = get_token_payload().project_id

        if project_id is None:
            raise NotProjectAPIKeyError("No project ID found in token")

        with get_api() as api:
            project = api.get_project(
                authorization=get_auth(),
                project_id=project_id,
            )

        return cls(project)

    @classmethod
    def get(cls, project_id: str) -> Self:
        """
        Get a project using the project ID.

        Parameters:
            project_id: The ID of the project to get.

        Returns:
            The project with the given ID.
        """
        with get_api() as api:
            project = api.get_project(
                authorization=get_auth(),
                project_id=project_id,
            )

        return cls(project)

    @classmethod
    def get_all(
        cls,
        *,
        page_size: Optional[int] = None,
        page: Optional[int] = None,
        project_type_filter: rawapi.ProjectTypeFilter = rawapi.ProjectTypeFilter.API,
    ) -> List[Self]:
        """
        Get all projects.

        Parameters:
            page_size: Number of projects per page, defaults to 1000.
            page: Page number to return, defaults to 1.
            project_type_filter: Filter by project type. Defaults to ProjectTypeFilter.API.
               By default, only projects created with the public API are returned.

        Returns:
            A list of projects that the authentication has access to.
        """
        with get_api() as api:
            projects = api.get_projects(
                authorization=get_auth(),
                page_size=page_size,
                page=page,
                project_type=project_type_filter,
            )

        return [cls(p) for p in projects.projects]

    @classmethod
    def get_by_name(
        cls,
        name: str,
        project_type_filter: rawapi.ProjectTypeFilter = rawapi.ProjectTypeFilter.ALL,
    ) -> Self | None:
        """
        Search for a project that matches the exact given name.
        Returns None if no project matches the exact given name.
        Raises ValueError if multiple projects match the exact given name.

        Parameters:
            name: The name of the project to search for.
            project_type_filter: Filter by project type. Defaults to ProjectTypeFilter.ALL.
               By default, all project types are returned.
        Returns:
            The project that matches the exact given name, or None.
        """
        with get_api() as api:
            projects = api.get_projects(
                authorization=get_auth(),
                project_type=project_type_filter,
                name=name,
            ).projects

        if len(projects) == 0:
            return None
        if len(projects) > 1:
            raise ValueError(f"Multiple projects found with name {name}")
        return cls(projects[0])

    @classmethod
    def create(
        cls,
        name: str,
        description: str = "",
        organization_write_access: bool | None = None,
        labels: List[str] | None = None,
        geometry_pipeline_version: GeometryPipelineVersion = GeometryPipelineVersion.V2,
        dimension: int = 3,
        geometry_no_implicit_fragment: bool = False,
    ) -> Self:
        """
        Create a new project.

        Parameters:
            name: The name of the project.
            description: The description of the project.
            organization_write_access: Optional boolean whether the organization has write access to the project.
            labels: Optional list of labels for the project.
            geometry_pipeline_version: Optional GeometryPipelineVersion. Default is V2.
            dimension: Optional dimension of the project. Default is 3.
            geometry_no_implicit_fragment: Optional boolean whether to disable the automatic
                final Fragment All operation. Default is False.
                By default, the final Fragment All operation splits intersecting geometric
                entities into non-intersecting, disjoint parts. Setting parameter to True
                prevents automatic splitting, preserving the original geometric entities as-is.
        Returns:
            The created project.

        Raises:
            ValueError: If authenticated with a project API key. Creating projects
                requires an organization API key.
        """
        if is_project_api_key():
            raise ValueError(
                "Operation not authorized with a project API key. "
                "Creating a project requires an organization API key."
            )

        with get_api() as api:
            project = api.create_project(
                authorization=get_auth(),
                new_project=rawapi.NewProject(
                    name=name,
                    description=description,
                    organizationWriteAccess=organization_write_access,
                    labels=labels,
                    geometryPipelineVersion=geometry_pipeline_version.value,
                    dimension=dimension,
                    geometryNoImplicitFragment=geometry_no_implicit_fragment,
                ),
            )

        return cls(project)

    def __init__(self, project: rawapi.Project) -> None:
        self._project = project
        self._deleted: bool = False
        self._uncommitted_update: rawapi.NewProject | None = None
        self._copy_files_job: Job | None = None
        if self._project.copy_files_job_id is not None:
            self._copy_files_job = Job(
                self._project.id, self._project.copy_files_job_id
            )

    @property
    @prevent_deleted
    def id(self) -> str:
        """Get the ID of the project."""
        return self._project.id

    @property
    @prevent_deleted
    def name(self) -> str:
        """Get the name of the project."""
        return self._project.name

    @name.setter
    @prevent_deleted
    def name(self, name: str) -> None:
        """Set the name of the project."""
        self._current_uncommitted_update().name = name

    @property
    @prevent_deleted
    def description(self) -> str:
        """Get the description of the project."""
        return self._project.description

    @description.setter
    @prevent_deleted
    def description(self, description: str) -> None:
        """Set the description of the project."""
        self._current_uncommitted_update().description = description

    @property
    @prevent_deleted
    def readonly(self) -> bool:
        """Get whether the project is read-only."""
        return self._project.readonly

    @property
    @prevent_deleted
    def labels(self) -> List[str]:
        """Get the labels of the project."""
        return self._project.labels

    @property
    @prevent_deleted
    def geometry_pipeline_version(self) -> GeometryPipelineVersion:
        """Get the geometry pipeline version of the project."""
        return GeometryPipelineVersion(self._project.geometry_pipeline_version)

    @property
    @prevent_deleted
    def dimension(self) -> int:
        """Get the dimension of the project."""
        if self._project.dimension is None:
            return 3
        return self._project.dimension

    @property
    @prevent_deleted
    def geometry_no_implicit_fragment(self) -> bool:
        """Get whether the project geometry has NO implicit Fragment all operation."""
        if self._project.geometry_no_implicit_fragment is None:
            return False
        return self._project.geometry_no_implicit_fragment

    @property
    @prevent_deleted
    def pml_num_layers(self) -> int | None:
        """Get the number of Perfectly Matched Layers, or None if not set."""
        pml = self._get_current_pml_settings()
        if pml is None:
            return None
        return pml.num_layers

    @pml_num_layers.setter
    @prevent_deleted
    def pml_num_layers(self, value: int | None) -> None:
        """Set the number of Perfectly Matched Layers. Use save() to commit."""
        update = self._current_uncommitted_update()
        if update.pml_settings is None:
            update.pml_settings = rawapi.PMLSettings(
                numLayers=value,
                thickness=(
                    self._project.pml_settings.thickness
                    if self._project.pml_settings
                    else None
                ),
            )
        else:
            update.pml_settings.num_layers = value

    @property
    @prevent_deleted
    def pml_thickness(self) -> float | int | None:
        """Get the thickness of the PML region, or None if not set."""
        pml = self._get_current_pml_settings()
        if pml is None:
            return None
        return pml.thickness

    @pml_thickness.setter
    @prevent_deleted
    def pml_thickness(self, value: float | int | None) -> None:
        """Set the thickness of the PML region. Use save() to commit."""
        update = self._current_uncommitted_update()
        if update.pml_settings is None:
            update.pml_settings = rawapi.PMLSettings(
                numLayers=(
                    self._project.pml_settings.num_layers
                    if self._project.pml_settings
                    else None
                ),
                thickness=value,
            )
        else:
            update.pml_settings.thickness = value

    def _get_current_pml_settings(self) -> rawapi.PMLSettings | None:
        """Get PML settings from uncommitted update or from the project."""
        if (
            self._uncommitted_update is not None
            and self._uncommitted_update.pml_settings is not None
        ):
            return self._uncommitted_update.pml_settings
        return self._project.pml_settings

    @prevent_deleted
    def _current_uncommitted_update(self) -> rawapi.NewProject:
        if self._uncommitted_update is None:
            self._uncommitted_update = rawapi.NewProject(
                name=self.name,
                description=self.description,
            )

        return self._uncommitted_update

    @prevent_deleted
    def geometry_builder(self) -> GeometryBuilder:
        """
        Get the geometry builder for the project.
        Use with GeometryPipelineVersion.V2
        """
        if self.geometry_pipeline_version != GeometryPipelineVersion.V2:
            raise ValueError(
                "Geometry pipeline version must be V2 to use the geometry builder"
            )
        return GeometryBuilder(project_id=self._project.id)

    @prevent_deleted
    @deprecated("Use geometry pipeline version V2 for new projects")
    def get_geometry(self) -> List[Geometry]:
        """
        Get geometry elements in the project.
        Currently only one geometry element per project is supported.
        Use with deprecated geometry pipeline version V1.

        Returns:
            A list of geometry elements in the project.
        """
        return Geometry.get(project_id=self._project.id)

    @prevent_deleted
    def import_step(
        self, filepath: str, name: str | None = None
    ) -> Geometry | GeometryBuilder:
        """
        Import the geometry file in the given path to the project.

        Parameters:
            filepath: path to a file in the local system
            name: Optional name for the geometry element

        Returns:
            The GeometryBuilder if GeometryPipelineVersion.V2,
            or the created geometry for deprecated GeometryPipelineVersion.V1,
        """
        if self.geometry_pipeline_version == GeometryPipelineVersion.V2:
            return self.geometry_builder().add(
                CadStepFile(filepath=filepath, name=name)
            )
        return Geometry.create(
            geometry_imports=[GeometryElement.ImportStep(filepath)],
            project_id=self._project.id,
        )

    @prevent_deleted
    def import_iges(
        self, filepath: str, name: str | None = None
    ) -> Geometry | GeometryBuilder:
        """
        Import the geometry file in the given path to the project.

        Parameters:
            filepath: path to a file in the local system
            name: Optional name for the geometry element

        Returns:
            The GeometryBuilder if GeometryPipelineVersion.V2,
            or the created geometry for deprecated GeometryPipelineVersion.V1,
        """
        if self.geometry_pipeline_version == GeometryPipelineVersion.V2:
            return self.geometry_builder().add(
                CadIgesFile(filepath=filepath, name=name)
            )
        return Geometry.create(
            geometry_imports=[GeometryElement.ImportIges(filepath)],
            project_id=self._project.id,
        )

    @prevent_deleted
    def import_brep(
        self, filepath: str, name: str | None = None
    ) -> Geometry | GeometryBuilder:
        """
        Import the geometry file in the given path to the project.

        Parameters:
            filepath: path to a file in the local system
            name: Optional name for the geometry element

        Returns:
            The GeometryBuilder if GeometryPipelineVersion.V2,
            or the created geometry for deprecated GeometryPipelineVersion.V1,
        """
        if self.geometry_pipeline_version == GeometryPipelineVersion.V2:
            return self.geometry_builder().add(
                CadBrepFile(filepath=filepath, name=name)
            )
        return Geometry.create(
            geometry_imports=[GeometryElement.ImportBrep(filepath)],
            project_id=self._project.id,
        )

    @prevent_deleted
    def import_sat(
        self, filepath: str, name: str | None = None
    ) -> Geometry | GeometryBuilder:
        """
        Import the geometry file in the given path to the project.

        Parameters:
            filepath: path to a file in the local system
            name: Optional name for the geometry element

        Returns:
            The GeometryBuilder if GeometryPipelineVersion.V2,
            or the created geometry for deprecated GeometryPipelineVersion.V1,
        """
        if self.geometry_pipeline_version == GeometryPipelineVersion.V2:
            return self.geometry_builder().add(CadSatFile(filepath=filepath, name=name))
        return Geometry.create(
            geometry_imports=[GeometryElement.ImportSat(filepath)],
            project_id=self._project.id,
        )

    @prevent_deleted
    def import_msh(self, filepath: str) -> Geometry | GeometryBuilder:
        """
        Import the geometry file in the given path to the project.

        Parameters:
            filepath: path to a file in the local system

        Returns:
            The GeometryBuilder if GeometryPipelineVersion.V2,
            or the created geometry for deprecated GeometryPipelineVersion.V1,
        """
        if self.geometry_pipeline_version == GeometryPipelineVersion.V2:
            return self.geometry_builder().add(CadMshFile(filepath=filepath))
        return Geometry.create(
            geometry_imports=[GeometryElement.ImportMsh(filepath)],
            project_id=self._project.id,
        )

    @prevent_deleted
    def import_nas(self, filepath: str) -> Geometry | GeometryBuilder:
        """
        Import the geometry file in the given path to the project.

        Parameters:
            filepath: path to a file in the local system

        Returns:
            The GeometryBuilder if GeometryPipelineVersion.V2,
            or the created geometry for deprecated GeometryPipelineVersion.V1,
        """
        if self.geometry_pipeline_version == GeometryPipelineVersion.V2:
            return self.geometry_builder().add(CadNasFile(filepath=filepath))
        return Geometry.create(
            geometry_imports=[GeometryElement.ImportNas(filepath)],
            project_id=self._project.id,
        )

    @prevent_deleted
    def import_gds2(
        self,
        filepath: str,
        config: GDS2ImportConfig | None = None,
        layers: (List[CadGdsLayer]) | None = None,
        name: str | None = None,
    ) -> Geometry | GeometryBuilder:
        """
        Import the geometry file in the given path to the project.

        Parameters:
            filepath: path to a file in the local system
            config: Optional configuration for the GDS import. Use only for deprecated GeometryPipelineVersion.V1.
            layers: Optional layers for the GDS import. Use only for GeometryPipelineVersion.V2.
            name: Optional name for the geometry element
        Returns:
            The GeometryBuilder if GeometryPipelineVersion.V2,
            or the created geometry for deprecated GeometryPipelineVersion.V1,
        """
        if self.geometry_pipeline_version == GeometryPipelineVersion.V2:
            if config is not None:
                raise ValueError(
                    "Config is not supported for GeometryPipelineVersion.V2. Use layers instead."
                )
            if layers is None:
                raise ValueError("Layers are required for GeometryPipelineVersion.V2")
            return self.geometry_builder().add(
                CadGds2File(filepath=filepath, layers=layers, name=name)
            )
        else:
            if config is None:
                raise ValueError(
                    "Config is required for deprecated GeometryPipelineVersion.V1"
                )
            if layers is not None:
                raise ValueError(
                    "Layers are not supported for deprecated GeometryPipelineVersion.V1. Use config instead."
                )
            return Geometry.create(
                geometry_imports=[GeometryElement.ImportGds2(filepath, config)],
                project_id=self._project.id,
            )

    @prevent_deleted
    def add_shared_file(self, filepath: str) -> rawapi.InputFile:
        """
        Add the file in the given path to the project as shared file

        Parameters:
            filepath: path to a file in the local system. If used in a simulation,
                      it is available with its basename.

        Returns:
            A handle to the created file.

        Raises:
            FileExistsError: If a file with the same name already exists and is fully uploaded.
        """
        file = pathlib.Path(filepath)
        try:
            handle = create_file(
                filepath=file,
                size=file.stat().st_size,
                project_id=self._project.id,
            )
        except rawapi.ApiException as e:
            if e.status == 409:
                files = self.get_files()
                for existing_file in files:
                    if existing_file.name == file.name:
                        if existing_file.file_uploaded_at is not None:
                            raise FileExistsError(
                                f"A file named '{file.name}' already exists in this project. "
                                f"Use delete_file() to remove it first."
                            ) from e
                        handle = existing_file
                        break
                else:
                    raise  # File not found, re-raise original error
            else:
                raise

        upload_file(
            filepath=file,
            handle=handle,
            project_id=self._project.id,
        )

        return handle

    @prevent_deleted
    def add_shared_json_file(self, name: str, content: dict) -> rawapi.InputFile:
        """
        Add shared file to the project with the given dictionary serialized
        into JSON as content.

        Parameters:
            name: The name for the file during the simulation
            content: The content of the file

        Returns:
            A handle to the created file.

        Raises:
            FileExistsError: If a file with the same name already exists and is fully uploaded.
        """
        data = json.dumps(content, sort_keys=True).encode()
        file = pathlib.Path(name)
        try:
            handle = create_file(
                filepath=file,
                size=len(data),
                project_id=self._project.id,
            )
        except rawapi.ApiException as e:
            if e.status == 409:
                files = self.get_files()
                for existing_file in files:
                    if existing_file.name == file.name:
                        if existing_file.file_uploaded_at is not None:
                            raise FileExistsError(
                                f"A file named '{file.name}' already exists in this project. "
                                f"Use delete_file() to remove it first."
                            ) from e
                        handle = existing_file
                        break
                else:
                    raise  # File not found, re-raise original error
            else:
                raise

        upload_bytes(
            data=data,
            handle=handle,
            project_id=self._project.id,
        )

        return handle

    @prevent_deleted
    def get_files(self) -> List[rawapi.InputFile]:
        """
        Get all files in the project.

        Returns:
            A list of files in the project.
        """
        with get_api() as api:
            return api.get_files(
                authorization=get_auth(),
                project_id=self._project.id,
            )

    @prevent_deleted
    def get_meshes(self) -> List[Mesh]:
        """
        Get all meshes in the project.

        Returns:
            A list of meshes in the project.
        """
        return Mesh.get_all(project_id=self._project.id)

    @prevent_deleted
    def create_mesh(
        self,
        mesh_settings: MeshSettings | None = None,
    ) -> Mesh:
        """
        Create a new mesh in the project.

        Parameters:
            mesh_settings: The settings for the mesh.

        Returns:
            The created mesh.
        """
        return Mesh.create(
            project_id=self._project.id,
            mesh_settings=mesh_settings,
        )

    @prevent_deleted
    def get_physics(self) -> List[Physic]:
        """
        Get all physics in the project.
        """
        return Physic.get_all(project_id=self._project.id)

    @prevent_deleted
    def add_physics(self, physic: Physic) -> Physic:
        """
        Add a physics definition to the project.

        Example::

            solid_mechanics_physics = project.add_physics(
                allsolve.Physics.SolidMechanics(
                    target=solid_mechanics_region
                )
            )
            solid_mechanics_physics.add_interactions(
                [
                    allsolve.Interaction.SolidMechanicsClamp(
                        name="Clamp",
                        target=clamp_surface_region,
                    ),
                ]
            )
        """
        if self._project.id is None:
            raise ValueError("Project must have an id before adding physics")
        if not isinstance(physic, Physic):
            raise ValueError("physic must be a Physic instance")
        return physic._create_bound(project_id=self._project.id)

    @prevent_deleted
    def get_simulation(self, simulation_id: str) -> Simulation:
        """
        Get a simulation using the simulation ID.

        Parameters:
            simulation_id: The ID of the simulation to get.

        Returns:
            The simulation with the given ID.
        """
        return Simulation.get(
            simulation_id=simulation_id,
            project_id=self._project.id,
        )

    @prevent_deleted
    def get_simulations(self) -> List[Simulation]:
        """
        Get all simulations in the project.

        Returns:
            A list of simulations in the project.
        """
        return Simulation.get_all(project_id=self._project.id)

    @prevent_deleted
    def create_simulation(
        self,
        name: str,
        description: str,
        max_run_time_minutes: int,
        solver_mode: rawapi.DistributedSolverMode,
        mesh_id: str | None = None,
        variable_overrides_id: str | None = None,
        analysis_type: rawapi.AnalysisType | None = None,
        harmonics: list[int] | None = None,
        physics: list[str] | None = None,
        transient_start_time: str | None = None,
        transient_end_time: str | None = None,
        transient_timestep_size: str | None = None,
        timestep_algorithm: rawapi.TimestepAlgorithm | None = None,
        fundamental_frequency: str | None = None,
        num_fft_samples: int | None = None,
        num_requested_eigenmodes: str | None = None,
        target_eigenfrequency: str | None = None,
        eigenmode_port_analysis: bool | None = None,
        solver_tolerance: str | None = None,
        nonlinear_solver_tolerance: str | None = None,
        nonlinear_solver_max_iterations: str | None = None,
        eigenmode_solver_tolerance: str | None = None,
        eigenmode_solver_max_iterations: str | None = None,
        target_frequency: str | None = None,
        numerical_jacobian: bool | None = None,
    ) -> Simulation:
        return Simulation.create(
            name=name,
            description=description,
            max_run_time_minutes=max_run_time_minutes,
            solver_mode=solver_mode,
            project_id=self._project.id,
            mesh_id=mesh_id,
            variable_overrides_id=variable_overrides_id,
            analysis_type=analysis_type,
            harmonics=harmonics,
            physics=physics,
            transient_start_time=transient_start_time,
            transient_end_time=transient_end_time,
            transient_timestep_size=transient_timestep_size,
            timestep_algorithm=timestep_algorithm,
            fundamental_frequency=fundamental_frequency,
            num_fft_samples=num_fft_samples,
            num_requested_eigenmodes=num_requested_eigenmodes,
            target_eigenfrequency=target_eigenfrequency,
            eigenmode_port_analysis=eigenmode_port_analysis,
            solver_tolerance=solver_tolerance,
            nonlinear_solver_tolerance=nonlinear_solver_tolerance,
            nonlinear_solver_max_iterations=nonlinear_solver_max_iterations,
            eigenmode_solver_tolerance=eigenmode_solver_tolerance,
            eigenmode_solver_max_iterations=eigenmode_solver_max_iterations,
            target_frequency=target_frequency,
            numerical_jacobian=numerical_jacobian,
        )

    @staticmethod
    def _resolve_mesh_id(mesh: "Mesh | str | None") -> str | None:
        if mesh is None or isinstance(mesh, str):
            return mesh
        return mesh.id

    @staticmethod
    def _resolve_variable_overrides_id(
        variable_overrides: "VariableOverrides | str | None",
    ) -> str | None:
        if variable_overrides is None or isinstance(variable_overrides, str):
            return variable_overrides
        return variable_overrides.id

    @staticmethod
    def _resolve_simulation_id(simulation: "Simulation | str") -> str:
        if isinstance(simulation, str):
            return simulation
        return simulation.id

    @prevent_deleted
    def create_simulation_static(
        self,
        name: str,
        description: str,
        max_run_time_minutes: int,
        solver_mode: rawapi.DistributedSolverMode = rawapi.DistributedSolverMode.DIRECT,
        mesh: "Mesh | str | None" = None,
        variable_overrides: "VariableOverrides | str | None" = None,
        physics: list[str] | None = None,
        solver_tolerance: str | None = None,
        nonlinear_solver_tolerance: str | None = None,
        nonlinear_solver_max_iterations: str | None = None,
        numerical_jacobian: bool | None = None,
    ) -> Simulation:
        """
        Create a new steady-state (static) simulation in the project.

        Parameters:
            name: The name of the new simulation.
            description: The description of the new simulation.
            max_run_time_minutes: The maximum run time of the simulation.
            solver_mode: The solver mode of the simulation.
            mesh: The mesh to use (Mesh object or ID string).
            variable_overrides: The variable overrides to use (VariableOverrides object or ID string).
            physics: List of physics IDs to simulate.
            solver_tolerance: The solver tolerance expression (used when solver_mode is iterative).
            nonlinear_solver_tolerance: The nonlinear solver tolerance expression.
            nonlinear_solver_max_iterations: The nonlinear solver maximum iterations expression.
            numerical_jacobian: Whether numerical Jacobian is enabled.

        Returns:
            The created simulation.
        """
        return Simulation.create(
            analysis_type=rawapi.AnalysisType.STEADYSTATE,
            name=name,
            description=description,
            max_run_time_minutes=max_run_time_minutes,
            solver_mode=solver_mode,
            mesh_id=self._resolve_mesh_id(mesh),
            variable_overrides_id=self._resolve_variable_overrides_id(
                variable_overrides
            ),
            physics=physics,
            solver_tolerance=solver_tolerance,
            nonlinear_solver_tolerance=nonlinear_solver_tolerance,
            nonlinear_solver_max_iterations=nonlinear_solver_max_iterations,
            numerical_jacobian=numerical_jacobian,
            project_id=self._project.id,
        )

    @prevent_deleted
    def create_simulation_harmonic(
        self,
        name: str,
        description: str,
        max_run_time_minutes: int,
        solver_mode: rawapi.DistributedSolverMode = rawapi.DistributedSolverMode.DIRECT,
        fundamental_frequency: str | None = None,
        num_fft_samples: int | None = None,
        mesh: "Mesh | str | None" = None,
        variable_overrides: "VariableOverrides | str | None" = None,
        physics: list[str] | None = None,
        solver_tolerance: str | None = None,
        nonlinear_solver_tolerance: str | None = None,
        nonlinear_solver_max_iterations: str | None = None,
        numerical_jacobian: bool | None = None,
    ) -> Simulation:
        """
        Create a new harmonic simulation in the project.

        Harmonic-specific parameters:
            fundamental_frequency: The fundamental frequency expression.
            num_fft_samples: The number of FFT samples (minimum 3).

        Parameters:
            name: The name of the new simulation.
            description: The description of the new simulation.
            max_run_time_minutes: The maximum run time of the simulation.
            solver_mode: The solver mode of the simulation.
            mesh: The mesh to use (Mesh object or ID string).
            variable_overrides: The variable overrides to use (VariableOverrides object or ID string).
            physics: List of physics IDs to simulate.
            solver_tolerance: The solver tolerance expression (used when solver_mode is iterative).
            nonlinear_solver_tolerance: The nonlinear solver tolerance expression.
            nonlinear_solver_max_iterations: The nonlinear solver maximum iterations expression.
            numerical_jacobian: Whether numerical Jacobian is enabled.

        Returns:
            The created simulation.
        """
        return Simulation.create(
            analysis_type=rawapi.AnalysisType.HARMONIC,
            name=name,
            description=description,
            max_run_time_minutes=max_run_time_minutes,
            solver_mode=solver_mode,
            fundamental_frequency=fundamental_frequency,
            num_fft_samples=num_fft_samples,
            mesh_id=self._resolve_mesh_id(mesh),
            variable_overrides_id=self._resolve_variable_overrides_id(
                variable_overrides
            ),
            physics=physics,
            solver_tolerance=solver_tolerance,
            nonlinear_solver_tolerance=nonlinear_solver_tolerance,
            nonlinear_solver_max_iterations=nonlinear_solver_max_iterations,
            numerical_jacobian=numerical_jacobian,
            project_id=self._project.id,
        )

    @prevent_deleted
    def create_simulation_multiharmonic(
        self,
        name: str,
        description: str,
        max_run_time_minutes: int,
        solver_mode: rawapi.DistributedSolverMode = rawapi.DistributedSolverMode.DIRECT,
        fundamental_frequency: str | None = None,
        harmonics: list[int] | None = None,
        num_fft_samples: int | None = None,
        mesh: "Mesh | str | None" = None,
        variable_overrides: "VariableOverrides | str | None" = None,
        physics: list[str] | None = None,
        solver_tolerance: str | None = None,
        nonlinear_solver_tolerance: str | None = None,
        nonlinear_solver_max_iterations: str | None = None,
        numerical_jacobian: bool | None = None,
    ) -> Simulation:
        """
        Create a new multiharmonic simulation in the project.

        Multiharmonic-specific parameters:
            fundamental_frequency: The fundamental frequency expression.
            harmonics: The list of harmonics.
            num_fft_samples: The number of FFT samples (minimum 3).

        Parameters:
            name: The name of the new simulation.
            description: The description of the new simulation.
            max_run_time_minutes: The maximum run time of the simulation.
            solver_mode: The solver mode of the simulation.
            mesh: The mesh to use (Mesh object or ID string).
            variable_overrides: The variable overrides to use (VariableOverrides object or ID string).
            physics: List of physics IDs to simulate.
            solver_tolerance: The solver tolerance expression (used when solver_mode is iterative).
            nonlinear_solver_tolerance: The nonlinear solver tolerance expression.
            nonlinear_solver_max_iterations: The nonlinear solver maximum iterations expression.
            numerical_jacobian: Whether numerical Jacobian is enabled.

        Returns:
            The created simulation.
        """
        return Simulation.create(
            analysis_type=rawapi.AnalysisType.MULTIHARMONIC,
            name=name,
            description=description,
            max_run_time_minutes=max_run_time_minutes,
            solver_mode=solver_mode,
            fundamental_frequency=fundamental_frequency,
            harmonics=harmonics,
            num_fft_samples=num_fft_samples,
            mesh_id=self._resolve_mesh_id(mesh),
            variable_overrides_id=self._resolve_variable_overrides_id(
                variable_overrides
            ),
            physics=physics,
            solver_tolerance=solver_tolerance,
            nonlinear_solver_tolerance=nonlinear_solver_tolerance,
            nonlinear_solver_max_iterations=nonlinear_solver_max_iterations,
            numerical_jacobian=numerical_jacobian,
            project_id=self._project.id,
        )

    @prevent_deleted
    def create_simulation_transient(
        self,
        name: str,
        description: str,
        max_run_time_minutes: int,
        solver_mode: rawapi.DistributedSolverMode = rawapi.DistributedSolverMode.DIRECT,
        transient_start_time: str | None = None,
        transient_end_time: str | None = None,
        transient_timestep_size: str | None = None,
        timestep_algorithm: rawapi.TimestepAlgorithm | None = None,
        target_frequency: str | None = None,
        mesh: "Mesh | str | None" = None,
        variable_overrides: "VariableOverrides | str | None" = None,
        physics: list[str] | None = None,
        solver_tolerance: str | None = None,
        nonlinear_solver_tolerance: str | None = None,
        nonlinear_solver_max_iterations: str | None = None,
        numerical_jacobian: bool | None = None,
    ) -> Simulation:
        """
        Create a new transient simulation in the project.

        Transient-specific parameters:
            transient_start_time: The transient start time expression.
            transient_end_time: The transient end time expression.
            transient_timestep_size: The transient timestep size expression.
            timestep_algorithm: The timestep algorithm.
            target_frequency: The target frequency expression.

        Parameters:
            name: The name of the new simulation.
            description: The description of the new simulation.
            max_run_time_minutes: The maximum run time of the simulation.
            solver_mode: The solver mode of the simulation.
            mesh: The mesh to use (Mesh object or ID string).
            variable_overrides: The variable overrides to use (VariableOverrides object or ID string).
            physics: List of physics IDs to simulate.
            solver_tolerance: The solver tolerance expression (used when solver_mode is iterative).
            nonlinear_solver_tolerance: The nonlinear solver tolerance expression.
            nonlinear_solver_max_iterations: The nonlinear solver maximum iterations expression.
            numerical_jacobian: Whether numerical Jacobian is enabled.

        Returns:
            The created simulation.
        """
        return Simulation.create(
            analysis_type=rawapi.AnalysisType.TRANSIENT,
            name=name,
            description=description,
            max_run_time_minutes=max_run_time_minutes,
            solver_mode=solver_mode,
            transient_start_time=transient_start_time,
            transient_end_time=transient_end_time,
            transient_timestep_size=transient_timestep_size,
            timestep_algorithm=timestep_algorithm,
            target_frequency=target_frequency,
            mesh_id=self._resolve_mesh_id(mesh),
            variable_overrides_id=self._resolve_variable_overrides_id(
                variable_overrides
            ),
            physics=physics,
            solver_tolerance=solver_tolerance,
            nonlinear_solver_tolerance=nonlinear_solver_tolerance,
            nonlinear_solver_max_iterations=nonlinear_solver_max_iterations,
            numerical_jacobian=numerical_jacobian,
            project_id=self._project.id,
        )

    @prevent_deleted
    def create_simulation_eigenmode(
        self,
        name: str,
        description: str,
        max_run_time_minutes: int,
        solver_mode: rawapi.DistributedSolverMode = rawapi.DistributedSolverMode.DIRECT,
        num_requested_eigenmodes: str | None = None,
        target_eigenfrequency: str | None = None,
        eigenmode_solver_tolerance: str | None = None,
        eigenmode_solver_max_iterations: str | None = None,
        mesh: "Mesh | str | None" = None,
        variable_overrides: "VariableOverrides | str | None" = None,
        physics: list[str] | None = None,
        solver_tolerance: str | None = None,
    ) -> Simulation:
        """
        Create a new eigenmode simulation in the project.

        Eigenmode-specific parameters:
            num_requested_eigenmodes: The number of requested eigenmodes expression.
            target_eigenfrequency: The target eigenfrequency expression.
            eigenmode_solver_tolerance: The eigenmode solver tolerance expression.
            eigenmode_solver_max_iterations: The eigenmode solver maximum iterations expression.

        Parameters:
            name: The name of the new simulation.
            description: The description of the new simulation.
            max_run_time_minutes: The maximum run time of the simulation.
            solver_mode: The solver mode of the simulation.
            mesh: The mesh to use (Mesh object or ID string).
            variable_overrides: The variable overrides to use (VariableOverrides object or ID string).
            physics: List of physics IDs to simulate.
            solver_tolerance: The solver tolerance expression (used when solver_mode is iterative).

        Returns:
            The created simulation.
        """
        return Simulation.create(
            analysis_type=rawapi.AnalysisType.EIGENMODE,
            name=name,
            description=description,
            max_run_time_minutes=max_run_time_minutes,
            solver_mode=solver_mode,
            num_requested_eigenmodes=num_requested_eigenmodes,
            target_eigenfrequency=target_eigenfrequency,
            eigenmode_solver_tolerance=eigenmode_solver_tolerance,
            eigenmode_solver_max_iterations=eigenmode_solver_max_iterations,
            mesh_id=self._resolve_mesh_id(mesh),
            variable_overrides_id=self._resolve_variable_overrides_id(
                variable_overrides
            ),
            physics=physics,
            solver_tolerance=solver_tolerance,
            project_id=self._project.id,
        )

    @prevent_deleted
    def copy_simulation(self, simulation: "Simulation | str") -> Simulation:
        """
        Create a copy of a simulation in the project.

        Parameters:
            simulation: The simulation to copy (Simulation object or ID string).

        Returns:
            The copied simulation.
        """
        simulation_id = self._resolve_simulation_id(simulation)
        return self.get_simulation(simulation_id=simulation_id).copy()

    @prevent_deleted
    def get_regions(self) -> List[Region]:
        """
        Get all regions in the project.

        Returns:
            A list of regions in the project.
        """
        return Region.get_all(project_id=self._project.id)

    @prevent_deleted
    def create_region_basic(
        self,
        name: str,
        entity_type: rawapi.EntityType,
        entity_tags: List[int],
        *,
        shared: bool = True,
    ) -> Region:
        """
        Create a basic region in the project.

        Parameters:
            name: The name of the region.
            entity_type: The type of the entity.
            entity_tags: The tags of the entity.

        Returns:
            The created region.
        """
        return Region.create(
            name=name,
            entity_type=entity_type,
            entity_tags=entity_tags,
            region_rule=None,
            project_id=self._project.id,
            shared=shared,
        )

    @prevent_deleted
    def create_region_computed(
        self,
        name: str,
        entity_type: rawapi.EntityType,
        operation: RegionOperation,
        source_regions: "Sequence[Region | str]",
        *,
        shared: bool = True,
    ) -> ComputedRegion:
        """
        Create a computed region in the project.

        Parameters:
            name: The name of the region.
            entity_type: The type of the entity.
            operation: The operation to perform on the source regions.
            source_regions: The source regions (Region objects or ID strings).

        Returns:
            The created computed region.
        """
        return ComputedRegion.create(
            name=name,
            entity_type=entity_type,
            operation=operation.value,
            source_regions=source_regions,
            project_id=self._project.id,
            shared=shared,
        )

    @prevent_deleted
    def create_region_rule(
        self,
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
        *,
        shared: bool = True,
    ) -> Region:
        """
        Create a region rule in the project.

        Parameters:
            name: The name of the region.
            entity_type: The type of the entity.
            attribute_path: The attribute path to use for the region.
                Can be a list of tuples (key, value).
                Example: [("LayerName", "Polysilicon")]
            bounding_box: The bounding box to use for the region. May be an ``ExpressionBoundingBox``
                or ``(min_corner, max_corner)``; each corner may be an ``ExpressionVector`` or a
                length-3 ``(x, y, z)`` tuple of ``str``, ``int``, or ``float`` (coerced to
                expression strings for the API).
            min_size: The minimum size to use for the region. May be an ``ExpressionVector`` or a
                length-3 ``(x, y, z)`` tuple of ``str``, ``int``, or ``float``.
            max_size: The maximum size to use for the region. Same accepted shapes as ``min_size``.

        Returns:
            The created region rule.
        """
        return RegionRule.create(
            name=name,
            entity_type=entity_type,
            attribute_path=attribute_path,
            bounding_box=bounding_box,
            min_size=min_size,
            max_size=max_size,
            project_id=self._project.id,
            shared=shared,
        )

    @prevent_deleted
    def create_variable(
        self, name: str, expression: str | float | int, description: str = ""
    ) -> Variable:
        """
        Create a variable in the project.

        Parameters:
            name: The name of the variable.
            expression: The expression of the variable.
            description: The description of the variable.

        Returns:
            The created variable.
        """
        return Variable.create(
            name=name,
            expression=expression,
            description=description,
            project_id=self._project.id,
        )

    @prevent_deleted
    def create_variables(
        self,
        variables: List[
            Union[
                Tuple[str, str | float | int],
                Tuple[str, str | float | int, str],
            ]
        ],
        update_existing: bool = False,
    ) -> List[Variable]:
        """
        Create multiple variables in the project.

        Each entry is ``(name, expression)`` or ``(name, expression, description)``.

        Parameters:
            variables: List of variable definitions as tuples.
            update_existing: If False (default), a variable with the same name
                must not already exist or ``ValueError`` is raised. If True,
                an existing variable is updated (expression and description).

        Returns:
            The created or updated variables, in the same order as ``variables``.
        """
        pid = self._project.id
        existing_vars = {v.name: v for v in Variable.get_all(project_id=pid)}
        vars: List[Variable] = []
        for item in variables:
            if len(item) == 2:
                name, expression = item
                description = ""
            elif len(item) == 3:
                name, expression, description = item
            else:
                raise ValueError(
                    "Each entry must be a 2-tuple (name, expression) or "
                    f"3-tuple (name, expression, description); got length {len(item)}: {item!r}"
                )
            existing = existing_vars.get(name)
            if existing is not None:
                if not update_existing:
                    raise ValueError(
                        f"Variable with name {name!r} already exists in the project"
                    )
                if expression is not None:
                    expression = str(expression)
                existing.expression = expression
                existing.description = description
                existing.save()
                vars.append(existing)
            else:
                vars.append(
                    Variable.create(
                        name=name,
                        expression=expression,
                        description=description,
                        project_id=pid,
                    )
                )
        return vars

    @prevent_deleted
    def create_function(
        self,
        name: str,
        args: List[str],
        expression: str,
        description: str = "",
    ) -> Function:
        """
        Create a function in the project.

        Parameters:
            name: The name of the function.
            args: The arguments of the function.
            expression: The expression of the function.
            description: The description of the function.

        Returns:
            The created function.
        """
        return Function.create(
            name=name,
            expression=expression,
            args=args,
            description=description,
            project_id=self._project.id,
        )

    @prevent_deleted
    def create_interpolated_function(
        self,
        name: str,
        args: List[Tuple[str, List[float]]],
        values: List[float],
        description: str = "",
        cubic_interpolation: bool | None = None,
    ) -> InterpolatedFunction:
        """
        Create an interpolated function in the project.

        Parameters:
            name: The name of the interpolated function.
            args: The arguments of the interpolated function.
            values: The values of the interpolated function.
            description: The description of the interpolated function.
            cubic_interpolation: If True, values are interpolated using a natural
                cubic spline. If False or None, linear interpolation is used.

        Returns:
            The created interpolated function.
        """
        return InterpolatedFunction.create(
            name=name,
            args=args,
            values=values,
            description=description,
            cubic_interpolation=cubic_interpolation,
            project_id=self._project.id,
        )

    @prevent_deleted
    def get_variables(self) -> List[Variable]:
        """
        Get all variables in the project.
        """
        return Variable.get_all(project_id=self._project.id)

    @prevent_deleted
    def get_functions(self) -> List[Function]:
        """
        Get all functions in the project.
        """
        return Function.get_all(project_id=self._project.id)

    @prevent_deleted
    def get_interpolated_functions(self) -> List[InterpolatedFunction]:
        """
        Get all interpolated functions in the project.
        """
        return InterpolatedFunction.get_all(project_id=self._project.id)

    @prevent_deleted
    def create_variable_overrides(
        self,
        name: str,
        overrides: List[
            Tuple[Variable | str, str | float | int | List[str | float | int]]
        ],
        sweep_type: rawapi.SweepType | None = None,
    ) -> VariableOverrides:
        """
        Create a VariableOverrides in the project.
        It can be used to override a value of a single or multiple variables,
        or to create a sweep over variables.

        Args:
            name: The name of the set of variable overrides.
            overrides: A list of variable overrides.
                The first element of the tuple is the variable to override.
                The variable can be a Variable object or a string with the name of the variable.
                The second element is the new value for the variable.
                The value can be a string, float, int, or list of strings, floats, or ints.
            sweep_type: The type of the sweep. Only valid for sweep overrides.
                If not provided, it will be set to SPECIFIC_VALUES.

        Returns:
            The created variable overrides.
        """
        return VariableOverrides.create(
            name=name,
            override_type=SharedExpressionOverrideType.SWEEP,
            sweep_type=sweep_type,
            overrides=overrides,
            project_id=self._project.id,
        )

    @prevent_deleted
    def get_variable_overrides(self) -> List[VariableOverrides]:
        """
        Get all variable overrides in the project.
        """
        return VariableOverrides.get_all(project_id=self._project.id)

    @prevent_deleted
    def get_materials(self) -> List[Material]:
        """
        Get all materials in the project.

        Returns:
            A list of materials in the project.
        """
        return Material.get_all(project_id=self._project.id)

    @prevent_deleted
    def create_material(
        self,
        name: str,
        description: str = "",
        color: str = "#535050FF",
        abbreviation: str | None = None,
        target_region: Region | None = None,
        coefficient_of_thermal_expansion: str | float | List[float | str] | None = None,
        density: str | float | None = None,
        dynamic_viscosity: str | float | List[List[float | str]] | None = None,
        elasticity_matrix: (
            MaterialProperty.ElasticityMatrixYoungsModulusPoissonsRatio
            | MaterialProperty.ElasticityMatrixPressureShearVelocity
            | MaterialProperty.ElasticityMatrix
            | None
        ) = None,
        electric_conductivity: str | float | List[List[float | str]] | None = None,
        electric_permittivity: str | float | List[List[float | str]] | None = None,
        heat_capacity: str | float | None = None,
        magnetic_permeability: str | float | List[List[float | str]] | None = None,
        mass_damping_coefficient: str | float | None = None,
        piezoelectric_coupling: List[List[float | str]] | None = None,
        prony_series: MaterialProperty.PronySeries | None = None,
        speed_of_sound: str | float | None = None,
        stiffness_damping_coefficient: str | float | None = None,
        thermal_conductivity: str | float | List[List[float | str]] | None = None,
        orientation: str | Tuple[float | int, float | int, float | int] | None = None,
        enabled: str | None = None,
    ) -> Material:
        """
        Create a material in the project.

        Parameters:
            name: The name of the material.
            description: Optional description of the material.
            color: The color of the material. Format: "#RRGGBB"
            abbreviation: Optional abbreviation of the material.
            target_region: The target Region of the material.
            coefficient_of_thermal_expansion: Optional coefficient of thermal expansion.
                Pass a float or string expression for isotropic, or a list of 6 floats/strings
                for anisotropic.
            density: Optional density of the material. Can be a float or string expression.
            dynamic_viscosity: Optional dynamic viscosity. Pass a float or string expression
                for isotropic, or a 3x3 matrix (list of 3 lists of 3 floats/strings) for
                anisotropic.
            elasticity_matrix: Optional elasticity definition. Accepts one of:
                - MaterialProperty.ElasticityMatrixYoungsModulusPoissonsRatio
                - MaterialProperty.ElasticityMatrixPressureShearVelocity
                - MaterialProperty.ElasticityMatrix (full 6x6 matrix)
            electric_conductivity: Optional electric conductivity. Pass a float or string
                expression for isotropic, or a 3x3 matrix (list of 3 lists of 3
                floats/strings) for anisotropic.
            electric_permittivity: Optional electric permittivity. Pass a float or string
                expression for isotropic, or a 3x3 matrix (list of 3 lists of 3
                floats/strings) for anisotropic.
            heat_capacity: Optional heat capacity. Can be a float or string expression.
            magnetic_permeability: Optional magnetic permeability. Pass a float or string
                expression for isotropic, or a 3x3 matrix (list of 3 lists of 3
                floats/strings) for anisotropic.
            mass_damping_coefficient: Optional mass damping coefficient. Can be a float
                or string expression.
            piezoelectric_coupling: Optional piezoelectric coupling matrix. A 6x3 matrix
                as a list of lists of floats or strings.
            prony_series: Optional Prony series for viscoelastic material properties.
                A MaterialProperty.PronySeries object.
            speed_of_sound: Optional speed of sound. Can be a float or string expression.
            stiffness_damping_coefficient: Optional stiffness damping coefficient. Can be
                a float or string expression.
            thermal_conductivity: Optional thermal conductivity. Pass a float or string
                expression for isotropic, or a 3x3 matrix (list of 3 lists of 3
                floats/strings) for anisotropic.
            orientation: Optional orientation of the material.
                Can be a tuple of 3 floats or a string like "[90; 0; 0]"
            enabled: Optional enabled expression of the material.
                Can be a string expression like "eq(my_variable, 1)"

        Returns:
            The created material.
        """
        properties: List[MaterialProperty.PhysicalProperty] = []
        if coefficient_of_thermal_expansion is not None:
            if isinstance(coefficient_of_thermal_expansion, list):
                properties.append(
                    MaterialProperty.CoefficientOfThermalExpansionAnisotropic(
                        value=coefficient_of_thermal_expansion
                    )
                )
            else:
                properties.append(
                    MaterialProperty.CoefficientOfThermalExpansion(
                        value=coefficient_of_thermal_expansion,
                    )
                )
        if density is not None:
            properties.append(MaterialProperty.Density(value=density))
        if dynamic_viscosity is not None:
            if isinstance(dynamic_viscosity, list):
                properties.append(
                    MaterialProperty.DynamicViscosityAnisotropic(
                        value=dynamic_viscosity
                    )
                )
            else:
                properties.append(
                    MaterialProperty.DynamicViscosity(value=dynamic_viscosity)
                )
        if elasticity_matrix is not None:
            properties.append(elasticity_matrix)
        if electric_conductivity is not None:
            if isinstance(electric_conductivity, list):
                properties.append(
                    MaterialProperty.ElectricConductivityAnisotropic(
                        value=electric_conductivity
                    )
                )
            else:
                properties.append(
                    MaterialProperty.ElectricConductivity(value=electric_conductivity)
                )
        if electric_permittivity is not None:
            if isinstance(electric_permittivity, list):
                properties.append(
                    MaterialProperty.ElectricPermittivityAnisotropic(
                        value=electric_permittivity
                    )
                )
            else:
                properties.append(
                    MaterialProperty.ElectricPermittivity(value=electric_permittivity)
                )
        if heat_capacity is not None:
            properties.append(MaterialProperty.HeatCapacity(value=heat_capacity))
        if magnetic_permeability is not None:
            if isinstance(magnetic_permeability, list):
                properties.append(
                    MaterialProperty.MagneticPermeabilityAnisotropic(
                        value=magnetic_permeability
                    )
                )
            else:
                properties.append(
                    MaterialProperty.MagneticPermeability(value=magnetic_permeability)
                )
        if mass_damping_coefficient is not None:
            properties.append(
                MaterialProperty.MassDampingCoefficient(value=mass_damping_coefficient)
            )
        if piezoelectric_coupling is not None:
            properties.append(
                MaterialProperty.PiezoelectricCoupling(value=piezoelectric_coupling)
            )
        if prony_series is not None:
            properties.append(prony_series)
        if speed_of_sound is not None:
            properties.append(MaterialProperty.SpeedOfSound(value=speed_of_sound))
        if stiffness_damping_coefficient is not None:
            properties.append(
                MaterialProperty.StiffnessDampingCoefficient(
                    value=stiffness_damping_coefficient
                )
            )
        if thermal_conductivity is not None:
            if isinstance(thermal_conductivity, list):
                properties.append(
                    MaterialProperty.ThermalConductivityAnisotropic(
                        value=thermal_conductivity
                    )
                )
            else:
                properties.append(
                    MaterialProperty.ThermalConductivity(value=thermal_conductivity)
                )

        return Material.create(
            project_id=self._project.id,
            name=name,
            description=description,
            color=color,
            properties=properties,
            abbreviation=abbreviation,
            target_region=target_region,
            orientation=orientation,
            enabled=enabled,
        )

    @prevent_deleted
    def create_material_from_library(
        self,
        name: str,
        target_region: Region | None = None,
        enabled: str | None = None,
    ) -> Material:
        """
        Create a material from the library by name.

        Parameters:
            name: The name of the library material to copy.
            target_region: The target Region of the material.
            enabled: Optional enabled expression of the material.
                Can be a string expression like "eq(my_variable, 1)"

        Returns:
            The created Material.

        Raises:
            ValueError: If no library material with the given name is found.
        """
        return Material.create_from_library(
            name=name,
            target_region=target_region,
            enabled=enabled,
            project_id=self._project.id,
        )

    @prevent_deleted
    def save(self) -> None:
        """
        Explictly save the changes to the cloud made by
        setting properties like `name`, `description`, `pml_num_layers` and `pml_thickness`.
        """
        if self._uncommitted_update is not None:
            with get_api() as api:
                api.update_project(
                    authorization=get_auth(),
                    project_id=self._project.id,
                    new_project=self._uncommitted_update,
                )
                self._uncommitted_update = None

                self._project = api.get_project(
                    authorization=get_auth(),
                    project_id=self._project.id,
                )

    @prevent_deleted
    def delete(self) -> None:
        """
        Delete the project.
        """
        with get_api() as api:
            api.delete_project(
                authorization=get_auth(),
                project_id=self._project.id,
            )
        self._deleted = True

    @prevent_deleted
    def copy(
        self,
        with_results: bool = False,
        name: str | None = None,
        wait_for_completion: bool = True,
    ) -> Self:
        """
        Copies the project and returns the copied project.

        Parameters:
            with_results: If True then files of the original project are copied to the new project.
            name: The name of the new project.
            wait_for_completion: If True, the copied project is returned after the copy job is completed.
                If False, get_copy_job() should be used to check the status of the copy job.

        Returns:
            The copied project.

        Raises:
            ValueError: If authenticated with a project API key. Copying projects
                requires an organization API key.
        """
        if is_project_api_key():
            raise ValueError(
                "Operation not authorized with a project API key. "
                "Copying a project requires an organization API key."
            )

        with get_api() as api:
            project_data = api.copy_project(
                authorization=get_auth(),
                project_id=self._project.id,
                with_results=with_results,
                copy_request=rawapi.CopyRequest(
                    name=name,
                ),
            )
        copy = self.__class__(project_data)
        if wait_for_completion:
            copy._wait_for_copy()
        return copy

    @prevent_deleted
    def get_copy_job(self) -> Job | None:
        """
        Get the copy job for the project.
        The copy job exists only if the project was copied from another project with results.

        Returns:
            The copy job for the project.
        """
        return self._copy_files_job

    @prevent_deleted
    def _wait_for_copy(self, interval_s: float = 1) -> bool:
        """
        Wait for the project's file copy job to complete.

        Parameters:
            interval_s: Time in seconds between status refreshes.

        Returns:
            True if the copy job completed successfully or was already complete/non-existent,
            False if the copying failed.
        """
        if self._copy_files_job is None:
            return True

        while self._copy_files_job.is_running(interval_s):
            pass
        return self._copy_files_job.get_status() == Job.SUCCESS

    @prevent_deleted
    def export(
        self,
        include_meshes: bool = True,
        download_geometries: bool = False,
        files_output_dir: str | pathlib.Path = ".",
        file_overwrite_mode: FileOverwriteMode = FileOverwriteMode.SKIP,
    ) -> dict:
        """
        Export project data as a dictionary.

        The returned dict is compatible with import_project() and can be:
        - Modified programmatically before saving
        - Serialized to YAML or JSON
        - Used directly with import_project(data_dict, project_to_modify=...)

        Args:
            include_meshes: Whether to include mesh definitions (default True).
                Note: Exported meshes are definitions only; mesh data is not included.
            download_geometries: If True, download geometry import files into
                ``files_output_dir``. See ``export_project_data``.
            files_output_dir: Output directory when ``download_geometries`` is True.
            file_overwrite_mode: Controls behavior when a geometry file already
                exists on disk. ``FileOverwriteMode.SKIP`` (default) keeps the
                existing file, ``FileOverwriteMode.OVERWRITE`` replaces it, and
                ``FileOverwriteMode.ERROR`` raises ``FileExistsError``.

        Returns:
            Dictionary containing the project data.

        Note:
            Geometry file paths are placeholders unless ``download_geometries=True``.
            When re-importing without downloaded files, provide the files
            at the exported paths.

        Example:
            >>> project = Project.get("my-project-id")
            >>> data = project.export()
            >>> data["name"] = "Modified Project"
            >>> # Re-import to new project
            >>> from allsolve import import_project
            >>> new_project = import_project(data)
        """
        from .export_project import export_project_data

        if self.geometry_pipeline_version == GeometryPipelineVersion.V1:
            warnings.warn(
                "Exporting a project with geometry pipeline V1. "
                "V1 does not support exporting geometry elements. "
                "Consider upgrading to geometry pipeline V2 for full export support.",
                UserWarning,
                stacklevel=2,
            )

        return export_project_data(
            self,
            include_meshes=include_meshes,
            download_geometries=download_geometries,
            files_output_dir=files_output_dir,
            file_overwrite_mode=file_overwrite_mode,
        )

    @prevent_deleted
    def export_yaml(
        self,
        output_path: str,
        include_meshes: bool = True,
        download_geometries: bool = False,
        files_output_dir: str | pathlib.Path | None = None,
        file_overwrite_mode: FileOverwriteMode = FileOverwriteMode.SKIP,
    ) -> None:
        """
        Export project to a YAML file.

        Args:
            output_path: Path to write the YAML file.
            include_meshes: Whether to include mesh definitions (default True).
            download_geometries: If True, download geometry CAD files; see ``export()``.
            files_output_dir: Directory for downloads. When ``download_geometries`` is True
                and this is omitted, defaults to the parent directory of ``output_path``.
            file_overwrite_mode: Controls behavior when a geometry file already
                exists on disk. ``FileOverwriteMode.SKIP`` (default) keeps the
                existing file, ``FileOverwriteMode.OVERWRITE`` replaces it, and
                ``FileOverwriteMode.ERROR`` raises ``FileExistsError``.

        Note:
            See ``export()`` for CAD path and ``download_geometries`` behavior.

        Example:
            >>> project = Project.get("my-project-id")
            >>> project.export_yaml("./my_project.yaml")
        """
        import yaml

        if download_geometries:
            effective_dir = files_output_dir
            if effective_dir is None:
                effective_dir = pathlib.Path(output_path).expanduser().resolve().parent
            data = self.export(
                include_meshes=include_meshes,
                download_geometries=True,
                files_output_dir=effective_dir,
                file_overwrite_mode=file_overwrite_mode,
            )
        else:
            data = self.export(include_meshes=include_meshes)
        with open(output_path, "w") as f:
            yaml.dump(
                data, f, default_flow_style=False, sort_keys=False, allow_unicode=True
            )

    @prevent_deleted
    def export_json(
        self,
        output_path: str,
        include_meshes: bool = True,
        indent: int = 2,
        download_geometries: bool = False,
        files_output_dir: str | pathlib.Path | None = None,
        file_overwrite_mode: FileOverwriteMode = FileOverwriteMode.SKIP,
    ) -> None:
        """
        Export project to a JSON file.

        Args:
            output_path: Path to write the JSON file.
            include_meshes: Whether to include mesh definitions (default True).
            indent: JSON indentation level (default 2).
            download_geometries: If True, download geometry CAD files; see ``export()``.
            files_output_dir: Directory for downloads. When ``download_geometries`` is True
                and this is omitted, defaults to the parent directory of ``output_path``.
            file_overwrite_mode: Controls behavior when a geometry file already
                exists on disk. ``FileOverwriteMode.SKIP`` (default) keeps the
                existing file, ``FileOverwriteMode.OVERWRITE`` replaces it, and
                ``FileOverwriteMode.ERROR`` raises ``FileExistsError``.

        Note:
            See ``export()`` for CAD path and ``download_geometries`` behavior.

        Example:
            >>> project = Project.get("my-project-id")
            >>> project.export_json("./my_project.json")
        """
        if download_geometries:
            effective_dir = files_output_dir
            if effective_dir is None:
                effective_dir = pathlib.Path(output_path).expanduser().resolve().parent
            data = self.export(
                include_meshes=include_meshes,
                download_geometries=True,
                files_output_dir=effective_dir,
                file_overwrite_mode=file_overwrite_mode,
            )
        else:
            data = self.export(include_meshes=include_meshes)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=indent)

    def __str__(self) -> str:
        return f"Project(name={self.name}, id={self.id}, description={self.description}, readonly={self.readonly})"

    def __repr__(self) -> str:
        parts = [f"id={self._project.id!r}", f"name={self._project.name!r}"]
        if self._deleted:
            parts.append("deleted=True")
        return f"Project({', '.join(parts)})"
