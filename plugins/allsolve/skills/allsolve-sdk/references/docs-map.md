# Allsolve docs map

This reference maps concepts to pages of the Allsolve documentation, so you can fetch the right page instead of browsing. The pages describe the web app (GUI), but the concepts and names match the SDK.

Docs paths are relative to the user's Allsolve host (`client.host`, from `ALLSOLVE_HOST`; default `https://allsolve.quanscient.com`). Open `<host>` + the path. All paths were checked against the site map (`/documentation/sitemap-0.xml`). For SDK names, prefer the SDK source; see the lookup table in [SKILL.md](../SKILL.md#documentation-lookup-fetch-and-grep).

## Reference

| Concept | Page |
|---|---|
| SDK classes, methods and kwargs (generated; can be several releases behind the installed package) | SDK reference (`/documentation/reference/allsolve-sdk`) |
| Solver script API (`qs.*`) | Script API (`/documentation/reference/api`) |
| Expression language, built-in variables and functions | Expressions (`/documentation/reference/expressions`) |
| SDK install, API keys, general concepts | Getting started (`/documentation/reference/public-api-getting-started`) |
| SDK capabilities and limitations | Introduction (`/documentation/reference/public-api-introduction`) |
| Script-based simulations (project layout) | Script-based simulations (`/documentation/reference/public-api-script-based`) |
| Release notes of the web app | Change log (`/documentation/change-log`) |

## Model setup

| Concept | Page |
|---|---|
| Geometry elements | Working with geometries (`/documentation/using-allsolve/geometries/working-with-geometries`) |
| STEP, GDSII, NASTRAN import | STEP (`/documentation/using-allsolve/geometries/file-imports/step`), GDSII (`/documentation/using-allsolve/geometries/file-imports/gdsii`), NASTRAN (`/documentation/using-allsolve/geometries/file-imports/nastran`) |
| Assembly names and paths (`attribute_path`) | Assemblies (`/documentation/using-allsolve/common/assemblies`) |
| Regions, entity tags | Regions → Entities & tags (`/documentation/using-allsolve/common/regions#entities--tags`) |
| Computed regions, boundary, boundary intersection | Regions → Computed region (`/documentation/using-allsolve/common/regions#computed-region`) |
| Rule selector (bounding box, min size, max size, attribute) | Regions → Rule selector (`/documentation/using-allsolve/common/regions#rule-selector`) |
| Variables and functions | Variables & functions (`/documentation/using-allsolve/common/variables-functions`) |
| Variable overrides, sweeps | Variable overrides (`/documentation/using-allsolve/common/variable-overrides`) |
| Materials, elasticity matrix, damping, material sweeps | Working with materials (`/documentation/using-allsolve/materials/working-with-materials`) |
| Piezoelectric material properties from impedance data | Piezo properties characterization (`/documentation/using-allsolve/materials/piezo-properties-generation`) |
| Shared library (scripts, materials) | Library (`/documentation/using-allsolve/library`) |

## Physics

| Concept | Page |
|---|---|
| Physics sets, adding physics, interactions and couplings | Working with physics (`/documentation/using-allsolve/physics/working-with-physics`) |
| Load expressions: `sin`, `sn()`/`cn()`, `wavelet`, ramps, pulses | Defining time-varying loads (`/documentation/using-allsolve/physics/load-expressions`) |
| Solid mechanics | Solid mechanics (`/documentation/using-allsolve/physics/solid-mechanics`) |
| Elastic waves, and how it differs from solid mechanics | Elastic waves → Elastic waves vs solid mechanics (`/documentation/using-allsolve/physics/elastic-waves#elastic-waves-vs-solid-mechanics`) |
| Voigt notation (elastic waves) | Elastic waves → Voigt notation (`/documentation/using-allsolve/physics/elastic-waves#voigt-notation`) |
| Acoustic waves, PML, absorbing boundary | Acoustic waves (`/documentation/using-allsolve/physics/acoustic-waves`) |
| Electrostatics | Electrostatics (v-formulation) (`/documentation/using-allsolve/physics/v-formulation-electrostatics`) |
| Current flow | Current flow (v-formulation) (`/documentation/using-allsolve/physics/v-formulation-current-flow`) |
| Electromagnetic waves | Electromagnetic waves (`/documentation/using-allsolve/physics/em-waves`) |
| Magnetism A, H, phi and H-phi formulations | A (`/documentation/using-allsolve/physics/a-formulation`), H (`/documentation/using-allsolve/physics/h-formulation`), phi (`/documentation/using-allsolve/physics/phi-formulation`), H-phi (`/documentation/using-allsolve/physics/hphi-equations`) |
| Heat transfer in solids and fluids | Solids (`/documentation/using-allsolve/physics/heat-solid`), fluids (`/documentation/using-allsolve/physics/heat-fluid`) |
| Laminar flow | Laminar flow (`/documentation/using-allsolve/physics/laminar-flow`) |

## Mesh and simulation

