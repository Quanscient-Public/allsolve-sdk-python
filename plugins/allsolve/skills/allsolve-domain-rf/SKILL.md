---
name: allsolve-domain-rf
description: >-
  Allsolve SDK domain guide for RF, microwave and antenna simulations:
  ElectromagneticWaves physics, PEC, boundary admittance, dielectric loss,
  eigenmode ports, lumped ports, PML and absorbing boundaries, radiation
  patterns, and S-parameter (S11/S21) extraction for patch antennas, microstrip
  lines and waveguides (including rectangular waveguides), plus frequency
  sweeps. Use when building or
  debugging a full-wave EM model in Allsolve.
---

# RF / Microwave / Antenna simulations

End-to-end guide for full-wave electromagnetic simulations with `ElectromagneticWaves` physics. Read the [allsolve-sdk](../allsolve-sdk/SKILL.md) skill first for setup, the build order and the building-block references.

## Physics

```python
physics_set = project.get_default_physics_set()
em = physics_set.add_physics(
    allsolve.Physics.ElectromagneticWaves(target=regions.em_domain)
)
```

The EM `target` region is the volume where Maxwell's equations are solved; without a `target`, it is the whole domain.

Metal conductors: the skin depth at RF is far thinner than any practical mesh (about 2 µm for copper at 1 GHz), so do not mesh the current inside the metal. Model the metal's faces (or the metal volume) as PEC when conductor loss does not matter, or put `ElectromagneticWavesBoundaryAdmittance` on its faces when it does: its good-conductor mode computes the surface admittance from the metal's conductivity and permeability (see Boundary admittance below). Both RF examples keep the default target (the whole domain) and put PEC on the conductors. For the admittance route, leave the metal volume out of the physics target, so that its faces bound the EM domain: with the metal inside the target the run succeeds, but the loss is wrong.

## Interactions

### Perfect electric conductor (PEC)

Metallic walls, ground planes, and traces:

```python
allsolve.Interaction.ElectromagneticWavesPerfectConductor(
    name="PEC walls and trace",
    target=regions.pec,
)
```

For a closed structure such as a waveguide, PEC is often the domain boundary minus the port faces:

```python
pec = project.create_region_computed(
    name="pec",
    entity_type=allsolve.Region.SURFACE,
    operation=allsolve.RegionOperation.DIFFERENCE,
    source_regions=[em_boundary.id, ports.id],
)
```

### Boundary admittance

`ElectromagneticWavesBoundaryAdmittance` (replaces the removed `BoundaryImpedance` from v0.4.x):

```python
allsolve.Interaction.ElectromagneticWavesBoundaryAdmittance(
    name="Surface admittance",
    target=regions.boundary,
    electromagnetic_waves_boundary_admittance_type=allsolve.ElectromagneticWavesBoundaryAdmittanceType.ADMITTANCE,
    electromagnetic_waves_boundary_admittance_yr="Y_r",   # project variables
    electromagnetic_waves_boundary_admittance_yi="Y_i",
)
```

`electromagnetic_waves_boundary_admittance_type` selects how the admittance is given: `ElectromagneticWavesBoundaryAdmittanceType.ADMITTANCE` takes Yr and Yi directly; `ElectromagneticWavesBoundaryAdmittanceType.GOOD_CONDUCTOR` computes it from `..._conductivity` and `..._magnetic_permeability` (skin-effect loss of a metal; both are required, so give `"mu0"` for a non-magnetic metal).

### Dielectric loss

Lossy substrate (e.g. FR-4):

```python
allsolve.Interaction.ElectromagneticWavesDielectricLoss(
    name="FR-4 loss",
    target=regions.substrate,
    electromagnetic_waves_dielectric_loss_loss_tangent="0.02",
)
```

### Open (radiating) boundaries and lumped ports

An outer face with no interaction acts as a magnetic wall (PMC), not as an open boundary. For antennas and other radiating models, put an absorbing layer on the outer boundary of the air:

```python
allsolve.Interaction.ElectromagneticWavesPml(
    name="Box PML",
    target=regions.airbox_outer_faces,   # all PML faces in one region: one PML interaction per physics, one PML type per simulation
    electromagnetic_waves_pml_type=allsolve.ElectromagneticWavesPmlType.BOX,  # AML (default) for curved boundaries
)
```

