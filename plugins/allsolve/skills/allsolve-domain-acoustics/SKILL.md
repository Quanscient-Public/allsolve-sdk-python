---
name: allsolve-domain-acoustics
description: >-
  Allsolve SDK domain guide for acoustic, elastic-wave and piezoelectric device
  models: PMUT, CMUT, FBAR/BAW resonators, piezo discs and ultrasonic
  transducers, acoustic-structure coupling, PML placement, unit-cell periodic
  stacks, and the choice of transient, harmonic or eigenmode analysis. Use when
  the user wants to set up or tune such a device as an Allsolve simulation. Not
  for pure theory questions.
---

# Allsolve acoustic and piezoelectric device modelling

Domain guide for wave and piezoelectric devices. Read the [allsolve-sdk](../allsolve-sdk/SKILL.md) skill first for setup and the build order.

## Choosing the analysis type

| Device class | Analysis type | Reason |
|---|---|---|
| Thin-film bulk resonator (FBAR/BAW) | **Harmonic** | Impedance vs frequency; no time ringdown needed |
| Piezocomposite / bulk transducer | **Transient** for bandwidth and pulse KPIs; **harmonic** sweep for impedance | Broadband wavelet → FFT for Tx sensitivity; impedance at each frequency |
| MEMS membrane (PMUT) | **Harmonic** or **Eigenmode** | Harmonic for an impedance sweep; eigenmode for the resonant frequency |
| Send/receive, pulse response (PMUT, CMUT, piezo disc) | **Transient** (`GEN_ALPHA`) | Time signals of the transmitted pulse and the received echo |
| Frequency sweep (any resonator) | **Harmonic + variable override on freq** | Cheap per-point solve |
| Natural frequency / mode shape | **Eigenmode** | Cheapest for resonance location |
| Static bias, then dynamics (CMUT, electrostatic MEMS) | **Static → transient**, chained | See [Chaining simulations](../allsolve-sdk/references/simulation.md#chaining-simulations) |

Rule of thumb: for spectral bandwidth or time-domain ring-down, use transient. For impedance at discrete frequencies, use harmonic. For only the resonant frequency, eigenmode is cheapest.

## Unit cell architecture (periodic devices)

Infinite periodic arrays (transducer arrays, metamaterials) are modelled as a **quarter or half unit cell** with symmetry boundary conditions:

```
Mirror symmetry on all lateral faces → infinite array, all cells in phase, and only modes that are even across each symmetry face.
```

For odd modes or an alternating (180°) array, model a full cell with the `*Periodicity` interactions (translation; periodic or anti-periodic) on every physics, for example `ElasticWavesPeriodicity` and `ElectrostaticsPeriodicity` for a piezo cell, plus `AcousticWavesPeriodicity` when the cell has fluid. An arbitrary phase between cells (beam steering, Floquet–Bloch) is not available.

Cell width:
- **1-3 composite**: `cell_w = pillar_w / 2 + kerf_w / 2` (half pillar + half kerf)
- **Square array (PMUT)**: `cell_w = pitch / 2` (quarter cell)

This uses the in-plane periodicity and keeps the DOF count low.

## Standard layer stack pattern

Many planar transducers share this z-axis structure:

```
z_max  ┌──────────────────┐  ← Absorbing boundary (PML)
       │    Load medium    │  (water / air)
       ├──────────────────┤  ← Output surface (pressure measurement)
       │    Active layers  │  (piezo + electrodes + matching)
       ├──────────────────┤  ← Excitation surface (electrode)
       │    Backing        │  (absorbing or clamped)
z_min  └──────────────────┘  ← Absorbing boundary (PML) or clamp
```

Load medium thickness: **1 wavelength** at the centre frequency, for planar layer stacks only. Around a finite device (a disc, a membrane in a fluid), use the distance that the spec gives.

## Physics coupling pattern

Piezoelectric devices couple three physics. The pattern below uses the elastic-waves family, as in `examples/pmut_array`:

```python
physics_set = project.get_default_physics_set()
ew = physics_set.add_physics(allsolve.Physics.ElasticWaves(target=vol_solid))
aw = physics_set.add_physics(allsolve.Physics.AcousticWaves(target=vol_fluid))
es = physics_set.add_physics(allsolve.Physics.Electrostatics(target=vol_piezo))
```

Coupling interactions (elastic-waves family):
- **Piezoelectric**: `ElasticWavesPiezoelectricity` on the piezo region (one interaction only)
- **Acoustic-structure**: `AcousticWavesAcousticStructureForElasticWaves`

For non-piezoelectric elastic-acoustic problems, leave out Electrostatics. Create all physics before you add any coupling interaction.

### Choose the mechanics family

Use the family that the spec or the reference project names. Each coupling class belongs to one family, and the server rejects a class from the wrong family.

| Role | Solid mechanics family | Elastic waves family |
|---|---|---|
| Mechanics physics | `Physics.SolidMechanics` | `Physics.ElasticWaves` |
| Piezoelectric coupling (exactly one) | `SolidMechanicsPiezoelectricity` **or** `ElectrostaticsPiezoelectricity` | `ElasticWavesPiezoelectricity` **or** `ElectrostaticsElasticWavesPiezoelectricity` |
| Acoustic-structure coupling (on the acoustic physics) | `AcousticWavesAcousticStructure` | `AcousticWavesAcousticStructureForElasticWaves` |
| Symmetry plane | `SolidMechanicsSymmetry` | `ElasticWavesSymmetry` |
| Absorbing mechanical boundary | none | `ElasticWavesPml`, `ElasticWavesAbsorbingBoundary` |
| Large deformation | `SolidMechanicsLargeDisplacement`, `SolidMechanicsGeometricNonlinearity` | none |
| Example | `examples/pmut_send_receive` | `examples/pzt_disc_in_water`, `examples/pmut_array` |

- **The two piezo classes in one row are the same interaction seen from each physics.** One instance adds the coupling to both equations. A second one fails with `Only 1 "Piezoelectricity" interactions can be enabled`.
- Choose **solid mechanics** for static solves, a static bias followed by a transient, or large deflection (CMUT, pull-in). Choose **elastic waves** when elastic waves must leave the model through an elastic PML (bulk transducers, a substrate that is not clamped).

## Boundary conditions by role

| Role | Interaction | Notes |
|---|---|---|
| Lateral symmetry | `ElasticWavesSymmetry` | On all lateral faces of the unit cell |
| Absorbing (elastic) | `ElasticWavesPml` | On the backing bottom. Pick the type below |
| Absorbing (acoustic) | `AcousticWavesPml` | On the fluid's outer boundary. Pick the type below |
| Absorbing, lighter | `AcousticWavesAbsorbingBoundary` | First-order condition, no parameters. Some residual reflection |
| Substrate clamp | `ElasticWavesClamp` | Alternative to a PML for a rigid backing |
| Ground electrode | `ElectrostaticsConstraint(name="Ground", electrostatics_constraint="0", target=...)` | On one electrode face |
| Drive electrode | `ElectrostaticsLump` | On the other electrode face. See [Excitation patterns](#excitation-patterns) |

**PML tips:**
- Choose the PML type by the shape of the boundary (`AcousticWavesPmlType`, `ElasticWavesPmlType`): **AML** for smooth or curved boundaries (for example a sphere around the device), **BOX** for rectangular or cornered ones (for example the flat top of a layer stack). AML is the default.
  ```python
  allsolve.Interaction.AcousticWavesPml(
      name="PML top",
      target=regions.pml_surface,
      acoustic_waves_pml_type=allsolve.AcousticWavesPmlType.BOX,
  )
  ```
- `project.pml_num_layers = N` (default 2) + `project.save()` before you create the interactions.
- The PML is a SURFACE interaction, not a volume. One body of fluid is enough. A physics accepts one enabled PML interaction (a second one is created without error but the simulation does not start), so put all PML faces in one region.
- **Selecting the PML faces.** The PML goes on the faces that face open space. `BOUNDARY` of the union of all volumes in the physics target gives the outer skin and leaves out internal faces; `BOUNDARY` of a single fluid volume also includes the faces it shares with the device, which must not get a PML. Remove symmetry planes and any face with another outer condition (a baffle, a clamp) with `DIFFERENCE`. If the PML covers only part of the skin (for example the top of a layer stack), select those faces with a bounding-box rule instead.
- The PML is built by extruding the boundary mesh outwards, `pml_num_layers` element layers deep (project setting, default 2; the project's `pml_thickness` is not used). Each layer comes out at about 0.6–0.8 × the element size at that boundary, so the PML thickness scales with layers × element size: a finer mesh there makes the PML thinner, not only finer. To make it thicker without coarsening the mesh, raise `pml_num_layers`. If reflections from the boundary change the result, add layers and compare. Also compare with `AcousticWavesAbsorbingBoundary`.
- All PML interactions in one simulation (its physics set, across all its physics) must have the same type; otherwise it does not start ("All PML interactions must have the same type"). Different physics sets in one project can use different types. BOX needs an outer boundary whose faces are aligned with the x, y and z axes; use AML for anything else.

## Electroacoustic device patterns

| Device | Key interactions | Analysis | Example |
|---|---|---|---|
| Bulk or disc transducer, FBAR | Elastic-waves family (table above) | Harmonic impedance sweep, or transient | `pzt_disc_in_water` |
| PMUT, piezo layer on a membrane | Either family; choose with the rules above | Harmonic, or transient send/receive | `pmut_array` (elastic waves), `pmut_send_receive` (solid mechanics) |
| CMUT, electrostatic MEMS | `SolidMechanicsLargeDisplacement` + `ElectrostaticsLargeDisplacement`, electric force, mesh deformation | Static bias, then a transient started from its field state | `cmut` |

### Floating electrode

A receive electrode with no external circuit is an `ElectrostaticsLump` in charge mode with zero charge. Read its voltage as `<namespace>.V`:

```python
allsolve.Interaction.ElectrostaticsLump(
    name="Receive", target=rx_electrode, namespace="rx",
    electrostatics_lump_actuation_mode=allsolve.ElectrostaticsLumpActuationMode.CHARGE,
    electrostatics_lump_charge="0",
)
# Output expression: "rx.V"; current on a driven lump: "dt(drive.Q)"
```

### Impedance from a harmonic solve

Harmonic 2 is the sin coefficient and harmonic 3 is the cos coefficient. For a drive `V0*sn(1)`, the phasor is `X = harm(3, x) - j*harm(2, x)`, or use the same sign convention for V and I so that it cancels in Z:

```
V = harm(3, drive.V) - j*harm(2, drive.V)
I = harm(3, dt(drive.Q)) - j*harm(2, dt(drive.Q))
Z = V / I
```

`examples/pzt_disc_in_water` computes `Z real` and `Z imag` as value outputs with project functions.

### Symmetry models

- **Scale lumped values back to the full device.** A symmetry model carries only its share of the electrode current, and a cut through the electrode gap carries only part of the voltage. Scale V and I by the factor of each cut before you compute the impedance. Example: `examples/pzt_disc_in_water`.
- Put the mechanics symmetry interaction on every cut plane. Acoustic waves has no symmetry interaction: a cut plane with no acoustic boundary condition is sound-hard, which is correct for a pressure field that is even across the plane. The mid-plane at 0 V is an electrostatics constraint.

### Large deformation

- `SolidMechanicsGeometricNonlinearity` uses Green-Lagrange strain: large rotations and stress stiffening of the structure.
- `SolidMechanicsLargeDisplacement` and `ElectrostaticsLargeDisplacement` solve on the deformed mesh. They need a `MeshDeformation` physics, and a coupling uses the deformed mesh only if every physics in it has large displacement. Electrostatic MEMS needs both so that the gap really shrinks.


## Excitation patterns

### Transient wavelet (broadband)

```python
allsolve.Interaction.ElectrostaticsLump(
    name="Drive", target=electrode_surface, namespace="drive",
    electrostatics_lump_voltage="V_amp * wavelet(freq, 1.2)",
)
```

`delay=1.2` puts the Ricker wavelet peak at 1.2 periods from t=0.

### Harmonic (single frequency)

Drive at the interaction level with `sn(1)`, a sine at the fundamental frequency of the harmonic simulation:

```python
allsolve.Interaction.ElectrostaticsLump(
    name="Drive", target=electrode_surface, namespace="drive",
    electrostatics_lump_voltage="V0 * sn(1)",
)
```

Set `fundamental_frequency="freq"` on the harmonic simulation, and sweep `freq` with variable overrides for an impedance sweep. Prefer `sn(1)`/`cn(1)`. An explicit `sin(2*pi*freq*t)` also works when `freq` is the simulation's fundamental frequency. Docs: load expressions, `sn()` and `cn()` (`/documentation/using-allsolve/physics/load-expressions#sn-and-cn--harmonic-shortcuts`).

## Transient simulation settings

- **Timestepper**: `TimestepAlgorithm.GEN_ALPHA` for 2nd-order wave equations
- **Duration**: travel time to the observation point (and back, for pulse-echo), plus ring-down (about Q·ln(1/ε)/π cycles, where ε is the remaining amplitude ratio, for example 0.01). Tutorials use 5–10 cycles for low-Q stacks; a high-Q PMUT in air needs far more.
- **Steps per cycle**: 20–25 (`1 / (freq * ppc)`)
- **`target_frequency`** only defines the variable `f` in the generated script. Set it when an expression uses `f` (for example frequency-dependent material or damping). It does not tune the time stepper or the PML.
- **Solver**: DIRECT for small unit cells; ITERATIVE for >1M DOF

## Standard outputs (transient piezoelectric)

| Output | Expression | Use |
|---|---|---|
| Drive voltage | `drive.V` | FFT numerator for impedance |
| Drive charge | `drive.Q` | Integrate for current |
| Drive current | `dt(drive.Q)` | FFT denominator for impedance |
| Front pressure | `average(reg.front_face, p, 3)` | FFT for Tx sensitivity |
| Front velocity | `average(reg.front_face, dt(compz(u)), 3)` | Mechanical output |

Read [postprocessing](../allsolve-sdk/references/postprocessing.md) for FFT, windowing and KPI extraction when you compute frequency-domain results from a transient.

## Mesh sizing for wave problems

**Elements per wavelength** drive the accuracy:

| Medium | Rule of thumb | Notes |
|---|---|---|
| Water (acoustic) | 6 elements / λ | |
| Solid (elastic) | 6–10 elements / λ_shear | Shear wavelength is shorter |
| Thin layers | thickness / 2.5 | ≥2 quadratic elements through |

Read [mesh](../allsolve-sdk/references/mesh.md) for mesh sizing, `use_mesh_refiner` and node sizing when you set up the mesh.

## Reference examples

- `examples/pmut_array/pmut_array_demo.py`: PMUT array ultrasound emission with piezoelectric, elastic and acoustic wave coupling.
- `examples/lumped_pull_in_analysis/lumped_pull_in_analysis.py`: electrostatic MEMS with mesh deformation and chained static simulations.

- `examples/pzt_disc_in_water/pzt_disc_in_water.py`: harmonic impedance of a PZT disc in water, 1/8 symmetry with scaling, AML PML on a sphere, `sn(1)` drive, sweep.
- `examples/pmut_send_receive/pmut_send_receive.py`: transient PMUT send/receive in solid mechanics, floating electrode, two simulations run at the same time with `allsolve.run_simulations()`.
- `examples/cmut/CMUT_single_cell_rx.py`: CMUT static bias, then a transient from the field state; interface faces with `BOUNDARY` and `INTERSECTION`; `MeshExtrusion`; a sweep and a transient run with `allsolve.run_simulations()`.

Docs: PMUT unit cell tutorial (`/documentation/tutorials/ultrasound/ultrasound-001-pmut-unit-cell`), piezocomposite tutorial (`/documentation/tutorials/ultrasound/piezocomposite`). More in [docs-map](../allsolve-sdk/references/docs-map.md).

## Gotchas

### Physics
- **One piezoelectric interaction, not two.** Do not add both `ElasticWavesPiezoelectricity` and a separate electrostatics piezo coupling.
- **The default source is a uniform piston.** Do not add a window function unless the user asks for one.
- **Acoustic-structure coupling goes on the acoustic physics,** not on the elastic one.

### Analysis
- **Harmonic devices (FBAR)**: the impedance comes directly from the port V/I. No FFT is needed.
- **Transient devices**: run long enough for a complete ring-down (see Duration). An incomplete ringdown causes spectral leakage; use a right-hand Hanning window.
- **Eigenmode is cheapest for finding the resonant frequency.** No damping or sweep is needed, one solve per mesh. Use it when only the frequency matters, not the amplitude.
- **Without damping, a harmonic sweep has very large, mesh-dependent peaks at resonance** (unless a PML, an absorbing boundary or radiation adds loss). Add damping:
  - material losses: `ElasticWavesViscousDamping` with `par.Mub(f)`, `par.Mus(f)` (see [materials](../allsolve-sdk/references/materials.md)), or `AcousticWavesAcousticDamping` in the fluid;
  - a target quality factor Q: `ElasticWavesProportionalDamping` (or `SolidMechanicsProportionalDamping`) with alpha = `"qtoalpha(f, Q)"` and beta = `"qtobeta(f, Q)"` **together**. Each helper gives half of the damping, so the pair gives Q at the frequency f; beta alone gives 2Q. With `f` in the expression, Q holds at every frequency of a sweep; with a number instead of `f`, it holds at that frequency only (true Rayleigh damping);
  - Rayleigh coefficients stored on the material (`mass_damping_coefficient`, `stiffness_damping_coefficient`): alpha = `"par.alphad()"`, beta = `"par.betad()"`.
