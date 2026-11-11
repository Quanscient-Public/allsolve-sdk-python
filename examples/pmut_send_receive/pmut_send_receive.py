"""
Transient ultrasound send / receive between two PMUTs in water.

This script demonstrates a transient 3D piezoelectric simulation of two
piezoelectric micromachined ultrasonic transducers (PMUTs) that face each
other across a 5 mm water gap, using the Allsolve SDK.
One PMUT gets a short sin^2 voltage pulse. Its membrane sends an acoustic
pulse through the water, and the other PMUT converts the received pressure
back to a voltage on a floating electrode.

The project consists of:
- Variables for the membrane and piezo dimensions, PMUT distance, and
  driving frequency
- Geometry with two silicon membranes, two PZT discs, and a water cylinder
  between them, fragmented so that the meshes are conformal
- Regions for water, silicon, PZT, clamped membrane rims, ground and signal
  electrodes, and the PML boundary
- Materials for water, monocrystalline silicon (anisotropic elasticity), and
  PZT (anisotropic elasticity, permittivity tensor, piezoelectric coupling)
- Two physics sets with the same three coupled physics: solid mechanics,
  electrostatics with piezoelectricity, and acoustic waves. In "Bottom sends"
  the bottom PMUT is driven and the top PMUT receives, in "Top sends" the
  roles are swapped.
- Coarse mesh with a finer mesh size in the water
- Two transient simulations, one for each physics set

Demonstrates:
- Transient analysis with TimestepAlgorithm.GEN_ALPHA and a target frequency
  for the PML
- Piezoelectricity with solid mechanics: ElectrostaticsPiezoelectricity on
  the electrostatics physics and AcousticWavesAcousticStructure on the
  acoustic waves physics
- A time-dependent voltage pulse with ElectrostaticsConstraint
- A floating electrode: ElectrostaticsLump in CHARGE mode with zero charge,
  its voltage read with the expression "<namespace>.V"
- Several physics sets in one project
- Running several simulations at the same time with allsolve.run_simulations()
- Region selection rules by size and bounding box, with a check of the
  number of selected entities
- CSV export of the transient value outputs

The simulation outputs:
- ValueOutput "Receive voltage" (lump.V) at each time step, saved to a CSV
  file for each simulation. The receiver stays near 0 V until the pulse
  arrives after about 5 mm / 1480 m/s = 3.4 us. Because the model is
  symmetric, both simulations give nearly the same receive voltage.
- FieldOutput for the displacement (u) and the acoustic pressure (p). Add a
  Visualization of "p" in the Allsolve web app to see the wave front move
  from one membrane to the other.
- Use visualize_pmut_send_receive.py to plot the receive voltages.

Use --quick for a shorter run (end time 5 us instead of 7 us).
"""

import argparse
import os
from types import SimpleNamespace

import allsolve

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_NAME = "PMUT send receive"
SIGNAL_EXPRESSION = "ifpositive(0.5e-6 - t, pow(sin(2*pi*freq*t), 2), 0)"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--quick", action="store_true", help="Shorter end time (5 us) for testing"
    )
    args = parser.parse_args()
    end_time = "5e-6" if args.quick else "7e-6"

    client = allsolve.Client()

    project = client.create_project(
        name=PROJECT_NAME,
        description="Transient ultrasound send / receive between two PMUTs in water.",
    )
    print(f"Created project: {project.name} (id: {project.id})")

    try:
        create_variables(project)
        build_geometry(project, verbose=True)
        regions = create_regions(project)
        check_regions(project)
        create_materials(project, regions)
        bottom_sends = create_physics(
            project,
            regions,
            name="Bottom sends",
            signal=regions.bottom_electrode,
            floating=regions.top_electrode,
        )
        top_sends = create_physics(
            project,
            regions,
            name="Top sends",
            signal=regions.top_electrode,
            floating=regions.bottom_electrode,
        )
        project.pml_num_layers = 2
        project.save()
        mesh = create_mesh(project, regions)
        sims = [
            create_simulation(project, mesh, bottom_sends, "Bottom sends", end_time),
            create_simulation(project, mesh, top_sends, "Top sends", end_time),
        ]
        run_mesh_and_simulations(mesh, sims)
        for sim in sims:
            save_results(sim)
        client.set_current_project(project)
    except Exception as e:
        print(f"Error running project: {e}")
    finally:
        if input("Delete project? [Y/n]: ").strip().lower() in ("", "y", "yes"):
            client.set_current_project(None)
            project.delete()
            print("Project deleted.")


