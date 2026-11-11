# Changelog

All notable changes to the Allsolve SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.3] - 2026-11-10

### Added

- **Main node type** — `Runtime(main_node_type=...)` and `Simulation.main_node_type` set the compute size of the main (coordinator) node. When it is omitted, the main node uses `node_type`. `set_runtime()` raises `ValueError` if `node_count` is 1 and `main_node_type` differs from `node_type`. Project import/export supports `runtime.mainNodeType`.
- **Run many meshes or simulations at the same time** — `allsolve.run_meshes()` and `allsolve.run_simulations()` start all items, then get the status of all running items with one request for each project, and return when all of them are complete. With `OnError.RAISE` or `OnError.STRICT`, the `JobError` names each item that failed. If an item does not start, the others are still started and processed, and a `JobError` that names it is raised at the end, whatever `on_error` is. If no item starts, the first start error is raised at once. `run_meshes(include_overrides=True)` also processes the variable-override instances of each mesh.
- **`include_overrides` on `Mesh.run()` and `Mesh.start()`** — `include_overrides=True` also processes all variable-override instances of the mesh, at the same time as the default instance. If an instance fails to start, `start()` still starts the others and then raises a `JobError` that names it. The default `False` keeps the old behavior.
- **`allsolve.refresh_statuses()`** — refreshes the status of many simulations, meshes, mesh instances or jobs with one request for each project. Use it in your own polling loop, for example to write the logs of each simulation to a different file.
- **`Project.copy(on_error=...)`** — `OnError.RAISE` and `OnError.STRICT` raise `JobError` when the copy job fails. The default `OnError.IGNORE` keeps the old behavior.
- **Multi-valued overrides in `get_sweep_index()`** — a sweep variable with more than one value is found by its list of values.
- **`PhysicsInteraction` export** — the base class of all physics interactions (`allsolve.physics.interaction.Interaction`) is exported as `allsolve.PhysicsInteraction`, to pair with `OutputInteraction`. Use it in type hints for the values returned by `Physic.interactions` and `Physic.get_interactions()`. The `Interaction` namespace (`Interaction.SolidMechanicsLoad` and others) is unchanged.
- **Batch output field download** — `Simulation.save_output_fields()` saves many fields, sweep steps and steps in one call and returns the saved paths. It sends one URL request for each sweep step and downloads the files in parallel. When the files come from more than one sweep step, each sweep step gets a `sweep-NNNNN` subdirectory.
- **Multiple simple mesh extrusions** — `MeshSettings(extrusions=[...])` and the `Mesh.extrusions` property accept a list of `MeshExtrusion`. `MeshSettings(extrusion=...)` and `Mesh.extrusion` still work for a single extrusion. Project import/export supports the `simpleExtrusions` YAML list; the single `simpleExtrusion` key is still accepted on import.
- **Boundary current density interaction** — `ElectromagneticWavesBoundaryCurrentDensity` sets the time derivative dJb/dt of the tangential surface current density on a boundary (a vector, one value for each direction).
- **Acoustic extrapolation symmetry, patterning and attenuation** — `AcousticWavesAcousticExtrapolation` accepts the optional `acoustic_waves_acoustic_extrapolation_symmetry_x`, `_symmetry_y` and `_symmetry_z` (default `False`), `_patterning_pitch`, `_patterning_num_copies` and `_attenuation` parameters. The new parameters are at the end of the signature, so existing calls are not affected.
- **Solver precision** — `Simulation.solver_precision` gets and sets the solver precision, with the values `SolverPrecision.DOUBLE` (default), `QUADRUPLE` and `DOUBLE_INT32`. Changing other simulation settings keeps the precision.
- **Examples** — new CMUT single cell receive, PMUT send/receive, PMUT surrogate (Pareto front), PZT disc in water and RF patch antenna (build123d geometry) examples. `examples/README.md` now lists the examples by technique.
- **AI agent skills** — the new `plugins/allsolve/skills/` directory has Agent Skills for AI coding agents (Claude Code, Cursor, Codex): `allsolve-sdk` for setup, build order and the SDK building blocks, and domain skills for RF, structural, thermal and acoustic models. See `plugins/allsolve/skills/README.md`.

