import math
import csv
import json
from functools import cache
import quanscient as qs
from utils import Mesh, Variables, Empty, Fields, DerivedFields
from expressions import expr
from materials import mat
from regions import reg

var = Variables()
mesh = Mesh()
fld = Fields()
df = DerivedFields()

# Load the mesh
mesh.mesh = qs.mesh()
mesh.mesh.setphysicalregions(*reg.get_region_data())
mesh.skin = reg.get_next_free()
mesh.mesh.selectskin(mesh.skin)
mesh.mesh.partition()
mesh.mesh.load("gmsh:simulation.msh", mesh.skin, 1, 1)

# Electric potential field
fld.v = qs.field("h1", [1])
fld.v.setorder(reg.all, 2)

df.E = qs.parameter(3, 1)

# Electric field
df.E.addvalue(reg.all, -qs.grad(fld.v))

# Constraint interaction
fld.v.setconstraint(reg.gnd, 0.0)

# Constraint interaction: Constraint 2
fld.v.setconstraint(reg.drive, expr.pres)

form = qs.formulation()

# Electrostatics
form += qs.integral(
    reg.all, -(par.epsilon() * qs.grad(qs.dof(fld.v))) * qs.grad(qs.tf(fld.v))
)

form.allsolve(
    relrestol=1e-06, maxnumit=1000, nltol=1e-05, maxnumnlit=1000, relaxvalue=-1
)

# Field output: v
qs.setoutputfield("v", reg.all, fld.v, 2)
