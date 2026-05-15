"""
This script creates a project that trains a neural network surrogate model.
It uses simple dummy data as the training data.
"""

from types import SimpleNamespace
import allsolve


def main():
    client = allsolve.Client()

    project = client.create_project(
        name="Surrogate model training",
        description="Example project that trains a surrogate model for a simulation",
    )

    print(f"Created project: {project.name} (id: {project.id})")

    try:
        setup_project(project)
    except Exception as e:
        print(f"Error setting up project: {e}")
    finally:
        print("Deleting project")
        project.delete()


def setup_project(project: allsolve.Project):
    print("Creating variables")

    project.create_variable(
        name="hidden_layer_size",
        expression=32,
        description="The size of the hidden layers in the surrogate model neural network",
    )
    project.create_variable(
        name="epochs",
        expression=300,
        description="How many epochs to train the surrogate model. One epoch means one full pass through the training data.",
    )
    project.create_variable(
        name="num_blocks",
        expression=1,
        description="How many blocks should the surrogate model neural network have. This relates directly to the depth of the neural network.",
    )

    print("Setup training data generation simulation")

    sims = SimpleNamespace()
    sims.generate_training_data = project.create_simulation_static(
        name="Generate training data",
        description="This simulation generates the training data for the surrogate model. In a real use case, you'd replace this one with a simulation that generates the training data.",
        max_run_time_minutes=10,
    )
    sims.generate_training_data.set_scripts(
        [
            allsolve.Script(
                is_main=True,
                filepath="./simulation_scripts/generate_training_data.py",
            )
        ]
    )

    print("Setup surrogate model training simulation")

    sims.train_surrogate_model = project.create_simulation_static(
        name="Train surrogate model",
        description="This simulation takes in the training data from the training data generation simulation and trains the surrogate model.",
        max_run_time_minutes=60,
    )
    sims.train_surrogate_model.set_scripts(
        [
            allsolve.Script(
                is_main=True,
                filepath="./simulation_scripts/train_surrogate_model.py",
            )
        ]
    )
    # Input the training data from `sims.generate_training_data`
    sims.train_surrogate_model.add_input_value_outputs_from_simulation(
        source_simulation=sims.generate_training_data,
        target_file_name="training_data",
    )

    print("Setup pareto front analysis simulation")

    sims.find_pareto_front = project.create_simulation_static(
        name="Find pareto front",
        description="This simulation takes in the surrogate model and analyzes the Pareto front.",
        max_run_time_minutes=10,
    )
    sims.find_pareto_front.set_scripts(
        [
            allsolve.Script(
                is_main=True,
                filepath="./simulation_scripts/find_pareto_front.py",
            )
        ]
    )
    # Input the surrogate model file from `sims.train_surrogate_model`
    sims.find_pareto_front.add_input_file_from_simulation(
        source_simulation=sims.train_surrogate_model,
        source_file_name="model.ts",
        target_file_name="model.ts",
    )

    print("Setup post-processing simulation")

    sims.post_processing = project.create_simulation_static(
        name="Post-process",
        description="This simulation demonstrates how to read in the output data from another simulation and perform arbitrary post-processing on it.",
        max_run_time_minutes=10,
    )
    sims.post_processing.set_scripts(
        [
            allsolve.Script(
                is_main=True,
                filepath="./simulation_scripts/post_process.py",
            )
        ]
    )
    # Input the pareto front solutions from `sims.find_pareto_front`
    sims.post_processing.add_input_value_outputs_from_simulation(
        source_simulation=sims.find_pareto_front,
        target_file_name="pareto_front_solutions",
    )

    for name, sim in [
        ("Generate training data", sims.generate_training_data),
        ("Train surrogate model", sims.train_surrogate_model),
        ("Find pareto front", sims.find_pareto_front),
        ("Post-process", sims.post_processing),
    ]:
        print()
        print("=" * 80)
        print(f"Running simulation: {name}")

        sim.start()
        while sim.is_running(refresh_delay_s=1):
            sim.print_new_loglines()

        sim.print_new_loglines()
        print("Simulation finished with status:", sim.get_status())


if __name__ == "__main__":
    main()
