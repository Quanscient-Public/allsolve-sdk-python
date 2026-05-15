# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

"""Shared constants for output YAML aliases used by import, export, and codegen."""

# Friendly YAML type name → raw output type ID.
OUTPUT_TYPE_ALIASES: dict[str, str] = {
    "field": "fieldOutput",
    "value": "discreteOutput",
}

# Friendly YAML param key → raw parameter ID pattern.
# "{otype}" is replaced with the resolved output type at runtime.
OUTPUT_PARAM_ALIASES: dict[str, str] = {
    "skinOnly": "{otype}SkinOnly",
    "deformedMesh": "{otype}DeformedMesh",
    "expression": "{otype}",
}

# Reverse of OUTPUT_PARAM_ALIASES: raw suffix → friendly key.
OUTPUT_PARAM_REVERSE: dict[str, str] = {
    "SkinOnly": "skinOnly",
    "DeformedMesh": "deformedMesh",
}

# Friendly keys whose values should be treated as booleans.
OUTPUT_BOOL_ALIASES: set[str] = {"skinOnly", "deformedMesh"}
