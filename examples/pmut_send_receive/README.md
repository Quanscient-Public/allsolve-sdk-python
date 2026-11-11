# Introduction

This is a demo project for using the Quanscient Allsolve SDK to simulate
ultrasound send / receive between two PMUTs
(piezoelectric micromachined ultrasonic transducers) that face each other across a 5 mm water gap.
The pmut_send_receive.py script builds a transient 3D model with solid mechanics,
electrostatics with piezoelectricity, and acoustic waves.
One PMUT gets a 0.5 µs sin² voltage pulse and the other PMUT measures the voltage
on a floating electrode.
The script runs two simulations at the same time, one in each direction
("Bottom sends" and "Top sends"), and saves the value outputs to CSV files.

# Prerequisites

Follow [Installation](../README.md#installation) and [Running](../README.md#running)
in the parent example README to set up Python, install the Allsolve SDK,
and configure credentials.

# Running

From the `examples/` directory:

```
(venv) $ python pmut_send_receive/pmut_send_receive.py
```

Add `--quick` for a shorter run (end time 5 µs instead of 7 µs).

When prompted `Delete project? [Y/n]`, answer **`n`** if you plan to run the visualize
script below.

# Visualization

After the simulations have finished, install this example's dependencies and visualize the results:

```
(venv) $ pip install -r pmut_send_receive/requirements.txt
(venv) $ python pmut_send_receive/visualize_pmut_send_receive.py
```

The script reads the value outputs of both simulations and saves the drive and receive
voltages vs time to `output/pmut_send_receive.png`.
The receive voltage stays near zero until the acoustic pulse arrives after about
5 mm / 1480 m/s ≈ 3.4 µs.
To see the pressure wave front, add a Visualization of the `p` field output in the Allsolve web app.
