"""
Interactive CLI: create a resource reservation, renew until you quit, then release.

Startup prompts (press Enter to accept defaults in brackets):

- **Node type** — choose a numbered :class:`~allsolve.CPU` size.
- **Number of nodes** — default ``1``.
- **Number of replicas** — default ``1``.
- **Project id** — optional. Leave empty to skip interactive simulation listing.
  When set, menu option ``1`` lets you list and run simulations from that project.
- **Team** — fetched automatically via ``client.get_teams()``. When teams exist, a
  numbered menu is shown (``1 = No team``, ``2+`` = available teams). When no teams
  are found, the prompt is skipped.
- **Max idle seconds** — default ``600`` (10 minutes of idle time between jobs;
  auto-renew stops after this limit but the reservation is not released).

After the reservation is ready, the CLI keeps the lease alive with idle auto-renew and
writes its id to a local handoff file (see ``reservation_handoff.py``). Another
script in a separate process can pick it up from that file.

**Project id:** If you provide one, menu option ``1`` lets you list and run
simulations from that project. If you leave it empty, skip option ``1`` in this
CLI and run your workload from another script that reads the reservation id and
passes the reservation to ``simulation.run(resource_reservation=...)`` (or mesh
APIs that accept a reservation).

**Team:** Teams are fetched automatically. If you belong to teams, a selection
menu appears. Choose "No team" to skip, or pick a team whose quota to use.
When no teams are found the prompt is skipped entirely.

Interactive commands:

- ``1`` — List and run a simulation from the project (shown only when a project
  id was given)
- ``2`` — Renew reservation manually
- ``3`` — Refresh reservation status
- ``q`` — Quit and release

On quit or interrupt, the reservation is released and the stored id is cleared.
"""

from __future__ import annotations

from dataclasses import dataclass

import allsolve

from reservation_handoff import clear_reservation_id, write_reservation_id


@dataclass(frozen=True, slots=True)
class Command:
    """Interactive command shown in the menu and selected by number."""

    key: str
    label: str
    menu_number: int
    requires_project: bool = False


COMMANDS: tuple[Command, ...] = (
    Command(
        "run_simulation",
        "List and run a simulation from the project",
        menu_number=1,
        requires_project=True,
    ),
    Command("renew", "Renew reservation manually", menu_number=2),
    Command("status", "Refresh reservation status", menu_number=3),
)

QUIT_COMMAND = Command("quit", "quit and release", menu_number=0)
QUIT_KEY = "q"


def _visible_commands(*, has_project: bool) -> list[tuple[int, Command]]:
    visible: list[tuple[int, Command]] = []
    for command in COMMANDS:
        if command.requires_project and not has_project:
            continue
        visible.append((command.menu_number, command))
    return visible


def _command_by_number(*, has_project: bool) -> dict[str, Command]:
    return {
        str(number): command
        for number, command in _visible_commands(has_project=has_project)
    }


def _unknown_command_message(*, has_project: bool) -> str:
    keys = [str(number) for number, _ in _visible_commands(has_project=has_project)]
    keys.append(QUIT_KEY)
    return f"Unknown command. Use {', '.join(keys)}."