Box PML needs an air box whose faces are aligned with the x, y and z axes; a box that is not axis-aligned cannot use it. For a curved outer boundary, use AML (the default). Set the number of PML layers with `project.pml_num_layers` and `project.save()`. `ElectromagneticWavesAbsorbingBoundary` is the alternative to a PML.

For a feed that is not a waveguide port (a probe, a gap), use a lumped port. It needs two electrode edges on the port face, and its series resistance sets the reference impedance:

```python
allsolve.Interaction.ElectromagneticWavesLumpVI(
    name="Feed", namespace="port",
    port_target=regions.port_surface,
    one_volt_electrode=regions.port_top_edge,
    ground_electrode=regions.port_bottom_edge,
    electromagnetic_waves_lump_v_i_voltage="sn(1)",
    electromagnetic_waves_lump_v_i_series_resistance="50",
    electromagnetic_waves_lump_v_i_voltage_drive=True,
)
```

`Output.SParameters` works with lumped ports too. For the far field, add `allsolve.Output.ElectromagneticWavesRadiationPattern(name="Radiation pattern")`. Full model: `examples/patch_antenna/patch_antenna_demo.py` (`create_physics`, `apply_pml_settings`, `create_simulation`).

### Eigenmode port (S-parameter extraction)

```python
em.add_interactions([
    allsolve.Interaction.ElectromagneticWavesEigenmodePort(
        name="Port 1",
        port_target=regions.port1,
        electromagnetic_waves_eigenmode_port_driving_signal="sn(1)",
        electromagnetic_waves_eigenmode_port_drive=True,
        electromagnetic_waves_eigenmode_port_num_eigenmodes="5",
        electromagnetic_waves_eigenmode_port_eigenmode_index="0",
        electromagnetic_waves_eigenmode_port_target_eigenvalue_type=(
            allsolve.ElectromagneticWavesEigenmodePortTargetEigenvalueType.EFFECTIVE_REFRACTIVE_INDEX
        ),
        electromagnetic_waves_eigenmode_port_effective_refractive_index="n_eff",  # project variable
    ),
    # Port 2: the same, with name="Port 2" and port_target=regions.port2
])
```

Full two-port model: `examples/geometric_sweep/control.py` (the model functions, including the ports and the sweep definition), run by `sweep.py`.

The `effective_refractive_index` value is geometry- and substrate-dependent. Define it as a project variable and compute it from your substrate permittivity (e.g. `n_eff ≈ sqrt((ε_r + 1)/2)` for a microstrip approximation). It is a search target, not a result: the solver returns the port mode nearest to it. Check the mode in the simulation log (see Simulation), and change `eigenmode_index` if a spurious mode is picked.

### Eigenmode port gotchas

- **`driving_signal`** must be a sinusoid at the fundamental frequency: `"sn(1)"` (default choice), `"cn(1)"`, or `"sin(2*pi*freq*t)"` with an optional phase. A constant such as `"1"` gives no excitation from that port: the field is zero and that port's S-parameter column is wrong, and the run still succeeds.
- **`target_eigenvalue_type`** defaults to `PROPAGATION_CONSTANT`. Supply the value that matches the type you choose (`…_propagation_constant` or `…_effective_refractive_index`), or the call raises `ValueError`.
- **`drive` only selects which ports excite the field output.** S-parameters are always computed by powering each port in turn, so the full S-matrix comes out whatever the drive flags are. One driven port is a sensible default; driving several is fine.
- Port target regions must be surface regions **contained within** the physics domain boundary. If a bounding-box region rule picks up surfaces outside the EM domain, intersect with the domain boundary (see Port regions below).
- **The mode solver already uses the physics' PEC.** `mode_pec` (optional) adds PEC for the mode calculation only. Use it when a conductor that should short the port's mode does not touch the port face, for example the vias of a grounded coplanar waveguide. When the port edges lie on PEC walls, it changes nothing. Other wall conditions (a boundary admittance, for example) do not reach the mode solver: put any port edge that lies on such a face in `mode_pec`, or the port picks a wrong mode and the run succeeds with near-total reflection.
- **The effective-index target picks among the propagating modes.** The port's eigen solver returns only modes that propagate at the drive frequency ("Found N modes …" in the log). With one propagating mode, the target hardly matters; with several (multi-conductor lines, overmoded guides), set it near the wanted mode.
- **"Below cutoff": the requested port mode does not propagate at the drive frequency.**
  - Eigenmode port: the log shows "Found 0 modes …" and the script fails with `IndexError: list index out of range` at `qs.alleigenport`. No mode of the port cross-section propagates at that frequency: the frequency is too low for this cross-section and material, or the port face is not the cross-section you meant.
  - Rectangular port: "cannot drive rectangular port mode te<m><n> below its cutoff frequency X Hz". The analytic mode (m, n) has its cutoff above the drive frequency. Either the frequency is too low, or (m, n) do not match the port's local axes: those come from three corner points of the face that the platform picks; see `<port name>_origin`, `<port name>_x` and `<port name>_y` in the generated `expressions.py` (`save_generated_scripts`), and count m along local x and n along local y.
