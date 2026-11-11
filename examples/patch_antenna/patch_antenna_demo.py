"""
RF patch antenna harmonic simulation using the Allsolve SDK.

This script demonstrates an electromagnetic waves simulation of a microstrip
patch antenna using the Allsolve SDK.
Based on the example case from the Allsolve documentation:
https://allsolve.quanscient.com/documentation/learn-by-doing/example-cases/radio-frequency/rf-003-patch-antenna

The project consists of:
- Variables for substrate dimensions (Ls, hs), 50-ohm feed line (L50, W50),
  quarter-wavelength transformer (Lqw, Wqw), patch size (L, W), substrate
  relative permittivity (epsilonR), air box size and position (air_w, air_h,
  air_z), and fundamental frequency (freq)
- Geometry imported from a STEP file (substrate, feed_50ohm, qw_line, patch,
  port_surface) built with build123d, plus a separate air box added in the
  demo script
- Regions for the simulation domain, substrate, feed line, quarter-wave line,
  patch, ground plane, lumped port surface and electrodes, PML boundary
  surfaces, copper antenna tracks, and surrounding air
- Materials for air, copper (antenna tracks), and a dielectric substrate
  with variable relative permittivity
- Electromagnetic waves physics with perfect conductor interactions on the
  ground plane and antenna tracks, a lumped V/I port at the feed edge, and
  box PML absorption on the air box boundary
- A frequency sweep over 51 points from 2.0 GHz to 5.0 GHz using variable
  overrides
- Mesh with adaptive refinement enabled
- Harmonic simulation driven at the sweep frequency

The simulation outputs:
- SParameters for return loss and port coupling across the frequency sweep.
  The S-parameter data is printed in CSV format to the console.
- ElectromagneticWavesRadiationPattern for the far-field radiation pattern,
  which can be inspected in the Allsolve web app.
- FieldOutput for the second-harmonic electric field (E) on the substrate
  (skin only), which can be visualized in the Allsolve web app to inspect
  field distribution at each frequency point.

Demonstrates:
- STEP geometry import with add_step_file, with the STEP file built by
  build123d when it is missing
- Region selection by CAD name (attribute_path) and by bounding boxes written
  with project variables
- Computed regions with RegionOperation.BOUNDARY, UNION and DIFFERENCE
- Electromagnetic waves physics with ElectromagneticWavesLumpVI as a lumped
  port, ElectromagneticWavesPerfectConductor and a box PML
- A harmonic frequency sweep with SweepType.SPECIFIC_VALUES
- SParameters and ElectromagneticWavesRadiationPattern outputs
"""

import os
from types import SimpleNamespace

import allsolve

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Geometry dimensions in meters — matching RF 003 / Allsolve example case variables
LS = 95.12e-3
HS = 1.57e-3
L50 = 15e-3
W50 = 4.84e-3
HT = 1e-4
LQW = 24.05e-3
WQW = 0.72e-3
L = 41.08e-3
W = L

STEP_FILE = os.path.join(SCRIPT_DIR, "patch_antenna.step")


def main() -> None:
    client = allsolve.Client()

    verbose = True

    project = client.create_project(
        name="Patch antenna demo",
        description="RF patch antenna harmonic simulation",
    )
    print(f"Created project: {project.name} (id: {project.id})")

    try:
        create_variables(project)
        ensure_step_geometry()
        build_geometry(project, verbose=verbose)
        regions = create_regions(project)
        create_materials(project, regions)
        create_physics(project, regions)
        apply_pml_settings(project)
        variable_overrides = create_variable_overrides_for_project(project)
        mesh = create_mesh(project, variable_overrides)
        sim = create_simulation(
            project,
            mesh,
            variable_overrides,
            regions,
        )
        run_mesh_and_simulation(mesh, sim, variable_overrides, verbose)
        print_results(sim)
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
            ("Ls", str(LS), "Substrate length [m]"),
            ("hs", str(HS), "Substrate height [m]"),
            ("L50", str(L50), "50 ohm transmission line length [m]"),
            ("W50", str(W50), "50 ohm transmission line width [m]"),
            ("ht", str(HT), "Track height [m]"),
            ("Lqw", str(LQW), "Quarter wavelength transformer line length [m]"),
            ("Wqw", str(WQW), "Quarter wavelength transformer line width [m]"),
            ("L", str(L), "Patch length [m]"),
            ("epsilonR", "2.2", "Substrate relative permittivity"),
            ("air_w", "0.2", "Air box width and length [m]"),
            ("air_h", "0.1", "Air box height [m]"),
            ("air_z", "0.03", "Air box center z [m]"),
            ("freq", "2.35e9", "Fundamental frequency [Hz]"),
            ("W", "L", "Patch width [m]"),
        ],
    )


