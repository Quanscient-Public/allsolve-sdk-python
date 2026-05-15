"""
This script creates a project with a simplified bending beam simulation.

The simulation outputs:
- FieldOutput data that can be visualized in the Allsolve web app.
  Add a result visualization it the GUI for Displacement field and
  add a Warp filter. Then adjust the scale factor to view the displacement.
"""

import allsolve
from types import SimpleNamespace


def main():
    # Create client which uses .env file for authentication
    client = allsolve.Client()

    verbose = True

    # Create project
    project = client.create_project(
        name="Bending beam",
        description="Simulation for a bending beam",
    )
    print(f"Created project: {project.name} (id: {project.id})")

    # Create variables for geometry and regions
    print("Creating variables")
    project.create_variables(
        [
            ("length", "24e-3", "Length of the beam"),
            ("width", "2e-3", "Width of the beam"),
            ("height", "3e-3", "Height of the beam"),
            ("tolerance", "1e-4", "Tolerance for regions"),
        ]
    )

    # Create geometry
    print("Creating geometry")
    project.geometry_builder().add_box(
        name="beam",
        position=(0, 0, 0),
        size=("length", "width", "height"),
    ).build(print_logs=verbose, on_error=allsolve.OnError.RAISE)
    print("Geometry built")

    # Create regions
    print("Creating regions")
    regions = SimpleNamespace()
    # Beam volume
    regions.beam_volume = project.create_region_rule(
        name="beam_volume",
        entity_type=allsolve.Region.VOLUME,
        max_size=allsolve.ExpressionVector(
            x="length + tolerance",
            y="width + tolerance",
            z="height + tolerance",
        ),
        min_size=allsolve.ExpressionVector(
            x="length - tolerance",
            y="width - tolerance",
            z="height - tolerance",
        ),
    )

    # Clamp surface
    regions.clamp_surface = project.create_region_rule(
        name="clamp_surface",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=allsolve.ExpressionBoundingBox(
            min=allsolve.ExpressionVector(
                x="(-length / 2) - tolerance",
                y="(-width / 2) - tolerance",
                z="(-height / 2) - tolerance",
            ),
            max=allsolve.ExpressionVector(
                x="(-length / 2) + tolerance",
                y="(width / 2) + tolerance",
                z="(height / 2) + tolerance",
            ),
        ),
    )

    # Top surface
    regions.top_surface = project.create_region_rule(
        name="top_surface",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=allsolve.ExpressionBoundingBox(
            min=allsolve.ExpressionVector(
                x="(-length / 2) - tolerance",
                y="(-width / 2) - tolerance",
                z="(height / 2) - tolerance",
            ),
            max=allsolve.ExpressionVector(
                x="(length / 2) + tolerance",
                y="(width / 2) + tolerance",
                z="(height / 2) + tolerance",
            ),
        ),
    )

    # Create materials
    print("Creating materials")
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

    # Create physics and interactions
    print("Creating physics and interactions")
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
                force=(0, 0, -1000),
            ),
        ]
    )

    # Create mesh
    print("Creating mesh")
    mesh = project.create_mesh()

    # Run mesh
    mesh.run(print_logs=verbose)
    if mesh.get_status() != allsolve.Job.SUCCESS:
        raise ValueError(f"Mesh processing failed: {mesh.get_status()}")

    # Create simulation
    print("Creating simulation")
    sim = project.create_simulation_static(
        name="Simulation",
        description="Simulation 1",
        max_run_time_minutes=10,
        solver_mode=allsolve.SolverMode.DIRECT,
        mesh=mesh.id,
    )

    # Add outputs to the simulation
    sim.add_outputs(
        [
            allsolve.Output.FieldOutput(
                name="Displacement",
                expression="u",
            ),
        ]
    )

    # Run the simulation
    print("Running simulation")
    sim.start()
    while sim.is_running(refresh_delay_s=1):
        sim.print_new_loglines()

    print("Simulation status:", sim.get_status())


if __name__ == "__main__":
    try:
        project = main()
    except Exception as e:
        print(f"Error running project: {e}")