### Changed

- **Mesh extrusions sent as a list** — simple mesh extrusions are sent in the `meshExtrusions` API field instead of the deprecated `meshExtrusion`. Project export writes `simpleExtrusions` (a list) instead of `simpleExtrusion`.
- **Parallel output file download** — `save_output_field()`, `save_output_mesh()` and `save_output_files()` download the rank files in parallel (at most 8 at a time) instead of one after another.
- **Internal modules made private (breaking)** — `intcomp`, `varint`, `http_transfer`, `token`, `export_format` and `job_mixin` are now `_`-prefixed (for example `allsolve._token`). They were not public API; update any direct imports.
- **Getters return the saved state (breaking)** — before `save()`, all getters return the server state. Before, the `SharedExpression`, Project PML, `Physic` and `Simulation.physics_set_id` getters returned the pending change.
- **No retry for POST requests that can create duplicates** — create, copy and start requests are retried only on 429, 503 with `Retry-After` and connection errors. Requests that are safe to repeat (token, job status, download URLs, lease renew and release, abort) are retried as before.
- **Sweep index checks in output data (breaking)** — all `SimulationOutputData` methods accept a negative `sweep_index` (counted from the end) and raise `ValueError` for an index out of range. Before, some methods returned `{}`, raised `IndexError` or found no files.
- **`KeyError` for an unknown value header (breaking)** — `get_values_at()`, `get_value_at()` and `get_array_index_count_at()` raise `KeyError` for an unknown value header. Before, they returned `None` or 0, the same as for a known value with no data.
- **`Client` checks (breaking)** — methods that call the API raise `RuntimeError` when the client is not the active client. Pickling or copying a `Client` raises `TypeError`. `get_url()` raises `TypeError` for an argument that is not a `Project` (before, it returned a wrong link). Nested `with client:` blocks on the same client are allowed.
- **`physics_set` setter enables the physics (breaking)** — setting `Simulation.physics_set` also enables all physics of the new set, as the web app does. Set `physics` after it to enable only some of them. Setting the physics set that the simulation already has keeps `physics`.
- **Stricter input checks** — a CAD path segment of an unknown type raises `TypeError` (before, it was dropped and the path selected more entities). A mesh refinement on a point region or without an entity type raises `ValueError` (before, it was dropped). `Project.create_variables()` validates all entries before any API call.
- **Warning for `*` in CAD names** — a `cad_names` entry or a string segment in `cad_paths` that contains `*` gives a `UserWarning`. The server matches such a name exactly, so it selects nothing. Use `CadGlob.STAR` or `CadGlob.DOUBLESTAR` for wildcards.
- **`print_new_loglines()` prints all new lines** — `limit` is now the maximum number of new lines, and `None` (the new default) prints all of them. Before, one call printed at most one page of 100 lines, so `run(print_logs=True)` could return before the last lines were shown.
- **`Simulation.is_running()`** returns `False` before the simulation is started.
- **Select parameter values are readable** — for a select parameter (for example `currentFlowLumpActuationMode`), `InteractionParameter.value` returns the option ID, such as `currentFlowLumpActuationModeVoltage`. Before, it returned the character codes that the API stores, such as `[99, 117, ...]`. The setter and the `value` argument accept the option ID or the character codes. The values sent to the API do not change. The new generated `SELECT_PARAMETER_IDS` lists these parameters.
- **Faster requests** — override variables and mesh override set IDs are read with one request, `import_simulations` uses a cache, and mesh files are downloaded outside the API lock.

### Fixed