def ensure_step_geometry() -> None:
    """Build the STEP geometry locally when the file is not already present."""
    if os.path.isfile(STEP_FILE):
        return

    print(f"STEP file not found, building geometry: {STEP_FILE}")

    from build_patch_antenna_geometry import (  # type: ignore[import-not-found]
        PatchAntennaGeometryParams,
        build_patch_antenna_step,
    )

    build_patch_antenna_step(
        PatchAntennaGeometryParams(
            substrate_length_m=LS,
            substrate_height_m=HS,
            feed_length_m=L50,
            feed_width_m=W50,
            track_height_m=HT,
            qw_length_m=LQW,
            qw_width_m=WQW,
            patch_length_m=L,
            patch_width_m=W,
        ),
        STEP_FILE,
    )


def build_geometry(project: allsolve.Project, verbose: bool = False) -> None:
    geometry_builder = project.geometry_builder()

    geometry_builder.add_step_file(
        filepath=STEP_FILE,
        name="Import",
        cleanup=False,
    )

    geometry_builder.add_box(
        name="airbox",
        position=(0.0, 0.0, "air_z"),
        size=("air_w", "air_w", "air_h"),
        alignment=allsolve.CadAlignment.CENTER,
    )

    geometry_builder.build(print_logs=verbose, on_error=allsolve.OnError.RAISE)


