"""
Visualize the pin fin heat sink simulation results using pyvista.

The script downloads "T" (temperature) field files for every timestep,
applies a clip filter to reveal the interior temperature distribution,
and opens an interactive pyvista window.

Usage:
    python visualize_heat_sink.py --interactive
    python visualize_heat_sink.py

First, the project is searched for by name and the first simulation is used.
Then the simulation results are downloaded to the "output/results" subfolder.
In interactive mode, the script opens an interactive window showing the clipped
temperature field at a specific timestep.
In non-interactive mode, the script creates PNG images in "output/images"
for each timestep.
"""

import sys
import os
import glob
import re

import allsolve
import pyvista as pv

PROJECT_NAME = "Pin fin heat sink demo"
FIELD_NAME = "Temperature"
RESULT_FILE_EXTENSION = ".hdf"
_RESULT_FILE_PATTERN = re.compile(r"^(.+)_(.+)_(\d+)\.hdf$", re.IGNORECASE)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
RESULTS_DIR = os.path.join(OUTPUT_DIR, "results")
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")

CAMERA = {
    "position": [-0.2941901649101568, 0.1811806039559683, 0.06961678615056432],
    "focal_point": [0.017038620449775443, -0.018127495379133773, 0.048813751377931106],
    "view_up": [0.009419994996909348, -0.08924536219837262, 0.9959651243996144],
    "clipping_range": [0.3081782863019225, 0.427586959275503],
    "view_angle": 30,
}

CLIP_NORMAL = (1, 0, 0)
CLIP_ORIGIN = (0, 0, 0)

SCALAR_RANGE = [293.15, 293.187]
BACKGROUND_COLOR = "#e3f4ff"
AMBIENT = 0.3
DIFFUSE = 0.7


def _result_file_sort_key(path: str) -> tuple[float | str, int, str]:
    """Sort result files by numeric step label, then MPI rank."""
    basename = os.path.basename(path)
    match = _RESULT_FILE_PATTERN.match(basename)
    if match is None:
        return (basename, 0, basename)

    _field_name, step_label, rank_str = match.groups()
    try:
        step_key: float | str = float(step_label)
    except ValueError:
        step_key = step_label
    return (step_key, int(rank_str), basename)


def _list_result_files(results_dir: str) -> list[str]:
    """Return field output files (.hdf) sorted by timestep."""
    files = glob.glob(os.path.join(results_dir, f"*{RESULT_FILE_EXTENSION}"))
    return sorted(files, key=_result_file_sort_key)


def _scalar_name(mesh: pv.DataSet) -> str:
    """Resolve the temperature scalar array name of the HDF output."""
    if FIELD_NAME in mesh.array_names:
        return FIELD_NAME
    if mesh.array_names:
        return mesh.array_names[0]
    raise ValueError("No scalar arrays found in result file")


def download_result_files(project: allsolve.Project) -> None:
    """Download the temperature field files for all timesteps."""
    print("Downloading simulation result files...")

    simulations = project.get_simulations()
    if len(simulations) == 0:
        raise ValueError(f"No simulations found in project: {project.name}")
    simulation = simulations[0]
    print(f"Simulation: {simulation.name} (id: {simulation.id})")

    if os.path.exists(RESULTS_DIR) and _list_result_files(RESULTS_DIR):
        print(f"Found result files in {RESULTS_DIR}, skipping download.")
        return

    os.makedirs(RESULTS_DIR, exist_ok=True)

    output_data = simulation.get_output_data()
    step_count = output_data.get_step_count()
    print(f"Downloading '{FIELD_NAME}' for {step_count} timesteps...")

    for step_index in range(step_count):
        simulation.save_output_field(
            name=FIELD_NAME, step_index=step_index, output_dir=RESULTS_DIR
        )
        print(f"  step {step_index}/{step_count - 1} done")

    output_data.clean_cache()


def _load_and_clip(result_path: str) -> pv.DataSet:
    """Load an HDF file, clean to grid, and apply the clip filter."""
    mesh = pv.read(result_path)
    if hasattr(mesh, "clean"):
        mesh = mesh.clean()  # type: ignore[union-attr]
    clipped = mesh.clip(  # type: ignore[union-attr]
        normal=CLIP_NORMAL, origin=CLIP_ORIGIN, invert=False
    )
    return clipped  # type: ignore[return-value]


def _apply_camera(plotter: pv.Plotter) -> None:
    """Apply the saved camera settings to the plotter."""
    plotter.camera.position = CAMERA["position"]  # type: ignore[assignment]
    plotter.camera.focal_point = CAMERA["focal_point"]  # type: ignore[assignment]
    plotter.camera.up = CAMERA["view_up"]  # type: ignore[assignment]
    plotter.camera.clipping_range = CAMERA["clipping_range"]  # type: ignore[assignment]
    plotter.camera.view_angle = CAMERA["view_angle"]  # type: ignore[assignment]


