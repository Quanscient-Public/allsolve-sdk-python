import csv
import json
import quanscient as qs
from utils import Mesh, Variables, Consts, Empty, Fields, DerivedFields
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
mesh.e_harmonic_2_target_skin = reg.get_next_free()
mesh.mesh.selectskin(mesh.skin)
mesh.mesh.selectskin(mesh.e_harmonic_2_target_skin, reg.e_harmonic_2_target)
mesh.mesh.partition()
mesh.mesh.load("gmsh:microstrip.msh", mesh.skin, 1, 1)

# Fundamental frequency
var.f = expr.freq

qs.setfundamentalfrequency(var.f)

# Electric field
fld.E = qs.field("hcurl", [2, 3])
fld.E.setorder(reg.all, 2)

df.E = qs.parameter(3, 1)

# Electric field
df.E.addvalue(reg.all, fld.E)

# Perfect conductor interaction: Track PEC
fld.E.setconstraint(reg.track_pec_target)

# Perfect conductor interaction: Ground PEC
fld.E.setconstraint(reg.ground_pec_target)

form = qs.formulation()

# Prepare for the EM wave port mode projection
var.mode_project = form.lump([reg.in_target, reg.out_target], [2, 3])

# Electromagnetic waves
form += qs.integral(
    reg.all,
    3,
    qs.predefinedemwave(
        qs.dof(fld.E), qs.tf(fld.E), par.mu(), 0, par.epsilon(), 0, 0, 0, "oo2"
    ),
)

var.E_sources = []
var.E_port_regs = []

# Eigenmode port interaction: In
var.E_port, var.H_port, _ = qs.alleigenport(
    reg.in_target,
    5,
    5.0 * 2.0 * qs.getpi() * var.f / qs.getc0(),
    fld.E,
    par.mu(),
    par.epsilon(),
    [-1.0, 0.0, 0.0],
    1e-06,
    1000,
)[0]
qs.setoutputfield("In", reg.in_target, var.E_port, 2)
var.normal = qs.array3x1(-1.0, 0.0, 0.0)
form += qs.integral(
    reg.in_target,
    3,
    2.0
    * qs.crossproduct(
        var.normal,
        qs.dt(qs.sin(2.0 * qs.getpi() * expr.freq * qs.t()), 0, 0) * var.H_port,
    )
    * qs.tf(fld.E),
    0,
    1,
)
form += qs.integral(
    reg.in_target,
    3,
    qs.crossproduct(qs.dof(fld.E), var.H_port)
    * var.normal
    / 2
    * qs.tf(var.mode_project[0]),
)
form += qs.integral(
    reg.in_target,
    3,
    qs.crossproduct(var.normal, -qs.dt(qs.dof(var.mode_project[0])) * var.H_port)
    * qs.tf(fld.E),
)
var.E_sources.append(qs.sin(2.0 * qs.getpi() * expr.freq * qs.t()) * var.E_port)
var.E_port_regs.append(reg.in_target)

# Eigenmode port interaction: Out
var.E_port, var.H_port, _ = qs.alleigenport(
    reg.out_target,
    5,
    5.0 * 2.0 * qs.getpi() * var.f / qs.getc0(),
    fld.E,
    par.mu(),
    par.epsilon(),
    [-1.0, 0.0, 0.0],
    1e-06,
    1000,
)[0]
qs.setoutputfield("Out", reg.out_target, var.E_port, 2)
var.normal = qs.array3x1(-1.0, 0.0, 0.0)
form += qs.integral(
    reg.out_target,
    3,
    2.0
    * qs.crossproduct(
        var.normal,
        qs.dt(qs.sin(2.0 * qs.getpi() * expr.freq * qs.t()), 0, 0) * var.H_port,
    )
    * qs.tf(fld.E),
    0,
    2,
)
form += qs.integral(
    reg.out_target,
    3,
    qs.crossproduct(qs.dof(fld.E), var.H_port)
    * var.normal
    / 2
    * qs.tf(var.mode_project[1]),
)
form += qs.integral(
    reg.out_target,
    3,
    qs.crossproduct(var.normal, -qs.dt(qs.dof(var.mode_project[1])) * var.H_port)
    * qs.tf(fld.E),
)
var.E_sources.append(qs.sin(2.0 * qs.getpi() * expr.freq * qs.t()) * var.E_port)
var.E_port_regs.append(reg.out_target)

var.solutions = form.allsolve(
    relrestol=1e-06,
    maxnumit=1000,
    nltol=1e-05,
    maxnumnlit=-1,
    relaxvalue=-1,
    rhsblocks=[[0, 1], [0, 2], [0, 1, 2]],
)

# S-parameters
var.s_parameters = qs.allcomputesparameters(
    var.E_port_regs, fld.E, var.E_sources, var.solutions
)
qs.setoutputvalue(
    "S-parameters",
    qs.bode(var.s_parameters[0], var.s_parameters[1])[0],
    None,
    "magnitude",
)
qs.setoutputvalue(
    "S-parameters", qs.bode(var.s_parameters[0], var.s_parameters[1])[1], None, "angle"
)
qs.printsparameters(var.s_parameters)

# Field output: E harmonic 2
qs.setoutputfield(
    "E harmonic 2",
    mesh.e_harmonic_2_target_skin,
    qs.on(reg.e_harmonic_2_target, qs.harm(2, df.E, 3)),
    2,
)
