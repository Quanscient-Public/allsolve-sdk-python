"""
Visualize the PMUT array simulation results.

This script provides two types of visualization:
1. A frequency response PNG plot (P above and U max vs. frequency)
   generated from the simulation value output CSV data using matplotlib.
2. A time-domain pressure animation (MP4 video) for a single sweep step
   reconstructed from "p harmonic 2" and "p harmonic 3" VTU field outputs
   using pyvista.

Time-domain reconstruction (Allsolve convention: harm(2) = sine, harm(3) = cosine):
    p(x, t) = harm2(x) * sin(2*pi*f*t) + harm3(x) * cos(2*pi*f*t)

Usage:
    python visualize_pmut_array_results.py

Note: This script fetches the project using the project name and the first simulation is used.
      If you have multiple projects with the same name,
      use the project ID instead of the name, or define an unique name for your project.
"""

import csv
import os
import glob
from pathlib import Path

import allsolve
import matplotlib.pyplot as plt
import pyvista as pv
import numpy as np
import imageio.v3 as iio

PROJECT_NAME = "PMUT array demo"
FIELD_COSINE = "p harmonic 2"
FIELD_SINE = "p harmonic 3"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
RESULTS_DIR = os.path.join(OUTPUT_DIR, "vtus")
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
ANIMATION_DIR = os.path.join(OUTPUT_DIR, "animation")

# Number of time frames per period for the animation
FRAMES_PER_PERIOD = 30
FPS = 15

# Sweep step to animate. Set to None to automatically pick the step
# with the strongest pressure above the array (highest P above value).
SWEEP_STEP: int | None = None


def main() -> None:
    client = allsolve.Client()

    project = client.get_current_project()
    if project is None or project.name != PROJECT_NAME:
        raise ValueError(
            f"Project not found: {PROJECT_NAME!r}. Run pmut_array_demo.py first."
        )
    print(f"Project: {project.name} (id: {project.id})")

    sim = project.get_simulations()[0]
    print(f"Simulation: {sim.name} (id: {sim.id})")

    output_data = sim.get_output_data()

    plot_frequency_response(output_data)

    sweep_step = _resolve_sweep_step(output_data)
    freq_hz = _get_frequency(output_data, sweep_step)
    print(f"Animating sweep step {sweep_step}  (f = {freq_hz / 1e3:.1f} kHz)")

    # 1. Download VTU files for the chosen sweep step
    harm2_path, harm3_path = download_vtu_pair(sim, sweep_step)

    # 2. Load meshes and extract scalar arrays
    mesh_harm2: pv.DataSet = pv.read(harm2_path)  # type: ignore[assignment]
    mesh_harm3: pv.DataSet = pv.read(harm3_path)  # type: ignore[assignment]

    harm2_name = _find_scalar_field(mesh_harm2)
    harm3_name = _find_scalar_field(mesh_harm3)
    if harm2_name is None or harm3_name is None:
        raise RuntimeError("Could not find scalar fields in VTU files")

    harm2_arr = np.asarray(mesh_harm2.point_data[harm2_name]).ravel()
    harm3_arr = np.asarray(mesh_harm3.point_data[harm3_name]).ravel()

    magnitude = np.sqrt(harm2_arr**2 + harm3_arr**2)
    max_mag = float(magnitude.max())
    clim = [-max_mag, max_mag]
    print(f"Pressure magnitude range: [0, {max_mag:.4g}]")

    # 3. Render time-domain frames
    png_paths = render_time_frames(mesh_harm2, harm2_arr, harm3_arr, freq_hz, clim)

    # 4. Stitch into MP4
    create_mp4(png_paths, freq_hz)

    output_data.clean_cache()