def create_variables(project: allsolve.Project) -> None:
    project.create_variables(
        [
            ("thmem", "20e-6", "Silicon membrane thickness"),
            ("radmem", "200e-6", "Membrane radius"),
            ("cov", "0.67", "Piezo disc radius as a fraction of the membrane radius"),
            ("pmutdist", "5e-3", "Distance between the two PMUTs"),
            ("freq", "1e6", "Driving frequency"),
            ("thpiezo", "thmem/5", "Piezo layer thickness"),
        ]
    )


def build_geometry(project: allsolve.Project, verbose: bool = False) -> None:
    geometry_builder = project.geometry_builder()

    # The cylinder position is the center of the cylinder.
    geometry_builder.add_cylinder(
        name="Bottom_membrane",
        position=(0.0, 0.0, 0.0),
        axis=(0.0, 0.0, "thmem"),
        radius="radmem",
    )
    geometry_builder.add_cylinder(
        name="Bottom_piezo",
        position=(0.0, 0.0, "thmem/2 + thpiezo/2"),
        axis=(0.0, 0.0, "thpiezo"),
        radius="radmem*cov",
    )
    geometry_builder.add_cylinder(
        name="Water",
        position=(0.0, 0.0, "pmutdist/2"),
        axis=(0.0, 0.0, "pmutdist - thmem"),
        radius="pmutdist/2",
    )
    geometry_builder.add_cylinder(
        name="Top_membrane",
        position=(0.0, 0.0, "pmutdist"),
        axis=(0.0, 0.0, "thmem"),
        radius="radmem",
    )
    geometry_builder.add_cylinder(
        name="Top_piezo",
        position=(0.0, 0.0, "pmutdist - thmem/2 - thpiezo/2"),
        axis=(0.0, 0.0, "thpiezo"),
        radius="radmem*cov",
    )

    # The piezo discs are inside the water cylinder. Fragmenting removes them
    # from the water and makes the meshes conformal at all interfaces.
    geometry_builder.add_fragment_all(name="Fragment_all")

    geometry_builder.build(print_logs=verbose, on_error=allsolve.OnError.RAISE)


def create_disc_face_region(
    project: allsolve.Project, name: str, z: str
) -> allsolve.Region:
    # The box is only a little larger than the piezo disc, so the membrane
    # faces at the same height are not selected.
    r = "1.1*radmem*cov"
    dz = "thpiezo/10"
    return project.create_region_rule(
        name=name,
        entity_type=allsolve.Region.SURFACE,
        bounding_box=(
            (f"-{r}", f"-{r}", f"{z} - {dz}"),
            (r, r, f"{z} + {dz}"),
        ),
    )


def create_regions(project: allsolve.Project) -> SimpleNamespace:
    regions = SimpleNamespace()

    regions.water = project.create_region_rule(
        name="Water",
        entity_type=allsolve.Region.VOLUME,
        min_size=("pmutdist/2", "pmutdist/2", "pmutdist/2"),
    )
    regions.silicon = project.create_region_rule(
        name="Silicon",
        entity_type=allsolve.Region.VOLUME,
        min_size=("1.5*radmem", "1.5*radmem", "0.5*thmem"),
        max_size=("2.5*radmem", "2.5*radmem", "1.5*thmem"),
    )
    regions.pzt = project.create_region_rule(
        name="PZT",
        entity_type=allsolve.Region.VOLUME,
        max_size=("1.5*radmem", "1.5*radmem", "1.5*thpiezo"),
    )
    regions.solid = project.create_region_computed(
        name="Solid",
        entity_type=allsolve.Region.VOLUME,
        operation=allsolve.RegionOperation.UNION,
        source_regions=[regions.silicon.id, regions.pzt.id],
    )

    # The membrane rims are the only surfaces that are about 2*radmem wide
    # and thmem high.
    regions.clamp = project.create_region_rule(
        name="Clamp",
        entity_type=allsolve.Region.SURFACE,
        min_size=("1.5*radmem", "1.5*radmem", "0.5*thmem"),
        max_size=("2.5*radmem", "2.5*radmem", "1.5*thmem"),
    )
    # Ground: the piezo faces that touch the membranes.
    ground_bottom = create_disc_face_region(project, "Ground bottom", "thmem/2")
    ground_top = create_disc_face_region(project, "Ground top", "pmutdist - thmem/2")
    regions.ground = project.create_region_computed(
        name="Ground",
        entity_type=allsolve.Region.SURFACE,
        operation=allsolve.RegionOperation.UNION,
        source_regions=[ground_bottom.id, ground_top.id],
    )
    # Signal or floating electrodes: the piezo faces that touch the water.
    regions.bottom_electrode = create_disc_face_region(
        project, "Bottom electrode", "thmem/2 + thpiezo"
    )
    regions.top_electrode = create_disc_face_region(
        project, "Top electrode", "pmutdist - thmem/2 - thpiezo"
    )
    # The outer side of the water cylinder is the only surface that is large
    # in all three directions.
    regions.pml_boundary = project.create_region_rule(
        name="PML boundary",
        entity_type=allsolve.Region.SURFACE,
        min_size=("0.9*pmutdist", "0.9*pmutdist", "0.9*pmutdist"),
    )

    return regions


