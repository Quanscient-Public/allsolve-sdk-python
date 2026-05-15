# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing_extensions import Self, List, TextIO
import sys
import pathlib
import json
import time
import uuid
from enum import Enum

from allsolve.physics import OutputInteraction
from allsolve.physics.physic import Field
from allsolve.override import VariableOverrides
from allsolve.simulation.simulation_output_data import CsvExportFormat

from . import SimulationOutputData
import allsolve_rawapi as rawapi

from ..util import JobError, NotInitializedError, prevent_deleted
from ..job_mixin import JobMixin
from ..api import (
    check_for_project_api_key,
    get_allow_insecure_http,
    get_api,
    get_auth,
    get_http_session,
)
from ..http_transfer import CONNECT_TIMEOUT_S, TRANSFER_TIMEOUT_S, validate_url_scheme
from ..file import create_file, upload_file, upload_bytes
from ..job import Job, OnError

_GENERATED_HELPER_MODULES = (
    "utils",
    "tagmappings",
    "regions",
    "expressions",
    "materials",
    "parameters",
)


def _import_to_string(imp: rawapi.PythonScriptImport) -> str:
    if imp.attrs and len(imp.attrs) > 0:
        return f"from {imp.module} import {', '.join(imp.attrs)}"
    elif imp.module_alias:
        return f"import {imp.module} as {imp.module_alias}"
    else:
        return f"import {imp.module}"


class CPU(Enum):
    """
    Compute instance size used to run a simulation.

    Each member specifies the number of CPU cores and available RAM.
    """

    DEFAULT = None
    """The default instance size."""

    CORES_1_16GB = "large-new"
    """1 CPU core, 16 GB RAM."""

    CORES_2_32GB = "xlarge-new"
    """2 CPU cores, 32 GB RAM."""

    CORES_3_10GB_FAST_START = "lambda"
    """3 CPU cores, 10 GB RAM — optimised for fast start."""

    CORES_4_64GB = "2xlarge-new"
    """4 CPU cores, 64 GB RAM."""

    CORES_8_128GB = "4xlarge-new"
    """8 CPU cores, 128 GB RAM."""

    CORES_16_256GB = "8xlarge-new"
    """16 CPU cores, 256 GB RAM."""

    CORES_32_512GB = "16xlarge-new"
    """32 CPU cores, 512 GB RAM."""


class Runtime:
    """
    Runtime for a simulation.
    """

    def __init__(
        self, node_count: int = 1, node_type: CPU = CPU.CORES_3_10GB_FAST_START
    ) -> None:
        self._node_count: int = node_count
        self._node_type: CPU = node_type

    @property
    def node_count(self) -> int:
        return self._node_count

    @property
    def node_type(self) -> CPU:
        return self._node_type


class DisableableSection(Enum):
    """
    Enum for generated simulation script sections that can be disabled.
    The generated script can be seen in Allsolve GUI.

    A simulation script is generated from the project configuration. It consists of
    generated sections interleaved with custom injection
    points (see ``CustomSection``). Disabling a generated section causes its code to
    be emitted as comments, allowing users to replace it entirely using the surrounding
    custom sections.

    Use ``Simulation.disabled_script_sections`` to disable sections.

    Values:

    - ``SETUP`` -- Namespace declarations (variables, mesh, fields, etc.) and
      pre-mesh configuration.
    - ``MESH`` -- Mesh loading, PML layers, skin meshes, partitioning.
    - ``FIELDS`` -- Field creation for all physics.
    - ``DERIVED_FIELDS`` -- Derived field definitions.
    - ``CONSTRAINTS`` -- Physics boundary conditions and constraints.
    - ``PORTS`` -- Port and lump interaction definitions.
    - ``FIELD_INITS`` -- Field state initializations (initial conditions).
    - ``FORMULATIONS`` -- Formulation assembly and regular interaction definitions.
    - ``SOLVE`` -- Solver execution (transient loop, eigenvalue solve, or
      steady-state solve).
    """

    SETUP = rawapi.DisabledScriptSection.SETUP
    MESH = rawapi.DisabledScriptSection.MESH
    FIELDS = rawapi.DisabledScriptSection.FIELDS
    DERIVED_FIELDS = rawapi.DisabledScriptSection.DERIVEDFIELDS
    CONSTRAINTS = rawapi.DisabledScriptSection.CONSTRAINTS
    PORTS = rawapi.DisabledScriptSection.PORTS
    FIELD_INITS = rawapi.DisabledScriptSection.FIELDINITS
    FORMULATIONS = rawapi.DisabledScriptSection.FORMULATIONS
    SOLVE = rawapi.DisabledScriptSection.SOLVE


class CustomSection(Enum):
    """
    Enum for injection points for custom Python code in the generated simulation script.
    The generated script can be seen in Allsolve GUI.

    A simulation script is composed of generated sections interleaved with custom
    sections. Custom sections let you insert your own Python code at specific points
    in the script. Use ``Simulation.set_scripts`` to assign code to a section.

    Script structure example::


        # imports
        import quanscient as qs
        from utils import Mesh, Variables, Empty, Fields, DerivedFields

        # AFTER_IMPORTS

        # setup
        var = Variables()
        mesh = Mesh()

        # BEFORE_MESH_LOAD

        # mesh
        mesh.mesh = qs.mesh()
        mesh.mesh.setphysicalregions(*reg.get_region_data())

        # AFTER_MESH_LOAD

        # fields
        fld.u = qs.field("h1xyz", [1])
        fld.u.setorder(reg.all, 2)

        # AFTER_FIELDS_CREATED

        # derivedFields
        df.sigma = qs.parameter(6, 1)
        df.vm = qs.parameter(1, 1)

        # AFTER_DERIVED_FIELDS_CREATED

        # constraints
        fld.u.setconstraint(reg.clamp)

        # AFTER_CONSTRAINTS_CREATED

        # ports
        port.lump.V = qs.port([2, 3])

        # AFTER_PORTS_CREATED

        # fieldInits

        # AFTER_FIELD_INITS

        # formulations
        form = qs.formulation()
        form += qs.integral(reg.solid_mechanics, qs.predefinedelasticity(qs.dof(fld.u), qs.tf(fld.u), par.H()))

        # AFTER_FORMULATIONS_CREATED

        # solve. Contains analysis-type-specific sub-sections
        form.allsolve(relrestol=1e-06, maxnumit=1000, nltol=1e-05, maxnumnlit=-1, relaxvalue=-1)

        # AFTER_SOLVE and other analysis-type-specific sections

        #AFTER_ALL

    Values:

    - ``AFTER_IMPORTS`` -- After all module imports. Import additional Python
      modules or define global variables.
    - ``BEFORE_MESH_LOAD`` -- After setup (namespace and variable declarations).
      Modify setup variables before mesh loading.
    - ``AFTER_MESH_LOAD`` -- After the mesh is loaded and partitioned. Inspect or
      modify the mesh object.
    - ``AFTER_FIELDS_CREATED`` -- After all fields are created. Modify field
      properties or add custom fields.
    - ``AFTER_DERIVED_FIELDS_CREATED`` -- After derived fields are created. Modify
      derived field definitions.
    - ``AFTER_CONSTRAINTS_CREATED`` -- After physics constraints are applied. Add
      or modify boundary conditions.
    - ``AFTER_PORTS_CREATED`` -- After port/lump interaction definitions. Modify
      port configurations.
    - ``AFTER_FIELD_INITS`` -- After field state initializations. Override initial
      conditions.
    - ``AFTER_FORMULATIONS_CREATED`` -- After formulations and regular interactions
      are created. Modify the formulation before solving.
    - ``AFTER_SOLVE`` -- After the solve section.
    - ``AFTER_ALL`` -- After the solve section and all outputs. Post-processing,
      custom outputs, or cleanup.

    Analysis-type-specific sections (only available when the analysis type
    matches):

    - ``AFTER_TIMESTEPPER_CREATED`` -- Transient only. After the timestepper is
      created and configured, before the time loop.
    - ``BEFORE_TRANSIENT_SOLVE`` -- Transient only. Inside the time loop, before
      each solve step. Update time-dependent parameters or log per-step info.
    - ``AFTER_EIGENVALUE_SOLVER_CREATED`` -- Eigenmode only. After the eigenvalue
      solver is created, before eigenfrequency computation.
    - ``AFTER_SOLVE_REAL`` -- Eigenmode only. After the real part of the
      eigenmode solve.
    - ``AFTER_SOLVE_IMAGINARY`` -- Eigenmode only. After the imaginary part of
      the eigenmode solve.
    """

    AFTER_IMPORTS = rawapi.CustomScriptSectionName.AFTERIMPORTS
    BEFORE_MESH_LOAD = rawapi.CustomScriptSectionName.BEFOREMESHLOAD
    AFTER_MESH_LOAD = rawapi.CustomScriptSectionName.AFTERMESHLOAD
    AFTER_FIELDS_CREATED = rawapi.CustomScriptSectionName.AFTERFIELDSCREATED
    AFTER_DERIVED_FIELDS_CREATED = (
        rawapi.CustomScriptSectionName.AFTERDERIVEDFIELDSCREATED
    )
    AFTER_CONSTRAINTS_CREATED = rawapi.CustomScriptSectionName.AFTERCONSTRAINTSCREATED
    AFTER_PORTS_CREATED = rawapi.CustomScriptSectionName.AFTERPORTSCREATED
    AFTER_FIELD_INITS = rawapi.CustomScriptSectionName.AFTERFIELDINITS
    AFTER_FORMULATIONS_CREATED = rawapi.CustomScriptSectionName.AFTERFORMULATIONSCREATED
    AFTER_TIMESTEPPER_CREATED = rawapi.CustomScriptSectionName.AFTERTIMESTEPPERCREATED
    BEFORE_TRANSIENT_SOLVE = rawapi.CustomScriptSectionName.BEFORETRANSIENTSOLVE
    AFTER_EIGENVALUE_SOLVER_CREATED = (
        rawapi.CustomScriptSectionName.AFTEREIGENVALUESOLVERCREATED
    )
    AFTER_SOLVE = rawapi.CustomScriptSectionName.AFTERSOLVE
    AFTER_SOLVE_REAL = rawapi.CustomScriptSectionName.AFTERSOLVEREAL
    AFTER_SOLVE_IMAGINARY = rawapi.CustomScriptSectionName.AFTERSOLVEIMAGINARY
    AFTER_ALL = rawapi.CustomScriptSectionName.AFTERALL


