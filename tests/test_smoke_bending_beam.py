"""
Smoke test: create a bending beam simulation end-to-end, verify results,
then tear down every resource in reverse creation order.
"""

from types import SimpleNamespace

import allsolve
import pytest


def test_bending_beam_smoke(smoke_project: allsolve.Project) -> None:
    project = smoke_project

    # 1. Variables
    variables = project.create_variables(
        [
            ("length", "24e-3", "Length of the beam"),
            ("width", "2e-3", "Width of the beam"),
            ("height", "3e-3", "Height of the beam"),
            ("tolerance", "1e-4", "Tolerance for regions"),
        ]
    )

    # 2. Geometry
    builder = project.geometry_builder()
    builder.add_box(
        name="beam",
        position=(0, 0, 0),
        size=("length", "width", "height"),
    ).build(on_error=allsolve.OnError.RAISE)

    # 3. Regions
    regions = SimpleNamespace()

    regions.beam_volume = project.create_region_rule(
        name="beam_volume",
        entity_type=allsolve.Region.VOLUME,
        max_size=allsolve.ExpressionVector(
            x="length + tolerance",
            y="width + tolerance",
            z="height + tolerance",
        ),
        min_size=allsolve.ExpressionVector(
            x="length - tolerance",
            y="width - tolerance",
            z="height - tolerance",
        ),
    )

    regions.clamp_surface = project.create_region_rule(
        name="clamp_surface",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=allsolve.ExpressionBoundingBox(
            min=allsolve.ExpressionVector(
                x="(-length / 2) - tolerance",
                y="(-width / 2) - tolerance",
                z="(-height / 2) - tolerance",
            ),
            max=allsolve.ExpressionVector(
                x="(-length / 2) + tolerance",
                y="(width / 2) + tolerance",
                z="(height / 2) + tolerance",
            ),
        ),
    )

    regions.top_surface = project.create_region_rule(
        name="top_surface",
        entity_type=allsolve.Region.SURFACE,
        bounding_box=allsolve.ExpressionBoundingBox(
            min=allsolve.ExpressionVector(
                x="(-length / 2) - tolerance",
                y="(-width / 2) - tolerance",
                z="(height / 2) - tolerance",
            ),
            max=allsolve.ExpressionVector(
                x="(length / 2) + tolerance",
                y="(width / 2) + tolerance",
                z="(height / 2) + tolerance",
            ),
        ),
    )

    regions.top_surface_clamp_corner = project.create_region_rule(
        name="top_surface_clamp_corner",
        entity_type=allsolve.Region.POINT,
        bounding_box=(
            (
                "(-length / 2) - tolerance",
                "(width / 2) - tolerance",
                "(height / 2) - tolerance",
            ),
            (
                "(-length / 2) + tolerance",
                "(width / 2) + tolerance",
                "(height / 2) + tolerance",
            ),
        ),
    )

    regions.top_surface_free_corner = project.create_region_rule(
        name="top_surface_free_corner",
        entity_type=allsolve.Region.POINT,
        bounding_box=(
            (
                "(length / 2) - tolerance",
                "(width / 2) - tolerance",
                "(height / 2) - tolerance",
            ),
            (
                "(length / 2) + tolerance",
                "(width / 2) + tolerance",
                "(height / 2) + tolerance",
            ),
        ),
    )

    # 4. Material
    material = project.create_material(
        name="Aluminium",
        description="Aluminium",
        color="#aaaaaa",
        abbreviation="Al",
        target_region=regions.beam_volume,
        coefficient_of_thermal_expansion=1e-06,
        density=2700,
        elasticity_matrix=allsolve.MaterialProperty.ElasticityMatrixYoungsModulusPoissonsRatio(
            "68000000000.0",
            "0.32",
        ),
        electric_conductivity=36900000.0,
        electric_permittivity="epsilon0",
        heat_capacity=897,
        magnetic_permeability="mu0",
        speed_of_sound=6320,
        thermal_conductivity=237,
    )

    # 5. Physics & interactions
    solid_mechanics_physics = project.add_physics(allsolve.Physics.SolidMechanics())
    solid_mechanics_physics.add_interactions(
        [
            allsolve.Interaction.SolidMechanicsClamp(
                name="Clamp",
                target=regions.clamp_surface,
            ),
            allsolve.Interaction.SolidMechanicsLoad(
                name="Load",
                target=regions.top_surface,
                force=(0, 0, -1000),
            ),
        ]
    )

    # 6. Mesh
    mesh = project.create_mesh()
    mesh.run()
    assert (
        mesh.get_status() == allsolve.Job.SUCCESS
    ), f"Mesh failed: {mesh.get_status()}"

    # 7. Simulation
    sim = project.create_simulation_static(
        name="Simulation",
        description="Bending beam smoke test simulation",
        max_run_time_minutes=10,
        solver_mode=allsolve.SolverMode.DIRECT,
        mesh=mesh,
    )
    sim.add_outputs(
        [
            # Output the z-deflection at the top surface clamp corner and the top surface free corner
            allsolve.Output.ValueOutput(
                name="z_deflection",
                expression="lineinterpolate(reg.beam_volume, compz(u), getcoords(reg.top_surface_clamp_corner), getcoords(reg.top_surface_free_corner), 2)",
            ),
        ]
    )

    sim.start()
    while sim.is_running(refresh_delay_s=1):
        pass

    assert (
        sim.get_status() == allsolve.Job.SUCCESS
    ), f"Simulation failed: {sim.get_status()}"

    # 8. Verify results
    output_data = sim.get_output_data()

    # 8a. Read via CSV (contains header and data rows for all sweep steps)
    csv = output_data.to_csv()
    lines = csv.strip().splitlines()
    assert len(lines) == 3, "Output CSV should contain a header and 2 data rows"
    header = lines[0].split(",")
    assert "z_deflection" in header, "Missing z_deflection column"
    z_col = header.index("z_deflection")
    csv_clamp_deflection = float(lines[1].split(",")[z_col])
    csv_free_deflection = float(lines[2].split(",")[z_col])

    # 8b. Read via dict (contains data for a single sweep step)
    output_dict = output_data.to_dict(sweep_index=0)
    dict_clamp_deflection = output_dict["nostep"]["z_deflection"][0]
    dict_free_deflection = output_dict["nostep"]["z_deflection"][1]

    # 8c. Read via get_value_at (slowest method)
    gva_clamp_deflection = output_data.get_value_at(
        sweep_index=0,
        step_index=0,
        value_header="z_deflection",
        array_index=0,
    )
    gva_free_deflection = output_data.get_value_at(
        sweep_index=0,
        step_index=0,
        value_header="z_deflection",
        array_index=1,
    )
    assert gva_clamp_deflection is not None
    assert gva_free_deflection is not None

    # 8d. All three accessors must agree
    assert csv_clamp_deflection == pytest.approx(dict_clamp_deflection)
    assert csv_clamp_deflection == pytest.approx(gva_clamp_deflection)
    assert csv_free_deflection == pytest.approx(dict_free_deflection)
    assert csv_free_deflection == pytest.approx(gva_free_deflection)

    # 8e. Read via DataFrame (skipped if pandas is not installed)
    try:
        df = output_data.to_dataframe()
        assert "z_deflection" in df.columns, "Missing z_deflection column in DataFrame"
        z_values = df["z_deflection"].tolist()
        assert len(z_values) == 2, f"Expected 2 rows in DataFrame, got {len(z_values)}"
        df_clamp_deflection = z_values[0]
        df_free_deflection = z_values[1]
        assert csv_clamp_deflection == pytest.approx(df_clamp_deflection)
        assert csv_free_deflection == pytest.approx(df_free_deflection)
    except (ImportError, AttributeError):
        print("SKIPPED: DataFrame assertions (pandas not installed)")

    # 8f. Physics sanity checks
    assert (
        abs(csv_clamp_deflection) < 1e-10
    ), f"Clamped corner should have near-zero deflection, got {csv_clamp_deflection}"
    assert (
        csv_free_deflection < 0
    ), f"Free end should deflect downward (negative z), got {csv_free_deflection}"
    assert abs(csv_free_deflection) == pytest.approx(
        2.72e-07, rel=0.1
    ), f"Free-end deflection outside expected range, got {csv_free_deflection}"

    # 9. Teardown in reverse creation order
    output_data.clean_cache()
    sim.delete()
    mesh.delete()
    solid_mechanics_physics.delete()
    material.delete()
    for region in reversed(list(vars(regions).values())):
        region.delete()
    builder.delete()
    for var in reversed(variables):
        var.delete()
