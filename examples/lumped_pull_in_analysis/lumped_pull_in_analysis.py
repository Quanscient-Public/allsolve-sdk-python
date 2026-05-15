"""
Lumped pull-in analysis of a parallel plate capacitor with spring coupling.

This script demonstrates a coupled electrostatic-mechanical simulation of
pull-in behavior in a MEMS parallel-plate actuator using the Allsolve SDK.

The project consists of:
- Two SiO₂ parallel plates (bottom fixed, top movable) separated by a vacuum gap
- Variables for plate dimensions (L, B, H), gap (do), spring stiffness (K),
  DC voltage (Vdc), and theoretical pull-in quantities (Vpullin, Upullin)
- An interpolated function (U_theoritical) for analytical deflection vs voltage
- Three coupled physics: solid mechanics (with lumped spring and electric force),
  electrostatics (with lumped voltage actuation), and mesh deformation
  (coupling structural displacement to the electrostatic mesh)
- A DC voltage sweep from 15V to 365V over 36 points

Two simulations are created:
1. Field state simulation: Solves the coupled problem and exports field states
   (u, v, umesh) for use as initial conditions
2. Initial state simulation: Reinitializes from the field state outputs and
   produces comparison outputs (simulated vs theoretical deflection, pull-in
   voltage and deflection)
"""

import os

import allsolve
from types import SimpleNamespace

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    client = allsolve.Client()

    project = client.create_project(
        name="Lumped pull-in analysis",
        description="Lumped pull-in analysis of a parallel plate capacitor",
    )
    print(f"Created project: {project.name} (id: {project.id})")

    create_variables(project)
    build_geometry(project, verbose=True)
    regions = create_regions(project)
    create_materials(project, regions)
    physics = create_physics(project, regions)
    sweep = create_sweep(project)
    mesh = create_mesh(project, regions)

    sim_field_state = create_field_state_simulation(project, mesh, sweep, physics)
    sim_initial_state = create_initial_state_simulation(
        project, mesh, sweep, physics, sim_field_state
    )

    run_mesh_and_simulation(mesh, sim_field_state, verbose=True)
    run_simulation(sim_initial_state, verbose=True)
    save_results(sim_initial_state)

    client.set_current_project(project)


def create_variables(project: allsolve.Project) -> None:
    project.create_variables(
        [
            ("L", "50e-6", "length of the plate"),
            ("B", "50e-6", "width of the plate"),
            ("H", "3e-6", "thickness of the plate"),
            ("do", "1e-6", "gap between the parallel plates at zero-voltage"),
            ("Aeff", "L*B", "Effective overlap area between the parallel plates"),
            ("Vdc", "10", "DC voltage"),
            ("K", "1e4", "Spring stiffness"),
            (
                "Vpullin",
                "sqrt(8 * K * pow(do,3) / (epsilon0 * Aeff * 27))",
                "Theoritical pull-in voltage",
            ),
            ("Upullin", "do/3", "Theoritical pull-in deflection"),
        ]
    )

    project.create_interpolated_function(
        name="U_theoritical",
        description="theoritical deflection of plate in um vs voltage applied",
        args=[
            (
                "voltage",
                [
                    5,
                    15,
                    25,
                    35,
                    45,
                    55,
                    65,
                    75,
                    85,
                    95,
                    105,
                    115,
                    125,
                    135,
                    145,
                    155,
                    165,
                    175,
                    185,
                    195,
                    205,
                    215,
                    225,
                    235,
                    245,
                    255,
                    265,
                    275,
                    285,
                    295,
                    305,
                    315,
                    325,
                    335,
                    345,
                    355,
                    365,
                ],
            )
        ],
        values=[
            0.000027670868247752846,
            0.00024914816638716894,
            0.0006926927369616294,
            0.0013594914300989124,
            0.002251341960344928,
            0.0033706743622996496,
            0.00472058050642613,
            0.006304852511021983,
            0.00812803117243557,
            0.010195465881991285,
            0.01251338792704371,
            0.015088999614928138,
            0.017930582353008054,
            0.0210476277220207,
            0.02445099677313013,
            0.0281531143755407,
            0.03216820760704656,
            0.036512600159693105,
            0.04120507889574971,
            0.04626735460121706,
            0.05172464753092499,
            0.057606440939755324,
            0.06394746477941048,
            0.07078900104764246,
            0.07818064877511971,
            0.08618276273921278,
            0.09486990908411595,
            0.1043359092666947,
            0.11470146747734804,
            0.12612621063721263,
            0.13882873259438586,
            0.15312230677307004,
            0.16948449609542546,
            0.18871097223895958,
            0.21232677899147978,
            0.2441301274270858,
            0.3072469395895287,
        ],
        cubic_interpolation=True,
    )


