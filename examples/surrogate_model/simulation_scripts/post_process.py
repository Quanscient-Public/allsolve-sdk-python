
from quanscient.experimental import get_value_dataset
import numpy as np

data = get_value_dataset("pareto_front_solutions")
solutions = np.array(list(data.get_table(["x", "y", "f1", "f2"])))
print(solutions)