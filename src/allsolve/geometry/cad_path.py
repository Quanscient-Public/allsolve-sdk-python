# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import List, Tuple, Union


class CadGlob(Enum):
    """
    Wildcard patterns for CAD path matching.
    """

    STAR = "star"
    """Matches a single level in the CAD hierarchy."""

    DOUBLESTAR = "doublestar"
    """Matches zero or more levels in the CAD hierarchy."""


CadPath = List[Union[str, Tuple[str, str], CadGlob]]
"""
A path to select CAD entities in a hierarchical structure.

A CAD path is a list of segments, where each segment can be:
- A string: Name of a geometry element at that level
- A tuple of (key, value): Attribute filter matching entities with the given attribute
- A CadGlob enum: Wildcard pattern for matching multiple entities

CAD paths are used in geometry operations (union, difference, intersection, translate,
rotate, grid, remove, etc.) to select which entities to operate on.
"""
