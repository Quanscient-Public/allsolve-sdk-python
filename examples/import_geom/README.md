# Introduction

This is an example for creating a project, importing a SAT file, creating regions with
attribute names, meshing and running the simulation.

Note that this is not runnable without appropriate `heat.sat` file, which has the CAD
attributes used to create the regions. Regardless, this can be used as an example to
see how you can import your own geometries with their own CAD attributes.

# Running

Create an organization key for your user via settings->organization->API keys.

Then run

```
(venv) $ export QS_ACCESS_KEY=<your key id>
(venv) $ export QS_SECRET_KEY=<your secret key>
(venv) $ python main.py
```

to execute your simulation via the API.
