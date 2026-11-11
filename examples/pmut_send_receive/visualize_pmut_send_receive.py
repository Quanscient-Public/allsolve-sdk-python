"""
Visualize the receive voltages from the PMUT send / receive simulations.

Produces one plot saved to the "output" directory:

pmut_send_receive.png — two panels vs time (us):
  - Drive voltage (V) on the sending PMUT
  - Receive voltage (mV) on the floating electrode of the receiving PMUT,
    one line for each simulation ("Bottom sends" and "Top sends"), and a
    marker at the acoustic travel time 5 mm / 1480 m/s

Prerequisites:
  Run pmut_send_receive.py first, or have a project named
  "PMUT send receive" with finished "Bottom sends" and "Top sends"
  simulations.

Usage::

    python visualize_pmut_send_receive.py
"""

from __future__ import annotations

from pathlib import Path

import allsolve
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_NAME = "PMUT send receive"
SIMULATION_NAMES = ["Bottom sends", "Top sends"]
OUTPUT_DIR_NAME = "output"

# Distance between the PMUTs (m) and speed of sound in water (m/s).
TRAVEL_TIME_US = 5e-3 / 1480 * 1e6


def main() -> None:
    client = allsolve.Client()

    project = client.get_current_project()
    if project is None or project.name != PROJECT_NAME:
        project = client.get_project_by_name(PROJECT_NAME)
    if project is None:
        raise ValueError(
            f"Project not found: {PROJECT_NAME!r}. Run pmut_send_receive.py first."
        )
    print(f"Project: {project.name} (id: {project.id})")

    try:
        simulations = {sim.name: sim for sim in project.get_simulations()}
        results = {}
        for name in SIMULATION_NAMES:
            sim = simulations.get(name)
            if sim is None:
                raise ValueError(f"Simulation {name!r} not found in project.")
            output_data = sim.get_output_data()
            df = output_data.to_dataframe()
            # The step of a transient simulation is the time in seconds.
            df["Time (us)"] = pd.to_numeric(df["Step"], errors="coerce") * 1e6
            results[name] = df.sort_values("Time (us)")
            output_data.clean_cache()

            peak = results[name]["Receive voltage"].abs().max()
            print(f"{name}: peak |receive voltage| = {peak * 1e3:.3f} mV")

        script_dir = Path(__file__).resolve().parent
        output_dir = script_dir / OUTPUT_DIR_NAME
        output_dir.mkdir(parents=True, exist_ok=True)
        plot_path = output_dir / "pmut_send_receive.png"
        plot_voltages(results, plot_path)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.set_current_project(None)
        if input("Delete project? [Y/n]: ").strip().lower() in ("", "y", "yes"):
            project.delete()
            print("Project deleted.")


def plot_voltages(results: dict[str, pd.DataFrame], plot_path: Path) -> None:
    fig, (ax_drive, ax_receive) = plt.subplots(
        2, 1, figsize=(10, 7), sharex=True, gridspec_kw={"height_ratios": [1, 2]}
    )

    first = next(iter(results.values()))
    ax_drive.plot(first["Time (us)"], first["Drive voltage"], color="#4472C4")
    ax_drive.set_ylabel("Drive voltage (V)", fontsize=12)
    ax_drive.set_title("PMUT send / receive", fontsize=14, fontweight="bold")
    ax_drive.grid(True, alpha=0.3)

    styles = {"Bottom sends": ("#ED7D31", "-"), "Top sends": ("#70AD47", "--")}
    for name, df in results.items():
        color, linestyle = styles.get(name, (None, "-"))
        ax_receive.plot(
            df["Time (us)"],
            df["Receive voltage"] * 1e3,
            color=color,
            linestyle=linestyle,
            linewidth=2,
            label=name,
        )
    ax_receive.axvline(
        TRAVEL_TIME_US,
        color="gray",
        linestyle=":",
        label=f"Travel time {TRAVEL_TIME_US:.2f} us",
    )
    ax_receive.set_xlabel("Time (us)", fontsize=12)
    ax_receive.set_ylabel("Receive voltage (mV)", fontsize=12)
    ax_receive.legend(loc="upper left", framealpha=0.9)
    ax_receive.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(plot_path, dpi=200)
    plt.close(fig)
    print(f"Saved plot: {plot_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
