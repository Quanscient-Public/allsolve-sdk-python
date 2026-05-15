# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import contextvars
import logging
import os
from contextlib import contextmanager
from typing import TYPE_CHECKING, Generator

import allsolve_rawapi as rawapi
import requests
from .token import AccessToken
from .util import NotInitializedError

if TYPE_CHECKING:
    from .client import Client

logger = logging.getLogger(__name__)

_current_client: contextvars.ContextVar[Client | None] = contextvars.ContextVar(
    "_current_client", default=None
)


def _get_current_client() -> Client:
    """Return the active client or raise if none has been set up."""
    client = _current_client.get()
    if client is None:
        raise NotInitializedError(
            "API not set up. Use `allsolve.setup()` to set up the API."
        )
    return client


@contextmanager
def get_api() -> Generator[rawapi.DefaultApi, None, None]:
    with _get_current_client()._yield_api() as api:
        yield api


def get_http_basic_auth_header() -> dict[str, str]:
    return _get_current_client()._get_http_basic_auth_header()


def get_token_payload() -> AccessToken:
    client = _current_client.get()
    if client is None:
        raise ValueError("No access token")
    return client._get_token_payload()


def is_project_api_key() -> bool:
    """
    Return True if the current access token was issued for a project-scoped API key.
    """
    return _get_current_client()._is_project_api_key()


def check_for_project_api_key(project_id: str | None = None) -> str:
    return _get_current_client()._check_for_project_api_key(project_id)


def get_auth() -> str:
    return _get_current_client()._refresh_auth()


def get_http_session() -> requests.Session:
    client = _current_client.get()
    if client is None:
        return requests.Session()
    return client._http_session


def get_allow_insecure_http() -> bool:
    client = _current_client.get()
    if client is None:
        return False
    return client._allow_insecure_http


def is_setup() -> bool:
    """Check if the Allsolve API client has been initialized."""
    return _current_client.get() is not None


def get_cache_dir() -> str | None:
    """Get the cache directory path.
    The cache directory is created in the cache_base_dir directory,
    which can be set in setup method."""
    client = _current_client.get()
    if client is None:
        return None
    return client._cache_dir


def setup(
    api_key: str | None = None,
    api_secret: str | None = None,
    host: str | None = None,
    cache_base_dir: str = os.getcwd(),
    *,
    dotenv_file: str | None = ".env",
    allow_insecure_http: bool = False,
) -> Client:
    """
    Initialize the Allsolve API client and perform authentication.

    Credentials are resolved using a layered fallback — see
    :class:`~allsolve.client.Client` for the full priority chain.

    Parameters:
        api_key: The API key. Falls back to the
            ``ALLSOLVE_ACCESS_KEY`` / ``QS_ACCESS_KEY`` env var.
        api_secret: The API secret. Falls back to the
            ``ALLSOLVE_SECRET_KEY`` / ``QS_SECRET_KEY`` env var.
        host: The API host. Falls back to the
            ``ALLSOLVE_HOST`` / ``QS_HOST`` env var, then to
            ``https://allsolve.quanscient.com/``.
        cache_base_dir: Optional directory path for caching simulation data.
            If not provided, then cache directory will be created in the
            current working directory.
        dotenv_file: Path to a ``.env`` file whose variables are used
            for credential resolution (without modifying ``os.environ``).
            Defaults to ``".env"`` (silently skipped when absent).  Pass
            ``None`` to disable.
        allow_insecure_http: When ``False`` (default), only ``https://`` API
            hosts are allowed, plus ``http://localhost`` / ``http://127.0.0.1``.
            Set to ``True`` to allow other ``http://`` hosts (not for production).

    Returns:
        An :class:`~allsolve.client.Client` instance that provides methods
        for managing projects, quotas, and caching.

    Raises:
        ValueError: If required credentials cannot be resolved from any
            source, or if authentication fails.
    """
    from .client import Client

    return Client(
        api_key=api_key,
        api_secret=api_secret,
        host=host,
        cache_base_dir=cache_base_dir,
        dotenv_file=dotenv_file,
        allow_insecure_http=allow_insecure_http,
    )


def clean_cache() -> None:
    """
    Delete the cache directory used by all Allsolve projects.
    """
    _get_current_client().clean_cache()
