"""
Visualize S₁₂ results from the microstrip stub filter Cartesian sweep.

Loads the project saved by ``sweep.py`` (via ``client.get_current_project``),
retrieves the first simulation's output data, groups sweep steps by stub
length, and plots S₁₂ magnitude vs. frequency for each stub length.

Prerequisites:

- Run ``sweep.py`` first, or have project
  "SDK - Microstrip stub filter sweep" with a finished simulation in Allsolve.

Usage::

    pip install -r requirements.txt
    python visualize_geometric_sweep.py
"""

from __future__ import annotations

import allsolve
import numpy as np
import matplotlib.pyplot as plt

PROJECT_NAME = "SDK - Microstrip stub filter sweep"


def main() -> None:
    client = allsolve.Client()

    project = client.get_current_project()

    if project is None or project.name != PROJECT_NAME:
        project = allsolve.Project.get_by_name(name=PROJECT_NAME)
    if project is None or project.name != PROJECT_NAME:
        raise ValueError(f"Project not found: {PROJECT_NAME!r}. Run sweep.py first.")

    print(f"Project: {project.name} (id: {project.id})")

    try:
        simulations = project.get_simulations()
        if not simulations:
            raise ValueError("No simulations on this project.")
        sim = simulations[0]
        print(f"Simulation: {sim.name} (id: {sim.id})")

        output_data = sim.get_output_data()
        n_sweeps = output_data.get_sweep_count()
        headers = output_data.get_value_headers()
        print(f"Sweep steps: {n_sweeps}, value outputs: {headers}")

        step_idx = output_data.get_step_index(allsolve.SimulationOutputData.NO_STEP)
        overrides = output_data.get_sweep_step_overrides()

        stub_to_indices: dict[float, list[int]] = {}
        for j in range(n_sweeps):
            stub_val = float(overrides[j]["stub_length"][0])
            stub_to_indices.setdefault(stub_val, []).append(j)

        fig, ax = plt.subplots()

        for stub_length in sorted(stub_to_indices):
            indices = stub_to_indices[stub_length]

            frequencies = np.array([float(overrides[j]["freq"][0]) for j in indices])
            s_magnitudes = np.array(
                [
                    output_data.get_values_at(j, step_idx, "S-parameters (magnitude)")
                    for j in indices
                ]
            )

            sort_order = np.argsort(frequencies)
            ax.plot(
                frequencies[sort_order],
                s_magnitudes[sort_order, 1],
                label=f"S_12, Stub {stub_length:.4f}",
            )

        output_data.clean_cache()

        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("|S_12|")
        ax.set_title("Microstrip stub filter — S_12 vs frequency")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        plt.show()
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
