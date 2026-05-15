from quanscient.experimental.multiphysicsai import find_pareto_front

find_pareto_front(
    inputs=["x", "y"],
    outputs=["f1", "f2"],
    model_file_name="model.ts",
    input_bounds=[(0, 1), (0, 1)],
    directions=["maximize", "maximize"],
)