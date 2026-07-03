"""
Bending beam sweep with separate resource pools for preprocessing and simulation.

- The resource reservation pools stay reserved across jobs in each phase without
  re-acquiring resources from the cloud.
- Each resource reservation pool is created and waited on only when that phase starts, so quota is
  not held during unrelated setup or while the other pool is in use.
- Resource reservations use a 120-second lease. The SDK renews reservations automatically during job
  runs and while idle between jobs.

- preprocess_pool: small (1 node), created at the start of the script. The same pool is used for
  geometry build and all mesh jobs. Job runs keep the pool alive until each job finishes.
  The pool is released manually once geometry and all mesh jobs are done.

- sim_pool: larger (4 nodes), created right before the sweep simulations are run and released after
  all simulations are done.
"""

import allsolve
from types import SimpleNamespace
from typing import List


def main() -> None:
    client = allsolve.Client()
    verbose = True
    project: allsolve.Project | None = None

    preprocess_pool: allsolve.ResourceReservation | None = None
    sim_pool: allsolve.ResourceReservation | None = None

    try:
        project = client.create_project(
            name="Bending beam sweep (dual reservation)",
            description="Sweep with separate preprocess and simulation compute pools",
            # team_id="your-team-id", # Optional; see README "Team quota"
        )
        print(f"Created project: {project.name} (id: {project.id})")
        print("Creating preprocess resource reservation pool...")
        preprocess_pool = allsolve.ResourceReservation.create(
            node_type=allsolve.CPU.CORES_1_16GB,
            num_nodes=1,
            # team_id="your-team-id",  # Optional; see README "Team quota"
        )
        print("Waiting for preprocess resource reservation pool...")
        preprocess_pool.wait_until_ready()
        print(f"Preprocess resource reservation pool ready: {preprocess_pool.id}")

        create_variables(project)
        build_geometry(project, preprocess_pool, verbose=verbose)
        regions = create_regions(project)
        create_materials(project, regions)
        physics_set = create_physics(project, regions)
        sweeps = create_sweeps(project)
        mesh = create_mesh(project, sweeps)
        simulations = create_simulations(project, mesh, sweeps, physics_set)

        run_meshes(mesh, sweeps, preprocess_pool, verbose=verbose)

        # Release preprocess pool once geometry and mesh are done to stop idle quota burn.
        preprocess_pool.release()
        preprocess_pool = None
        print("Released preprocess resource reservation pool")

        # Create larger (4 nodes) resource reservation for simulations
        print("Creating simulation resource reservation pool...")
        sim_pool = allsolve.ResourceReservation.create(
            main_node_type=allsolve.CPU.CORES_2_32GB,
            node_type=allsolve.CPU.CORES_2_32GB,
            num_nodes=1,  # Number of DDM nodes is 1 for this example
            num_replicas=6,  # There are 6 sweep steps in the sweeps. Run them parallelly.
            # team_id="your-team-id",  # Optional; see README "Team quota"
            # max_idle_seconds=600,  # Increase max_idle_seconds if gaps between jobs in your
            # workflow can be longer than 10 minutes; the SDK renews the lease
            # in the background while idle and the timer resets every time a job finishes.
        )
        print("Waiting for simulation resource reservation pool...")
        sim_pool.wait_until_ready()
        print(f"Simulation resource reservation pool ready: {sim_pool.id}")

        run_simulations(simulations, sim_pool, verbose=verbose)

        # Release simulation pool once simulations are done to stop idle quota burn.
        sim_pool.release()
        sim_pool = None
        print("Released simulation resource reservation pool")

    except Exception as e:
        print(f"Error running project: {e}")
    finally:
        for pool, label in ((preprocess_pool, "preprocess"), (sim_pool, "sim")):
            if pool is None:
                continue
            try:
                pool.release()
                print(f"Released {label} pool")
            except allsolve.ResourceReservationError as e:
                print(f"Failed to release {label} pool: {e}")
        if project is not None and input("Delete project? [Y/n]: ").strip().lower() in (
            "",
            "y",
            "yes",
        ):
            project.delete()
            print("Project deleted.")


