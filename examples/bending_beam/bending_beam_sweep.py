"""
This script creates a project with a simplified bending beam simulation with
a sweep over some project parameters:
- height of the beam
- material of the beam
- force applied to the beam

The simulation outputs:
- ValueOutput data that is printed in CSV format to the console.
  Z deflection of the beam in 10 points along the beam top surface is calculated
  and printed in CSV format.
- FieldOutput data that can be visualized in the Allsolve web app.
  Add a result visualization it the GUI for Displacement field and
  add a Warp filter. Then adjust the scale factor to view the displacement.
"""

import allsolve
from types import SimpleNamespace


def main():
    client = allsolve.Client()

    verbose = True

    project = client.create_project(
        name="Bending beam sweep",
        description="Demo simulation for a bending beam with a sweep over some simulation parameters",
    )
    print(f"Created project: {project.name} (id: {project.id})")

    create_variables(project)
    build_geometry(project, verbose=verbose)
    regions = create_regions(project)
    create_materials(project, regions)
    create_physics(project, regions)
    sweep = create_sweep(project)
    mesh = create_mesh(project, sweep)
    sim = create_simulation(project, mesh, sweep)
    run_mesh_and_simulation(mesh, sim)
    print_results(sim)

    # Store the project id in the cache to be used in visualize_bending_beam_sweep_results.py script
    client.set_current_project(project)


def create_variables(project: allsolve.Project) -> None:
    project.create_variables(
        [
            ("length", "24e-3", "Length of the beam"),
            ("width", "2e-3", "Width of the beam"),
            ("height", "3e-3", "Height of the beam"),
            ("tolerance", "1e-4", "Tolerance for regions"),
            ("force", "-1000", "Force for Load interaction"),
            ("material_index", "0", "Selects used material for the beam"),
        ]
    )


def build_geometry(project: allsolve.Project, verbose: bool = False) -> None:
    geometry_builder = project.geometry_builder()
    geometry_builder.add_box(
        name="beam",
        position=(0, 0, 0),
        size=("length", "width", "height"),
    )
    geometry_builder.build(print_logs=verbose, on_error=allsolve.OnError.RAISE)


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
        enabled="eq(material_index,0)",
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
    project.create_material(
        name="Copper",
        enabled="eq(material_index,1)",
        description="",
        color="#DD6839",
        abbreviation="Cu",
        target_region=regions.beam_volume,
        coefficient_of_thermal_expansion=1.65e-05,
        density=8960,
        elasticity_matrix=allsolve.MaterialProperty.ElasticityMatrixYoungsModulusPoissonsRatio(
            "130000000000.0",
            "0.34",
        ),
        electric_conductivity=60000000.0,
        electric_permittivity="epsilon0",
        heat_capacity=385,
        magnetic_permeability="mu0",
        thermal_conductivity=401,
    )


def create_physics(project: allsolve.Project, regions: SimpleNamespace) -> None:
    solid_mechanics_physics = project.add_physics(allsolve.Physics.SolidMechanics())
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


def create_sweep(project: allsolve.Project) -> allsolve.VariableOverrides:
    sweep = project.create_variable_overrides(
        name="sweep_1",
        sweep_type=allsolve.SweepType.CARTESIAN_PRODUCT,
        overrides=[
            ("height", ["3e-3", "3.5e-3"]),
            ("material_index", ["0", "1"]),
            ("force", "linspace(-1000, -2000, 3)"),
        ],
    )
    return sweep


def create_mesh(
    project: allsolve.Project, sweep: allsolve.VariableOverrides
) -> allsolve.Mesh:
    mesh = project.create_mesh(
        mesh_settings=allsolve.MeshSettings(
            # 'height' in variable overrides affects the geometry.
            #  Add the variable_overrides to the MeshSettings to
            #  create the mesh for each geometry configuration.
            variable_overrides=[sweep],
        ),
    )
    return mesh


def create_simulation(
    project: allsolve.Project, mesh: allsolve.Mesh, sweep: allsolve.VariableOverrides
) -> allsolve.Simulation:
    # Create simulation
    print("Creating simulation")
    sim = project.create_simulation_static(
        name="Simulation",
        description="Simulation 1",
        max_run_time_minutes=10,
        solver_mode=allsolve.SolverMode.DIRECT,
        mesh=mesh.id,
        # Add variable overrides to the simulation
        variable_overrides=sweep.id,
    )

    # Add outputs to the simulation
    sim.add_outputs(
        [
            allsolve.Output.FieldOutput(
                name="Displacement",
                expression="u",
            ),
            allsolve.Output.ValueOutput(
                name="z_deflection",
                expression="lineinterpolate(reg.beam_volume, compz(u), getcoords(reg.top_surface_clamp_corner), getcoords(reg.top_surface_free_corner), 10)",
            ),
        ]
    )
    return sim


def run_mesh_and_simulation(
    mesh: allsolve.Mesh, sim: allsolve.Simulation, verbose: bool = False
) -> None:
    override = sim.variable_overrides
    if override is None:
        raise ValueError("Simulation has no variable overrides")
    instance = mesh.get_override(variable_override=override)
    instance.run(print_logs=verbose)
    if instance.get_status() != allsolve.Job.SUCCESS:
        raise ValueError(f"Mesh processing failed: {instance.get_status()}")

    sim.run(print_logs=verbose)
    if sim.get_status() != allsolve.Job.SUCCESS:
        raise ValueError(f"Simulation processing failed: {sim.get_status()}")


def print_results(sim: allsolve.Simulation) -> None:

    # Access simulation results via output_data
    output_data = sim.get_output_data()
    results = output_data.to_csv(
        csv_format=allsolve.CsvExportFormat.EXPLODED, include_overrides=True
    )
    print("Simulation output:")
    print(results)

    # Delete output_data cache from disk when it's no longer needed
    output_data.clean_cache()


if __name__ == "__main__":
    main()
