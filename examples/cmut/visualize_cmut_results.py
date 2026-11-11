"""
Visualize the results of CMUT_single_cell_rx.py.

Produces two plots in the "output" directory:

1. cmut_bias_sweep.png: static membrane deflection vs DC bias voltage.
2. cmut_transient.png: acoustic pressure in the water, membrane front-face
   displacement and change in electrode charge vs time in the transient
   simulation.

Prerequisites:
  Run CMUT_single_cell_rx.py first and answer "n" at the "Delete project?"
  prompt, or have a project named "CMUT single cell rx" with finished
  "Static DC bias sweep" and "Transient" simulations.

Usage::

    python visualize_cmut_results.py
"""

from __future__ import annotations

from pathlib import Path

import allsolve
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_NAME = "CMUT single cell rx"
SWEEP_SIMULATION_NAME = "Static DC bias sweep"
TRANSIENT_SIMULATION_NAME = "Transient"
OUTPUT_DIR_NAME = "output"


def main() -> None:
    client = allsolve.Client()

    project = client.get_current_project()
    if project is None or project.name != PROJECT_NAME:
        project = allsolve.Project.get_by_name(name=PROJECT_NAME)
    if project is None or project.name != PROJECT_NAME:
        raise ValueError(
            f"Project not found: {PROJECT_NAME!r}. Run CMUT_single_cell_rx.py first."
        )
    print(f"Project: {project.name} (id: {project.id})")

    try:
        output_dir = Path(__file__).resolve().parent / OUTPUT_DIR_NAME
        output_dir.mkdir(parents=True, exist_ok=True)

        sweep_df = get_dataframe(project, SWEEP_SIMULATION_NAME, include_overrides=True)
        plot_bias_sweep(sweep_df, output_dir / "cmut_bias_sweep.png")

        transient_df = get_dataframe(project, TRANSIENT_SIMULATION_NAME)
        plot_transient(transient_df, output_dir / "cmut_transient.png")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.set_current_project(None)
        if input("Delete project? [Y/n]: ").strip().lower() in ("", "y", "yes"):
            project.delete()
            print("Project deleted.")


def get_dataframe(
    project: allsolve.Project, name: str, include_overrides: bool = False
) -> pd.DataFrame:
    sim = next((s for s in project.get_simulations() if s.name == name), None)
    if sim is None:
        raise ValueError(f"Simulation {name!r} not found in project.")
    output_data = sim.get_output_data()
    df = output_data.to_dataframe(include_overrides=include_overrides)
    output_data.clean_cache()
    print(f"{name}: columns {list(df.columns)}")
    return df


def plot_bias_sweep(df: pd.DataFrame, plot_path: Path) -> None:
    df = df.apply(pd.to_numeric, errors="coerce").sort_values("Bias")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df["Bias"], df["Displacement"] * 1e9, color="#4472C4", marker="o")
    ax.set_xlabel("DC bias (V)")
    ax.set_ylabel("Membrane center deflection (nm)")
    ax.set_title("Static deflection vs DC bias")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(plot_path, dpi=200)
    plt.close(fig)
    print(f"Saved plot: {plot_path}")


def plot_transient(df: pd.DataFrame, plot_path: Path) -> None:
    df = df.apply(pd.to_numeric, errors="coerce").sort_values("Step")
    time_us = df["Step"] * 1e6

    df["Charge change"] = df["Charge"] - df["Charge"].iloc[0]
    series = [
        ("Pressure", 1, "Pressure in water (Pa)"),
        ("Displacement", 1e9, "Front-face displacement (nm)"),
        ("Charge change", 1e15, "Electrode charge change (fC)"),
    ]
    fig, axes = plt.subplots(len(series), 1, figsize=(9, 8), sharex=True)
    for ax, (column, scale, label) in zip(axes, series):
        ax.plot(time_us, df[column] * scale, color="#4472C4")
        ax.set_ylabel(label)
        ax.grid(True, alpha=0.3)
    axes[-1].set_xlabel("Time (us)")
    axes[0].set_title("Receive transient at the DC operating point")

    fig.tight_layout()
    fig.savefig(plot_path, dpi=200)
    plt.close(fig)
    print(f"Saved plot: {plot_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
