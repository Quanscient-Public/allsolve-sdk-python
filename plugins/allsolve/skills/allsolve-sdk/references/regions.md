# Allsolve regions

**Contents:** [Region types](#region-types) · [How rules select entities](#how-rules-select-entities) · [Recipes](#recipes) · [Basic usage](#basic-usage) · [Selection patterns](#selection-patterns) · [Mapping STEP product names](#mapping-step-product-names) · [Gotchas](#gotchas) · [Pitfalls](#pitfalls)

This reference covers region rules, computed regions and basic regions, which select the entities that materials, physics, interactions and mesh refinements target.

## Region types

| Method | Use when |
|--------|----------|
| `create_region_rule` | Select entities by bounding box, `min_size`, `max_size`, or `attribute_path` |
| `create_region_computed` | Boolean ops on regions: `UNION`, `DIFFERENCE`, `INTERSECTION`, `BOUNDARY`, … |
| `create_region_basic` | Explicit `entity_tags` from built geometry |

Entity types: `Region.VOLUME`, `Region.SURFACE`, `Region.CURVE`, `Region.POINT`.

`RegionOperation` for computed regions (from the SDK docstrings):

| Operation | Result |
|-----------|--------|
| `UNION` | Entities in any source region |
| `INTERSECTION` | Entities in all source regions. With a surface target, two volume regions give their shared faces |
| `DIFFERENCE` | Entities of the first source region that are in none of the others |
| `SYMMETRIC_DIFFERENCE` | Entities in an odd number of source regions |
| `BOUNDARY` | Outer boundary, one dimension lower. Faces shared by two source entities are left out, also across source regions |
| `COMPLEMENT` | All entities of the target dimension that are in no source region |

A source region of higher dimension than the target is first replaced by all its entities of the target dimension.

## How rules select entities

- **Bounding box: the entity must be fully inside.** Its own axis-aligned bounding box must lie inside the box on all three axes. Touching or overlapping is not enough.
- **Tolerance is relative.** The box grows by 0.1% of its extent on each side. An axis with zero extent (a flat box for a planar face) gets almost no tolerance (±5e-11). For flat faces, pad the box with a small tolerance variable, for example `("x0 - tol", ...), ("x0 + tol", ...)`.
- **`min_size` / `max_size`** compare the entity's bounding-box extents (x, y, z), each axis separately, inclusive, with 0.2% tolerance. All axes must pass. A `max_size` of 0 on an axis means "flat on that axis".
- Bounding box, `min_size` and `max_size` are combined with AND.
- **`attribute_path` that matches nothing does not filter** when the rule also has a bounding box or a size filter. You get every entity that passes the geometric filters. Check the entity count.

## Recipes

- **Interface between two parts:** `INTERSECTION` of `BOUNDARY(a)` and `BOUNDARY(b)`, or `INTERSECTION` of the two volume regions with `entity_type=Region.SURFACE`. Do not use `BOUNDARY` of the union: it leaves out the shared faces. Example: `examples/cmut`.
- **Symmetry faces:** one flat bounding-box rule per cut plane, padded by a tolerance variable, combined with `UNION`. If the rule also catches faces of a body that has no symmetry interaction, remove them with `DIFFERENCE`. Example: `examples/pzt_disc_in_water`.
- **Build regions from rules, check them with tags.** Do not hard-code `create_region_basic(entity_tags=...)`: tags change when the geometry is rebuilt or a sweep changes a dimension.
- **Check every region after you create it.** Rule regions are evaluated right away after `build()`, so `len(region.entity_tags)` is known before meshing. Assert the expected counts, as `examples/pzt_disc_in_water` does. After meshing, `mesh.get_metrics()` shows element counts per type.

### 2D vs 3D entity type mapping

| Concept | 2D simulation | 3D simulation |
|---------|---------------|---------------|
| Domain body | `Region.SURFACE` | `Region.VOLUME` |
| Boundary | `Region.CURVE` | `Region.SURFACE` |
| Point | `Region.POINT` | `Region.POINT` |

**2D projects** require `dimension=2` on `client.create_project()` (the default is 3; without it, all CURVE-based interactions are invalid). All region types shift down one dimension — use `Region.SURFACE` for domain bodies and `Region.CURVE` for boundaries. Bounding boxes still use 3D coordinates but z-extents should bracket the 2D plane (typically `z=0`).

## Basic usage

`bounding_box`, `min_size`, and `max_size` accept plain tuples or typed `ExpressionBoundingBox`/`ExpressionVector` objects:

```python
vol = project.create_region_rule(
    name="solid",
    entity_type=allsolve.Region.VOLUME,
    bounding_box=(
        ("-L/2", "-W/2", "-H/2"),
        ("L/2", "W/2", "H/2"),
    ),
    # Equivalent typed form:
    # bounding_box=allsolve.ExpressionBoundingBox(
    #     min=allsolve.ExpressionVector(x="-L/2", y="-W/2", z="-H/2"),
    #     max=allsolve.ExpressionVector(x="L/2", y="W/2", z="H/2"),
    # ),
)

surface = project.create_region_computed(
    name="outer_surface",
    entity_type=allsolve.Region.SURFACE,
    operation=allsolve.RegionOperation.BOUNDARY,
    source_regions=[vol.id],
)
```

## Selection patterns

**Bulk volume** — bounding box around expected extent:

```python
project.create_region_rule(
    name="large_part",
    entity_type=allsolve.Region.VOLUME,
    bounding_box=((min_x, min_y, min_z), (max_x, max_y, max_z)),
)
```

**Small feature among many** — add `max_size` to filter by characteristic length:

```python
project.create_region_rule(
    name="pins",
    entity_type=allsolve.Region.VOLUME,
    max_size=("pin_radius * 2", "pin_radius * 2", "pin_height"),
)
```

**Large domain only** — `min_size`:

```python
project.create_region_rule(
    name="air",
    entity_type=allsolve.Region.VOLUME,
    min_size=("box_size", "box_size", "box_size"),
)
```

**Thin shell / annulus** — `max_size` on wall thickness often yields **zero entity tags**. Instead use computed difference:

```python
outer = project.create_region_rule(name="outer_vol", ..., bounding_box=full_extent)
inner = project.create_region_rule(name="inner_vol", ..., max_size=inner_dims)
shell = project.create_region_computed(
    name="shell",
    entity_type=allsolve.Region.VOLUME,
    operation=allsolve.RegionOperation.DIFFERENCE,
    source_regions=[outer.id, inner.id],
)
```

**Convection / flux BC surfaces** — `BOUNDARY` on the solid region:

```python
project.create_region_computed(
    name="exposed_surfaces",
    entity_type=allsolve.Region.SURFACE,
    operation=allsolve.RegionOperation.BOUNDARY,
    source_regions=[solid_region.id],
)
```

Union multiple surface regions with `RegionOperation.UNION`.

**Name-based selection** — `attribute_path` selects entities by name tag instead of spatial filters:

```python
project.create_region_rule(
    name="track",
    entity_type=allsolve.Region.VOLUME,
    attribute_path=[("name", "track_part")],
)
```

For geometry-builder and STEP parts the key is `"name"`. Imported files can carry other keys (for example `LayerName`, `BC_ID`). Each (key, value) item matches exactly, with no wildcards: the last item selects a node, the earlier items must match its ancestors in order (the path need not start at the root), and the rule takes every entity of its type below the match. A path that matches something is combined with `bounding_box` by AND; a path that matches nothing is ignored (see above). Wildcards exist only in geometry-operation targets (see geometry.md).

## Mapping STEP product names

STEP files from OpenCASCADE do not have self-describing product names. **Never guess** which product name maps to which part — adjacent numbers (e.g. `2.2.12` vs `2.2.13`) can be completely different entities.

Use **build123d** (`pip install build123d`) to analyse the geometry locally: import the STEP file, then inspect each part's area, centroid position, bounding-box extent, and edge count to build a name mapping. Use the mapping as named constants, then pass `attribute_path=[("name", step_name)]` to `create_region_rule`.

Port/interaction target containment: if a bounding-box region picks up surfaces outside the physics domain, intersect it with the domain boundary. See [the RF domain skill](../../allsolve-domain-rf/SKILL.md#port-regions) for the full pattern.

## Gotchas

- `create_region_rule` before a successful geometry build fails with HTTP 500 "failed to evaluate region rules". Build first, with `gb.build(on_error=allsolve.OnError.STRICT)`; `get_status()` only knows builds started by the same builder object (a fresh `project.geometry_builder()` returns `None`).
- `region.entity_tags` is a snapshot from when the region was evaluated. After a geometry rebuild, re-read the regions with `project.get_regions()`.
- **POINT regions select CAD vertices, not mesh nodes.** If no CAD vertex exists within the bbox, the region contains zero entities → solver fails with `"physical region number N is not defined"`. For probing at arbitrary coordinates, use `interpolate(reg, expr, [x, y, z])` in the output expression instead.
- **`interpolate()` expression syntax:** `interpolate(region, scalar_expr, [x, y, z])` — the third argument is a square-bracket comma-separated vector. Do not pass coordinates as separate arguments. Do not use semicolons (`[0; 0; z]` is force/vector syntax).
- **Region bounding boxes support project-variable expressions** (e.g. `("-L/2", "-W/2", 0)`) — these resolve at build time. If a region unexpectedly has zero entities, verify the expressions evaluate to coordinates that enclose the expected geometry entities.
- **Check the count of every `attribute_path` rule**: a path that matches nothing does not filter.
- **STEP product names are not self-describing.** Verify the mapping (for example with build123d) before writing `attribute_path` rules.

## Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `region had zero entity tags` | Wrong `min_size`/`max_size` filter | Adjust filters; use computed regions |
| `Invalid regions in mesh parameters: zero entity tags` | Region rule matches nothing | Fix region selectors before meshing |
| `targets tags [...] that are outside its physics target region` | Interaction target includes entities outside the physics domain | Intersect with the domain boundary (see [the RF domain skill](../../allsolve-domain-rf/SKILL.md#port-regions)) |
