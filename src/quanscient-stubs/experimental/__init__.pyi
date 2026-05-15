import math
from typing import Iterator, Literal

NO_STEP = -math.inf

class ValueDataset:
    def __init__(self, working_dir=".", dataset_name="values"): ...
    def get_table(
        self,
        columns: list[str | tuple[str, str]],
        missing_value_behavior: Literal["error", "fill", "omit"] = "error",
        missing_value_fill: float = 0.0,
    ) -> Iterator[list[float]]:
        """
        Read tabular data from the value dataset.

        The columns can be any of the value names that were saved to the dataset in
        the input simulation using the `qs.setoutputvalue` function. If you've saved
        values with specifiers, you can use a tuple. For example ("impedance", "real").

        Two special columns "sweep_step" and "step" are supported. "sweep_step" is
        the index of the sweep step that saved the data and "step" is the time step
        or eigenvalue index that saved the data. If a value was saved without a step,
        the step is set to the value of the `NO_STEP` constant.

        You can also add any of the simulation's variable overrides in the columns
        list and those will be filled with the value of the simulation that saved
        the data.

        The data is returned in an "exploded" format. If a single step in a single
        sweep step has `x` with one value and `y` with ten values, then ten rows
        will be added to the return value, where the same `x` is repeated for
        each `y` value.

        If steps with missing values are found, the behavior is determined by the
        `missing_value_behavior` parameter. If it is "error", a ValueError is raised.
        If it is "fill", the missing value is filled with the value of the
        `missing_value_fill` parameter. If it is "omit", the step is omitted.
        As an example, let's assume you've saved values `x` and `y` for each time
        step of a transient simulation, and you've also saved `s` without specifying
        a step. `s` could be, for example, some kind of statistic over all the time
        steps. If you want to get all values of `x` and `y`, but ignore `s`, you need
        to set the `missing_value_behavior` parameter to "omit". Otherwise the code
        will hit the row for `s` and not find values for `x` and `y` in it, which
        will raise an error.

        **Example**

        >>> data = get_value_dataset("values")
        >>> for row in data.get_table(["step", "x", "y"]):
        >>>     # Each row is a list of float values, one for each column.
        >>>     print(row)

        >>> data = get_value_dataset("values")
        >>> for row in data.get_table([("impedance", "real"), ("impedance", "imaginary")]):
        >>>     # Each row is a list of float values, one for each column.
        >>>     print(row)

        >>> data = get_value_dataset("values")
        >>> # You can turn a table into a numpy array like this:
        >>> arr = np.array(list(data.get_table(["step", "x", "y"])))
        >>> print(arr)
        """
        ...

    def _db_step_to_str(self, sweep_step: int, step: float) -> str: ...

def get_value_dataset(dataset_name: str) -> ValueDataset:
    """
    Returns an object for accessing value data added as an input to this simulation.

    **Example**

    >>> data = get_value_dataset("My dataset")
    >>> for row in data.get_table(["step", "x", "y"]):
    >>>     # Each row is a list of float values, one for each column.
    >>>     print(row)
    """
    return ValueDataset()
