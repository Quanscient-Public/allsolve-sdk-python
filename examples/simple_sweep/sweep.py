import os
import pathlib
import matplotlib.pyplot as plt
import allsolve


api_key = os.environ["QS_ACCESS_KEY"]
api_secret = os.environ["QS_SECRET_KEY"]
allsolve.setup(
    api_key=api_key,
    api_secret=api_secret,
    host="https://testing-eu-west-1.quanscient.com",
)

project = allsolve.Project.from_token()


def start_sim(pressure, paramfile, template_sim):
    sim = allsolve.Simulation.copy_simulation(simulation_id=template_sim.id)
    print("Starting {}, id {}".format(sim.name, sim.id))

    sim.set_scripts(
        [
            allsolve.Script("sim/main.py", is_main=True),
        ]
    )

    sim.set_runtime(
        allsolve.Runtime(
            node_count=1,
            node_type=allsolve.CPU.CORES_1_16GB,
        )
    )

    sim.set_shared_files([paramfile])
    sim.add_json_file("params.json", {"pressure": pressure})

    sim.start()

    return sim


sims = []
u_maxes = []

try:
    print("Project: {}".format(project.name))

    paramfile = project.add_shared_json_file("common_params.json", {"commonValue": 10})

    print(project.get_files())

    all_sims = project.get_simulations()

    # Delete all other than the template simulation, which is at index 0 to cleanup old results
    for sim in all_sims[1:]:
        sim.delete()

    template_sim = all_sims[0]

    pressures = list(range(1000, 10000, 1000))
    for pressure in pressures:
        sim = start_sim(pressure, paramfile, template_sim)
        sims.append(sim)

    for i, sim in enumerate(sims):
        while sim.is_running(refresh_delay_s=1):
            pass

        if sim.get_status() != allsolve.Job.SUCCESS:
            raise ValueError("Simulation failed")

        for step, values in sim.get_output_values().items():
            u_maxes.append(values["u_max"])

        outdir: pathlib.Path = pathlib.Path("./sim_{}_res".format(i))
        outdir.mkdir(parents=True, exist_ok=True)

        sim.save_output_field("u", output_dir=str(outdir))

    print(u_maxes)

    fig, ax = plt.subplots()
    ax.plot(pressures, u_maxes)

    plt.show()

except Exception as e:
    print("Something failed, aborting all sims")
    print(e)
    for sim in sims:
        if sim.is_running():
            sim.abort()
