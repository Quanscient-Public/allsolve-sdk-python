# Changelog

All notable changes to the Allsolve SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- **Compute resource reservations** — reserve cloud compute ahead of geometry, mesh, and simulation jobs to avoid repeated queue waits. New `ResourceReservation` class, `ReservationStatus` enum, `Client.resource_reservation()`. Geometry, mesh, and simulation `run()` / `start()` accept a `resource_reservation=` argument. See resource reservation examples (`example/resource_reservation/`).
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
