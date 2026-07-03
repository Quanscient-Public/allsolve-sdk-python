import os

import gmsh
import allsolve

client = allsolve.Client()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_project(project: allsolve.Project) -> None:
    gmsh.initialize()
    gmsh.open(os.path.join(SCRIPT_DIR, "cube.geo"))
    gmsh.model.mesh.generate()
    mesh_path = os.path.join(SCRIPT_DIR, "cube.msh")
    gmsh.write(mesh_path)
    gmsh.finalize()

    print("Project: {}".format(project.name))

    meshfile = project.add_shared_file(mesh_path)

    sim = project.create_simulation(
        name="acoustics",
        description="Full script acoustics simulation",
        max_run_time_minutes=10,
        solver_mode=allsolve.SolverMode.DIRECT,
    )

    # Add your custom simulation scripts, as many as you need. The directory structure
    # won't be preserved, but all files are loaded to the same folder in the simulation
    # worker nodes. Parameter "is_main" defaults to False.
    sim.set_scripts(
        [
            allsolve.Script(
                os.path.join(SCRIPT_DIR, "sim", "main.py"),
                is_main=True,
            ),
        ]
    )

    # Select your simulation runtime configuration, ie. node count and type. Note that
    # allsolve.CPU.CORES_3_10GB_FAST_START cannot be run with more than 1 node.
    sim.set_runtime(
        allsolve.Runtime(
            node_count=1,
            node_type=allsolve.CPU.CORES_1_16GB,
        )
    )

    # Tell the simulation to use the previously added shared mesh
    sim.set_shared_files([meshfile])

    # You can add parameters on the fly via files like this, only
    # for this single simulation:
    sim.add_json_file(
        "material_params.json",
        {
            "density": {
                "air": 1.293,
                "steel": 7850,
            },
            "speedofsound": {
                "air": 340,
                "steel": 5000,
            },
        },
    )
    #
    # Then in the simulation script read the json file
    # "material_params.json" to get the values.

    sim.start()

    # Wait until simulation is in one of the end states
    while sim.is_running(refresh_delay_s=1):
        sim.print_new_loglines()  # prints new log lines live

    sim.print_new_loglines()  # print remaining new log lines if any

    # Print status without refreshing it, to check for success
    print(sim.get_status())

    # You can get values added with `setoutputvalue()` calls using
    print(sim.get_output_values())

    output_dir = os.path.join(SCRIPT_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)

    # To save VTUs use
    sim.save_output_field("p harmonic 2", output_dir=output_dir)

    # To save a modified / deformed mesh, use setoutputmesh() function on the
    # simulation side and save with
    # sim.save_output_mesh("meshname", output_dir=output_dir)

    # You can save any other files you might have written:
    sim.save_output_files(["Test_file.txt"], output_dir=output_dir)


if __name__ == "__main__":
    project = allsolve.Project.create(
        "full_script_template",
        "Full script acoustics example with external mesh",
    )

    try:
        run_project(project)
    finally:
        if input("Delete project? [Y/n]: ").strip().lower() in ("", "y", "yes"):
            project.delete()
            print("Project deleted.")
