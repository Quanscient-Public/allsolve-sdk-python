"""
Electrical impedance of a thickness-poled PZT disc radiating into water,
simulated with the Allsolve SDK.

Demonstrates:
- A 1/8 symmetry model of a 3D device, with the lumped voltage and current
  scaled back to the impedance of the full device
- Symmetry faces and electrode faces selected with region rules written
  with the project variables (no hard-coded entity tags), and a check of
  the region entity counts after the geometry is built
- An AML type PML on a curved (spherical) outer boundary
- A harmonic drive with sn(1) and complex impedance from the sin and cos
  harmonics, computed with project functions
- A single-frequency run followed by a frequency sweep
- CSV export of the value outputs

The project consists of:
- Variables for the disc radius and thickness, the water layer thickness
  (R_water = R_disc + t_water), the drive frequency and voltage, the mesh
  size and the symmetry scaling factors
- Geometry: one octant (x, y, z >= 0) of a PZT disc centred in a water sphere
- Regions: PZT and water volumes, the top electrode, the mid-plane (z = 0),
  the x = 0 and y = 0 faces of the disc, and the outer water surface
- Materials: PZT (anisotropic permittivity, elasticity matrix and
  piezoelectric coupling in e form) and water
- Physics: elastic waves and electrostatics in the PZT, acoustic waves in
  the water, with piezoelectricity, symmetry, acoustic-structure coupling,
  PML, a 0 V mid-plane and a lumped voltage drive on the top electrode

Symmetry model and impedance scaling:
- The device is symmetric about x = 0, y = 0 and z = 0. On these planes the
  normal displacement is zero (ElasticWavesSymmetry). The normal electric
  flux and the normal pressure gradient are zero there too, which are the
  natural boundary conditions, so no interaction is needed for them.
- With +V0/2 on the top electrode and -V0/2 on the bottom electrode, the
  potential is antisymmetric about z = 0, so the mid-plane is at 0 V. The
  octant model therefore drives the top electrode with V0/2*sn(1), and the
  full disc sees V0 across its electrodes.
- The lump voltage is half of the full-disc voltage (V_scale = 2), and the
  octant top electrode carries 1/4 of the full-disc current (I_scale = 4):
      Z_full = (V_scale * V_lump) / (I_scale * I_lump) = Z_lump / 2

Phasor convention:
- A harmonic simulation solves harmonics 2 and 3 of the fundamental
  frequency: x(t) = harm(2, x)*sin(wt) + harm(3, x)*cos(wt).
- The complex amplitude is X = harm(3, x) - j*harm(2, x). With
  V = Vc - j*Vs and I = Ic - j*Is:
      Re(Z) = (Vs*Is + Vc*Ic) / (Is^2 + Ic^2)
      Im(Z) = (Vc*Is - Vs*Ic) / (Is^2 + Ic^2)
- The current into the electrode is dt(lump.Q).

Two simulations are created:
1. "Single frequency": harmonic at freq (404 kHz), with the impedance,
   the maximum |uz| and |p|, and displacement and pressure field outputs
2. "Frequency sweep": harmonic sweep from 312 kHz to 512 kHz in 2 kHz steps
   (101 points), with the impedance only

Run with --quick for a smoke test: a coarse mesh and a 3-point sweep.
Use visualize_pzt_disc_results.py to plot |Z| against frequency and the
pressure field.
"""

import argparse
import os

import allsolve
from types import SimpleNamespace

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_NAME = "PZT disc in water"

SWEEP_START_HZ = 312e3
SWEEP_STOP_HZ = 512e3
SWEEP_POINTS = 101
QUICK_SWEEP_POINTS = 3

# Maximum element size: about 1 mm resolves the acoustic wavelength in water
# (2.9 mm at 512 kHz). The quick mode uses a coarse mesh for a smoke test.
H_MAX = "1e-3"
QUICK_H_MAX = "2e-3"


