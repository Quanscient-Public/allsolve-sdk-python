# Introduction

This is a demo project for using Quanscient Allsolve public API to do a simple
optimization.

Link to the demo:
https://allsolve.quanscient.com/#/projects/demo/d6e2f9f1-6e36-4db5-98a4-eea3443eb220

# Prerequisites

Follow [Installation](../README.md#installation) and [Running](../README.md#running)
in the parent example README to set up Python, install the Allsolve SDK,
and configure credentials.

This example also requires additional dependencies (scipy, matplotlib):

```
(venv) $ pip install -r requirements.txt
```

# Running

Make a copy of the demo to your own organization and check the project info to get
your API key and secret.

From the `examples/` directory:

```
(venv) $ python optimization/optimizelsq.py
```

To run with a genetic algorithm (differential_evolution):

```
(venv) $ python optimization/optimizede.py
```
