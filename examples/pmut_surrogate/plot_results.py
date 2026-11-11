"""
Post-processing plots for the PMUT surrogate optimisation demo.

Reads the artefacts produced by ``pareto_front.py`` (under ``output/data/``) and
generates:

    output/figures/pareto_front.png    training data + predicted Pareto front
    output/figures/validation.png      predicted front vs. high-fidelity sims
    output/figures/validation_freq.png frequency-response overlay of validated designs

Run after a successful ``pareto_front.py`` execution::

    python plot_results.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output"
DATA = OUTPUT / "data"
FIGS = OUTPUT / "figures"
FIGS.mkdir(parents=True, exist_ok=True)


def _read_header(path):
    """Return column names from the first line of a CSV."""
    with open(path) as f:
        return f.readline().strip().split(",")


def _load():
    header = _read_header(DATA / "dataset.csv")
    col_tx = header.index("tx_max")
    col_fbw = header.index("fbw")

    dataset = np.loadtxt(DATA / "dataset.csv", delimiter=",", skiprows=1)
    pareto = np.loadtxt(DATA / "pareto.csv", delimiter=",", skiprows=1)
    valid = np.loadtxt(DATA / "validation.csv", delimiter=",", skiprows=1)

    archive = np.load(DATA / "freq_response.npz", allow_pickle=True)
    n_initial = int(archive["n_initial"])

    return dataset, pareto, valid, n_initial, col_tx, col_fbw


def _load_freq():
    """Load the per-design frequency-response curves from the NPZ archive."""
    path = DATA / "freq_response.npz"
    if not path.exists():
        return None, None
    archive = np.load(path, allow_pickle=True)
    n = int(archive["n_designs"])
    freqs = [archive[f"freq_{i}"] for i in range(n)]
    tx_mags = [archive[f"txmag_{i}"] for i in range(n)]
    return freqs, tx_mags


def plot_pareto_front(dataset, pareto, n_initial, col_tx, col_fbw, save_path):
    """Training samples split by batch, with the predicted Pareto overlay."""
    initial = dataset[:n_initial]
    adaptive = dataset[n_initial:]

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.scatter(
        initial[:, col_fbw],
        initial[:, col_tx],
        s=14,
        alpha=0.6,
        color="steelblue",
        label=f"Initial DOE (n={len(initial)})",
    )
    ax.scatter(
        adaptive[:, col_fbw],
        adaptive[:, col_tx],
        s=50,
        marker="s",
        facecolors="none",
        edgecolors="darkorange",
        linewidths=1.1,
        label=f"Adaptive infill (n={len(adaptive)})",
    )
    ax.scatter(
        pareto[:, col_fbw],
        pareto[:, col_tx],
        s=14,
        color="red",
        alpha=0.6,
        label=f"Pareto front (n={len(pareto)})",
    )

    ax.set_xlabel("fbw  (fractional bandwidth, %)")
    ax.set_ylabel("tx_max  (transmit sensitivity)")
    ax.set_title(
        f"PMUT Pareto Front — sklearn GP + pymoo NSGA-II  "
        f"({len(dataset)} training pts)"
    )
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"  Saved → {save_path}")


def plot_validation(dataset, pareto, valid, col_tx, col_fbw, save_path):
    """Overlay training data, predicted Pareto front and HF validation."""
    fig, ax = plt.subplots(figsize=(10, 7))

    ax.scatter(
        dataset[:, col_fbw],
        dataset[:, col_tx],
        s=6,
        alpha=0.2,
        color="grey",
        label=f"Training data (n={len(dataset)})",
    )
    ax.scatter(
        pareto[:, col_fbw],
        pareto[:, col_tx],
        s=18,
        color="red",
        label="Pareto front (surrogate)",
    )
    ax.scatter(
        valid[:, col_fbw],
        valid[:, col_tx],
        s=18,
        marker="x",
        color="green",
        label="Pareto front (validated)",
    )

    ax.set_xlabel("fbw  (fractional bandwidth, %)")
    ax.set_ylabel("tx_max  (transmit sensitivity)")
    ax.set_title("PMUT validation — surrogate prediction vs. simulation")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"  Saved → {save_path}")


def plot_freq_response(freqs, tx_mags, save_path):
    """Overlay the high-fidelity frequency-response curves of all validated
    Pareto designs — the hallmark PMUT plot."""
    fig, ax = plt.subplots(figsize=(10, 6))

    for freq, txmag in zip(freqs, tx_mags):
        ax.plot(freq, txmag, alpha=0.4, linewidth=0.8)

    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Tx sensitivity (Pa/V)")
    ax.set_title("PMUT validation: frequency-response overlay")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"  Saved → {save_path}")


def main():
    print("Loading data …")
    dataset, pareto, valid, n_initial, col_tx, col_fbw = _load()
    freqs, tx_mags = _load_freq()
    print(
        f"  dataset:    {dataset.shape[0]} rows ({n_initial} initial + {dataset.shape[0] - n_initial} infill)"
    )
    print(f"  pareto:     {pareto.shape[0]} rows")
    print(f"  validation: {valid.shape[0]} rows")
    if freqs is not None:
        print(f"  freq curves: {len(freqs)} designs, {len(freqs[0])} freq points each")
    else:
        print("  freq curves: not available (run pareto_front.py with full_outputs)")

    print("\nGenerating plots …")
    plot_pareto_front(
        dataset, pareto, n_initial, col_tx, col_fbw, FIGS / "pareto_front.png"
    )
    plot_validation(dataset, pareto, valid, col_tx, col_fbw, FIGS / "validation.png")
    if freqs is not None and tx_mags is not None:
        plot_freq_response(freqs, tx_mags, FIGS / "validation_freq.png")

    print(f"\nAll plots saved under {FIGS}/")


if __name__ == "__main__":
    main()
