"""
Create and run a microstrip stub filter simulation with a Cartesian product
sweep over frequency and stub length.

Only the ``allsolve`` package is required.  After the simulation finishes the
project is stored via ``client.set_current_project`` so the companion
``visualize_geometric_sweep.py`` script can pick it up for plotting.
"""

import traceback

import allsolve

from control import (
    setup_client,
    create_project,
    create_variables,
    create_regions,
    create_materials,
    create_physics,
    create_cartesian_sweep,
    create_simulation,
)
from geo import build_geometry, create_and_run_mesh

sim: allsolve.Simulation | None = None

try:
    client = setup_client()
    project = create_project(client)

    create_variables(project)
    build_geometry(project)

    regions = create_regions(project)
    create_materials(project, regions)
    em_physics = create_physics(project, regions)
    sweep = create_cartesian_sweep(project)
    mesh = create_and_run_mesh(project, sweep=sweep)

    sim = create_simulation(project, mesh, em_physics, sweep)

    print("Starting simulation ...")
    sim.run(print_logs=True, on_error=allsolve.OnError.RAISE)
    print("Simulation completed.")

    client.set_current_project(project)

except Exception:
    print("Something failed, aborting simulation")
    print(traceback.format_exc())
    if sim is not None and sim.is_running():
        sim.abort()