def plot_frequency_response(output_data: allsolve.SimulationOutputData) -> None:
    """Save value output data to CSV (if not present) and generate a frequency response plot."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    csv_path = os.path.join(OUTPUT_DIR, "pmut_array_demo_output.csv")
    png_path = os.path.join(OUTPUT_DIR, "pmut_array_demo_plot.png")

    if not os.path.exists(csv_path):
        output_data.to_csv_file(
            filename=csv_path,
            csv_format=allsolve.CsvExportFormat.NORMAL,
            include_overrides=True,
        )
        print(f"Saved results to CSV: {csv_path}")

    plot_results_to_png(csv_path=csv_path, output_png_path=png_path)


def plot_results_to_png(
    csv_path: str | Path,
    output_png_path: str | Path,
) -> None:
    """Read simulation CSV and generate a dual-axis frequency response plot."""
    x_values: list[float] = []
    p_values: list[float] = []
    u_values: list[float] = []

    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        rows = csv.DictReader(csv_file)
        for row in rows:
            if "freq" not in row or not row["freq"]:
                raise ValueError("Missing required column 'freq'")
            if "P above" not in row or not row["P above"]:
                raise ValueError("Missing required column 'P above'")
            if "U max" not in row or not row["U max"]:
                raise ValueError("Missing required column 'U max'")

            x_values.append(float(row["freq"]))
            p_values.append(float(row["P above"]))
            u_values.append(float(row["U max"]))

    fig, axis_left = plt.subplots(figsize=(10, 6))
    axis_right = axis_left.twinx()

    left_color = "#1f77b4"
    right_color = "#d62728"

    axis_left.plot(x_values, p_values, color=left_color, label="P above", linewidth=2)
    axis_right.plot(x_values, u_values, color=right_color, label="U max", linewidth=2)

    axis_left.set_xlabel("Frequency (Hz)")
    axis_left.set_ylabel("P above", color=left_color)
    axis_right.set_ylabel("U max", color=right_color)
    axis_left.tick_params(axis="y", labelcolor=left_color)
    axis_right.tick_params(axis="y", labelcolor=right_color)
    axis_left.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_png_path, dpi=200)
    plt.close(fig)
    print(f"Saved frequency response plot: {output_png_path}")


def _resolve_sweep_step(output_data: allsolve.SimulationOutputData) -> int:
    """Return the sweep step to animate."""
    if SWEEP_STEP is not None:
        return SWEEP_STEP

    sweep_count = output_data.get_sweep_count()
    return sweep_count - 1


def _get_frequency(
    output_data: allsolve.SimulationOutputData, sweep_step: int
) -> float:
    """Extract the frequency (Hz) for a given sweep step."""
    overrides = output_data.get_sweep_step_overrides()
    step_overrides = overrides[sweep_step]
    if "freq" in step_overrides:
        vals = step_overrides["freq"]
        return float(vals[0]) if isinstance(vals, list) else float(vals)
    raise ValueError(f"No 'freq' override found for sweep step {sweep_step}")


def download_vtu_pair(sim: allsolve.Simulation, sweep_step: int) -> tuple[str, str]:
    """Download 'p harmonic 2' and 'p harmonic 3' VTUs for one sweep step.

    Returns (harm2_path, harm3_path).
    """
    step_dir = os.path.join(RESULTS_DIR, f"sweep_step_{sweep_step}")

    harm2_dir = os.path.join(step_dir, "harm2")
    harm3_dir = os.path.join(step_dir, "harm3")

    harm2_path = _download_field_if_needed(sim, FIELD_COSINE, sweep_step, harm2_dir)
    harm3_path = _download_field_if_needed(sim, FIELD_SINE, sweep_step, harm3_dir)

    return harm2_path, harm3_path


def _download_field_if_needed(
    sim: allsolve.Simulation,
    field_name: str,
    sweep_step: int,
    output_dir: str,
) -> str:
    """Download a field VTU if not already present. Returns the VTU path."""
    existing = glob.glob(os.path.join(output_dir, "*.vtu"))
    if existing:
        print(f"  Found {field_name} VTU in {output_dir}, skipping download.")
        return existing[0]

    os.makedirs(output_dir, exist_ok=True)
    print(f"  Downloading '{field_name}' for sweep step {sweep_step} …")
    sim.save_output_field(
        name=field_name,
        sweep_index=sweep_step,
        output_dir=output_dir,
    )

    vtus = glob.glob(os.path.join(output_dir, "*.vtu"))
    if not vtus:
        raise RuntimeError(
            f"No VTU file found after downloading '{field_name}' "
            f"(sweep step {sweep_step}) to {output_dir}"
        )
    return vtus[0]


def _find_scalar_field(mesh: pv.DataSet) -> str | None:
    """Return the name of the first scalar (1-component) point-data array, or None."""
    for name in mesh.point_data:
        arr = mesh.point_data[name]
        if arr.ndim == 1 or (arr.ndim == 2 and arr.shape[1] == 1):
            return name
    return None


def render_time_frames(
    mesh: pv.DataSet,
    harm2: np.ndarray,
    harm3: np.ndarray,
    freq_hz: float,
    clim: list[float],
) -> list[str]:
    """Render time-domain pressure frames for one period.

    Reconstructs the instantaneous pressure at each time step:
        p(x, t_i) = harm2(x) * sin(phase_i) + harm3(x) * cos(phase_i)

    Two slices cut through the mesh:
    * Y-slice through mesh center — reveals the XZ cross-section.
    * Z-slice at z = 20 µm — horizontal cut just above the piezoelectric layer.
    """
    print(f"Rendering {FRAMES_PER_PERIOD} time-domain frames …")
    os.makedirs(IMAGES_DIR, exist_ok=True)

    period_us = 1e6 / freq_hz
    phases = np.linspace(0.0, 2 * np.pi, FRAMES_PER_PERIOD, endpoint=False)
    scalar_name = "p_reconstructed"
    png_paths: list[str] = []

    for i, phase in enumerate(phases):
        png_path = os.path.join(
            IMAGES_DIR, f"p_timedomain_{freq_hz / 1e3:.0f}kHz_{i:03d}.png"
        )
        png_paths.append(png_path)

        if os.path.exists(png_path):
            print(f"  [{i + 1}/{FRAMES_PER_PERIOD}] Already exists, skipping")
            continue

        p_instant = harm2 * np.sin(phase) + harm3 * np.cos(phase)
        mesh.point_data[scalar_name] = p_instant

        t_us = phase / (2 * np.pi) * period_us
        title = f"f = {freq_hz / 1e3:.0f} kHz,  t = {t_us:.3f} µs"

        slice_y = mesh.slice(normal="y", origin=mesh.center)  # type: ignore[union-attr]
        z_above_piezo = 20e-6
        slice_z = mesh.slice(  # type: ignore[union-attr]
            normal="z",
            origin=(mesh.center[0], mesh.center[1], z_above_piezo),
        )

        pl = pv.Plotter(off_screen=True, window_size=[1200, 800])

        pl.add_mesh(
            slice_y,  # type: ignore[arg-type]
            scalars=scalar_name,
            cmap="coolwarm",
            clim=clim,
            show_edges=False,
            opacity=0.95,
            show_scalar_bar=False,
        )
        pl.add_mesh(
            slice_z,  # type: ignore[arg-type]
            scalars=scalar_name,
            cmap="coolwarm",
            clim=clim,
            show_edges=False,
            scalar_bar_args={
                "title": "Pressure (Pa)",
                "vertical": False,
                "position_x": 0.55,
                "position_y": 0.9,
                "width": 0.4,
                "height": 0.06,
                "n_labels": 5,
                "n_colors": 256,
            },
        )
        pl.add_text(title, font_size=10, position="upper_left")
        pl.add_axes()  # type: ignore[call-arg]

        cx, cy, cz = mesh.center
        dist = mesh.length
        pl.camera_position = [  # type: ignore[assignment]
            (cx, cy - dist * 1.2, cz + dist * 0.4),
            (cx, cy, cz),
            (0, 0, 1),
        ]

        pl.screenshot(png_path)
        pl.close()
        print(
            f"  [{i + 1}/{FRAMES_PER_PERIOD}] Saved frame (phase = {np.degrees(phase):.0f}°)"
        )

    return png_paths


def create_mp4(
    png_paths: list[str],
    freq_hz: float,
    output_path: str | None = None,
) -> str | None:
    """Stitch PNG frames into a looping MP4 video."""
    print("Creating MP4 video …")
    if not png_paths:
        print("No PNG images to combine.")
        return None

    if output_path is None:
        os.makedirs(ANIMATION_DIR, exist_ok=True)
        output_path = os.path.join(
            ANIMATION_DIR, f"pmut_pressure_{freq_hz / 1e3:.0f}kHz.mp4"
        )

    if os.path.exists(output_path):
        print(f"MP4 already exists: {output_path}")
        return output_path

    frames = [iio.imread(p) for p in png_paths if os.path.exists(p)]
    if not frames:
        print("Could not open any PNG frames.")
        return None

    iio.imwrite(output_path, frames, fps=FPS, codec="libx264")
    print(f"Saved MP4 video: {output_path}")
    return output_path


if __name__ == "__main__":
    main()
