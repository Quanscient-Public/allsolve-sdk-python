# Introduction

This is a demo project for using Quanscient Allsolve SDK to do a
eigenmode analysis for a MEMS comb-drive accelerometer.
The results are visualized using pyvista library.
The demo project is based on example case:
https://allsolve.quanscient.com/documentation/guides/example-cases/mems/mems-001-combdrive-eigenmodes

# Prerequisites

Follow [Installation](../README.md#installation) and [Running](../README.md#running)
in the parent example README to set up Python, install the Allsolve SDK,
and configure credentials.

# Running

From the `examples/` directory:

```
(venv) $ python combdrive_eigenmodes/combdrive_eigenmodes.py
```

When prompted `Delete project? [Y/n]`, answer **`n`** if you plan to run the visualize
script below.

# Visualization

After running the simulation, install this example's dependencies and run the visualization script:

```
(venv) $ pip install -r requirements.txt
(venv) $ python visualize_combdrive_eigenmodes.py --interactive
```
