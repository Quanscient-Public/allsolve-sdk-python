---
name: allsolve-domain-thermal
description: >-
  Allsolve SDK domain guide for thermal and heat-transfer simulations:
  HeatTransfer/HeatFluid physics, convection (Robin), heat sources (volumetric,
  or a flux on faces), fixed temperature, initial temperature, Joule heating
  driven by CurrentFlow (busbars, resistors, traces), conjugate heat transfer,
  steady-state vs transient, temperature outputs. Use when setting up an
  Allsolve model whose result is a temperature field, for example heat sinks,
  chips, busbars and power electronics.
---

# Thermal / Heat transfer simulations

End-to-end guide for heat transfer simulations with `HeatTransfer` (solid conduction) and `HeatFluid` (fluid thermal) physics. Read the [allsolve-sdk](../allsolve-sdk/SKILL.md) skill first for setup, the build order and the building-block references.

## Physics

```python
physics_set = project.get_default_physics_set()
heat = physics_set.add_physics(allsolve.Physics.HeatTransfer())
```

For fluid thermal problems, use `HeatFluid` instead:

```python
heat_fluid = physics_set.add_physics(allsolve.Physics.HeatFluid())
```

`HeatFluid` solves the energy equation in a fluid domain. Advection comes from the `LaminarFlowThermalFluid` interaction on a `LaminarFlow` physics. Without it there is no advection. HeatFluid has its own interactions (`HeatFluidConstraint`, `HeatFluidHeatSource`, `HeatFluidPeriodicity`, `HeatFluidInitialValue`) and shares the field `T` with HeatTransfer, so give the two disjoint targets: `add_physics` accepts overlapping ones, but the simulation then does not start ("The target regions of Heat fluid and Heat solid must be disjoint"). Typically used for conjugate heat transfer (solid conduction + fluid convection).

Temperature field symbol: **`T`**. Temperatures are always **kelvin**.

## Interactions

### Convection (Robin BC)

Heat loss to an ambient fluid:

```python
allsolve.Interaction.HeatTransferConvection(
    name="Ambient convection",
    target=regions.exposed,
    heat_transfer_convection_heat_transfer_coefficient="h_conv",  # project variable [W/m²/K]
    heat_transfer_convection_fluid_temperature="T_ambient",       # project variable [K]
)
```

