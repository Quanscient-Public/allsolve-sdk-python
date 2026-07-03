# Introduction

This is a demo project for using the Quanscient Allsolve SDK to simulate
lumped pull-in behavior of a parallel-plate MEMS actuator with spring coupling.
The script builds coupled electrostatic–mechanical physics, runs a DC voltage
sweep, and saves comparison outputs (simulated vs theoretical deflection,
pull-in quantities).

# Prerequisites

Follow [Installation](../README.md#installation) and [Running](../README.md#running)
in the parent example README to set up Python, install the Allsolve SDK,
and configure credentials.

# Running

From the `examples/` directory:

```
(venv) $ python lumped_pull_in_analysis/lumped_pull_in_analysis.py
```

When prompted `Delete project? [Y/n]`, answer **`n`** if you plan to run the visualize
script below.

# Visualization

After the simulation has finished, install this example's dependencies and visualize the results:

```
(venv) $ pip install -r requirements.txt
(venv) $ python visualize_pull_in_results.py
```

The script reads outputs from the project simulation and saves plots under the
`output/` directory (`pull_in_analysis.png` and `pull_in_bar_comparison.png`).