def create_variables(project: allsolve.Project) -> None:
    project.create_variables(
        [
            ("length", "24e-3", "Length of the beam"),
            ("width", "2e-3", "Width of the beam"),
            ("height", "3e-3", "Height of the beam"),
            ("tolerance", "1e-4", "Tolerance for regions"),
            ("force", "-1000", "Force for Load interaction"),
        ]
    )


def build_geometry(
    project: allsolve.Project,
    preprocess_pool: allsolve.ResourceReservation,
    verbose: bool = False,
) -> None:
    geometry_builder = project.geometry_builder()
    geometry_builder.add_box(
        name="beam",
        position=(0, 0, 0),
        size=("length", "width", "height"),
    )
    print(f"Building geometry on reservation {preprocess_pool.id}")
    geometry_builder.build(
        print_logs=verbose,
        on_error=allsolve.OnError.RAISE,
        resource_reservation=preprocess_pool,
    )


def create_regions(project: allsolve.Project) -> SimpleNamespace:
    regions = SimpleNamespace()
    # Beam volume
    regions.beam_volume = project.create_region_rule(
        name="beam_volume",
        entity_type=allsolve.Region.VOLUME,
        max_size=("length + tolerance", "width + tolerance", "height + tolerance"),
        min_size=("length - tolerance", "width - tolerance", "height - tolerance"),
    )

    # Clamp surface
    regions.clamp_surface = project.create_region_rule(
        name="clamp_surface",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=(
            (
                "(-length / 2) - tolerance",
                "(-width / 2) - tolerance",
                "(-height / 2) - tolerance",
            ),
            (
                "(-length / 2) + tolerance",
                "(width / 2) + tolerance",
                "(height / 2) + tolerance",
            ),
        ),
    )

    # Top surface
    regions.top_surface = project.create_region_rule(
        name="top_surface",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=(
            (
                "(-length / 2) - tolerance",
                "(-width / 2) - tolerance",
                "(height / 2) - tolerance",
            ),
            (
                "(length / 2) + tolerance",
                "(width / 2) + tolerance",
                "(height / 2) + tolerance",
            ),
        ),
    )

    # Top surface clamp corner
    # Corner at clamp end (-X) and top surface (+Z). Pick +Y corner.
    regions.top_surface_clamp_corner = project.create_region_rule(
        name="top_surface_clamp_corner",
        entity_type=allsolve.Region.POINT,
        bounding_box=(
            (
                "(-length / 2) - tolerance",
                "(width / 2) - tolerance",
                "(height / 2) - tolerance",
            ),
            (
                "(-length / 2) + tolerance",
                "(width / 2) + tolerance",
                "(height / 2) + tolerance",
            ),
        ),
    )

    # Top surface free corner
    # Same top +Y corner, but at the free end (+X).
    regions.top_surface_free_corner = project.create_region_rule(
        name="top_surface_free_corner",
        entity_type=allsolve.Region.POINT,
        bounding_box=(
            (
                "(length / 2) - tolerance",
                "(width / 2) - tolerance",
                "(height / 2) - tolerance",
            ),
            (
                "(length / 2) + tolerance",
                "(width / 2) + tolerance",
                "(height / 2) + tolerance",
            ),
        ),
    )
    return regions


def create_materials(project: allsolve.Project, regions: SimpleNamespace) -> None:
    project.create_material(
        name="Aluminium",
        description="Aluminium",
        color="#aaaaaa",
        abbreviation="Al",
        target_region=regions.beam_volume,
        coefficient_of_thermal_expansion=1e-06,
        density=2700,
        elasticity_matrix=allsolve.MaterialProperty.ElasticityMatrixYoungsModulusPoissonsRatio(
            "68000000000.0",
            "0.32",
        ),
        electric_conductivity=36900000.0,
        electric_permittivity="epsilon0",
        heat_capacity=897,
        magnetic_permeability="mu0",
        speed_of_sound=6320,
        thermal_conductivity=237,
    )