def main():
    parser = argparse.ArgumentParser(description="PZT disc in water impedance demo")
    parser.add_argument(
        "--quick",
        action="store_true",
        help=f"Coarse mesh and a {QUICK_SWEEP_POINTS}-point sweep (smoke test)",
    )
    args = parser.parse_args()
    sweep_points = QUICK_SWEEP_POINTS if args.quick else SWEEP_POINTS
    h_max = QUICK_H_MAX if args.quick else H_MAX

    client = allsolve.Client()

    verbose = True

    project = client.create_project(
        name=PROJECT_NAME,
        description="Impedance of a thickness-poled PZT disc in water (1/8 symmetry model).",
    )
    print(f"Created project: {project.name} (id: {project.id})")

    try:
        create_variables(project, h_max)
        create_functions(project)
        build_geometry(project, verbose=verbose)
        regions = create_regions(project)
        check_regions(project, regions)
        create_materials(project, regions)
        physics_set = create_physics(project, regions)
        mesh = create_mesh(project)
        sim_single = create_single_frequency_simulation(project, mesh, physics_set)
        sweep = create_sweep(project, sweep_points)
        sim_sweep = create_sweep_simulation(
            project, mesh, physics_set, sweep, sweep_points
        )

        mesh.run(print_logs=verbose, on_error=allsolve.OnError.STRICT)
        print("Mesh metrics:", mesh.get_metrics())

        # Check one frequency before the sweep starts many parallel solves.
        sim_single.run(print_logs=verbose, on_error=allsolve.OnError.STRICT)
        output_data = sim_single.get_output_data()
        print(
            f"|Z| at {get_value(output_data, 'Frequency') / 1e3:g} kHz: "
            f"{get_value(output_data, 'Z abs'):.4g} ohm (full disc)"
        )
        save_results(sim_single, "pzt_disc_single_frequency.csv")

        sim_sweep.run(print_logs=verbose, on_error=allsolve.OnError.STRICT)
        save_results(sim_sweep, "pzt_disc_sweep.csv")
        client.set_current_project(project)
    except Exception as e:
        print(f"Error running project: {e}")
    finally:
        if input("Delete project? [Y/n]: ").strip().lower() in ("", "y", "yes"):
            client.set_current_project(None)
            project.delete()
            print("Project deleted.")


def create_variables(project: allsolve.Project, h_max: str) -> None:
    project.create_variables(
        [
            ("R_disc", "20e-3", "PZT disc radius [m]"),
            ("t_disc", "5e-3", "PZT disc thickness [m]"),
            ("t_water", "5e-3", "Water layer between the disc rim and the PML [m]"),
            ("R_water", "R_disc + t_water", "Water sphere radius [m]"),
            ("freq", "404e3", "Drive frequency [Hz]"),
            ("V0", "1", "Drive voltage amplitude across the full disc [V]"),
            ("h_max", h_max, "Maximum mesh element size [m]"),
            ("tol", "1e-6", "Geometric tolerance for the region rules [m]"),
            ("V_scale", "2", "Full-disc voltage / lump voltage (mid-plane at 0 V)"),
            ("I_scale", "4", "Full-disc current / lump current (quarter electrode)"),
        ]
    )


def create_functions(project: allsolve.Project) -> None:
    # Vs, Vc, Is, Ic are the sin (harm 2) and cos (harm 3) components of V and I.
    project.create_function(
        name="z_re",
        args=["Vs", "Vc", "Is", "Ic"],
        expression="(Vs*Is + Vc*Ic) / (Is*Is + Ic*Ic)",
        description="Real part of V/I",
    )
    project.create_function(
        name="z_im",
        args=["Vs", "Vc", "Is", "Ic"],
        expression="(Vc*Is - Vs*Ic) / (Is*Is + Ic*Ic)",
        description="Imaginary part of V/I",
    )


def build_geometry(project: allsolve.Project, verbose: bool = False) -> None:
    geometry_builder = project.geometry_builder()

    geometry_builder.add_box(
        name="Octant",
        position=("R_water", "R_water", "R_water"),
        size=("2*R_water", "2*R_water", "2*R_water"),
    )
    geometry_builder.add_sphere(
        name="Water",
        position=(0.0, 0.0, 0.0),
        radius="R_water",
    )
    geometry_builder.add_cylinder(
        name="Disc",
        position=(0.0, 0.0, 0.0),
        axis=(0.0, 0.0, "t_disc"),
        radius="R_disc",
    )

    # Keep only the octant x, y, z >= 0 of both bodies.
    geometry_builder.add_intersection(
        name="Water_octant",
        cad_names_1=["Water"],
        cad_names_2=["Octant"],
        delete_tool=False,
    )
    geometry_builder.add_intersection(
        name="Disc_octant",
        cad_names_1=["Disc"],
        cad_names_2=["Octant"],
    )
    # Cut the disc out of the water, but keep the disc.
    geometry_builder.add_difference(
        name="Water_around_disc",
        cad_names_1=["Water"],
        cad_names_2=["Disc"],
        delete_tool=False,
    )

    geometry_builder.build(print_logs=verbose, on_error=allsolve.OnError.RAISE)


