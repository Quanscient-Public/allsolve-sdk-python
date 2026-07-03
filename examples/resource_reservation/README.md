# Introduction

This example demonstrates **compute resource reservations** with the Quanscient Allsolve SDK.

The resource reservations can be used to avoid waiting for cloud compute to be
reserved before each job. For example, if you have multiple simulations then the wait is repeated
for every job and can add up to significant overhead compared to the actual solver time.

Resource reservations let you **hold compute up front** and reuse the same pool across multiple
jobs. Each subsequent run starts on already-reserved nodes instead of waiting for the cloud again.

The scripts use the same bending-beam model as [`bending_beam/`](../bending_beam/), but show
two ways to use reservations:

1. **In-process (single script)** — create separate preprocess (geometry + mesh) and simulation
   pools inside one script, run jobs against each pool, then release when done.
2. **Cross-process (CLI + workload script)** — run an interactive CLI in one terminal to create
   and keep a reservation alive; run mesh and simulation jobs from another script that picks up
   the reservation id from a local handoff file.

Each reservation has a **120-second lease** on the server; if the lease is not renewed
periodically the server releases the reserved resources after 120 seconds.
`ResourceReservation.create()` starts lease renewal automatically. By default the automatic lease
renewal stops if there is **10 minutes** idle time; configurable via `max_idle_seconds`.
Prefer `GeometryBuilder.run()`, `Mesh.run()`, or `Simulation.run()` with `resource_reservation=`
— they renew the lease for the full duration of the job, and idle time timer restarts each time
a job has finished.

See [Usage patterns](#usage-patterns) for create / wait / release, the context-manager
shortcut, and manual `start()` + polling (requires `keep_reservation_alive()`).

## Usage patterns

### Manual create, wait, and release

This is the pattern used by the runnable scripts in this folder (`bending_beam_sweep_with_reservations.py`,
etc.). Use `run()` or `build()` with `resource_reservation=` so the lease stays alive for each job.

```python
import allsolve

pool = allsolve.ResourceReservation.create(
    node_type=allsolve.CPU.CORES_1_16GB,
    num_nodes=1,
)
pool.wait_until_ready()

try:
    mesh.run(
        resource_reservation=pool,
    )
    sim.run(
        resource_reservation=pool,
    )
finally:
    pool.release()
    # pool.wait_until_released() # Optional: Wait until server has released the reserved resources
```

### Context manager (create, run jobs, release on exit)

Using `Client.resource_reservation()`; lease renewal starts automatically; the reservation is
released when the block exits.

```python
import allsolve

client = allsolve.Client()
project = client.create_project(name="my-project")

with client.resource_reservation(
    node_type=allsolve.CPU.CORES_1_16GB,
    num_nodes=1,
) as pool:
    sim.run(
        resource_reservation=pool,
    )
```

Equivalent to the [manual create / wait / release](#manual-create-wait-and-release) flow above,
with `stop_auto_renew()` and `release()` in a `finally` block when the `with` block exits.

### Manual `start()` and polling

Use this when you need custom control between job start and completion.
`Simulation.start()` (and `Mesh.start()`, `GeometryBuilder.start()`)
assign the reservation to the job but **do not** renew the lease while you poll — wrap the poll
loop in `keep_reservation_alive()`:

```python
import allsolve
from allsolve.resource_reservation import keep_reservation_alive

pool = allsolve.ResourceReservation.create(
    node_type=allsolve.CPU.CORES_1_16GB,
    num_nodes=1,
)
pool.wait_until_ready()
try:
    with keep_reservation_alive(pool):
        sim.start(resource_reservation=pool)
        while sim.is_running(refresh_delay_s=1):
            sim.print_new_loglines()
finally:
    pool.release()
```

The same pattern applies to geometry and mesh: `with keep_reservation_alive(pool):` around
`start()` and `while ... is_running(...)`.

If you do not need custom polling, use `Simulation.run()` (or `Mesh.run()`, `GeometryBuilder.build()`)
with `resource_reservation=` instead — see `bending_beam_with_reservation.py`.

## Team quota

When **team credits enforcement** is active for your organization, reservations must be tied to a team. Use `allsolve.get_teams()` to list valid team ids.

- If team credits enforcement is active and you belong to **more than one** team with active credits,
  `team_id` is **required**.
- If you belong to **exactly one** such team, it is assigned automatically when omitted.
- When team credits enforcement is inactive, `team_id` may be omitted.

> **Note:** If a reservation uses a team quota, the project whose simulations you run on that reservation must also be created with the same `team_id`.

```python
import allsolve

client = allsolve.Client()
print("Teams:", client.get_teams()) # Prints team IDs and names

project = client.create_project(
        name="Example project",
        description="Project using team credits",
        team_id="your-team-id",
    )

pool = allsolve.ResourceReservation.create(
    node_type=allsolve.CPU.CORES_1_16GB,
    num_nodes=1,
    team_id="your-team-id",
)
```

## Project structure

| File                                      | Purpose                                                                                                          |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `bending_beam_sweep_with_reservations.py` | Bending-beam parameter sweep with preprocess pool (1 node: geometry + mesh) and simulation pool (4 nodes)        |
| `resource_reservation_cli.py`             | Interactive CLI to create a reservation, auto-renew the lease, list/run project simulations, and release on quit |
| `bending_beam_with_reservation.py`        | Single bending-beam run that waits for a reservation from the CLI and uses it for mesh and simulation            |
| `reservation_handoff.py`                  | Helper for cross-process reservation id handoff via a local file                                                 |

# Prerequisites

Follow [Installation](../README.md#installation) and [Running](../README.md#running)
in the parent example README to set up Python, install the Allsolve SDK,
and configure credentials.

# Running

From the `examples/` directory:

## Example project with two separate reservation pools

```
(venv) $ python resource_reservation/bending_beam_sweep_with_reservations.py
```

## Cross-process: CLI + workload script

Use two terminals:

**Terminal 1** — create and hold a reservation:

```
(venv) $ python resource_reservation/resource_reservation_cli.py
```

When prompted for **Project id**, either leave it empty (no interactive simulation menu),
or paste the project id printed by the workload script after it creates a project.
The project id selects which project's simulations the CLI can list and run — it does not
bind the reservation to that project. Use **Team id** at reservation create time to
select team quota when needed.

**Terminal 2** — run the bending-beam workload against that reservation:

```
(venv) $ python resource_reservation/bending_beam_with_reservation.py
```

Either script can be started first. If the workload script runs before the CLI has written a
reservation id, it prompts you to retry until one is available.

You can also pass the reservation id directly:

```
(venv) $ python resource_reservation/bending_beam_with_reservation.py --reservation-id=<id>
```

## Run simulations on an existing project with CLI script

If you already have a project with simulations defined in Allsolve, you can run them on
reserved compute:

1. Start `resource_reservation_cli.py`.
2. At **Project id**, paste the id of the existing project (do not leave it empty).
3. After the reservation is ready, choose command **`1`** — **List and run a simulation from the project**.
4. Pick a simulation from the numbered list; the CLI runs it with resource reservation on the held pool.

Use **`q`** to quit and release the reservation when done.