_SECTION_REQUIRED_ANALYSIS_TYPE: dict["CustomSection", rawapi.AnalysisType] = {
    CustomSection.AFTER_TIMESTEPPER_CREATED: rawapi.AnalysisType.TRANSIENT,
    CustomSection.BEFORE_TRANSIENT_SOLVE: rawapi.AnalysisType.TRANSIENT,
    CustomSection.AFTER_EIGENVALUE_SOLVER_CREATED: rawapi.AnalysisType.EIGENMODE,
    CustomSection.AFTER_SOLVE_REAL: rawapi.AnalysisType.EIGENMODE,
    CustomSection.AFTER_SOLVE_IMAGINARY: rawapi.AnalysisType.EIGENMODE,
}


class Script:
    """
    A script attached to a simulation.

    The script can be a custom section script, a module, or a main script replacement.

    - Custom section script: Injects code at a specific ``CustomSection`` point in
      the generated simulation script. Set ``section_name`` to the desired
      injection point.
    - Module: A helper file that other scripts can import. Created when
      ``section_name`` is ``None`` and ``is_main`` is ``False`` (the defaults).
    - Main script replacement: Replaces the entire generated main script
      with your own. Set ``is_main=True``.

    Provide code via ``content`` (inline string) or ``filepath`` (path to a ``.py``
    file on disk). When using ``filepath``, the file is read at the time
    ``Simulation.set_scripts`` is called.

    Parameters:
        filepath: Path to a ``.py`` file whose contents will be used as the script.
        is_main: If ``True``, this script replaces the generated main script.
        section_name: The ``CustomSection`` injection point where this script's
            code will be inserted. ``None`` for main scripts and modules.
        name: Script file name (e.g. ``"afterMeshLoad.py"``). Required when using
            ``content``; inferred from ``filepath`` otherwise. A ``.py`` suffix is
            added automatically if missing.
        content: Inline Python code as a string.

    Example::

        # Custom section script
        sim.set_scripts([
            allsolve.Script(
                name="afterMeshLoad.py",
                section_name=allsolve.CustomSection.AFTER_MESH_LOAD,
                content="print('mesh loaded')",
            )
        ])
    """

    def __init__(
        self,
        filepath: str | None = None,
        is_main: bool = False,
        section_name: CustomSection | None = None,
        name: str | None = None,
        origin: str | None = None,
        content: str | None = None,
    ) -> None:
        self._filepath: str | None = filepath
        self._is_main: bool = is_main
        self._section_name: CustomSection | None = section_name
        self._name: str | None = name
        self._origin: str | None = origin
        self._content: str | None = content

    @property
    def filepath(self) -> str | None:
        return self._filepath

    @property
    def is_main(self) -> bool:
        return self._is_main

    @property
    def section_name(self) -> CustomSection | None:
        return self._section_name

    @property
    def name(self) -> str | None:
        return self._name

    @property
    def origin(self) -> str | None:
        return self._origin

    @property
    def content(self) -> str | None:
        return self._content


class FieldInitialization:
    """
    A field initialization for a simulation.

    Initializes a simulation field from the output of another simulation.

    Parameters:
        type: The type of field initialization.
        source_simulation: The source simulation (``Simulation`` object or
            simulation ID string) whose output is used.
        source_output_name: Source simulation's field state output name.
        field: The field to initialize (``Field`` object or field ID string).
            ``None`` is only allowed when ``type`` is ``TRANSIENTSTATE`` or
            ``HPHISTATE``; for other types a field must be specified.
        source_output_specifier: Optional specifier of the field.
            Some field states are saved in multiple parts. Each part is
            specified with a specifier. For example in eigenmode simulations,
            a field has both real and imaginary parts. In that case the field
            needs to be initialized with two field initializations: one where
            the specifier is "real" and one where the specifier is "imaginary".
        source_sweep_step: If specified, the initialization is taken from
            this sweep step. The source simulation must be a sweep with enough
            steps.
        source_step: If specified, the initialization is taken from this
            step (time step, eigenvalue index, etc.) of the source simulation.
        harmonic: If specified, only this harmonic of the field is initialized.

    Example::

        sim.set_field_initializations([
            allsolve.FieldInitialization(
                type=allsolve.FieldInitializationType.FIELDSTATE,
                source_simulation=source_sim,
                source_output_name="u",
                field=solid_mechanics_physics.fields[0]
            )
        ])
    """

    _FIELD_OPTIONAL_TYPES = frozenset(
        {
            rawapi.FieldInitializationType.TRANSIENTSTATE,
            rawapi.FieldInitializationType.HPHISTATE,
        }
    )

    def __init__(
        self,
        type: rawapi.FieldInitializationType,
        source_simulation: Simulation | str,
        source_output_name: str,
        field: Field | str | None = None,
        source_output_specifier: str | None = None,
        source_sweep_step: int | None = None,
        source_step: str | None = None,
        harmonic: int | None = None,
    ) -> None:
        if field is None and type not in self._FIELD_OPTIONAL_TYPES:
            raise ValueError(
                f"'field' is required for type {type!r}; "
                f"it may only be None for TRANSIENTSTATE or HPHISTATE"
            )
        self._type = type
        self._source_simulation_id = (
            source_simulation
            if isinstance(source_simulation, str)
            else source_simulation.id
        )
        self._source_output_name = source_output_name
        self._field_id: str | None = (
            None if field is None else field if isinstance(field, str) else field.id
        )
        self._source_output_specifier = source_output_specifier
        self._source_sweep_step = source_sweep_step
        self._source_step = source_step
        self._harmonic = harmonic

    def __repr__(self) -> str:
        parts = [
            f"type={self._type!r}",
            f"source_simulation={self._source_simulation_id!r}",
            f"source_output_name={self._source_output_name!r}",
        ]
        if self._field_id is not None:
            parts.append(f"field={self._field_id!r}")
        if self._source_output_specifier is not None:
            parts.append(f"source_output_specifier={self._source_output_specifier!r}")
        if self._source_sweep_step is not None:
            parts.append(f"source_sweep_step={self._source_sweep_step!r}")
        if self._source_step is not None:
            parts.append(f"source_step={self._source_step!r}")
        if self._harmonic is not None:
            parts.append(f"harmonic={self._harmonic!r}")
        return f"FieldInitialization({', '.join(parts)})"

    @property
    def type(self) -> rawapi.FieldInitializationType:
        return self._type

    @property
    def source_simulation_id(self) -> str:
        """ID of the source simulation."""
        return self._source_simulation_id

    @property
    def source_output_name(self) -> str:
        return self._source_output_name

    @property
    def field_id(self) -> str | None:
        """ID of the field to initialize, or ``None`` for TRANSIENTSTATE/HPHISTATE."""
        return self._field_id

    @property
    def source_output_specifier(self) -> str | None:
        return self._source_output_specifier

    @property
    def source_sweep_step(self) -> int | None:
        return self._source_sweep_step

    @property
    def source_step(self) -> str | None:
        return self._source_step

    @property
    def harmonic(self) -> int | None:
        return self._harmonic

    @classmethod
    def _from_rawapi(cls, raw: rawapi.FieldInitialization) -> Self:
        return cls(
            type=raw.type,
            field=raw.field_id,
            source_simulation=raw.init_value_simulation_id,
            source_output_name=raw.init_value_output_name,
            source_output_specifier=raw.init_value_output_specifier,
            source_sweep_step=raw.init_value_sweep_step,
            source_step=raw.init_value_step,
            harmonic=raw.harmonic,
        )

    def _to_rawapi(self) -> rawapi.FieldInitializationUpdate:
        return rawapi.FieldInitializationUpdate(
            type=self._type,
            fieldId=self._field_id,
            initValueSimulationId=self._source_simulation_id,
            initValueOutputName=self._source_output_name,
            initValueOutputSpecifier=self._source_output_specifier,
            initValueSweepStep=self._source_sweep_step,
            initValueStep=self._source_step,
            harmonic=self._harmonic,
        )