def _prompt(text: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{text}{suffix}: ").strip()
    if not value and default is not None:
        return default
    return value


def _cpu_choices() -> list[allsolve.CPU]:
    """CPU sizes available for reservations (excludes :attr:`~allsolve.CPU.DEFAULT`)."""
    return [member for member in allsolve.CPU if member.value is not None]


def _prompt_node_type(*, default_index: int = 1) -> allsolve.CPU:
    """Print numbered :class:`~allsolve.CPU` options and return the selected member."""
    choices = _cpu_choices()
    print("Node type:")
    for index, cpu in enumerate(choices, start=1):
        print(f"  {index}) {cpu.name} — {cpu.value}")
    while True:
        raw = input(f"Choose 1-{len(choices)} [{default_index}]: ").strip()
        if not raw:
            return choices[default_index - 1]
        try:
            selected = int(raw)
        except ValueError:
            print(f"Enter a number from 1 to {len(choices)}.")
            continue
        if 1 <= selected <= len(choices):
            return choices[selected - 1]
        print(f"Enter a number from 1 to {len(choices)}.")


def _print_commands(*, has_project: bool) -> None:
    print("Commands:")
    for number, command in _visible_commands(has_project=has_project):
        print(f"  {number} - {command.label}")
    print(f"  {QUIT_KEY} - {QUIT_COMMAND.label}")


def _print_project_info(project: allsolve.Project) -> None:
    print(f"Project: {project.name} (id={project.id})")


def _print_session_context(
    project: allsolve.Project | None,
    reservation: allsolve.ResourceReservation,
) -> None:
    print()
    if project is not None:
        _print_project_info(project)
        print()
    reservation.refresh()
    print(
        f"Reservation: id={reservation.id} "
        f"status={reservation.status.value} "
        f"expires_at={reservation.expires_at}"
    )
    print()
    _print_commands(has_project=project is not None)


def _prompt_simulation(project: allsolve.Project) -> allsolve.Simulation | None:
    simulations = project.get_simulations()
    if not simulations:
        print("No simulations in project.")
        return None

    print("Simulations:")
    for index, simulation in enumerate(simulations, start=1):
        status = simulation.get_status()
        print(f"  {index}) {simulation.name} (id={simulation.id}, status={status})")

    while True:
        raw = input(f"Choose 1-{len(simulations)} or Enter to cancel: ").strip()
        if not raw:
            return None
        try:
            selected = int(raw)
        except ValueError:
            print(f"Enter a number from 1 to {len(simulations)}, or Enter to cancel.")
            continue
        if 1 <= selected <= len(simulations):
            return simulations[selected - 1]
        print(f"Enter a number from 1 to {len(simulations)}, or Enter to cancel.")


def _run_simulation(
    project: allsolve.Project,
    reservation: allsolve.ResourceReservation,
) -> None:
    simulation = _prompt_simulation(project)
    if simulation is None:
        print("Run cancelled.")
        return

    print(f"Running simulation '{simulation.name}' with reserved compute...")
    simulation.run(
        print_logs=True,
        on_error=allsolve.OnError.RAISE,
        resource_reservation=reservation,
    )
    print(f"Simulation '{simulation.name}' status: {simulation.get_status()}")


def _execute_command(
    command: Command,
    *,
    project: allsolve.Project | None,
    reservation: allsolve.ResourceReservation,
) -> None:
    if command.key == "renew":
        reservation.renew_lease()
        reservation.refresh()
        print("Renewed reservation manually.")
    elif command.key == "status":
        reservation.refresh()
    elif command.key == "run_simulation":
        if project is None:
            raise RuntimeError(f"Command {command.key!r} requires a project")
        _run_simulation(project, reservation)


def _prompt_team(client: allsolve.Client) -> str | None:
    """Fetch user's teams and show a selection menu. Returns the team id or ``None``."""
    teams = client.get_teams()
    if not teams:
        return None

    print("Team:")
    print("  1) No team")
    for index, team in enumerate(teams, start=2):
        print(f"  {index}) {team.name} (id={team.id})")

    while True:
        raw = input(f"Choose 1-{len(teams) + 1} [1]: ").strip()
        if not raw or raw == "1":
            return None
        try:
            selected = int(raw)
        except ValueError:
            print(f"Enter a number from 1 to {len(teams) + 1}.")
            continue
        if 2 <= selected <= len(teams) + 1:
            return teams[selected - 2].id
        print(f"Enter a number from 1 to {len(teams) + 1}.")


def _release_reservation(
    reservation: allsolve.ResourceReservation,
) -> None:
    clear_reservation_id()
    try:
        reservation.release()
        print(f"Released reservation {reservation.id}.")
    except allsolve.ResourceReservationError as e:
        print(f"Release failed: {e}")


def main() -> None:
    client = allsolve.Client()
    reservation: allsolve.ResourceReservation | None = None

    try:
        print("Enter resource reservation details:")
        node_type = _prompt_node_type()
        num_nodes = int(_prompt("Number of nodes", "1"))
        num_replicas = int(_prompt("Number of replicas", "1"))
        team_id = _prompt_team(client)
        project_id = _prompt("Project id (optional, for simulation menu)") or None
        max_idle_seconds = float(
            _prompt(
                "Max idle seconds",
                str(int(allsolve.resource_reservation.DEFAULT_MAX_IDLE_SECONDS)),
            )
        )

        project: allsolve.Project | None = None
        if project_id is not None:
            project = allsolve.Project.get(project_id)
            print(f"Project: {project.name} (id={project.id})")

        print("Creating reservation...")
        reservation = allsolve.ResourceReservation.create(
            num_nodes=num_nodes,
            num_replicas=num_replicas,
            node_type=node_type,
            team_id=team_id,
            max_idle_seconds=max_idle_seconds,
        )
        reservation.wait_until_ready()
        print(
            f"Reservation {reservation.id} is {reservation.status.value} "
            f"(expires_at={reservation.expires_at})"
        )

        handoff_path = write_reservation_id(reservation.id)
        print(f"Reservation id written to: {handoff_path}")

        print(f"Idle auto-renew active (max_idle_seconds={max_idle_seconds:g}).")
        _print_session_context(project, reservation)

        has_project = project is not None
        commands = _command_by_number(has_project=has_project)

        while True:
            cmd = input("> ").strip().lower()
            if cmd == QUIT_KEY:
                break

            command = commands.get(cmd)
            if command is None:
                print(_unknown_command_message(has_project=has_project))
            else:
                _execute_command(
                    command,
                    project=project,
                    reservation=reservation,
                )
            _print_session_context(project, reservation)
    except KeyboardInterrupt:
        if reservation is not None:
            print("\nInterrupted. Releasing reservation...")
        else:
            print("\nAborted.")
    finally:
        if reservation is not None:
            _release_reservation(reservation)


if __name__ == "__main__":
    main()
