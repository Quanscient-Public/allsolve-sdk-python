"""
This script demonstrates a multiphysics harmonic simulation of ultrasound
emission from a piezoelectric micromachined ultrasonic transducer (PMUT) array
using the Allsolve SDK.
The project consists of:
- Variables for the membrane, piezo layer, cavity dimensions, array size,
  excitation frequency, and surrounding air domain radius
- Geometry with circular membranes, PZT piezo discs, and back-cavities
  arranged in an n-by-n grid, enclosed by an air dome with a cut-away
  baseplate
- Regions for the air domain, PZT elements, silicon membranes, baseplate,
  electrode surfaces, a measurement point above the array, and the PML boundary
- Materials for air, PZT-5H (with anisotropic permittivity, full elasticity
  matrix, and piezoelectric coupling), and monocrystalline silicon (with
  anisotropic elasticity)
- Three coupled physics: elastic waves in solids, acoustic waves in air,
  and electrostatics in the PZT layer, with interactions for clamping,
  piezoelectricity, PML absorption, acoustic-structure coupling, ground
  electrode, and sinusoidal voltage excitation
- A frequency sweep over 41 points from 0.7 MHz to 0.9 MHz using
  variable overrides
- Mesh with adaptive refinement enabled
- Harmonic simulation with 3 FFT samples driven at the sweep frequency

The simulation outputs:
- ValueOutput for maximum displacement (U max), pressure above the array (P above),
  and drive voltage/current (V drive real, I drive real, I drive imag).
  The value output data is saved to a CSV file.
- FieldOutput for the second-harmonic displacement field (u) and
  pressure field (p) with both cosine and sine components ("p harmonic 2"
  and "p harmonic 3"). These can be visualized in the Allsolve web app
  to inspect the acoustic radiation pattern across the frequency sweep.
  The two pressure components allow time-domain reconstruction:
  p(x,t) = harm2(x)*sin(wt) + harm3(x)*cos(wt).
  Add a new Visualization and select "p harmonic 2" field with a Slice filter
  to visualize the FieldOutput on the air region.
- Use visualize_pmut_array_results.py to generate a frequency response plot
  and time-domain pressure animation.
"""

import os

import allsolve
from types import SimpleNamespace

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    client = allsolve.Client()

    verbose = True

    project = client.create_project(
        name="PMUT array demo",
        description="Simulation of ultrasound emission from an array of PMUTs.",
    )
    print(f"Created project: {project.name} (id: {project.id})")

    create_variables(project)
    build_geometry(project, verbose=verbose)
    regions = create_regions(project)
    create_materials(project, regions)
    create_physics(project, regions)
    sweep = create_sweep(project)
    mesh = create_mesh(project)
    sim = create_simulation(project, mesh, sweep)
    run_mesh_and_simulation(mesh, sim, verbose=verbose)
    save_results(sim)

    client.set_current_project(project)


def create_variables(project: allsolve.Project) -> None:
    project.create_variables(
        [
            ("R", "100e-6", "Cavity radius"),
            ("thmem", "10e-6", "Membrane thickness"),
            ("thpiezo", "2e-6", "Piezo thickness"),
            ("thcavity", "20e-6", "Cavity thickness"),
            ("n", "2", "Array size (even numbers only)"),
            ("freq", "1e6", "Frequency"),
            ("Rair", "5*R*n", "Air bubble radius"),
        ]
    )


