# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from enum import Enum


class CadGeometryType(Enum):
    """
    Type of a CAD geometry element.

    Members fall into three categories:

    **Imported file formats** — geometry loaded from an external file
    (STEP, IGES, SAT, BREP, GDS2, MSH, NAS).

    **Primitives** — built-in parametric shapes
    (BOX, CYLINDER, SPHERE, CONE, TORUS, SURFACE_RECTANGLE, DISK, RECTANGLE).

    **Operations** — transformations and Boolean operations applied to
    existing geometry (TRANSLATE, ROTATE, GRID, REMOVE, UNION, DIFFERENCE,
    INTERSECTION, FRAGMENTS, FRAGMENT_ALL).
    """

    STEP_FILE = "step_file"
    IGES_FILE = "iges_file"
    SAT_FILE = "sat_file"
    BREP_FILE = "brep_file"
    GDS2_FILE = "gds2_file"
    MSH_FILE = "msh_file"
    NAS_FILE = "nas_file"
    BOX = "box"
    CYLINDER = "cylinder"
    SPHERE = "sphere"
    CONE = "cone"
    TORUS = "torus"
    SURFACE_RECTANGLE = "surface_rectangle"
    DISK = "disk"
    RECTANGLE = "rectangle"
    TRANSLATE = "translate"
    ROTATE = "rotate"
    GRID = "grid"
    REMOVE = "remove"
    UNION = "union"
    DIFFERENCE = "difference"
    INTERSECTION = "intersection"
    FRAGMENTS = "fragments"
    FRAGMENT_ALL = "fragmentall"
