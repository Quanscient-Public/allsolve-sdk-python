---
name: allsolve-domain-structural
description: >-
  Allsolve SDK domain guide for structural mechanics simulations:
  SolidMechanics physics, clamps, loads, prescribed displacement, pressure,
  thermal expansion and thermal stress, isotropic and anisotropic elasticity,
  static deflection, stress and von Mises outputs, eigenmodes and natural
  frequencies, MEMS structures from GDSII with extruded meshes. Use when setting up an Allsolve model of static deformation, modal
  analysis or mechanical loading, for example beams, brackets and comb drives.
---

# Structural mechanics simulations

End-to-end guide for solid mechanics simulations with `SolidMechanics` physics. Read the [allsolve-sdk](../allsolve-sdk/SKILL.md) skill first for setup, the build order and the building-block references.

## Physics

```python
physics_set = project.get_default_physics_set()
solid = physics_set.add_physics(allsolve.Physics.SolidMechanics())
```

For multi-body problems where only a subset of volumes is structural, pass an explicit target:

```python
solid = physics_set.add_physics(
    allsolve.Physics.SolidMechanics(target=regions.solid_domain)
)
```

## Interactions

### Clamp (fixed support)

```python
allsolve.Interaction.SolidMechanicsClamp(
    name="Fixed end",
    target=regions.clamp_surface,
)
```

### Applied load

```python
allsolve.Interaction.SolidMechanicsLoad(
    name="Tip load",
    target=regions.load_surface,
    force=(0, 0, "-F_total / (W * H)"),  # traction in N/m²: total force / face area
)
```

`force` is **per unit measure of the target**: N/m² (traction) on a face, N/m³ on a volume, N/m on a curve, N on a point. It is not a total force. For a total force in N, divide by the area as above, or use a lump port in force mode: `SolidMechanicsLump(..., namespace="tip", solid_mechanics_lump_actuation_mode=allsolve.SolidMechanicsLumpActuationMode.FORCE, solid_mechanics_lump_force="[0, 0; 0, 0; 1, -F_total]")`. Components can be numbers or variable expressions.

### Prescribed displacement (constraint)

```python
allsolve.Interaction.SolidMechanicsConstraint(
    name="Constraint",
    target=regions.movable_plate,
    solid_mechanics_constraint="[1, 0; 1, 0; 0, 0]",
)
```

The constraint format is `[flag, value; ...]` per component — `1` = constrained, `0` = free.

### Additional interactions

| Interaction | Purpose |
|-------------|---------|
| `SolidMechanicsPressure` | Pressure on a face (Pa); positive pushes into the solid |
| `SolidMechanicsSymmetry` | Symmetry plane (half or quarter models) |
| `SolidMechanicsLump` | Lumped port on a face: total force (N) or displacement, or a circuit equation (can act as a spring). Needs `namespace` |
| `SolidMechanicsThermalExpansion` | Thermal strain; needs CTE and a solved temperature field (`HeatTransfer` or `HeatFluid`; a variable `T` is not enough). Reference temperature defaults to 273 K |
| `SolidMechanicsProportionalDamping` | Rayleigh damping; needs `density` on the material |
| `SolidMechanicsElectricForce` | Electric force; needs a physics that provides the electric field (Electrostatics, CurrentFlow, ElectromagneticWaves or MagnetismH) and `electric_permittivity` on the material |
| `SolidMechanicsGeometricNonlinearity` | Green-Lagrange strain: large rotations, stress stiffening. No parameters |
| `SolidMechanicsLargeDisplacement` | Solve on the deformed mesh. Needs a `MeshDeformation` physics; a coupled physics sees the deformed mesh only with its own `*LargeDisplacement` (Electrostatics, LaminarFlow). No parameters |

## Materials

Structural materials need `elasticity_matrix`; add `density` for every analysis except static. Read [materials](../allsolve-sdk/references/materials.md) for custom and library materials when you create or change a material.

### Isotropic

```python
project.create_material(
    name="Aluminium",
    target_region=regions.beam,
    density=2700,
    elasticity_matrix=allsolve.MaterialProperty.ElasticityMatrixYoungsModulusPoissonsRatio(
        68e9, 0.32,
    ),
)
```

### Anisotropic (full 6x6 elasticity matrix)

Voigt order: xx, yy, zz, yz, xz, xy. The values below are single-crystal silicon with x‖[110], y‖[1-10], z‖[001] (a standard (001) wafer, rotated 45°; Hopcroft et al., J. MEMS 19(2), 2010). Rotate the stiffness to your own axes.

```python
elasticity_matrix=allsolve.MaterialProperty.ElasticityMatrix(
    value=[
        [194.5e9, 35.7e9, 64.1e9, 0, 0, 0],
        [35.7e9, 194.5e9, 64.1e9, 0, 0, 0],
        [64.1e9, 64.1e9, 165.7e9, 0, 0, 0],
        [0, 0, 0, 79.6e9, 0, 0],
        [0, 0, 0, 0, 79.6e9, 0],
        [0, 0, 0, 0, 0, 50.9e9],
    ]
)
```

## Simulation types