def create_regions(project: allsolve.Project) -> SimpleNamespace:
    regions = SimpleNamespace()

    regions.simulation_domain = project.create_region_rule(
        name="simulation_domain",
        entity_type=allsolve.Region.VOLUME,
        bounding_box=allsolve.ExpressionBoundingBox(
            min=allsolve.ExpressionVector(
                x="-air_w / 2",
                y="-air_w / 2",
                z="air_z - air_h / 2",
            ),
            max=allsolve.ExpressionVector(
                x="air_w / 2",
                y="air_w / 2",
                z="air_z + air_h / 2",
            ),
        ),
    )
    regions.substrate = project.create_region_rule(
        name="substrate",
        entity_type=allsolve.Region.VOLUME,
        attribute_path=allsolve.KeyValueAttributePath(path=[("name", "substrate")]),
    )
    regions.feed_50ohm = project.create_region_rule(
        name="feed_50ohm",
        entity_type=allsolve.Region.VOLUME,
        attribute_path=allsolve.KeyValueAttributePath(path=[("name", "feed_50ohm")]),
    )
    regions.qw_line = project.create_region_rule(
        name="qw_line",
        entity_type=allsolve.Region.VOLUME,
        attribute_path=allsolve.KeyValueAttributePath(path=[("name", "qw_line")]),
    )
    regions.patch = project.create_region_rule(
        name="patch",
        entity_type=allsolve.Region.VOLUME,
        attribute_path=allsolve.KeyValueAttributePath(path=[("name", "patch")]),
    )
    regions.substrate_bottom = project.create_region_rule(
        name="substrate_bottom",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=allsolve.ExpressionBoundingBox(
            min=allsolve.ExpressionVector(
                x="-Ls / 2",
                y="-Ls / 2",
                z="-hs",
            ),
            max=allsolve.ExpressionVector(
                x="Ls / 2",
                y="Ls / 2",
                z="-hs",
            ),
        ),
    )
    regions.port_surface = project.create_region_rule(
        name="port_surface",
        entity_type=allsolve.Region.SURFACE,
        attribute_path=allsolve.KeyValueAttributePath(path=[("name", "port_surface")]),
    )
    regions.port_top_edge = project.create_region_rule(
        name="port_top_edge",
        entity_type=allsolve.Region.CURVE,
        bounding_box=allsolve.ExpressionBoundingBox(
            min=allsolve.ExpressionVector(
                x="-Ls / 2",
                y="-W50 / 2",
                z="0",
            ),
            max=allsolve.ExpressionVector(
                x="-Ls / 2",
                y="W50 / 2",
                z="0",
            ),
        ),
    )
    regions.port_bottom_edge = project.create_region_rule(
        name="port_bottom_edge",
        entity_type=allsolve.Region.CURVE,
        bounding_box=allsolve.ExpressionBoundingBox(
            min=allsolve.ExpressionVector(
                x="-Ls / 2",
                y="-W50 / 2",
                z="-hs",
            ),
            max=allsolve.ExpressionVector(
                x="-Ls / 2",
                y="W50 / 2",
                z="-hs",
            ),
        ),
    )
    regions.airbox_pml_surfaces = project.create_region_computed(
        name="airbox_pml_surfaces",
        entity_type=allsolve.Region.SURFACE,
        operation=allsolve.RegionOperation.BOUNDARY,
        source_regions=[regions.simulation_domain.id],
    )
    regions.solids = project.create_region_computed(
        name="solids",
        entity_type=allsolve.Region.VOLUME,
        operation=allsolve.RegionOperation.UNION,
        source_regions=[
            regions.substrate.id,
            regions.feed_50ohm.id,
            regions.qw_line.id,
            regions.patch.id,
        ],
    )
    regions.antenna_tracks = project.create_region_computed(
        name="antenna_tracks",
        entity_type=allsolve.Region.VOLUME,
        operation=allsolve.RegionOperation.UNION,
        source_regions=[regions.feed_50ohm.id, regions.qw_line.id, regions.patch.id],
    )
    regions.air = project.create_region_computed(
        name="air",
        entity_type=allsolve.Region.VOLUME,
        operation=allsolve.RegionOperation.DIFFERENCE,
        source_regions=[regions.simulation_domain.id, regions.solids.id],
    )
    return regions


def create_materials(project: allsolve.Project, regions: SimpleNamespace) -> None:
    project.create_material(
        name="Air",
        description="Air, 20 C, 100kPa",
        color="#99D9FF",
        target_region=regions.air,
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
        target_region=regions.antenna_tracks,
        density="8960",
        heat_capacity="385",
        coefficient_of_thermal_expansion="16.5e-06",
        electric_conductivity="6e7",
        electric_permittivity="epsilon0",
        magnetic_permeability="mu0",
        thermal_conductivity="401",
    )
    project.create_material(
        name="Dielectric",
        description="Substrate with variable relative permittivity",
        color="#8B7355",
        target_region=regions.substrate,
        electric_conductivity="0",
        electric_permittivity="epsilonR * epsilon0",
        magnetic_permeability="mu0",
    )