def build_geometry(project: allsolve.Project, verbose: bool = False) -> None:
    gb = project.geometry_builder()

    # Bottom plate
    gb.add_box(
        name="box",
        position=("0", "0", "0"),
        size=("L", "B", "H"),
    )

    # Copy bottom plate upward to create top plate (movable)
    gb.add_translate(
        name="translate",
        cad_names=["box"],
        translation=("0", "0", "H/2 + do + H/2"),
        copy_object=True,
        repeat=1,
    )

    # Vacuum gap between the plates
    gb.add_box(
        name="box 2",
        position=("0", "0", "H/2 + do/2"),
        size=("L", "B", "do"),
    )

    gb.build(print_logs=verbose, on_error=allsolve.OnError.RAISE)


def create_regions(project: allsolve.Project) -> SimpleNamespace:
    """Create regions using bounding-box rules (V2 geometry pipeline).

    Geometry layout (z-axis):
      Bottom plate ("box"):      z ∈ [-H/2,      H/2]
      Vacuum gap  ("box 2"):     z ∈ [ H/2,      H/2 + do]
      Top plate   (copy of box): z ∈ [ H/2 + do,  3H/2 + do]
    All three share the same L × B footprint in x–y.
    """
    regions = SimpleNamespace()

    # --- Individual volume regions ---

    # Bottom plate: the only volume whose upper face is at z = H/2.
    # Bounding box caps z below the vacuum mid-plane; min_size in z
    # excludes the thin vacuum gap (do < H).
    regions.fixed_bottom_plate = project.create_region_rule(
        name="fixed bottom plate",
        entity_type=allsolve.Region.VOLUME,
        bounding_box=(
            ("-L", "-B", "-H"),
            ("L", "B", "H/2 + do/2"),
        ),
        min_size=("L/2", "B/2", "H/2"),
    )

    # Top plate: bounding box starts above the vacuum mid-plane.
    regions.movable_top_plate = project.create_region_rule(
        name="movable top plate",
        entity_type=allsolve.Region.VOLUME,
        bounding_box=(
            ("-L", "-B", "H/2 + do/2"),
            ("L", "B", "2*H + do"),
        ),
        min_size=("L/2", "B/2", "H/2"),
    )

    # Vacuum gap: the only volume thinner than H in z.
    regions.vacuum_target = project.create_region_rule(
        name="Vacuum target",
        entity_type=allsolve.Region.VOLUME,
        max_size=("2*L", "2*B", "(H + do) / 2"),
    )

    # --- Computed (union) volume regions ---

    regions.sio2_target = project.create_region_computed(
        name="Silicon dioxide target",
        entity_type=allsolve.Region.VOLUME,
        operation=allsolve.RegionOperation.UNION,
        source_regions=[regions.fixed_bottom_plate, regions.movable_top_plate],
    )

    regions.solid_domain = project.create_region_computed(
        name="solid domain",
        entity_type=allsolve.Region.VOLUME,
        operation=allsolve.RegionOperation.UNION,
        source_regions=[regions.fixed_bottom_plate, regions.movable_top_plate],
    )

    regions.vacuum_domain = regions.vacuum_target

    regions.electric_domain = project.create_region_computed(
        name="electric domain",
        entity_type=allsolve.Region.VOLUME,
        operation=allsolve.RegionOperation.UNION,
        source_regions=[regions.solid_domain, regions.vacuum_target],
    )

    # --- Surface regions ---

    # Top surface of the fixed bottom plate lies at z = H/2.
    # Bounding box collapses to that z-plane; min_size ensures we pick
    # the full L × B face, not a small edge fragment.
    regions.top_surface_fixed = project.create_region_rule(
        name="top-surface of fixed-bottom-plate",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=(
            ("-L", "-B", "H/2"),
            ("L", "B", "H/2"),
        ),
        min_size=("L/2", "B/2", 0),
    )

    # Bottom surface of the movable top plate lies at z = H/2 + do.
    regions.bottom_surface_movable = project.create_region_rule(
        name="bottom-surface of movable-top-plate",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=(
            ("-L", "-B", "H/2 + do"),
            ("L", "B", "H/2 + do"),
        ),
        min_size=("L/2", "B/2", 0),
    )

    return regions


