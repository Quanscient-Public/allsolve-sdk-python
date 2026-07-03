from pathlib import Path

import allsolve
import signal

SCRIPT_DIR = Path(__file__).resolve().parent

# Global variables for signal handler
geom = None
mesh = None
sim = None


def sigint_handler(signum, frame):
    """Handle SIGINT by aborting running jobs"""
    print("\nReceived interrupt signal. Attempting to abort running jobs...")

    if geom and geom.is_running():
        print("Aborting geometry import...")
        geom.abort()

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

    sim = project.create_simulation(
        name="electrostatics",
        description="Electrostatics simulation",
        max_run_time_minutes=10,
        solver_mode=allsolve.SolverMode.DIRECT,
    )

    sim.set_runtime(
        allsolve.Runtime(
            node_type=allsolve.CPU.CORES_1_16GB,
            node_count=1,
        )
    )

    sim.set_scripts(
        [
            allsolve.Script(
                filepath=str(SCRIPT_DIR / "sim" / "simulation.py"),
                is_main=True,
            ),
        ],
    )

    sim.mesh_id = project.get_meshes()[0].id
    sim.variable_overrides = project.get_variable_overrides()[0]

    sim.start()

    while sim.is_running(refresh_delay_s=1):
        sim.print_new_loglines()

    sim.print_new_loglines()

    if sim.get_status() == allsolve.Job.SUCCESS:
        print("Simulation Success")
    else:
        print("Simulation Failed")


if __name__ == "__main__":
    client = allsolve.Client()
    project = client.import_project(str(SCRIPT_DIR / "import-format.yaml"))
    # project = client.import_project(str(SCRIPT_DIR / "import-format.json"))

    try:
        run_project(project)
    finally:
        if input("Delete project? [Y/n]: ").strip().lower() in ("", "y", "yes"):
            project.delete()
            print("Project deleted.")
