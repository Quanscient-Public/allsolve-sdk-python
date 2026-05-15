# Introduction

This is an example of running a demo project using Quanscient Allsolve public API
for a full GUI project, using the mesh etc. all created there.

The included `sim/main.py` is just the auto-generated simulation script without
modifications, but you could add your modifications there.

Link to the demo:
https://allsolve.quanscient.com/#/projects/demo/617a79e1-a45e-4859-acf6-b13029889bb9

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
(venv) $ python main.py
```

to execute your simulation via the API.
