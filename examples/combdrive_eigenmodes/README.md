# Introduction

This is a demo project for using Quanscient Allsolve SDK to do a
eigenmode analysis for a MEMS comb-drive accelerometer.
The results are visualized using pyvista library.
The demo project is based on example case:
https://allsolve.quanscient.com/documentation/guides/example-cases/mems/mems-001-combdrive-eigenmodes

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
(venv) $ python combdrive_eigenmodes.py
```

Optionally you can create .env file and copy the key and secret there.

.env file:

```
ALLSOLVE_ACCESS_KEY=<your key id>
ALLSOLVE_SECRET_KEY=<your secret key>
```

Then run the script:

```
(venv) $ python combdrive_eigenmodes.py
```

After running the simulation you can also run the visualization script in interactive mode:

```
(venv) $ python visualize_combdrive_eigenmodes.py --interactive
```
