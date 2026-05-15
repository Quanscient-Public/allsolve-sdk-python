import csv
import json
import quanscient as qs
from utils import Mesh, Variables, Empty, Fields, DerivedFields
from expressions import expr
from materials import mat
from regions import reg
from parameters import par

var = Variables()
mesh = Mesh()
fld = Fields()
df = DerivedFields()

# Load the mesh
mesh.mesh = qs.mesh()
mesh.mesh.setphysicalregions(*reg.get_region_data())
mesh.skin = reg.get_next_free()
mesh.magnetic_force_left_target_skin = reg.get_next_free()
mesh.magnetic_force_right_target_skin = reg.get_next_free()
mesh.mesh.selectskin(mesh.skin)
mesh.mesh.selectskin(
    mesh.magnetic_force_left_target_skin, reg.magnetic_force_left_target
)
mesh.mesh.selectskin(
    mesh.magnetic_force_right_target_skin, reg.magnetic_force_right_target
)
mesh.mesh.partition()
mesh.mesh.load("gmsh:simulation.msh", mesh.skin, 1, 1)

# Magnetic scalar potential field
fld.phi = qs.field("h1", [1])
fld.phi.setorder(reg.all, 2)

df.H = qs.parameter(3, 1)
df.B = qs.parameter(3, 1)

# Magnetic field
df.H.addvalue(reg.magnetism_phi, -qs.grad(fld.phi))

# Magnetic flux density
df.B.addvalue(reg.magnetism_phi, -par.mu() * qs.grad(fld.phi))
df.B.addvalue(reg.remanence_right_target, qs.array3x1(0.0, -1.35, 0.0))
df.B.addvalue(reg.remanence_left_target, qs.array3x1(0.0, 1.35, 0.0))

form = qs.formulation()

# Magnetism φ
form += qs.integral(
    reg.magnetism_phi, -par.mu() * qs.grad(qs.dof(fld.phi)) * qs.grad(qs.tf(fld.phi))
)

# Remanence interaction: Remanence left
form += qs.integral(
    reg.remanence_left_target, qs.array3x1(0.0, 1.35, 0.0) * qs.grad(qs.tf(fld.phi))
)

# Remanence interaction: Remanence right
form += qs.integral(
    reg.remanence_right_target, qs.array3x1(0.0, -1.35, 0.0) * qs.grad(qs.tf(fld.phi))
)

form.allsolve(relrestol=1e-06, maxnumit=1000, nltol=1e-05, maxnumnlit=-1, relaxvalue=-1)

# Field output: B air
qs.setoutputfield("B air", reg.b_air_target, df.B, 2)

# Field output: B magnets
qs.setoutputfield("B magnets", reg.b_magnets_target, df.B, 2)

# Magnetic force: Magnetic force left
var.T = qs.inverse(par.mu()) * (
    df.B * qs.transpose(df.B) - 0.5 * df.B * df.B * qs.eye(3)
)
var.force_density = qs.on(reg.magnetic_force_left_target, var.T) * qs.normal(
    reg.magnetic_force_left_target
)
var.force_x = qs.compx(var.force_density).allintegrate(
    mesh.magnetic_force_left_target_skin, 2
)
var.force_y = qs.compy(var.force_density).allintegrate(
    mesh.magnetic_force_left_target_skin, 2
)
var.force_z = qs.compz(var.force_density).allintegrate(
    mesh.magnetic_force_left_target_skin, 2
)
qs.setoutputvalue("Magnetic force left", [var.force_x, var.force_y, var.force_z])

# Magnetic force: Magnetic force right
var.T = qs.inverse(par.mu()) * (
    df.B * qs.transpose(df.B) - 0.5 * df.B * df.B * qs.eye(3)
)
var.force_density = qs.on(reg.magnetic_force_right_target, var.T) * qs.normal(
    reg.magnetic_force_right_target
)
var.force_x = qs.compx(var.force_density).allintegrate(
    mesh.magnetic_force_right_target_skin, 2
)
var.force_y = qs.compy(var.force_density).allintegrate(
    mesh.magnetic_force_right_target_skin, 2
)
var.force_z = qs.compz(var.force_density).allintegrate(
    mesh.magnetic_force_right_target_skin, 2
)
qs.setoutputvalue("Magnetic force right", [var.force_x, var.force_y, var.force_z])
