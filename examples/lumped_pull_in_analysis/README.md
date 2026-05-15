# Introduction

This is a demo project for using the Quanscient Allsolve SDK to simulate
lumped pull-in behavior of a parallel-plate MEMS actuator with spring coupling.
The script builds coupled electrostatic–mechanical physics, runs a DC voltage
sweep, and saves comparison outputs (simulated vs theoretical deflection,
pull-in quantities).

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
(venv) $ python lumped_pull_in_analysis.py
```

Optionally you can create .env file and copy the key and secret there.

.env file:

```
ALLSOLVE_ACCESS_KEY=<your key id>
ALLSOLVE_SECRET_KEY=<your secret key>
```

Then run the script:

```
(venv) $ python lumped_pull_in_analysis.py
```

# Visualization

After the simulation has finished, you can visualize the results by running:

```
(venv) $ python visualize_pull_in_results.py
```

The script reads outputs from the project simulation and saves plots under the
`output/` directory (`pull_in_analysis.png` and `pull_in_bar_comparison.png`).
