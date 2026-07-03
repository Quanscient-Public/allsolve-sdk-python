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
(venv) $ pip install -r requirements.txt
(venv) $ python visualize_heat_sink.py
```

Use `--interactive` for an interactive pyvista window.
