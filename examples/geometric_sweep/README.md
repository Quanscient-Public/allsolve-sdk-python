# Introduction

This example demonstrates a geometric parameter sweep for a microstrip stub filter
using the Quanscient Allsolve SDK. The entire project — geometry, mesh, materials,
physics, and simulation — is defined programmatically via the SDK, with no
GUI-created template required.

The filter stub length is a project variable referenced by the geometry. A single
**Cartesian product sweep** covers both frequency (21 points, 5–15 GHz) and stub
length (6 points), producing 126 solver jobs from one simulation. The server
automatically rebuilds geometry and mesh for each stub length. S₁₂ parameters are
then plotted as a function of frequency for each stub length.

## Project structure

| File | Purpose |
|------|---------|
| `sweep.py` | Main entry point — creates the project, runs the sweep, and stores the project for later visualization |
| `visualize_geometric_sweep.py` | Loads the finished project and plots S₁₂ vs frequency for each stub length |
| `control.py` | SDK setup helpers: project creation, variables, regions, materials, physics, Cartesian sweep, simulation |
| `geo.py` | Geometry building (`geometry_builder.add_box`) with parameterised stub length, and server-side meshing |

## Running

Create a `.env` file in the working directory:

```
ALLSOLVE_ACCESS_KEY=<your key id>
ALLSOLVE_SECRET_KEY=<your secret key>
```

Then run:

```bash
python sweep.py
```

Alternatively, export the variables directly:

```bash
# Linux / macOS
export ALLSOLVE_ACCESS_KEY=<your key id>
export ALLSOLVE_SECRET_KEY=<your secret key>

# Windows (PowerShell)
$env:ALLSOLVE_ACCESS_KEY="<your key id>"
$env:ALLSOLVE_SECRET_KEY="<your secret key>"
```

Then run:

```bash
python sweep.py
```

## Visualizing results

The visualization script requires additional dependencies:

```bash
pip install -r requirements.txt
python visualize_geometric_sweep.py
```
