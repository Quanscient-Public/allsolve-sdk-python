import numpy as np
from scipy.optimize import least_squares
from scipy.optimize import Bounds
from scipy.optimize import differential_evolution
import multiprocessing as mp

import os
import matplotlib.pyplot as plt
import allsolve

api_key = os.environ["QS_ACCESS_KEY"]
api_secret = os.environ["QS_SECRET_KEY"]
allsolve.setup(
    api_key=api_key,
    api_secret=api_secret,
    host="https://allsolve.quanscient.com",
)

project = allsolve.Project.from_token()

all_sims = project.get_simulations()

template_sim = all_sims[0]


def start_sim(param, template_sim):

    sim = allsolve.Simulation.copy_simulation(simulation_id=template_sim.id)
    print("Starting {}, id {}".format(sim.name, sim.id))

    sim.max_run_time_minutes = 10
    sim.save()

    sim.set_scripts(
        [
            allsolve.Script("sim/main.py", is_main=True),
        ]
    )

    sim.set_runtime(
        allsolve.Runtime(
            node_count=1,
            node_type=allsolve.CPU.CORES_3_10GB_FAST_START,
        )
    )

    sim.add_json_file("params.json", {"E": param[0], "G": param[1]})

    sim.start()

    return sim


def residual(param):

    global template_sim

    sim = start_sim(param, template_sim)
    while sim.is_running(refresh_delay_s=1):
        pass

    if sim.get_status() != allsolve.Job.SUCCESS:
        raise ValueError("Simulation failed")

    values = sim.get_output_values()["nostep"]
    ifreq1 = values["Eigenfrequencies"][0]
    ifreq2 = values["Eigenfrequencies"][2]
    ifreq3 = values["Eigenfrequencies"][4]

    res = pow(
        (
            (ifreq1 - 81266.7953118201) ** 2 / 81266.7953118201**2
            + (ifreq2 - 487160) ** 2 / 487160**2
            + (ifreq3 - 711235) ** 2 / 711235**2
        )
        / 3.0,
        0.5,
    )
    print("Residual: " + str(res))

    with open("iterations.csv", "a") as outfile:
        outfile.write(
            str(param[0])
            + ", "
            + str(param[1])
            + ", "
            + str(res)
            + ", "
            + str(ifreq1)
            + ", "
            + str(ifreq2)
            + ", "
            + str(ifreq3)
            + "\n"
        )

    # Delete the simulation for this step to cleanup
    sim.delete()

    return res


def objective(param):
    try:
        return residual(param)
    except Exception as e:
        print(e)
        return np.inf


# This if is required for multiprocessing to work, as it loads the module
# multiple times.
if __name__ == "__main__":
    print("Project: " + project.name)

    # Cleanup previous runs
    for sim in all_sims[1:]:
        sim.delete()

    with open("iterations.csv", "w") as outfile:
        outfile.write("E,G,Residual,Freq1,Freq2,Freq3\n")

    x0 = np.array([6.0, 3.0])
    bounds = Bounds([5, 2], [7, 4])

    num_workers = 10

    with mp.Pool(num_workers) as pool:
        result = differential_evolution(
            objective,
            bounds,
            x0=x0,
            updating="deferred",
            workers=pool.map,
            maxiter=250,
            popsize=8,
        )

    fig, ax = plt.subplots()

    data = np.genfromtxt("iterations.csv", delimiter=",", dtype=float, skip_header=True)
    x = data[:, 0]
    y = data[:, 1]
    normed_residual = (data[:, 2] - np.min(data[:, 2])) / np.min(data[:, 2])
    ax.scatter(
        data[:, 0],
        data[:, 1],
        c="black",
        alpha=1 - normed_residual / np.max(normed_residual),
    )

    plt.xlabel("Young's modulus [Pa] x 1e10")
    plt.ylabel("Shear modulus [Pa] x 1e10")
    plt.savefig("scatterplot.pdf", bbox_inches="tight")
    plt.show()
