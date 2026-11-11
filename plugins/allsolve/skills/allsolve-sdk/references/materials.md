# Allsolve materials

**Contents:** [Custom material](#custom-material) · [Library material](#library-material) · [Common properties](#common-properties) · [Gotchas](#gotchas)

This reference covers custom and library materials, the common property kwargs, elasticity and damping (`MaterialProperty`), and material sweeps.

Each material needs a `target_region` matching the geometry it represents.

## Custom material

```python
project.create_material(
    name="Steel",
    target_region=regions.solid,
    density=7850,
    heat_capacity=460,
    thermal_conductivity=50,
)
```

Properties accept numbers or strings. Use strings for project variables and expressions:

```python
project.create_material(
    name="Custom",
    target_region=regions.part,
    density="rho",
    heat_capacity="cp",
    thermal_conductivity="k",
)
```

### Conditional activation for sweeps

Use `enabled` to activate a material only when a sweep variable matches:

```python
project.create_material(
    name="Aluminium",
    enabled="material_index == 0",
    target_region=regions.part,
    density=2700,
    thermal_conductivity=237,
    heat_capacity=897,
)
project.create_material(
    name="Steel",
    enabled="material_index == 1",
    target_region=regions.part,
    density=7850,
    thermal_conductivity=50,
    heat_capacity=460,
)
```

## Library material

```python
project.create_material_from_library(name="Copper", target_region=regions.part)
```

Library materials come with standard property values. List the names available on the current host with `[m.name for m in allsolve.Material.get_all_from_library()]`.

## Common properties

| Property                  | Unit     | Typical use     | Notes |
| ------------------------- | -------- | --------------- | ----- |
| `color`                   | —        | Visualization   | Direct kwarg; hex `#RRGGBB` (e.g. `"#99D9FF"`). Library materials inherit their color |
| `density`                 | kg/m³    | All physics     | Direct kwarg |
| `heat_capacity`           | J/(kg·K) | Thermal         | Direct kwarg |
| `thermal_conductivity`    | W/(m·K)  | Thermal         | Direct kwarg |
| `electric_permittivity`   | F/m      | Electromagnetic | Direct kwarg |
| `magnetic_permeability`   | H/m      | Electromagnetic | Direct kwarg |
| `electric_conductivity`   | S/m      | Electromagnetic | Direct kwarg (note: `electric_`, not `electrical_`) |
| `speed_of_sound`          | m/s      | Acoustic        | Direct kwarg |
| `longitudinal_attenuation`| dB/(m·MHz) | Elastic viscous damping | Direct kwarg; same property as in `ViscousDampingLongitudinalAttenuationShearAttenuation` |
| `shear_attenuation`       | dB/(m·MHz) | Elastic viscous damping | Direct kwarg; same property as in `ViscousDampingLongitudinalAttenuationShearAttenuation` |

**Structural elasticity** — Young's modulus and Poisson's ratio are NOT direct kwargs. Use `MaterialProperty`:

```python
project.create_material(
    name="Steel",
    target_region=regions.solid,
    density=7850,
    elasticity_matrix=allsolve.MaterialProperty.ElasticityMatrixYoungsModulusPoissonsRatio(
        youngs_modulus=210e9,
        poissons_ratio=0.3,
    ),
)
```

`youngs_modulus` and `poissons_ratio` accept `float | str`. Use a string only for a variable or an expression, for example `"E_film"`.

For wave problems the elasticity can be given by the wave velocities (needs `density`):

```python
elasticity_matrix=allsolve.MaterialProperty.ElasticityMatrixPressureShearVelocity(
    pressure_velocity=6000, shear_velocity=3000,  # m/s
)
```

**Anisotropic and piezoelectric input:**
- Voigt order is **xx, yy, zz, yz, xz, xy**, with engineering shear strain. This applies to the 6×6 `ElasticityMatrix` (c66 is the xy shear term).
- `MaterialProperty.PiezoelectricCoupling` is the **e-form** (stress-charge, C/m²), entered as **6 rows × 3 columns**: rows are the Voigt components above, columns are Ex, Ey, Ez. This is eᵀ of the usual 3×6 matrix. There is no d-form input.
- The permittivity goes with the e-form, so use the value at constant strain (ε^S).
- For a z-poled ceramic: rows 1–3 are `[0, 0, e31]`, `[0, 0, e31]`, `[0, 0, e33]`; row 4 (yz) is `[0, e15, 0]`; row 5 (xz) is `[e15, 0, 0]`; row 6 (xy) is zero. Examples: `examples/pzt_disc_in_water`, `examples/pmut_send_receive`.

Viscous damping — use `MaterialProperty` classes:

```python
allsolve.MaterialProperty.ViscousDampingBulkViscosityShearViscosity(
    bulk_viscosity="1e-3", shear_viscosity="1e-4",
)
# or attenuation-based, in dB/(m·MHz):
allsolve.MaterialProperty.ViscousDampingLongitudinalAttenuationShearAttenuation(
    longitudinal_attenuation="200", shear_attenuation="600",  # 2 and 6 dB/cm at 1 MHz
)
```

Attenuation-based damping:
- **The attenuations are in dB/(m·MHz), not Np/m.**
- The damping model is linear in frequency: the viscosities are evaluated at the target frequency `f`. Set `target_frequency` on the simulation (see [physics-and-interactions](physics-and-interactions.md#wave-physics-acoustics-em-see-the-domain-skills-for-details)).
- The material must define its elasticity with `ElasticityMatrixPressureShearVelocity`, because the conversion uses the wave velocities.
- **The attenuation form needs `f` in every simulation that uses the material**, also when no damping interaction reads it: an eigenmode simulation (which has no `f`) fails with "Could not resolve variable "f" for property "Bulk viscosity"", and a transient needs `target_frequency` unless the project has a variable named `f`. For eigenmode runs, use a material without it, or the bulk/shear-viscosity form.
- The material property alone does not damp anything. Add an `ElasticWavesViscousDamping` interaction that reads it with `par.Mub(f)` and `par.Mus(f)` (see [physics-and-interactions](physics-and-interactions.md#interaction-parameters-from-material-properties)).

All values use SI units. Use `"epsilon0"` and `"mu0"` for free-space EM constants.

## Gotchas

- **One material per substance, multiple target volumes.** Do not call `create_material_from_library` twice for the same material on different volumes. `target_region` accepts a single `Region` object — for multiple volumes, create a computed UNION region first and pass that as the target.
- **`orientation` does NOT support spatial expressions** — only constant Euler angles. Passing expressions with `x`, `y`, etc. fails with `"Orientation expression can't be space dependent"`.
