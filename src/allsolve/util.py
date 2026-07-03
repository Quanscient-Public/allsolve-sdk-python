# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

import inspect
import json
import warnings
from enum import Enum
from functools import wraps

import allsolve_rawapi as rawapi


def deprecated(reason):
    """
    Mark functions or methods as deprecated; emits DeprecationWarning on call.
    Use as ``@deprecated("message")`` or bare ``@deprecated``.
    """

    string_types = (str, type(b""))

    if isinstance(reason, string_types):

        def decorator(func1):
            if inspect.isclass(func1):
                fmt1 = "Call to deprecated class {name} ({reason})."
            else:
                fmt1 = "Call to deprecated function {name} ({reason})."

            @wraps(func1)
            def new_func1(*args, **kwargs):
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
        func2 = reason

        if inspect.isclass(func2):
            fmt2 = "Call to deprecated class {name}."
        else:
            fmt2 = "Call to deprecated function {name}."

        @wraps(func2)
        def new_func2(*args, **kwargs):
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


def prevent_deleted(f):
    """
    Decorator to prevent access to methods/properties of deleted objects.
    Raises DeletedError if the object's _deleted attribute is True.
    """

    @wraps(f)
    def deny(self, *args, **kwargs):
        if self._deleted:
            raise DeletedError()

        return f(self, *args, **kwargs)

    return deny
