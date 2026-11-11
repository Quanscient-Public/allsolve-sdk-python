"""
CMUT single cell in receive (Rx) mode: a static DC bias followed by a transient
that starts from the biased state.

A CMUT (capacitive micromachined ultrasonic transducer) is a membrane above a
vacuum gap. A DC bias pulls the membrane towards the substrate. In receive mode
an ultrasound pulse in water pushes on the biased membrane, and the movement
changes the charge on the electrodes.

Demonstrates:
- Coupled SolidMechanics + Electrostatics + MeshDeformation + AcousticWaves,
  with large displacement in both solid mechanics and electrostatics
- Static DC bias -> transient chain: FieldState outputs of the static
  simulation initialize the transient (FieldInitialization with
  FieldInitializationType.FIELDSTATE)
- Interface faces from region operations: INTERSECTION of the BOUNDARY regions
  of two volumes (electrodes, membrane front face, source plane in the water)
- Symmetry faces from bounding-box region rules, minus the vacuum faces with
  DIFFERENCE
- MeshExtrusion with sub_layer_counts for a layered geometry with a recessed
  vacuum gap
- Transient with TimestepAlgorithm.GEN_ALPHA
- Running two simulations in parallel with allsolve.run_simulations()

FIELDSTATE or POSTPROCESSING:
- FIELDSTATE uses the stored field as the initial value and then solves. Use it
  to start a transient (or another solve) from a static operating point.
- POSTPROCESSING solves nothing. It loads the stored fields of each step and
  only evaluates the outputs of the new simulation. Use it to add outputs to a
  finished simulation without running it again.

Geometry (quarter model, 0 <= x, y <= cell_pitch/2):
- Polysilicon substrate (100 um), the bias electrode is its top face
- SiO2 layer (400 nm) with a recessed vacuum gap (250 nm, radius 35 um)
- Polysilicon membrane (4 um), grounded underside
- Water column: 2 wavelengths at 6.5 MHz, then 1 wavelength above the source
  plane, with an absorbing boundary on top

Simulations:
1. Static DC bias at Vdc = 160 V. Saves the final u, v and umesh fields.
2. Static DC bias sweep from 1 V to 186 V.
3. Transient: 10 cycles at 6.5 MHz with GEN_ALPHA, initialized from
   simulation 1. A wavelet normal acceleration on the source plane sends a
   pulse towards the membrane.

The value outputs are saved to CSV files in the output/ folder. Use
visualize_cmut_results.py to plot them.
"""

import os
from types import SimpleNamespace

import allsolve

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_NAME = "CMUT single cell rx"
BIAS_SWEEP = "linspace(1, 186, 50)"
TOL = "1e-9"
Z_MEMBRANE_TOP = "thk_substrate+thk_oxide+thk_membrane"
Z_TOP = "thk_substrate+thk_oxide+thk_membrane+thk_load+wave_load"


def main():
    client = allsolve.Client()

    project = client.create_project(
        name=PROJECT_NAME,
        description="CMUT single cell in receive mode: static DC bias and transient",
    )
    print(f"Created project: {project.name} (id: {project.id})")

    try:
        create_variables(project)
        build_geometry(project, verbose=True)
        regions = create_regions(project)
        create_materials(project, regions)
        physics = create_physics(project, regions)
        sweep = create_sweep(project)
        mesh = create_mesh(project, regions)

        sim_static = create_static_simulation(
            project, mesh, physics, "Static DC bias", field_states=True
        )
        sim_sweep = create_static_simulation(
            project, mesh, physics, "Static DC bias sweep", sweep=sweep
        )
        sim_transient = create_transient_simulation(project, mesh, physics, sim_static)

        run_job(mesh, "Mesh")
        run_job(sim_static, sim_static.name)
        allsolve.run_simulations(
            [sim_sweep, sim_transient],
            print_status=True,
            on_error=allsolve.OnError.STRICT,
        )

        save_results(sim_static, "cmut_static_dc_bias.csv")
        save_results(sim_sweep, "cmut_static_dc_bias_sweep.csv", include_overrides=True)
        save_results(sim_transient, "cmut_transient.csv")
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
            ("thk_substrate", "100e-6", "Substrate thickness"),
            ("thk_oxide", "400e-9", "Oxide thickness"),
            ("thk_vacuum", "250e-9", "Vacuum gap thickness"),
            ("thk_membrane", "4e-6", "Membrane thickness"),
            ("cell_rad", "35e-6", "Vacuum gap radius"),
            ("cell_pitch", "95e-6", "Cell pitch"),
            ("frequency", "6.5e6", "Center frequency"),
            ("vel_load", "1480", "Speed of sound in water"),
            ("ncycles", "10", "Number of simulated periods"),
            ("ppc", "20", "Time steps per period"),
            ("Vdc", "160", "DC bias voltage"),
            (
                "z_front_face",
                "thk_substrate+thk_oxide+thk_vacuum+thk_membrane",
                "Reference z for the pressure probe",
            ),
            ("wave_load", "vel_load/frequency", "Wavelength in water"),
            ("thk_load", "2*wave_load", "Water thickness below the source plane"),
        ]
    )


