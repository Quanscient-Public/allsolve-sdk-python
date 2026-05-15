# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import base64
import datetime as dt
import logging
import multiprocessing as mp
import os
import pathlib
import shutil
from contextlib import contextmanager
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Generator, List, Optional

from .util import FileOverwriteMode

import allsolve_rawapi as rawapi
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .api import _current_client
from .project import GeometryPipelineVersion, Project
from .token import AccessToken, parse_access_token
from .util import NotProjectAPIKeyError

logger = logging.getLogger(__name__)

_CURRENT_PROJECT_FILE = ".allsolve_current_project_id"
_ALLSOLVE_CACHE_DIR = ".allsolve_cache"
_EXPIRE_MARGIN_S = 120
_MAX_RETRIES = 5


class Client:
    """
    Entry point for the AllSolve SDK.

    The simplest way to get started is to place a ``.env`` file in your
    working directory and create a client with no arguments::

        import allsolve

        client = allsolve.Client()
        project = client.get_project("my-project-id")

    You can pass the path to a ``.env`` file to the constructor::

        client = allsolve.Client(dotenv_file=".env")

    You can also pass credentials explicitly (they take priority over
    any ``.env`` file or environment variables)::

        client = allsolve.Client(
            api_key="...", api_secret="...", host="...",
        )

    For multi-tenancy, create additional clients and use them as context
    managers to temporarily make them the active default::

        client2 = allsolve.Client(
            api_key="my-other-api-key",
            api_secret="my-other-api-secret",
            host="https://other-host.example.com/",
            _set_as_default=False,
            cache_base_dir="other-cache-dir", # optional, defaults to the current working directory
        )
        with client2:
            projects = client2.get_projects()
    """

    # ------------------------------------------------------------------
    # Static / class helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_env(
        name_allsolve: str,
        name_qs: str,
        dotenv_vars: dict[str, str] | None = None,
    ) -> str | None:
        """Look up a config value by ALLSOLVE_ name, falling back to QS_ name.

        Resolution order: ``os.environ`` first, then *dotenv_vars* (if
        provided).  This keeps real environment variables at higher priority
        than values read from a ``.env`` file.
        """
        value = os.environ.get(name_allsolve) or os.environ.get(name_qs)
        if value:
            return value
        if dotenv_vars is not None:
            return dotenv_vars.get(name_allsolve) or dotenv_vars.get(name_qs)
        return None

    @staticmethod
    def _format_auth_failure_detail(exc: rawapi.ApiException) -> str:
        parts: list[str] = []
        if exc.status is not None:
            parts.append(f"HTTP {exc.status}")
        if exc.reason:
            parts.append(str(exc.reason))
        body = exc.body
        if body:
            if isinstance(body, bytes):
                body = body.decode("utf-8", errors="replace")
            parts.append(str(body)[:500])
        return "; ".join(parts) if parts else str(exc)

    @staticmethod
    def _load_dotenv(dotenv_file: str | os.PathLike[str] | None) -> dict[str, str]:
        """Read a dotenv file and return its variables as a dictionary.

        Unlike ``load_dotenv``, this does **not** modify ``os.environ``,
        keeping secrets out of the global process environment.

        * ``None`` — skip entirely (returns empty dict).
        * Default ``".env"`` — silently ignored when the file is absent.
        * Any other explicit path — ``ValueError`` if the file is missing.
        """
        if dotenv_file is None:
            return {}
        if not os.path.isfile(dotenv_file):
            if os.fspath(dotenv_file) == ".env":
                return {}
            raise ValueError(f"dotenv_file not found: {dotenv_file}")

        from dotenv import dotenv_values

        return {k: v for k, v in dotenv_values(dotenv_file).items() if v is not None}

    @staticmethod
    def _validate_host(host: str, allow_insecure_http: bool) -> None:
        from urllib.parse import urlparse

        parsed = urlparse(host)
        scheme = parsed.scheme.lower()

        if scheme == "https":
            return

        if scheme == "http":
            hostname = (parsed.hostname or "").lower()
            if hostname in ("localhost", "127.0.0.1", "::1"):
                return
            if allow_insecure_http:
                return
            raise ValueError(
                f"Host {host!r} uses HTTP, which transmits credentials in plaintext. "
                "Use HTTPS, or pass allow_insecure_http=True for non-production use."
            )

        raise ValueError(
            f"Host {host!r} does not use HTTPS. "
            "The host must start with https:// (or http://localhost for local development)."
        )

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------

    _DEFAULT_HOST = "https://allsolve.quanscient.com/"

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        host: str | None = None,
        cache_base_dir: str = os.getcwd(),
        *,
        dotenv_file: str | os.PathLike[str] | None = ".env",
        allow_insecure_http: bool = False,
        _set_as_default: bool = True,
    ) -> None:
        """
        Initialize the Allsolve API client and perform authentication.

        Credentials are resolved using a layered fallback:

        1. **Explicit parameters** take highest priority.
        2. **Environment variables** — ``ALLSOLVE_ACCESS_KEY``,
           ``ALLSOLVE_SECRET_KEY``, and ``ALLSOLVE_HOST`` (or their
           ``QS_`` prefixed equivalents).
        3. **Dotenv file** — if ``dotenv_file`` points to an existing file,
           its variables are read (but **not** injected into
           ``os.environ``). Defaults to ``".env"``.  Pass ``None`` to
           disable auto-detection.

        Parameters:
            api_key: The API key. Falls back to the
                ``ALLSOLVE_ACCESS_KEY`` / ``QS_ACCESS_KEY`` env var.
            api_secret: The API secret. Falls back to the
                ``ALLSOLVE_SECRET_KEY`` / ``QS_SECRET_KEY`` env var.
            host: The API host. Falls back to the
                ``ALLSOLVE_HOST`` / ``QS_HOST`` env var, then to
                ``https://allsolve.quanscient.com/``.
            cache_base_dir: Directory path for caching simulation data.
                If not provided, the cache directory (.allsolve_cache)
                is created in the current working directory.
            dotenv_file: Path to a ``.env`` file whose variables are used
                for credential resolution (without modifying ``os.environ``).
                The file is silently skipped when it does not exist (for the
                default ``".env"``).  Pass an explicit path to require the
                file — a ``ValueError`` is raised if it is missing.  Pass
                ``None`` to skip dotenv loading entirely.
            allow_insecure_http: When ``False`` (default), only ``https://``
                hosts are allowed, plus ``http://localhost`` and
                ``http://127.0.0.1`` for local development. Set to ``True``
                to allow other ``http://`` hosts (not recommended for production).
            _set_as_default: When ``True`` (the default), this client becomes
                the active default.  Set to ``False`` when creating a
                secondary client for multi-tenancy.

        Raises:
            ValueError: If required credentials cannot be resolved from any
                source, if an explicitly provided ``dotenv_file`` does not
                exist, or if authentication fails.
        """
        dotenv_vars = self._load_dotenv(dotenv_file)

        if api_key is None:
            api_key = self._resolve_env(
                "ALLSOLVE_ACCESS_KEY", "QS_ACCESS_KEY", dotenv_vars
            )
        if api_secret is None:
            api_secret = self._resolve_env(
                "ALLSOLVE_SECRET_KEY", "QS_SECRET_KEY", dotenv_vars
            )
        if host is None:
            host = (
                self._resolve_env("ALLSOLVE_HOST", "QS_HOST", dotenv_vars)
                or self._DEFAULT_HOST
            )

        _no_creds_hint = (
            " Pass it explicitly, set the corresponding environment variable, "
            "or create a .env file."
        )
        if not api_key:
            raise ValueError("api_key is required." + _no_creds_hint)
        if not api_secret:
            raise ValueError("api_secret is required." + _no_creds_hint)

        key = api_key.strip()
        secret = api_secret.strip()
        host_str = host.strip()
        if not key:
            raise ValueError("api_key must not be empty." + _no_creds_hint)
        if not secret:
            raise ValueError("api_secret must not be empty." + _no_creds_hint)
        if not host_str:
            raise ValueError("host must not be empty.")

        self._credentials = {"api_key": key, "api_secret": secret}

        if not os.path.exists(cache_base_dir):
            raise ValueError(
                f"Output cache base directory {cache_base_dir} does not exist"
            )
        self._cache_dir: str | None = os.path.join(cache_base_dir, _ALLSOLVE_CACHE_DIR)

        self._host = host_str.rstrip("/")
        self._validate_host(self._host, allow_insecure_http)
        self._allow_insecure_http = allow_insecure_http
        self._api_lock = mp.Lock()
        self._access_token: rawapi.OauthClientTokenResponse | None = None
        self._access_token_refreshed: dt.datetime | None = None

        self._config = rawapi.Configuration(host=self._host)
        self._config.retries = Retry(
            total=_MAX_RETRIES,
            status_forcelist=[429, 502, 503, 504],
            backoff_factor=1.0,
            respect_retry_after_header=True,
            allowed_methods=None,
        )
        api_client = rawapi.ApiClient(configuration=self._config)
        self._api: rawapi.DefaultApi = rawapi.DefaultApi(api_client=api_client)

        try:
            self._sdk_version = version("allsolve")
        except PackageNotFoundError:
            self._sdk_version = "dev"
        api_client.user_agent = f"allsolve-sdk-{self._sdk_version}"

        self._http_session = requests.Session()
        self._http_session.headers["User-Agent"] = f"allsolve-sdk-{self._sdk_version}"
        _adapter = HTTPAdapter(max_retries=self._config.retries)
        self._http_session.mount("https://", _adapter)
        self._http_session.mount("http://", _adapter)

        if _set_as_default:
            _current_client.set(self)

        try:
            self._refresh_auth()
        except rawapi.ApiException as e:
            raise ValueError(
                f"Authentication failed for host {self._host!r}: "
                f"{self._format_auth_failure_detail(e)} "
                "Double-check your API key and secret, and ensure the host "
                "matches your API key."
            ) from None

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"Client(host={self._host!r}, sdk_version={self._sdk_version!r})"

    def __enter__(self) -> Client:
        self._ctx_token = _current_client.set(self)
        return self

    def __exit__(self, *exc: object) -> None:
        _current_client.reset(self._ctx_token)

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        state.pop("_credentials", None)
        state.pop("_api_lock", None)
        return state

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def host(self) -> str:
        """The API host this client is connected to."""
        return self._host

    @property
    def cache_dir(self) -> str | None:
        """The cache directory path, or ``None`` if not set."""
        return self._cache_dir

    @property
    def sdk_version(self) -> str:
        """The SDK version string."""
        return self._sdk_version

    # ------------------------------------------------------------------
    # Internal API / auth helpers (used by api.py delegation layer)
    # ------------------------------------------------------------------

    @contextmanager
    def _yield_api(self) -> Generator[rawapi.DefaultApi, None, None]:
        """Context manager that yields the raw API under the instance lock."""
        with self._api_lock:
            try:
                yield self._api
            finally:
                pass

    def _get_http_basic_auth_header(self) -> dict[str, str]:
        creds = self._credentials
        return {
            "Authorization": "Basic {}".format(
                base64.b64encode(
                    f"{creds['api_key']}:{creds['api_secret']}".encode()
                ).decode(),
            ),
        }

    def _get_token_payload(self) -> AccessToken:
        if self._access_token is None:
            raise ValueError("No access token")
        return parse_access_token(self._access_token.access_token)

    def _refresh_auth(self) -> str:
        """Return a Bearer token string, refreshing the token if needed.

        The _EXPIRE_MARGIN_S (120s) buffer ensures the token is refreshed
        before actual expiry, mitigating clock skew between client and server.
        """
        if (
            self._access_token is None
            or self._access_token_refreshed is None
            or dt.datetime.now(dt.timezone.utc)
            >= self._access_token_refreshed
            + dt.timedelta(seconds=self._access_token.expires_in - _EXPIRE_MARGIN_S)
        ):
            self._access_token = self._api.request_oauth_client_token(
                grant_type=rawapi.OauthClientTokenGrantType.CLIENT_CREDENTIALS,
                scope="scripting manualScaling",
                _headers=self._get_http_basic_auth_header(),
            )
            self._access_token_refreshed = dt.datetime.now(dt.timezone.utc)

        return "Bearer {}".format(self._access_token.access_token)

    def _is_project_api_key(self) -> bool:
        return self._get_token_payload().project_id is not None

    def _check_for_project_api_key(self, project_id: str | None = None) -> str:
        if project_id is None:
            project_id = self._get_token_payload().project_id
            if project_id is None:
                raise NotProjectAPIKeyError("No project ID found in token")
        return project_id

    # ------------------------------------------------------------------
    # Project CRUD
    # ------------------------------------------------------------------

    def get_project(self, project_id: str) -> Project:
        """
        Get a project by its ID.

        Parameters:
            project_id: The ID of the project.

        Returns:
            The project.
        """
        return Project.get(project_id)

    def get_project_from_token(self) -> Project:
        """
        Get the project associated with the current project-scoped API key.

        Returns:
            The project.

        Raises:
            NotProjectAPIKeyError: If not authenticated with a project API key.
        """
        return Project.from_token()

    def get_projects(
        self,
        *,
        page_size: Optional[int] = None,
        page: Optional[int] = None,
        project_type_filter: rawapi.ProjectTypeFilter = rawapi.ProjectTypeFilter.API,
    ) -> List[Project]:
        """
        Get all projects accessible with the current credentials.

        Parameters:
            page_size: Number of projects per page, defaults to 1000.
            page: Page number to return, defaults to 1.
            project_type_filter: Filter by project type. Defaults to ProjectTypeFilter.API.
               By default, only projects created with the public API are returned.

        Returns:
            A list of projects.
        """
        return Project.get_all(
            page_size=page_size,
            page=page,
            project_type_filter=project_type_filter,
        )

    def get_project_by_name(
        self,
        name: str,
        project_type_filter: rawapi.ProjectTypeFilter = rawapi.ProjectTypeFilter.ALL,
    ) -> Project | None:
        """
        Search for a project that matches the given name.
        Returns None if no project matches the given name.
        Raises ValueError if multiple projects match the given name.

        Parameters:
            name: The name of the project to search for.
            project_type_filter: Filter by project type. Defaults to ProjectTypeFilter.ALL.
               By default, all project types are returned.
        Returns:
            The project that matches the given name.
        """
        return Project.get_by_name(name=name, project_type_filter=project_type_filter)

    def create_project(
        self,
        name: str,
        description: str = "",
        organization_write_access: bool | None = None,
        labels: List[str] | None = None,
        geometry_pipeline_version: GeometryPipelineVersion = GeometryPipelineVersion.V2,
        dimension: int = 3,
        geometry_no_implicit_fragment: bool = False,
    ) -> Project:
        """
        Create a new project.

        Parameters:
            name: The name of the project.
            description: The description of the project.
            organization_write_access: Optional boolean whether the organization has write access to the project.
            labels: Optional list of labels for the project.
            geometry_pipeline_version: Optional GeometryPipelineVersion. Default is V2.
            dimension: Optional dimension of the project. Default is 3.
            geometry_no_implicit_fragment: Optional boolean whether to disable the automatic
                final Fragment All operation. Default is False.
                By default, the final Fragment All operation splits intersecting geometric
                entities into non-intersecting, disjoint parts. Setting parameter to True
                prevents automatic splitting, preserving the original geometric entities as-is.

        Returns:
            The created project.

        Raises:
            ValueError: If authenticated with a project API key.
        """
        return Project.create(
            name=name,
            description=description,
            organization_write_access=organization_write_access,
            labels=labels,
            geometry_pipeline_version=geometry_pipeline_version,
            dimension=dimension,
            geometry_no_implicit_fragment=geometry_no_implicit_fragment,
        )

    def delete_project(self, project_id: str) -> None:
        """
        Delete a project by its ID.

        Parameters:
            project_id: The ID of the project to delete.
        """
        project = Project.get(project_id)
        project.delete()

    def copy_project(
        self,
        project_id: str,
        with_results: bool = False,
        name: str | None = None,
        wait_for_completion: bool = True,
    ) -> Project:
        """
        Copy a project.

        Parameters:
            project_id: The ID of the project to copy.
            with_results: If ``True``, copy result files as well.
            name: Name for the new project.
            wait_for_completion: If ``True``, wait for file copying to finish.

        Returns:
            The copied project.

        Raises:
            ValueError: If authenticated with a project API key. Copying projects
                requires an organization API key.
        """
        project = Project.get(project_id)
        return project.copy(
            with_results=with_results,
            name=name,
            wait_for_completion=wait_for_completion,
        )

    def get_url(self, project: Project) -> str:
        """
        Return the browser URL for a project.

        Parameters:
            project: The project to build the URL for.

        Returns:
            The full URL to open the project in the Allsolve web app.
        """
        return f"{self._host}/#/projects/{project.id}/model"

    # ------------------------------------------------------------------
    # Current project persistence
    # ------------------------------------------------------------------

    def set_current_project(self, project: Project | None) -> None:
        """
        Persist a project as the "current" project in the cache directory.
        Only the project ID is stored to disk, not the project object itself.

        This allows one script to create or select a project and another
        script to retrieve it with :meth:`get_current_project`.

        Passing ``None`` clears the stored project.

        The "current" project is not Client specific. For multi-tenancy
        scenarios, consider using separate ``cache_base_dir`` paths or manage
        project IDs explicitly.

        Parameters:
            project: The project to store, or ``None`` to clear.

        Raises:
            ValueError: If the cache directory is not configured.
        """
        cache_dir = self.cache_dir
        if cache_dir is None:
            raise ValueError("Cache directory not set")
        os.makedirs(cache_dir, mode=0o700, exist_ok=True)
        path = os.path.join(cache_dir, _CURRENT_PROJECT_FILE)
        if project is None:
            if os.path.exists(path):
                os.remove(path)
            return
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.write(fd, project.id.encode())
        finally:
            os.close(fd)

    def get_current_project(self) -> Project | None:
        """
        Retrieve the project previously stored with :meth:`set_current_project`.

        Returns:
            The stored project, or ``None`` if no project has been set
            or the stored reference was cleared.

        Raises:
            ValueError: If the cache directory is not configured.
        """
        cache_dir = self.cache_dir
        if cache_dir is None:
            raise ValueError("Cache directory not set")
        path = os.path.join(cache_dir, _CURRENT_PROJECT_FILE)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            project_id = f.read().strip()
        if not project_id:
            return None
        return Project.get(project_id)

    # ------------------------------------------------------------------
    # Import / Export
    # ------------------------------------------------------------------

    def import_project(
        self,
        file_or_data: str | dict[str, Any],
        project_to_modify: Project | None = None,
        verbose: bool | None = None,
        run_meshes_and_simulations: bool = True,
        *,
        allow_paths_outside_project: bool = False,
    ) -> Project:
        """
        Import a project from a YAML/JSON file or a dictionary.

        Parameters:
            file_or_data: Path to a YAML/JSON file or a data dictionary.
            project_to_modify: Optional existing project to update instead of creating
                a new one. By default, a new project is created.
            verbose: When true, print progress messages and stream logs to the
                console during import. When ``None``, use the ``verbose`` field from the import
                data (YAML/JSON or dict).
            run_meshes_and_simulations: When ``False``, skip running all meshes and simulations
                after import. Defaults to ``True``. To skip individual meshes or simulations instead,
                set ``createOnly: true`` on the corresponding entry in the import data.
            allow_paths_outside_project: When ``False`` (default), every file path in the
                import (relative or absolute) must resolve under the project directory
                (the parent folder of a YAML/JSON file). Set to ``True`` only for trusted
                import data that must use absolute paths to files outside that directory
                (e.g. shared assets on a secure host). **Do not** use for untrusted bundles.

        Returns:
            The imported project.
        """
        from .import_project import import_project as _import_project

        return _import_project(
            file_or_data=file_or_data,
            project_to_modify=project_to_modify,
            verbose=verbose,
            run_meshes_and_simulations=run_meshes_and_simulations,
            allow_paths_outside_project=allow_paths_outside_project,
        )

    def export_project_yaml(
        self,
        project: Project,
        output_path: str,
        *,
        include_meshes: bool = True,
        download_geometries: bool = False,
        files_output_dir: str | pathlib.Path = ".",
        file_overwrite_mode: FileOverwriteMode = FileOverwriteMode.SKIP,
    ) -> None:
        """
        Export project to a YAML file.

        Parameters:
            project: The project to export.
            output_path: Path to write the YAML file.
            include_meshes: Whether to include mesh definitions (default ``True``).
            download_geometries: Download geometry files to disk.
            files_output_dir: Directory for downloads. When ``download_geometries`` is True
                and this is omitted, defaults to the parent directory of ``output_path``.
            file_overwrite_mode: Controls behavior when a geometry file already
                exists on disk. ``FileOverwriteMode.SKIP`` (default) keeps the
                existing file, ``FileOverwriteMode.OVERWRITE`` replaces it, and
                ``FileOverwriteMode.ERROR`` raises ``FileExistsError``.
        """

        project.export_yaml(
            output_path=output_path,
            include_meshes=include_meshes,
            download_geometries=download_geometries,
            files_output_dir=files_output_dir,
            file_overwrite_mode=file_overwrite_mode,
        )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def clean_cache(self) -> None:
        """
        Delete the cache directory used by all Allsolve projects.

        All simulation output data that was downloaded to the cache directory is deleted.
        Clears the current project selection set using :meth:`set_current_project`.
        """
        if self._cache_dir is None:
            raise ValueError("Cache directory not set")
        if os.path.exists(self._cache_dir):
            shutil.rmtree(self._cache_dir)

    def get_quota(self) -> rawapi.OrganizationQuota:
        """
        Get the organization's quota information.

        Returns:
            Current quota status including total credits, used credits,
            and concurrent core limits.
        """
        from .quota import get_quota as _get_quota

        return _get_quota()

    def is_project_api_key(self) -> bool:
        """
        Check whether the current credentials are a project-scoped API key.

        Returns:
            ``True`` if the access token was issued for a project-scoped key.
        """
        return self._is_project_api_key()

    def is_organization_api_key(self) -> bool:
        """
        Check whether the current credentials are an organization-level API key.

        Returns:
            ``True`` if the access token was **not** issued for a
            project-scoped key (i.e. it is an organization key).
        """
        return not self.is_project_api_key()

    def get_cache_dir(self) -> str | None:
        """
        Get the cache directory path.

        Returns:
            The cache directory path, or ``None`` if not set.
        """
        return self._cache_dir
