# Introduction

This is a full script simulation for acoustics using Quanscient Allsolve public API,
where you provide the mesh yourself.

# Installation

You need to have python3 and virtualenv module "venv" installed. Copy the allsolve
wheel package to the working directory. Then, create a new virtualenv and install
the dependencies with the following:

```
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
```

# Running

Create a pure script project in Allsolve, and add one simulation to it. Then go back
to the projects overview, and check the project info to get your API key and secret.
Then run

```
(venv) $ export QS_ACCESS_KEY=<your key id>
(venv) $ export QS_SECRET_KEY=<your secret key>
(venv) $ python main.py
```

to execute your simulation via the API.
