"""
Hello World example for the AllSolve SDK.

Demonstrates how to:
  1. Authenticate (from a .env file or by entering credentials manually)
  2. Create a project
  3. Clean up (delete the project and optionally the .env file)

Run:
    python hello_world.py
"""

import getpass
import os
from datetime import datetime

import allsolve


def _save_dotenv(path: str, api_key: str, api_secret: str, host: str) -> None:
    """Write credentials to a .env file with restricted permissions (owner-only).

    On Windows the 0o600 mode is effectively ignored (only read-only vs
    read-write is distinguished), so the file will have default ACLs.
    """
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(f'ALLSOLVE_ACCESS_KEY="{api_key}"\n')
        f.write(f'ALLSOLVE_SECRET_KEY="{api_secret}"\n')
        f.write(f'ALLSOLVE_HOST="{host}"\n')


def main() -> None:
    dotenv_file = None
    project = None

    try:
        # --- Authenticate -----------------------------------------------

        if input("Load credentials from a .env file? [y/N]: ").strip().lower() == "y":
            dotenv_file = input("Filename [.env]: ").strip() or ".env"

            # Create Client from .env file
            client = allsolve.Client(dotenv_file=dotenv_file)
        else:
            api_key = input("API key: ").strip()
            api_secret = getpass.getpass("API secret: ").strip()
            host = input("Host [https://allsolve.quanscient.com/]: ").strip() or None

            # Create Client with explicit credentials
            client = allsolve.Client(api_key=api_key, api_secret=api_secret, host=host)

            if input("Save credentials to a .env file? [y/N]: ").strip().lower() == "y":
                dotenv_file = input("Filename [.env]: ").strip() or ".env"
                _save_dotenv(dotenv_file, api_key, api_secret, client.host)
                print(f"Credentials saved to {dotenv_file}")

        print(f"Connected to {client.host}")

        # --- Create project ---------------------------------------------

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            project = client.create_project(
                name="Hello, Allsolve",
                description=f"Created with Allsolve SDK at {timestamp}",
            )
        except Exception as e:
            print(f"Failed to create project: {e}")
            return

        print(f"Created project: {project.name} (id: {project.id})")
        print(f"See the project in the API projects page: {client.host}/#/projects/api")
        print(f"or open the project in the browser: {client.get_url(project)}")

        input("Press Enter to continue...")

        # --- Clean up ---------------------------------------------------

        if input("Delete project? [Y/n]: ").strip().lower() != "n":
            project.delete()
            project = None
            print("Project deleted.")

        if dotenv_file and os.path.isfile(dotenv_file):
            if input(f"Delete {dotenv_file}? [y/N]: ").strip().lower() == "y":
                os.remove(dotenv_file)
                print(f"{dotenv_file} deleted.")

    except KeyboardInterrupt:
        print("\nAborted.")
        if project is not None:
            try:
                project.delete()
                print("Cleaned up project from server.")
            except Exception:
                print(
                    f"Warning: project '{project.name}' (id: {project.id}) "
                    "may still exist on the server."
                )


if __name__ == "__main__":
    main()
