# Quanscient Allsolve SDK

[![PyPI version](https://img.shields.io/pypi/v/allsolve)](https://pypi.org/project/allsolve/)
[![Python](https://img.shields.io/pypi/pyversions/allsolve)](https://pypi.org/project/allsolve/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Python SDK for [Quanscient Allsolve](https://allsolve.quanscient.com/) — a cloud-based multiphysics simulation platform.

Automate multiphysics simulations from Python. Define geometry, materials, physics, and boundary conditions in code — then solve in the cloud.

- **Multiphysics simulation** — structural, electromagnetic, acoustic, thermal, fluid, and coupled physics
- **Geometry tools** — programmatic primitives & operations, or import STEP / IGES / GDS2 / mesh files
- **Parametric sweeps** — run thousands of design variations with a single script
- **Cloud-native** — no local solvers to install; results stream back to your Python session
- **Export & reproduce** — serialize entire projects to YAML/JSON for version control and sharing

## Installation

Requires Python 3.10 or newer.

```bash
pip install allsolve
```

## Authentication

Create an Organization API key in the Allsolve web UI:

**Settings > API keys > "Create key"**

Then create a `.env` file with your credentials:

```
ALLSOLVE_ACCESS_KEY=your-access-key-here
ALLSOLVE_SECRET_KEY=your-secret-key-here
ALLSOLVE_HOST=https://allsolve.quanscient.com/
```

Or pass them directly:

```python
client = allsolve.Client(
    api_key="your-access-key-here",
    api_secret="your-secret-key-here",
)
```

## Quick Start

```python
import allsolve

client = allsolve.Client(dotenv_file=".env")

project = client.create_project(
    name="My Simulation",
    description="Created with Allsolve SDK",
)
print(f"Project URL: {client.get_url(project)}")
```

## Examples

See the [`examples/`](examples/) directory for complete working examples, including:

- **hello_world** — Create and delete a project
- **bending_beam** — Parametric sweep of a bending beam simulation
- And more

## AI agent skills

The [`plugins/allsolve/skills/`](plugins/allsolve/skills/) directory has [Agent Skills](https://agentskills.io) that teach AI coding agents (Claude Code, Cursor, Codex and others) to build, run and debug Allsolve simulations with this SDK: an entry skill `allsolve-sdk` and domain skills for RF, structural, thermal and acoustics.

Install them in Claude Code as a plugin:

```bash
claude plugin marketplace add Quanscient-Public/allsolve-sdk-python
claude plugin install allsolve@quanscient
```

Get new versions with `claude plugin update allsolve@quanscient`, or turn on auto-update in `/plugin` → Marketplaces → quanscient. To use the skills of an older SDK version, add the marketplace at that version's tag: `claude plugin marketplace add Quanscient-Public/allsolve-sdk-python#v<version>`.

For other clients, see [plugins/allsolve/skills/README.md](plugins/allsolve/skills/README.md).

## Documentation

- **SDK reference**: <https://allsolve.quanscient.com/documentation/reference/allsolve-sdk>
- **Full documentation**: <https://allsolve.quanscient.com/documentation>

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

This project is licensed under the Apache License 2.0 — see [LICENSE](LICENSE) for details.