def create_physics(project: allsolve.Project, regions: SimpleNamespace) -> None:
    default_physics_set = allsolve.PhysicsSet.get_default(project_id=project.id)
    electromagnetic_waves_physics = default_physics_set.add_physics(
        allsolve.Physics.ElectromagneticWaves()
    )

    # Add interactions
    electromagnetic_waves_physics.add_interactions(
        [
            allsolve.Interaction.ElectromagneticWavesPerfectConductor(
                name="Ground plane",
                target=regions.substrate_bottom,
            ),
            allsolve.Interaction.ElectromagneticWavesPerfectConductor(
                name="Antenna tracks PEC",
                target=regions.antenna_tracks,
            ),
            allsolve.Interaction.ElectromagneticWavesLumpVI(
                name="Lump V/I port",
                port_target=regions.port_surface,
                one_volt_electrode=regions.port_top_edge,
                ground_electrode=regions.port_bottom_edge,
                namespace="port",
                electromagnetic_waves_lump_v_i_voltage="sn(1)",
                electromagnetic_waves_lump_v_i_series_resistance="50",
                electromagnetic_waves_lump_v_i_voltage_drive="1",
            ),
            allsolve.Interaction.ElectromagneticWavesPml(
                name="Box PML",
                target=regions.airbox_pml_surfaces,
                electromagnetic_waves_pml_type="electromagneticWavesPmlTypeBox",
            ),
        ]
    )


def apply_pml_settings(project: allsolve.Project) -> None:
    project.pml_num_layers = 2
    project.save()


def create_variable_overrides_for_project(project: allsolve.Project) -> SimpleNamespace:
    variable_overrides = SimpleNamespace()
    variable_overrides.Frequency_sweep = project.create_variable_overrides(
        name="Frequency sweep",
        sweep_type=allsolve.SweepType.SPECIFIC_VALUES,
        overrides=[
            ("freq", "linspace(2.0e9, 5.0e9, 51)"),
        ],
    )
    return variable_overrides


def create_mesh(
    project: allsolve.Project,
    variable_overrides: SimpleNamespace,
) -> allsolve.Mesh:

    return project.create_mesh(
        allsolve.MeshSettings(
            name="Patch antenna mesh",
            use_mesh_refiner=True,
            scale_factor="2",
            max_run_time_minutes=30,
            variable_overrides=[variable_overrides.Frequency_sweep],
        ),
    )


def create_simulation(
    project: allsolve.Project,
    mesh: allsolve.Mesh,
    variable_overrides: SimpleNamespace,
    regions: SimpleNamespace,
) -> allsolve.Simulation:
    sim = project.create_simulation_harmonic(
        name="Patch antenna harmonic sweep",
        description="Harmonic EM sweep for RF 003 patch antenna",
        max_run_time_minutes=60,
        solver_mode=allsolve.SolverMode.ITERATIVE,
        mesh=mesh,
        physics_set=project.get_default_physics_set(),
        fundamental_frequency="freq",
        solver_tolerance="1e-6",
        numerical_jacobian=False,
    )
    sim.variable_overrides = variable_overrides.Frequency_sweep
    sim.set_runtime(allsolve.Runtime(node_type=allsolve.CPU.CORES_2_32GB, node_count=1))
    sim.eigenmode_port_analysis = False
    sim.save()
    sim.add_outputs(
        [
            allsolve.Output.SParameters(
                name="S-parameters",
            ),
            allsolve.Output.ElectromagneticWavesRadiationPattern(
                name="Radiation pattern",
            ),
            allsolve.Output.FieldOutput(
                name="E harmonic 2",
                expression="harm(2, E)",
                target=regions.substrate,
                field_output_skin_only=True,
            ),
        ]
    )
    return sim


def run_mesh_and_simulation(
    mesh: allsolve.Mesh,
    sim: allsolve.Simulation,
    variable_overrides: SimpleNamespace,
    verbose: bool,
) -> None:
    mesh_instance = mesh.get_override(
        variable_override=variable_overrides.Frequency_sweep
    )
    mesh_instance.run(print_logs=verbose, on_error=allsolve.OnError.RAISE)
    sim.run(print_logs=verbose, on_error=allsolve.OnError.RAISE)
    print("Simulation status:", sim.get_status())


def print_results(
    sim: allsolve.Simulation,
) -> None:
    output_data = sim.get_output_data()
    results = output_data.to_csv(csv_format=allsolve.CsvExportFormat.NORMAL)
    print("Simulation output:")
    print(results)

    output_data.clean_cache()


if __name__ == "__main__":
    main()