def build_geometry(project: allsolve.Project, verbose: bool = False) -> None:
    gb = project.geometry_builder()
    pitch = ("cell_pitch", "cell_pitch")

    gb.add_box(
        name="substrate",
        position=(0, 0, "thk_substrate/2"),
        size=(*pitch, "thk_substrate"),
    )
    gb.add_box(
        name="oxide",
        position=(0, 0, "thk_substrate+thk_oxide/2"),
        size=(*pitch, "thk_oxide"),
    )
    gb.add_cylinder(
        name="vacuum",
        position=(0, 0, "thk_substrate+thk_oxide-thk_vacuum/2"),
        radius="cell_rad",
        axis=(0, 0, "thk_vacuum"),
    )
    gb.add_difference(
        name="vacuum cut",
        cad_names_1=["oxide"],
        cad_names_2=["vacuum"],
        delete_tool=False,
    )
    gb.add_box(
        name="membrane",
        position=(0, 0, "thk_substrate+thk_oxide+thk_membrane/2"),
        size=(*pitch, "thk_membrane"),
    )
    gb.add_box(
        name="load bot",
        position=(0, 0, "thk_substrate+thk_oxide+thk_membrane+thk_load/2"),
        size=(*pitch, "thk_load"),
    )
    gb.add_box(
        name="load top",
        position=(0, 0, "thk_substrate+thk_oxide+thk_membrane+thk_load+wave_load/2"),
        size=(*pitch, "wave_load"),
    )

    gb.add_box(name="xcut", position=(-0.5, 0, 0), size=(1, 1, 1))
    gb.add_box(name="ycut", position=(0, -0.5, 0), size=(1, 1, 1))
    gb.add_difference(
        name="symmetry cuts",
        cad_names_1=[
            "substrate",
            "oxide",
            "vacuum",
            "membrane",
            "load bot",
            "load top",
        ],
        cad_names_2=["xcut", "ycut"],
        delete_tool=True,
    )

    gb.build(print_logs=verbose, on_error=allsolve.OnError.RAISE)


def _volume(project: allsolve.Project, name: str, cad_name: str) -> allsolve.Region:
    return project.create_region_rule(
        name=name,
        entity_type=allsolve.Region.VOLUME,
        attribute_path=[("name", cad_name)],
    )


def _computed(project, name, entity_type, operation, sources) -> allsolve.Region:
    return project.create_region_computed(
        name=name,
        entity_type=entity_type,
        operation=operation,
        source_regions=sources,
    )


def _box_faces(
    project: allsolve.Project, name: str, box_min, box_max
) -> allsolve.Region:
    # Bounding-box rules select the entities that lie inside the box, so pad
    # flat boxes with TOL on both sides.
    x0, y0, z0 = box_min
    x1, y1, z1 = box_max
    return project.create_region_rule(
        name=name,
        entity_type=allsolve.Region.SURFACE,
        bounding_box=(
            (f"{x0}-{TOL}", f"{y0}-{TOL}", f"{z0}-{TOL}"),
            (f"{x1}+{TOL}", f"{y1}+{TOL}", f"{z1}+{TOL}"),
        ),
    )


