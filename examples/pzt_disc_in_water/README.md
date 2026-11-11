# Introduction

This is a demo project for using the Quanscient Allsolve SDK to calculate the
electrical impedance of a thickness-poled PZT disc (Ø 40 mm × 5 mm) that
radiates into water. The water is a sphere of radius `R_water = R_disc + t_water`
(25 mm) with an AML type PML on its curved outer surface.

The script `pzt_disc_in_water.py` models one octant of the device (1/8 symmetry),
runs a harmonic simulation at 404 kHz and then a frequency sweep from 312 kHz to
512 kHz in 2 kHz steps (101 points). It saves the value outputs to CSV files.

The symmetry faces and the electrode faces are selected with region rules
written with the project variables, so you can change the dimensions without
fixing entity tags. The script checks the entity count of each region after
the geometry is built.

# Symmetry model and impedance scaling

- On the planes x = 0, y = 0 and z = 0 the normal displacement is zero
  (symmetry interaction). Zero normal electric flux and zero normal pressure
  gradient are the natural boundary conditions, so they need no interaction.
- The full disc has +V0/2 on the top electrode and -V0/2 on the bottom
  electrode, so the mid-plane z = 0 is at 0 V. The octant model drives the top
  electrode with `V0/2*sn(1)`.
- The lump voltage is half of the full-disc voltage (`V_scale = 2`), and the
  octant electrode carries a quarter of the full-disc current (`I_scale = 4`).
  The outputs `Z real`, `Z imag` and `Z abs` are for the full disc:
  `Z_full = (V_scale * V_lump) / (I_scale * I_lump)`.

# Phasor convention

A harmonic simulation solves harmonics 2 and 3 of the fundamental frequency:
`x(t) = harm(2, x)*sin(wt) + harm(3, x)*cos(wt)`. The complex amplitude is
`X = harm(3, x) - j*harm(2, x)`. The project functions `z_re` and `z_im`
compute the real and imaginary parts of V/I from these components. The current
into the electrode is `dt(lump.Q)`.

# Prerequisites

Follow [Installation](../README.md#installation) and [Running](../README.md#running)
in the parent example README to set up Python, install the Allsolve SDK,
and configure credentials.

# Running

From the `examples/` directory:

```
(venv) $ python pzt_disc_in_water/pzt_disc_in_water.py
```

The full run uses a 1 mm mesh and runs the 101 sweep frequencies in parallel.
For a quick smoke test with a coarse 2 mm mesh and a 3-point sweep, add `--quick`:

```
(venv) $ python pzt_disc_in_water/pzt_disc_in_water.py --quick
```

When prompted `Delete project? [Y/n]`, answer **`n`** if you plan to run the visualize
script below.

The results are saved to `output/pzt_disc_single_frequency.csv` and
`output/pzt_disc_sweep.csv`. With the 1 mm mesh, |Z| at 404 kHz is about 41 Ω.

# Visualization

After the simulation has finished, install this example's dependencies and visualize the results:

```
(venv) $ pip install -r requirements.txt
(venv) $ python visualize_pzt_disc_results.py
```

The script plots |Z| and the phase against frequency (`output/pzt_disc_impedance.png`).
It also downloads the pressure field files in VTKHDF format (.hdf) and plots the
pressure amplitude in the xz plane (`output/pzt_disc_pressure.png`).
