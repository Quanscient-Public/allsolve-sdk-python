"""
Visualize the simulation results of a MEMS comb-drive accelerometer eigenmode analysis using pyvista library.

The script can be run in interactive mode or non-interactive mode:
python visualize_combdrive_eigenmodes.py --interactive
python visualize_combdrive_eigenmodes.py

First, the project is searched for by name and the first simulation is used.
Then the simulation results are downloaded to the "output/results" subfolder.
In interactive mode, the script will open an interactive window with all eigenmodes in a subplot grid.
In non-interactive mode, the script will create PNG images in "output/images" and animated GIFs in "output/animation".
"""

import sys
import allsolve
import os
import glob
import pyvista as pv
import numpy as np
from PIL import Image

PROJECT_NAME = "Combdrive Eigenmodes demo"
FIELD_NAME = "u (real)"
RESULT_FILE_EXTENSIONS = (".vtu", ".hdf")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
RESULTS_DIR = os.path.join(OUTPUT_DIR, "results")
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
ANIMATION_DIR = os.path.join(OUTPUT_DIR, "animation")


def _result_file_sort_key(path: str) -> tuple[float | str, int, str]:
    """Sort result files by numeric step label, then MPI rank."""
    basename = os.path.basename(path)
    stem, _ext = os.path.splitext(basename)
    parts = stem.rsplit("_", 2)
    if len(parts) != 3:
        return (basename, 0, basename)

    _field_name, step_label, rank_str = parts
    try:
        step_key: float | str = float(step_label)
    except ValueError:
        step_key = step_label
    return (step_key, int(rank_str), basename)


def _list_result_files(results_dir: str) -> list[str]:
    """Return field output files (.vtu or .hdf) sorted by step label."""
    files: list[str] = []
    for ext in RESULT_FILE_EXTENSIONS:
        files.extend(glob.glob(os.path.join(results_dir, f"*{ext}")))
    return sorted(files, key=_result_file_sort_key)


def main():
    client = allsolve.Client()

    # Try to get the project that was created by combdrive_eigenmodes.py
    project = client.get_current_project()

    if project is None or project.name != PROJECT_NAME:
        # Try searching for the project by name
        project = allsolve.Project.get_by_name(name=PROJECT_NAME)
    if project is None or project.name != PROJECT_NAME:
        raise ValueError(
            f"Project not found: {PROJECT_NAME!r}. Run combdrive_eigenmodes.py first."
        )

    try:
        download_result_files(project)

        # To run visualizations in interactive mode, use:
        # python visualize_combdrive_eigenmodes.py --interactive
        interactive = "--interactive" in sys.argv
        if interactive:
            # Show the interactive grid if the --interactive flag is used
            show_interactive_grid()
        else:
            # Create the PNG images and animated GIFs to the output folder
            create_png_images_with_pyvista()
            create_animated_gifs()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.set_current_project(None)
        if input("Delete project? [Y/n]: ").strip().lower() in ("", "y", "yes"):
            project.delete()
            print("Project deleted.")


def download_result_files(project: allsolve.Project) -> None:
    """Download the displacement field files for all eigenmode steps."""
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
    print(f"Downloading '{FIELD_NAME}' for {step_count} steps...")
    for step_index in range(step_count):
        simulation.save_output_field(
            name=FIELD_NAME, step_index=step_index, output_dir=RESULTS_DIR
        )
        print(f"  step {step_index}/{step_count - 1} done")

    output_data.clean_cache()


def _find_vector_field(mesh) -> str | None:
    """Return the name of the first 3-component vector point-data array, or None."""
    for name in mesh.point_data:
        arr = mesh.point_data[name]
        if arr.ndim == 2 and arr.shape[1] == 3:
            return name
    return None


def _warp_and_color(mesh, vector_name: str):
    """Warp mesh by displacement vector and add a magnitude scalar."""
    warped = mesh.warp_by_vector(vectors=vector_name, factor=0.001)
    mag = np.linalg.norm(mesh[vector_name], axis=1)  # type: ignore[index]
    warped.point_data["Displacement Magnitude"] = mag
    return warped