def create_regions(project: allsolve.Project) -> SimpleNamespace:
    r = SimpleNamespace()
    VOL = allsolve.Region.VOLUME
    SURF = allsolve.Region.SURFACE
    UNION = allsolve.RegionOperation.UNION
    BOUNDARY = allsolve.RegionOperation.BOUNDARY
    INTERSECTION = allsolve.RegionOperation.INTERSECTION
    DIFFERENCE = allsolve.RegionOperation.DIFFERENCE

    r.substrate = _volume(project, "substrate", "substrate")
    r.oxide = _volume(project, "oxide", "oxide")
    r.vacuum = _volume(project, "vacuum", "vacuum")
    r.membrane = _volume(project, "membrane", "membrane")
    r.load_bot = _volume(project, "load_bot", "load bot")
    r.load_top = _volume(project, "load_top", "load top")

    r.load = _computed(project, "load", VOL, UNION, [r.load_bot, r.load_top])
    r.acoustic_waves = _computed(project, "acoustic_waves", VOL, UNION, [r.load])
    r.solid_mechanics = _computed(
        project, "solid_mechanics", VOL, UNION, [r.substrate, r.oxide, r.membrane]
    )
    r.polysilicon = _computed(
        project, "polysilicon", VOL, UNION, [r.substrate, r.membrane]
    )
    r.electrostatics = _computed(
        project, "electrostatics", VOL, UNION, [r.oxide, r.vacuum]
    )

    # BOUNDARY of a region leaves out the faces shared by its own volumes, so
    # the boundary of "electrostatics" has no oxide-vacuum faces and the
    # boundary of "load" has no load_bot-load_top face.
    r.substrate_bnd = _computed(
        project, "substrate_boundary", SURF, BOUNDARY, [r.substrate]
    )
    r.membrane_bnd = _computed(
        project, "membrane_boundary", SURF, BOUNDARY, [r.membrane]
    )
    r.vacuum_bnd = _computed(project, "vacuum_boundary", SURF, BOUNDARY, [r.vacuum])
    r.electrostatics_bnd = _computed(
        project, "electrostatics_boundary", SURF, BOUNDARY, [r.electrostatics]
    )
    r.load_bnd = _computed(project, "load_boundary", SURF, BOUNDARY, [r.load])
    r.load_bot_bnd = _computed(
        project, "load_bot_boundary", SURF, BOUNDARY, [r.load_bot]
    )
    r.load_top_bnd = _computed(
        project, "load_top_boundary", SURF, BOUNDARY, [r.load_top]
    )

    # Interfaces: INTERSECTION of the boundaries of the two sides.
    r.bias_electrode = _computed(
        project,
        "bias_electrode",
        SURF,
        INTERSECTION,
        [r.substrate_bnd, r.electrostatics_bnd],
    )
    r.ground_electrode = _computed(
        project,
        "ground_electrode",
        SURF,
        INTERSECTION,
        [r.membrane_bnd, r.electrostatics_bnd],
    )
    r.front_face = _computed(
        project, "front_face", SURF, INTERSECTION, [r.membrane_bnd, r.load_bnd]
    )
    r.source_plane = _computed(
        project, "source_plane", SURF, INTERSECTION, [r.load_bot_bnd, r.load_top_bnd]
    )

    r.clamp_face = _box_faces(
        project, "clamp_face", (0, 0, 0), ("cell_pitch/2", "cell_pitch/2", 0)
    )
    r.absorbing_face = _box_faces(
        project,
        "absorbing_face",
        (0, 0, Z_TOP),
        ("cell_pitch/2", "cell_pitch/2", Z_TOP),
    )

    # Symmetry faces: the four side planes of the solid layers. The vacuum's
    # own side faces lie on x = 0 and y = 0 too, so DIFFERENCE removes them.
    side_planes = [
        _box_faces(project, "side_x0", (0, 0, 0), (0, "cell_pitch/2", Z_MEMBRANE_TOP)),
        _box_faces(project, "side_y0", (0, 0, 0), ("cell_pitch/2", 0, Z_MEMBRANE_TOP)),
        _box_faces(
            project,
            "side_xmax",
            ("cell_pitch/2", 0, 0),
            ("cell_pitch/2", "cell_pitch/2", Z_MEMBRANE_TOP),
        ),
        _box_faces(
            project,
            "side_ymax",
            (0, "cell_pitch/2", 0),
            ("cell_pitch/2", "cell_pitch/2", Z_MEMBRANE_TOP),
        ),
    ]
    r.side_faces = _computed(project, "side_faces", SURF, UNION, side_planes)
    r.symmetry_faces = _computed(
        project, "symmetry_faces", SURF, DIFFERENCE, [r.side_faces, r.vacuum_bnd]
    )

    return r


