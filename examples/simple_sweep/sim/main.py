import csv
import json
import quanscient as qs
from utils import Mesh, Variables, Empty, Fields
from expressions import expr
from materials import mat
from regions import reg
from parameters import par

var = Variables()
mesh = Mesh()
fld = Fields()

# Load the mesh
mesh.mesh = qs.mesh()
mesh.mesh.setphysicalregions(*reg.get_region_data())
mesh.skin = reg.get_next_free()
mesh.mesh.selectskin(mesh.skin)
mesh.mesh.partition()
mesh.mesh.load("gmsh:simulation.msh", mesh.skin, 1, 1)

# Displacement field
fld.u = qs.field("h1xyz", [1])
fld.u.setorder(reg.all, 2)

# Clamp interaction
fld.u.setconstraint(reg.clamp_target)

form = qs.formulation()

# Solid mechanics
form += qs.integral(reg.all, qs.predefinedelasticity(qs.dof(fld.u), qs.tf(fld.u), par.H()))

with open("params.json") as f:
    inputs = json.load(f)

# Pressure interaction
form += qs.integral(reg.pressure_target, -inputs["pressure"] * qs.normal(reg.all) * qs.tf(fld.u))

form.allsolve(relrestol=1e-06, maxnumit=1000, nltol=1e-05, maxnumnlit=-1, relaxvalue=-1)

# Field output: u
qs.setoutputfield("u", reg.all, fld.u, 2)

# Value output: u_max
var.discrete = qs.evaluate(qs.allmax(reg.aluminium_target, qs.compz(fld.u), 5))
qs.setoutputvalue("u_max", var.discrete)