def create_png_images_with_pyvista(results_dir: str = RESULTS_DIR):
    """Render each result file to a PNG screenshot and save the screenshots to the "images" folder."""
    print("Creating PNG images...")
    result_files = _list_result_files(results_dir)
    if not result_files:
        print(f"No VTU or HDF files found in {results_dir}")
        return

    os.makedirs(IMAGES_DIR, exist_ok=True)

    for result_path in result_files:
        filename = os.path.basename(result_path)
        stem = os.path.splitext(filename)[0]
        print(f"Processing {filename}...")

        mesh = pv.read(result_path)
        vector_name = _find_vector_field(mesh)
        if vector_name is None:
            print(f"  No vector field found, skipping.")
            continue

        warped = _warp_and_color(mesh, vector_name)

        plotter = pv.Plotter(off_screen=True)
        plotter.add_mesh(
            warped,
            show_edges=False,  # Hide the edges of the mesh
            scalars="Displacement Magnitude",
            cmap="coolwarm",  # Use a coolwarm colormap for the displacement magnitude
            clim=[0, 0.04],  # Use a fixed color range for the displacement magnitude
            scalar_bar_args={"title": "Displacement Magnitude"},
        )
        plotter.add_axes()  # type: ignore[call-arg]

        # For demonstration purposes, rotate the camera by 15 degrees
        plotter.camera.azimuth -= 15

        # Save the screenshot to the "images" folder
        screenshot_path = os.path.join(IMAGES_DIR, f"{stem}.png")
        plotter.screenshot(screenshot_path)
        plotter.close()
        print(f"  Saved screenshot to {screenshot_path}")


def create_animated_gifs(
    results_dir: str = RESULTS_DIR,
    animation_dir: str = ANIMATION_DIR,
    n_frames: int = 40,
    warp_factor: float = 0.001,
    duration: int = 50,
):
    """Create one animated GIF per result file with sinusoidal warp ramping and save the GIFs to the animation folder."""
    print("Creating animated GIFs...")
    result_files = _list_result_files(results_dir)
    if not result_files:
        print(f"No VTU or HDF files found in {results_dir}")
        return

    os.makedirs(animation_dir, exist_ok=True)

    phases = np.linspace(0, 2 * np.pi, n_frames, endpoint=False)

    for result_path in result_files:
        stem = os.path.splitext(os.path.basename(result_path))[0]
        gif_path = os.path.join(animation_dir, f"{stem}.gif")
        if os.path.exists(gif_path):
            print(f"Found {gif_path}, skipping.")
            continue

        mesh = pv.read(result_path)
        vector_name = _find_vector_field(mesh)
        if vector_name is None:
            print(f"  No vector field in {stem}, skipping.")
            continue

        mag = np.linalg.norm(mesh[vector_name], axis=1)  # type: ignore[index]
        clim = [0.0, float(mag.max()) if mag.max() > 0 else 1.0]

        print(f"Rendering {n_frames} frames for {stem}...")
        frames: list[Image.Image] = []
        camera_position = None
        for phase in phases:
            factor = warp_factor * np.sin(phase)
            warped = mesh.warp_by_vector(vectors=vector_name, factor=factor)
            warped.point_data["Displacement Magnitude"] = mag * abs(np.sin(phase))

            pl = pv.Plotter(off_screen=True, window_size=[800, 600])
            pl.add_mesh(
                warped,
                show_edges=False,
                scalars="Displacement Magnitude",
                cmap="coolwarm",
                clim=clim,
                scalar_bar_args={"title": "Displacement Magnitude"},
            )
            pl.add_axes()  # type: ignore[call-arg]
            if camera_position is None:
                pl.reset_camera()  # type: ignore[call-arg,attr-defined]
                pl.camera.azimuth -= 15
                camera_position = pl.camera_position
            else:
                pl.camera_position = camera_position
            img = pl.screenshot(return_img=True)
            pl.close()
            if img is not None:
                frames.append(Image.fromarray(img))

        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0,
        )
        print(f"  Saved {gif_path}")


def show_interactive_grid(results_dir: str = RESULTS_DIR):
    """Open an interactive PyVista window with all eigenmodes in a subplot grid."""
    result_files = _list_result_files(results_dir)
    if not result_files:
        print(f"No VTU or HDF files found in {results_dir}")
        return

    n = len(result_files)
    cols = 4
    rows = (n + cols - 1) // cols

    plotter = pv.Plotter(shape=(rows, cols))
    for i, result_path in enumerate(result_files):
        r, c = divmod(i, cols)
        plotter.subplot(r, c)

        mesh = pv.read(result_path)
        vector_name = _find_vector_field(mesh)
        if vector_name is None:
            continue

        warped = _warp_and_color(mesh, vector_name)

        plotter.add_mesh(
            warped,
            scalars="Displacement Magnitude",
            cmap="coolwarm",
            clim=[0, 0.04],
            show_edges=False,
        )
        plotter.add_axes()  # type: ignore[call-arg]
        plotter.add_text(
            os.path.splitext(os.path.basename(result_path))[0], font_size=8
        )

    plotter.link_views()
    plotter.show()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
