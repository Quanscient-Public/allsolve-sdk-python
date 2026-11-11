"""PMUT Pareto front demo — sklearn GP surrogates + pymoo NSGA-II."""

from pathlib import Path

import allsolve
import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.optimize import minimize as pymoo_minimize
from pymoo.termination import get_termination
from scipy.stats.qmc import LatinHypercube
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output"
DATA = OUTPUT / "data"
DATA.mkdir(parents=True, exist_ok=True)
SCRIPTS = HERE / "scripts"

VARIABLES = {
    "piezo_thick": (5.250e-07, 9.750e-07),
    "elastic_thick": (1.645e-06, 3.055e-06),
    "cavity_frac": (0.700, 0.850),
    "bot_elec_frac": (0.400, 0.900),
}
OBJECTIVES = ["tx_max", "fbw"]
CONSTRAINTS = ["fc"]
ALL_OUTPUTS = OBJECTIVES + CONSTRAINTS

FC_TARGET = 12e6  # centre-frequency target [Hz]
FC_TOL = 0.01  # ±1 %
N_INITIAL = 50
N_INFILL = 30
SEED = 42

VAR_NAMES = list(VARIABLES.keys())
LOWERS = np.array([VARIABLES[v][0] for v in VAR_NAMES])
UPPERS = np.array([VARIABLES[v][1] for v in VAR_NAMES])


def normalize(X):
    return (X - LOWERS) / (UPPERS - LOWERS)


def generate_samples(n, seed):
    unit = LatinHypercube(d=len(VAR_NAMES), rng=seed).random(n)
    return LOWERS + unit * (UPPERS - LOWERS)


def run_simulations(project, X, name):
    """Run parameter sweep through Allsolve and return output array."""
    n = X.shape[0]
    overrides = [
        (var, [str(X[i, j]) for i in range(n)]) for j, var in enumerate(VAR_NAMES)
    ]

    sweep = project.create_variable_overrides(
        name=name,
        overrides=overrides,
        sweep_type=allsolve.SweepType.SPECIFIC_VALUES,
    )

    mesh = project.get_meshes()[0]
    sim = next(s for s in project.get_simulations() if s.name == "template")

    mesh_override = mesh.create_override(sweep)
    sim.variable_overrides = sweep
    sim.save()

    mesh_override.run(print_logs=False)
    sim.run(print_logs=False)

    data = sim.get_output_data()
    nostep_idx = data.get_step_index(data.NO_STEP)
    Y = np.zeros((data.get_sweep_count(), len(ALL_OUTPUTS)))
    freqs, tx_mags = [], []
    for i in range(Y.shape[0]):
        for j, col in enumerate(ALL_OUTPUTS):
            Y[i, j] = data.get_value_at(i, nostep_idx, col)
        freq_vals = data.get_values_at(i, nostep_idx, "freq")
        txmag_vals = data.get_values_at(i, nostep_idx, "Txmag")
        freqs.append(np.asarray(freq_vals or [], dtype=float))
        tx_mags.append(np.asarray(txmag_vals or [], dtype=float))
    data.clean_cache()

    return Y, freqs, tx_mags


def fit_surrogates(X, Y):
    X_norm = normalize(X)
    kernel = ConstantKernel(1.0) * Matern(nu=2.5)
    models = []
    for j in range(Y.shape[1]):
        gp = GaussianProcessRegressor(
            kernel=kernel,
            normalize_y=True,
            alpha=1e-6,
            n_restarts_optimizer=10,
            random_state=SEED,
        )
        gp.fit(X_norm, Y[:, j])
        models.append(gp)
    return models


def find_pareto_front(surrogates):
    fc_lo = FC_TARGET * (1 - FC_TOL)
    fc_hi = FC_TARGET * (1 + FC_TOL)

    def _evaluate(self, X, out, *args, **kwargs):
        preds = np.column_stack([gp.predict(normalize(X)) for gp in surrogates])
        out["F"] = -preds[:, : len(OBJECTIVES)]
        fc = preds[:, len(OBJECTIVES)]
        out["G"] = np.column_stack([fc_lo - fc, fc - fc_hi])

    SurrogateProblem = type("SurrogateProblem", (Problem,), {"_evaluate": _evaluate})
    problem = SurrogateProblem(
        n_var=len(VAR_NAMES),
        n_obj=len(OBJECTIVES),
        n_ieq_constr=2,
        xl=LOWERS,
        xu=UPPERS,
    )
    res = pymoo_minimize(
        problem,
        NSGA2(pop_size=100),
        get_termination("n_gen", 300),
        seed=SEED,
        verbose=False,
    )
    return np.atleast_2d(res.X), -np.atleast_2d(res.F)


