# Introduction

This folder contains examples for Quanscient Allsolve SDK.
See specific example READMEs for more details.

# Installation

You need to have Python 3.10 or newer and the virtualenv module "venv" installed.
Create a new virtualenv and install the Allsolve SDK:

```
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install allsolve
```

# Running

Create an Organization API key in the Allsolve web UI:

**Settings > API keys > "Create key"**

Copy the example environment file and fill in your credentials:

```
cp .env.default .env
```

Then edit `.env` with `ALLSOLVE_ACCESS_KEY` and `ALLSOLVE_SECRET_KEY` (see `.env.default`).

> **Security:** Never commit your `.env` file or hardcode API credentials in scripts.
> The `.env` file is already in `.gitignore`. Always use environment variables or
> `.env` files for credential management.

You can optionally use hello_world example for creating the `.env` file.

```
(venv) $ python hello_world/hello_world.py
```

After that you can try running some other example.

# Examples

## Client API examples (recommended)

These examples define simulations entirely through the SDK.
The client handles project creation, geometry, physics setup, meshing,
and result retrieval without writing separate simulation scripts.

| Example                          | Description                                                                     |
| -------------------------------- | ------------------------------------------------------------------------------- |
| `hello_world/`                   | Authentication and project creation                                             |
| `bending_beam/`                  | Structural simulation, parameter sweeps, YAML-based setup, result visualization |
| `combdrive_eigenmodes/`          | MEMS eigenmode analysis with GDSII geometry import                              |
| `pin_fin_heat_sink/`             | Conjugate heat transfer simulation                                              |
| `pmut_array/`                    | PMUT array (n×n) harmonic sweep in air, frequency response, MP4 pressure video  |
| `lumped_pull_in_analysis/`       | Lumped parallel-plate electrostatic-mechanical pull-in (voltage sweep, plots)   |
| `pmut_send_receive/`             | Transient piezo PMUT send/receive in water, floating electrode, parallel runs   |
| `pzt_disc_in_water/`             | Piezo impedance of a PZT disc in water: 1/8 symmetry, AML PML, harmonic sweep   |
| `cmut/`                          | CMUT receive mode: static DC bias, then transient started from its field state  |
| `geometric_sweep/`               | Microstrip stub filter with Cartesian product sweep over geometry and frequency |
| `twisted_superconductor_acloss/` | AC loss in twisted HTS wire (H-φ formulation, custom YBCO Newton linearization) |
| `patch_antenna/`                 | RF patch antenna harmonic sweep, lumped port and S11, build123d STEP geometry   |
| `pmut_surrogate/`                | PMUT surrogate-assisted Pareto optimization (GP + NSGA-II), YAML project import |

### Find an example by technique

Search this table, or search the example scripts for an SDK name, for example
`grep -rl GEN_ALPHA */*.py`. Each example's module docstring lists what it demonstrates.

