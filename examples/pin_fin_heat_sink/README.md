# Introduction

This is a demo project for using Quanscient Allsolve SDK to do a simplified
simulation for a pin fin heat sink.

# Prerequisites

Follow [Installation](../README.md#installation) and [Running](../README.md#running)
in the parent example README to set up Python, install the Allsolve SDK,
and configure credentials.

# Running

From the `examples/` directory:

```
(venv) $ python pin_fin_heat_sink/heat_sink_demo.py
```

When prompted `Delete project? [Y/n]`, answer **`n`** if you plan to run the visualize
script below.

# Visualization

After the simulation has finished, install this example's dependencies and visualize the results:

```
(venv) $ pip install -r pin_fin_heat_sink/requirements.txt
(venv) $ python pin_fin_heat_sink/visualize_heat_sink.py
```

The script saves a PNG image of each timestep to `pin_fin_heat_sink/output/images`.
Use `--interactive` for an interactive pyvista window.

**Note:** On the first run, the script downloads the temperature field of all
10 timesteps (about 360 MB) to `pin_fin_heat_sink/output/results`. Later runs
use these files. Delete the `output` folder to free the disk space.
