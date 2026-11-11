# Allsolve project workflow

**Contents:** [Authentication](#authentication) · [Current project (multi-script workflow)](#current-project-multi-script-workflow) · [One folder per project](#one-folder-per-project) · [Browser + SDK editing](#browser--sdk-editing) · [Reset project (rebuild simulation setup)](#reset-project-rebuild-simulation-setup) · [Teams](#teams) · [Thread-safe client](#thread-safe-client) · [Copy and cleanup](#copy-and-cleanup) · [Temporary project pattern (sweep-and-delete)](#temporary-project-pattern-sweep-and-delete) · [Organization quota](#organization-quota) · [Gotchas](#gotchas)

This reference covers authentication, the current project, reuse across scripts, reset and copy, teams, organization quota and job logs.

## Authentication

Create an Organization API key in the Allsolve UI: **Settings → API keys → Create key**.

```python
client = allsolve.Client(dotenv_file=".env")
# or explicit: Client(api_key=..., api_secret=..., host=...)
print(client.host)
```

Add to `.gitignore`:

```
.env
.allsolve_cache/
.venv/
```

## Current project (multi-script workflow)

Save the current project so that later scripts reuse it and do not create duplicates:

```python
project = client.create_project(name="My study", description="...")
client.set_current_project(project)

# Later script:
project = client.get_current_project()
if project is None:
    raise RuntimeError("No current project. Run the setup script first.")
```

Storage: `.allsolve_cache/.allsolve_current_project_id` (project ID only), relative to the working directory.

Clear the selection: `client.set_current_project(None)`.

**During development**, prefer `get_current_project()` to `create_project()`. Reuse one project and reset it in place while you iterate. **Once mesh or results exist**, keep that project unless the user wants a fresh start. Do not reset it and lose results.

## One folder per project

When you create new projects, give each its own folder. The `.allsolve_cache` that stores the current project ID is per folder. If two unrelated projects share a folder, `get_current_project()` mixes them up. In an existing workspace, follow its layout.

```
my_projects/
├── bending_beam/
│   ├── bending_beam.py
│   └── .allsolve_cache/      ← tracks the beam project
├── chessboard/
│   ├── chessboard.py
│   └── .allsolve_cache/      ← tracks the chessboard project
└── .env                      ← shared credentials (symlink or parent-level)
```

The `.env` file can be shared: symlink it, or put it in a parent folder and pass its relative path.

## Browser + SDK editing

Keep the project open in the browser (`client.get_url(project)`) while you edit it with the SDK. Refresh to see changes. Reference: `examples/edit_project/edit_project.py`.

## Reset project (rebuild simulation setup)

Delete in this order to avoid dangling references:

```python
def reset_project(project: allsolve.Project) -> None:
    for sim in project.get_simulations():
        sim.delete()
    for mesh in project.get_meshes():
        mesh.delete()
    for physic in project.get_physics():
        for interaction in physic.interactions:
            interaction.delete()
        physic.delete()
    for material in project.get_materials():
        material.delete()
    for region in project.get_regions():
        region.delete()
    project.geometry_builder().delete()
    for fn in project.get_interpolated_functions():
        fn.delete()
    for fn in project.get_functions():
        fn.delete()
    for overrides in project.get_variable_overrides():
        overrides.delete()
    for var in reversed(project.get_variables()):
        var.delete()
    for file in project.get_files():
        allsolve.delete_file(file, project.id)
```

Use it before you rebuild geometry or physics in the same project.

It leaves non-default physics sets in place. If the rebuild creates new ones, delete the old ones first: `[ps for ps in project.get_physics_sets() if not ps.is_default]`.

## Teams

When team credits enforcement is active, assign projects to a team:

```python
teams = allsolve.get_teams()  # discover available teams
project = client.create_project(name="...", description="...", team_id=teams[0].id)
print(project.team_id)
```

If the API user belongs to exactly one team with active credits, the team is set automatically. If there are several teams, `team_id` is required.

## Thread-safe client

Use `client.in_thread()` instead of `with client` when threads share a `Client`:

```python
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor() as pool:
    def worker():
        with client.in_thread():
            project = client.get_current_project()
            # ...
    pool.submit(worker)
```

## Copy and cleanup

```python
project.delete()                                          # delete entirely
project.copy(with_results=False, on_error=allsolve.OnError.STRICT)  # duplicate; raises JobError if the copy fails
client.clean_cache()                                      # remove local .allsolve_cache; also deletes downloaded outputs and clears the current project
```

## Temporary project pattern (sweep-and-delete)

For tuning sweeps or convergence studies where you extract the results and then discard the project:

```python
project = client.create_project(name="Tuning sweep", description="...")
results = run_study(project)      # build, sweep, extract the numbers you need
save(results)                     # keep the numbers locally first
project.delete()                  # only after success; on failure the project stays for debugging
```

Ask the user before deleting projects that hold results they may want to inspect.

Use it for two-stage tuning, mesh convergence, or any study where the project is disposable.

## Organization quota

Jobs from all users in your organization count against the same vCPU quota. Check it before you launch:

```python
quota = allsolve.get_quota()
# Organization-level: quota.max_concurrent_cores, quota.total_running_cores
# Team enforcement: quota.team_quota_enforcement_active
# Per-team: quota.teams → list of TeamQuota with team-level limits
```

- `vcpu_limit_exceeded` arrives as `allsolve_rawapi.ApiException` with a JSON body `{"error": "vcpu_limit_exceeded", ...}` (reservations raise `ResourceReservationError` with `.error_code`). Catch it and retry later. Free cores = max − running − reserved (`quota.total_reserved_cores`).
- Node size choice: see [mesh.md](mesh.md#instance-size-node-type).

## Gotchas

- **Older (V1 geometry pipeline) projects:** `export()` warns and omits geometry elements, and `geometry_builder()` raises. Use the per-resource getters.
- **Load existing projects with `Project.get(id)`**, for example to inspect or change projects made in the web UI.
- **`get_logs(limit=N)` returns plain messages without timestamps.** Each call downloads at most `N` new lines and returns all lines downloaded so far. `N` is capped at `LOG_MAX_LIMIT` (25000).
- **Never delete a project while a process still polls it.** A driver in `mesh.run()` or `sim.run()` crashes with `NotFoundException (404)`. Delete only in the process that owns the run. Read-only polls (`get_status`, `get_output_data`) are safe.
- **Split long runs into a launcher and a harvester.** Cloud runs continue when the local process stops. The **launcher** calls `sim.start()` (non-blocking) and skips runs that already exist. The **harvester** reads the cloud state and pulls results, and you can run it again. Make the launcher idempotent: match meshes and simulations by name, skip anything running or completed, and exit in seconds.
