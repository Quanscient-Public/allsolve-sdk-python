import math
import csv
import json
import quanscient as qs
from utils import Mesh, Variables, Empty, Fields
from expressions import expr
from materials import mat
from regions import reg

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
fld.u = qs.field("h1xyz")
fld.u.setorder(reg.all_2, 2)

# Clamp interaction
fld.u.setconstraint(reg.bc_id_0)

rho = qs.parameter(1, 1)
rho.setvalue(reg.all, 2700.0)

H = qs.parameter(6, 6)
H.setvalue(
    reg.all,
    qs.expression(
        6,
        6,
        [
            9.73063973063973e10,
            4.579124579124579e10,
            4.579124579124579e10,
            0.0,
            0.0,
            0.0,
            4.579124579124579e10,
            9.73063973063973e10,
            4.579124579124579e10,
            0.0,
            0.0,
            0.0,
            4.579124579124579e10,
            4.579124579124579e10,
            9.73063973063973e10,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            2.5757575757575756e10,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            2.5757575757575756e10,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            2.5757575757575756e10,
        ],
    ),
)

form = qs.formulation()

# Solid mechanics
form += qs.integral(reg.all_2, qs.predefinedelasticity(qs.dof(fld.u), qs.tf(fld.u), H))
# Inertia terms
form += qs.integral(reg.all_2, rho * qs.dtdt(qs.dof(fld.u)) * qs.tf(fld.u))

eig = qs.eigenvalue(form)

eig.settolerance(1e-06, 1000)
eig.allcomputeeigenfrequencies(1e-06, 1000, 10, 40000.0)
eig.printeigenfrequencies()

var.eigenvalue_real = eig.geteigenvaluerealpart()
var.eigenvalue_imag = eig.geteigenvalueimaginarypart()

var.eigenvector_real = eig.geteigenvectorrealpart()
var.eigenvector_imag = eig.geteigenvectorimaginarypart()

var.eigenfrequencies = eig.geteigenfrequencies()

for i in range(len(var.eigenvector_real)):
    qs.setdata(var.eigenvector_real[i])

    # Eigenfrequencies
    qs.setoutputvalue("Eigenfrequencies", [var.eigenfrequencies[i]], i)

    qs.setdata(var.eigenvector_imag[i])