def create_regions(project: allsolve.Project) -> SimpleNamespace:
    regions = SimpleNamespace()

    regions.pzt = project.create_region_rule(
        name="pzt",
        entity_type=allsolve.Region.VOLUME,
        max_size=("R_disc + tol", "R_disc + tol", "t_disc/2 + tol"),
    )
    regions.water = project.create_region_rule(
        name="water",
        entity_type=allsolve.Region.VOLUME,
        min_size=("0.9*R_water", "0.9*R_water", "0.9*R_water"),
    )
    # The curved outer surface is the only water surface that is large in
    # all three directions.
    regions.water_outer_surface = project.create_region_rule(
        name="water_outer_surface",
        entity_type=allsolve.Region.SURFACE,
        min_size=("0.9*R_water", "0.9*R_water", "0.9*R_water"),
    )

    # Faces of the disc octant: a bounding box rule selects the faces that
    # lie completely inside the box.
    regions.pzt_top = project.create_region_rule(
        name="pzt_top",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=(
            ("-tol", "-tol", "t_disc/2 - tol"),
            ("R_disc + tol", "R_disc + tol", "t_disc/2 + tol"),
        ),
    )
    regions.pzt_mid = project.create_region_rule(
        name="pzt_mid",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=(
            ("-tol", "-tol", "-tol"),
            ("R_disc + tol", "R_disc + tol", "tol"),
        ),
    )
    regions.pzt_x0 = project.create_region_rule(
        name="pzt_x0",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=(
            ("-tol", "-tol", "-tol"),
            ("tol", "R_disc + tol", "t_disc/2 + tol"),
        ),
    )
    regions.pzt_y0 = project.create_region_rule(
        name="pzt_y0",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=(
            ("-tol", "-tol", "-tol"),
            ("R_disc + tol", "tol", "t_disc/2 + tol"),
        ),
    )
    regions.pzt_symmetry = project.create_region_computed(
        name="pzt_symmetry",
        entity_type=allsolve.Region.SURFACE,
        operation=allsolve.RegionOperation.UNION,
        source_regions=[regions.pzt_mid.id, regions.pzt_x0.id, regions.pzt_y0.id],
    )

    return regions


def check_regions(project: allsolve.Project, regions: SimpleNamespace) -> None:
    # A rule that matches no entity, or too many, fails silently. Check the
    # counts so that a changed geometry cannot select the wrong faces.
    expected = {
        "pzt": 1,
        "water": 1,
        "water_outer_surface": 1,
        "pzt_top": 1,
        "pzt_mid": 1,
        "pzt_x0": 1,
        "pzt_y0": 1,
        "pzt_symmetry": 3,
    }
    counts = {r.name: len(r.entity_tags) for r in project.get_regions()}
    for name, count in expected.items():
        if counts.get(name) != count:
            raise ValueError(
                f"Region {name!r} has {counts.get(name)} entities, expected {count}"
            )
    print("Region entity counts:", {name: counts[name] for name in expected})