class SolverMode:
    """
    Solver mode for a simulation.
    """

    DIRECT = rawapi.DistributedSolverMode.DIRECT
    ITERATIVE = rawapi.DistributedSolverMode.ITERATIVE


class TimestepAlgorithm:
    """
    Timestep algorithm for a transient simulation.
    """

    IMPLICIT_EULER = rawapi.TimestepAlgorithm.IMPLICITEULER
    GEN_ALPHA = rawapi.TimestepAlgorithm.GENALPHA


class AnalysisType:
    """
    Simulation analysis type.
    """

    STATIC = rawapi.AnalysisType.STEADYSTATE
    HARMONIC = rawapi.AnalysisType.HARMONIC
    MULTIHARMONIC = rawapi.AnalysisType.MULTIHARMONIC
    TRANSIENT = rawapi.AnalysisType.TRANSIENT
    EIGENMODE = rawapi.AnalysisType.EIGENMODE


class Simulation(JobMixin):
    """
    Simulation of a project.
    """

    # TODO: These will be removed. Use constants from job.py instead.
    SUCCESS = rawapi.JobStatusType.SUCCESS
    RUNNING = rawapi.JobStatusType.RUNNING
    ABORTED = rawapi.JobStatusType.ABORTED
    ABORTING = rawapi.JobStatusType.ABORTING
    ERROR = rawapi.JobStatusType.ERROR
    FAILING = rawapi.JobStatusType.FAILING
    PROCESSING_OUTPUT = rawapi.JobStatusType.PROCESSING_OUTPUT
    QUEUED = rawapi.JobStatusType.QUEUED
    SUBMITTED = rawapi.JobStatusType.SUBMITTED
    PARTIAL_SUCCESS = rawapi.JobStatusType.PARTIAL_SUCCESS
    STARTING = rawapi.JobStatusType.STARTING
    NOT_STARTED = None

    @classmethod
    def get(cls, simulation_id: str, project_id: str | None = None) -> Self:
        """
        Get a simulation by its ID.

        Parameters:
            simulation_id: The ID of the simulation.
            project_id: The ID of the project. Can be omitted if project API key is used.

        Returns:
            The simulation.
        """
        project_id = check_for_project_api_key(project_id)
        with get_api() as api:
            simulation = api.get_simulation(
                authorization=get_auth(),
                project_id=project_id,
                simulation_id=simulation_id,
            )

        return cls(project_id, simulation)

    @classmethod
    def get_all(cls, project_id: str | None = None) -> List[Self]:
        """
        Get all simulations in the given project.

        Parameters:
            project_id: The ID of the project. Can be omitted if project API key is used.

        Returns:
            A list of simulations.
        """
        project_id = check_for_project_api_key(project_id)
        with get_api() as api:
            simulations = api.get_simulation_list(
                authorization=get_auth(),
                project_id=project_id,
            )

        return [cls(project_id, s) for s in simulations]

    @classmethod
    def from_template(
        cls,
        by_id: str | None = None,
        by_name: str | None = None,
        project_id: str | None = None,
    ) -> Self:
        print(
            "Deprecated. The function `Simulation.from_template()` will be removed"
            " in a future version. Use `Simulation.get(...).copy()` instead."
        )
        if by_id is not None and by_name is not None:
            raise ValueError("Only one of (by_id, by_name) arguments is allowed")
        elif by_name is None and by_id is None:
            raise ValueError("One of the arguments (by_id, by_name) must be given")
        elif by_id is None:
            raise NotImplementedError("Argument by_name not implemented yet")

        project_id = check_for_project_api_key(project_id)
        with get_api() as api:
            simulation = api.create_simulation(
                authorization=get_auth(), project_id=project_id, template=by_id, body={}
            )

        return cls(project_id, simulation)

    @classmethod
    def copy_simulation(cls, simulation_id: str, project_id: str | None = None) -> Self:
        """
        Make a copy of the given simulation identified by its ID. Useful for creating simulations from a template.

        Parameters:
            simulation_id: The id of the source simulation.
            project_id: The id of the project where the source and target
                simulation exist. If project API key is used, this is optional.

        Returns:
            The copied simulation.
        """
        project_id = check_for_project_api_key(project_id)
        with get_api() as api:
            simulation = api.create_simulation(
                authorization=get_auth(),
                project_id=project_id,
                template=simulation_id,
                body={},
            )

        return cls(project_id, simulation)

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        max_run_time_minutes: int,
        solver_mode: rawapi.DistributedSolverMode,
        mesh_id: str | None = None,
        variable_overrides_id: str | None = None,
        analysis_type: rawapi.AnalysisType | None = None,
        harmonics: List[int] | None = None,
        physics: List[str] | None = None,
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
        project_id: str | None = None,
    ) -> Self:
        """
        Create a new simulation in the given project.

        Parameters:
            name: The name of the new simulation.
            description: The description of the new simulation.
            max_run_time_minutes: The maximum run time of the simulation.
            solver_mode: The solver mode of the simulation.
            mesh_id: The ID of the mesh to use in the simulation.
            variable_overrides_id: The optional ID of the VariableOverrides to use in the simulation.
            analysis_type: The analysis type of the simulation. Defaults to STATIC.
            harmonics: The harmonics of the simulation.
            physics: List of physics IDs to simulate.
            transient_start_time: The transient start time expression (for transient simulations).
            transient_end_time: The transient end time expression (for transient simulations).
            transient_timestep_size: The transient timestep size expression (for transient simulations).
            timestep_algorithm: The timestep algorithm (for transient simulations).
            fundamental_frequency: The fundamental frequency expression (for harmonic simulations).
            num_fft_samples: The number of FFT samples (minimum 3).
            num_requested_eigenmodes: The number of requested eigenmodes expression.
            target_eigenfrequency: The target eigenfrequency expression.
            eigenmode_port_analysis: Whether eigenmode port analysis is enabled.
            solver_tolerance: The solver tolerance expression.
            nonlinear_solver_tolerance: The nonlinear solver tolerance expression.
            nonlinear_solver_max_iterations: The nonlinear solver maximum iterations expression.
            eigenmode_solver_tolerance: The eigenmode solver tolerance expression.
            eigenmode_solver_max_iterations: The eigenmode solver maximum iterations expression.
            target_frequency: The target frequency expression.
            numerical_jacobian: Whether numerical Jacobian is enabled.
            project_id: The id of the project where the new simulation should
                be created. If project API key is used, this is optional.

        Returns:
            The created simulation.
        """
        project_id = check_for_project_api_key(project_id)

        if analysis_type is None:
            analysis_type = rawapi.AnalysisType.STEADYSTATE
        if analysis_type is rawapi.AnalysisType.STEADYSTATE:
            harmonics = [1]
        elif analysis_type is rawapi.AnalysisType.HARMONIC:
            harmonics = [2, 3]

        with get_api() as api:
            simulation = api.create_simulation(
                authorization=get_auth(),
                project_id=project_id,
                body={},
            )

            api.update_simulation(
                authorization=get_auth(),
                project_id=project_id,
                simulation_id=simulation.id,
                simulation_update=rawapi.SimulationUpdate(
                    name=name,
                    description=description,
                    maxRunTimeMinutes=max_run_time_minutes,
                    solverMode=solver_mode,
                    analysisType=analysis_type,
                    harmonics=harmonics,
                    mesh=mesh_id,
                    overrideSet=variable_overrides_id,
                    physics=physics,
                    internalStartTime=transient_start_time,
                    internalEndTime=transient_end_time,
                    internalTimestepSize=transient_timestep_size,
                    timestepAlgorithm=timestep_algorithm,
                    fundamentalFrequency=fundamental_frequency,
                    numFFTSamples=num_fft_samples,
                    numRequestedEigenmodes=num_requested_eigenmodes,
                    targetEigenfrequency=target_eigenfrequency,
                    eigenmodePortAnalysis=eigenmode_port_analysis,
                    solverTolerance=solver_tolerance,
                    nonlinearSolverTolerance=nonlinear_solver_tolerance,
                    nonlinearSolverMaxIterations=nonlinear_solver_max_iterations,
                    eigenmodeSolverTolerance=eigenmode_solver_tolerance,
                    eigenmodeSolverMaxIterations=eigenmode_solver_max_iterations,
                    targetFrequency=target_frequency,
                    numericalJacobian=numerical_jacobian,
                ),
            )
            simulation = api.get_simulation(
                authorization=get_auth(),
                project_id=project_id,
                simulation_id=simulation.id,
            )

        return cls(project_id, simulation)

    def __init__(
        self,
        project_id: str,
        simulation: rawapi.Simulation,
    ) -> None:
        self._project_id: str = project_id
        self._simulation: rawapi.Simulation = simulation
        self._job: Job | None = None
        if simulation.simulation_job is not None:
            self._job = Job(project_id, simulation.simulation_job.id)
        self._shared_files: List[rawapi.InputFile] = []
        self._uncommitted_update: rawapi.SimulationUpdate | None = None
        self._deleted: bool = False
        self._output_data: SimulationOutputData | None = None

    @prevent_deleted
    def _refresh(self) -> None:
        with get_api() as api:
            self._simulation = api.get_simulation(
                authorization=get_auth(),
                project_id=self._project_id,
                simulation_id=self.id,
            )
            if self._simulation.simulation_job is not None:
                if (
                    self._job is None
                    or self._job.id != self._simulation.simulation_job.id
                ):
                    self._job = Job(
                        self._project_id, self._simulation.simulation_job.id
                    )
            else:
                self._job = None

    @property
    @prevent_deleted
    def id(self) -> str:
        """Get the ID of the simulation."""
        return self._simulation.id

    @property
    @prevent_deleted
    def name(self) -> str:
        """Get the name of the simulation."""
        return self._simulation.name

    @name.setter
    @prevent_deleted
    def name(self, name: str) -> None:
        """Set the name of the simulation."""
        self._current_uncommitted_update().name = name

    @property
    @prevent_deleted
    def description(self) -> str | None:
        """Get the description of the simulation."""
        return self._simulation.description

    @description.setter
    @prevent_deleted
    def description(self, description: str) -> None:
        """Set the description of the simulation."""
        self._current_uncommitted_update().description = description

    @property
    @prevent_deleted
    def mesh_id(self) -> str | None:
        """Get the ID of the mesh used in the simulation."""
        return self._simulation.mesh

    @mesh_id.setter
    @prevent_deleted
    def mesh_id(self, mesh_id: str) -> None:
        """Set the ID of the mesh used in the simulation."""
        self._current_uncommitted_update().mesh = mesh_id

    @property
    @prevent_deleted
    def max_run_time_minutes(self) -> int:
        """Get the maximum run time of the simulation."""
        return self._simulation.max_run_time_minutes

    @max_run_time_minutes.setter
    @prevent_deleted
    def max_run_time_minutes(self, max_run_time_minutes: int) -> None:
        """Set the maximum run time of the simulation."""
        self._current_uncommitted_update().max_run_time_minutes = max_run_time_minutes

    @property
    @prevent_deleted
    def solver_mode(self) -> rawapi.DistributedSolverMode:
        """Get the solver mode of the simulation."""
        return self._simulation.solver_mode

    @solver_mode.setter
    @prevent_deleted
    def solver_mode(self, solver_mode: rawapi.DistributedSolverMode) -> None:
        """Set the solver mode of the simulation."""
        self._current_uncommitted_update().solver_mode = solver_mode

    @property
    @prevent_deleted
    def node_count(self) -> int | None:
        """Get the number of nodes used in the simulation."""
        return self._simulation.node_count

    @property
    @prevent_deleted
    def node_type(self) -> CPU:
        """Get the type of nodes used in the simulation."""
        return CPU(self._simulation.node_type)

    @property
    @prevent_deleted
    def shared_files(self) -> List[rawapi.InputFile]:
        """Get the shared files used in the simulation."""
        input_files = self.get_input_files()
        shared_file_ids = [
            f.source_extra_input_file_id
            for f in input_files
            if f.type == rawapi.SimulationInputFileType.EXTRAINPUTFILE
            and f.source_extra_input_file_id is not None
        ]

        if not shared_file_ids:
            self._shared_files = []
            return self._shared_files

        with get_api() as api:
            files = api.get_files(
                authorization=get_auth(),
                project_id=self._project_id,
            )
        self._shared_files = [f for f in files if f.id in shared_file_ids]

        return self._shared_files

    @property
    @prevent_deleted
    def files(self) -> List[rawapi.SimulationInputFile]:
        """Get the files used in the simulation."""
        return self._simulation.input_files

    @prevent_deleted
    def get_input_files(self) -> List[rawapi.SimulationInputFile]:
        """
        Get all input files used in the simulation.

        Returns:
            Unified list of all simulation input files.
        """
        with get_api() as api:
            input_files = api.get_simulation_input_files(
                authorization=get_auth(),
                project_id=self._project_id,
                simulation_id=self.id,
            )

        self._simulation.input_files = input_files
        return input_files

    @prevent_deleted
    def set_input_files(self, input_files: List[rawapi.SimulationInputFile]) -> None:
        """
        Set all input files used in the simulation.

        Any existing input files missing from the provided list are removed.

        Parameters:
            input_files: Full list of input files to use in the simulation.
        """
        self._update_all_input_files(input_files)

    @property
    @prevent_deleted
    def variable_overrides(self) -> VariableOverrides | None:
        """Get the variable overrides of the simulation."""
        if self._simulation.override_set is None:
            return None
        return VariableOverrides.get(
            variable_overrides_id=self._simulation.override_set,
            project_id=self._project_id,
        )

    @variable_overrides.setter
    @prevent_deleted
    def variable_overrides(self, variable_overrides: VariableOverrides | None) -> None:
        """Set the variable overrides of the simulation."""
        if variable_overrides is None:
            self._current_uncommitted_update().override_set = None
            return

        self._current_uncommitted_update().override_set = variable_overrides.id

    @property
    @prevent_deleted
    def analysis_type(self) -> rawapi.AnalysisType | None:
        """Get the analysis type of the simulation."""
        return self._simulation.analysis_type

    @analysis_type.setter
    @prevent_deleted
    def analysis_type(self, value: rawapi.AnalysisType | None) -> None:
        """Set the analysis type of the simulation."""
        self._current_uncommitted_update().analysis_type = value

    @property
    @prevent_deleted
    def harmonics(self) -> List[int] | None:
        """Get the harmonics of the simulation."""
        return self._simulation.harmonics

    @harmonics.setter
    @prevent_deleted
    def harmonics(self, value: List[int] | None) -> None:
        """Set the harmonics of the simulation."""
        self._current_uncommitted_update().harmonics = value

    @property
    @prevent_deleted
    def disabled_script_sections(self) -> List[DisableableSection]:
        """
        Generated script sections that are currently disabled.

        When a section is disabled, its generated code is emitted as comments in
        the simulation script. This lets you replace the generated logic entirely
        by providing your own code in the surrounding ``CustomSection`` injection
        points.

        Returns:
            List of disabled sections.

        See Also:
            ``DisableableSection`` for the list of sections and what each one
            generates.
        """
        raw = self._simulation.disabled_script_sections
        if raw is None:
            return []
        return [DisableableSection(v) for v in raw]

    @disabled_script_sections.setter
    @prevent_deleted
    def disabled_script_sections(self, value: List[DisableableSection]) -> None:
        """
        Set which generated script sections to disable.

        Disabled sections have their generated code commented out, allowing you to
        replace them with custom code via ``Simulation.set_scripts``.

        Parameters:
            value: List of sections to disable.

        Example::

            sim.disabled_script_sections = [
                allsolve.DisableableSection.SETUP,
                allsolve.DisableableSection.MESH,
            ]
            sim.save()
        """
        if value is not None:
            self._current_uncommitted_update().disabled_script_sections = [
                v.value for v in value
            ]
        else:
            self._current_uncommitted_update().disabled_script_sections = None

    @property
    @prevent_deleted
    def physics(self) -> List[str] | None:
        """Get the list of physics IDs to simulate."""
        return self._simulation.physics

    @physics.setter
    @prevent_deleted
    def physics(self, value: List[str] | None) -> None:
        """Set the list of physics IDs to simulate."""
        self._current_uncommitted_update().physics = value

    @property
    @prevent_deleted
    def transient_start_time(self) -> str | None:
        """Get the transient start time expression."""
        return self._simulation.internal_start_time

    @transient_start_time.setter
    @prevent_deleted
    def transient_start_time(self, value: str | None) -> None:
        """Set the transient start time expression."""
        self._current_uncommitted_update().internal_start_time = value

    @property
    @prevent_deleted
    def transient_end_time(self) -> str | None:
        """Get the transient end time expression."""
        return self._simulation.internal_end_time

    @transient_end_time.setter
    @prevent_deleted
    def transient_end_time(self, value: str | None) -> None:
        """Set the transient end time expression."""
        self._current_uncommitted_update().internal_end_time = value

    @property
    @prevent_deleted
    def transient_timestep_size(self) -> str | None:
        """Get the transient timestep size expression."""
        return self._simulation.internal_timestep_size

    @transient_timestep_size.setter
    @prevent_deleted
    def transient_timestep_size(self, value: str | None) -> None:
        """Set the transient timestep size expression."""
        self._current_uncommitted_update().internal_timestep_size = value

    @property
    @prevent_deleted
    def timestep_algorithm(self) -> rawapi.TimestepAlgorithm | None:
        """Get the timestep algorithm."""
        return self._simulation.timestep_algorithm

    @timestep_algorithm.setter
    @prevent_deleted
    def timestep_algorithm(self, value: rawapi.TimestepAlgorithm | None) -> None:
        """Set the timestep algorithm."""
        self._current_uncommitted_update().timestep_algorithm = value

    @property
    @prevent_deleted
    def fundamental_frequency(self) -> str | None:
        """Get the fundamental frequency expression."""
        return self._simulation.fundamental_frequency

    @fundamental_frequency.setter
    @prevent_deleted
    def fundamental_frequency(self, value: str | None) -> None:
        """Set the fundamental frequency expression."""
        self._current_uncommitted_update().fundamental_frequency = value

    @property
    @prevent_deleted
    def num_fft_samples(self) -> int | None:
        """Get the number of FFT samples."""
        return self._simulation.num_fft_samples

    @num_fft_samples.setter
    @prevent_deleted
    def num_fft_samples(self, value: int | None) -> None:
        """Set the number of FFT samples (minimum 3)."""
        self._current_uncommitted_update().num_fft_samples = value

    @property
    @prevent_deleted
    def num_requested_eigenmodes(self) -> str | None:
        """Get the number of requested eigenmodes expression."""
        return self._simulation.num_requested_eigenmodes

    @num_requested_eigenmodes.setter
    @prevent_deleted
    def num_requested_eigenmodes(self, value: str | None) -> None:
        """Set the number of requested eigenmodes expression."""
        self._current_uncommitted_update().num_requested_eigenmodes = value

    @property
    @prevent_deleted
    def target_eigenfrequency(self) -> str | None:
        """Get the target eigenfrequency expression."""
        return self._simulation.target_eigenfrequency

    @target_eigenfrequency.setter
    @prevent_deleted
    def target_eigenfrequency(self, value: str | None) -> None:
        """Set the target eigenfrequency expression."""
        self._current_uncommitted_update().target_eigenfrequency = value

    @property
    @prevent_deleted
    def eigenmode_port_analysis(self) -> bool | None:
        """Get whether eigenmode port analysis is enabled."""
        return self._simulation.eigenmode_port_analysis

    @eigenmode_port_analysis.setter
    @prevent_deleted
    def eigenmode_port_analysis(self, value: bool | None) -> None:
        """Set whether eigenmode port analysis is enabled."""
        self._current_uncommitted_update().eigenmode_port_analysis = value

    @property
    @prevent_deleted
    def solver_tolerance(self) -> str | None:
        """Get the solver tolerance expression."""
        return self._simulation.solver_tolerance

    @solver_tolerance.setter
    @prevent_deleted
    def solver_tolerance(self, value: str | None) -> None:
        """Set the solver tolerance expression."""
        self._current_uncommitted_update().solver_tolerance = value

    @property
    @prevent_deleted
    def nonlinear_solver_tolerance(self) -> str | None:
        """Get the nonlinear solver tolerance expression."""
        return self._simulation.nonlinear_solver_tolerance

    @nonlinear_solver_tolerance.setter
    @prevent_deleted
    def nonlinear_solver_tolerance(self, value: str | None) -> None:
        """Set the nonlinear solver tolerance expression."""
        self._current_uncommitted_update().nonlinear_solver_tolerance = value

    @property
    @prevent_deleted
    def nonlinear_solver_max_iterations(self) -> str | None:
        """Get the nonlinear solver maximum iterations expression."""
        return self._simulation.nonlinear_solver_max_iterations

    @nonlinear_solver_max_iterations.setter
    @prevent_deleted
    def nonlinear_solver_max_iterations(self, value: str | None) -> None:
        """Set the nonlinear solver maximum iterations expression."""
        self._current_uncommitted_update().nonlinear_solver_max_iterations = value

    @property
    @prevent_deleted
    def eigenmode_solver_tolerance(self) -> str | None:
        """Get the eigenmode solver tolerance expression."""
        return self._simulation.eigenmode_solver_tolerance

    @eigenmode_solver_tolerance.setter
    @prevent_deleted
    def eigenmode_solver_tolerance(self, value: str | None) -> None:
        """Set the eigenmode solver tolerance expression."""
        self._current_uncommitted_update().eigenmode_solver_tolerance = value

    @property
    @prevent_deleted
    def eigenmode_solver_max_iterations(self) -> str | None:
        """Get the eigenmode solver maximum iterations expression."""
        return self._simulation.eigenmode_solver_max_iterations

    @eigenmode_solver_max_iterations.setter
    @prevent_deleted
    def eigenmode_solver_max_iterations(self, value: str | None) -> None:
        """Set the eigenmode solver maximum iterations expression."""
        self._current_uncommitted_update().eigenmode_solver_max_iterations = value

    @property
    @prevent_deleted
    def target_frequency(self) -> str | None:
        """Get the target frequency expression."""
        return self._simulation.target_frequency

    @target_frequency.setter
    @prevent_deleted
    def target_frequency(self, value: str | None) -> None:
        """Set the target frequency expression."""
        self._current_uncommitted_update().target_frequency = value

    @property
    @prevent_deleted
    def numerical_jacobian(self) -> bool | None:
        """Get whether numerical Jacobian is enabled."""
        return self._simulation.numerical_jacobian

    @numerical_jacobian.setter
    @prevent_deleted
    def numerical_jacobian(self, value: bool | None) -> None:
        """Set whether numerical Jacobian is enabled."""
        self._current_uncommitted_update().numerical_jacobian = value

    @property
    @prevent_deleted
    def field_initializations(self) -> List[FieldInitialization] | None:
        """Get the field initializations of the simulation."""
        raw = self._simulation.field_initializations
        if raw is None:
            return None
        return [FieldInitialization._from_rawapi(fi) for fi in raw]

    @prevent_deleted
    def set_field_initializations(
        self, field_initializations: List[FieldInitialization]
    ) -> None:
        """
        Set the field initializations of the simulation.

        All existing initializations are replaced with the provided ones.

        Parameters:
            field_initializations: List of field initializations to set.
        """
        updates = [fi._to_rawapi() for fi in field_initializations]
        with get_api() as api:
            self._simulation.field_initializations = (
                api.update_simulation_field_initializations(
                    authorization=get_auth(),
                    project_id=self._project_id,
                    simulation_id=self.id,
                    field_initialization_update=updates,
                )
            )

    @prevent_deleted
    def get_outputs(self) -> List[OutputInteraction]:
        """Get the output interactions of the simulation."""
        project_id = check_for_project_api_key(self._project_id)
        if self.id is None:
            raise ValueError("Simulation ID is not set")
        with get_api() as api:
            simulation = api.get_simulation(
                authorization=get_auth(),
                project_id=project_id,
                simulation_id=self.id,
            )
            if simulation.output_interactions is None:
                return []
            from allsolve.physics.generated.registries import get_output_class

            outputs: List[OutputInteraction] = []
            for interaction in simulation.output_interactions:
                subclass = get_output_class(interaction.definition)
                if subclass is None:
                    subclass = OutputInteraction
                outputs.append(
                    subclass._from_rawapi(
                        project_id=project_id,
                        interaction=interaction,
                        simulation_id=self.id,
                    )
                )
            return outputs

    @prevent_deleted
    def add_outputs(self, outputs: List[OutputInteraction]) -> List[OutputInteraction]:
        """Add output interactions to the simulation."""
        if self.id is None:
            raise ValueError("Simulation ID is not set")
        if not isinstance(outputs, list):
            raise ValueError("outputs must be a list of OutputInteraction instances")
        created: List[OutputInteraction] = []
        for output in outputs:
            if not isinstance(output, OutputInteraction):
                raise ValueError(
                    "All items in outputs must be OutputInteraction instances"
                )
            created.append(
                output._create_for_simulation(
                    simulation_id=self.id,
                    project_id=self._project_id,
                )
            )
        return created

    @prevent_deleted
    def _current_uncommitted_update(self) -> rawapi.SimulationUpdate:
        if self._uncommitted_update is None:
            self._uncommitted_update = rawapi.SimulationUpdate(
                name=self.name,
                description=self.description,
                maxRunTimeMinutes=self.max_run_time_minutes,
                nodeCount=self.node_count,
                nodeType=self.node_type.value,
                solverMode=self.solver_mode,
                overrideSet=self._simulation.override_set,
                analysisType=self._simulation.analysis_type,
                harmonics=self._simulation.harmonics,
                mesh=self.mesh_id,
                physics=self._simulation.physics,
                internalStartTime=self._simulation.internal_start_time,
                internalEndTime=self._simulation.internal_end_time,
                internalTimestepSize=self._simulation.internal_timestep_size,
                timestepAlgorithm=self._simulation.timestep_algorithm,
                fundamentalFrequency=self._simulation.fundamental_frequency,
                numFFTSamples=self._simulation.num_fft_samples,
                numRequestedEigenmodes=self._simulation.num_requested_eigenmodes,
                targetEigenfrequency=self._simulation.target_eigenfrequency,
                eigenmodePortAnalysis=self._simulation.eigenmode_port_analysis,
                solverTolerance=self._simulation.solver_tolerance,
                nonlinearSolverTolerance=self._simulation.nonlinear_solver_tolerance,
                nonlinearSolverMaxIterations=self._simulation.nonlinear_solver_max_iterations,
                eigenmodeSolverTolerance=self._simulation.eigenmode_solver_tolerance,
                eigenmodeSolverMaxIterations=self._simulation.eigenmode_solver_max_iterations,
                targetFrequency=self._simulation.target_frequency,
                numericalJacobian=self._simulation.numerical_jacobian,
                disabledScriptSections=self._simulation.disabled_script_sections,
            )

        return self._uncommitted_update

    @prevent_deleted
    def set_scripts(self, scripts: List[Script]) -> None:
        """
        Upload scripts attached to this simulation.

        Scripts can inject custom Python code at specific points in the generated
        simulation script (see ``CustomSection`` for the full list of injection
        points), or replace the main script entirely.

        Parameters:
            scripts: List of ``Script`` objects to upload.

        Example::

            sim.set_scripts([
                allsolve.Script(
                    name="afterMeshLoad.py",
                    section_name=allsolve.CustomSection.AFTER_MESH_LOAD,
                    content="print('mesh loaded')",
                ),
                allsolve.Script(
                    name="afterAll.py",
                    section_name=allsolve.CustomSection.AFTER_ALL,
                    filepath="my_postprocessing.py",
                ),
            ])
        """
        scriptUpdates = []
        for script in scripts:
            if script.filepath is not None:
                with open(script.filepath, "r") as f:
                    script_content = f.read()
                script_name = script.name or pathlib.Path(script.filepath).name
            elif script.content is not None:
                script_content = script.content
                if script.name is None:
                    raise ValueError("Script name is required")
                script_name = script.name
            else:
                raise ValueError("Script must have either filepath or content")

            if script.section_name is not None:
                required = _SECTION_REQUIRED_ANALYSIS_TYPE.get(script.section_name)
                if required is not None and self.analysis_type != required:
                    raise ValueError(
                        f"Custom section {script.section_name.name} requires "
                        f"analysis type {required.value}, but this simulation "
                        f"uses {self.analysis_type.value if self.analysis_type else None}"
                    )
            if script.is_main and script.section_name is not None:
                raise ValueError("Main script cannot have a section name")

            if not script_name.endswith(".py"):
                script_name += ".py"
            scriptUpdates.append(
                rawapi.SimulationScriptUpdate(
                    id=None,
                    name=script_name,
                    script=script_content,
                    mainScript=script.is_main,
                    sectionName=(
                        script.section_name.value if script.section_name else None
                    ),
                )
            )
        with get_api() as api:
            api.update_simulation_scripts(
                authorization=get_auth(),
                project_id=self._project_id,
                simulation_id=self.id,
                simulation_script_update=scriptUpdates,
            )

    @prevent_deleted
    def get_scripts(self) -> List[Script]:
        """
        Retrieve all scripts attached to this simulation.

        Returns user-provided custom scripts.
        Each returned ``Script`` has its ``name``, ``content``,
        and ``section_name`` (if applicable) populated.

        Returns:
            List of ``Script`` objects.
        """
        with get_api() as api:
            raw_scripts = api.get_simulation_scripts(
                authorization=get_auth(),
                project_id=self._project_id,
                simulation_id=self.id,
            )
        return [
            Script(
                name=s.name,
                content=s.script,
                is_main=s.main_script,
                section_name=CustomSection(s.section_name) if s.section_name else None,
                origin=s.origin,
            )
            for s in raw_scripts
        ]

    @prevent_deleted
    def refresh_status(self, delay_s: float = 1) -> str | None:
        """
        Refresh the status of the processing of the simulation.

        Parameters:
            delay_s: Optional delay in seconds between checking the status of the simulation.

        Returns:
            The status of the processing of the simulation.
        """
        if delay_s > 0:
            time.sleep(delay_s)
        self._refresh()

        job = self._simulation.simulation_job
        if job is None:
            return Job.NOT_STARTED

        return job.status

    @prevent_deleted
    def get_status(self) -> str | None:
        """
        Get the status of the processing of the simulation.

        Returns:
            The status of the processing of the simulation.
        """
        job = self._simulation.simulation_job
        if job is None:
            return Job.NOT_STARTED

        return job.status

    @prevent_deleted
    def is_running(self, refresh_delay_s: float | None = None) -> bool:
        """
        Check if the processing of the simulation is running.

        Parameters:
            refresh_delay_s: Optional delay in seconds between checking the status of the simulation.

        Returns:
            True if the simulation is running, False otherwise.
        """
        if refresh_delay_s is None:
            status = self.get_status()
        else:
            status = self.refresh_status(delay_s=refresh_delay_s)

        return status not in (
            Job.SUCCESS,
            Job.ERROR,
            Job.ABORTED,
            Job.PARTIAL_SUCCESS,
        )

    @prevent_deleted
    def get_status_reason(self) -> str | None:
        """
        Get the status reason of the simulation.

        Returns:
            The status reason of the simulation.
        """
        job = self._simulation.simulation_job
        if job is None:
            return ""

        return job.status_reason

    @prevent_deleted
    def get_logs(self, limit: int = 100) -> List[str]:
        """
        Get the logs of the simulation.

        Parameters:
            limit: Optional maximum number of logs to return.

        Returns:
            The logs of the simulation.
        """
        return super().get_logs(limit)

    @prevent_deleted
    def print_new_loglines(self, file: TextIO = sys.stdout, limit: int = 100) -> None:
        """
        Print the new log lines of the simulation.

        Parameters:
            file: Optional file to print the logs to.
            limit: Optional maximum number of logs to print.
        """
        return super().print_new_loglines(file, limit)

    @prevent_deleted
    def set_runtime(self, runtime: Runtime) -> None:
        """Set the runtime of the simulation."""
        if runtime.node_type == CPU.CORES_3_10GB_FAST_START:
            if runtime.node_count > 1:
                raise ValueError(
                    "Node count for type {} must be 1".format(
                        CPU.CORES_3_10GB_FAST_START
                    )
                )

            if self.max_run_time_minutes > 15:
                raise ValueError(
                    "Max run time for type {} must be 15 minutes or less".format(
                        CPU.CORES_3_10GB_FAST_START
                    )
                )

        self._current_uncommitted_update().node_count = runtime.node_count
        self._current_uncommitted_update().node_type = runtime.node_type.value

    @prevent_deleted
    def save(self) -> None:
        """
        Explicitly save the changes to the cloud made by ``set_runtime`` or by
        setting any of the following properties:

        ``name``, ``description``, ``mesh_id``, ``max_run_time_minutes``,
        ``solver_mode``, ``variable_overrides``, ``analysis_type``, ``harmonics``,
        ``disabled_script_sections``, ``physics``, ``transient_start_time``,
        ``transient_end_time``, ``transient_timestep_size``, ``timestep_algorithm``,
        ``fundamental_frequency``, ``num_fft_samples``, ``num_requested_eigenmodes``,
        ``target_eigenfrequency``, ``eigenmode_port_analysis``, ``solver_tolerance``,
        ``nonlinear_solver_tolerance``, ``nonlinear_solver_max_iterations``,
        ``eigenmode_solver_tolerance``, ``eigenmode_solver_max_iterations``,
        ``target_frequency``, ``numerical_jacobian``.

        Otherwise the changes are saved automatically when ``start()`` is called.
        """
        if self._uncommitted_update is None:
            return

        with get_api() as api:
            api.update_simulation(
                authorization=get_auth(),
                project_id=self._project_id,
                simulation_id=self.id,
                simulation_update=self._uncommitted_update,
            )

            self._uncommitted_update = None

            self._simulation = api.get_simulation(
                authorization=get_auth(),
                project_id=self._project_id,
                simulation_id=self.id,
            )

    @prevent_deleted
    def set_shared_files(self, handles: List[rawapi.InputFile]) -> None:
        """
        Takes a list of project shared file handles and marks them to be used with
        this simulation. To remove files, remove them from the list and set again.

        Parameters:
            handles: List of project shared file handles to use in the simulation
        """
        current_input_files = self.get_input_files()

        with get_api() as api:
            sim_scoped_files = api.get_files(
                authorization=get_auth(),
                project_id=self._project_id,
                simulation_id=self.id,
            )
        sim_scoped_file_ids = {f.id for f in sim_scoped_files}

        kept = [
            f
            for f in current_input_files
            if f.type != rawapi.SimulationInputFileType.EXTRAINPUTFILE
            or f.source_extra_input_file_id in sim_scoped_file_ids
        ]
        new_shared = [
            rawapi.SimulationInputFile(
                id=str(uuid.uuid4()),
                type=rawapi.SimulationInputFileType.EXTRAINPUTFILE,
                sourceExtraInputFileId=handle.id,
            )
            for handle in handles
        ]

        self._update_all_input_files(kept + new_shared)
        self._shared_files = handles

    @prevent_deleted
    def add_input_file_from_simulation(
        self,
        source_simulation: Self | str,
        source_file_name: str,
        target_file_name: str,
        source_sweep_step: int | None = None,
        target_sweep_step: int | None = None,
        target_rank: int | None = None,
    ) -> rawapi.SimulationInputFile:
        """
        Add a simulation output file written by another simulation as an input file for this simulation.

        Parameters:
            source_simulation: Source simulation or source simulation ID.
            source_file_name: Source file name in the source simulation.
            target_file_name: Target file name in this simulation.
            source_sweep_step: Optional source sweep step index.
            target_sweep_step: Optional target sweep step index in this simulation.
            target_rank: Optional target rank index.

        Returns:
            The created input file handle.
        """
        source_simulation_id = self._get_source_simulation_id(source_simulation)
        input_file = rawapi.SimulationInputFile(
            id=str(uuid.uuid4()),
            type=rawapi.SimulationInputFileType.SIMULATIONOUTPUTFILE,
            sourceSimulationId=source_simulation_id,
            sourceSweepStep=source_sweep_step,
            sourceFileName=source_file_name,
            targetSweepStep=target_sweep_step,
            targetRank=target_rank,
            targetFileName=target_file_name,
        )
        update_response = self._update_all_input_files(
            self.get_input_files() + [input_file]
        )
        # Server returns the full list of input files; the newly added one at the end.
        if update_response.using is not None and len(update_response.using) > 0:
            return update_response.using[-1]
        else:
            input_file.id = ""
            return input_file

    @prevent_deleted
    def add_input_value_outputs_from_simulation(
        self,
        source_simulation: Self | str,
        target_file_name: str,
        source_sweep_step: int | None = None,
        target_sweep_step: int | None = None,
        target_rank: int | None = None,
    ) -> rawapi.SimulationInputFile:
        """
        Add a simulation value outputs written by another simulation as an input for this simulation.

        Parameters:
            source_simulation: Source simulation or source simulation ID.
            target_file_name: Target file name in this simulation.
            source_sweep_step: Optional source sweep step index.
            target_sweep_step: Optional target sweep step index in this simulation.
            target_rank: Optional target rank index.

        Returns:
            The created input file handle.
        """
        source_simulation_id = self._get_source_simulation_id(source_simulation)
        input_file = rawapi.SimulationInputFile(
            id=str(uuid.uuid4()),
            type=rawapi.SimulationInputFileType.SIMULATIONOUTPUTDATABASE,
            sourceSimulationId=source_simulation_id,
            sourceSweepStep=source_sweep_step,
            targetSweepStep=target_sweep_step,
            targetRank=target_rank,
            targetFileName=target_file_name,
        )
        update_response = self._update_all_input_files(
            self.get_input_files() + [input_file]
        )
        # Server returns the full list of input files; the newly added one at the end.
        if update_response.using is not None and len(update_response.using) > 0:
            return update_response.using[-1]
        else:
            input_file.id = ""
            return input_file

    @prevent_deleted
    def add_file(self, filepath: str) -> rawapi.InputFile:
        """
        Add the file in the given path to the simulation as an input file.

        Parameters:
            filepath: path to a file in the local system. If used in a simulation,
                      it is available with its basename.

        Returns:
            The file handle.

        Raises:
            FileExistsError: If a file with the same name already exists and is fully uploaded.
        """
        if self._simulation is None:
            raise NotInitializedError()

        file = pathlib.Path(filepath)
        try:
            handle = create_file(
                filepath=file,
                size=file.stat().st_size,
                project_id=self._project_id,
                simulation_id=self.id,
            )
        except rawapi.ApiException as e:
            if e.status == 409:
                self._refresh()

                with get_api() as api:
                    extra_files = api.get_files(
                        authorization=get_auth(),
                        project_id=self._project_id,
                        simulation_id=self.id,
                    )

                for existing_file in extra_files:
                    if existing_file.name == file.name:
                        if existing_file.file_uploaded_at is not None:
                            raise FileExistsError(
                                f"A file named '{file.name}' already exists in this simulation. "
                                f"Use delete_file() to remove it first."
                            ) from e
                        handle = existing_file
                        break
                else:
                    raise  # File not found, re-raise original error
            else:
                raise

        upload_file(file, handle, self._project_id)

        return handle

    @prevent_deleted
    def add_json_file(self, name: str, content: dict) -> rawapi.InputFile:
        """
        Add a JSON file to the simulation with the given dictionary serialized
        into JSON as content.

        Parameters:
            name: The name for the file during the simulation
            content: dictionary containing your data

        Returns:
            The file handle.

        Raises:
            FileExistsError: If a file with the same name already exists and is fully uploaded.
        """
        if self._simulation is None:
            raise NotInitializedError()

        data = json.dumps(content, sort_keys=True).encode()
        file = pathlib.Path(name)
        try:
            handle = create_file(
                filepath=file,
                size=len(data),
                project_id=self._project_id,
                simulation_id=self.id,
            )
        except rawapi.ApiException as e:
            if e.status == 409:
                self._refresh()

                with get_api() as api:
                    extra_files = api.get_files(
                        authorization=get_auth(),
                        project_id=self._project_id,
                        simulation_id=self.id,
                    )

                for existing_file in extra_files:
                    if existing_file.name == file.name:
                        if existing_file.file_uploaded_at is not None:
                            raise FileExistsError(
                                f"A file named '{file.name}' already exists in this simulation. "
                                f"Use delete_file() to remove it first."
                            ) from e
                        handle = existing_file
                        break
                else:
                    raise  # File not found, re-raise original error
            else:
                raise

        upload_bytes(data, handle, self._project_id)

        return handle

    @prevent_deleted
    def run(
        self,
        print_logs: bool = False,
        refresh_delay_s: float = 1,
        on_error: OnError = OnError.IGNORE,
    ) -> None:
        """Runs the simulation and returns when the processing is complete.

        Parameters:
            print_logs: If True, print logs to the console.
            refresh_delay_s: Optional delay in seconds between checking the status of the job.
            on_error: Controls error handling after the job completes.
                ``OnError.IGNORE`` (default) — never raises; use :meth:`get_status` to check.
                ``OnError.RAISE`` — raises :exc:`JobError` unless status is ``SUCCESS``,
                ``PARTIAL_SUCCESS``, or ``ABORTED`` (partial results may still be available).
                ``OnError.STRICT`` — raises :exc:`JobError` unless status is exactly ``SUCCESS``.
        """
        self.start()
        while self.is_running(refresh_delay_s=refresh_delay_s):
            if print_logs:
                self.print_new_loglines()
        if print_logs:
            self.print_new_loglines()
        status = self.get_status()
        status_reason = self.get_status_reason() or ""
        if on_error is OnError.STRICT and status != Job.SUCCESS:
            raise JobError(
                f"Simulation '{self.name}' (id={self.id}) failed with status: {status} {status_reason}",
                status=status,
                status_reason=status_reason,
            )
        elif on_error is OnError.RAISE and status not in (
            Job.SUCCESS,
            Job.PARTIAL_SUCCESS,
            Job.ABORTED,
        ):
            raise JobError(
                f"Simulation '{self.name}' (id={self.id}) failed with status: {status} {status_reason}",
                status=status,
                status_reason=status_reason,
            )

    @prevent_deleted
    def start(self) -> None:
        """
        Start the simulation.
        """
        with get_api() as api:
            if self._uncommitted_update is not None:
                api.update_simulation(
                    authorization=get_auth(),
                    project_id=self._project_id,
                    simulation_id=self.id,
                    simulation_update=self._uncommitted_update,
                )
                self._uncommitted_update = None

            self._simulation = api.start_simulation(
                authorization=get_auth(),
                project_id=self._project_id,
                simulation_id=self.id,
                body={},
            )

    @prevent_deleted
    def abort(self) -> None:
        """
        Abort the simulation.
        """
        return super().abort()

    @prevent_deleted
    def get_output_csv(
        self,
        delimiter=",",
        refresh: bool = False,
        csv_format: CsvExportFormat = CsvExportFormat.EXPLODED,
    ) -> str:
        """
        Get the output of the simulation in CSV format.

        Parameters:
            delimiter: The delimiter to use in the CSV file.
            refresh: Whether to refresh the output data.
            csv_format: The format of the CSV file.

        Returns:
            String containing the output of the simulation in CSV format.
        """
        return self.get_output_data(refresh).to_csv(delimiter, csv_format)

    @prevent_deleted
    def get_output_data(self, refresh: bool = True) -> SimulationOutputData:
        """
        Returns the output data of the simulation.

        Parameters:
            refresh: Whether to refresh the output data.

        Returns:
            allsolve.sim.SimulationOutputData object
        """
        if self._output_data is None:
            self._output_data = SimulationOutputData(self._project_id, self.id)
        if refresh or self._output_data._database is None:
            self._output_data.refresh()
        return self._output_data

    @prevent_deleted
    def get_output_values(self, sweep_index: int = 0, refresh: bool = False) -> dict:
        """
        Get the output values of the simulation.

        Parameters:
            sweep_index: The index of the sweep.
            refresh: Whether to refresh the output values.

        Returns:
            The output values of the simulation.
        """
        return self.get_output_data(refresh).to_dict(sweep_index)

    @prevent_deleted
    def clean_output_data_cache(self) -> None:
        """
        Clean the output data cache for this simulation.
        This invalidates any existing SimulationOutputData objects for this simulation.
        """
        output_data = self.get_output_data(refresh=False)
        output_data.clean_cache()

    @prevent_deleted
    def _download_files(
        self,
        all_files: List[str],
        job_id: str | None = None,
        output_dir: str = "./",
    ) -> None:
        path = pathlib.Path(output_dir)

        with get_api() as api:
            download_urls = api.get_simulation_output_data_download_urls(
                authorization=get_auth(),
                project_id=self._project_id,
                simulation_id=self.id,
                job_id=job_id,
                request_body=all_files,
            )

        for download_url, filename in zip(download_urls, all_files):
            validate_url_scheme(download_url, get_allow_insecure_http())
            session = get_http_session()
            with session.get(
                download_url,
                stream=True,
                timeout=(CONNECT_TIMEOUT_S, TRANSFER_TIMEOUT_S),
            ) as r:
                r.raise_for_status()

                with open(path.joinpath(filename), "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

    @prevent_deleted
    def save_output_field(
        self,
        name: str,
        output_dir: str = "./",
        sweep_index: int = 0,
        step_index: int | None = None,
        refresh: bool = False,
    ) -> None:
        """
        Save the output field of the simulation.

        Parameters:
            name: The name of the field to save.
            output_dir: The directory to save the field to.
            sweep_index: The optional index of the sweep.
            step_index: The optional index of the step or None.
            refresh: Whether to refresh the output data.
        """
        path = pathlib.Path(output_dir)
        if not path.exists():
            raise ValueError("Given output_dir does not exist")

        output_data = self.get_output_data(refresh=refresh)
        file_names = output_data.get_filenames_for_output_field(
            name, sweep_index, step_index
        )
        job_id = output_data.get_simulation_job_id(sweep_index, step_index)
        self._download_files(file_names, job_id, output_dir=output_dir)

    @prevent_deleted
    def save_output_mesh(
        self,
        name: str,
        output_dir: str = "./",
        sweep_index: int = 0,
        step_index: int | None = None,
        refresh: bool = False,
    ) -> None:
        """
        Save the output mesh of the simulation.

        Parameters:
            name: The name of the mesh to save.
            output_dir: The directory to save the mesh to.
            sweep_index: The optional index of the sweep.
            step_index: The optional index of the step or None.
            refresh: Whether to refresh the output data.
        """
        path = pathlib.Path(output_dir)
        if not path.exists():
            raise ValueError("Given output_dir does not exist")

        output_data = self.get_output_data(refresh=refresh)
        file_names = output_data.get_filenames_for_mesh(name, sweep_index, step_index)
        job_id = output_data.get_simulation_job_id(sweep_index, step_index)
        self._download_files(file_names, job_id, output_dir=output_dir)

    @prevent_deleted
    def save_output_files(
        self,
        filenames: List[str],
        output_dir: str = "./",
        sweep_index: int = 0,
        step_index: int | None = None,
        refresh: bool = False,
    ) -> None:
        """
        Save the output files of the simulation.

        Parameters:
            filenames: The names of the files to save.
            output_dir: The directory to save the files to.
            sweep_index: The optional index of the sweep.
            step_index: The optional index of the step or None.
            refresh: Whether to refresh the output data.
        """
        output_data = self.get_output_data(refresh=refresh)
        job_id = output_data.get_simulation_job_id(sweep_index, step_index)
        self._download_files(filenames, job_id, output_dir=output_dir)

    @prevent_deleted
    def copy(
        self,
    ) -> Self:
        """
        Make a copy of the simulation. Useful for creating simulations from a template.

        Returns:
            The copied simulation.
        """

        with get_api() as api:
            simulation = api.create_simulation(
                authorization=get_auth(),
                project_id=self._project_id,
                template=self.id,
                body={},
            )

        return self.__class__(self._project_id, simulation)

    @prevent_deleted
    def delete(self) -> None:
        """
        Delete the simulation from the project. After deletion, the
        `Simulation` object cannot be used and should be discarded.
        """
        with get_api() as api:
            api.delete_simulation(
                authorization=get_auth(),
                project_id=self._project_id,
                simulation_id=self.id,
            )

        self._deleted = True

    @prevent_deleted
    def save_generated_scripts(self, output_dir: str = "./") -> List[str]:
        """
        Fetch the server-generated simulation helper scripts and save them to disk.

        This writes the generated Python helper modules (utils, tagmappings,
        regions, expressions, materials, parameters) into ``output_dir``.
        These files are normally generated server-side and injected at
        simulation runtime. Having them on disk enables IDE features like
        autocomplete and type checking when editing custom simulation scripts.

        Parameters:
            output_dir: The directory to save the scripts to.

        Returns:
            List of file paths that were written.
        """
        path = pathlib.Path(output_dir)
        if not path.exists():
            raise ValueError("Given output_dir does not exist")

        with get_api() as api:
            generated = api.get_generated_scripts(
                authorization=get_auth(),
                project_id=self._project_id,
                simulation_id=self.id,
            )

        written: List[str] = []
        for attr in _GENERATED_HELPER_MODULES:
            script = getattr(generated, attr)
            imports_block = "\n".join(_import_to_string(imp) for imp in script.imports)
            content = (
                imports_block + "\n\n" + script.code if imports_block else script.code
            )
            file_path = path / f"{script.module}.py"
            file_path.write_text(content)
            written.append(str(file_path))

        return written

    def _update_all_input_files(
        self, input_files: List[rawapi.SimulationInputFile]
    ) -> rawapi.SimulationInputFileUpdateResponse:
        with get_api() as api:
            update_response = api.update_simulation_input_files(
                authorization=get_auth(),
                project_id=self._project_id,
                simulation_id=self.id,
                simulation_input_file=input_files,
            )

        self._simulation.input_files = update_response.using
        self._refresh()
        return update_response

    def _get_source_simulation_id(self, source_simulation: Self | str) -> str:
        if isinstance(source_simulation, str):
            return source_simulation
        if isinstance(source_simulation, Simulation):
            return source_simulation.id
        raise ValueError("source_simulation must be a simulation ID or Simulation")

    def __str__(self) -> str:
        return f"Simulation(id={self.id}, name={self.name})"

    def __repr__(self) -> str:
        return self.__str__()
