import allsolve

L_MIN = 2.1e-3
L_MAX = (10 - 0.43) * 1e-3 / 2 - 0.1e-3
N_STUB_LENGTHS = 6

LX_DIELECTRIC = 8.65e-3
LY_DIELECTRIC = 10e-3
LZ_DIELECTRIC = 0.5e-3

LX_TRACK = 8.65e-3
LY_TRACK = 0.43e-3
LZ_TRACK = 0.01524e-3

LX_AIR = 8.65e-3
LY_AIR = 10e-3
LZ_AIR = 3e-3

LX_STUB = 0.43e-3
LZ_STUB = 0.01524e-3


def build_geometry(project: allsolve.Project) -> None:
    """Build the microstrip stub filter geometry using the SDK geometry builder.

    The filter stub dimensions reference the project variable ``stub_length``
    so they are resolved per sweep step by the server.
    """
    geometry_builder = project.geometry_builder()

    geometry_builder.delete()

    geometry_builder.add_box(
        name="Dielectric",
        position=(0, 0, 0),
        size=(LX_DIELECTRIC, LY_DIELECTRIC, LZ_DIELECTRIC),
    )

    geometry_builder.add_box(
        name="Track",
        position=(0, 0, LZ_DIELECTRIC / 2 + LZ_TRACK / 2),
        size=(LX_TRACK, LY_TRACK, LZ_TRACK),
    )

    geometry_builder.add_box(
        name="Air",
        position=(0, 0, LZ_DIELECTRIC / 2 + LZ_AIR / 2),
        size=(LX_AIR, LY_AIR, LZ_AIR),
    )

    geometry_builder.add_box(
        name="Filter stub",
        position=(
            0,
            f"{LY_TRACK / 2} + stub_length / 2",
            LZ_DIELECTRIC / 2 + LZ_STUB / 2,
        ),
        size=(LX_STUB, "stub_length", LZ_STUB),
    )

    geometry_builder.build(print_logs=True, on_error=allsolve.OnError.RAISE)


def create_and_run_mesh(
    project: allsolve.Project,
    sweep: allsolve.VariableOverrides,
) -> allsolve.Mesh:
    """Create and run the mesh on the server.

    When *sweep* contains overrides that affect geometry (e.g. stub_length),
    the mesh is linked to the variable override so the server creates a mesh
    instance per geometry variant.
    """
    mesh = project.create_mesh(
        allsolve.MeshSettings(
            name="Sweep mesh",
            max_run_time_minutes=60,
        )
    )
    instance = mesh.create_override(variable_override=sweep)
    try:
        instance.run(print_logs=True, on_error=allsolve.OnError.RAISE)
    except Exception as e:
        print(f"Meshing failed: {e}")
        raise
    return mesh
