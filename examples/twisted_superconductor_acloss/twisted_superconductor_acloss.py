"""
Twisted superconductor AC loss (H-φ formulation) using the Allsolve SDK.

The project consists of:
- Geometry imported from twisted-superconductor.step
- Shared regions for air, copper matrix, and SC filaments
- Materials: Air, Copper, YBCO superconductor
- Physics: Magnetism H on the conductor and Magnetism φ on air with lump current and gauge
- Simulation: Transient simulation with Newton-linearized YBCO formulation (custom script)
- Value outputs for Joule losses in SC and copper regions

The simulation outputs:
- ValueOutput data for SC loss and Cu loss saved as CSV to the output directory and printed to the console.
"""

import os

import allsolve
from types import SimpleNamespace

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def main() -> None:

    client = allsolve.Client()

    project = client.create_project(
        name="SC twisted filament AC loss",
        description="",
    )
    print(f"Created project: {project.name} (id: {project.id})")

    try:
        create_variables(project)
        build_geometry(project)
        regions = create_regions(project)
        create_materials(project, regions)
        physics_set = create_physics(project, regions)
        mesh = create_mesh(project)
        sim1 = create_simulation(project, mesh, physics_set)
        run_mesh_and_simulation(mesh, sim1)
        save_simulation_results(sim1, output_basename="sim1_output.csv")
    except Exception as e:
        print(f"Error running project: {e}")
    finally:
        if input("Delete project? [Y/n]: ").strip().lower() in ("", "y", "yes"):
            project.delete()
            print("Project deleted.")


def create_variables(project: allsolve.Project) -> None:
    project.create_variables(
        [
            ("YBCO_n", "30", "Power law exponent"),
            ("YBCO_Ec", "1e-4", "Critical E field [V/m]"),
            ("f", "50", "Frequency [Hz]"),
            ("YBCO_Ic", "100", "Critical current [A]"),
            ("YBCO_Asc", "3.4541e-7", "Filament cross-section area [m^2]"),
            ("Iop", "0.8 * YBCO_Ic * sin(2 * pi * f * t)", "Operating current [A]"),
            ("YBCO_Jc", "YBCO_Ic / YBCO_Asc", "Critical current density [A/m^2]"),
        ]
    )


def build_geometry(project: allsolve.Project, verbose: bool = True) -> None:
    geometry_builder = project.geometry_builder()

    geometry_builder.add_step_file(
        filepath=os.path.join(SCRIPT_DIR, "twisted-superconductor.step"),
        name="twisted-superconductor.step",
        cleanup=False,
    )

    geometry_builder.build(print_logs=verbose, on_error=allsolve.OnError.RAISE)


def create_regions(project: allsolve.Project) -> SimpleNamespace:
    regions = SimpleNamespace()

    # Tags are tied to STEP file: twisted-superconductor.step
    regions.Air = project.create_region_basic(
        name="Air",
        entity_type=allsolve.Region.VOLUME,
        entity_tags=[2],
    )
    regions.Copper = project.create_region_basic(
        name="Copper",
        entity_type=allsolve.Region.VOLUME,
        entity_tags=[53],
    )
    regions.sc = project.create_region_basic(
        name="sc",
        entity_type=allsolve.Region.VOLUME,
        entity_tags=[200, 227, 254, 281, 308],
    )
    regions.Magnetism_H = project.create_region_basic(
        name="Magnetism H",
        entity_type=allsolve.Region.VOLUME,
        entity_tags=[227, 200, 254, 308, 281, 53],
    )
    regions.Magnetism_Phi = project.create_region_basic(
        name="Magnetism φ",
        entity_type=allsolve.Region.VOLUME,
        entity_tags=[2],
    )
    regions.Circulation_loop = project.create_region_basic(
        name="Circulation loop",
        entity_type=allsolve.Region.CURVE,
        entity_tags=[13, 9, 25, 23],
    )
    regions.Gauge_target = project.create_region_basic(
        name="Gauge target",
        entity_type=allsolve.Region.POINT,
        entity_tags=[34],
    )
    return regions


def create_materials(project: allsolve.Project, regions: SimpleNamespace) -> None:
    project.create_material(
        name="Air",
        description="Air, 20 C, 100kPa",
        color="#99D9FF",
        target_region=regions.Air,
        density="1.225",
        heat_capacity="1012",
        speed_of_sound="343",
        dynamic_viscosity="1.8e-5",
        electric_conductivity="0",
        electric_permittivity="epsilon0",
        magnetic_permeability="mu0",
        thermal_conductivity="0.026",
    )
    project.create_material(
        name="Copper",
        description="Copper",
        color="#DD6839",
        abbreviation="Cu",
        target_region=regions.Copper,
        density="8960",
        heat_capacity="385",
        coefficient_of_thermal_expansion="16.5e-06",
        electric_conductivity="6e7",
        electric_permittivity="epsilon0",
        magnetic_permeability="mu0",
        thermal_conductivity="401",
        elasticity_matrix=allsolve.MaterialProperty.ElasticityMatrixYoungsModulusPoissonsRatio(
            "130e9",
            "0.34",
        ),
    )
    project.create_material(
        name="YBCO superconductor",
        description="YBCO at 77K",
        color="#535050",
        abbreviation="YBCO",
        target_region=regions.sc,
        density="6300",
        heat_capacity="88.8",
        electric_conductivity="powerlaw(j, YBCO_Jc, YBCO_Ec, YBCO_n, 1e3, 1e16)",
        magnetic_permeability="mu0",
        thermal_conductivity="5.75",
    )


