import math

x_vals: list[float] = []
y_vals: list[float] = []
f1_vals: list[float] = []
f2_vals: list[float] = []

grid_size = 100
for i in range(grid_size):
    for j in range(grid_size):
        x = i / (grid_size - 1)
        y = j / (grid_size - 1)
        f1 = x
        g  = 1 + 9*y
        f2 = g * (1 - math.sqrt(x / g))

        x_vals.append(x)
        y_vals.append(y)
        f1_vals.append(f1)
        f2_vals.append(f2)

qs.setoutputvalue("x", x_vals)
qs.setoutputvalue("y", y_vals)
qs.setoutputvalue("f1", f1_vals)
qs.setoutputvalue("f2", f2_vals)
