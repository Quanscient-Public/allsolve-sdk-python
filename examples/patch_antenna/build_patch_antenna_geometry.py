"""
Builds the antenna from the Allsolve RF 003 example case with build123d.

Run::

    python build_patch_antenna_geometry.py

This writes ``patch_antenna.step``.

**Units:** build123d works in millimeters. Parameters below are defined in
meters to match ``patch_antenna_demo.py`` and converted to mm when building.

Geometry components:
- substrate: Dielectric slab, top face at z=0
- feed_50ohm: 50 ohm microstrip feed line on top of the substrate
- qw_line: Quarter-wavelength impedance transformer
- patch: Radiating patch element
- port_surface: Named lumped-port face on the -X edge of the substrate
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from build123d import (
    Box,
    Compound,
    Face,
    Location,
    Shape,
    Vector,
    Wire,
    export_step,
)


@dataclass(frozen=True)
class PatchAntennaGeometryParams:
    """Antenna geometry dimensions in meters."""

    substrate_length_m: float
    substrate_height_m: float
    feed_length_m: float
    feed_width_m: float
    track_height_m: float
    qw_length_m: float
    qw_width_m: float
    patch_length_m: float
    patch_width_m: float


def _mm(length_m: float) -> float:
    """Convert a length in meters to build123d millimeters."""
    return length_m * 1000.0


def build_substrate(params: PatchAntennaGeometryParams) -> Shape:
    """Dielectric substrate slab centered at origin with top face at z=0."""
    return Box(
        _mm(params.substrate_length_m),
        _mm(params.substrate_length_m),
        _mm(params.substrate_height_m),
    ).move(Location((0, 0, -_mm(params.substrate_height_m) / 2)))


def build_feed_50ohm(params: PatchAntennaGeometryParams) -> Shape:
    """50-ohm microstrip feed line sitting on top of the substrate."""
    cx = -_mm(params.substrate_length_m) / 2 + _mm(params.feed_length_m) / 2
    return Box(
        _mm(params.feed_length_m),
        _mm(params.feed_width_m),
        _mm(params.track_height_m),
    ).move(Location((cx, 0, _mm(params.track_height_m) / 2)))


def build_qw_line(params: PatchAntennaGeometryParams) -> Shape:
    """Quarter-wavelength impedance transformer connecting feed to patch."""
    cx = (
        -_mm(params.substrate_length_m) / 2
        + _mm(params.feed_length_m)
        + _mm(params.qw_length_m) / 2
    )
    return Box(
        _mm(params.qw_length_m),
        _mm(params.qw_width_m),
        _mm(params.track_height_m),
    ).move(Location((cx, 0, _mm(params.track_height_m) / 2)))


def build_patch(params: PatchAntennaGeometryParams) -> Shape:
    """Radiating patch element on top of the substrate."""
    cx = (
        -_mm(params.substrate_length_m) / 2
        + _mm(params.feed_length_m)
        + _mm(params.qw_length_m)
        + _mm(params.patch_length_m) / 2
    )
    return Box(
        _mm(params.patch_length_m),
        _mm(params.patch_width_m),
        _mm(params.track_height_m),
    ).move(Location((cx, 0, _mm(params.track_height_m) / 2)))


def build_port_surface(params: PatchAntennaGeometryParams) -> Face:
    """Named lumped port surface on the -X face of the substrate.

    Matches ``geometry_builder.add_surface_rectangle(name="port_surface", ...)``
    in patch_antenna_demo.py: spans substrate height (hs) and feed width (W50)
    at x = -Ls/2.
    """
    x = -_mm(params.substrate_length_m) / 2
    corners = [
        Vector(x, -_mm(params.feed_width_m) / 2, -_mm(params.substrate_height_m)),
        Vector(x, _mm(params.feed_width_m) / 2, -_mm(params.substrate_height_m)),
        Vector(x, _mm(params.feed_width_m) / 2, 0),
        Vector(x, -_mm(params.feed_width_m) / 2, 0),
    ]
    return Face(Wire.make_polygon(corners, close=True))


def build_assembly(params: PatchAntennaGeometryParams) -> Compound:
    """Build the full patch antenna assembly with labeled volumes and surfaces."""
    parts: list[tuple[str, Shape | Face]] = [
        ("substrate", build_substrate(params)),
        ("feed_50ohm", build_feed_50ohm(params)),
        ("qw_line", build_qw_line(params)),
        ("patch", build_patch(params)),
        ("port_surface", build_port_surface(params)),
    ]
    labeled: list[Shape | Face] = []
    for label, part in parts:
        part.label = label
        labeled.append(part)
    return Compound(children=labeled)


def build_patch_antenna_step(
    params: PatchAntennaGeometryParams,
    output_path: Path | str,
) -> None:
    """Build the patch antenna assembly and export it as a STEP file."""
    export_step(build_assembly(params), Path(output_path))


def main() -> None:
    """Build and export the patch antenna STEP file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "patch_antenna.step",
        help="Output STEP path",
    )
    args = parser.parse_args()

    params = PatchAntennaGeometryParams(
        substrate_length_m=95.12e-3,
        substrate_height_m=1.57e-3,
        feed_length_m=15e-3,
        feed_width_m=4.84e-3,
        track_height_m=1e-4,
        qw_length_m=24.05e-3,
        qw_width_m=0.72e-3,
        patch_length_m=41.08e-3,
        patch_width_m=41.08e-3,
    )
    build_patch_antenna_step(params, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