| Concept | Page |
|---|---|
| Mesh size settings, scale factor, curvature enhancement | Meshing → Mesh size settings (`/documentation/using-allsolve/simulations/meshing#mesh-size-settings`) |
| Mesh refinement, transfinite and autotransfinite meshing | Meshing → Customizations (`/documentation/using-allsolve/simulations/meshing#customizations`) |
| Mesh extrusion (simple, path, slanted) | Meshing → Mesh extrusion (`/documentation/using-allsolve/simulations/meshing#mesh-extrusion`) |
| Mesh element quality | Meshing → Mesh element quality (`/documentation/using-allsolve/simulations/meshing#mesh-element-quality`) |
| Mesh instances for sweeps | Meshing → Mesh instances (`/documentation/using-allsolve/simulations/meshing#mesh-instances`) |
| Analysis types, generalized alpha, timestep size | Simulations overview → Analysis types (`/documentation/using-allsolve/simulations/overview#analysis-types`) |
| Direct or iterative solver | Simulations overview → Solver settings (`/documentation/using-allsolve/simulations/overview#solver-settings`) |
| Field initialization (initial field state, transient state, H-phi state) | Inputs & outputs → Field initializations (`/documentation/using-allsolve/simulations/inputs-and-outputs#field-initializations`) |
| Chaining simulations | Inputs & outputs → Chaining (`/documentation/using-allsolve/simulations/inputs-and-outputs#chaining`) |
| Value outputs, field outputs, output filters, final field states | Inputs & outputs → Outputs (`/documentation/using-allsolve/simulations/inputs-and-outputs#outputs`) |
| Node type and count, timeout | Runtime settings (`/documentation/using-allsolve/simulations/runtime`) |
| Simulation scripts, script sections | Scripting (`/documentation/using-allsolve/simulations/scripting`) |
| Job logs | Logs (`/documentation/using-allsolve/simulations/logs`) |
| Result files, plots, visualizations | Results (`/documentation/using-allsolve/simulations/results`) |

## Tutorials

All tutorials: Overview (`/documentation/tutorials/00-overview`).

| Topic | Tutorial |
|---|---|
| Cantilever beam (static) | Bending of a cantilever beam (`/documentation/tutorials/solid-mechanics/cantilever-beam`) |
| MEMS comb drive: eigenmodes, static deflection | MEMS 001 (`/documentation/tutorials/mems/mems-001-combdrive-eigenmodes`), MEMS 002 (`/documentation/tutorials/mems/mems-002-combdrive-static-deflection`) |
| MEMS pull-in of an electrostatic actuator | Pull-in (`/documentation/tutorials/mems/mems-pull-in`) |
| Viscoelasticity | MEMS 003 (`/documentation/tutorials/mems/mems-003-viscoelasticity`) |
| PMUT unit cell, PMUT 11x11 array | Ultrasound 001 (`/documentation/tutorials/ultrasound/ultrasound-001-pmut-unit-cell`), Ultrasound 002 (`/documentation/tutorials/ultrasound/ultrasound-002-pmut-array-11x11`) |
| Piezocomposite transducer | Piezocomposite (`/documentation/tutorials/ultrasound/piezocomposite`) |
| Loudspeaker, SAW unit cell | Loudspeaker (`/documentation/tutorials/acoustics/loudspeaker-with-cabinet`), SAW (`/documentation/tutorials/acoustics/saw-unit-cell`) |
| Eigenmode ports, lumped ports, patch antenna | RF 001 (`/documentation/tutorials/radio-frequency/rf-001-eigenmode-ports`), RF 002 (`/documentation/tutorials/radio-frequency/rf-002-lumped-ports`), RF 003 (`/documentation/tutorials/radio-frequency/rf-003-patch-antenna`) |
| Heat transfer and conjugate heat transfer | NAFEMS 2D (`/documentation/tutorials/heat-transfer/nafems-2d-heat-transfer`), CHT 001 (`/documentation/tutorials/heat-transfer/cht-001-manifold-microchannel-heat-sink`), CHT 002 (`/documentation/tutorials/heat-transfer/cht-002-2d-taylor-couette-flow`) |
| Packaging warpage | Packaging 001 (`/documentation/tutorials/packaging/packaging-001-fcbga`) |
| Permanent magnets, electric motors | Permanent magnets (`/documentation/tutorials/magnetism/permanent-magnets`), PMSM (`/documentation/tutorials/electric-motors/pmsm`), EM 001 (`/documentation/tutorials/electric-motors/em-001-pmsm-2d`), EM 002 (`/documentation/tutorials/electric-motors/em-002-im-2d`) |
| Superconductors | SC 001 (`/documentation/tutorials/superconductors/sc-001-hts-tape-acloss`), SC 002 (`/documentation/tutorials/superconductors/sc-002-twisted-superconductor-acloss`), SC 003 (`/documentation/tutorials/superconductors/sc-003-quench`) |
| Harmonic balance | HB 001 (`/documentation/tutorials/harmonic-balance/hb-001-joule-heating`), HB 002 (`/documentation/tutorials/harmonic-balance/hb-002-backbone-curve`), HB 003 (`/documentation/tutorials/harmonic-balance/hb-003-microspeaker`) |

Other: FAQ (`/documentation/faq`).

<!-- Validated against the Allsolve documentation site map on 2026-10-27 -->