- `ElectromagneticWavesRectangularPort` needs a rectangular face, uniform dielectric over it, and PEC on all four edges.

## Port regions

Port faces selected by bounding box may include surfaces outside the EM domain (e.g. outer enclosure faces at the same coordinate as the port plane). This causes: `Interaction "..." targets tags [...] that are outside its physics target region.`

Fix by intersecting the bounding-box rule with the domain boundary:

```python
em_domain = project.create_region_computed(
    name="em_domain",
    entity_type=allsolve.Region.VOLUME,
    operation=allsolve.RegionOperation.UNION,
    source_regions=[substrate.id, air.id],
)
em_boundary = project.create_region_computed(
    name="em_boundary",
    entity_type=allsolve.Region.SURFACE,
    operation=allsolve.RegionOperation.BOUNDARY,
    source_regions=[em_domain.id],
)

port1_all = project.create_region_rule(
    name="port1_all",
    entity_type=allsolve.Region.SURFACE,
    bounding_box=(port1_min, port1_max),
)
port1 = project.create_region_computed(
    name="port1",
    entity_type=allsolve.Region.SURFACE,
    operation=allsolve.RegionOperation.INTERSECTION,
    source_regions=[port1_all.id, em_boundary.id],
)
```

## Materials

EM simulations need `electric_permittivity`, `magnetic_permeability`, and `electric_conductivity` on every material region. Use `"epsilon0"` and `"mu0"` for free-space constants.

| Material | `electric_permittivity` | Notes |
|----------|------------------------|-------|
| Air / vacuum | `"epsilon0"` | |
| FR-4 substrate | `"4.4 * epsilon0"` | Add `ElectromagneticWavesDielectricLoss` for the loss tangent |
| Copper trace | `"epsilon0"` | Conductor; often modelled as PEC instead |

The conductor region (trace) needs a material assigned even if it is outside the EM physics domain, because the mesh covers it.

## Simulation

Use `create_simulation_harmonic` for frequency-domain S-parameter extraction:

```python
sim = project.create_simulation_harmonic(
    name="S-parameter sweep",
    description="...",
    max_run_time_minutes=120,
    solver_mode=allsolve.SolverMode.DIRECT,
    mesh=mesh.id,
    fundamental_frequency="freq",
    physics_set=physics_set,
)
```

Every harmonic run prints each port's modes (effective index, attenuation, phase constant) in the simulation log. To view the mode shapes, set `sim.eigenmode_port_analysis = True`; that run gives no S-parameters and no value outputs, so switch it off again. `create_simulation_eigenmode` finds cavity resonances, not port modes.

## Outputs

```python
sim.add_outputs([
    allsolve.Output.SParameters(name="S-parameters"),
    allsolve.Output.FieldOutput(
        name="E field (sin)",
        expression="harm(2, E)",
        field_output_skin_only=True,
    ),
])
```

- `Output.SParameters` writes two value columns, `<name> (magnitude)` in dB and `<name> (angle)` in degrees. Each holds the N×N S-matrix flattened row by row: S11, S12, …, S1N, S21, …, SNN (N² values; 4 for 2 ports, 9 for 3). Port k is the k-th port interaction of the physics in the order you added them, not by name (an `ElectromagneticWavesLumpVI` counts only in voltage or current mode); it is `var.E_port_regs[k-1]` in the script from `save_generated_scripts`.
- `harm(2, E)` gives the sine component of the electric field; `harm(3, E)` gives cosine.