def build_geometry(project: allsolve.Project, verbose: bool = False) -> None:
    geometry_builder = project.geometry_builder()

    geometry_builder.add_cylinder(
        name="Membrane",
        position=("-4*R*(n-1)/2", "-4*R*(n-1)/2", 0.0),
        axis=(0.0, 0.0, "thmem"),
        radius="R",
    )

    geometry_builder.add_cylinder(
        name="Piezo",
        position=("-4*R*(n-1)/2", "-4*R*(n-1)/2", "thmem/2 + thpiezo/2"),
        axis=(0.0, 0.0, "thpiezo"),
        radius="0.67*R",
    )

    geometry_builder.add_cylinder(
        name="Cavity",
        position=("-4*R*(n-1)/2", "-4*R*(n-1)/2", "-thcavity/2 - thmem/2"),
        axis=(0.0, 0.0, "thcavity"),
        radius="R",
    )

    geometry_builder.add_grid(
        name="PMUT_grid",
        translation=("4*R", "4*R", 0.0),
        size=("n", "n", 1),
        cad_names=["Membrane", "Piezo", "Cavity"],
    )

    geometry_builder.add_sphere(
        name="Air_sphere",
        position=(0.0, 0.0, 0.0),
        radius="Rair",
    )

    geometry_builder.add_box(
        name="Sphere_bottom_cut",
        position=(0.0, 0.0, "(-Rair + thmem/2) / 2"),
        size=("2*Rair + 0.001", "2*Rair + 0.001", "Rair + thmem/2"),
    )

    geometry_builder.add_difference(
        name="Air_dome",
        cad_names_1=["Air_sphere"],
        cad_names_2=["Sphere_bottom_cut"],
    )

    geometry_builder.add_cylinder(
        name="Baseplate",
        position=(0.0, 0.0, "-thcavity/2"),
        axis=(0.0, 0.0, "thmem + thcavity"),
        radius="Rair",
    )

    geometry_builder.add_difference(
        name="Baseplate_with_holes",
        cad_names_1=["Baseplate"],
        cad_names_2=["Cavity"],
    )

    geometry_builder.add_difference(
        name="Baseplate_with_holes_2",
        cad_names_1=["Baseplate"],
        cad_names_2=["Membrane"],
        delete_tool=False,
    )

    geometry_builder.add_difference(
        name="Air_dome_2",
        cad_names_1=["Air_sphere"],
        cad_names_2=["Piezo"],
        delete_tool=False,
    )

    geometry_builder.build(print_logs=verbose, on_error=allsolve.OnError.RAISE)


def create_regions(project: allsolve.Project) -> SimpleNamespace:
    regions = SimpleNamespace()

    regions.air_bubble = project.create_region_rule(
        name="air_bubble",
        entity_type=allsolve.Region.VOLUME,
        min_size=("1.5*Rair", "1.5*Rair", "0.5*Rair"),
    )
    regions.pzt = project.create_region_rule(
        name="pzt",
        entity_type=allsolve.Region.VOLUME,
        max_size=("2*0.67*R", "2*0.67*R", "thpiezo"),
    )
    regions.membranes = project.create_region_rule(
        name="membranes",
        entity_type=allsolve.Region.VOLUME,
        attribute_path=allsolve.KeyValueAttributePath(path=[("name", "Membrane")]),
    )
    regions.baseplate_clamp = project.create_region_rule(
        name="baseplate_clamp",
        entity_type=allsolve.Region.VOLUME,
        attribute_path=allsolve.KeyValueAttributePath(path=[("name", "Baseplate")]),
    )
    regions.air_dome_surface = project.create_region_rule(
        name="air_dome_surface",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=(
            ("-Rair", "-Rair", "0"),
            ("Rair", "Rair", "Rair"),
        ),
        min_size=("Rair", "Rair", "0.5*Rair"),
    )
    regions.pzt_bottom_surfaces = project.create_region_rule(
        name="pzt_bottom_surfaces",
        entity_type=allsolve.Region.SURFACE,
        attribute_path=allsolve.KeyValueAttributePath(path=[("name", "Piezo")]),
        bounding_box=(
            ("-4*R*(n-1)/2 - R", "-4*R*(n-1)/2 - R", "thmem/2"),
            ("4*R*(n-1)/2 + R", "4*R*(n-1)/2 + R", "thmem/2"),
        ),
    )
    regions.pzt_top_surfaces = project.create_region_rule(
        name="pzt_top_surfaces",
        entity_type=allsolve.Region.SURFACE,
        attribute_path=allsolve.KeyValueAttributePath(path=[("name", "Piezo")]),
        bounding_box=(
            ("-4*R*(n-1)/2 - R", "-4*R*(n-1)/2 - R", "thmem/2 + thpiezo"),
            ("4*R*(n-1)/2 + R", "4*R*(n-1)/2 + R", "thmem/2 + thpiezo"),
        ),
    )

    regions.mono_si = project.create_region_computed(
        name="mono_si",
        entity_type=allsolve.Region.VOLUME,
        operation=allsolve.RegionOperation.UNION,
        source_regions=[regions.baseplate_clamp.id, regions.membranes.id],
    )
    regions.solid_volumes = project.create_region_computed(
        name="solid_volumes",
        entity_type=allsolve.Region.VOLUME,
        operation=allsolve.RegionOperation.UNION,
        source_regions=[regions.mono_si.id, regions.pzt.id],
    )
    regions.p_above = project.create_region_rule(
        name="p_above",
        entity_type=allsolve.Region.POINT,
        bounding_box=(
            ("-0.1*Rair", "-0.1*Rair", "0.9*Rair"),
            ("0.1*Rair", "0.1*Rair", "1.1*Rair"),
        ),
    )

    return regions