def select_infill(surrogates, n_select, seed):
    """Select infill points by maximum total GP uncertainty,
    filtered to candidates near the fc target (within 5x tolerance).
    """
    rng = np.random.default_rng(seed)
    candidates = LOWERS + rng.random((5000, len(VAR_NAMES))) * (UPPERS - LOWERS)
    cand_norm = normalize(candidates)

    fc_pred = surrogates[-1].predict(cand_norm)
    near_target = np.abs(fc_pred - FC_TARGET) / FC_TARGET <= FC_TOL * 5
    pool = candidates[near_target]
    pool_norm = cand_norm[near_target]

    if len(pool) < n_select:
        order = np.argsort(np.abs(fc_pred - FC_TARGET))[: max(n_select * 5, 500)]
        pool, pool_norm = candidates[order], cand_norm[order]

    total_var = sum(gp.predict(pool_norm, return_std=True)[1] ** 2 for gp in surrogates)
    return pool[np.argsort(-total_var)[:n_select]]


def print_validation_summary(F_pareto, Y_val):
    F_actual = Y_val[:, : len(OBJECTIVES)]
    fc_actual = Y_val[:, len(OBJECTIVES)]

    for j, name in enumerate(OBJECTIVES):
        rel = np.abs(F_pareto[:, j] - F_actual[:, j]) / (np.abs(F_actual[:, j]) + 1e-30)
        print(f"  {name}: mean rel. error = {rel.mean():.1%}, max = {rel.max():.1%}")

    fc_lo, fc_hi = FC_TARGET * (1 - FC_TOL), FC_TARGET * (1 + FC_TOL)
    feasible = np.sum((fc_actual >= fc_lo) & (fc_actual <= fc_hi))
    print(f"  fc constraint: {feasible}/{len(fc_actual)} feasible")


def save_csv(path, X, Y, out_names):
    header = ",".join(VAR_NAMES + out_names)
    np.savetxt(path, np.hstack([X, Y]), delimiter=",", header=header, comments="")


def main():
    client = allsolve.Client()

    project = client.import_project(
        str(HERE / "pmut_surrogate.yaml"),
        run_meshes_and_simulations=False,
    )

    sim = next(s for s in project.get_simulations() if s.name == "template")
    sim.set_scripts(
        [
            allsolve.Script(
                name="postprocessing.py",
                section_name=allsolve.CustomSection.AFTER_ALL,
                filepath=str(SCRIPTS / "postprocessing.py"),
            ),
        ]
    )

    try:
        # Initial DOE
        print(f"Generating {N_INITIAL} LHS samples and simulating …")
        X = generate_samples(N_INITIAL, SEED)
        Y, _, _ = run_simulations(project, X, name="pmut_doe")
        surrogates = fit_surrogates(X, Y)

        # Adaptive infill — pick points with highest surrogate uncertainty near fc target
        print(f"Selecting {N_INFILL} infill points and simulating …")
        X_new = select_infill(surrogates, N_INFILL, seed=SEED + 1)
        Y_new, _, _ = run_simulations(project, X_new, name="pmut_infill")
        X = np.vstack([X, X_new])
        Y = np.vstack([Y, Y_new])
        surrogates = fit_surrogates(X, Y)

        # Optimise
        print("Running NSGA-II …")
        X_pareto, F_pareto = find_pareto_front(surrogates)
        print(f"  {len(X_pareto)} Pareto designs found.")

        # Validate
        print("Validating Pareto designs (full fidelity) …")
        Y_val, freqs, tx_mags = run_simulations(
            project,
            X_pareto,
            name="validation",
        )
        print_validation_summary(F_pareto, Y_val)

        # Save
        save_csv(DATA / "dataset.csv", X, Y, ALL_OUTPUTS)
        save_csv(DATA / "pareto.csv", X_pareto, F_pareto, OBJECTIVES)
        save_csv(DATA / "validation.csv", X_pareto, Y_val, ALL_OUTPUTS)
        np.savez(
            DATA / "freq_response.npz",
            n_designs=len(freqs),
            n_initial=N_INITIAL,
            **{f"freq_{i}": f for i, f in enumerate(freqs)},
            **{f"txmag_{i}": t for i, t in enumerate(tx_mags)},
        )
        print(f"Done — results under {DATA}/")

    except Exception as e:
        print(f"Error running project: {e}")
    finally:
        if input("\nDelete project? [Y/n]: ").strip().lower() in ("", "y", "yes"):
            project.delete()


if __name__ == "__main__":
    main()
