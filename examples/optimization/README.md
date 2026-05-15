# Introduction

This is a demo project for using Quanscient Allsolve public API to do a simple
optimization.

Link to the demo:
https://allsolve.quanscient.com/#/projects/demo/d6e2f9f1-6e36-4db5-98a4-eea3443eb220

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

Make a copy of the demo to your own organization and check the project info to get
your API key and secret.

Then run

```
(venv) $ export QS_ACCESS_KEY=<your key id>
(venv) $ export QS_SECRET_KEY=<your secret key>
(venv) $ python optimizelsq.py
```

to execute your simulation via the API.

To run with Genetic algorithm (differential_evolution), run

```
(venv) $ python optimizede.py
```