def create_materials(project: allsolve.Project, regions: SimpleNamespace) -> None:
    project.create_material(
        name="Air",
        description="Air, 20 C, 100kPa",
        color="#99D9FF",
        target_region=regions.air_bubble,
        density="1.225",
        heat_capacity="1012",
        speed_of_sound="343",
        dynamic_viscosity="1.8e-05",
        electric_conductivity="0",
        electric_permittivity="epsilon0",
        magnetic_permeability="mu0",
        thermal_conductivity="0.026",
    )
    project.create_material(
        name="PZT",
        description="Lead zirconate titanate (PZT-5H)",
        color="#FFD700",
        abbreviation="PZT",
        target_region=regions.pzt,
        density="7500",
        heat_capacity="420",
        electric_permittivity=[
            ["1704 * epsilon0", 0.0, 0.0],
            [0.0, "1704 * epsilon0", 0.0],
            [0.0, 0.0, "1433 * epsilon0"],
        ],
        thermal_conductivity="0.14",
        elasticity_matrix=allsolve.MaterialProperty.ElasticityMatrix(
            value=[
                [127000000000.0, 80200000000.0, 84600000000.0, 0.0, 0.0, 0.0],
                [80200000000.0, 127000000000.0, 84600000000.0, 0.0, 0.0, 0.0],
                [84600000000.0, 84600000000.0, 117000000000.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 22900000000.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 22900000000.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 23400000000.0],
            ]
        ),
        piezoelectric_coupling=[
            [0.0, 0.0, -6.6],
            [0.0, 0.0, -6.6],
            [0.0, 0.0, 23.2],
            [0.0, 0.0, 0.0],
            [0.0, 17.0, 0.0],
            [17.0, 0.0, 0.0],
        ],
    )
    project.create_material(
        name="Monocrystalline silicon",
        description="Monocrystalline silicon",
        color="#808080",
        abbreviation="Si",
        target_region=regions.mono_si,
        density="2329",
        heat_capacity="700",
        coefficient_of_thermal_expansion="2.6e-6",
        electric_conductivity="0.00031",
        electric_permittivity="11.7*epsilon0",
        magnetic_permeability="mu0",
        thermal_conductivity="149",
        elasticity_matrix=allsolve.MaterialProperty.ElasticityMatrix(
            value=[
                [194500000000.0, 35700000000.0, 64100000000.0, 0.0, 0.0, 0.0],
                [35700000000.0, 194500000000.0, 64100000000.0, 0.0, 0.0, 0.0],
                [64100000000.0, 64100000000.0, 165700000000.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 79600000000.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 79600000000.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 50900000000.0],
            ]
        ),
    )


def create_physics(project: allsolve.Project, regions: SimpleNamespace) -> None:
    elastic_waves_physics = project.add_physics(
        allsolve.Physics.ElasticWaves(target=regions.solid_volumes)
    )
    acoustic_waves_physics = project.add_physics(
        allsolve.Physics.AcousticWaves(target=regions.air_bubble)
    )
    electrostatics_physics = project.add_physics(
        allsolve.Physics.Electrostatics(target=regions.pzt)
    )

    elastic_waves_physics.add_interactions(
        [
            allsolve.Interaction.ElasticWavesClamp(
                name="Clamp",
                target=regions.baseplate_clamp,
            ),
            allsolve.Interaction.ElasticWavesPiezoelectricity(
                name="Piezoelectricity",
                target=regions.pzt,
            ),
        ]
    )

    acoustic_waves_physics.add_interactions(
        [
            allsolve.Interaction.AcousticWavesPml(
                name="PML",
                target=regions.air_dome_surface,
            ),
            allsolve.Interaction.AcousticWavesAcousticStructureForElasticWaves(
                name="Acoustic structure",
            ),
        ]
    )

    electrostatics_physics.add_interactions(
        [
            allsolve.Interaction.ElectrostaticsConstraint(
                name="Ground",
                target=regions.pzt_bottom_surfaces,
                electrostatics_constraint="0",
            ),
            allsolve.Interaction.ElectrostaticsLump(
                name="Voltage excitation",
                target=regions.pzt_top_surfaces,
                namespace="lump",
                electrostatics_lump_voltage="sin(2*pi*freq*t)",
            ),
        ]
    )

    project.pml_num_layers = 2
    project.save()


