"""
This script demonstrates an eigenmode analysis of a MEMS comb-drive
accelerometer using the Allsolve SDK.
The project consists of:
- Geometry imported from a GDSII file with multiple layers
- Regions for each material layer and clamp boundaries
- Materials with mechanical properties, including an
  anisotropic elasticity matrix for monocrystalline silicon
- Solid mechanics physics with a clamp interaction on the anchor pads
- Extruded mesh with per-layer sub-layer counts for thin-film resolution
- Eigenmode simulation requesting the first 5 or more eigenmodes
- The found eigenmodes are printed to the console

The simulation outputs:
- FieldOutput for the displacement field (u) rendered as skin-only,
  which can be visualized in the Allsolve web app or using the
  visualize_combdrive_eigenmodes.py script to inspect each
  eigenmode shape of the comb-drive structure.
"""

import os
import sys

import allsolve
from types import SimpleNamespace

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)


def main():
    client = allsolve.Client()

    verbose = True

    project = client.create_project(
        name="Combdrive Eigenmodes demo",
        description="Eigenmode analysis of a MEMS comb-drive accelerometer to find the first 5 or more eigenmodes.",
    )
    print(f"Created project: {project.name} (id: {project.id})")

    build_geometry(project, verbose=verbose)
    regions = create_regions(project)
    create_materials(project, regions)
    create_physics(project, regions)
    mesh = create_mesh(project, regions)
    sim = create_simulation(project, mesh)
    run_mesh_and_simulation(mesh, sim, verbose=verbose)

    client.set_current_project(project)


def build_geometry(project: allsolve.Project, verbose: bool = False) -> None:
    geometry_builder = project.geometry_builder()
    geometry_builder.add_gds2_file(
        filepath=os.path.join(SCRIPT_DIR, "Comb_drive_Accelerometer.gds"),
        name="Comb_drive_Accelerometer.gds",
        unit=allsolve.CadDistanceUnit.MICROMETER,
        layers=[
            allsolve.CadGdsLayer(
                layer=23, type=0, absolute_z0="61.25", thickness="0.1", name="Reflector"
            ),
            allsolve.CadGdsLayer(
                layer=2, type=0, absolute_z0="31.25", thickness="30.0", name="Comb top"
            ),
            allsolve.CadGdsLayer(
                layer=1, type=0, absolute_z0="1.0", thickness="30.0", name="Comb bottom"
            ),
            allsolve.CadGdsLayer(
                layer=12,
                type=0,
                absolute_z0="31.0",
                thickness="0.25",
                name="Oxide separator",
            ),
            allsolve.CadGdsLayer(
                layer=11, type=0, absolute_z0="0.0", thickness="1.0", name="Anchor"
            ),
        ],
        # extrude_parameters is optional. Using default values here for demonstration.
        extrude_parameters=allsolve.CadGdsExtrudeParameters(
            unify_layer_discretizations=allsolve.CadGdsUnifyLayerDiscretizations.OFF,
            fuzzy_value=1e-04,
            feature_angle_threshold=30.0,
            length_ratio_threshold=5.0,
            circle_max_arc_angle_per_segment=5.625,
            circle_fit_tolerance_fraction=200,
            spline_method=allsolve.CadSplineMethod.ITERATIVE,
            spline_tolerance=1e-1,
            iterative_max_iterations=5,
        ),
    )
    geometry_builder.build(print_logs=verbose, on_error=allsolve.OnError.RAISE)


