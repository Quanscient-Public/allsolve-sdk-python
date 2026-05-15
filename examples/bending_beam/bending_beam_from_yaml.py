"""
This script creates a project with a simplified bending beam simulation from a YAML file.

The simulation outputs:
- FieldOutput data that can be visualized in the Allsolve web app.
  Add a result visualization it the GUI for Displacement field and
  add a Warp filter. Then adjust the scale factor to view the displacement.
"""

from pathlib import Path

import allsolve

SCRIPT_DIR = Path(__file__).resolve().parent


def main():
    client = allsolve.Client()

    yaml_file = SCRIPT_DIR / "bending_beam_sweep.yaml"
    # Create project
    project = client.import_project(
        file_or_data=str(yaml_file),
        run_meshes_and_simulations=True,
        verbose=True,
    )

    print(f"Project: {project.name} (id: {project.id})")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error running project: {e}")
