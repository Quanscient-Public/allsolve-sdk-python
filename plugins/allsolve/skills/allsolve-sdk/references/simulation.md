# Allsolve simulation

**Contents:** [Simulation types](#simulation-types) · [Common kwargs](#common-kwargs) · [Type-specific examples](#type-specific-examples) · [Resource reservations](#resource-reservations) · [Run pattern](#run-pattern) · [Job statuses](#job-statuses) · [Logs and debugging](#logs-and-debugging) · [Outputs](#outputs) · [Chaining simulations](#chaining-simulations) · [Sweeps and parallel runs](#sweeps-and-parallel-runs) · [Simulation properties](#simulation-properties) · [Gotchas](#gotchas)

This reference covers simulation types, the run pattern and error handling, job status, outputs and result files, chaining simulations, sweeps and parallel runs, and resource reservations. Node sizing is in [mesh.md](mesh.md#instance-size-node-type).

## Simulation types

All helpers are on `project`. Each maps to an `AnalysisType`.

| Method | Analysis type | Typical use |
| ------ | ------------- | ----------- |
| `create_simulation_static` | Steady-state | Equilibrium solutions (thermal, structural, EM, …) |
| `create_simulation_harmonic` | Harmonic | Single-frequency AC / frequency-domain |
| `create_simulation_multiharmonic` | Multiharmonic | Multiple harmonics in one solve |
| `create_simulation_transient` | Transient | Time-dependent (heating, dynamics over time) |
| `create_simulation_eigenmode` | Eigenmode | Natural frequencies / modes |

Low-level escape hatch: `create_simulation(...)` with an explicit `analysis_type`.

## Common kwargs

- `name`, `description`, `max_run_time_minutes`: required on all helpers
- `mesh`: `Mesh` object or mesh ID string
- `solver_mode=allsolve.SolverMode.DIRECT`, or iterative with `solver_tolerance`
- Solver precision is a property, not a kwarg: `sim.solver_precision = allsolve.SolverPrecision.QUADRUPLE`, then `sim.save()`. Values: `DOUBLE` (default), `QUADRUPLE`, `DOUBLE_INT32`.
- `physics_set`: `PhysicsSet` object or ID string (replaces the deprecated `physics=[id, ...]`)
- `variable_overrides`: for parametric sweeps (see [variables-and-overrides.md](variables-and-overrides.md))

## Type-specific examples

**Transient:**

```python
sim = project.create_simulation_transient(
    name="Thermal transient",
    description="...",
    max_run_time_minutes=30,
    solver_mode=allsolve.SolverMode.DIRECT,
    mesh=mesh.id,
    physics_set=physics_set,
    timestep_algorithm=allsolve.TimestepAlgorithm.IMPLICIT_EULER,  # or GEN_ALPHA; SolidMechanics/ElasticWaves need GEN_ALPHA
    transient_start_time="0",
    transient_end_time="3600",
    transient_timestep_size="30",
)
```

Use project variables for end time and timestep when you sweep them: `transient_end_time="sim_end_time"`.

**Harmonic:**

```python
sim = project.create_simulation_harmonic(
    name="Harmonic",
    description="...",
    max_run_time_minutes=30,
    mesh=mesh.id,
    physics_set=physics_set,
    fundamental_frequency="1e6",
)
```

**Multiharmonic:** as harmonic, plus `harmonics=[...]`. Indices: 1 = DC, 2/3 = sin/cos of the fundamental, 4/5 = sin/cos at 2f, and so on. `sn(2)` in a load is the sin at 2f (index 4); `cn(2)` is index 5.

**Eigenmode:**

```python
sim = project.create_simulation_eigenmode(
    name="Modal analysis",
    description="...",
    max_run_time_minutes=30,
    mesh=mesh.id,
    physics_set=physics_set,
    num_requested_eigenmodes="10",
    target_eigenfrequency="1e6",
)
```

## Resource reservations

You can reserve cloud compute ahead of time to avoid repeated queue waits across geometry, mesh and simulation jobs:

```python
with client.resource_reservation(node_type=allsolve.CPU.CORES_4_64GB) as reservation:
    mesh.run(print_logs=True, on_error=allsolve.OnError.STRICT, resource_reservation=reservation)
    sim.run(print_logs=True, on_error=allsolve.OnError.STRICT, resource_reservation=reservation)
```

`resource_reservation=` is accepted by geometry `build()`/`run()`, mesh `run()`/`start()`, and simulation `run()`/`start()`. All reserved replicas count against the quota for the whole lease. See `examples/resource_reservation/` for sweeps with reservations. With `start()` instead of `run()`, keep the lease alive while you poll: `with allsolve.resource_reservation.keep_reservation_alive(reservation): ...`.

## Run pattern

Always mesh before you simulate. Pick one error-handling style:

| `on_error` | Behavior |
|------------|----------|
| `IGNORE` (default) | Never raises. Check `get_status()` yourself |
| `RAISE` | Tolerates non-fatal outcomes, which depend on the job: simulation `PARTIAL_SUCCESS` and `ABORTED`; mesh `PARTIAL_SUCCESS`; geometry nothing (same as `STRICT`) |
| `STRICT` | Raises `JobError` unless the status is exactly `SUCCESS` |

**Recommended: strict success.**

```python
def run_mesh_and_simulation(mesh, sim, verbose=True):
    mesh.run(print_logs=verbose, on_error=allsolve.OnError.STRICT)
    sim.run(print_logs=verbose, on_error=allsolve.OnError.STRICT)
```

With the default `IGNORE`, check `get_status() == allsolve.Job.SUCCESS` after each `run()` and stop otherwise. Do not combine `OnError.RAISE` with a manual status check unless you want two layers. For most scripts, use `STRICT`.

**Non-blocking run.** Always pass `refresh_delay_s` to `is_running()`:

```python
sim.start()
while sim.is_running(refresh_delay_s=5):
    sim.print_new_loglines()
sim.print_new_loglines()
print("Status:", sim.get_status())
```

**Several simulations at the same time**: `allsolve.run_simulations()` starts all of them, polls them with one request for each project, and returns when all are complete. With `RAISE` or `STRICT`, one `JobError` names each simulation that failed. If a simulation fails to start, there is a warning at once, the others still run, and at the end a `JobError` names the simulation that did not start, also with `OnError.IGNORE`. Nothing is aborted. If no simulation starts, the first start error is raised at once. `allsolve.run_meshes()` does the same for meshes.

```python
allsolve.run_meshes([mesh_a, mesh_b], on_error=allsolve.OnError.STRICT)
allsolve.run_simulations([sim_a, sim_b, sim_c], print_status=True, on_error=allsolve.OnError.STRICT)
```

For your own polling loop, for example to write the log of each simulation to a different file, use `allsolve.refresh_statuses()`. It refreshes all items with one request:

```python
for s in sims:
    s.start()
while any(s.is_running() for s in sims):
    allsolve.refresh_statuses(sims, delay_s=5)
    for s in sims:
        s.print_new_loglines(file=log_files[s.name])
```

Do not poll many simulations with `is_running(refresh_delay_s=5)` in a loop: each call waits 5 s, so one pass over N simulations takes about 5·N s.

## Job statuses

- With `on_error=allsolve.OnError.IGNORE` (default), check `.get_status()` after `run()`. Continue only on `allsolve.Job.SUCCESS`.
- With `on_error=allsolve.OnError.STRICT`, `run()` raises `JobError` on any non-`SUCCESS` status. No separate check is needed.
- With `on_error=allsolve.OnError.RAISE`, hard failures raise `JobError`. Which other statuses return normally depends on the job type (see the table in [Run pattern](#run-pattern)).
- For a failed mesh sweep step, get the `MeshInstance` with `mesh.get_override(...)`, then call `instance.get_sweep_status(sweep_index=i)` and `instance.get_sweep_status_reason(sweep_index=i)`. For a simulation sweep, there is no status for each step: use `sim.get_status_reason()` and the logs of the simulation job. For a failed sweep step, see [Logs and debugging](#logs-and-debugging).

On failure, read the last log lines before you retry. Do not re-run blindly with the same settings.

## Logs and debugging

- `mesh.run(print_logs=True)` / `sim.run(print_logs=True)` stream the cloud job logs.
- Transient logs show `@30s`, `@60s`, … progress markers.
- Errors in custom simulation scripts (for example `NameError`) appear only in the cloud job logs. See [simulation-scripts.md](simulation-scripts.md).
- **A sweep step failed with only "error in child job #N"?** The parent log does not include the solver error. Read the step's own job log (the last 300 lines):

  ```python
  data = sim.get_output_data(refresh=True)
  job_id = data.get_simulation_job_id(sweep_index=N)
  print("\n".join(allsolve.Job(project.id, job_id).get_logs(limit=25000)[-300:]))
  ```

  A sweep with failed steps ends `PARTIAL_SUCCESS`, which `OnError.RAISE` lets through; use `STRICT` to make it raise.

## Outputs

```python
sim.add_outputs([
    allsolve.Output.FieldOutput(name="Temperature", expression="T"),
    allsolve.Output.ValueOutput(name="Max stress", expression="maxvalue(reg.part, vonmises(sigma), 1)"),
])
```

- **Region maximum/minimum: `maxvalue(reg, expr, n)` / `minvalue(reg, expr, n)`.** `max(a, b)` and `min(a, b)` compare two expressions point by point; `max(reg, expr, n)` fails only when the simulation starts.

For the full output type list, run `dir(allsolve.Output)` or read `allsolve/physics/generated/outputs.py` in the installed package. Common types:

| Type | Use |
|------|-----|
| `Output.FieldOutput` | Spatial field. Downloads as VTKHDF `.hdf` files, one file per rank |
| `Output.ValueOutput` | Scalar or vector value per step |
| `Output.FieldState` | Final field state, used to initialize a later simulation (see [Chaining simulations](#chaining-simulations)) |
| `Output.TransientState` | Transient state, used to continue a transient in a later simulation |
| `Output.Eigenfrequencies` | Natural frequencies (eigenmode) |
| `Output.Eigenvalues` | Eigenvalues (eigenmode) |
| `Output.SParameters` | S-parameters (EM) |

After a successful run:

```python
data = sim.get_output_data()          # refresh=True by default
csv_text = data.to_csv(csv_format=allsolve.CsvExportFormat.NORMAL)
data.to_csv_file("results.csv")
data.clean_cache()                    # free the local cache when done
```

CSV notes:
- The SDK CSV names the time (or frequency) column **`Step`**.
- **Transient value outputs start at the first time step, not at t = 0.** The outputs are evaluated after each solved step, so the CSV has no row for the initial state. If a plot needs the start point, add it from the known initial value.
- **`Sweep step`** appears for parametric sweeps.
- Match output names exactly when you parse (for example `"Average temperature (part)"`).
- **`to_csv_file()` does not overwrite** existing files. Delete or rename the target file first, or use unique file names.

**Field output files.** `save_output_field` and `save_output_fields` write VTKHDF files (`.hdf`), one file per rank. `output_dir` must exist. Read them with pyvista (`pip install pyvista`; ask the user first) or ParaView. Do not use a `.vtu` reader.

```python
import pyvista as pv

paths = sim.save_output_fields(["u"], output_dir="results", step_indices=[-1])  # FieldOutput names; an unknown name raises ValueError listing the available ones
parts = [pv.read(p) for p in paths]  # one mesh per rank file
```

`save_output_fields` downloads many fields, steps and sweep steps in one call, and puts each sweep step in its own `sweep-NNNNN` subfolder. For one field: `sim.save_output_field(name="Temperature", output_dir="./results", sweep_index=0)`.

## Chaining simulations

Use the result of one simulation as the start of another, for example a static bias solve that feeds a transient. Docs: Inputs & outputs → Chaining (`/documentation/using-allsolve/simulations/inputs-and-outputs#chaining`).

1. In the source simulation, add an `Output.FieldState` for each field to pass on. The default filter (`FieldStateFilterType.FINAL_ONLY`) stores the final state.
2. Run the source simulation.
3. In the target simulation, call `set_field_initializations` with one `FieldInitialization` per field. The call replaces all existing initializations.

```python
static = project.create_simulation_static(..., physics_set=physics_set)
static.add_outputs([
    allsolve.Output.FieldState(name="u", field_state="u"),
    allsolve.Output.FieldState(name="v", field_state="v"),
])
static.run(print_logs=True, on_error=allsolve.OnError.STRICT)

transient = project.create_simulation_transient(..., physics_set=physics_set)
transient.set_field_initializations([
    allsolve.FieldInitialization(
        type=allsolve.FieldInitializationType.FIELDSTATE,
        source_simulation=static,
        source_output_name="u",
        field=solid.fields.displacement,  # or solid.fields[0]
    ),
    allsolve.FieldInitialization(
        type=allsolve.FieldInitializationType.FIELDSTATE,
        source_simulation=static,
        source_output_name="v",
        field=electrostatics.fields.electricPotential,
    ),
])
```

`physic.fields` supports attribute access by definition name, dict access and indexing. Print `[f.definition for f in physic.fields]` to see the names.

| `FieldInitializationType` | What it does |
|---|---|
| `FIELDSTATE` | Loads a field from a `FieldState` output and uses it as the initial value. The simulation then solves normally. |
| `TRANSIENTSTATE` | Continues a transient simulation from a stored `TransientState` output. `field` may be `None`. |
| `HPHISTATE` | Initializes the H and phi fields from a stored H-phi state. `field` may be `None`. |
| `POSTPROCESSING` (experimental) | Nothing is solved. For each stored step of the source, the fields are loaded and the outputs of this simulation are evaluated. Outputs that need a solve (for example eigenvalues) are not supported. |

Optional `FieldInitialization` arguments:
- `source_output_specifier`: for a field stored in parts. An eigenmode field has a real and an imaginary part, so it needs two initializations, one with `"real"` and one with `"imaginary"`.
- `source_sweep_step`: take the state from this sweep step of a sweep source.
- `source_step`: take the state from this step (time step, eigenvalue index, …).
- `harmonic`: initialize only this harmonic of the field.

Example: `examples/lumped_pull_in_analysis/lumped_pull_in_analysis.py` chains a static solve into a second static solve with `FIELDSTATE` for `u`, `v` and `umesh`.

Use `FIELDSTATE` when the second simulation must solve from the stored state, for example a transient that starts from a static bias (`examples/cmut`). Use `POSTPROCESSING` only to evaluate new outputs on stored results without solving again.

The source simulation needs one `Output.FieldState(name=..., field_state="u")` for each field to pass on. `source_output_name` is that output's name, and `field` is the matching field of the target physics.

## Sweeps and parallel runs

- **A sweep starts all its points in parallel.** Run one point first and check the result. Then run the sweep.
- **Cap the parallelism** with a reservation: `client.resource_reservation(node_type=..., num_replicas=N)` runs at most N sweep points at the same time. Your organization also has a maximum parallelism.
- **Scale `max_run_time_minutes` with the number of points** when they cannot all run at the same time.
- Sweep result extraction: see [variables-and-overrides.md](variables-and-overrides.md#extracting-per-sweep-point-results).

## Simulation properties

- `sim.project_id`: project this simulation belongs to.
- `sim.variable_overrides_id`: ID of the variable overrides set, or `None`.
- `sim.physics_set`: `PhysicsSet` object, or `None`. Setting it also enables all physics of the new set, so set `sim.physics` after it, not before. Setting the set that the simulation already has keeps `physics`.

Custom simulation scripts (`set_scripts`, solver namespaces, stubs): see [simulation-scripts.md](simulation-scripts.md). They are rarely needed.

## Gotchas

### Timestep and solver

- **The enum is `TimestepAlgorithm.GEN_ALPHA`** (and `IMPLICIT_EULER`). There are no `GENALPHA` or `IMPLICITEULER` names: they raise `AttributeError`. `repr()` shows the API names (for example `<TimestepAlgorithm.GENALPHA: 'genAlpha'>`), but use the SDK names in code.
- **Solid Mechanics and Elastic Waves need `GEN_ALPHA`.** `IMPLICIT_EULER` does not apply to these physics.
- **`genalpha` is implicit.** CFL stability limits do not apply. Choose `dt` for temporal accuracy (about 20 points per period).
- **Node sizing:** start with the smallest node type and count, and scale up when the run is too slow or runs out of memory. For multi-node runs the docs suggest about 50–100k DOF per 16 GB node. For eigenmode analysis the docs recommend DIRECT on several 1-core / 16 GB nodes. If a multi-node DIRECT run fails, try ITERATIVE.
- **Large runs need a bigger main node.** Rank 0 needs much more memory than the workers. If the run dies right after `Time to partition the mesh ...` with no `Generalized alpha run for N dofs` line, set `allsolve.Runtime(node_count=N, node_type=..., main_node_type=allsolve.CPU.CORES_8_128GB)`, or pass `main_node_type` to `client.resource_reservation()`.

### Job polling

- **`is_running()` without `refresh_delay_s` returns the cached status and never turns `False`.** A loop on it hangs. Always pass `refresh_delay_s`, or call `allsolve.refresh_statuses()` in the loop.
- **`is_running()` returns `False` before the simulation is started.** Call `start()` first.

### Output extraction

- **`get_output_values()` returns a dict of all steps**, keyed by step label (for example time values for transient simulations). For structured access, use `sim.get_output_data(refresh=True)` and `get_value_at(sweep_index, step_index, value_header)`. See [variables-and-overrides.md](variables-and-overrides.md#extracting-per-sweep-point-results).
- **`to_dataframe()` / `sweep_step_to_dataframe(si)`** give a pandas view of `SimulationOutputData`, as an alternative to `get_value_at` loops. One row per array element; columns `Sweep step`, `Step`, `Array index`, overrides and value outputs. Needs `pip install allsolve[dataframe]`.
- **`save_output_field` `step_index` defaults to `None`.** That is fine for static and harmonic simulations. For transient simulations, pass `step_index=N` (or `-1` for the last step). Pass `refresh=True` on the first call.
- **Harmonic field downloads** are named like `<name>_nostep_0.hdf`, the same name for each sweep step. With `save_output_field`, use a separate `output_dir` per sweep step, or use `save_output_fields`. For `norm(field)` versus `norm(harm(2, E))`, see [the RF domain skill](../../allsolve-domain-rf/SKILL.md#gotchas).
- **Harmonic simulations: value outputs must reduce to one harmonic.** `average(reg.x, p, 3)` fails with "cannot integrate a multiharmonic expression". Use `average(reg.x, harm(2, p), 3)` for one component, or `harmonicnorm([2, 3], p)` for the amplitude.
- **`Output.FieldOutput(..., target=region)` restricts the export to a region.** Use it for per-part renders.

### Robust result extraction

- **Static** results live at `NO_STEP`.
- **Eigenmode** results: one value per step (one frequency per mode). There can be more modes than requested, and they are not guaranteed to be sorted.
- **A fully failed sweep** has no steps, so `get_step_index(NO_STEP)` raises `Step label nostep not found`.
- **FFT and impedance post-processing:** see also [postprocessing.md](postprocessing.md) for windowing, zero-padding and division-by-zero guards.
