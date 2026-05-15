"""
Simple interactive script for editing an Allsolve project using YAML file on disk.

After selecting a project, you can keep the project open in the browser tab,
export the project to a YAML file, do some modifications to the YAML file,
import the YAML file back to the project, and refresh the browser tab to see the changes.

Project selection (in priority order):
  1. PROJECT_ID - use a project by ID specified in this script.
  2. PROJECT_NAME - search for a a project by unique name specified in this script.
  3. CURRENT_PROJECT - use the current project set using client.set_current_project().
  4. NEW_PROJECT - create a new project interactively.
  5. PROJECT_ID - use a project by ID specified interactively.

Supported operations:
  - Export project to a YAML file.
  - Import project from a YAML file, optionally resetting the project data first,
    then running meshes & simulations after import.
  - Reset project data (but keep the project itself).
  - Delete project entirely.
"""

import allsolve
import os

# Set one of these to skip the interactive project selection prompt.
PROJECT_ID = ""
PROJECT_NAME = ""

# Define custom YAML file to import / export. If not set, the project name will be used.
YAML_FILE = ""
# Files are saved to same directory as this script by default.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    client = allsolve.Client()
    print(f"Connected to {client.host}")

    project = get_project(client)

    print(f"Project: {project.name} (id: {project.id})")
    print(f"See the project in the browser: {client.get_url(project)}")

    operations = {
        "1": ("Export project", export_project_yaml),
        "2": ("Import project", import_project_yaml),
        "3": ("Reset project", reset_project),
        "4": ("Delete project", delete_project),
    }

    while True:
        print()
        for key, (label, _) in operations.items():
            print(f"{key}. {label}")
        print("5. Exit")

        choice = input("\nEnter your choice: ").strip()

        if choice == "5":
            break

        if choice not in operations:
            print(f"Invalid choice: {choice!r}. Please enter a number 1-5.")
            continue

        label, operation = operations[choice]
        try:
            operation(client, project)
        except Exception as e:
            print(f"Error during '{label}': {e}")


def get_project(client: allsolve.Client) -> allsolve.Project:
    if PROJECT_ID:
        return allsolve.Project.get(PROJECT_ID)
    elif PROJECT_NAME:
        project = client.get_project_by_name(PROJECT_NAME)
        if project is None:
            raise ValueError(f"Project with name {PROJECT_NAME} not found")
        return project
    else:
        current_project = client.get_current_project()
        if current_project is not None:
            answer = (
                input(f"Use project '{current_project.name}'? [Y/n] ").strip().lower()
            )
            if answer in ("", "y", "yes"):
                return current_project
            client.set_current_project(None)
            print("Current project unset")

        answer = input("Create a new project? [Y/n] ").strip().lower()
        if answer in ("", "y", "yes"):
            name = input("Enter project name: ").strip()
            description = input("Enter project description: ").strip()
            project = client.create_project(name=name, description=description)
            print(f"Created project: {project.name} (id: {project.id})")
            client.set_current_project(project)
            print(f"Current project set to {project.name} (id: {project.id})")
            return project
        else:
            project_id = input("Enter project id: ").strip()
            project = allsolve.Project.get(project_id)
            if project is None:
                raise ValueError(f"Project with id {project_id} not found")
            client.set_current_project(project)
            print(f"Current project set to {project.name} (id: {project.id})")
            return project


def export_project_yaml(client: allsolve.Client, project: allsolve.Project):
    filename = YAML_FILE or f"{project.name}.yaml"
    client.export_project_yaml(
        project,
        output_path=os.path.join(SCRIPT_DIR, filename),
        download_geometries=True,
        files_output_dir=SCRIPT_DIR,
        file_overwrite_mode=allsolve.FileOverwriteMode.SKIP,
    )
    print(f"Exported project to {filename}")


def import_project_yaml(client: allsolve.Client, project: allsolve.Project):
    filename = YAML_FILE or f"{project.name}.yaml"
    if not os.path.exists(os.path.join(SCRIPT_DIR, filename)):
        raise FileNotFoundError(f"File {filename} not found")

    print(f"Using {filename} to import project data.")

    # Optionally reset existing project data before importing
    reset_project(client, project)

    print(f"Importing project data...")
    project = client.import_project(
        file_or_data=os.path.join(SCRIPT_DIR, filename),
        project_to_modify=project,
        verbose=True,
        run_meshes_and_simulations=False,
    )
    print(f"Imported project: {project.name} (id: {project.id})")

    meshes = project.get_meshes()
    simulations = project.get_simulations()
    if meshes or simulations:
        answer = input("Run meshes and simulations? [Y/n] ").strip().lower()
        if answer in ("", "y", "yes"):
            print("Running meshes and simulations...")
            for mesh in meshes:
                mesh.run(print_logs=True)
                print(f"Mesh '{mesh.name}' status: {mesh.get_status()}")
            for simulation in simulations:
                simulation.run(print_logs=True)
                print(
                    f"Simulation '{simulation.name}' status: {simulation.get_status()}"
                )
    print("Done")


def reset_project(_client: allsolve.Client, project: allsolve.Project):
    answer = input("Reset project? [Y/n] ").strip().lower()
    if answer in ("", "y", "yes"):
        print("Resetting project...")
        for sim in project.get_simulations():
            sim.delete()
        for mesh in project.get_meshes():
            mesh.delete()
        for physic in project.get_physics():
            for interaction in physic.interactions:
                interaction.delete()
            physic.delete()
        for material in project.get_materials():
            material.delete()
        for region in project.get_regions():
            region.delete()
        project.geometry_builder().delete()
        for interpolated_function in project.get_interpolated_functions():
            interpolated_function.delete()
        for function in project.get_functions():
            function.delete()
        for var in reversed(project.get_variables()):
            var.delete()
        for file in project.get_files():
            allsolve.delete_file(file, project.id)
        print("Project reset")
    else:
        print("Project not reset")


def delete_project(client: allsolve.Client, project: allsolve.Project):
    answer = input("Delete project? [Y/n] ").strip().lower()
    if answer in ("", "y", "yes"):
        client.set_current_project(None)
        print("Current project unset")
        project.delete()
        raise SystemExit("Project deleted, exiting...")
    else:
        print("Project not deleted")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit("\nAborted.")