def create_materials(project: allsolve.Project, r: SimpleNamespace) -> None:
    E = allsolve.MaterialProperty.ElasticityMatrixYoungsModulusPoissonsRatio
    project.create_material(
        name="Polycrystalline Silicon",
        description="Appendix G: Semiconducting Materials, Table G.1",
        color="#87CEEB",
        abbreviation="Poly-Si",
        target_region=r.polysilicon,
        density="2320",
        heat_capacity="678",
        coefficient_of_thermal_expansion="2.5e-6",
        electric_conductivity="7.69e4",
        electric_permittivity="4.2*epsilon0",
        magnetic_permeability="(1 - 39e-7)*mu0",
        thermal_conductivity="34",
        elasticity_matrix=E("161e9", "0.22"),
    )
    project.create_material(
        name="Silicon dioxide",
        description="Amorphous SiO2",
        color="#36F00C",
        abbreviation="SiO₂",
        target_region=r.oxide,
        density="2200",
        heat_capacity="733",
        coefficient_of_thermal_expansion="7.64e-6",
        electric_permittivity="3.9*epsilon0",
        magnetic_permeability="mu0",
        thermal_conductivity="9.50",
        elasticity_matrix=E("70e9", "0.17"),
    )
    project.create_material(
        name="Vacuum",
        description="Perfect vacuum",
        color="#F1140B",
        target_region=r.vacuum,
        electric_conductivity="0",
        electric_permittivity="epsilon0",
        magnetic_permeability="mu0",
        thermal_conductivity="0",
    )
    project.create_material(
        name="Water",
        description="Deionized water, 20 C, 100kPa",
        color="#59AAF3",
        abbreviation="H₂O",
        target_region=r.load,
        density="998",
        heat_capacity="4182",
        speed_of_sound="1480",
        dynamic_viscosity="8.9e-4",
        electric_conductivity="5e-6",
        electric_permittivity="81*epsilon0",
        magnetic_permeability="mu0",
        thermal_conductivity="0.55",
    )


def create_physics(project: allsolve.Project, r: SimpleNamespace) -> SimpleNamespace:
    p = SimpleNamespace(physics_set=project.get_default_physics_set())
    ia = allsolve.Interaction

    p.solid_mechanics = p.physics_set.add_physics(
        allsolve.Physics.SolidMechanics(target=r.solid_mechanics)
    )
    p.electrostatics = p.physics_set.add_physics(
        allsolve.Physics.Electrostatics(target=r.electrostatics)
    )
    p.acoustic_waves = p.physics_set.add_physics(
        allsolve.Physics.AcousticWaves(target=r.acoustic_waves)
    )
    # The vacuum mesh follows the membrane through the large-displacement
    # interactions, so mesh deformation needs no boundary conditions.
    p.mesh_deformation = p.physics_set.add_physics(
        allsolve.Physics.MeshDeformation(target=r.vacuum)
    )

    p.solid_mechanics.add_interactions(
        [
            ia.SolidMechanicsLargeDisplacement(name="Large displacement"),
            ia.SolidMechanicsSymmetry(name="Symmetry", target=r.symmetry_faces),
            ia.SolidMechanicsElectricForce(name="Electric force"),
            ia.SolidMechanicsClamp(name="Clamp", target=r.clamp_face),
        ]
    )
    p.electrostatics.add_interactions(
        [
            ia.ElectrostaticsLargeDisplacement(name="Large displacement"),
            ia.ElectrostaticsConstraint(
                name="Ground",
                target=r.ground_electrode,
                electrostatics_constraint="0",
            ),
            ia.ElectrostaticsLump(
                name="Bias",
                target=r.bias_electrode,
                namespace="lump",
                electrostatics_lump_voltage="Vdc",
            ),
        ]
    )
    p.acoustic_waves.add_interactions(
        [
            ia.AcousticWavesAcousticStructure(name="Acoustic structure"),
            ia.AcousticWavesNormalAcceleration(
                name="Rx pulse",
                target=r.source_plane,
                acoustic_waves_normal_acceleration="10e3*wavelet(frequency, 1.2)",
            ),
            ia.AcousticWavesAbsorbingBoundary(
                name="Absorbing boundary", target=r.absorbing_face
            ),
        ]
    )
    return p


def create_sweep(project: allsolve.Project) -> allsolve.VariableOverrides:
    return project.create_variable_overrides(
        name="Bias sweep",
        sweep_type=allsolve.SweepType.SPECIFIC_VALUES,
        overrides=[("Vdc", BIAS_SWEEP)],
    )


def create_mesh(project: allsolve.Project, r: SimpleNamespace) -> allsolve.Mesh:
    # The extrusion lists every volume it covers. sub_layer_counts has one
    # count per z-layer of the stack, not per region, bottom to top: substrate,
    # oxide below the gap, gap level (oxide and vacuum side by side), membrane,
    # water below the source plane (6 per wavelength), water above it.
    return project.create_mesh(
        allsolve.MeshSettings(
            name="Mesh 10um extruded",
            use_mesh_refiner=False,
            max_run_time_minutes=60,
            mesh_size_max=10e-6,
            extrusion=allsolve.MeshExtrusion(
                regions=[
                    r.substrate,
                    r.oxide,
                    r.vacuum,
                    r.membrane,
                    r.load_bot,
                    r.load_top,
                ],
                sub_layer_counts=[
                    4,
                    1,
                    1,
                    3,
                    "ceil(thk_load/(wave_load/6))",
                    "ceil(wave_load/(wave_load/6))",
                ],
            ),
        )
    )


