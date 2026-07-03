# Introduction

This is a demo project for using the Quanscient Allsolve SDK to simulate
ultrasound emission from an array of PMUTs
(piezoelectric micromachined ultrasonic transducers).
By default the pmut_array_demo.py script creates a small 2x2 array of PMUTs.
(Adjust the array size by changing variable "n".)
The script saves the simulation output data to a CSV file and uses Matplotlib to generate a PNG plot.
The demo project is based on example case:
https://allsolve.quanscient.com/documentation/guides/example-cases/muts/muts-001-pmut-array

# Prerequisites

Follow [Installation](../README.md#installation) and [Running](../README.md#running)
in the parent example README to set up Python, install the Allsolve SDK,
and configure credentials.

# Running

From the `examples/` directory:

```
(venv) $ python pmut_array/pmut_array_demo.py
```

When prompted `Delete project? [Y/n]`, answer **`n`** if you plan to run the visualize
script below.

# Visualization

After the simulation has finished, install this example's dependencies and visualize the results:

```
(venv) $ pip install -r requirements.txt
(venv) $ python visualize_pmut_array_results.py
```

The script downloads result .vtu files and visualizes the simulation results
using pyvista. Results are saved under the `output/` directory.