def create_physics(
    project: allsolve.Project, regions: SimpleNamespace
) -> allsolve.PhysicsSet:
    physics_set = project.get_default_physics_set()
    solid_mechanics_physics = physics_set.add_physics(allsolve.Physics.SolidMechanics())
    solid_mechanics_physics.add_interactions(
        [
            # Clamp beam at the clamp surface
            allsolve.Interaction.SolidMechanicsClamp(
                name="Clamp",
                target=regions.clamp_surface,
            ),
            # Apply force at the top surface
            allsolve.Interaction.SolidMechanicsLoad(
                name="Load",
                target=regions.top_surface,
                force=(0, 0, "force"),
            ),
        ]
    )
    return physics_set


def create_sweeps(project: allsolve.Project) -> list[allsolve.VariableOverrides]:
    sweep = project.create_variable_overrides(
        name="sweep_1",
        sweep_type=allsolve.SweepType.CARTESIAN_PRODUCT,
        overrides=[
            ("height", ["3e-3", "3.5e-3"]),
            ("force", "linspace(-1000, -2000, 3)"),
        ],
    )
    sweep2 = project.create_variable_overrides(
        name="sweep_2",
        sweep_type=allsolve.SweepType.CARTESIAN_PRODUCT,
        overrides=[
            ("height", ["4e-3", "4.5e-3"]),
            ("force", "[-1234, -3456, -5678]"),
        ],
    )
    return [sweep, sweep2]


def create_mesh(
    project: allsolve.Project, sweeps: List[allsolve.VariableOverrides]
) -> allsolve.Mesh:
    mesh = project.create_mesh(
        mesh_settings=allsolve.MeshSettings(
            # 'height' in variable overrides affects the geometry.
            #  Add the variable_overrides to the MeshSettings to
            #  create the mesh for each geometry configuration.
            variable_overrides=sweeps,
        ),
    )
    return mesh


def run_meshes(
    mesh: allsolve.Mesh,
    sweeps: List[allsolve.VariableOverrides],
    preprocess_pool: allsolve.ResourceReservation,
    *,
    verbose: bool = False,
) -> None:
    print(f"Running mesh on reservation {preprocess_pool.id}")
    for sweep in sweeps:
        mesh_instance = mesh.get_override(variable_override=sweep)

        # mesh_instance.run keeps the reservation lease alive for the job duration;
        # idle auto-renew covers gaps between mesh jobs.
        mesh_instance.run(
            print_logs=verbose,
            on_error=allsolve.OnError.RAISE,
            resource_reservation=preprocess_pool,
        )
        print(f"Mesh {sweep.name} status: {mesh_instance.get_status()}")


def create_simulations(
    project: allsolve.Project,
    mesh: allsolve.Mesh,
    sweeps: List[allsolve.VariableOverrides],
    physics_set: allsolve.PhysicsSet,
) -> List[allsolve.Simulation]:
    # Create simulation
    print("Creating simulations")
    simulations = []
    for i, sweep in enumerate(sweeps):
        sim = project.create_simulation_static(
            name=f"Simulation {i+1}",
            description=f"Simulation {i+1}",
            max_run_time_minutes=10,
            solver_mode=allsolve.SolverMode.DIRECT,
            mesh=mesh.id,
            # Add variable overrides to the simulation
            variable_overrides=sweep,
            physics_set=physics_set,
        )

        # Add outputs to the simulation
        sim.add_outputs(
            [
                allsolve.Output.ValueOutput(
                    name="z_deflection",
                    expression="lineinterpolate(reg.beam_volume, compz(u), getcoords(reg.top_surface_clamp_corner), getcoords(reg.top_surface_free_corner), 10)",
                ),
            ]
        )
        simulations.append(sim)
    return simulations


def run_simulations(
    simulations: List[allsolve.Simulation],
    sim_pool: allsolve.ResourceReservation,
    *,
    verbose: bool = False,
) -> None:
    # Run all simulations on the same reservation to avoid waiting
    # for the resources to be reserved from the cloud for each new simulation.
    print(f"Running simulation sweep on reservation {sim_pool.id}")
    for sim in simulations:
        sim.run(
            print_logs=verbose,
            on_error=allsolve.OnError.RAISE,
            resource_reservation=sim_pool,
        )
        print(f"Simulation {sim.name} status: {sim.get_status()}")


if __name__ == "__main__":
    main()
