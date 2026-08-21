# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from typing import Sequence, Union

# Type alias for string expressions used in solver parameters.
# An Expression is a string that represents a solver expression (e.g., a variable
# name, a mathematical formula, or a literal value in string form).
# Using a named type documents intent and provides a foundation for future validation.
Expression = str

# Type aliases for parameter values that accept Python-native types
ScalarValue = Union[Expression, float, int]
VectorValue = Union[Expression, Sequence[Union[float, int, Expression]]]
MatrixValue = Union[Expression, Sequence[Sequence[Union[float, int, Expression]]]]
BooleanValue = Union[Expression, bool]


def vector_to_str(value: VectorValue) -> str:
    """
    Convert a vector value to allsolve string format.

    Parameters:
        value: A vector as a string, tuple, or list.
            - If string, returned as-is (assumed to be in correct format).
            - If tuple/list, converted to "[x; y; z]" format.

    Returns:
        The vector in allsolve format "[x; y; z]".

    Examples:
        >>> vector_to_str((0, 0, -1000))
        '[0; 0; -1000]'
        >>> vector_to_str([1.5, 2.0, 3.0])
        '[1.5; 2.0; 3.0]'
        >>> vector_to_str("[0; 0; -1000]")
        '[0; 0; -1000]'
    """
    if isinstance(value, str):
        return value
    return "[" + "; ".join(str(v) for v in value) + "]"


def vector_from_str(value: str) -> VectorValue:
    """
    Parse a vector string back to a list of values.

    Parameters:
        value: A string in allsolve vector format "[x; y; z]".

    Returns:
        A list of floats (or strings if not numeric).

    Examples:
        >>> vector_from_str("[0; 0; -1000]")
        [0.0, 0.0, -1000.0]
        >>> vector_from_str("[1.5; 2.0; 3.0]")
        [1.5, 2.0, 3.0]
        >>> vector_from_str("[x; y; z]")
        ['x', 'y', 'z']
    """
    # Remove brackets and split by semicolon
    inner = value.strip()[1:-1]
    parts = [p.strip() for p in inner.split(";")]
    result: list[float | str] = []
    for part in parts:
        try:
            result.append(float(part))
        except ValueError:
            result.append(part)
    return result


def matrix_to_str(value: MatrixValue) -> str:
    """
    Convert a matrix value to allsolve string format.

    Parameters:
        value: A matrix as a string or nested sequence.
            - If string, returned as-is (assumed to be in correct format).
            - If nested sequence, converted to "[r0c0, r0c1; r1c0, r1c1; ...]" format.
              Rows are separated by semicolons, columns by commas.

    Returns:
        The matrix in allsolve format.

    Examples:
        >>> matrix_to_str([[1, 0], [0, 1], [0, 0]])
        '[1, 0; 0, 1; 0, 0]'
        >>> matrix_to_str("[1, 0; 0, 42; 0, 0]")
        '[1, 0; 0, 42; 0, 0]'
    """
    if isinstance(value, str):
        return value
    rows = [", ".join(str(c) for c in row) for row in value]
    return "[" + "; ".join(rows) + "]"


def matrix_from_str(value: str) -> MatrixValue:
    """
    Parse a matrix string back to a nested list of values.

    Parameters:
        value: A string in allsolve matrix format "[r0c0, r0c1; r1c0, r1c1; ...]".

    Returns:
        A nested list of floats (or strings if not numeric).

    Examples:
        >>> matrix_from_str("[1, 0; 0, 1; 0, 0]")
        [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]
        >>> matrix_from_str("[1.5, 2.0; 3.0, 4.5]")
        [[1.5, 2.0], [3.0, 4.5]]
    """
    # Remove brackets and split by semicolon for rows
    inner = value.strip()[1:-1]
    row_strs = [r.strip() for r in inner.split(";")]
    result: list[list[float | str]] = []
    for row_str in row_strs:
        cols = [c.strip() for c in row_str.split(",")]
        row: list[float | str] = []
        for col in cols:
            try:
                row.append(float(col))
            except ValueError:
                row.append(col)
        result.append(row)
    return result


def boolean_to_str(value: BooleanValue) -> str:
    """
    Convert a boolean value to allsolve string format.

    Parameters:
        value: A boolean value as string or bool.
            - If string, returned as-is.
            - If bool, converted to "1" (True) or "0" (False).

    Returns:
        The boolean as "1" or "0".

    Examples:
        >>> boolean_to_str(True)
        '1'
        >>> boolean_to_str(False)
        '0'
        >>> boolean_to_str("1")
        '1'
    """
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


def enabled_from_expr(expr: str | None) -> BooleanValue | None:
    """
    Parse an enabled expression from the API to a Python bool or expression string.

    Parameters:
        expr: Enabled expression from rawapi ``enabled_expr``.

    Returns:
        True for ``"1"``, False for ``"0"``, the expression string otherwise,
        or None when expr is None.
    """
    if expr is None:
        return None
    if expr == "1":
        return True
    if expr == "0":
        return False
    return expr


def enabled_to_expr(value: BooleanValue | None) -> str:
    """
    Convert a Python enabled value to an API enabled expression string for **create** calls.

    Parameters:
        value: A bool, expression string, or None (defaults to ``"1"``).

    Returns:
        The enabled expression string for rawapi ``enabledExpr``.

    Note:
        This helper is used on the create path only (``Interaction.create``,
        ``OutputInteraction.create``). ``NewInteraction.enabledExpr`` is required to
        carry an explicit value, so ``None`` is mapped to ``"1"`` (enabled by default).
    """
    if value is None:
        return "1"
    return boolean_to_str(value)


def export_enabled_value(enabled: BooleanValue | None) -> BooleanValue | None:
    """
    Return the enabled value to write to export YAML, or None to omit the field.

    Parameters:
        enabled: The interaction or output enabled value.

    Returns:
        None when enabled (omit from YAML), ``False`` or an expression string otherwise.
    """
    if enabled is None or enabled is True:
        return None
    if enabled == False or enabled == "0":
        return False
    if enabled == "1":
        return None
    return enabled


def boolean_from_str(value: str) -> bool:
    """
    Parse a boolean string back to a Python bool.

    Parameters:
        value: A string "1" or "0".

    Returns:
        True if value is "1", False if value is "0".

    Raises:
        ValueError: If value is not "1" or "0".

    Examples:
        >>> boolean_from_str("1")
        True
        >>> boolean_from_str("0")
        False
    """
    if value == "1":
        return True
    if value == "0":
        return False
    raise ValueError(f"Invalid boolean string: {value!r}, expected '1' or '0'")