EXPECTED_ENTITY_COUNTS = {
    "Water": 1,
    "Silicon": 2,
    "PZT": 2,
    "Solid": 4,
    "Clamp": 2,
    "Ground bottom": 1,
    "Ground top": 1,
    "Ground": 2,
    "Bottom electrode": 1,
    "Top electrode": 1,
    "PML boundary": 1,
}


def check_regions(project: allsolve.Project) -> None:
    # Make sure that each region rule selects the expected geometry entities.
    errors = []
    for region in project.get_regions():
        count = len(region.entity_tags)
        expected = EXPECTED_ENTITY_COUNTS.get(region.name)
        print(f"Region {region.name!r}: {count} entities")
        if expected is not None and count != expected:
            errors.append(f"{region.name!r}: {count} entities, expected {expected}")
    if errors:
        raise ValueError("Unexpected region selection: " + "; ".join(errors))


def create_materials(project: allsolve.Project, regions: SimpleNamespace) -> None:
    project.create_material(
        name="Water",
        description="Water",
        color="#59AAF3",
        target_region=regions.water,
        density="998",
        speed_of_sound="1480",
        heat_capacity="4182",
        dynamic_viscosity="8.9e-4",
        electric_conductivity="5e-6",
        electric_permittivity="81*epsilon0",
        thermal_conductivity="0.55",
    )
    project.create_material(
        name="Monocrystalline silicon",
        description="Monocrystalline silicon",
        color="#9AA7C5",
        abbreviation="Si",
        target_region=regions.silicon,
        density="2329",
        heat_capacity="700",
        coefficient_of_thermal_expansion="2.6e-6",
        electric_conductivity="0.00031",
        electric_permittivity="11.7*epsilon0",
        thermal_conductivity="149",
        elasticity_matrix=allsolve.MaterialProperty.ElasticityMatrix(
            value=[
                [194.5e9, 35.7e9, 64.1e9, 0.0, 0.0, 0.0],
                [35.7e9, 194.5e9, 64.1e9, 0.0, 0.0, 0.0],
                [64.1e9, 64.1e9, 165.7e9, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 79.6e9, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 79.6e9, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 50.9e9],
            ]
        ),
    )
    # Both discs are poled along +z (the default material orientation).
    project.create_material(
        name="PZT",
        description="Lead zirconate titanate",
        color="#F7EDD3",
        abbreviation="PZT",
        target_region=regions.pzt,
        density="7550",
        heat_capacity="420",
        thermal_conductivity="0.14",
        electric_permittivity=[
            ["1704*epsilon0", 0.0, 0.0],
            [0.0, "1704*epsilon0", 0.0],
            [0.0, 0.0, "1433*epsilon0"],
        ],
        elasticity_matrix=allsolve.MaterialProperty.ElasticityMatrix(
            value=[
                [127e9, 80.2e9, 84.6e9, 0.0, 0.0, 0.0],
                [80.2e9, 127e9, 84.6e9, 0.0, 0.0, 0.0],
                [84.6e9, 84.6e9, 117e9, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 22.9e9, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 22.9e9, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 23.4e9],
            ]
        ),
        piezoelectric_coupling=[
            [0.0, 0.0, -6.62],
            [0.0, 0.0, -6.62],
            [0.0, 0.0, 23.24],
            [0.0, 17.03, 0.0],
            [17.03, 0.0, 0.0],
            [0.0, 0.0, 0.0],
        ],
    )


