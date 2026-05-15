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

with open("params.json") as f:
    inputs = json.load(f)

# Material properties
rho = 2700.0
E = inputs["E"]*1e10
G = inputs["G"]*1e10
nu = 0.32

# Compliance matrix 
Dc = qs.expression(6, 6, [1.0/E, -nu/E, -nu/E, 0.0, 0.0, 0.0, -nu/E, 1.0/E, -nu/E, 0.0, 0.0, 0.0, -nu/E, -nu/E, 1.0/E, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0/G, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0/G, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0/G])
# Elasticity matrix
H = qs.inverse(Dc)

# Load the mesh
mesh.mesh = qs.mesh()
mesh.mesh.setphysicalregions(*reg.get_region_data())
mesh.skin = reg.get_next_free()
mesh.mesh.selectskin(mesh.skin)
mesh.mesh.partition()
mesh.mesh.load("gmsh:simulation.msh", mesh.skin, 1, 1)

# Displacement field
fld.u = qs.field("h1xyz")
fld.u.setorder(reg.all, 2)

# Clamp interaction
fld.u.setconstraint(reg.clamp_target)

form = qs.formulation()

# Solid mechanics
form += qs.integral(reg.all, qs.predefinedelasticity(qs.dof(fld.u), qs.tf(fld.u), H))
# Inertia terms
form += qs.integral(reg.all, -rho * qs.dtdt(qs.dof(fld.u)) * qs.tf(fld.u))

eig = qs.eigenvalue(form)

eig.settolerance(1e-06, 1000)
eig.allcomputeeigenfrequencies(1e-06, 1000, 10, 1.0)
eig.printeigenfrequencies()

var.eigenvalue_real = eig.geteigenvaluerealpart()
var.eigenvalue_imag = eig.geteigenvalueimaginarypart()

var.eigenvector_real = eig.geteigenvectorrealpart()
var.eigenvector_imag = eig.geteigenvectorimaginarypart()

var.eigenfrequencies = eig.geteigenfrequencies()

qs.setoutputvalue("Eigenfrequencies", var.eigenfrequencies)