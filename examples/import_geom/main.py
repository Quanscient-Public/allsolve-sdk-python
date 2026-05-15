import os
import allsolve
import signal

api_key = os.environ["QS_ACCESS_KEY"]
api_secret = os.environ["QS_SECRET_KEY"]
allsolve.setup(
    api_key=api_key,
    api_secret=api_secret,
    host="https://allsolve.quanscient.com",
)

# Global variables for signal handler
geometry_builder = None
mesh = None
sim = None


def sigint_handler(signum, frame):
    """Handle SIGINT by aborting running jobs"""
    print("\nReceived interrupt signal. Attempting to abort running jobs...")

    if geometry_builder and geometry_builder.is_running():
        print("Aborting geometry import...")
        geometry_builder.abort()

    if mesh and mesh.is_running():
        print("Aborting mesh generation...")
        mesh.abort()

    if sim and sim.is_running():
        print("Aborting simulation...")
        sim.abort()

    exit(1)


# Register signal handler
signal.signal(signal.SIGINT, sigint_handler)


def run_project(project: allsolve.Project):
    global geometry_builder, mesh, sim

    geometry_builder = project.geometry_builder()

    try:
        # Remove any existing geometry
        geometry_builder.delete()
    except Exception as e:
        print(e)

    geometry_builder.add_sat_file("heat.sat")

    print(geometry_builder)

    geometry_builder.start()

    while geometry_builder.is_running(refresh_delay_s=1):
        pass

    if geometry_builder.get_status() == allsolve.Job.SUCCESS:
        print("Geom Success")
    else:
        print("Geom Failed")

    polysilicon = project.create_region_rule(
        name="polysilicon",
        entity_type=allsolve.Region.VOLUME,
        attribute_path=[("LayerName", "Polysilicon")],
    )

    goldfilm = project.create_region_rule(
        name="goldfilm",
        entity_type=allsolve.Region.VOLUME,
        attribute_path=[("LayerName", "Gold Film (Au)")],
    )

    siliconsub = project.create_region_rule(
        name="siliconsub",
        entity_type=allsolve.Region.VOLUME,
        attribute_path=[("LayerName", "Silicon Sub <100>")],
    )

    print(polysilicon)
    print(goldfilm)
    print(siliconsub)

    polyandgold = project.create_region_computed(
        name="polyandgold",
        entity_type=allsolve.Region.VOLUME,
        operation=allsolve.RegionOperation.UNION,
        source_regions=[polysilicon.id, goldfilm.id],
    )

    print(polyandgold)

    bc_id_0 = project.create_region_rule(
        name="bc_id_0",
        entity_type=allsolve.Region.SURFACE,
        attribute_path=[("BC_ID", "0")],
    )

    bc_id_1 = project.create_region_rule(
        name="bc_id_1",
        entity_type=allsolve.Region.SURFACE,
        attribute_path=[("BC_ID", "1")],
    )

    all = project.create_region_rule(
        name="all",
        entity_type=allsolve.Region.VOLUME,
        bounding_box=allsolve.ExpressionBoundingBox(
            min=allsolve.ExpressionVector(
                x="-0.001",
                y="-0.001",
                z="-0.001",
            ),
            max=allsolve.ExpressionVector(
                x="0.001",
                y="0.001",
                z="0.001",
            ),
        ),
    )

    mesh = project.create_mesh(
        mesh_settings=allsolve.MeshSettings(
            name="test_mesh",
            use_mesh_refiner=True,
            scale_factor=0.7,
            refinements=[
                allsolve.MeshRefinement(
                    region=bc_id_0,
                    max_size=0.5e-6,
                ),
                allsolve.MeshRefinement(
                    region=bc_id_1,
                    max_size=0.5e-6,
                ),
            ],
        ),
    )

    print(mesh)

    mesh.start()

    while mesh.is_running(refresh_delay_s=1):
        mesh.print_new_loglines()

    mesh.print_new_loglines()
    if mesh.get_status() == allsolve.Job.SUCCESS:
        print("Mesh Success")
    else:
        print("Mesh Failed")

    mesh.save_mesh_file(
        output_dir="./",  # Default
        filename="mesh.msh",  # Default
    )

    sim = project.create_simulation(
        name="eigenmode",
        description="Eigenmode simulation",
        max_run_time_minutes=10,
        solver_mode=allsolve.SolverMode.DIRECT,
    )

    sim.set_runtime(
        allsolve.Runtime(
            node_type=allsolve.CPU.CORES_1_16GB,
            node_count=50,
        )
    )

    sim.set_scripts(
        [
            allsolve.Script(
                filepath="sim/simulation.py",
                is_main=True,
            ),
        ],
    )

    sim.mesh_id = mesh.id

    sim.start()

    while sim.is_running(refresh_delay_s=1):
        sim.print_new_loglines()

    sim.print_new_loglines()

    if sim.get_status() == allsolve.Job.SUCCESS:
        print("Simulation Success")
    else:
        print("Simulation Failed")


if __name__ == "__main__":
    project = allsolve.Project.create(
        "test_sat_import",
        "For testing SAT import via SDK",
        geometry_pipeline_version=allsolve.GeometryPipelineVersion.V2,
    )

    try:
        run_project(project)
    finally:
        project.delete()