- **`ExpressionType` comparisons** — `expr.type == ExpressionType.FUNCTION` is now `True` for a function. Before, the comparison was `False` for every type. `ExpressionType` is now a `str` enum with the API values.
- **Mesh sweeps** — `Mesh.save()` works on a mesh with variable-override instances. Before, the server rejected each update.
- **Simulation status reason** — `Simulation.get_status_reason()` returns the reason of the last refreshed status. Before, it could return the reason from the time the simulation was started or loaded.
- **Geometry** — a `str` given to a `cad_names` setter is one name (before, each character was sent as a name). Changes to the setters of basic geometry and to `name` and `enabled` are saved.
- **Mesh** — refinements and extrusions can be cleared with `None` or `[]`. Setting `use_mesh_refiner` or `curved_mesh` keeps the mesh density. `print_new_loglines()` does not print the full log again after `refresh()`.
- **Physics and materials** — `name`, `namespace` and parameters work on interactions that are not added yet. A tuple matrix is sent as an anisotropic material property. The material abbreviation is kept when other changes are saved.
- **Simulation** — `save_generated_scripts()` also saves the main simulation script. `set_scripts()` and `set_runtime()` check the pending changes, not only the saved values.
- **Project import and export** — `enabled` values of outputs and CAD elements, JSON import files, variable dependencies and the layer groups of flatten-and-rebuild extrusions are kept correctly. A vector such as `[40, 50, 60]` is no longer exported as text, and an expression that starts with its parameter name is no longer imported as character codes.
- **Client and reservations** — an expired token is refreshed, API errors are raised when retries run out, and reservation leases are renewed after temporary errors.
- **Output data** — output data is downloaded again after the local cache is removed, a partial result file is deleted when its download fails, and CSV values are quoted when needed.
- **Path containment** — output download methods raise `ValueError` before they write a file outside `output_dir`, for example because of `..`, an absolute path or a symlink in a file name. Project import raises `ValueError` before it writes a `saveMesh` file outside the working directory, unless `allow_paths_outside_project=True`.
- **PMUT array example** — the piezo coupling rows are in the correct order and the drive is correct.

## [0.5.2] - 2026-10-01

### Added

- **CAD boolean tolerance** — `CadUnion`, `CadDifference`, `CadIntersection`, `CadFragments`, and `CadFragmentAll` accept an optional `boolean_tolerance` (`float | str | None`) for the Boolean operation algorithm. Project import/export supports the `booleanTolerance` YAML key on these geometry types.
- **Field-only output** — `FieldOnlyOutput` simulation output for writing a single field expression with optional skin-only, deformed-mesh, and step-filter settings. New `FieldOnlyOutputFilterType` enum.
- **Initial value interactions** — per-physics initial value interactions (e.g. `SolidMechanicsInitialValue`, `AcousticWavesInitialValue`, `ElectromagneticWavesInitialValue`, `HeatTransferInitialValue`, and related types for other physics domains).

### Changed

- **Acoustic radiation pattern** — `AcousticWavesRadiationPattern` no longer applies a SDK default for `acoustic_waves_radiation_pattern_num_points`; the parameter is now optional with no default.

### Fixed

