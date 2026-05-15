# Introduction

This is a demo project for using the Quanscient Allsolve SDK to simulate
ultrasound emission from an array of PMUTs
(piezoelectric micromachined ultrasonic transducers).
By default the pmut_array_demo.py script creates a small 2x2 array of PMUTs.
(Adjust the array size by changing variable "n".)
The script saves the simulation output data to a CSV file and uses Matplotlib to generate a PNG plot.
The demo project is based on example case:
https://allsolve.quanscient.com/documentation/guides/example-cases/muts/muts-001-pmut-array

# Installation

You need to have python3 and virtualenv module "venv" installed. Copy the allsolve
wheel package to the working directory. Then, create a new virtualenv and install
the dependencies with the following:

```
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -U pip
(venv) $ pip install -r requirements.txt
```

# Running

Create Organization API key via Allsolve web UI.
Use "Create key" action from "Settings" / "Organization" / "API keys" menu.

Then run:

```
(venv) $ export ALLSOLVE_ACCESS_KEY=<your key id>
(venv) $ export ALLSOLVE_SECRET_KEY=<your secret key>
(venv) $ python pmut_array_demo.py
```

Optionally you can create .env file and copy the key and secret there.

.env file:

```
ALLSOLVE_ACCESS_KEY=<your key id>
ALLSOLVE_SECRET_KEY=<your secret key>
```

Then run the script:

```
(venv) $ python pmut_array_demo.py
```

# Visualization

After the simulation has finished, you can visualize the results by running:

```
(venv) $ python visualize_pmut_array_results.py
```

The script downloads result .vtu files and visualizes the simulation results
using pyvista. Results are saved under the `output/` directory.
