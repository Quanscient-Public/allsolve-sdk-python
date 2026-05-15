"""
This script demonstrates various features of the Allsolve SDK.
It creates a project with a simplified pin fin heat sink simulation.
The project consists of:
- Variables that are used to define the geometry
- Geometry with a base plate and an array of pins
- Regions for the base plate, pins, and the surrounding air box
- Materials for the base plate, pins, and air
- Physics and interactions for the heat transfer
- Mesh with a default mesh and a custom mesh refinement for the pins
- Simulation with a transient analysis and a custom script section

The simulation outputs:
- ValueOutput data that is printed in CSV format to the console.
  Average temperature of the copper and air is calculated.
- FieldOutput data that can be visualized in the Allsolve web app.
  Add a result visualization it the GUI for Temperature field and
  add a clip filter to view the temperature distribution
  inside the geometry.
"""

import allsolve
from types import SimpleNamespace


def main():
    client = allsolve.Client()

    verbose = True

    project = client.create_project(
        name="Pin fin heat sink demo",
        description="Demo simulation for a pin fin heat sink",
    )
    print(f"Created project: {project.name} (id: {project.id})")

    create_variables(project)
    build_geometry(project, verbose=verbose)
    regions = create_regions(project)
    create_materials(project, regions)
    create_physics(project, regions)
    mesh = create_mesh(project, regions)
    sim = create_simulation(project, mesh)
    run_mesh_and_simulation(mesh, sim, verbose=verbose)
    print_results(sim)


def create_variables(project: allsolve.Project) -> None:
    project.create_variables(
        [
            ("base_length_x", "0.06", "Base plate length in X direction"),
            ("base_width_y", "0.06", "Base plate width in Y direction"),
            ("base_thickness", "0.005", "Base plate thickness"),
            ("pin_radius", "0.002", "Radius of cylindrical pins"),
            ("pin_height", "0.025", "Height of cylindrical pins"),
            ("pin_spacing", "0.008", "Center-to-center spacing between pins"),
            ("num_pins_x", "7", "Number of pins in X direction"),
            ("num_pins_y", "7", "Number of pins in Y direction"),
            (
                "offset_x",
                "- (num_pins_x - 1) * pin_spacing / 2",
                "X offset to center the pin array",
            ),
            (
                "offset_y",
                "- (num_pins_y - 1) * pin_spacing / 2",
                "Y offset to center the pin array",
            ),
            ("air_box_size", "0.1", "Size of the air box (cube)"),
        ]
    )


def build_geometry(project: allsolve.Project, verbose: bool = False) -> None:
    geometry_builder = project.geometry_builder()

    geometry_builder.add_box(
        name="base_plate",
        position=(0.0, 0.0, 0.0),
        size=("base_length_x", "base_width_y", "base_thickness"),
    )

    geometry_builder.add_cylinder(
        name="single_pin",
        position=("offset_x", "offset_y", "base_thickness / 2 + pin_height / 2"),
        axis=(0.0, 0.0, "pin_height"),
        radius="pin_radius",
    )

    geometry_builder.add_grid(
        name="pin_array",
        translation=("pin_spacing", "pin_spacing", 0.0),
        size=("num_pins_x", "num_pins_y", "1"),
        cad_names=["single_pin"],
    )

    geometry_builder.add_box(
        name="air_box",
        position=(0.0, 0.0, "air_box_size / 2 - base_thickness / 2"),
        size=("air_box_size", "air_box_size", "air_box_size"),
    )

    geometry_builder.add_difference(
        name="air_box_without_pins_and_base_plate",
        cad_names_1=["air_box"],
        cad_names_2=["pin_array", "base_plate"],
        delete_tool=False,
    )

    geometry_builder.build(print_logs=verbose, on_error=allsolve.OnError.RAISE)


