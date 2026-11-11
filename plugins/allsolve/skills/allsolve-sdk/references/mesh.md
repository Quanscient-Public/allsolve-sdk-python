# Allsolve mesh

**Contents:** [Mesh creation](#mesh-creation) · [Instance size (node type)](#instance-size-node-type) · [Running the mesh](#running-the-mesh) · [Mesh status and metrics](#mesh-status-and-metrics) · [Failure guide](#failure-guide) · [Gotchas](#gotchas)

This reference covers mesh creation and tuning (`MeshSettings`, refinements, scale factor), mesh metrics, failure recovery, and node sizing for mesh and simulation jobs. It is the one home for node sizing; other files link here.

## Mesh creation

```python
mesh = project.create_mesh(
    allsolve.MeshSettings(
        name="Default mesh",
        scale_factor=1.0,           # >1 = coarser, <1 = finer globally
        curvature_enhancement=4.0,
        max_run_time_minutes=15,
        refinements=[
            allsolve.MeshRefinement(
                region=regions.fine_feature,
                max_size="feature_height / 10",
            ),
        ],
    )
)
```

`scale_factor` is the main knob for mesh density. It is applied after all other sizing, but `mesh_size_max` and refinement `max_size` are always respected, and it does not affect structured (extruded or transfinite) meshes. Values well above 1 may fail to coarsen.

**Start coarse, refine later.** For a new 3D problem, start with a larger `mesh_size_max` or `MeshSettings(density=allsolve.MeshDensity.COARSE)`. These are alternatives: `density=COARSE` is ignored when any size parameter is set (`scale_factor`, `curvature_enhancement`, `mesh_size_*` and `*_size_factor` override the preset). Check that the simulation runs to completion before you make the mesh finer. This avoids OOM failures while you set up the model.

For direct size control instead of relative scaling, use `mesh_size_min` and `mesh_size_max`:

```python
allsolve.MeshSettings(
    name="Sized mesh",
    mesh_size_min=0.000002,
    mesh_size_max=0.004,
    max_run_time_minutes=10,
    refinements=[
        allsolve.MeshRefinement(region=regions.small_part, max_size=0.0002),
    ],
)
```

As an alternative, `min_size_factor` / `max_size_factor` give factor-based size control. They cannot be used together with `mesh_size_min` / `mesh_size_max`.

Refine **bulk domains** (fluid, large solids), not ultra-thin shells, unless the study requires it.

Structured meshes through layers: `MeshSettings(extrusions=[allsolve.MeshExtrusion(...)])` (a list; `extrusion=` takes one). Full example: `examples/combdrive_eigenmodes/combdrive_eigenmodes.py`.

- **`MeshExtrusion` needs its regions listed.** With `regions=None` or `[]`, the mesh job can fail with only "Job failed" in the log.

## Instance size (node type)

Mesh and simulation jobs run on cloud nodes with fixed RAM. Mesh and simulation node types are set independently.

Node types (`allsolve.CPU`). For the current list, run `list(allsolve.CPU)` (it includes `CPU.DEFAULT`).

| Node type                 | Cores | RAM             |
| ------------------------- | ----- | --------------- |
| `CORES_3_10GB_FAST_START` | 3     | 10 GB |
| `CORES_1_16GB`            | 1     | 16 GB           |
| `CORES_2_32GB`            | 2     | 32 GB           |
| `CORES_4_64GB`            | 4     | 64 GB           |
| `CORES_8_128GB`           | 8     | 128 GB          |
| `CORES_16_256GB`          | 16    | 256 GB          |
| `CORES_32_512GB`          | 32    | 512 GB          |

Sizing rules:

- **Start with the smallest node that fits in memory.** Smaller nodes start faster, cost less, and let more jobs run at the same time.
- **On OOM, increase the node type before you coarsen the mesh.**
- **Large nodes use up the organization quota fast** (`CORES_8_128GB` = 8 vCPU). Start with the smallest node; for multi-node runs the docs suggest about 50–100k DOF per 16 GB node.
- **`CORES_3_10GB_FAST_START`** (`"lambda"`) starts fastest and suits light meshes and tiny simulations. Limits: 1 node and at most 15 minutes of run time. `Simulation.set_runtime` raises `ValueError` above these limits.
- **Big assemblies or fine geometries can OOM a small mesh node.** Use `CORES_4_64GB` or larger to mesh them.

Mesh node, at creation or on the mesh object:

```python
mesh = project.create_mesh(
    allsolve.MeshSettings(
        name="Default mesh",
        node_type=allsolve.CPU.CORES_4_64GB.value,
        scale_factor=1.0,
        max_run_time_minutes=15,
    )
)

# Or after creation:
mesh.node_type = allsolve.CPU.CORES_4_64GB.value
mesh.save()
```

Simulation node (OOM during the solve):

```python
sim.set_runtime(allsolve.Runtime(node_type=allsolve.CPU.CORES_4_64GB))
sim.save()
```

Multi-node runs (`Runtime(node_count=N)`), a larger main node (`main_node_type`) and reservations: see [simulation.md](simulation.md#timestep-and-solver).

## Running the mesh

```python
mesh.run(print_logs=True, on_error=allsolve.OnError.STRICT)
```

Always mesh before you simulate. `include_overrides=True` also processes the variable-override instances of the mesh. To process many meshes at the same time, use `allsolve.run_meshes()`. See [simulation.md](simulation.md#run-pattern) for the run pattern and the `on_error` modes.

## Mesh status and metrics

Check the mesh job status after the run:

```python
mesh.get_status()          # Job.SUCCESS, Job.PARTIAL_SUCCESS, etc.
mesh.get_status_reason()   # reason on failure
print(mesh.get_metrics())  # node and element counts, low-quality counts per element type
```

`mesh.get_metrics()` returns a `MeshMetrics` with `nodes`, `elements` and `element_counts` (each with `type`, `total` and `low_quality`).

For variable-override sweeps, use `MeshInstance`:

```python
instance = mesh.get_override(variable_overrides)
instance.get_sweep_status(sweep_index=0)   # per-step job status
instance.get_sweep_count()                 # number of sweep steps
instance.get_metrics(sweep_index=0)        # metrics of one sweep step
```

Resource reservations: see [simulation.md](simulation.md#resource-reservations).

## Failure guide

| Symptom                                                | Likely cause                 | Action                                                                                               |
| ------------------------------------------------------ | ---------------------------- | ---------------------------------------------------------------------------------------------------- |
| `ran out of memory` / refiner killed                   | Mesh too large for node RAM  | **First:** increase the node type. **Then:** raise `mesh_size_max`; remove aggressive `MeshRefinement` |
| `PARTIAL_SUCCESS` / status reason `lowQualityData`     | Low-quality elements in mesh | This is a warning: `RAISE` lets it through, `STRICT` raises. About 10% low-quality elements still ends `PARTIAL_SUCCESS`, so check `mesh.get_metrics()` for the counts. Fix slivers in the geometry, try `use_mesh_refiner=True`, or relax refinements. The fail tolerance is a GUI setting, not available in the SDK |
| `PLC Error: segment and facet intersect`               | Invalid/overlapping geometry | Fix geometry (see [geometry.md](geometry.md#pitfalls))                                               |
| `no elements in volume`                                | Bad geometry after boolean   | Rebuild; check `build(print_logs=True)`                                                              |
| `Invalid regions in mesh parameters: zero entity tags` | Region rule matches nothing  | Fix region selectors before meshing (see [regions.md](regions.md))                                   |

## Gotchas

### Sizing

- **Two independent knobs control DOF:** (1) `mesh_size_max` for the global element size (keep it coarse); (2) `MeshRefinement(region=..., max_size=...)` for small features. Over-refining a swept region makes DOF explode on the thick variants.
- For targeted sizing, use `MeshRefinement(region=..., max_size=...)` (keyword-only; not on POINT regions) with a coarse global `mesh_size_max`.
- **A fine global size to resolve a thin feature makes large bodies explode.** Keep the global size coarse and refine only the small features.
- **Starting point for thin features: element ≈ thickness / 2.5.** This gives at least 2 quadratic elements through the feature. For slender bending, an element up to the thickness gave about 1% difference from beam theory with the default quadratic elements. Bulk or stiff bodies ≈ body size / 7.
- **(Wave physics)** Rule of thumb: global mesh size ≈ `min_wavelength / 6`. See the [RF](../../allsolve-domain-rf/SKILL.md#mesh-strategy) and [acoustics](../../allsolve-domain-acoustics/SKILL.md#mesh-sizing-for-wave-problems) domain skills.
- **Precedence for wave physics:** wavelength / 6 comes before thin-feature refinement. Do not refine thin geometric features unless their thickness matters acoustically or electromagnetically. Over-refining thin layers costs DOF and does not improve accuracy.
- **(Wave physics)** `use_mesh_refiner=True` can over-resolve thin layers. Compare DOF with and without it (the patch antenna and PMUT examples use it). `target_width_to_height_ratio` only has an effect with `use_mesh_refiner=True`. Wavelength, not geometric features, should drive the density.
- **Check the base-mesh DOF on one point before you launch a sweep of 100.** Use the coarsest refinement that still meshes the smallest geometry in the sweep.
- **The hard floor on coarseness** is that the smallest feature must mesh: an element must be smaller than the thinnest member. If the thin end fails, narrow the swept range instead of refining globally.

### DOF and solver scaling

- **2nd-order elements** give scalar DOF ≈ 6–7× the vertex count. A coupled thermal + structural solve ≈ 4× the scalar DOF.
- **DIRECT solver memory grows fast.** It caps at about 1M DOF on typical nodes (`CORES_4_64GB`). Larger nodes go further. For larger problems, use ITERATIVE DDM and/or more nodes with a bigger node type.
- **Coupled nonlinear problems can be ill-conditioned for ITERATIVE.** DIRECT on a large-memory node is often more robust up to a few M DOF.

### 2D and structured meshing

- **Default 2D meshing is unstructured triangles** (consistent mass). For structured quads, use `AutoTransfiniteGroup` in `MeshSettings(auto_transfinite=...)` or set transfinite counts explicitly. Opposite edges must get matching segment counts.
- **`import_msh` of gmsh quads is re-triangulated.** Do not call `create_mesh` after the import; use `project.get_meshes()[0]`.

### 2D axisymmetric

2D axisymmetric projects exist in the web app (project dimension "2D axisymmetric"), but the SDK cannot create them yet: `create_project(dimension=...)` takes only 1, 2 or 3. A web-app axisymmetric project reports `dimension` 3 through the SDK. Use a 3D model with symmetry planes instead (see [acoustics](../../allsolve-domain-acoustics/SKILL.md#symmetry-models)).

### Other

- **`mesh.save_mesh_file(output_dir, filename)` does not overwrite** existing files. Remove the old file first (`os.remove(path)`) or use unique file names.
