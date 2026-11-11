# Allsolve SDK agent skills

Agent skills that teach AI coding agents to build, run and debug multiphysics cloud simulations with the [Allsolve Python SDK](https://github.com/Quanscient-Public/allsolve-sdk-python) (`pip install allsolve`).

The skills follow the [Agent Skills](https://agentskills.io) format: each skill is a folder with a `SKILL.md` file. They work with any client that reads Agent Skills, for example Claude Code, Cursor and Codex.

## Skills

| Skill | Use |
|---|---|
| `allsolve-sdk` | Entry skill. Setup, build order, gotchas, and links to the building-block references in `allsolve-sdk/references/` (project workflow, variables and sweeps, geometry, regions, materials, physics, mesh, simulation, solver scripts, post-processing, docs map) |
| `allsolve-domain-rf` | RF, microwave and antenna models (full-wave EM, eigenmode ports, S-parameters) |
| `allsolve-domain-structural` | Structural mechanics (static deflection, stress, eigenmodes, MEMS from GDSII) |
| `allsolve-domain-thermal` | Heat transfer (convection, heat sources, Joule heating, transient thermal) |
| `allsolve-domain-acoustics` | Acoustic, elastic-wave and piezoelectric devices (PMUT, CMUT, FBAR, transducers) |

The domain skills link to `../allsolve-sdk/references/`, so install all five folders next to each other.

## Install

Copy or symlink the five skill folders into the skills folder of your client. Keep them side by side.

```bash
# Example: personal skills folder of Claude Code
mkdir -p ~/.claude/skills
for s in allsolve-sdk allsolve-domain-rf allsolve-domain-structural allsolve-domain-thermal allsolve-domain-acoustics; do
  ln -s "$PWD/$s" ~/.claude/skills/$s     # or: cp -R "$s" ~/.claude/skills/
done
```

Common skills folders:

| Client | Personal | Project |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` |
| Codex | `~/.codex/skills/` | `.codex/skills/` |

Other clients: see their documentation for the skills folder. A client that does not read skills can still use them: point the agent at `allsolve-sdk/SKILL.md`.

## Prerequisites

- Python 3.10+ and `pip install allsolve`
- An Allsolve organization API key in `.env` (see `allsolve-sdk/SKILL.md` → Setup)
- Optional: a shallow clone of the SDK repo, so the agent can grep the examples and the source

No MCP server is needed. The skills tell the agent to grep the SDK examples and source, and to fetch the documentation pages listed in `allsolve-sdk/references/docs-map.md`.

## Version

The skills target Allsolve SDK 0.5.3. See "Version notes" in `allsolve-sdk/SKILL.md`.