## Mesh strategy

Full-wave EM meshes can be very large. Recommended approach:

1. **Start coarse:** raise `mesh_size_max` (λ/4) for the first run. `scale_factor` cannot coarsen beyond `mesh_size_max` or a refinement's `max_size`. Small models run on `CORES_1_16GB`; size the node by DOF (see mesh.md). Check that the simulation runs before you make the mesh finer.
2. **Set `mesh_size_max`** to about λ/6 (second-order elements, the default) at the highest frequency, **in the densest material**: λ = c0 / (f_max · sqrt(εr · μr)).
3. **Refine near traces and ports** with `MeshRefinement`. Read [mesh](../allsolve-sdk/references/mesh.md) for `use_mesh_refiner` and node sizing when you set up the mesh.

```python
import math

c0 = 3e8
f_max = 10e9  # highest sweep frequency in Hz
eps_r_max = 4.4  # largest εr·μr in the model
lambda_min = c0 / (f_max * math.sqrt(eps_r_max))  # shortest wavelength at the highest frequency

mesh = project.create_mesh(
    allsolve.MeshSettings(
        name="EM mesh",
        scale_factor=1.0,
        mesh_size_max=lambda_min / 6,
        max_run_time_minutes=30,
        refinements=[
            allsolve.MeshRefinement(region=regions.near_port, max_size=lambda_min / 20),
        ],
    )
)
```

Adapt `mesh_size_max`, `mesh_size_min`, and refinement sizes to your geometry — the values above are illustrative.

## Frequency sweeps

Use `create_variable_overrides` to sweep frequency (and optionally geometry parameters):

```python
sweep = project.create_variable_overrides(
    name="freq_sweep",
    sweep_type=allsolve.SweepType.CARTESIAN_PRODUCT,
    overrides=[
        ("freq", "linspace(f_start, f_end, N_freq)"),
    ],
)
```

Define `f_start`, `f_end` and `N_freq` as project variables. Pass `variable_overrides=sweep` to the simulation, and also to the mesh settings if the geometry changes. A sweep starts all points in parallel: run one frequency first (see [simulation](../allsolve-sdk/references/simulation.md#sweeps-and-parallel-runs)).

## Reference examples

- `examples/geometric_sweep/`: microstrip stub filter with eigenmode ports; Cartesian product sweep over stub length and frequency for S-parameter extraction.
- `examples/patch_antenna/`: microstrip patch antenna from a STEP file, air box with a box PML, lumped V/I port, radiation pattern, harmonic frequency sweep.

## Gotchas

- **MUMPS ICNTL(14) workaround for PML + direct solver:** PMLs cause too much fill-in (error -9). Inject `qs.universe.setmumpsicntl(14, N)` via `AFTER_FORMULATIONS_CREATED`. Default is 20; large PML problems may need ~200.
- **Known limitation: full-wave harmonic EM fails with MUMPS `INFOG(1)=-3` above about 1.5M DOF.** Observed in at least one large model; the cause is unconfirmed. `SolverMode.ITERATIVE` does not avoid it. For sub-wavelength coils, use magnetoquasistatic `MagnetismA` or analytic models.
- **Known limitation: multi-node DDM can leave boundary regions with an undefined interpolation order.** Fix it by injecting `fld.E.setorder(reg.all, 1)` at `AFTER_FIELDS_CREATED`. This lowers the element order everywhere: refine the mesh to keep accuracy (about λ/10–λ/15).
- **A harmonic field output `norm(field)` fails.** Use `norm(harm(2, E))` for the magnitude of one harmonic. Alternatively use `harmonicnorm([2, 3], E)`: the full amplitude, with the sin and cos parts combined.

Docs: eigenmode ports tutorial (`/documentation/tutorials/radio-frequency/rf-001-eigenmode-ports`), patch antenna tutorial (`/documentation/tutorials/radio-frequency/rf-003-patch-antenna`). More in [docs-map](../allsolve-sdk/references/docs-map.md).
