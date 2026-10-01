# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

import inspect
import json
import os
import warnings
from collections.abc import Callable
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Concatenate, ParamSpec, TypeVar, cast, overload

import allsolve_rawapi as rawapi

P = ParamSpec("P")
R = TypeVar("R")


@overload
def deprecated(reason: Callable[P, R]) -> Callable[P, R]: ...


@overload
def deprecated(reason: str) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def deprecated(
    reason: str | Callable[P, R],
) -> Callable[[Callable[P, R]], Callable[P, R]] | Callable[P, R]:
    """
    Mark functions or methods as deprecated; emits DeprecationWarning on call.
    Use as ``@deprecated("message")`` or bare ``@deprecated``.
    """

    string_types = (str, type(b""))

    if isinstance(reason, string_types):

        def decorator(func1: Callable[P, R]) -> Callable[P, R]:
            if inspect.isclass(func1):
                fmt1 = "Call to deprecated class {name} ({reason})."
            else:
                fmt1 = "Call to deprecated function {name} ({reason})."

            @wraps(cast(Any, func1))
            def new_func1(*args: P.args, **kwargs: P.kwargs) -> R:
                warnings.simplefilter("always", DeprecationWarning)
                warnings.warn(
                    fmt1.format(name=func1.__name__, reason=reason),
                    category=DeprecationWarning,
                    stacklevel=2,
                )
                warnings.simplefilter("default", DeprecationWarning)
                return func1(*args, **kwargs)

            return new_func1

        return decorator

    elif inspect.isclass(reason) or inspect.isfunction(reason):
        func2 = cast(Callable[P, R], reason)

        if inspect.isclass(func2):
            fmt2 = "Call to deprecated class {name}."
        else:
            fmt2 = "Call to deprecated function {name}."

        @wraps(func2)
        def new_func2(*args: P.args, **kwargs: P.kwargs) -> R:
            warnings.simplefilter("always", DeprecationWarning)
            warnings.warn(
                fmt2.format(name=func2.__name__),
                category=DeprecationWarning,
                stacklevel=2,
            )
            warnings.simplefilter("default", DeprecationWarning)
            return func2(*args, **kwargs)

        return new_func2

    else:
        raise TypeError(repr(type(reason)))


class FileOverwriteMode(Enum):
    """Controls behavior when a downloaded file already exists on disk."""

    OVERWRITE = "overwrite"
    SKIP = "skip"
    ERROR = "error"


def reject_unsafe_path_component(name: str, *, context: str = "path component") -> None:
    """
    Reject strings that must not be used as a single filesystem path component.

    Raises:
        ValueError: If *name* is empty, contains a NUL byte or path separator,
            is ``.`` / ``..``, is a UNC or drive-qualified path, or contains
            ``:`` on Windows.
    """
    if not name:
        raise ValueError(f"Empty {context} is not allowed.")
    if "\0" in name:
        raise ValueError(f"NUL byte in {context} {name!r} is not allowed.")
    if name in (".", ".."):
        raise ValueError(f"{context.capitalize()} {name!r} is not allowed.")
    if name.startswith(("\\\\", "//")):
        raise ValueError(f"UNC {context} {name!r} is not allowed.")
    if len(name) >= 2 and name[1] == ":" and name[0].isalpha():
        raise ValueError(f"Drive-qualified {context} {name!r} is not allowed.")
    if "/" in name or "\\" in name:
        raise ValueError(
            f"{context.capitalize()} {name!r} must not contain path separators."
        )
    if os.name == "nt" and ":" in name:
        raise ValueError(
            f"{context.capitalize()} {name!r} must not contain ':' on Windows."
        )


def resolve_path_under_base(base: Path, relative: str) -> Path:
    """
    Resolve *relative* under *base* and reject paths that escape the base.

    Raises:
        ValueError: If *relative* is absolute or resolves outside *base*.
    """
    base_resolved = base.resolve()
    relative_path = Path(relative)
    if relative_path.is_absolute() or relative_path.drive:
        raise ValueError(f"Path {relative!r} must be relative to the export directory.")
    resolved = (base_resolved / relative_path).resolve()
    if not resolved.is_relative_to(base_resolved):
        raise ValueError(
            f"Path {relative!r} resolves outside {base_resolved}. "
            "This may indicate a path traversal attempt."
        )
    return resolved


class JobError(Exception):
    """
    Raised when a job completes with an unacceptable status.

    Attributes:
        status: The job status that triggered the error.
        status_reason: Optional reason provided by the backend for the status.
    """

    def __init__(
        self,
        message: str,
        status: str | None,
        status_reason: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.status_reason = status_reason


class NotInitializedError(Exception):
    """
    Exception for when a class or data is not initialized.
    """

    pass


class DeletedError(Exception):
    """
    Exception for when an object is deleted.
    """

    pass


class NotProjectAPIKeyError(Exception):
    """
    Exception for when a project API key is not set.
    """

    pass


def parse_api_error(exc: rawapi.ApiException) -> tuple[str | None, str]:
    """Extract ``error`` code and ``message`` from an API exception body."""
    message = exc.reason or "API error"
    error_code: str | None = None
    if exc.body:
        try:
            payload = json.loads(exc.body)
            if isinstance(payload, dict):
                if payload.get("error") is not None:
                    error_code = str(payload["error"])
                if payload.get("message") is not None:
                    message = str(payload["message"])
        except (json.JSONDecodeError, TypeError):
            pass
    return error_code, message


class ResourceReservationError(Exception):
    """
    Raised when a resource reservation operation fails.

    Attributes:
        error_code: Optional API error code (e.g. ``quota_exceeded``).
    """

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code


def prevent_deleted(
    func: Callable[Concatenate[Any, P], R],
) -> Callable[Concatenate[Any, P], R]:
    """
    Decorator to prevent access to methods/properties of deleted objects.
    Raises DeletedError if the object's _deleted attribute is True.
    """

    @wraps(func)
    def deny(self: Any, *args: P.args, **kwargs: P.kwargs) -> R:
        if self._deleted:
            raise DeletedError()

        return func(self, *args, **kwargs)

    return deny