Convection belongs on faces that touch the ambient fluid. See the physics target notes in [physics-and-interactions](../allsolve-sdk/references/physics-and-interactions.md#general).

Define `h_conv` and `T_ambient` as project variables. Typical `h_conv`: natural air 2–25, forced air 25–250, forced liquid 100–20,000 W/m²K (orders of magnitude; prefer spec values). `T_ambient` = 293.15 K (20 °C).

### Heat source

Volumetric or surface heating:

```python
allsolve.Interaction.HeatTransferHeatSource(
    name="Heater",
    target=regions.heat_surface,
    heat_source_power_density="Q_heat",  # per unit measure of the target: W/m³ on a volume, W/m² on a face
)
```

For a total power P in W, divide by the target's volume or area in the expression (`"P_chip / (L_chip * W_chip * H_chip)"`), or, on a boundary, use `HeatTransferLumpTPhi` in `HeatTransferLumpTPhiActuationMode.HEAT_POWER` mode, which takes the total heat power through the port. See the [source and load density rule](../allsolve-sdk/references/physics-and-interactions.md#interactions-boundary-conditions).

### Temperature constraint (Dirichlet)

Fixed temperature on a boundary:

```python
allsolve.Interaction.HeatTransferTemperatureConstraint(
    name="Fixed temp",
    target=regions.fixed_surface,
    temperature_constraint="273.15",
)
```

### Joule heating (electro-thermal)

Joule heating needs a physics that provides current density: `CurrentFlow` (DC/AC conduction) or `MagnetismH` (eddy currents). `ElectromagneticWaves`, `Electrostatics` and `MagnetismA` do not provide it. Add both physics before any interaction.

```python
cf = physics_set.add_physics(allsolve.Physics.CurrentFlow(target=regions.conductor))
heat = physics_set.add_physics(allsolve.Physics.HeatTransfer(target=regions.conductor))
cf.add_interactions([
    allsolve.Interaction.CurrentFlowConstraint(
        name="Ground", target=regions.end_a, current_flow_constraint="0"),
    allsolve.Interaction.CurrentFlowLump(          # drive a total current in A
        name="Drive", namespace="drive", target=regions.end_b,
        current_flow_lump_actuation_mode=allsolve.CurrentFlowLumpActuationMode.CURRENT,
        current_flow_lump_current="I_drive"),
])
heat.add_interactions([
    allsolve.Interaction.HeatTransferJouleHeating(name="Joule", target=regions.conductor),
    # plus convection and temperature constraints as usual
])
```

The potential field is `v`. The lump gives `drive.V` (its potential relative to the 0 V ground) and `drive.I` as output expressions. The material needs `electric_conductivity` and `thermal_conductivity`.

### Interaction summary

| Interaction | Purpose |
|-------------|---------|
| `HeatTransferConvection` | Robin BC to ambient fluid |
| `HeatTransferHeatSource` | Heating per unit measure of the target (W/m³ on volumes, W/m² on faces) |
| `HeatTransferTemperatureConstraint` | Dirichlet (fixed T) |
| `HeatTransferJouleHeating` | Coupled electrical heating |
| `HeatTransferInitialValue` | Initial temperature (transient) |

## Thermal contact

For solid heat transfer (`Physics.HeatTransfer`), touching volumes share temperature at interfaces automatically. **A gap between bodies blocks conduction** — volumes must meet (coincident shared faces after geometry `build()`). There is no contact-resistance interaction: shared faces are in perfect contact. To model a resistance, insert a thin layer with k_eff = h_c · t. Faces with no thermal interaction are adiabatic.

## Initial temperature

The default initial temperature is 0 K. Set a physical initial value with the `HeatTransferInitialValue` interaction:

```python
heat.add_interactions([
    allsolve.Interaction.HeatTransferInitialValue(
        name="Initial temperature",
        heat_transfer_initial_value="room_temp",  # project variable [K]
        target=regions.solid,
    ),
])
```

To start different regions at different temperatures, add one interaction per region. The interactions are applied in the order you add them, and **nodes on a shared face get the value of the last one applied**.

The initial value can be any expression, including a variable or a function of x, y, z.

## Materials

Thermal materials need `density`, `heat_capacity` and `thermal_conductivity`. Read [materials](../allsolve-sdk/references/materials.md) for custom and library materials when you create or change a material.

- `density` and `heat_capacity` are required for transient (thermal mass).
- `thermal_conductivity` is required for all thermal simulations.

## Simulation types

Use `create_simulation_static` for steady state or `create_simulation_transient` for time-dependent problems. Read [simulation](../allsolve-sdk/references/simulation.md#common-kwargs) for the kwargs when you create the simulation.

For transient thermal: `TimestepAlgorithm.IMPLICIT_EULER` (or `GEN_ALPHA`), and always set an initial temperature (see above) — the default 0 K is unphysical.

If only the final temperature matters, use a static simulation. For a transient, estimate the time scale first: lumped τ ≈ ρ·c·V / (h·A), or diffusion τ ≈ ρ·c·L² / k. Run several τ to reach steady state; `pin_fin_heat_sink` (10 s, 1 s steps) is far from it.

## Outputs

### Temperature field

```python
allsolve.Output.FieldOutput(
    name="Temperature",
    expression="T",
)
```

### Scalar value outputs

```python
allsolve.Output.ValueOutput(
    name="Average temperature (part)",
    expression="average(reg.copper_material_region, T, 3)",
)
allsolve.Output.ValueOutput(
    name="Max temperature",
    expression="maxvalue(reg.all, T, 1)",
)
```

## Typical region pattern

For a heat sink with convection on exposed surfaces:

```python
regions.solid = project.create_region_rule(
    name="solid",
    entity_type=allsolve.Region.VOLUME,
    bounding_box=(solid_min, solid_max),
)
regions.bottom = project.create_region_rule(
    name="bottom_surface",
    entity_type=allsolve.Region.SURFACE,
    bounding_box=(bottom_min, bottom_max),
)
skin = project.create_region_computed(
    name="solid_skin", entity_type=allsolve.Region.SURFACE,
    operation=allsolve.RegionOperation.BOUNDARY, source_regions=[regions.solid.id],
)
regions.exposed = project.create_region_computed(   # convection everywhere except the heated face
    name="exposed_surfaces", entity_type=allsolve.Region.SURFACE,
    operation=allsolve.RegionOperation.DIFFERENCE, source_regions=[skin.id, regions.bottom.id],
)
```

When the solid touches other bodies, take `BOUNDARY` of the union of all volumes; see the boundary-face note in [physics-and-interactions](../allsolve-sdk/references/physics-and-interactions.md#general).

## Reference examples

- `examples/pin_fin_heat_sink/heat_sink_demo.py`: transient pin-fin heat sink with convection cooling, a surface heat source (W/m²), library materials, mesh refinement, and average temperature outputs.

Docs: heat transfer in solids (`/documentation/using-allsolve/physics/heat-solid`), heat transfer in fluids (`/documentation/using-allsolve/physics/heat-fluid`). More in [docs-map](../allsolve-sdk/references/docs-map.md).
