# Introduction

This is a demo project for using the Quanscient Allsolve SDK to simulate a
single CMUT (capacitive micromachined ultrasonic transducer) cell in receive
mode. A CMUT is a thin membrane above a vacuum gap. A DC bias voltage pulls the
membrane towards the substrate. An ultrasound pulse arriving through water
then moves the biased membrane, which changes the charge on the electrodes.

The model is a quarter of one cell in an array:

    1. A polysilicon substrate (the bias electrode is its top face)
    2. An oxide layer with a recessed vacuum gap
    3. A polysilicon membrane (grounded underside)
    4. A water column with an absorbing boundary on top

The script CMUT_single_cell_rx.py couples solid mechanics, electrostatics,
mesh deformation and acoustic waves, and runs three simulations:

    1. **Static DC bias** at 160 V. It saves the final displacement, potential
       and mesh deformation fields as field states.
    2. **Static DC bias sweep** from 1 V to 186 V (50 points).
    3. **Transient** of 10 cycles at 6.5 MHz with the generalized-alpha time
       stepping, initialized from the static field states. A wavelet pulse
       in the water travels to the membrane.

The example shows these SDK techniques:

- A static simulation feeding a transient through `Output.FieldState` and
  `FieldInitialization` with `FieldInitializationType.FIELDSTATE`
- Interface faces (electrodes, membrane front face) from region operations:
  `INTERSECTION` of the `BOUNDARY` regions of two volumes
- Symmetry faces from bounding-box region rules
- `MeshExtrusion` with `sub_layer_counts` for a layered geometry
- `TimestepAlgorithm.GEN_ALPHA`
- Two simulations run in parallel with `allsolve.run_simulations()`

The model is based on a simplified version of a CMUT cell from DTU Nanotech.

# Prerequisites

Follow [Installation](../README.md#installation) and [Running](../README.md#running)
in the parent example README to set up Python, install the Allsolve SDK,
and configure credentials.

# Running

From the `examples/` directory:

```
(venv) $ python cmut/CMUT_single_cell_rx.py
```

The script saves the value outputs of the three simulations as CSV files under
the `output/` directory.

When prompted `Delete project? [Y/n]`, answer **`n`** if you plan to run the visualize
script below.

# Visualization

After the simulation has finished, install this example's dependencies and visualize the results:

```
(venv) $ pip install -r requirements.txt
(venv) $ python visualize_cmut_results.py
```

The script reads outputs from the project simulations and saves plots under the
`output/` directory (`cmut_bias_sweep.png` and `cmut_transient.png`).