def create_static_simulation(
    project: allsolve.Project,
    mesh: allsolve.Mesh,
    physics: SimpleNamespace,
    name: str,
    sweep: allsolve.VariableOverrides | None = None,
    field_states: bool = False,
) -> allsolve.Simulation:
    sim = project.create_simulation_static(
        name=name,
        description="",
        max_run_time_minutes=60,
        solver_mode=allsolve.SolverMode.DIRECT,
        mesh=mesh,
        variable_overrides=sweep,
        physics_set=physics.physics_set,
    )
    outputs = [
        allsolve.Output.ValueOutput(name="Bias", expression="Vdc"),
        allsolve.Output.ValueOutput(
            name="Displacement",
            expression="interpolate(reg.membrane, abs(compz(u)), [0, 0, thk_substrate+thk_oxide])",
        ),
        allsolve.Output.FieldOutput(
            name="u", expression="u", field_output_skin_only=True
        ),
    ]
    if field_states:
        # The final static fields become the initial state of the transient.
        outputs += [
            allsolve.Output.FieldState(
                name=field,
                field_state=field,
                field_state_filter_type=allsolve.FieldStateFilterType.FINAL_ONLY,
            )
            for field in ("u", "v", "umesh")
        ]
    sim.add_outputs(outputs)
    return sim


def create_transient_simulation(
    project: allsolve.Project,
    mesh: allsolve.Mesh,
    physics: SimpleNamespace,
    sim_static: allsolve.Simulation,
) -> allsolve.Simulation:
    sim = project.create_simulation_transient(
        name="Transient",
        description="Rx pulse on the DC-biased membrane",
        max_run_time_minutes=60,
        solver_mode=allsolve.SolverMode.DIRECT,
        transient_start_time="0",
        transient_end_time="ncycles/frequency",
        transient_timestep_size="1/frequency/ppc",
        timestep_algorithm=allsolve.TimestepAlgorithm.GEN_ALPHA,
        nonlinear_solver_tolerance="1e-4",
        nonlinear_solver_max_iterations="100",
        mesh=mesh,
        physics_set=physics.physics_set,
    )

    init = allsolve.FieldInitializationType.FIELDSTATE
    sim.set_field_initializations(
        [
            allsolve.FieldInitialization(
                type=init,
                source_simulation=sim_static,
                source_output_name="u",
                field=physics.solid_mechanics.fields.displacement,
            ),
            allsolve.FieldInitialization(
                type=init,
                source_simulation=sim_static,
                source_output_name="v",
                field=physics.electrostatics.fields.electricPotential,
            ),
            allsolve.FieldInitialization(
                type=init,
                source_simulation=sim_static,
                source_output_name="umesh",
                field=physics.mesh_deformation.fields.meshDeformation,
            ),
        ]
    )

    sim.add_outputs(
        [
            allsolve.Output.ValueOutput(name="Voltage", expression="lump.V"),
            allsolve.Output.ValueOutput(name="Charge", expression="lump.Q"),
            allsolve.Output.ValueOutput(
                name="Displacement",
                expression="average(reg.front_face, compz(u), 2)",
            ),
            allsolve.Output.ValueOutput(
                name="Pressure",
                expression="interpolate(reg.acoustic_waves, p, [0, 0, z_front_face+thk_load/2])",
            ),
        ]
    )
    return sim


def run_job(job, label: str) -> None:
    print(f"Running {label}...")
    job.run(print_logs=True)
    if job.get_status() != allsolve.Job.SUCCESS:
        raise ValueError(f"{label} failed: {job.get_status()}")


def save_results(
    sim: allsolve.Simulation, filename: str, include_overrides: bool = False
) -> None:
    output_dir = os.path.join(SCRIPT_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    if os.path.exists(path):
        os.remove(path)
    output_data = sim.get_output_data()
    output_data.to_csv_file(
        filename=path,
        csv_format=allsolve.CsvExportFormat.NORMAL,
        include_overrides=include_overrides,
    )
    output_data.clean_cache()
    print(f"Saved results to CSV: {path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
