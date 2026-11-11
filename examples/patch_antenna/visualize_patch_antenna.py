"""
Visualize S-parameter magnitude from the patch antenna frequency sweep.

Loads the project saved by ``patch_antenna_demo.py`` (via
``client.get_current_project``), retrieves the first simulation's output data,
plots the S-parameter magnitude in dB vs. frequency, and marks the resonance dip
and design frequency.

Prerequisites:

- Run ``patch_antenna_demo.py`` first, or have project
  "Patch antenna demo" with a finished simulation in Allsolve.

Usage::

    pip install -r requirements.txt
    python visualize_patch_antenna.py
"""

from __future__ import annotations

from pathlib import Path

import allsolve
import matplotlib.pyplot as plt
import numpy as np

PROJECT_NAME = "Patch antenna demo"
SIMULATION_NAME = "Patch antenna harmonic sweep"
S_PARAMETERS_HEADER = "S-parameters (magnitude)"
DESIGN_FREQ_HZ = 2.35e9
OUTPUT_DIR_NAME = "output"
PLOT_FILENAME = "s_parameter_magnitude.png"


def _load_project(client: allsolve.Client) -> allsolve.Project:
    project = client.get_current_project()

    if project is None or project.name != PROJECT_NAME:
        project = allsolve.Project.get_by_name(name=PROJECT_NAME)
    if project is None or project.name != PROJECT_NAME:
        raise ValueError(
            f"Project not found: {PROJECT_NAME!r}. Run patch_antenna_demo.py first."
        )
    return project


def _load_simulation(project: allsolve.Project) -> allsolve.Simulation:
    simulations = project.get_simulations()
    if not simulations:
        raise ValueError("No simulations on this project.")

    for sim in simulations:
        if sim.name == SIMULATION_NAME:
            return sim
    return simulations[0]


def _s_parameter_db_at(
    output_data: allsolve.SimulationOutputData,
    sweep_index: int,
    step_index: int,
) -> float:
    values = output_data.get_values_at(sweep_index, step_index, S_PARAMETERS_HEADER)
    if values is None or not values:
        raise ValueError(
            f"No S-parameter data at sweep index {sweep_index}, "
            f"step index {step_index}"
        )
    return values[0]


def plot_s_parameter_magnitude(
    frequencies_hz: np.ndarray,
    s_parameter_db: np.ndarray,
    *,
    design_freq_hz: float,
    plot_path: Path,
) -> None:
    resonance_index = int(np.argmin(s_parameter_db))
    resonance_freq_hz = float(frequencies_hz[resonance_index])
    resonance_db = float(s_parameter_db[resonance_index])

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(
        frequencies_hz / 1e9,
        s_parameter_db,
        linewidth=2,
        label="|S11| (dB)",
    )
    ax.plot(
        resonance_freq_hz / 1e9,
        resonance_db,
        marker="o",
        markersize=8,
        linestyle="none",
        label=f"Resonance ({resonance_freq_hz / 1e9:.3f} GHz)",
    )
    ax.axvline(
        design_freq_hz / 1e9,
        color="tab:orange",
        linestyle="--",
        linewidth=1.5,
        label=f"Design freq ({design_freq_hz / 1e9:.2f} GHz)",
    )

    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("|S11| (dB)")
    ax.set_title("Patch antenna — |S11| vs frequency")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    plot_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(plot_path, dpi=200)
    plt.close(fig)

    print(
        f"Resonance dip: {resonance_freq_hz / 1e9:.4f} GHz, "
        f"|S11| = {resonance_db:.2f} dB"
    )
    print(f"Saved plot: {plot_path}")


def main() -> None:
    client = allsolve.Client()
    project = _load_project(client)
    print(f"Project: {project.name} (id: {project.id})")

    try:
        sim = _load_simulation(project)
        print(f"Simulation: {sim.name} (id: {sim.id})")

        output_data = sim.get_output_data()
        n_sweeps = output_data.get_sweep_count()
        headers = output_data.get_value_headers()
        print(f"Sweep steps: {n_sweeps}, value outputs: {headers}")

        if S_PARAMETERS_HEADER not in headers:
            raise ValueError(
                f"Expected {S_PARAMETERS_HEADER!r} in output headers: {headers}"
            )

        step_idx = output_data.get_step_index(allsolve.SimulationOutputData.NO_STEP)
        overrides = output_data.get_sweep_step_overrides()

        frequencies_hz = np.array(
            [float(overrides[j]["freq"][0]) for j in range(n_sweeps)]
        )
        s_parameter_db = np.array(
            [_s_parameter_db_at(output_data, j, step_idx) for j in range(n_sweeps)]
        )
        sort_order = np.argsort(frequencies_hz)
        frequencies_hz = frequencies_hz[sort_order]
        s_parameter_db = s_parameter_db[sort_order]

        plot_path = Path(__file__).resolve().parent / OUTPUT_DIR_NAME / PLOT_FILENAME
        plot_s_parameter_magnitude(
            frequencies_hz,
            s_parameter_db,
            design_freq_hz=DESIGN_FREQ_HZ,
            plot_path=plot_path,
        )

        output_data.clean_cache()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.set_current_project(None)
        if input("Delete project? [Y/n]: ").strip().lower() in ("", "y", "yes"):
            project.delete()
            print("Project deleted.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