def create_physics(
    project: allsolve.Project, regions: SimpleNamespace
) -> allsolve.PhysicsSet:
    physics_set = project.get_default_physics_set()
    magnetism_h_physics = physics_set.add_physics(
        allsolve.Physics.MagnetismH(target=regions.Magnetism_H)
    )
    magnetism_phi_physics = physics_set.add_physics(
        allsolve.Physics.MagnetismPhi(target=regions.Magnetism_Phi)
    )

    # Add interactions
    magnetism_h_physics.add_interactions(
        [
            allsolve.Interaction.MagnetismHHPhiCoupling(
                name="H-φ coupling",
            ),
        ]
    )
    magnetism_phi_physics.add_interactions(
        [
            allsolve.Interaction.MagnetismPhiLumpIV(
                name="Current source",
                circulation_loop=regions.Circulation_loop,
                namespace="lump",
                magnetism_phi_lump_i_v_current="Iop",
            ),
            allsolve.Interaction.MagnetismPhiConstraint(
                name="Gauge",
                target=regions.Gauge_target,
                magnetism_phi_constraint="0",
            ),
        ]
    )
    return physics_set


def create_mesh(
    project: allsolve.Project,
) -> allsolve.Mesh:
    mesh = project.create_mesh(
        allsolve.MeshSettings(
            name="Mesh 1",
            use_mesh_refiner=False,
            scale_factor="1",
            curvature_enhancement="25",
            target_width_to_height_ratio="4",
            max_run_time_minutes=60,
        ),
    )
    return mesh


def create_simulation(
    project: allsolve.Project,
    mesh: allsolve.Mesh,
    physics_set: allsolve.PhysicsSet,
) -> allsolve.Simulation:

    sim1 = project.create_simulation_transient(
        name="Simulation 1",
        description="",
        max_run_time_minutes=60,
        solver_mode=allsolve.SolverMode.ITERATIVE,
        mesh=mesh,
        physics_set=physics_set,
        transient_start_time="0",
        transient_end_time="0.0005",  # simulate only 0.5 milliseconds for demonstration
        transient_timestep_size="0.0001",
        timestep_algorithm=allsolve.TimestepAlgorithm.IMPLICIT_EULER,
    )
    sim1.set_runtime(
        allsolve.Runtime(node_count=50, node_type=allsolve.CPU.CORES_2_32GB)
    )
    sim1.add_outputs(
        [
            allsolve.Output.ValueOutput(
                name="sc loss",
                expression="integrate(reg.sc, transpose(E) * j, 4)",
            ),
            allsolve.Output.ValueOutput(
                name="cu loss",
                expression="integrate(reg.copper, transpose(E) * j, 4)",
            ),
        ]
    )

    # Disable the default formulations script and use the custom script
    sim1.disabled_script_sections = [allsolve.DisableableSection.FORMULATIONS]
    sim1.save()
    sim1.set_scripts(
        [
            allsolve.Script(
                name="formulations.py",
                section_name=allsolve.CustomSection.AFTER_FORMULATIONS_CREATED,
                filepath=os.path.join(SCRIPT_DIR, "scripts", "formulations.py"),
            ),
        ]
    )
    return sim1


def run_mesh_and_simulation(
    mesh: allsolve.Mesh, sim: allsolve.Simulation, verbose: bool = True
) -> None:
    mesh.run(print_logs=verbose, on_error=allsolve.OnError.STRICT)

    sim.run(print_logs=verbose, on_error=allsolve.OnError.STRICT)


def save_simulation_results(
    sim: allsolve.Simulation, *, output_basename: str = "simulation_output.csv"
) -> None:
    output_data = sim.get_output_data()

    output_dir = os.path.join(SCRIPT_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)
    output_csv_path = os.path.join(output_dir, output_basename)
    if os.path.exists(output_csv_path):
        os.remove(output_csv_path)
    output_data.to_csv_file(
        filename=output_csv_path,
        csv_format=allsolve.CsvExportFormat.NORMAL,
        include_overrides=True,
    )
    print(f"Saved results to CSV: {output_csv_path}")

    output_data.clean_cache()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error running project: {e}")