def create_sweep(project: allsolve.Project) -> allsolve.VariableOverrides:
    sweep = project.create_variable_overrides(
        name="freq_sweep",
        sweep_type=allsolve.SweepType.SPECIFIC_VALUES,
        overrides=[
            ("freq", "linspace(0.7e6, 0.9e6, 41)"),
        ],
    )
    return sweep


def create_mesh(project: allsolve.Project) -> allsolve.Mesh:
    mesh = project.create_mesh(
        allsolve.MeshSettings(
            name="Mesh 1",
            # If low quality elements are detected in the initial mesh,
            # the mesh refiner will perform adaptive refinement and remeshing
            use_mesh_refiner=True,
            scale_factor=1.0,
            curvature_enhancement=6.0,
            target_width_to_height_ratio=4.0,
            max_run_time_minutes=60,
            mesh_size_max=0.0001,
            mesh_size_min=0.0,
        ),
    )
    return mesh


def create_simulation(
    project: allsolve.Project, mesh: allsolve.Mesh, sweep: allsolve.VariableOverrides
) -> allsolve.Simulation:
    sim = project.create_simulation_harmonic(
        name="Simulation 1",
        description="",
        max_run_time_minutes=60,
        solver_mode=allsolve.SolverMode.DIRECT,
        mesh=mesh.id,
        fundamental_frequency="freq",
        num_fft_samples=3,
        variable_overrides=sweep.id,
    )
    sim.add_outputs(
        [
            allsolve.Output.FieldOutput(
                name="u harmonic 2",
                expression="harm(2, u)",
                field_output_skin_only=True,
            ),
            allsolve.Output.FieldOutput(
                name="p harmonic 2",
                expression="harm(2, p)",
                field_output_skin_only=False,
            ),
            allsolve.Output.FieldOutput(
                name="p harmonic 3",
                expression="harm(3, p)",
                field_output_skin_only=False,
            ),
            allsolve.Output.ValueOutput(
                name="P above",
                expression="probe(reg.p_above, sqrt(pow(harm(2, p), 2) + pow(harm(3, p), 2)))",
            ),
            allsolve.Output.ValueOutput(
                name="U max",
                expression="maxvalue(reg.solid_volumes, sqrt(pow(harm(2, compz(u)), 2) + pow(harm(3, compz(u)), 2)), 5)",
            ),
            allsolve.Output.ValueOutput(
                name="V drive real",
                expression="harm(2, lump.V)",
            ),
            allsolve.Output.ValueOutput(
                name="I drive real",
                expression="harm(2, dt(lump.Q))",
            ),
            allsolve.Output.ValueOutput(
                name="I drive imag",
                expression="harm(3, dt(lump.Q))",
            ),
        ]
    )
    return sim


def run_mesh_and_simulation(
    mesh: allsolve.Mesh, sim: allsolve.Simulation, verbose: bool = False
) -> None:
    mesh.run(print_logs=verbose)
    if mesh.get_status() != allsolve.Job.SUCCESS:
        raise ValueError(f"Mesh processing failed: {mesh.get_status()}")

    sim.run(print_logs=verbose)
    print("Simulation status:", sim.get_status())
    if sim.get_status() != allsolve.Job.SUCCESS:
        raise ValueError(f"Simulation failed: {sim.get_status()}")


def save_results(sim: allsolve.Simulation) -> None:
    output_data = sim.get_output_data()

    output_dir = os.path.join(SCRIPT_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)
    output_csv_path = os.path.join(output_dir, "pmut_array_demo_output.csv")
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
    main()