def create_materials(project: allsolve.Project, regions: SimpleNamespace) -> None:
    project.create_material(
        name="Water",
        description="Water",
        color="#59AAF3",
        target_region=regions.water,
        density="998",
        speed_of_sound="1480",
    )
    project.create_material(
        name="PZT",
        description="PZT, poled along z",
        color="#F7EDD3",
        abbreviation="PZT",
        target_region=regions.pzt,
        density="7550",
        electric_permittivity=[
            ["1704 * epsilon0", 0.0, 0.0],
            [0.0, "1704 * epsilon0", 0.0],
            [0.0, 0.0, "1433 * epsilon0"],
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
        # e matrix [C/m^2], one row per Voigt strain component.
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
    project: allsolve.Project, regions: SimpleNamespace
) -> allsolve.PhysicsSet:
    physics_set = project.get_default_physics_set()
    elastic_waves = physics_set.add_physics(
        allsolve.Physics.ElasticWaves(target=regions.pzt)
    )
    acoustic_waves = physics_set.add_physics(
        allsolve.Physics.AcousticWaves(target=regions.water)
    )
    electrostatics = physics_set.add_physics(
        allsolve.Physics.Electrostatics(target=regions.pzt)
    )

    elastic_waves.add_interactions(
        [
            allsolve.Interaction.ElasticWavesPiezoelectricity(
                name="Piezoelectricity",
                target=regions.pzt,
            ),
            allsolve.Interaction.ElasticWavesSymmetry(
                name="Symmetry",
                target=regions.pzt_symmetry,
            ),
        ]
    )
    acoustic_waves.add_interactions(
        [
            # AML follows a curved boundary. Box PML suits flat boundaries.
            allsolve.Interaction.AcousticWavesPml(
                name="PML",
                target=regions.water_outer_surface,
                acoustic_waves_pml_type=allsolve.AcousticWavesPmlType.AML,
            ),
            allsolve.Interaction.AcousticWavesAcousticStructureForElasticWaves(
                name="Acoustic structure",
            ),
        ]
    )
    electrostatics.add_interactions(
        [
            allsolve.Interaction.ElectrostaticsConstraint(
                name="Mid-plane 0 V",
                target=regions.pzt_mid,
                electrostatics_constraint="0",
            ),
            allsolve.Interaction.ElectrostaticsLump(
                name="Top electrode",
                target=regions.pzt_top,
                namespace="lump",
                electrostatics_lump_voltage="V0/2*sn(1)",
            ),
        ]
    )

    # The PML layers are extruded outward from the outer water surface.
    project.pml_num_layers = 4
    project.save()
    return physics_set


def create_mesh(project: allsolve.Project) -> allsolve.Mesh:
    return project.create_mesh(
        allsolve.MeshSettings(
            name="Mesh h_max",
            max_run_time_minutes=30,
            mesh_size_max="h_max",
            mesh_size_min=0.0,
        ),
    )


def impedance_outputs() -> list:
    v = "harm(2, lump.V), harm(3, lump.V)"
    i = "harm(2, dt(lump.Q)), harm(3, dt(lump.Q))"
    z_re = f"V_scale/I_scale * z_re({v}, {i})"
    z_im = f"V_scale/I_scale * z_im({v}, {i})"
    return [
        allsolve.Output.ValueOutput(name="Frequency", expression="freq"),
        allsolve.Output.ValueOutput(name="Z real", expression=z_re),
        allsolve.Output.ValueOutput(name="Z imag", expression=z_im),
        allsolve.Output.ValueOutput(
            name="Z abs", expression=f"sqrt(pow({z_re}, 2) + pow({z_im}, 2))"
        ),
    ]


def magnitude(expression: str) -> str:
    return f"sqrt(pow(harm(2, {expression}), 2) + pow(harm(3, {expression}), 2))"


def create_single_frequency_simulation(
    project: allsolve.Project, mesh: allsolve.Mesh, physics_set: allsolve.PhysicsSet
) -> allsolve.Simulation:
    sim = project.create_simulation_harmonic(
        name="Single frequency",
        description="Harmonic simulation at freq",
        max_run_time_minutes=30,
        solver_mode=allsolve.SolverMode.DIRECT,
        mesh=mesh.id,
        fundamental_frequency="freq",
        physics_set=physics_set,
    )
    sim.add_outputs(
        impedance_outputs()
        + [
            allsolve.Output.ValueOutput(
                name="Uz max",
                expression=f"maxvalue(reg.pzt, {magnitude('compz(u)')}, 5)",
            ),
            allsolve.Output.ValueOutput(
                name="P max",
                expression=f"maxvalue(reg.water, {magnitude('p')}, 5)",
            ),
            # Geometry values for the visualize script.
            allsolve.Output.ValueOutput(name="R disc", expression="R_disc"),
            allsolve.Output.ValueOutput(name="t disc", expression="t_disc"),
            allsolve.Output.ValueOutput(name="R water", expression="R_water"),
            allsolve.Output.FieldOutput(name="u sin", expression="harm(2, u)"),
            allsolve.Output.FieldOutput(name="u cos", expression="harm(3, u)"),
            allsolve.Output.FieldOutput(name="p sin", expression="harm(2, p)"),
            allsolve.Output.FieldOutput(name="p cos", expression="harm(3, p)"),
        ]
    )
    return sim


def create_sweep(
    project: allsolve.Project, sweep_points: int
) -> allsolve.VariableOverrides:
    return project.create_variable_overrides(
        name="freq_sweep",
        sweep_type=allsolve.SweepType.SPECIFIC_VALUES,
        overrides=[
            (
                "freq",
                f"linspace({SWEEP_START_HZ:g}, {SWEEP_STOP_HZ:g}, {sweep_points})",
            ),
        ],
    )


def create_sweep_simulation(
    project: allsolve.Project,
    mesh: allsolve.Mesh,
    physics_set: allsolve.PhysicsSet,
    sweep: allsolve.VariableOverrides,
    sweep_points: int,
) -> allsolve.Simulation:
    sim = project.create_simulation_harmonic(
        name="Frequency sweep",
        description=f"Harmonic frequency sweep, {sweep_points} points",
        # Each frequency is a separate solve: scale the time limit with the
        # number of points in case the solves do not all run in parallel.
        max_run_time_minutes=30 + 2 * sweep_points,
        solver_mode=allsolve.SolverMode.DIRECT,
        mesh=mesh.id,
        fundamental_frequency="freq",
        variable_overrides=sweep.id,
        physics_set=physics_set,
    )
    sim.add_outputs(impedance_outputs())
    return sim


def get_value(output_data: allsolve.SimulationOutputData, name: str) -> float:
    value = output_data.get_value_at(0, 0, name)
    if value is None:
        raise ValueError(f"Value output {name!r} not found")
    return value


def save_results(sim: allsolve.Simulation, file_name: str) -> None:
    output_data = sim.get_output_data()

    output_dir = os.path.join(SCRIPT_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)
    output_csv_path = os.path.join(output_dir, file_name)
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
        print(f"Error: {e}")
