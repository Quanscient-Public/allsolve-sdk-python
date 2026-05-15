import quanscient as qs
import json

air = 1
disk = 2
box = 3
pml = 4
skin = 5

mesh = qs.mesh("gmsh:cube.msh", skin, 1, qs.getrank() == 0)

all = qs.selectall()
inner = qs.selectunion([air, disk, box])

with open("material_params.json") as f:
    materials = json.load(f)

freq = 1000
c = qs.parameter()
c.setvalue(all, materials["speedofsound"]["air"])
c.setvalue(box, materials["speedofsound"]["steel"])
k = 2 * qs.getpi() * freq / c
rho = qs.parameter()
rho.setvalue(all, materials["density"]["air"])
rho.setvalue(box, materials["density"]["steel"])

Dterms = qs.predefinedboxpml(pml, inner, k)

qs.setfundamentalfrequency(freq)

p = qs.field("h1", [2, 3])

p.setorder(all, 2)
p.setconstraint(disk, [1, 0])

acoustics = qs.formulation()

acoustics += qs.integral(
    all, qs.predefinedacousticwave(qs.dof(p), qs.tf(p), c, rho, 0, Dterms, "oo2")
)

clk = qs.wallclock()

acoustics.allsolve(
    relrestol=1e-06, maxnumit=1000, nltol=1e-05, maxnumnlit=-1, relaxvalue=-1
)

clk.print("Whole solution took:")

qs.setoutputfield("p harmonic 2", all, p.harmonic(2), 2)
qs.setoutputvalue(
    "energy",
    qs.allintegrate(
        all,
        (1 / (2 * c * c * rho)) * qs.transpose(p.harmonic(2)) * p.harmonic(2),
        5,
    ),
)

# To save a mesh file, use
# qs.setoutputmesh("cube", [all], -1, mesh)

# To save some file you have written (txt, csv, ..) use
with open("Test_file.txt", "wb") as f:
    f.write(b"testing just testing")
