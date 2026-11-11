# Introduction

This is a demo project for using the Quanscient Allsolve SDK to run a
surrogate-assisted multi-objective optimisation for a circular single-cell
Piezoelectric Micromachined Ultrasonic Transducer (PMUT) with infinite symmetry
and water load.

The example demonstrates using the **Allsolve SDK** together with popular
Python libraries — **scikit-learn**, **pymoo** and **matplotlib**.
The entire workflow lives in a single script (`pareto_front.py`),
making it easy to follow and adapt.

## Workflow

1. **Import** the PMUT project from `pmut_surrogate.yaml` into the Allsolve cloud.
2. **Sample** the design space with a Latin Hypercube DOE (scipy).
3. **Run** cloud simulations for every DOE point in one sweep via the SDK.
4. **Fit** a Gaussian Process surrogate per output (scikit-learn `GaussianProcessRegressor`).
5. **Enrich** adaptively — for each of 2 rounds: select the most uncertain
   candidates (sigma-based infill from 5 000 uniform samples), simulate them,
   and re-fit the GPs with the expanded dataset.
6. **Optimise** with NSGA-II on the surrogates (pymoo), maximising `tx_max` and
   `fbw` while constraining the centre frequency `fc` to 12 MHz ±1 %.
7. **Validate** the Pareto-optimal designs at full fidelity (with full
   frequency-response curves).
8. **Save** all artefacts — DOE dataset, Pareto front, and validation results
   — as `.csv` files under `output/data/`.
9. **Plot** the resulting Pareto front.

# Prerequisites

Follow [Installation](../README.md#installation) and [Running](../README.md#running)
in the parent example README to set up Python, install the Allsolve SDK,
and configure credentials.

# Running

From the `examples/` directory:

```
(venv) $ pip install -r pmut_surrogate/requirements.txt
(venv) $ python pmut_surrogate/pareto_front.py
```

The script creates a new cloud project, runs the full pipeline (DOE →
surrogate → adaptive enrichment → optimisation → validation), and saves
results under `output/data/`. At the end it asks whether to delete the project.

When prompted `Delete project? [Y/n]`, answer **`n`** if you plan to run the
plot script below.

# Visualization

After the simulation has finished, visualize the results:

```
(venv) $ python pmut_surrogate/plot_results.py
```

# Files

| File | Description |
|---|---|
| `pareto_front.py` | Main script — DOE, simulation, GP fitting, adaptive enrichment, NSGA-II, validation, plotting |
| `plot_results.py` | Post-processing plots from saved artefacts |
| `pmut_surrogate.yaml` | Exported Allsolve project (geometry, physics, mesh, simulation) |
| `scripts/postprocessing.py` | Custom solver script injected at the `afterAll` section — time-stepping, FFT, KPI extraction |
| `output/data/` | Data directory (created at runtime): `dataset.csv`, `pareto.csv`, `validation.csv` |
| `output/figures/` | Generated plots: `pareto_front.png`, `validation.png`, `validation_freq.png` |