| Technique                                                    | Examples                                                             |
| ------------------------------------------------------------ | -------------------------------------------------------------------- |
| Static (`create_simulation_static`)                          | `bending_beam`, `lumped_pull_in_analysis`, `cmut`                    |
| Harmonic (`create_simulation_harmonic`)                      | `pmut_array`, `pzt_disc_in_water`, `patch_antenna`, `geometric_sweep` |
| Transient, `TimestepAlgorithm.IMPLICIT_EULER`                | `pin_fin_heat_sink`, `twisted_superconductor_acloss`                 |
| Transient, `TimestepAlgorithm.GEN_ALPHA` (wave and mechanics) | `pmut_send_receive`, `cmut`                                          |
| Eigenmode (`create_simulation_eigenmode`)                    | `combdrive_eigenmodes`                                               |
| Start from another simulation (`FieldInitialization`)        | `lumped_pull_in_analysis`, `cmut`                                    |
| Parametric sweep (`create_variable_overrides`)               | `bending_beam`, `pzt_disc_in_water`, `pmut_array`, `patch_antenna`, `cmut`, `lumped_pull_in_analysis`, `geometric_sweep`, `pmut_surrogate` |
| Run several simulations without blocking (`start()`, `is_running(refresh_delay_s=...)`) | `pmut_send_receive`, `cmut`                 |
| Piezoelectric coupling                                       | `pmut_send_receive`, `pzt_disc_in_water`, `pmut_array`               |
| Acoustic-structure coupling and acoustic PML                 | `pmut_send_receive`, `pzt_disc_in_water`, `pmut_array`, `cmut`       |
| Floating electrode (`ElectrostaticsLump` in charge mode)     | `pmut_send_receive`                                                  |
| Lumped port and S-parameters (`ElectromagneticWavesLumpVI`, `SParameters`) | `patch_antenna`, `geometric_sweep`                     |
| Electrostatic force with a moving mesh (`LargeDisplacement`) | `lumped_pull_in_analysis`, `cmut`                                    |
| Symmetry model and symmetry faces                            | `pzt_disc_in_water`, `cmut`                                          |
| Interface faces (`RegionOperation.BOUNDARY`, `INTERSECTION`) | `cmut`                                                               |
| Select by name (`attribute_path`)                            | `pmut_array`, `combdrive_eigenmodes`, `patch_antenna`, `cmut`        |
| Layered mesh (`MeshExtrusion`)                               | `cmut`, `lumped_pull_in_analysis`, `combdrive_eigenmodes`            |
| STEP or GDSII import                                         | `import_geom`, `patch_antenna`, `twisted_superconductor_acloss`, `combdrive_eigenmodes` |
| Project YAML import and export                               | `import_project`, `bending_beam`, `edit_project`, `pmut_surrogate`   |
| Optimization and surrogate models                            | `pmut_surrogate`, `surrogate_model`, `optimization`                  |
| Resource reservation                                         | `resource_reservation`                                               |
| Plots of value outputs (matplotlib)                          | `bending_beam`, `pmut_array`, `pzt_disc_in_water`, `pmut_send_receive`, `cmut`, `lumped_pull_in_analysis`, `patch_antenna`, `geometric_sweep`, `pmut_surrogate` |
| 3D field plots from downloaded field files (pyvista)         | `combdrive_eigenmodes`, `pin_fin_heat_sink`, `pmut_array`, `pzt_disc_in_water` |
| Animations (GIF, MP4)                                        | `combdrive_eigenmodes` (GIF of each eigenmode), `pmut_array` (MP4 of the pressure field) |

Examples that produce results have a `visualize_*.py` script that reads the outputs and
saves plots with matplotlib or pyvista. Install its `requirements.txt` first.

Run example:

```
(venv) $ python bending_beam/bending_beam_sweep.py
```

The script bending_beam_sweep.py creates a new project to Allsolve and runs the simulation.
You can then view the project and the simulation results in Allsolve GUI.
When it finishes, answer **`n`** at the `Delete project? [Y/n]` prompt if you want to
keep the project and visualize results with the SDK script below.
The result visualization via SDK requires installing some dependency libraries.
To install the dependencies and visualize results, run:

```
(venv) $ pip install -r bending_beam/requirements.txt
(venv) $ python bending_beam/visualize_bending_beam_sweep_results.py
```

Each example follows the same pattern: running the simulation requires only the
Allsolve SDK, but processing the results may require additional dependencies listed in
the example's `requirements.txt`.

Optionally, you can install all example dependencies at once:

```
(venv) $ pip install -r requirements.txt
```

## Script-based examples (legacy)

These examples manage projects that contain user-written simulation scripts. The scripts are
uploaded to the simulation worker and control the solver directly.

| Example                 | Description                                      |
| ----------------------- | ------------------------------------------------ |
| `full_script_template/` | Template for script-based simulations            |
| `simple_sweep/`         | Parameter sweep with simulation scripts          |
| `optimization/`         | Optimization using scipy with simulation scripts |
| `import_project/`       | Import a project from YAML                       |
| `import_geom/`          | Import geometry and mesh files                   |
| `permanent_magnet/`     | Permanent magnet simulation                      |

## Other examples

| Example                 | Description                                                             |
| ----------------------- | ----------------------------------------------------------------------- |
| `surrogate_model/`      | Neural-network surrogate training workflow for a simulation             |
| `edit_project/`         | Modify a project using YAML files while viewing it in the GUI           |
| `resource_reservation/` | Reserve cloud compute up front and reuse it across mesh/simulation jobs |
