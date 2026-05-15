from typing import Callable, Literal

class SurrogateTrainProgress:
    epoch: int
    train_mae: float
    val_mae: float
    best_val_mae: float

    def __init__(
        self, epoch: int, train_mae: float, val_mae: float, best_val_mae: float
    ): ...

def train_surrogate_model(
    value_dataset_names: list[str],
    inputs: list[str | tuple[str, str]],
    outputs: list[str | tuple[str, str]],
    model_file_name: str,
    missing_value_behavior: Literal["error", "fill", "omit"] = "error",
    missing_value_fill: float = 0.0,
    epochs: int = 500,
    hidden_layer_size: int = 256,
    num_blocks: int = 2,
    dropout: float = 0.0,
    learning_rate: float = 0.001,
    step_size: int = 1000,
    gamma: float = 0.25,
    validation_split: float = 0.2,
    mae_limit: float = 0.0,
    progress_callback: Callable[[SurrogateTrainProgress], None] | None = None,
) -> None:
    """
    Trains a surrogate model based on the data in `value_dataset_names`. The names in
    `value_dataset_names` must be names given to value data inputs added to this
    simulation.

    `inputs` and `outputs` are the names of the input and output values in the value
    datasets. `inputs` and `outputs` along with `missing_value_behavior` and
    `missing_value_fill` are passed to the `get_table` method of the value datasets.
    See the documentation of `quanscient.experimental.ValueDataset.get_table` for more
    information. Here's how to import it to access the docs:

    >>> from quanscient.experimental import get_value_dataset
    >>> data = get_value_dataset("values")
    >>> data.get_table(["x", "y"])

    The best model is save to `model_file_name` each time the validation MAE improves.

    **Example**

    >>> train_surrogate_model(
    >>>     value_dataset_names=["values"],
    >>>     inputs=["x", "y"],
    >>>     outputs=["z"],
    >>>     model_file_name="model.ts",
    >>> )
    """
    ...

def get_surrogate_model(
    model_file_name: str,
) -> Callable[[list[list[float]]], list[list[float]]]:
    """
    Returns a function that evaluates the surrogate model for a list of input values.

    **Example**

    >>> model = get_surrogate_model("model.ts")
    >>> # This model takes three inputs and returns two outputs.
    >>> # Evaluate one sample:
    >>> model([[0.1, 0.2, 0.3]])
    >>> # --> [[0, 1]]
    >>> # Evaluate two samples at once:
    >>> model([[0.1, 0.2, 0.3], [1.1, 1.2, 1.3]])
    >>> # --> [[0, 1], [2, 3]]
    """
    ...

def find_pareto_front(
    inputs: list[str | tuple[str, str]],
    outputs: list[str | tuple[str, str]],
    input_bounds: list[tuple[float, float]],
    directions: list[Literal["minimize", "maximize"]],
    model_file_name: str,
    population_size: int = 100,
    num_generations: int = 200,
    random_seed: int = 42,
    save_solutions: bool = True,
) -> tuple[list[list[float]], list[list[float]]]:
    """
    Finds the pareto front using a surrogate model.
    """
    return ([], [])