def _add_mesh_to_plotter(
    plotter: pv.Plotter,
    mesh: pv.DataSet,
    scalar_bar: bool = True,
) -> None:
    """Add the clipped mesh to a plotter with consistent rendering settings."""
    scalar_bar_args = (
        {
            "title": "Temperature [K]",
            "vertical": True,
            "n_labels": 5,
            "n_colors": 256,
            "fmt": "%.3f",
        }
        if scalar_bar
        else None
    )
    plotter.add_mesh(
        mesh,
        scalars=_scalar_name(mesh),
        cmap="coolwarm",
        clim=SCALAR_RANGE,
        show_edges=False,
        show_scalar_bar=scalar_bar,
        scalar_bar_args=scalar_bar_args,  # type: ignore[arg-type]
        ambient=AMBIENT,
        diffuse=DIFFUSE,
    )


def show_interactive(results_dir: str = RESULTS_DIR, step_index: int = 0) -> None:
    """Open an interactive PyVista window showing the clipped temperature field.

    By default shows step index 0. Use left/right arrow keys to navigate
    between timesteps.
    """
    result_files = _list_result_files(results_dir)
    if not result_files:
        print(f"No HDF files found in {results_dir}")
        return

    step_index = min(step_index, len(result_files) - 1)
    current = {"idx": step_index}

    plotter = pv.Plotter()
    plotter.set_background(BACKGROUND_COLOR)  # type: ignore[arg-type]

    clipped = _load_and_clip(result_files[current["idx"]])
    _add_mesh_to_plotter(plotter, clipped)
    plotter.add_axes()  # type: ignore[call-arg]

    plotter.add_text(  # type: ignore[call-arg]
        f"Step {current['idx']} — {os.path.basename(result_files[current['idx']])}",
        font_size=10,
        position="upper_left",
    )

    _apply_camera(plotter)

    def _update_step(new_idx: int) -> None:
        new_idx = max(0, min(new_idx, len(result_files) - 1))
        if new_idx == current["idx"]:
            return
        current["idx"] = new_idx
        plotter.clear()  # type: ignore[call-arg]
        new_clipped = _load_and_clip(result_files[new_idx])
        _add_mesh_to_plotter(plotter, new_clipped)
        plotter.add_axes()  # type: ignore[call-arg]
        plotter.add_text(  # type: ignore[call-arg]
            f"Step {new_idx} — {os.path.basename(result_files[new_idx])}",
            font_size=10,
            position="upper_left",
        )
        plotter.render()

    def _next_step() -> None:
        _update_step(current["idx"] + 1)

    def _prev_step() -> None:
        _update_step(current["idx"] - 1)

    plotter.add_key_event("Right", _next_step)  # type: ignore[call-arg]
    plotter.add_key_event("Left", _prev_step)  # type: ignore[call-arg]

    print(f"Showing step {current['idx']} of {len(result_files) - 1}")
    print("Use Left/Right arrow keys to navigate timesteps.")
    plotter.show()


def create_png_images(results_dir: str = RESULTS_DIR) -> list[str]:
    """Render each timestep result file as a PNG screenshot with the clip filter applied."""
    print("Creating PNG images...")
    result_files = _list_result_files(results_dir)
    if not result_files:
        print(f"No HDF files found in {results_dir}")
        return []

    os.makedirs(IMAGES_DIR, exist_ok=True)
    png_paths: list[str] = []

    for idx, result_path in enumerate(result_files):
        stem = os.path.splitext(os.path.basename(result_path))[0]
        png_path = os.path.join(IMAGES_DIR, f"{stem}.png")
        png_paths.append(png_path)

        if os.path.exists(png_path):
            print(
                f"  [{idx + 1}/{len(result_files)}] Already exists, skipping {png_path}"
            )
            continue

        clipped = _load_and_clip(result_path)

        pl = pv.Plotter(off_screen=True, window_size=[1200, 800])
        pl.set_background(BACKGROUND_COLOR)  # type: ignore[arg-type]
        _add_mesh_to_plotter(pl, clipped)
        pl.add_axes()  # type: ignore[call-arg]
        pl.add_text(  # type: ignore[call-arg]
            f"Step {idx} — {stem}", font_size=10, position="upper_left"
        )
        _apply_camera(pl)

        pl.screenshot(png_path)
        pl.close()
        print(f"  [{idx + 1}/{len(result_files)}] Saved {png_path}")

    return png_paths


if __name__ == "__main__":
    try:
        interactive = "--interactive" in sys.argv

        client = allsolve.Client()

        project = allsolve.Project.get_by_name(name=PROJECT_NAME)
        if project is None:
            raise ValueError(f"Project not found: {PROJECT_NAME}")
        print(f"Project: {project.name} (id: {project.id})")

        download_result_files(project)

        if interactive:
            show_interactive()
        else:
            create_png_images()
    except Exception as e:
        print(f"Error running project: {e}")
