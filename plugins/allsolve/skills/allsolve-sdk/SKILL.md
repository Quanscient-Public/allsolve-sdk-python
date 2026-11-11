---
name: allsolve-sdk
description: >-
  Allsolve SDK (Quanscient Allsolve Python SDK, pip install allsolve): build,
  run and debug multiphysics cloud simulations from Python. Covers projects,
  variables and sweeps, geometry, regions, materials, physics and interactions,
  mesh, simulations and outputs, chained simulations, custom solver scripts and
  FFT post-processing. Use when the user mentions Allsolve or Quanscient,
  wants to port a model from another simulation tool to Allsolve, or when code
  calls create_project, set_current_project, geometry_builder,
  create_region_rule, add_physics, create_mesh, create_simulation_* or
  get_output_data.
---

# Allsolve Python SDK

Official repo: https://github.com/Quanscient-Public/allsolve-sdk-python

## The spec wins

If the user's spec or a reference project names a physics, a boundary condition, an excitation or an analysis type, use it. The defaults and rules of thumb in these skills apply only where the spec says nothing. When a skill rule conflicts with the spec, follow the spec and tell the user.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install allsolve
```

Requires Python 3.10+. Credentials in `.env`:

```
ALLSOLVE_ACCESS_KEY=...
ALLSOLVE_SECRET_KEY=...
ALLSOLVE_HOST=<your Allsolve URL>   # optional; default https://allsolve.quanscient.com
```

```python
import allsolve

client = allsolve.Client()  # finds .env in the working directory; else pass dotenv_file="<path>/.env"
```

The key pair belongs to one Allsolve environment (installation), and `ALLSOLVE_HOST` must point to that environment; a key from another environment fails authentication. Variables already set in the shell override `.env`.

## Documentation lookup: fetch and grep

Do not guess API names. The installed package is the source of truth for the version you run:

```bash
SP=$(python -c "import allsolve, os; print(os.path.dirname(os.path.dirname(allsolve.__file__)))")
rg -n "class SolidMechanicsLoad" -A20 $SP/allsolve/physics/generated/interactions.py   # docstrings give units
```

| Need | Where |
|------|-------|
| SDK class, method, kwarg, units | `$SP/allsolve/` (interaction docstrings state units) |
| Solver scripting API (`qs.*`) | `$SP/quanscient/__init__.pyi` (`src/quanscient-stubs/__init__.pyi` in the SDK repo) |
| Expression functions (`vonmises`, `maxvalue`, …) | Docs: `/documentation/reference/expressions` |
| Closest working example | `examples/` in the SDK repo: clone the tag of your installed version (below) |
| REST API models and endpoints | `$SP/allsolve_rawapi/` (generated client) |
| What changed in a release | `CHANGELOG.md` in the SDK repo |
| Concepts, GUI workflows, tutorials | [references/docs-map.md](references/docs-map.md) |

```bash
# One time: shallow clone to a scratch folder outside the project
V=$(python -c "import allsolve; print(allsolve.__version__)")
git clone --depth 1 --branch "v$V" https://github.com/Quanscient-Public/allsolve-sdk-python.git /tmp/allsolve-sdk-python
```

Docs paths are relative to the user's Allsolve host (`client.host`, from `ALLSOLVE_HOST`; default `https://allsolve.quanscient.com`). The generated SDK reference page on the docs site can be several releases behind. When it disagrees with the installed package, trust the package.

## Before writing code

1. **Start from an example.** Find the closest example with `ls examples/`, then `rg <api name> examples/`. The examples are tested against each SDK release; the snippets in these skills are not.
2. If the simulation targets a specific domain, read the domain skill first:
   - **RF, microwave, antenna** → [../allsolve-domain-rf/SKILL.md](../allsolve-domain-rf/SKILL.md)
   - **Structural mechanics** → [../allsolve-domain-structural/SKILL.md](../allsolve-domain-structural/SKILL.md)
   - **Thermal, heat transfer** → [../allsolve-domain-thermal/SKILL.md](../allsolve-domain-thermal/SKILL.md)
   - **Acoustics, ultrasonics, piezoelectric** → [../allsolve-domain-acoustics/SKILL.md](../allsolve-domain-acoustics/SKILL.md)
