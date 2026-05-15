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

| Example                    | Description                                                                     |
| -------------------------- | ------------------------------------------------------------------------------- |
| `hello_world/`             | Authentication and project creation                                             |
| `bending_beam/`            | Structural simulation, parameter sweeps, YAML-based setup, result visualization |
| `combdrive_eigenmodes/`    | MEMS eigenmode analysis with GDSII geometry import                              |
| `pin_fin_heat_sink/`       | Conjugate heat transfer simulation                                              |
| `pmut_array/`              | Piezoelectric MEMS array simulation                                             |
| `lumped_pull_in_analysis/` | Lumped parallel-plate electrostatic-mechanical pull-in (voltage sweep, plots)   |
| `geometric_sweep/`         | Microstrip stub filter with Cartesian product sweep over geometry and frequency |

Run example:

```
(venv) $ python bending_beam/bending_beam_sweep.py
```

The script bending_beam_sweep.py creates a new project to Allsolve and runs the simulation.
You can then view the project and the simulation results in Allsolve GUI.
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

| Example            | Description                                                   |
| ------------------ | ------------------------------------------------------------- |
| `surrogate_model/` | Neural-network surrogate training workflow for a simulation   |
| `edit_project/`    | Modify a project using YAML files while viewing it in the GUI |