def create_physics(
    project: allsolve.Project,
    regions: SimpleNamespace,
    name: str,
    signal: allsolve.Region,
    floating: allsolve.Region,
) -> allsolve.PhysicsSet:
    physics_set = project.create_physics_set(name=name)
    solid_mechanics = physics_set.add_physics(
        allsolve.Physics.SolidMechanics(target=regions.solid)
    )
    electrostatics = physics_set.add_physics(
        allsolve.Physics.Electrostatics(target=regions.pzt)
    )
    acoustic_waves = physics_set.add_physics(
        allsolve.Physics.AcousticWaves(target=regions.water)
    )

    solid_mechanics.add_interactions(
        [
            allsolve.Interaction.SolidMechanicsClamp(
                name="Clamp",
                target=regions.clamp,
            ),
        ]
    )

    # With solid mechanics, the piezoelectric coupling is an electrostatics
    # interaction. Add it only once.
    electrostatics.add_interactions(
        [
            allsolve.Interaction.ElectrostaticsConstraint(
                name="Ground",
                target=regions.ground,
                electrostatics_constraint="0",
            ),
            # A single 0.5 us sin^2 pulse from 0 V to 1 V and back to 0 V.
            allsolve.Interaction.ElectrostaticsConstraint(
                name="Signal",
                target=signal,
                electrostatics_constraint=SIGNAL_EXPRESSION,
            ),
            # Floating electrode: zero total charge, the voltage is solved.
            # It is available in outputs as lump.V.
            allsolve.Interaction.ElectrostaticsLump(
                name="Floating electrode",
                target=floating,
                namespace="lump",
                electrostatics_lump_actuation_mode=allsolve.ElectrostaticsLumpActuationMode.CHARGE,
                electrostatics_lump_charge="0",
            ),
            allsolve.Interaction.ElectrostaticsPiezoelectricity(
                name="Piezoelectricity",
                target=regions.pzt,
            ),
        ]
    )

    # AcousticWavesAcousticStructure couples the pressure to solid mechanics
    # on all water-solid interfaces. (Use
    # AcousticWavesAcousticStructureForElasticWaves with elastic waves.)
    acoustic_waves.add_interactions(
        [
            allsolve.Interaction.AcousticWavesPml(
                name="PML",
                target=regions.pml_boundary,
            ),
            allsolve.Interaction.AcousticWavesAcousticStructure(
                name="Acoustic structure",
            ),
        ]
    )

    return physics_set


def create_mesh(project: allsolve.Project, regions: SimpleNamespace) -> allsolve.Mesh:
    return project.create_mesh(
        allsolve.MeshSettings(
            name="Coarse mesh",
            use_mesh_refiner=True,
            curvature_enhancement=36,
            mesh_size_max=1e-3,
            # About 7 elements per wavelength at 1 MHz in water.
            refinements=[allsolve.MeshRefinement(max_size=2e-4, region=regions.water)],
            max_run_time_minutes=60,
        ),
    )


def create_simulation(
    project: allsolve.Project,
    mesh: allsolve.Mesh,
    physics_set: allsolve.PhysicsSet,
    name: str,
    end_time: str,
) -> allsolve.Simulation:
    # Solid mechanics in a transient analysis needs the generalized-alpha
    # time stepping. The target frequency only defines the solver variable f.
    sim = project.create_simulation_transient(
        name=name,
        description="0.5 us sin^2 pulse on one PMUT, voltage on the other PMUT",
        max_run_time_minutes=60,
        solver_mode=allsolve.SolverMode.ITERATIVE,
        transient_start_time="0",
        transient_end_time=end_time,
        transient_timestep_size="1e-7",
        timestep_algorithm=allsolve.TimestepAlgorithm.GEN_ALPHA,
        target_frequency="freq",
        mesh=mesh,
        physics_set=physics_set,
    )
    sim.add_outputs(
        [
            allsolve.Output.FieldOutput(name="u", expression="u"),
            allsolve.Output.FieldOutput(name="p", expression="p"),
            allsolve.Output.ValueOutput(
                name="Drive voltage", expression=SIGNAL_EXPRESSION
            ),
            allsolve.Output.ValueOutput(name="Receive voltage", expression="lump.V"),
        ]
    )
    return sim


def run_mesh_and_simulations(
    mesh: allsolve.Mesh, sims: list[allsolve.Simulation]
) -> None:
    mesh.run(print_logs=True, on_error=allsolve.OnError.STRICT)
    allsolve.run_simulations(sims, print_status=True, on_error=allsolve.OnError.STRICT)


def save_results(sim: allsolve.Simulation) -> None:
    output_data = sim.get_output_data()

    output_dir = os.path.join(SCRIPT_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)
    file_name = sim.name.lower().replace(" ", "_")
    output_csv_path = os.path.join(output_dir, f"{file_name}_output.csv")
    if os.path.exists(output_csv_path):
        os.remove(output_csv_path)
    output_data.to_csv_file(
        filename=output_csv_path,
        csv_format=allsolve.CsvExportFormat.NORMAL,
    )
    print(f"Saved results to CSV: {output_csv_path}")

    output_data.clean_cache()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
