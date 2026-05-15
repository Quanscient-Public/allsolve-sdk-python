# Smoke Tests

Integration tests that exercise the full SDK lifecycle against a real backend.

## Prerequisites

- Python 3.10+
- pytest: `pip install pytest`

## Credentials

Set the following environment variables (or add them to a `.env` file in the `tests` directory):

```bash
ALLSOLVE_ACCESS_KEY=<your-access-key>
ALLSOLVE_SECRET_KEY=<your-secret-key>
```

Optionally set `ALLSOLVE_HOST` if targeting other than the default server.

Tests are skipped automatically when credentials are missing.

## Running

In repository root run:

```bash
pytest tests/ -v -s
```

## What the tests do

Test creates a project, builds a full simulation (geometry, mesh, physics, simulation run),
verifies the results, then deletes every resource in reverse order before deleting the project.
Valid credentials with organization-level access are required.
