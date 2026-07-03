"""
Example demonstrating the import-export cycle.

This script shows how to:
1. Import a project from YAML
2. Optionally modify it
3. Export it back to YAML/JSON

The exported file should be semantically equivalent to the imported one,
though formatting may differ slightly.
"""

import os
import allsolve


def main():

    script_dir = os.path.dirname(os.path.abspath(__file__))

    client = allsolve.Client()

    # Import project from YAML
    input_file = os.path.join(script_dir, "import-format.yaml")
    print(f"Importing project from {input_file}...")
    project = client.import_project(input_file)
    print(f"Created project: {project.name} (id: {project.id})")

    # You can modify the project here if needed
    # project.create_variable(name="new_var", expression="42")

    # Export to YAML
    output_yaml = os.path.join(script_dir, "exported-project.yaml")
    print(f"\nExporting project to {output_yaml}...")
    project.export_yaml(output_yaml)
    print("Exported successfully!")

    # Export to JSON
    output_json = os.path.join(script_dir, "exported-project.json")
    print(f"Exporting project to {output_json}...")
    project.export_json(output_json)
    print("Exported successfully!")

    # You can also get the export data as a dictionary
    data = project.export()
    print(f"\nExport contains {len(data.get('variables', []))} variables")
    print(f"Export contains {len(data.get('regions', []))} regions")
    print(f"Export contains {len(data.get('materials', []))} materials")
    print(f"Export contains {len(data.get('meshes', []))} meshes")

    # Clean up
    print("\nDeleting project...")
    project.delete()
    print("Done!")


if __name__ == "__main__":
    main()