def create_materials(project: allsolve.Project, regions: SimpleNamespace) -> None:
    project.create_material(
        name="Vacuum",
        description="Perfect vacuum",
        color="#EDFAFF",
        target_region=regions.vacuum_target,
        electric_conductivity="0",
        electric_permittivity="epsilon0",
        magnetic_permeability="mu0",
        thermal_conductivity="0",
    )

    project.create_material(
        name="Silicon dioxide",
        description="Amorphous SiO2",
        abbreviation="SiO₂",
        color="#F1FCFF",
        target_region=regions.sio2_target,
        coefficient_of_thermal_expansion="7.64e-6",
        density="2200",
        elasticity_matrix=allsolve.MaterialProperty.ElasticityMatrixYoungsModulusPoissonsRatio(
            youngs_modulus="70e9",
            poissons_ratio="0.17",
        ),
        electric_permittivity="3.9*epsilon0",
        heat_capacity="733",
        magnetic_permeability="mu0",
        thermal_conductivity="9.50",
    )


def create_physics(
    project: allsolve.Project, regions: SimpleNamespace
) -> SimpleNamespace:
    physics = SimpleNamespace()

    physics.solid_mechanics = project.add_physics(
        allsolve.Physics.SolidMechanics(target=regions.solid_domain)
    )
    physics.electrostatics = project.add_physics(
        allsolve.Physics.Electrostatics(target=regions.electric_domain)
    )
    physics.mesh_deformation = project.add_physics(
        allsolve.Physics.MeshDeformation(target=regions.electric_domain)
    )

    # --- Solid Mechanics ---
    physics.solid_mechanics.add_interactions(
        [
            allsolve.Interaction.SolidMechanicsClamp(
                name="Clamp",
                target=regions.fixed_bottom_plate,
            ),
            allsolve.Interaction.SolidMechanicsConstraint(
                name="Constraint",
                target=regions.movable_top_plate,
                solid_mechanics_constraint="[1, 0; 1, 0; 0, 0]",
            ),
            allsolve.Interaction.SolidMechanicsLump(
                name="Lump U/F",
                namespace="lump",
                target=regions.bottom_surface_movable,
                solid_mechanics_lump_actuation_mode=allsolve.SolidMechanicsLumpActuationMode.CIRCUIT_COUPLING,
                solid_mechanics_lump_circuit_coupling="[0, 0; 0, 0; 1, lump.Fz - -(K*lump.Uz)]",
            ),
            allsolve.Interaction.SolidMechanicsElectricForce(
                name="Electric force",
            ),
            allsolve.Interaction.SolidMechanicsLargeDisplacement(
                name="Large displacement",
            ),
            allsolve.Interaction.SolidMechanicsGeometricNonlinearity(
                name="Geometric nonlinearity",
                enabled=False,
            ),
        ]
    )

    # --- Electrostatics ---
    physics.electrostatics.add_interactions(
        [
            allsolve.Interaction.ElectrostaticsLump(
                name="Lump V/Q",
                namespace="lump_2",
                target=regions.top_surface_fixed,
                electrostatics_lump_actuation_mode=allsolve.ElectrostaticsLumpActuationMode.VOLTAGE,
                electrostatics_lump_voltage="Vdc",
            ),
            allsolve.Interaction.ElectrostaticsLump(
                name="Lump V/Q 2",
                namespace="lump_3",
                target=regions.bottom_surface_movable,
                electrostatics_lump_actuation_mode=allsolve.ElectrostaticsLumpActuationMode.VOLTAGE,
                electrostatics_lump_voltage="0.0",
            ),
            allsolve.Interaction.ElectrostaticsLargeDisplacement(
                name="Large displacement",
            ),
        ]
    )

    # --- Mesh Deformation ---
    physics.mesh_deformation.add_interactions(
        [
            allsolve.Interaction.MeshDeformationConstraint(
                name="Constraint",
                target=regions.solid_domain,
                mesh_deformation_constraint="[1, compx(u); 1, compy(u); 1, compz(u)]",
            ),
            allsolve.Interaction.MeshDeformationConstraint(
                name="Constraint 2",
                target=regions.vacuum_domain,
                mesh_deformation_constraint="[1, 0; 1, 0; 0, 0]",
            ),
        ]
    )

    return physics