def create_regions(project: allsolve.Project) -> SimpleNamespace:
    regions = SimpleNamespace()

    regions.gold = project.create_region_rule(
        name="gold",
        entity_type=allsolve.Region.VOLUME,
        attribute_path=[("name", "Reflector")],
    )
    regions.anchor = project.create_region_rule(
        name="anchor",
        entity_type=allsolve.Region.VOLUME,
        attribute_path=[("name", "Anchor")],
    )
    regions.separators = project.create_region_rule(
        name="separators",
        entity_type=allsolve.Region.VOLUME,
        attribute_path=[("name", "Oxide separator")],
    )
    regions.comb_top = project.create_region_rule(
        name="comb top",
        entity_type=allsolve.Region.VOLUME,
        attribute_path=[("name", "Comb top")],
    )
    regions.comb_bottom = project.create_region_rule(
        name="comb bottom",
        entity_type=allsolve.Region.VOLUME,
        attribute_path=[("name", "Comb bottom")],
    )

    regions.clamp = project.create_region_computed(
        name="clamp",
        entity_type=allsolve.Region.VOLUME,
        operation=allsolve.RegionOperation.UNION,
        source_regions=[
            regions.anchor.id,
        ],
    )
    regions.silicon_dioxide = project.create_region_computed(
        name="silicon_dioxide",
        entity_type=allsolve.Region.VOLUME,
        operation=allsolve.RegionOperation.UNION,
        source_regions=[
            regions.anchor.id,
            regions.separators.id,
        ],
    )
    regions.monocrystalline_silicon = project.create_region_computed(
        name="monocrystalline_silicon",
        entity_type=allsolve.Region.VOLUME,
        operation=allsolve.RegionOperation.UNION,
        source_regions=[
            regions.comb_top.id,
            regions.comb_bottom.id,
        ],
    )
    regions.all = project.create_region_computed(
        name="all",
        entity_type=allsolve.Region.VOLUME,
        operation=allsolve.RegionOperation.UNION,
        source_regions=[
            regions.silicon_dioxide.id,
            regions.gold.id,
            regions.monocrystalline_silicon.id,
        ],
    )

    return regions


def create_materials(project: allsolve.Project, regions: SimpleNamespace) -> None:
    project.create_material(
        name="Gold",
        description="Gold",
        color="#FFCE46",
        abbreviation="Au",
        target_region=regions.gold,
        density="19280",
        heat_capacity="128",
        coefficient_of_thermal_expansion="14.2e-6",
        electric_conductivity="4.55e7",
        electric_permittivity="epsilon0",
        magnetic_permeability="mu0",
        thermal_conductivity="301",
        elasticity_matrix=allsolve.MaterialProperty.ElasticityMatrixYoungsModulusPoissonsRatio(
            "77e9",
            "0.42",
        ),
    )
    project.create_material(
        name="Silicon dioxide",
        description="Amorphous SiO2",
        color="#BB1C1C",
        abbreviation="SiO₂",
        target_region=regions.silicon_dioxide,
        density="2200",
        heat_capacity="733",
        coefficient_of_thermal_expansion="7.64e-6",
        electric_permittivity="3.9*epsilon0",
        magnetic_permeability="mu0",
        thermal_conductivity="9.50",
        elasticity_matrix=allsolve.MaterialProperty.ElasticityMatrixYoungsModulusPoissonsRatio(
            "70e9",
            "0.17",
        ),
    )
    project.create_material(
        name="Monocrystalline silicon",
        description="Silicon wafer",
        color="#9AA7C5",
        abbreviation="Mono-Si",
        target_region=regions.monocrystalline_silicon,
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
    solid_mechanics_physics = project.add_physics(allsolve.Physics.SolidMechanics())
    solid_mechanics_physics.add_interactions(
        [
            allsolve.Interaction.SolidMechanicsClamp(
                name="Clamp",
                target=regions.clamp,
            ),
        ]
    )


def create_mesh(project: allsolve.Project, regions: SimpleNamespace) -> allsolve.Mesh:
    mesh = project.create_mesh(
        allsolve.MeshSettings(
            name="Mesh 1",
            use_mesh_refiner=False,
            scale_factor=0.25,
            curvature_enhancement=12.0,
            target_width_to_height_ratio=4.0,
            max_run_time_minutes=60,
            extrusion=allsolve.MeshExtrusion(
                regions=[regions.all], sub_layer_counts=["5", "10", "5", "10", "5"]
            ),
        ),
    )
    return mesh


def create_simulation(
    project: allsolve.Project, mesh: allsolve.Mesh
) -> allsolve.Simulation:
    sim = project.create_simulation_eigenmode(
        name="Simulation 1",
        description="",
        max_run_time_minutes=60,
        solver_mode=allsolve.SolverMode.ITERATIVE,
        mesh=mesh.id,
        num_requested_eigenmodes="5",
        target_eigenfrequency="0",
        solver_tolerance="1e-6",
    )
    sim.add_outputs(
        [
            allsolve.Output.FieldOutput(
                name="u",
                expression="u",
                field_output_skin_only=True,
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

    sim.run(print_logs=True)
    print("Simulation status:", sim.get_status())


if __name__ == "__main__":
    main()
