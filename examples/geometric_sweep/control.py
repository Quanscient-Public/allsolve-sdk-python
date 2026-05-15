from types import SimpleNamespace

import allsolve

from geo import (
    L_MIN,
    L_MAX,
    N_STUB_LENGTHS,
    LX_DIELECTRIC,
    LY_DIELECTRIC,
    LZ_DIELECTRIC,
    LZ_TRACK,
    LZ_AIR,
)


def setup_client() -> allsolve.Client:
    """Authenticate and return an SDK client.

    Credentials are resolved automatically from explicit parameters,
    ALLSOLVE_* environment variables, or a .env file.
    """
    return allsolve.Client()


def create_project(client: allsolve.Client) -> allsolve.Project:
    project = client.create_project(
        name="SDK - Microstrip stub filter sweep",
        description=(
            "S-parameter frequency sweep for a microstrip stub filter. "
            "Geometry, mesh, physics, and simulation are all defined via the SDK. "
            "A Cartesian product sweep covers both frequency and stub length."
        ),
    )
    print(f"Created project: {project.name} (id: {project.id})")
    return project


def create_variables(project: allsolve.Project) -> None:
    project.create_variables(
        [
            ("freq", "10e9", "Driving frequency"),
            ("stub_length", str(L_MIN), "Filter stub length"),
        ]
    )


def create_regions(project: allsolve.Project) -> SimpleNamespace:
    regions = SimpleNamespace()

    regions.dielectric = project.create_region_rule(
        name="dielectric",
        entity_type=allsolve.Region.VOLUME,
        bounding_box=(
            (-LX_DIELECTRIC / 2, -LY_DIELECTRIC / 2, -LZ_DIELECTRIC / 2),
            (LX_DIELECTRIC / 2, LY_DIELECTRIC / 2, LZ_DIELECTRIC / 2),
        ),
    )

    regions.copper = project.create_region_rule(
        name="copper",
        entity_type=allsolve.Region.VOLUME,
        max_size=(LX_DIELECTRIC, LY_DIELECTRIC, LZ_TRACK * 2),
    )

    regions.air = project.create_region_rule(
        name="air",
        entity_type=allsolve.Region.VOLUME,
        min_size=(LX_DIELECTRIC * 0.9, LY_DIELECTRIC * 0.9, LZ_AIR * 0.5),
    )

    regions.ground_pec = project.create_region_rule(
        name="ground_pec",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=(
            (-LX_DIELECTRIC / 2, -LY_DIELECTRIC / 2, -LZ_DIELECTRIC / 2),
            (LX_DIELECTRIC / 2, LY_DIELECTRIC / 2, -LZ_DIELECTRIC / 2),
        ),
    )

    regions.port_in = project.create_region_rule(
        name="port_in",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=(
            (-LX_DIELECTRIC / 2, -LY_DIELECTRIC / 2, -LZ_DIELECTRIC / 2),
            (-LX_DIELECTRIC / 2, LY_DIELECTRIC / 2, LZ_DIELECTRIC / 2 + LZ_AIR),
        ),
    )

    regions.port_out = project.create_region_rule(
        name="port_out",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=(
            (LX_DIELECTRIC / 2, -LY_DIELECTRIC / 2, -LZ_DIELECTRIC / 2),
            (LX_DIELECTRIC / 2, LY_DIELECTRIC / 2, LZ_DIELECTRIC / 2 + LZ_AIR),
        ),
    )

    return regions


def create_materials(project: allsolve.Project, regions: SimpleNamespace) -> None:
    project.create_material_from_library(
        name="Air",
        target_region=regions.air,
    )
    project.create_material_from_library(
        name="Copper",
        target_region=regions.copper,
    )
    project.create_material(
        name="Dielectric",
        description="Custom substrate (epsilon_r = 10)",
        color="#535050",
        electric_conductivity="0",
        electric_permittivity="10*epsilon0",
        magnetic_permeability="mu0",
        target_region=regions.dielectric,
    )


def create_physics(
    project: allsolve.Project, regions: SimpleNamespace
) -> allsolve.Physic:
    em = project.add_physics(allsolve.Physics.ElectromagneticWaves())
    em.add_interactions(
        [
            allsolve.Interaction.ElectromagneticWavesPerfectConductor(
                name="Track PEC",
                target=regions.copper,
            ),
            allsolve.Interaction.ElectromagneticWavesPerfectConductor(
                name="Ground PEC",
                target=regions.ground_pec,
            ),
            allsolve.Interaction.ElectromagneticWavesEigenmodePort(
                name="In",
                electromagnetic_waves_eigenmode_port_driving_signal="sin(2*pi*freq*t)",
                port_target=regions.port_in,
                electromagnetic_waves_eigenmode_port_target_eigenvalue_type=(
                    allsolve.ElectromagneticWavesEigenmodePortTargetEigenvalueType.EFFECTIVE_REFRACTIVE_INDEX
                ),
                electromagnetic_waves_eigenmode_port_effective_refractive_index="5",
            ),
            allsolve.Interaction.ElectromagneticWavesEigenmodePort(
                name="Out",
                electromagnetic_waves_eigenmode_port_driving_signal="sin(2*pi*freq*t)",
                port_target=regions.port_out,
                electromagnetic_waves_eigenmode_port_target_eigenvalue_type=(
                    allsolve.ElectromagneticWavesEigenmodePortTargetEigenvalueType.EFFECTIVE_REFRACTIVE_INDEX
                ),
                electromagnetic_waves_eigenmode_port_effective_refractive_index="5",
            ),
        ]
    )
    return em


def create_cartesian_sweep(project: allsolve.Project) -> allsolve.VariableOverrides:
    """Create a Cartesian product sweep over frequency and stub length."""
    return project.create_variable_overrides(
        name="Frequency x Stub length sweep",
        overrides=[
            ("freq", "linspace(5e9, 15e9, 21)"),
            ("stub_length", f"linspace({L_MIN}, {L_MAX}, {N_STUB_LENGTHS})"),
        ],
        sweep_type=allsolve.SweepType.CARTESIAN_PRODUCT,
    )


def create_simulation(
    project: allsolve.Project,
    mesh: allsolve.Mesh,
    em_physics: allsolve.Physic,
    sweep: allsolve.VariableOverrides,
) -> allsolve.Simulation:
    sim = project.create_simulation_harmonic(
        name="Microstrip stub filter — Cartesian sweep",
        description="Harmonic EM simulation sweeping frequency and stub length",
        max_run_time_minutes=15,
        solver_mode=allsolve.SolverMode.ITERATIVE,
        fundamental_frequency="freq",
        mesh=mesh,
        variable_overrides=sweep,
        physics=[em_physics.id],
        solver_tolerance="1e-06",
        numerical_jacobian=False,
    )

    sim.add_outputs(
        [
            allsolve.Output.SParameters(name="S-parameters"),
            allsolve.Output.FieldOutput(
                name="E harmonic 2",
                expression="harm(2, E)",
                target=None,
                field_output_skin_only=True,
            ),
        ]
    )

    sim.set_runtime(
        allsolve.Runtime(
            node_count=1,
            node_type=allsolve.CPU.CORES_1_16GB,
        )
    )

    return sim
