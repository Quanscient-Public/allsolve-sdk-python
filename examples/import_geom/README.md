# Introduction

This is an example for creating a project, importing a SAT file, creating regions with
attribute names, meshing and running the simulation.

Note that this is not runnable without appropriate `heat.sat` file, which has the CAD
attributes used to create the regions. Regardless, this can be used as an example to
see how you can import your own geometries with their own CAD attributes.

# Prerequisites

Follow [Installation](../README.md#installation) and [Running](../README.md#running)
in the parent example README to set up Python, install the Allsolve SDK,
and configure credentials.

# Running

From the `example/` directory:

```
(venv) $ python import_geom/main.py
```
