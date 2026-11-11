"""
Visualize the PZT disc in water simulation results.

Produces two plots saved to the "output" directory:

1. pzt_disc_impedance.png: |Z| and phase of the full-disc impedance against
   frequency, from the "Frequency sweep" value outputs.
2. pzt_disc_pressure.png: pressure amplitude |p| in the xz plane at the
   single drive frequency, from the "p sin" and "p cos" field outputs.
   The octant model is mirrored about x = 0 and z = 0 to show the full
   cross-section.

Allsolve harmonic convention: harm(2) = sin and harm(3) = cos, so
    p(x, t) = p_sin(x)*sin(wt) + p_cos(x)*cos(wt),  |p| = sqrt(p_sin^2 + p_cos^2)

Prerequisites:
  Run pzt_disc_in_water.py first and answer "n" when it asks to delete
  the project.

Usage::

    python visualize_pzt_disc_results.py
"""

import glob
import os

import allsolve
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
from matplotlib.patches import Rectangle

PROJECT_NAME = "PZT disc in water"
SINGLE_SIMULATION_NAME = "Single frequency"
SWEEP_SIMULATION_NAME = "Frequency sweep"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
FIELDS_DIR = os.path.join(OUTPUT_DIR, "fields")


def main() -> None:
    client = allsolve.Client()

    project = client.get_current_project()
    if project is None or project.name != PROJECT_NAME:
        raise ValueError(
            f"Project not found: {PROJECT_NAME!r}. Run pzt_disc_in_water.py first."
        )
    print(f"Project: {project.name} (id: {project.id})")

    simulations = {sim.name: sim for sim in project.get_simulations()}
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    plot_impedance(simulations[SWEEP_SIMULATION_NAME])
    plot_pressure(simulations[SINGLE_SIMULATION_NAME])


def plot_impedance(sim: allsolve.Simulation) -> None:
    output_data = sim.get_output_data()
    df = output_data.to_dataframe(include_overrides=True).sort_values("Frequency")
    output_data.clean_cache()

    freq_khz = df["Frequency"] / 1e3
    phase_deg = np.degrees(np.arctan2(df["Z imag"], df["Z real"]))

    fig, (ax_abs, ax_phase) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax_abs.semilogy(freq_khz, df["Z abs"], marker=".")
    ax_abs.set_ylabel("|Z| [Ω]")
    ax_abs.set_title("PZT disc in water: full-disc electrical impedance")
    ax_abs.grid(True, which="both", alpha=0.3)
    ax_phase.plot(freq_khz, phase_deg, marker=".")
    ax_phase.set_xlabel("Frequency [kHz]")
    ax_phase.set_ylabel("Phase [deg]")
    ax_phase.grid(True, alpha=0.3)
    fig.tight_layout()

    path = os.path.join(OUTPUT_DIR, "pzt_disc_impedance.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")


def read_field(sim: allsolve.Simulation, name: str) -> tuple[np.ndarray, np.ndarray]:
    """Download a field output and return its points and values.

    The VTKHDF files repeat each node for every cell that uses it, so
    duplicate points are merged.
    """
    field_dir = os.path.join(FIELDS_DIR, name.replace(" ", "_"))
    os.makedirs(field_dir, exist_ok=True)
    for old_file in glob.glob(os.path.join(field_dir, "*.hdf")):
        os.remove(old_file)
    sim.save_output_field(name=name, output_dir=field_dir)

    points, values = [], []
    for file in sorted(glob.glob(os.path.join(field_dir, "*.hdf"))):
        grid = pv.read(file)
        points.append(np.asarray(grid.points))
        values.append(np.asarray(grid.point_data[grid.point_data.keys()[0]]).ravel())
    points, values = np.vstack(points), np.concatenate(values)
    _, unique = np.unique(np.round(points, 9), axis=0, return_index=True)
    return points[unique], values[unique]


def get_value(output_data: allsolve.SimulationOutputData, name: str) -> float:
    value = output_data.get_value_at(0, 0, name)
    if value is None:
        raise ValueError(f"Value output {name!r} not found")
    return value


def plot_pressure(sim: allsolve.Simulation) -> None:
    output_data = sim.get_output_data()
    freq = get_value(output_data, "Frequency")
    r_disc = get_value(output_data, "R disc")
    t_disc = get_value(output_data, "t disc")
    r_water = get_value(output_data, "R water")
    output_data.clean_cache()

    points, p_sin = read_field(sim, "p sin")
    points_cos, p_cos = read_field(sim, "p cos")
    if not np.allclose(points, points_cos):
        raise ValueError("The p sin and p cos fields have different points")
    p_abs = np.sqrt(p_sin**2 + p_cos**2)

    # Nodes on the y = 0 symmetry plane, without the PML layers.
    r = np.linalg.norm(points, axis=1)
    on_plane = (np.abs(points[:, 1]) < 1e-9) & (r <= r_water * (1 + 1e-6))
    x, z, p = points[on_plane, 0], points[on_plane, 2], p_abs[on_plane]

    # Mirror the octant about x = 0 and z = 0 (p is even in x and z).
    x = np.concatenate([x, -x, x, -x]) * 1e3
    z = np.concatenate([z, z, -z, -z]) * 1e3
    p = np.tile(p, 4)

    fig, ax = plt.subplots(figsize=(7, 6))
    contour = ax.tricontourf(x, z, p / 1e3, levels=40, cmap="viridis")
    fig.colorbar(contour, ax=ax, label="|p| [kPa]")
    ax.add_patch(
        Rectangle(
            (-r_disc * 1e3, -t_disc / 2 * 1e3),
            2 * r_disc * 1e3,
            t_disc * 1e3,
            facecolor="lightgray",
            edgecolor="black",
            label="PZT disc",
        )
    )
    ax.set_aspect("equal")
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("z [mm]")
    ax.set_title(f"Pressure amplitude in the xz plane at {freq / 1e3:g} kHz (1 V)")
    ax.legend(loc="upper right")
    fig.tight_layout()

    path = os.path.join(OUTPUT_DIR, "pzt_disc_pressure.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")


if __name__ == "__main__":
    main()