- **Export path containment** — project export raises `ValueError` if API-returned names contain path traversal components (`..`, `/`, `\`, or similar).
- **Library material orientation** — `Material.create_from_library()` now keeps the library material's orientation.
- **2D rectangle rotation** — `CadRectangle` without a rotation now sends a zero rotation.

## [0.5.1] - 2026-08-19

### Added

- **Mesh metrics** — `Mesh.get_metrics()` and `MeshInstance.get_metrics()` fetch FEM node/element counts and optional per-type quality breakdown (`MeshMetrics`, `ElementCounts`). Raises `ApiException` with HTTP 404 when metrics are not yet available.
- **Mesh status reason** — `Mesh.get_status_reason()` and `MeshInstance.get_sweep_status_reason()` return the backend job status reason for the default or per-sweep mesh instance (e.g. `lowQualityData`).
- **Interaction enabled expressions** — physics interactions and simulation outputs accept `enabled` as a bool or expression string (`BooleanValue`).
- **Solid mechanics viscohyperelasticity** — `SolidMechanicsViscohyperelasticity` interaction.
- **Simulation script export** — project export now includes file-based simulation scripts in the `scripts` array. `export_yaml` / `export_json` write script files to a `sim/` directory beside the output file (via new `download_scripts` parameter, default `True` on file export). `Project.export(download_scripts=True)` enables the same for dict exports.
- **Shared files import/export** — project import/export now supports `sharedFiles` (project-level catalog) and per-simulation `sharedFiles` / `inputFiles` wiring, including cross-simulation output file and output database references. `export_yaml` / `export_json` accept `download_shared_files` (default `True`) to write shared file content when available; the API currently exposes upload metadata only, so binary file bytes cannot be downloaded from the cloud until a backend download endpoint is added.
- **VTK-HDF result files** — simulation result download automatically decompresses zstd-compressed `.hdf` files.

### Fixed

- **Material.create_from_library()** — includes elasticity matrices.

## [0.5.0] - 2026-07-03

### Added

- **Physics sets** — projects can define multiple named physics sets; simulations reference a set instead of a flat list of physics IDs. New types and methods: `PhysicsSet`, `Project.create_physics_set()`, `Project.get_default_physics_set()`, `Project.get_physics_sets()`, and `Simulation.physics_set`. Project import/export supports `physicsSets` and per-simulation `physicsSet` name references. Simulation factory methods (`create_simulation`, `create_simulation_static`, `create_simulation_harmonic`, `create_simulation_multiharmonic`, `create_simulation_transient`, `create_simulation_eigenmode`) accept `physics_set` (`PhysicsSet | str | None`) instead of a deprecated `physics` ID list.
- **Compute resource reservations** — reserve cloud compute ahead of geometry, mesh, and simulation jobs to avoid repeated queue waits. New `ResourceReservation` class, `ReservationStatus` enum, `Client.resource_reservation()`. Geometry, mesh, and simulation `run()` / `start()` accept a `resource_reservation=` argument. See resource reservation examples (`examples/resource_reservation/`).
- **Team support** — `get_teams()` lists teams available to the API user. `Project.create()` and `ResourceReservation.create()` accept an optional `team_id`; `Project.team_id` exposes the assigned team. Per-team quota is available from the organization quota endpoint.
- **Library shared expressions** — copy variables, functions, and interpolated functions from the organization library into a project. New `get_all_from_library()` and `create_from_library()` on `Variable`, `Function`, and `InterpolatedFunction`, plus `Project.create_variable_from_library()`, `create_function_from_library()`, and `create_interpolated_function_from_library()`.
- **Mesh sweep status** — `MeshInstance.get_sweep_status()` and `get_sweep_count()` for per-sweep-step mesh job status when using variable overrides.
- **Mesh size factors** — `MeshSettings` accepts `min_size_factor` and `max_size_factor` (mutually exclusive with `mesh_size_min` / `mesh_size_max`).
- **Batch job polling** — `Job.refresh_statuses()` refreshes status on multiple jobs in one API call.
- **Thread-safe client binding** — `Client.in_thread()` binds the SDK client per thread for safe use with `ThreadPoolExecutor`.
- **Simulation properties** — `Simulation.project_id` and `Simulation.variable_overrides_id`.
- **Material properties** — support for `longitudinalAttenuation`, `shearAttenuation`, and viscous damping variants (bulk/shear viscosity and attenuation-based).
- **Physics interaction** — `ElectromagneticWavesBoundaryAdmittance` replaces `ElectromagneticWavesBoundaryImpedance`.
- **Examples** — Added Twisted Superconductor AC Loss example, unified example READMEs, and project deletion in example scripts to free project quota.

### Changed

- Optimized `GeometryBuilder.add()` when passed multiple elements. A batch create API is used with parallel file uploads for imported geometry files.
- Minor optimization to `VariableOverrides.create()` when passed multiple variables.

### Deprecated

- `Project.add_physics()` — get the project's default physics set or create a physics set first, then call `physics_set.add_physics()`.
- `physics` parameter on simulation creation — use `physics_set` instead. Passing both raises `ValueError`.

### Removed

- Removed deprecated `Mesh.quality` / `MeshSettings.quality` — use `Mesh.density` / `MeshSettings.density` instead.

## [0.4.4] - 2026-05-15

Initial public release of the Quanscient Allsolve SDK.
