# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

import inspect
import warnings
from enum import Enum
from functools import wraps


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
