"""
Visualize the pull-in analysis results from the lumped pull-in simulation.

Produces two plots saved to the "output" directory:

1. pull_in_analysis.png — line plot with three series vs DC voltage (Vdc):
     - Uz_simulation (um)      : simulated deflection from the lumped model
     - Uz_theoritical           : analytical deflection (interpolated function)
     - Pull-in deflection (um)  : theoretical pull-in deflection (constant line)

2. pull_in_bar_comparison.png — grouped bar chart comparing simulated vs
   theoretical Uz at each sweep voltage.

Prerequisites:
  Run lumped_pull_in_analysis.py first, or have a project named
  "Lumped pull-in analysis" with a finished "Simulation 2: Initial state".

Usage::

    python visualize_pull_in_results.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import allsolve
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_NAME = "Lumped pull-in analysis"
SIMULATION_NAME = "Simulation 2: Initial state"
OUTPUT_DIR_NAME = "output"


def main() -> None:
    client = allsolve.Client()

    project = client.get_current_project()
    if project is None or project.name != PROJECT_NAME:
        project = allsolve.Project.get_by_name(name=PROJECT_NAME)
    if project is None or project.name != PROJECT_NAME:
        raise ValueError(
            f"Project not found: {PROJECT_NAME!r}. "
            "Run lumped_pull_in_analysis.py first."
        )
    print(f"Project: {project.name} (id: {project.id})")

    simulations = project.get_simulations()
    sim = next((s for s in simulations if s.name == SIMULATION_NAME), None)
    if sim is None:
        raise ValueError(f"Simulation {SIMULATION_NAME!r} not found in project.")
    print(f"Simulation: {sim.name} (id: {sim.id})")

    output_data = sim.get_output_data()
    df = output_data.to_dataframe(include_overrides=True)

    print(f"Columns: {list(df.columns)}")
    print(f"Sweep steps: {output_data.get_sweep_count()}")
    print(df.head().to_string())

    script_dir = Path(__file__).resolve().parent
    output_dir = script_dir / OUTPUT_DIR_NAME
    output_dir.mkdir(parents=True, exist_ok=True)

    plot_path = output_dir / "pull_in_analysis.png"
    plot_pull_in(df, plot_path)

    bar_path = output_dir / "pull_in_bar_comparison.png"
    plot_bar_comparison(df, bar_path)

    output_data.clean_cache()


def plot_pull_in(df: pd.DataFrame, plot_path: Path) -> None:
    col_vdc = "Vdc"
    col_uz_sim = "Uz_simulation (um)"
    col_uz_th = "Uz_theoritical"
    col_pullin = "Pull-in deflection (um)"

    required = {col_vdc, col_uz_sim, col_uz_th, col_pullin}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in output data: {missing}")

    for col in (col_vdc, col_uz_sim, col_uz_th, col_pullin):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    sweep_df = df.groupby("Sweep step").first().reset_index().sort_values(col_vdc)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(
        sweep_df[col_vdc],
        sweep_df[col_uz_sim],
        color="#4472C4",
        marker="o",
        markersize=5,
        linewidth=2,
        label="Uz_simulation (um)",
    )

    ax.plot(
        sweep_df[col_vdc],
        sweep_df[col_uz_th],
        color="#70AD47",
        marker="o",
        markersize=5,
        linewidth=2,
        label="Uz_theoritical",
    )

    ax.plot(
        sweep_df[col_vdc],
        sweep_df[col_pullin],
        color="#FFC000",
        marker="o",
        markersize=5,
        linewidth=1.5,
        label="Pull-in deflection (um)",
    )

    ax.set_xlabel("Vdc (V)", fontsize=12)
    ax.set_ylabel("U_z (um)", fontsize=12)
    ax.set_title("Pull-in Analysis", fontsize=14, fontweight="bold")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(plot_path, dpi=200)
    plt.close(fig)
    print(f"\nSaved plot: {plot_path}")


def plot_bar_comparison(df: pd.DataFrame, plot_path: Path) -> None:
    col_vdc = "Vdc"
    col_uz_sim = "Uz_simulation (um)"
    col_uz_th = "Uz_theoritical"

    required = {col_vdc, col_uz_sim, col_uz_th}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in output data: {missing}")

    for col in (col_vdc, col_uz_sim, col_uz_th):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    sweep_df = df.groupby("Sweep step").first().reset_index().sort_values(col_vdc)

    vdc_labels = [f"{v:.0f}" for v in sweep_df[col_vdc]]
    x = np.arange(len(vdc_labels))
    bar_width = 0.35

    fig, ax = plt.subplots(figsize=(14, 6))

    ax.bar(
        x - bar_width / 2,
        sweep_df[col_uz_sim],
        bar_width,
        label="Uz_simulation (um)",
        color="#4472C4",
    )
    ax.bar(
        x + bar_width / 2,
        sweep_df[col_uz_th],
        bar_width,
        label="Uz_theoritical (um)",
        color="#70AD47",
    )

    ax.set_xlabel("Vdc (V)", fontsize=12)
    ax.set_ylabel("U_z (um)", fontsize=12)
    ax.set_title(
        "Simulated vs Theoretical Deflection",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(vdc_labels, rotation=45, ha="right", fontsize=8)
    ax.legend(fontsize=11)
    ax.grid(True, axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(plot_path, dpi=200)
    plt.close(fig)
    print(f"Saved bar chart: {plot_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        raise
