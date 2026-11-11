# Advanced simulation scripts

This reference covers advanced solver script techniques: custom time loops, genalpha internals, and operator and DOF extraction. Read [simulation-scripts.md](simulation-scripts.md) first.

### Custom time loops

- **When modifying the solve loop, copy the project's own generated loop** — save it with `sim.save_generated_scripts("./generated_scripts/")` (it also saves the main simulation script). Disable SOLVE and re-inject an edited copy at `AFTER_FORMULATIONS_CREATED`.
- **Per-step Dirichlet update works** — re-call `fld.p.setconstraint(...)` before each `timestepper.allnext(...)`.

### Advanced

- **`genalpha` is consistent-mass with no lumping knob; its default IS Newmark.** There is no switch for lumped (diagonal) mass.
- **`genalpha` with moving-Dirichlet coupling adds a large reflection,** much larger than a custom lumped-mass Newmark loop. Do not use `genalpha` for Dirichlet interface regions.
- **`formulation.b()` returns the NEGATED nodal load** — negate `b()` to get internal stiffness force.
- **`vec` has no coordinate info** — build a DOF-to-coordinate map by setting the field to coordinates, gathering into a vec, and reading all entries.
- **Extract operator matrix column-by-column** — set field to each basis function via `qs.grid` indicator, then read `-form.b()` = column j.
