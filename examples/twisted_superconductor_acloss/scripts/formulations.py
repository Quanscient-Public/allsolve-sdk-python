form = qs.formulation()

# Lump I/V cut interaction: Current source
form += port.lump.I - expr.Top

# Default to V = 0 for the rest
for i in range(3, len(var.cps), 2):
    form += var.cps[i] - 0

# Magnetism H
rho = 1 / par.sigma(df.j)
dedj = rho * qs.eye(3) + (expr.YBCO_n - 1.0) * rho / qs.max(
    df.j * df.j, 1e-40
) * df.j * qs.transpose(df.j)
dofe = rho * df.j + dedj * (
    qs.curl(qs.dof(fld.H)) + var.curl_dof_Hs - qs.curl(fld.H) - var.curl_Hs
)
form += qs.integral(reg.sc, dofe * (qs.curl(qs.tf(fld.H)) - var.curl_tf_Hs))
form += qs.integral(
    reg.copper,
    qs.inverse(par.sigma(df.j))
    * (qs.curl(qs.dof(fld.H)) + var.curl_dof_Hs)
    * (qs.curl(qs.tf(fld.H)) - var.curl_tf_Hs),
)
form += qs.integral(
    reg.magnetism_h, par.mu() * (qs.dt(qs.dof(fld.H)) + var.dt_dof_Hs) * qs.tf(fld.H)
)

# H-φ coupling interaction
var.phi_dofs_reg = reg.magnetism_phi
form += qs.integral(
    reg.magnetism_h,
    -par.mu() * qs.grad(qs.dt(qs.dof(fld.phi, var.phi_dofs_reg))) * qs.tf(fld.H),
)
form += qs.integral(
    reg.magnetism_h,
    -par.mu()
    * (
        qs.dt(qs.dof(fld.H))
        + var.dt_dof_Hs
        - qs.grad(qs.dt(qs.dof(fld.phi, var.phi_dofs_reg)))
    )
    * var.tf_Hs,
)
form += qs.integral(
    reg.magnetism_phi,
    -par.mu() * (var.dt_dof_Hs - qs.dt(qs.grad(qs.dof(fld.phi)))) * var.tf_Hs,
)
form += qs.integral(
    reg.magnetism_h,
    par.mu()
    * (qs.dof(fld.H) - qs.grad(qs.dof(fld.phi, var.phi_dofs_reg)) + var.dof_Hs)
    * qs.grad(qs.tf(fld.phi, var.phi_dofs_reg)),
)

# Magnetism φ
form += qs.integral(
    reg.magnetism_phi,
    -par.mu() * (qs.grad(qs.dof(fld.phi)) - var.dof_Hs) * qs.grad(qs.tf(fld.phi)),
)
