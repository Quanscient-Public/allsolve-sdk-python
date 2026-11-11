# Introduction

This is a demo project for using the Quanscient Allsolve SDK to simulate
a microstrip patch antenna — a flat metal radiator on a PCB substrate used
in Wi-Fi, GPS, and other radio applications.
The script builds substrate, feed line, quarter-wave transformer, and radiating
patch geometry, adds an air box, sets up electromagnetic waves physics,
and runs a harmonic frequency sweep.
The demo project is based on example case:
https://allsolve.quanscient.com/documentation/learn-by-doing/example-cases/radio-frequency/rf-003-patch-antenna

# Prerequisites

Follow [Installation](../README.md#installation) and [Running](../README.md#running)
in the parent example README to set up Python, install the Allsolve SDK,
and configure credentials.

# Geometry

The demo imports `patch_antenna.step` for the antenna CAD. A pre-built STEP file
is included in this directory.

If `patch_antenna.step` is missing, the demo builds it automatically using
[build123d](https://build123d.readthedocs.io/) via `build_patch_antenna_geometry.py`.
build123d is not in the shared `examples/requirements.txt`, so install it with
this example's dependencies first:

```
(venv) $ pip install -r patch_antenna/requirements.txt
```

You can also build the STEP file manually, for example after you change the
dimensions:

```
(venv) $ python patch_antenna/build_patch_antenna_geometry.py
```

The geometry builder creates labeled volumes for the dielectric substrate, 50-ohm
microstrip feed line, quarter-wavelength impedance transformer, radiating patch,
and a named port surface on the feed edge. The demo script adds a separate
air box around the antenna for the surrounding simulation domain. The project
variables `air_w`, `air_h` and `air_z` set the air box size and position, and
the simulation domain region uses the same variables in its bounding box.

# Running

From the `examples/` directory:

```
(venv) $ python patch_antenna/patch_antenna_demo.py
```

The script creates a new project named `Patch antenna demo`, runs the simulation,
and prompts to delete the project when finished.
When prompted `Delete project? [Y/n]`, answer **`n`** if you want to keep the
project and inspect S-parameters, the radiation pattern, and electric field
outputs in the Allsolve web UI.

# Visualizing results

After the simulation finishes (and you kept the project), plot the S-parameter
magnitude curve in dB locally:

```
(venv) $ python patch_antenna/visualize_patch_antenna.py
```

The script loads the project via `client.get_current_project()` (set by the demo
when you keep the project), plots |S11| in dB vs. frequency, marks the
resonance dip, and saves `output/s_parameter_magnitude.png` in this directory.
