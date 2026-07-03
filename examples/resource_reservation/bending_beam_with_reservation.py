"""
Bending beam demo using a compute pool held by resource_reservation_cli.py.

Run ``resource_reservation_cli.py`` in one terminal to create a reservation and
keep it alive with auto-renew. Run this script in another terminal. It creates a
project, waits for a reservation if needed, then passes it to mesh and simulation
jobs. The CLI owns renewal and release; this script does not create or release
the reservation.

Either script can be started first. When the CLI prompts for **Project id**:

* Leave it empty to skip interactive simulation listing in the CLI.
* Or paste the project id printed by this script after it creates a project,
  so the CLI can list and run simulations from that project.

When team credits enforcement is active, the reservation and the project must
use the same ``team_id`` — select the team in the CLI and pass the same id to
``client.create_project``.

If no reservation id is available yet, this script prompts you to retry until
the CLI writes one. Press Ctrl+C while waiting to cancel and delete the project.

You can also pass ``--reservation-id``.
"""

from __future__ import annotations

import argparse
import sys
from types import SimpleNamespace

import allsolve

from reservation_handoff import read_reservation_id


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bending beam demo using a reservation from resource_reservation_cli.py",
    )
    parser.add_argument(
        "--reservation-id",
        help="Reservation id to use (overrides handoff file)",
    )
    return parser.parse_args()


def _wait_for_reservation(
    *,
    reservation_id: str | None = None,
) -> allsolve.ResourceReservation:
    print(
        "Waiting for a reservation from resource_reservation_cli.py...\n"
        "(Ctrl+C to cancel and delete the project)"
    )
    while True:
        resolved_id = reservation_id or read_reservation_id()
        if resolved_id is not None:
            reservation = allsolve.ResourceReservation.get(resolved_id)
            reservation.refresh()
            print(
                f"Using reservation {reservation.id} "
                f"(status={reservation.status.value}, expires_at={reservation.expires_at})"
            )
            return reservation
        print(
            "No reservation id found. Start resource_reservation_cli.py "
            "in another terminal, or pass --reservation-id.",
            file=sys.stderr,
        )
        input("Press Enter to try again...")


def _delete_project(project: allsolve.Project) -> None:
    try:
        project.delete()
        print(f"Deleted project {project.name} (id: {project.id}).")
    except Exception as e:
        print(
            f"Failed to delete project {project.name} (id: {project.id}): {e}",
            file=sys.stderr,
        )


def main() -> None:
    args = _parse_args()
    client = allsolve.Client()
    verbose = True
    project: allsolve.Project | None = None

    try:
        project = client.create_project(
            name="Bending beam (reservation)",
            description="Bending beam with resource reservation",
            # team_id="your-team-id", # See README "Team quota"
        )
        print(f"Created project: {project.name} (id: {project.id})")

        print("Creating variables")
        project.create_variables(
            [
                ("length", "24e-3", "Length of the beam"),
                ("width", "2e-3", "Width of the beam"),
                ("height", "3e-3", "Height of the beam"),
                ("tolerance", "1e-4", "Tolerance for regions"),
            ]
        )

        print("Creating geometry")
        project.geometry_builder().add_box(
            name="beam",
            position=(0, 0, 0),
            size=("length", "width", "height"),
        ).build(print_logs=verbose, on_error=allsolve.OnError.RAISE)

        print("Creating regions")
        regions = SimpleNamespace()
        regions.beam_volume = project.create_region_rule(
            name="beam_volume",
            entity_type=allsolve.Region.VOLUME,
            max_size=allsolve.ExpressionVector(
                x="length + tolerance",
                y="width + tolerance",
                z="height + tolerance",
            ),
            min_size=allsolve.ExpressionVector(
                x="length - tolerance",
                y="width - tolerance",
                z="height - tolerance",
            ),
        )
        regions.clamp_surface = project.create_region_rule(
            name="clamp_surface",
            entity_type=allsolve.Region.SURFACE,
            bounding_box=allsolve.ExpressionBoundingBox(
                min=allsolve.ExpressionVector(
                    x="(-length / 2) - tolerance",
                    y="(-width / 2) - tolerance",
                    z="(-height / 2) - tolerance",
                ),
                max=allsolve.ExpressionVector(
                    x="(-length / 2) + tolerance",
                    y="(width / 2) + tolerance",
                    z="(height / 2) + tolerance",
                ),
            ),
        )
        regions.top_surface = project.create_region_rule(
            name="top_surface",
            entity_type=allsolve.Region.SURFACE,
            bounding_box=allsolve.ExpressionBoundingBox(
                min=allsolve.ExpressionVector(
                    x="(-length / 2) - tolerance",
                    y="(-width / 2) - tolerance",
                    z="(height / 2) - tolerance",
                ),
                max=allsolve.ExpressionVector(
                    x="(length / 2) + tolerance",
                    y="(width / 2) + tolerance",
                    z="(height / 2) + tolerance",
                ),
            ),
        )

        print("Creating materials")
        project.create_material(
            name="Aluminium",
            description="Aluminium",
            color="#aaaaaa",
            abbreviation="Al",
            target_region=regions.beam_volume,
            coefficient_of_thermal_expansion=1e-06,
            density=2700,
            elasticity_matrix=allsolve.MaterialProperty.ElasticityMatrixYoungsModulusPoissonsRatio(
                "68000000000.0",
                "0.32",
            ),
            electric_conductivity=36900000.0,
            electric_permittivity="epsilon0",
            heat_capacity=897,
            magnetic_permeability="mu0",
            speed_of_sound=6320,
            thermal_conductivity=237,
        )

        print("Creating physics and interactions")
        physics_set = project.get_default_physics_set()
        solid_mechanics_physics = physics_set.add_physics(
            allsolve.Physics.SolidMechanics()
        )
        solid_mechanics_physics.add_interactions(
            [
                allsolve.Interaction.SolidMechanicsClamp(
                    name="Clamp",
                    target=regions.clamp_surface,
                ),
                allsolve.Interaction.SolidMechanicsLoad(
                    name="Load",
                    target=regions.top_surface,
                    force=(0, 0, -1000),
                ),
            ]
        )

        print("Creating mesh with reserved compute")
        mesh = project.create_mesh()

        reservation = _wait_for_reservation(reservation_id=args.reservation_id)

        print("Running mesh with reserved compute")
        mesh.run(
            print_logs=verbose,
            on_error=allsolve.OnError.RAISE,
            resource_reservation=reservation,
        )

        print("Creating simulation")
        sim = project.create_simulation_static(
            name="Simulation",
            description="Simulation 1",
            max_run_time_minutes=10,
            solver_mode=allsolve.SolverMode.DIRECT,
            mesh=mesh.id,
            physics_set=physics_set,
        )
        sim.add_outputs(
            [
                allsolve.Output.FieldOutput(
                    name="Displacement",
                    expression="u",
                ),
            ]
        )

        print("Running simulation with reserved compute")
        sim.run(
            print_logs=verbose,
            on_error=allsolve.OnError.RAISE,
            resource_reservation=reservation,
        )
        print("Simulation status:", sim.get_status())

    except KeyboardInterrupt:
        print("\nInterrupted.")
        if project is not None:
            _delete_project(project)
        sys.exit(130)


if __name__ == "__main__":
    main()