def create_sweep(project: allsolve.Project) -> allsolve.VariableOverrides:
    return project.create_variable_overrides(
        name="Sweep 1",
        sweep_type=allsolve.SweepType.SPECIFIC_VALUES,
        overrides=[
            ("Vdc", "linspace(15,365,36)"),
        ],
    )


def create_mesh(project: allsolve.Project, regions: SimpleNamespace) -> allsolve.Mesh:
    return project.create_mesh(
        allsolve.MeshSettings(
            name="Mesh 1",
            scale_factor=0.75,
            curved_mesh=False,
            extrusion=allsolve.MeshExtrusion(
                regions=[
                    regions.fixed_bottom_plate,
                    regions.movable_top_plate,
                    regions.vacuum_target,
                ],
                sub_layer_counts=[2, 2, 2],
                extrusion_overlap_mode=allsolve.ExtrusionOverlapMode.PREVENT,
            ),
        ),
    )


def create_field_state_simulation(
    project: allsolve.Project,
    mesh: allsolve.Mesh,
    sweep: allsolve.VariableOverrides,
    physics: SimpleNamespace,
) -> allsolve.Simulation:
    """Simulation 1: produces field states (u, v, umesh) for initialization."""
    sim = project.create_simulation_static(
        name="Simulation 1: Field state",
        description="",
        max_run_time_minutes=15,
        solver_mode=allsolve.SolverMode.DIRECT,
        mesh=mesh.id,
        variable_overrides=sweep.id,
    )
    sim.add_outputs(
        [
            allsolve.Output.FieldState(name="u", field_state="u"),
            allsolve.Output.FieldState(name="v", field_state="v"),
            allsolve.Output.FieldState(name="umesh", field_state="umesh"),
        ]
    )
    return sim


def create_initial_state_simulation(
    project: allsolve.Project,
    mesh: allsolve.Mesh,
    sweep: allsolve.VariableOverrides,
    physics: SimpleNamespace,
    field_state_sim: allsolve.Simulation,
) -> allsolve.Simulation:
    """Simulation 2: initializes from field states and produces analysis outputs."""
    sim = project.create_simulation_static(
        name="Simulation 2: Initial state",
        description="",
        max_run_time_minutes=15,
        solver_mode=allsolve.SolverMode.DIRECT,
        mesh=mesh.id,
        variable_overrides=sweep.id,
    )

    sim.set_field_initializations(
        [
            allsolve.FieldInitialization(
                type=allsolve.FieldInitializationType.POSTPROCESSING,
                source_simulation=field_state_sim,
                source_output_name="u",
                field=physics.solid_mechanics.fields.displacement,
            ),
            allsolve.FieldInitialization(
                type=allsolve.FieldInitializationType.POSTPROCESSING,
                source_simulation=field_state_sim,
                source_output_name="v",
                field=physics.electrostatics.fields.electricPotential,
            ),
            allsolve.FieldInitialization(
                type=allsolve.FieldInitializationType.POSTPROCESSING,
                source_simulation=field_state_sim,
                source_output_name="umesh",
                field=physics.mesh_deformation.fields.meshDeformation,
            ),
        ]
    )

    sim.add_outputs(
        [
            allsolve.Output.FieldOutput(
                name="u",
                expression="u",
                field_output_skin_only=True,
            ),
            allsolve.Output.FieldOutput(
                name="v",
                expression="v",
                field_output_skin_only=True,
            ),
            allsolve.Output.ValueOutput(
                name="Pull-in deflection (um)",
                expression="Upullin * 1e6",
            ),
            allsolve.Output.ValueOutput(
                name="Pull-in voltage",
                expression="Vpullin",
            ),
            allsolve.Output.ValueOutput(
                name="Uz_theoritical",
                expression="U_theoritical(Vdc)",
            ),
            allsolve.Output.ValueOutput(
                name="Uz_simulation (um)",
                expression="abs(lump.Uz) * 1e6",
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

    run_simulation(sim, verbose=verbose)


def run_simulation(sim: allsolve.Simulation, verbose: bool = False) -> None:
    sim.run(print_logs=verbose)
    print(f"Simulation '{sim.name}' status: {sim.get_status()}")
    if sim.get_status() != allsolve.Job.SUCCESS:
        raise ValueError(f"Simulation failed: {sim.get_status()}")


def save_results(sim: allsolve.Simulation) -> None:
    output_data = sim.get_output_data()

    output_dir = os.path.join(SCRIPT_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)
    output_csv_path = os.path.join(output_dir, "lumped_pull_in_output.csv")
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
