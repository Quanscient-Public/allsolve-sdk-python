# Allsolve physics and interactions

**Contents:** [Adding physics](#adding-physics) · [Interactions (boundary conditions)](#interactions-boundary-conditions) · [Coupling several physics](#coupling-several-physics) · [Domain-specific interactions](#domain-specific-interactions) · [Gotchas](#gotchas)

This reference covers the generic mechanics of physics and boundary conditions: physics sets, adding physics, interaction objects, targeting interactions at regions, and the ordering rules for coupled multiphysics. For domain choices (which interactions for a heat sink, antenna, beam or transducer), read the domain skill.

## Adding physics

Each project has a default physics set (named `"Physics 1"`). Use it for single-physics workflows:

```python
physics_set = project.get_default_physics_set()
heat = physics_set.add_physics(allsolve.Physics.HeatTransfer())
```

For alternative physics configurations, create a named set:

```python
alt_set = project.create_physics_set(name="alt_physics")
heat = alt_set.add_physics(allsolve.Physics.HeatTransfer())
```

`project.add_physics(...)` is deprecated — use `physics_set.add_physics()` instead.

### Physics set management

```python
project.get_physics_sets()              # list all sets
project.get_default_physics_set()       # default set
project.create_physics_set(name="alt")  # new named set
PhysicsSet.copy_physics_set(set.id)     # copy an existing set
```

Simulations reference a physics set instead of a flat list of physics IDs — pass `physics_set=` to `create_simulation_*` (the old `physics=` list is deprecated).

Available physics types:

| Physics type | Field | Domain |
|-------------|-------|--------|
| `HeatTransfer` | Temperature (`T`) | Solid conduction |
| `HeatFluid` | Temperature | Fluid thermal |
| `SolidMechanics` | Displacement (`u`) | Structural |
| `ElasticWaves` | Displacement (`u`) | Wave propagation in solids |
| `AcousticWaves` | Pressure (`p`) | Acoustic domains |
| `ElectromagneticWaves` | EM fields | Full-wave EM |
| `Electrostatics` | Potential (`v`) | Static electric fields |
| `CurrentFlow` | Potential (`v`) | Electric current |
| `MagnetismA` | Vector potential (`A`) | Magnetic (A-formulation) |
| `MagnetismH` | Magnetic field (`H`) | Magnetic (H-formulation) |
| `MagnetismPhi` | Scalar potential | Magnetic (scalar) |
| `LaminarFlow` | Velocity, pressure | Incompressible flow |
| `MeshDeformation` | Mesh displacement | ALE / moving mesh |

## Interactions (boundary conditions)

Interactions attach to a physics object and target a region:

```python
heat.add_interactions([
    allsolve.Interaction.HeatTransferConvection(
        name="Ambient convection",
        target=regions.exposed_surfaces,
        heat_transfer_convection_heat_transfer_coefficient="10",  # W/m²/K
        heat_transfer_convection_fluid_temperature="293.15",      # K
    ),
    allsolve.Interaction.HeatTransferHeatSource(
        name="Heater",
        target=regions.heat_surface,
        heat_source_power_density="100",  # W/m² here (surface target); W/m³ on a volume
    ),
    allsolve.Interaction.HeatTransferTemperatureConstraint(
        name="Fixed temp",
        target=regions.fixed_surface,
        temperature_constraint="273.15",
    ),
])
```

- **Source and load densities are per unit measure of the target**: per volume on a volume, per area on a face, per length on a curve. This applies to `SolidMechanicsLoad`, `ElasticWavesLoad`, `HeatTransferHeatSource` and `HeatFluidHeatSource`; the parameter docstring says "per unit volume, area or length" (check it for any other source). For a total, divide by the target's measure in the expression, or use the physics' Lump port on a boundary, which takes a total in its flow-type actuation mode (`*_actuation_mode`): `SolidMechanicsLump`/`ElasticWavesLump` (force, N), `HeatTransferLumpTPhi` (heat power, W), `CurrentFlowLump` (current, A), `ElectrostaticsLump` (charge, C), `LaminarFlowLumpPM` (mass flow rate).

### Interaction parameters from material properties

An interaction parameter can read a material property of its target region through the `par` namespace, as in the solver script: `par.<name>()`, or `par.<name>(f)` for a frequency-dependent property. The GUI calls this "from material properties". A bare name such as `"Mub(f)"` or `"bulkviscosity"` fails with `Unknown function` or `Unknown variable` when the script is generated.

```python
elastic.add_interactions([
    allsolve.Interaction.ElasticWavesViscousDamping(
        name="Viscous damping",
        target=regions.passive_solids,   # every volume needs a material with viscous damping
        elastic_waves_viscous_damping_bulk_viscosity="par.Mub(f)",
        elastic_waves_viscous_damping_shear_viscosity="par.Mus(f)",
    ),
])
```

Names for elastic materials (each exists only when the material defines that property): `rho`, `H` (stiffness), `vp`, `vs` (wave velocities), `Mub(f)`, `Mus(f)` (viscosities, only in the attenuation form), `dbpmpmhzP`, `dbpmpmhzS` (attenuations), `alphad()`, `betad()` (Rayleigh coefficients from `mass_damping_coefficient` and `stiffness_damping_coefficient`). For other materials, run `sim.save_generated_scripts(...)` and read `parameters.py`: each method is one name. `f` always exists in harmonic simulations, where it is the fundamental frequency; in a transient it needs `target_frequency`, or a project variable named `f`.

## Coupling several physics

To couple physics, add each physics to the same physics set, each with its own `target` region. Then add the coupling interactions (for example a piezoelectric, electric force or acoustic-structure interaction) to the physics that owns them. The interaction class name starts with the owning physics, for example `SolidMechanicsElectricForce` goes on `SolidMechanics`. Create all physics before any coupling interaction (see [Gotchas](#general)).

## Domain-specific interactions

Domain specifics: see the allsolve-domain-* skills.

**Coupled multiphysics examples:** `examples/cmut/CMUT_single_cell_rx.py`, `examples/lumped_pull_in_analysis/`, `examples/pzt_disc_in_water/`. Interaction kwargs and their meaning: grep the class in `src/allsolve/physics/generated/interactions.py`.

## Gotchas

### General

- **Coupled multiphysics: create ALL physics before adding interactions.** The server validates that required fields exist at interaction creation time. Fields (`displacement`, `electricPotential`, `meshDeformation`, `pressure`, `velocity`, …) are created as a side effect of `add_physics()`. Cross-physics interactions like `ElectrostaticsLargeDisplacement`, `SolidMechanicsElectricForce`, or `LaminarFlowFluidStructure` fail with `"project is missing a field required by the interaction"` (400) if the physics that owns the needed field has not been added yet. Safe pattern: call `add_physics()` for every physics first, then `add_interactions()` for each.
- **`set_field_interpolation_order(n)` MUST be followed by `physic.save()`** — otherwise the generated script keeps the default order.
- **Physics target.** Without `target=`, a physics uses its default target: the whole domain (every volume). Pass `target=` to restrict it to the volumes where that physics is solved, for example when the model has volumes that belong to another physics or to no physics.
- **Boundary interactions act wherever their faces are, also inside the physics domain.** A face shared by two volumes of the same physics is an internal face, and a boundary condition on it (convection, a load, a constraint) is applied there. When you select faces with `BOUNDARY` of one volume, the faces it shares with neighbours are included; use `BOUNDARY` of the union of all volumes in the physics target for the outer skin only.
- **Every Lump interaction needs a `namespace`; its port quantities are `<namespace>.<name>`:** `V` with `I` (`CurrentFlowLump`, `CurrentFlowLumpVICut`, `ElectromagneticWavesLumpVI`, `MagnetismPhiLumpIV`) or with `Q` (`ElectrostaticsLump`); `T`, `Phi` (`HeatTransferLumpTPhi`); `phi`, `PhiB` (`MagnetismPhiLumpPhiPhiB`); `P`, `M` (`LaminarFlowLumpPM`); and components such as `Ux`, `Fz` (mechanical lumps) or `Vx`, `Fvz` (`LaminarFlowLumpVFv`). Use them in outputs (`ValueOutput(expression="drive.V")`) and in the lump's own circuit-coupling equation. They are not allowed in other interactions' parameters ("Port references are not allowed in this context") or in project variables, and a project variable that uses one stops every simulation in the project from starting.

### Wave physics (acoustics, EM; see the domain skills for details)

- **`wavelet(freq, delay)`:** delay is in **periods**, not seconds. `delay=2.5` → peak at `2.5/freq` seconds. Meant for transient analysis; in harmonic analysis use `sn`/`cn`.
- **`target_frequency` on `create_simulation_transient` only defines the variable `f`** in the generated script. Set it when an expression uses `f`, for example a frequency-dependent material or damping. Viscous damping from material attenuations (`par.Mub(f)`, `par.Mus(f)`) needs it. It does not tune the time stepper or the PML.
- **`pml_num_layers` is a project-level setting:** `project.pml_num_layers = N` followed by `project.save()`. The default is 2. The server applies it when the property is unset; `project.pml_num_layers` then reads `None`.
- **PML placement and MUMPS ICNTL(14):** see [acoustics](../../allsolve-domain-acoustics/SKILL.md#boundary-conditions-by-role) and [RF](../../allsolve-domain-rf/SKILL.md#gotchas).

### Electromagnetic / MQS (see [allsolve-domain-rf](../../allsolve-domain-rf/SKILL.md))

- **Known limitation: full-wave harmonic EM fails with MUMPS `INFOG(1)=-3` above about 1.5M DOF.** Observed in at least one large model; the cause is unconfirmed. For sub-wavelength coils, use magnetoquasistatic `MagnetismA` instead.
- **In harmonic MQS simulations, drive with `"sn(1)"`, not `"1"`:** a constant is the DC harmonic and gives no excitation at the fundamental. Static and transient MagnetismA take constant or time-dependent drives.
- **Coil impedance: use `CurrentFlowLumpVICut` (cohomology cut)** — a two-terminal `CurrentFlowLump` across a gap does NOT capture inductive EMF.
- **Output field tokens for MQS are DERIVED fields** (`B`, `H`, `j`, `E`) — primary tokens `A`, `v` evaluate to 0 in `integrate()`/`average()`. `curl(A)` is not valid; use `B`.
