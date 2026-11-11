# Allsolve geometry

This reference covers the geometry builder: primitives, booleans, transforms, file imports, alignment and geometry build errors.

## Geometry builder

```python
builder = project.geometry_builder()

builder.add_box(name="part", position=(0, 0, 0), size=("L", "W", "H"))
builder.add_cylinder(
    name="rod",
    position=(0, 0, 0),
    axis=(0, 0, "H"),
    radius="R",
    inner_radius="R_inner",  # optional — hollow cylinder / shell
    alignment=allsolve.CadAlignment.BASE,
)
builder.add_difference(
    name="part_with_hole",
    cad_names_1=["part"],
    cad_names_2=["rod"],
    delete_tool=True,  # default: the tool body (rod) is removed; False keeps it as a separate body
)
builder.build(print_logs=True, on_error=allsolve.OnError.STRICT)
```

Use `OnError.STRICT` for geometry, mesh and simulation runs. For geometry, `RAISE` and `STRICT` are identical. See [simulation.md](simulation.md#run-pattern) for the full `on_error` guide.

## Methods by category

For the full method list, run `help(allsolve.GeometryBuilder)` or grep the installed package. Key methods:

| Category   | Methods                                                                                                                |
| ---------- | ---------------------------------------------------------------------------------------------------------------------- |
| Primitives | `add_box`, `add_cylinder`, `add_sphere`, `add_cone`, `add_torus`, `add_disk`, `add_rectangle`, `add_surface_rectangle` |
| Booleans   | `add_union`, `add_difference`, `add_intersection`, `add_fragments`, `add_fragment_all`                                 |
| Transforms | `add_translate`, `add_rotate`, `add_grid`, `add_remove`                                                                |
| Import     | `add_step_file`, `add_iges_file`, `add_brep_file`, `add_sat_file`, `add_msh_file`, `add_nas_file`, `add_gds2_file`     |

Shared helpers: `CadAlignment`, `CadPath`, `CadGlob`.

Import types: `CadStepFile`, `CadIgesFile`, `CadMshFile`, etc.

## Conditional geometry for sweeps

Use `enabled` to activate geometry parts only when a sweep variable matches:

```python
gb = project.geometry_builder()
for i, step_path in enumerate(step_files):
    gb.add_step_file(filepath=str(step_path), name=f"sample_{i}",
                     enabled=f"sample_idx == {i}")
gb.build(print_logs=True, on_error=allsolve.OnError.STRICT)
```

Combine with `create_variable_overrides` to sweep over different geometries (see [variables-and-overrides.md](variables-and-overrides.md)).

## Alignment

| Enum                  | Primitives        | Meaning                                              |
| --------------------- | ----------------- | ---------------------------------------------------- |
| `CadAlignment.CENTER` | Box, rectangle, cylinder, cone (default) | Bounding-box center at `position`                    |
| `CadAlignment.CORNER` | Box, rectangle    | Smallest XYZ corner at `position`                    |
| `CadAlignment.BASE`   | Cylinder, cone    | Bottom center at `position` (radial geometries)      |

Sphere, torus and disk take no `alignment`: `position` is their centre.

Resource reservations: see [simulation.md](simulation.md#resource-reservations).

## Gotchas

- **All geometry dimensions in SI (metres)**, except the `add_gds2_file` layer `absolute_z0`, `thickness` and `extrude_parameters` distances, which default to µm (`unit=`).
- **`alignment` defaults to `CadAlignment.CENTER`** — `position` is the bounding-box center, so box/rectangle span `[position - size/2, position + size/2]`. For `[0,W]×[0,H]`, use `position=(W/2, H/2)` or `alignment=CadAlignment.CORNER, position=(0, 0)` (smallest corner at `position`). Cylinder/cone: `CadAlignment.BASE` pins bottom center at `position`. Wrong alignment silently shifts the domain.
- **STEP export from scripted CAD (for example CadQuery):** use `lineTo`, not `spline`, so that adjacent layers share exact interface vertices after STEP export and fragmentation.
- **`geometry_no_implicit_fragment=True` breaks acoustic-elastic coupling** — coupling requires shared curves between domains. Only disable implicit fragmentation when no inter-domain coupling is needed.
- **`delete_tool=False` keeps the tool body.** That is how you cut a pocket and fill it with another material (`examples/pzt_disc_in_water`). Do not also add a second copy of the tool body.
- **Shared subshape names are lost during fragmentation.** A face or edge name shared by two solids does not survive. Select shared entities by bounding box instead. Unshared names survive.
- **Booleans that refer to earlier parts by `cad_names`:** check the entity counts after `build()`. Names may not survive every operation.
- **(EM/RF)** Model conductors as thin solids, not zero-thickness sheets: sheets produce sliver elements. The mesh then ends `PARTIAL_SUCCESS` with reason `lowQualityData`: `OnError.RAISE` lets it through, `STRICT` raises. Check `mesh.get_metrics()` for the low-quality count.
- **(EM/RF)** Axis-aligned via/feed boxes fused onto CURVED trace ends make sliver tets — give the trace a straight radial lead stub so the via/pad shares an aligned face.
- **Wildcards in geometry targets:** `cad_paths=[[allsolve.CadGlob.DOUBLESTAR, "part"]]` (any depth) or `[[allsolve.CadGlob.STAR]]` (one level), on `add_union`, `add_translate`, `add_rotate`, `add_grid` and `add_remove` (`cad_paths_1`/`cad_paths_2` on the booleans and `add_fragments`). A path segment is a name, a `(key, value)` tuple or a `CadGlob`. Pass the enum: a string `"*"` or `"block*"` matches nothing, without an error. `cad_names` and region-rule `attribute_path` match exact names only.
- **`add_*` methods are not idempotent:** each call creates a new element, so running the script again duplicates the parts. Clear with `project.geometry_builder().delete()` first, or check `gb.get_elements()`.

## Pitfalls

| Error                                    | Cause                             | Fix                                                                 |
| ---------------------------------------- | --------------------------------- | ------------------------------------------------------------------- |
| `PLC Error: segment and facet intersect` | Slivers or near-coincident faces (overlaps are fragmented automatically, unless the project was created with `geometry_no_implicit_fragment=True`) | Remove tiny gaps and near-coincident faces; set `boolean_tolerance` on a `Cad*` boolean element (`gb.add(allsolve.CadDifference(..., boolean_tolerance=...))`; the `add_*` helpers don't take it) |
| Thin feature mesh OOM                    | Mesh refined below real thickness | Raise the node type, then `mesh_size_max`; avoid sub-mm refinement unless required |
| `no elements in volume`                  | Bad geometry after boolean        | Rebuild; check `build(print_logs=True)`                             |