3. Read only the references that the task needs:
   - **Project lifecycle**: `Client`, `.env`, `set_current_project`, `get_current_project`, reset, copy, teams, organization quota, job logs → [references/project-workflow.md](references/project-workflow.md)
   - **Variables and sweeps**: `create_variables`, `create_variable_overrides`, `SweepType`, per-sweep-step results, geometry sweeps → [references/variables-and-overrides.md](references/variables-and-overrides.md)
   - **Geometry**: `geometry_builder`, `add_box`, `add_cylinder`, booleans, `add_step_file`, `add_gds2_file`, `CadAlignment`, `build`, PLC and segment-facet errors → [references/geometry.md](references/geometry.md)
   - **Regions**: `create_region_rule`, `create_region_computed`, `create_region_basic`, `bounding_box`, `min_size`, `max_size`, `RegionOperation`, `BOUNDARY`, `attribute_path`, STEP product names, zero entity tags → [references/regions.md](references/regions.md)
   - **Materials**: `create_material`, `create_material_from_library`, `MaterialProperty`, elasticity matrix, damping, `target_region` → [references/materials.md](references/materials.md)
   - **Physics and interactions**: `PhysicsSet`, `get_default_physics_set`, `create_physics_set`, `add_physics`, `Interaction.*`, targeting interactions at regions, coupling several physics, a failing physics or interaction call → [references/physics-and-interactions.md](references/physics-and-interactions.md)
   - **Mesh**: `create_mesh`, `MeshSettings`, `MeshRefinement`, `scale_factor`, `curvature_enhancement`, `get_metrics`, mesh and simulation node type (`CPU`), mesh failure or OOM → [references/mesh.md](references/mesh.md)
   - **Simulation and outputs**: `create_simulation_*`, `sim.run`, `sim.start`, `is_running`, `run_simulations`, `run_meshes`, `refresh_statuses`, `get_status`, `JobError`, `OnError`, `FieldOutput`, `ValueOutput`, `get_output_data`, `save_output_field`, `Runtime`, `ResourceReservation`, chaining with `FieldInitialization`, plotting results → [references/simulation.md](references/simulation.md)
   - **Custom solver scripts**: `set_scripts`, `CustomSection`, `expr`/`par`/`reg`/`fld`, typed stubs (`quanscient/__init__.pyi`), `NameError` in job logs → [references/simulation-scripts.md](references/simulation-scripts.md). Custom time loops and operator extraction → [references/advanced-simulation-scripts.md](references/advanced-simulation-scripts.md)
   - **FFT post-processing** of Allsolve transient outputs: Hanning window, zero-padding, impedance, Tx/Rx sensitivity, centre frequency, -6 dB bandwidth → [references/postprocessing.md](references/postprocessing.md)
   - **GUI names** in a spec or tutorial ("Floating electrode", "Absorbing boundary", "Initial field state") → [references/gui-to-sdk.md](references/gui-to-sdk.md)

## Standard build order

