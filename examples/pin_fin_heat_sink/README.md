# Introduction

This is a demo project for using Quanscient Allsolve SDK to do a simplified
simulation for a pin fin heat sink.

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
(venv) $ python heat_sink_demo.py
```

Optionally you can create .env file and copy the key and secret there.

.env file:

```
ALLSOLVE_ACCESS_KEY=<your key id>
ALLSOLVE_SECRET_KEY=<your secret key>
```

Then run the script:

```
(venv) $ python heat_sink_demo.py
```