Use `create_simulation_static` for equilibrium deflection and `create_simulation_eigenmode` for natural frequencies. Read [simulation](../allsolve-sdk/references/simulation.md#common-kwargs) for the kwargs when you create the simulation. For a transient, use `TimestepAlgorithm.GEN_ALPHA`, the only algorithm SolidMechanics supports.

Eigenmode-specific parameters:
- `num_requested_eigenmodes` — how many modes to find.
- `target_eigenfrequency` — solver searches near this frequency; `"0"` finds the lowest modes.
- The solver can return **more modes than requested** (6 requested gives 9-10). Each mode is one output step; the order is not guaranteed and near-degenerate pairs can swap. Select modes by frequency, not by count, and sort the values yourself.
- Constrain the structure as it is supported in reality. Leave it free only for a free-free analysis (a body in flight or orbit, or to match a free-free modal test); then the first six modes are rigid-body modes near 0 Hz and carry no information.

## Outputs

### Displacement field

```python
allsolve.Output.FieldOutput(
    name="Displacement",
    expression="u",
)
```

### Scalar value outputs

```python
allsolve.Output.ValueOutput(
    name="Tip deflection Z",
    expression="interpolate(reg.beam_volume, compz(u), [x_tip, 0, 0])",  # any point inside the volume
)
allsolve.Output.ValueOutput(
    name="Max von Mises stress",
    expression="maxvalue(reg.beam_volume, vonmises(sigma), 1)",
)
allsolve.Output.ValueOutput(
    name="Deflection along beam",
    expression="lineinterpolate(reg.beam_volume, compz(u), [0, 0, 0], [L, 0, 0], 10)",
)
```

`probe(reg.<point>, …)` needs a POINT region on a CAD vertex. `interpolate(volume_region, expr, [x, y, z])` works at any coordinate inside the region or on its boundary; the coordinates can be variables.

### Eigenmode outputs

```python
allsolve.Output.FieldOutput(
    name="u",
    expression="u",
    field_output_skin_only=True,
)
allsolve.Output.Eigenfrequencies(name="Eigenfrequencies")
```

## MEMS structures (GDS import + extruded mesh)

For MEMS devices imported from GDSII layout files, use `add_gds2_file` with `CadGdsLayer` entries for each layer. Pair this with `MeshExtrusion` for structured meshing through thin-film layers.

Key API surfaces:
- `geometry_builder.add_gds2_file(filepath, layers, name=..., extrude_parameters=..., unit=...)`: import GDS geometry. **`unit` defaults to micrometres**, so `absolute_z0`, `thickness` and the `extrude_parameters` distances are in µm unless you set it.
- `allsolve.CadGdsLayer(layer=..., type=..., absolute_z0=..., thickness=..., name=...)`: one entry per layer. Pass keywords: `previous_layer_index` comes before `name` in the signature.
- `allsolve.MeshExtrusion(regions, sub_layer_counts)` in `MeshSettings(extrusions=[...])`: structured extrusion mesh. Extrusion applies only to volumes with horizontal and vertical faces.

See `examples/combdrive_eigenmodes/combdrive_eigenmodes.py` in the SDK repo for a complete example with multi-layer GDS import, extruded meshing, and eigenmode analysis. Layer numbers, thicknesses, and mesh parameters are device-specific — adapt from the example to your geometry.

## Reference examples

- `examples/bending_beam/bending_beam.py`: basic cantilever beam, static analysis, displacement field output.
- `examples/bending_beam/bending_beam_sweep.py`: parametric sweep over height, material, and force.
- `examples/combdrive_eigenmodes/combdrive_eigenmodes.py`: MEMS comb-drive eigenmode analysis with GDS import and extruded mesh.

## Gotchas

- **`SolidMechanicsConstraint` value is a 3x2 matrix** — `[active_flag, value]` per (x,y,z). First column must be numeric flags (1=constrain, 0=free), second column the value/expression. A plain `"[0;0;0]"` (3x1) is rejected.
- **A material property that uses `T` needs a temperature.** Without a physics that solves `T`, the simulation does not start ("Could not find field "T" for property … of material …"), even when the property is one that mechanics does not use, such as thermal conductivity. Either add the thermal physics, or define `T` as a project variable (for example `("T", "400", "Operating temperature [K]")`) to evaluate the material at a fixed temperature. Constant thermal or electrical properties are harmless.
- **Thermal stress:** add `HeatTransfer` (solved, or with a `HeatTransferTemperatureConstraint` fixing `T`) before `SolidMechanicsThermalExpansion`; a project variable `T` is not enough. Give the material `coefficient_of_thermal_expansion`, and set `thermal_expansion_reference_temperature` (default 273 K, not room temperature).
- **`ElasticityMatrixYoungsModulusPoissonsRatio` accepts `float | str`.** Use strings only for variables or expressions.

Docs: cantilever beam tutorial (`/documentation/tutorials/solid-mechanics/cantilever-beam`), comb-drive eigenmodes tutorial (`/documentation/tutorials/mems/mems-001-combdrive-eigenmodes`). More in [docs-map](../allsolve-sdk/references/docs-map.md).