def create_regions(project: allsolve.Project) -> SimpleNamespace:
    regions = SimpleNamespace()

    regions.copper_material_region = project.create_region_rule(
        name="copper_material_region",
        entity_type=allsolve.Region.VOLUME,
        bounding_box=(
            ("-base_length_x / 2", "-base_width_y / 2", "-base_thickness / 2"),
            (
                "base_length_x / 2",
                "base_width_y / 2",
                "base_thickness / 2 + pin_height",
            ),
        ),
    )

    regions.air = project.create_region_rule(
        name="air",
        entity_type=allsolve.Region.VOLUME,
        min_size=("air_box_size", "air_box_size", "air_box_size"),
    )

    regions.pins = project.create_region_rule(
        name="pins",
        entity_type=allsolve.Region.VOLUME,
        max_size=("pin_radius * 2", "pin_radius * 2", "pin_height"),
    )

    regions.pin_surfaces = project.create_region_rule(
        name="pin_surfaces",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=(
            ("-base_length_x / 2", "-base_width_y / 2", "0"),
            (
                "base_length_x / 2",
                "base_width_y / 2",
                "base_thickness / 2 + pin_height",
            ),
        ),
    )

    regions.plate_top_surface = project.create_region_rule(
        name="plate_top_surface",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=(
            ("-base_length_x / 2", "-base_width_y / 2", "base_thickness / 2"),
            ("base_length_x / 2", "base_width_y / 2", "base_thickness / 2"),
        ),
    )

    # Union of pin surfaces and plate top surface for convection boundary
    regions.convection_surfaces = project.create_region_computed(
        name="convection_surfaces",
        entity_type=allsolve.Region.SURFACE,
        operation=allsolve.RegionOperation.UNION,
        source_regions=[
            regions.pin_surfaces.id,
            regions.plate_top_surface.id,
        ],
    )

    regions.plate_bottom_surface = project.create_region_rule(
        name="plate_bottom_surface",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=(
            ("-base_length_x / 2", "-base_width_y / 2", "-base_thickness / 2"),
            ("base_length_x / 2", "base_width_y / 2", "-base_thickness / 2"),
        ),
    )

    return regions


def create_materials(project: allsolve.Project, regions: SimpleNamespace) -> None:
    project.create_material_from_library(
        name="Copper",
        target_region=regions.copper_material_region,
    )
    project.create_material_from_library(
        name="Air",
        target_region=regions.air,
    )


def create_physics(project: allsolve.Project, regions: SimpleNamespace) -> None:
    heat_transfer_physics = project.add_physics(allsolve.Physics.HeatTransfer())
    heat_transfer_physics.add_interactions(
        [
            allsolve.Interaction.HeatTransferHeatSource(
                name="Heat source",
                target=regions.plate_bottom_surface,
                heat_source_power_density="100",
            ),
            allsolve.Interaction.HeatTransferConvection(
                name="Convection",
                target=regions.convection_surfaces,
                heat_transfer_convection_heat_transfer_coefficient="10",
                heat_transfer_convection_fluid_temperature="293.15",
            ),
        ]
    )


def create_mesh(project: allsolve.Project, regions: SimpleNamespace) -> allsolve.Mesh:
    mesh = project.create_mesh(
        allsolve.MeshSettings(
            name="Default mesh",
            scale_factor=1.0,
            curvature_enhancement=6.0,
            max_run_time_minutes=10,
            refinements=[
                allsolve.MeshRefinement(
                    region=regions.pins,
                    max_size="pin_height / 10",
                ),
            ],
        ),
    )
    return mesh


def create_simulation(
    project: allsolve.Project, mesh: allsolve.Mesh
) -> allsolve.Simulation:
    sim = project.create_simulation_transient(
        name="Heat sink demo",
        description="Transient simulation of heat transfer",
        max_run_time_minutes=10,
        solver_mode=allsolve.SolverMode.DIRECT,
        mesh=mesh.id,
        timestep_algorithm=allsolve.TimestepAlgorithm.IMPLICIT_EULER,
        transient_start_time="0",
        transient_end_time="10",
        transient_timestep_size="1",
    )

    sim.add_outputs(
        [
            allsolve.Output.FieldOutput(
                name="Temperature",
                expression="T",
            ),
            allsolve.Output.ValueOutput(
                name="Average temperature (copper)",
                expression="average(reg.copper_material_region, T, 3)",
            ),
            allsolve.Output.ValueOutput(
                name="Average temperature (air)",
                expression="average(reg.air, T, 3)",
            ),
        ]
    )

    sim.set_scripts(
        [
            allsolve.Script(
                name="afterFieldsCreated.py",
                section_name=allsolve.CustomSection.AFTER_FIELDS_CREATED,
                content="fld.T.setvalue(reg.all, 293.15)",
            )
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
    if sim.get_status() != allsolve.Job.SUCCESS:
        raise ValueError(f"Simulation failed: {sim.get_status()}")


def print_results(sim: allsolve.Simulation) -> None:
    output_data = sim.get_output_data()
    results = output_data.to_csv(csv_format=allsolve.CsvExportFormat.NORMAL)
    print("Simulation output:")
    print(results)

    output_data.clean_cache()


if __name__ == "__main__":
    main()