When you create a new project, give it its own folder first (see [project-workflow](references/project-workflow.md#one-folder-per-project)). In an existing workspace, follow its layout.

Follow this order. Later steps depend on earlier ones:

1. **Variables** → [references/variables-and-overrides.md](references/variables-and-overrides.md)
2. **Geometry** → [references/geometry.md](references/geometry.md)
3. **Regions** → [references/regions.md](references/regions.md)
4. **Materials** → [references/materials.md](references/materials.md)
5. **Physics** → [references/physics-and-interactions.md](references/physics-and-interactions.md)
6. **Mesh** → [references/mesh.md](references/mesh.md)
7. **Simulation** → [references/simulation.md](references/simulation.md)
8. **Run**: `mesh.run()`, then `sim.run(print_logs=True)`. Pass `on_error=allsolve.OnError.STRICT`. For geometry sweeps, run `mesh.get_override(sweep).run()` instead of `mesh.run()` (see [variables-and-overrides](references/variables-and-overrides.md#geometry-dependent-sweeps)).

## Key API surfaces

This is a routing map. For signatures, grep the installed package (see [Documentation lookup](#documentation-lookup-fetch-and-grep)).

| Area       | Entry points |
| ---------- | ------------ |
| Client     | `Client`, `create_project`, `get_current_project`, `set_current_project`, `get_project`, `get_url`, `export_project_yaml`, `import_project` |
| Teams      | `get_teams`, `team_id` on `create_project` and `ResourceReservation` |
| Variables  | `create_variables`, `VariableOverrides`, `create_variable_overrides`, `create_variable_from_library` |
| Geometry   | `geometry_builder()` → `add_box`, `add_cylinder`, `add_union`, `add_difference`, … → `build()` |
| Regions    | `create_region_rule`, `create_region_computed`, `create_region_basic`, `region.entity_tags` |
| Materials  | `create_material`, `create_material_from_library` |
| Physics    | `PhysicsSet`, `get_default_physics_set`, `create_physics_set`, `Physics.*`, `Interaction.*` |
| Mesh       | `create_mesh`, `MeshSettings`, `MeshRefinement`, `scale_factor`, `curvature_enhancement`, `get_metrics` |
| Simulation | `create_simulation_static`, `create_simulation_transient`, `create_simulation_harmonic`, `create_simulation_eigenmode`, `create_simulation_multiharmonic`, `FieldInitialization` |
| Reservation| `client.resource_reservation()`, `ResourceReservation`, `ReservationStatus` |

## Units

- Geometry variables and material properties use **SI** (metres, kelvin, kg, Pa, W).
- The CAD kernel may log internal millimetre units. Do not convert by hand unless errors show a mismatch.

## General gotchas

- **The PyPI package name is `allsolve`.**
- **The solver runs in the cloud.** The local Python process only streams logs and waits.
- **Start simple, verify, build up:** run the simplest model first, then add one layer at a time.
- **Prefer sweeps** to individual simulations in a loop. A sweep is one `create_variable_overrides(...)` object, given to the simulation (`variable_overrides=sweep`) and, when a swept variable changes the geometry or the mesh sizes, also to the mesh (`MeshSettings(variable_overrides=[sweep])`). The mesh is then generated once per distinct geometry in the sweep, not once per point, and each point runs as its own job. Run the mesh instances with `mesh.get_override(sweep).run()` or `mesh.run(include_overrides=True)`. Details: [variables-and-overrides](references/variables-and-overrides.md#geometry-dependent-sweeps).
- **A sweep starts all points in parallel.** Run one point first and check it. Then run the sweep. To cap the parallelism, pass a reservation to `run()` (`resource_reservation=pool`; `num_replicas` = number of points at the same time). Reserved replicas cost quota while idle. Scale the simulation's `max_run_time_minutes` with the number of points: the limit covers the whole sweep.
- **Check the quota before you run:** `quota = allsolve.get_quota()`. Jobs from other users in your organization count against the same quota, so you can get `vcpu_limit_exceeded`.
- **The current project is stored per working folder** (`.allsolve_cache/` in the current directory). Two scripts that run from the same folder share it and can overwrite each other's current project. Give each project its own folder, or pass the project ID explicitly.
- **Split scripts into small functions** with a thin `main()`.
- **`Physics.*` builds new physics; `Physic` is the saved server object** (`allsolve.Physic.get_all(project_id)`).
- **Inspecting existing projects**: see [project-workflow](references/project-workflow.md#gotchas) (`export()` limitation and per-resource APIs).
- **Web UI URL format:** `https://<host>/#/projects/<id>`, not `https://<host>/project/<id>`. Use `client.get_url(project)`.
- **Coupled multiphysics: create all physics before you add interactions.** Cross-physics interactions need the fields of the other physics. See [physics-and-interactions](references/physics-and-interactions.md#general).
- **Load and heat-source values are per unit measure of the target** (per volume, area or length). See [physics-and-interactions](references/physics-and-interactions.md#interactions-boundary-conditions).
- **Pass `update_existing=True` to `create_variables`** so that the script can run again. See [variables-and-overrides](references/variables-and-overrides.md#creating-variables).
- **`set_scripts` replaces the whole set.** Pass every script in one call; read the current ones with `get_scripts()`. See [simulation-scripts](references/simulation-scripts.md#attach-custom-code).
- **`is_running()` reads the cached status and does not poll.** In a wait loop, pass `refresh_delay_s` or call `allsolve.refresh_statuses()`. See [simulation](references/simulation.md#job-polling).
- **Validate new output expressions on one simulation before a batch.** A simulation that fails to start gives only a warning at once; the `JobError` comes when the batch ends. See [simulation](references/simulation.md#run-pattern).
- **A failed sweep step: read the child-job log.** The sweep ends `PARTIAL_SUCCESS`. See [simulation](references/simulation.md#logs-and-debugging).
- **Geometry `add_*` methods are not idempotent.** Each run adds the parts again. See [geometry](references/geometry.md#gotchas).

## Model verification checklist

After you build the model and before you launch large sweeps, check each layer:

1. **Geometry**: `build(print_logs=True)` succeeds. Open the project in the browser (`client.get_url(project)`) and check the shape.
2. **Regions**: print `region.entity_tags` for every region used by materials, physics or mesh refinements. Each list must be non-empty. Zero tags means a wrong selector.
3. **Materials**: every physics domain volume has exactly one material. Check the browser "Materials" tab for gaps.
4. **Mesh**: run with `on_error=OnError.STRICT`. Print `mesh.get_metrics()` for node, element and low-quality element counts (for a geometry sweep: `inst = mesh.get_override(sweep)`, then `inst.get_metrics(sweep_index=i)` for `i in range(inst.get_sweep_count())`; the index counts distinct meshes, not sweep points). For a new 3D problem, a coarse first mesh (a larger `mesh_size_max`) on a small node is fine.
5. **Simulation**: run one point (no sweep) and check that the outputs are physically plausible (units, order of magnitude). Only then launch the full sweep.

## Anti-patterns

### Project lifecycle

- **While you iterate:** calling `create_project()` on every script run. Reuse the same project with `get_current_project()` / `set_current_project()`, reset its contents in place when the setup is wrong, or delete failed projects explicitly. A new project on each run leaves half-built projects on the server.
- **Once mesh or simulation results exist:** resetting the project, rebuilding from scratch, or re-running mesh or simulation without the user's confirmation. Re-running loses the existing results. Load the current project and change only what changed. Ask before you start over.

### General

- Ignoring `mesh.get_status()` / `sim.get_status()` before you continue.
- Using `project.add_physics()` or `physics=[...]` on simulation creation. Both are deprecated. Use `PhysicsSet.add_physics()` and `physics_set=`.

## Version notes (SDK 0.5.3)

- Deprecated since 0.5.0: `project.add_physics()` and `physics=` on simulations → use `PhysicsSet`.
- New in 0.5.3: `run_simulations`/`run_meshes`, `include_overrides=True`, `MeshSettings(extrusions=[...])`, `save_output_fields`, `refresh_statuses`, `Runtime(main_node_type=...)`.
- Changed in 0.5.3 (breaking): getters return the saved state until `save()`; `get_url()` raises `TypeError` for an argument that is not a `Project`; `SimulationOutputData` raises `ValueError` for a sweep index out of range and `KeyError` for an unknown value header; setting a different `physics_set` enables all physics of the new set; `Client` methods raise `RuntimeError` when the client is not the active one; internal modules (`intcomp`, `varint`, `token` and others) are private.
- Changed in 0.5.3: `print_new_loglines()` prints all new lines by default; `is_running()` returns `False` before the simulation is started.
