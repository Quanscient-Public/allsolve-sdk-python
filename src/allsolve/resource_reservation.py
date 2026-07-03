# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING, Generator

import allsolve_rawapi as rawapi
from typing_extensions import Self

from .api import _get_current_client, get_api, get_auth
from .util import ResourceReservationError, parse_api_error

if TYPE_CHECKING:
    from .client import Client
    from .simulation import CPU

logger = logging.getLogger(__name__)

RENEW_INTERVAL_S = 15.0
DEFAULT_READY_POLL_INTERVAL_S = 1.0
DEFAULT_MAX_IDLE_SECONDS = 600.0


class ReservationStatus(Enum):
    """Status of a compute resource reservation."""

    QUEUED = rawapi.ReservationStatus.QUEUED
    RESERVING = rawapi.ReservationStatus.RESERVING
    RESERVED = rawapi.ReservationStatus.RESERVED
    RELEASING = rawapi.ReservationStatus.RELEASING
    RELEASED = rawapi.ReservationStatus.RELEASED
    FAILING = rawapi.ReservationStatus.FAILING
    FAILED = rawapi.ReservationStatus.FAILED


class _ReservationLeaseKeeper:  # pyright: ignore[reportUnusedClass]
    """Background lease renewal for a single reservation id (used by :class:`~allsolve.client.Client`).

    One daemon thread per reservation id renews the 120-second server lease every
    :data:`RENEW_INTERVAL_S` seconds. The thread runs while **either** hold counter is
    non-zero; both are reference-counted so nested callers (e.g. overlapping
    :func:`keep_reservation_alive` contexts) can share the same keeper safely.

    The counters track two independent reasons to keep renewing, with different idle
    timeout rules:

    * ``_auto_renew_refs`` — idle renewal between jobs (from
      :meth:`ResourceReservation.create` / :meth:`ResourceReservation.start_auto_renew`).
      Subject to ``max_idle_seconds``: when no job holds remain, renewal stops after
      that many consecutive idle seconds. Does **not** release the reservation.
    * ``_job_refs`` — job-scoped renewal while work is in flight (from
      :meth:`GeometryBuilder.run`, :meth:`Mesh.run`, :meth:`Simulation.run`, or
      :func:`keep_reservation_alive`). No idle timeout; the lease must stay alive until
      the job finishes.
    """

    def __init__(self, reservation_id: str, client: "Client") -> None:
        """
        Initialize a lease keeper for one reservation.

        Args:
            reservation_id: Server-side reservation id to renew.
            client: Client used for API calls from the background thread.
        """
        self._reservation_id = reservation_id
        self._client = client
        self._lock = threading.Lock()
        self._job_refs = 0  # active jobs; pauses idle timeout while > 0
        self._auto_renew_refs = 0  # idle renewal holds; subject to max_idle_seconds
        self._max_idle_seconds: float | None = None
        self._auto_renew_started_at: float | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def acquire_job(self) -> None:
        """
        Increment the job-scoped renewal hold and start renewal if needed.

        Pauses the idle auto-renew timer while any job holds remain.
        """
        with self._lock:
            self._job_refs += 1
            self._ensure_thread_started_unlocked()

    def release_job(self) -> None:
        """
        Decrement the job-scoped renewal hold.

        When the last job hold is released and auto-renew is still active,
        restarts the idle timer. Stops the background thread when no holds remain.
        """
        with self._lock:
            if self._job_refs <= 0:
                return
            if self._job_refs <= 1:
                self._job_refs = 0
            else:
                self._job_refs -= 1
            if self._job_refs == 0 and self._auto_renew_refs > 0:
                self._auto_renew_started_at = time.monotonic()
            if not self._is_active_unlocked():
                self._stop.set()

    def acquire_auto_renew(self, *, max_idle_seconds: float | None = None) -> None:
        """
        Increment the idle auto-renew hold and start renewal if needed.

        Args:
            max_idle_seconds: Maximum consecutive idle time (no job holds) before
                auto-renew expires. When ``None``, idle renewal has no timeout.
        """
        with self._lock:
            self._auto_renew_refs += 1
            if max_idle_seconds is not None:
                self._max_idle_seconds = max_idle_seconds
                if self._auto_renew_started_at is None:
                    self._auto_renew_started_at = time.monotonic()
            self._ensure_thread_started_unlocked()

    def release_auto_renew(self) -> None:
        """
        Decrement the idle auto-renew hold.

        Clears idle timeout state when the last auto-renew hold is released.
        Stops the background thread when no holds remain.
        """
        with self._lock:
            if self._auto_renew_refs <= 0:
                return
            if self._auto_renew_refs <= 1:
                self._auto_renew_refs = 0
                self._max_idle_seconds = None
                self._auto_renew_started_at = None
            else:
                self._auto_renew_refs -= 1
            if not self._is_active_unlocked():
                self._stop.set()

    def _ensure_thread_started_unlocked(self) -> None:
        """
        Start the daemon renewal thread if it is not already running.

        Caller must hold ``self._lock``.
        """
        if self._thread is None or not self._thread.is_alive():
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._run,
                name=f"reservation-lease-{self._reservation_id}",
                daemon=True,
            )
            self._thread.start()

    def is_active(self) -> bool:
        """Return whether any job or auto-renew holds are active."""
        with self._lock:
            return self._is_active_unlocked()

    def _is_active_unlocked(self) -> bool:
        """
        Return whether any holds are active without acquiring the lock.

        Caller must hold ``self._lock``.
        """
        return self._job_refs > 0 or self._auto_renew_refs > 0

    def _auto_renew_expired_unlocked(self) -> bool:
        """
        Return whether idle auto-renew has exceeded ``max_idle_seconds``.

        Caller must hold ``self._lock``. Only applies when auto-renew is active,
        no job holds remain, and a timeout was configured.
        """
        if self._auto_renew_refs <= 0:
            return False
        if self._job_refs > 0:
            return False
        if self._max_idle_seconds is None or self._auto_renew_started_at is None:
            return False
        return time.monotonic() - self._auto_renew_started_at >= self._max_idle_seconds

    def _expire_auto_renew_if_needed(self) -> None:
        """Release auto-renew when the idle timeout has elapsed."""
        with self._lock:
            if not self._auto_renew_expired_unlocked():
                return
        self.release_auto_renew()

    def _deactivate_on_renew_failure(self) -> None:
        """Clear all holds and remove this keeper from the client after renewal fails."""
        with self._lock:
            self._job_refs = 0
            self._auto_renew_refs = 0
            self._max_idle_seconds = None
            self._auto_renew_started_at = None
            self._stop.set()
        self._client._drop_lease_keeper(self._reservation_id)

    def _renew_lease(self) -> None:
        """
        Renew the reservation lease via the API.

        Raises:
            ResourceReservationError: When the renew API call fails.
        """
        with get_api() as api:
            try:
                api.renew_resource_reservation_lease(
                    authorization=get_auth(),
                    reservation_id=self._reservation_id,
                    body={},
                )
            except rawapi.ApiException as e:
                error_code, message = parse_api_error(e)
                raise ResourceReservationError(message, error_code=error_code) from e

    def _tick_renewal(self) -> bool:
        """
        Perform one renewal cycle while the keeper is active.

        Returns:
            False if the keeper should stop (inactive, stopped, expired, or renewal
            failed); True to continue the renewal loop.
        """
        if self._stop.is_set():
            return False
        if not self.is_active():
            return False
        self._expire_auto_renew_if_needed()
        if not self.is_active():
            return False
        try:
            self._renew_lease()
        except ResourceReservationError as e:
            logger.error(
                "Failed to renew reservation %s lease (error_code=%s): %s",
                self._reservation_id,
                e.error_code,
                e,
            )
            self._deactivate_on_renew_failure()
            return False
        except Exception:
            logger.exception(
                "Unexpected error renewing reservation %s",
                self._reservation_id,
            )
            self._deactivate_on_renew_failure()
            return False
        return True

    def _run(self) -> None:
        """Background loop: renew periodically until stopped or inactive."""
        with self._client.in_thread():
            while True:
                if not self._tick_renewal():
                    break
                if self._stop.wait(RENEW_INTERVAL_S):
                    break


class ResourceReservation:
    """
    A compute resource reservation holding cloud capacity for geometry, mesh, or simulation jobs.

    Each reservation has a 120-second lease that must be renewed before it expires;
    otherwise the server will release the reservation. Reservations consume quota while
    idle. :meth:`create` starts idle lease renewal automatically (see ``max_idle_seconds``).

    The SDK renews the lease in two ways:

    * **Idle renewal** — started by :meth:`create` (and optionally :meth:`start_auto_renew`).
      Renews the lease while the reservation is idle between jobs, until
      :meth:`stop_auto_renew` or :meth:`release` is called, or ``max_idle_seconds`` of
      consecutive idle time elapses. When the idle limit is reached, renewal stops and
      the reservation is released automatically after the lease expires. The idle timer
      resets automatically when a job ends if job-scoped renewal was used (see below).
    * **Job-scoped renewal** — triggered by :meth:`GeometryBuilder.run` /
      :meth:`GeometryBuilder.build`, :meth:`Mesh.run`, :meth:`Simulation.run`, or by
      :func:`keep_reservation_alive` when polling after :meth:`GeometryBuilder.start`,
      :meth:`Mesh.start`, or :meth:`Simulation.start`. Keeps the lease alive for the
      duration of the job and resets the idle timer when the job finishes.

    :meth:`GeometryBuilder.start`, :meth:`Mesh.start`, and :meth:`Simulation.start` assign
    a reservation to the job but do not renew the lease automatically during manual
    status polling.

    Call :meth:`renew_lease` manually if you need explicit control.
    """

    _LEASE_DURATION_S = 120
    _TERMINAL_STATUSES = frozenset(
        {
            ReservationStatus.RELEASED,
            ReservationStatus.FAILED,
            ReservationStatus.RELEASING,
            ReservationStatus.FAILING,
        }
    )
    _RELEASE_FAILURE_STATUSES = frozenset(
        {
            ReservationStatus.FAILED,
            ReservationStatus.FAILING,
        }
    )

    @staticmethod
    def _lease_expires_at(now: datetime | None = None) -> datetime:
        """Return a lease expiry matching the server contract (now + 120 seconds)."""
        base = now or datetime.now(timezone.utc)
        return base + timedelta(seconds=ResourceReservation._LEASE_DURATION_S)

    @staticmethod
    def _cpu_to_node_type_id(node_type: "CPU | None") -> str | None:
        """Map :class:`CPU` to API ``nodeType`` / ``mainNodeType`` string, or omit for default."""
        if node_type is None:
            return None
        value = node_type.value
        if value is None:
            return None
        return value

    @staticmethod
    def _build_create_request(
        *,
        num_nodes: int,
        num_replicas: int,
        node_type: "CPU | None",
        main_node_type: "CPU | None",
        team_id: str | None,
    ) -> rawapi.ResourceReservationRequest:
        node_type_id = ResourceReservation._cpu_to_node_type_id(node_type)
        main_node_type_id = ResourceReservation._cpu_to_node_type_id(main_node_type)
        return rawapi.ResourceReservationRequest(
            numNodes=num_nodes,
            numReplicas=num_replicas,
            nodeType=node_type_id,
            mainNodeType=main_node_type_id,
            teamId=team_id,
        )

    @classmethod
    def create(
        cls,
        *,
        node_type: "CPU | None" = None,
        main_node_type: "CPU | None" = None,
        num_nodes: int = 1,
        num_replicas: int = 1,
        team_id: str | None = None,
        max_idle_seconds: float = DEFAULT_MAX_IDLE_SECONDS,
    ) -> Self:
        """
        Create a compute resource reservation.

        Parameters:
            node_type: Compute size (:class:`~allsolve.CPU`), same as simulation ``nodeType``.
                When omitted or :attr:`~allsolve.CPU.DEFAULT`, the server uses ``large-new``.
            main_node_type: Optional main / coordinator node size; defaults to ``node_type``.
                You may need to select a bigger main node if the mesh is very large or
                memory limitations require it.
            num_nodes: Number of DDM nodes per replica (minimum 1).
                Select more if you need the due memory limitations.
            num_replicas: Replica groups to reserve (minimum 1); one per
                concurrent sweep step. All reserved replicas incur quota cost
                for the lease duration. Sweep parallelism is capped by your
                organization's max parallelism (default 100) — excess replicas
                remain idle but are still billed.
            team_id: Team whose quota to use. When team credits enforcement is active
                and the API user belongs to more than one team with active team credits,
                this is required. When omitted and the user belongs to exactly one such
                team, that team is used automatically. Use :func:`~allsolve.get_teams`
                to discover valid team ids.
            max_idle_seconds: Maximum consecutive idle time between jobs (default 10
                minutes) for which the SDK renews the lease in a background thread.
                :meth:`create` starts this automatically. Renewal stops when the limit
                is reached, :meth:`stop_auto_renew` is called, or :meth:`release` is
                called; reaching the limit does not call :meth:`release`. The idle
                timer restarts each time a job finishes (when using
                :meth:`Mesh.run`, :meth:`Simulation.run`,
                or :func:`keep_reservation_alive`).

        Returns:
            The created reservation (may still be provisioning).

        Raises:
            ResourceReservationError: On API errors (including ``quota_exceeded``,
                ``team_reserved_quota_not_active``, and
                ``team_quota_enforcement_active_no_team``).
        """
        request = cls._build_create_request(
            num_nodes=num_nodes,
            num_replicas=num_replicas,
            node_type=node_type,
            main_node_type=main_node_type,
            team_id=team_id,
        )
        with get_api() as api:
            try:
                raw = api.create_resource_reservation(
                    authorization=get_auth(),
                    resource_reservation_request=request,
                )
            except rawapi.ApiException as e:
                error_code, message = parse_api_error(e)
                raise ResourceReservationError(message, error_code=error_code) from e
        reservation = cls(raw)
        reservation.start_auto_renew(max_idle_seconds=max_idle_seconds)
        return reservation

    @classmethod
    def get(cls, reservation_id: str) -> Self:
        """
        Fetch the current reservation status.

        Does not start idle lease renewal. Call :meth:`start_auto_renew` if you load a
        reservation by id and need the SDK to renew its lease while idle.

        Parameters:
            reservation_id: Reservation id from create.

        Raises:
            ResourceReservationError: On API errors.
        """
        with get_api() as api:
            try:
                raw = api.get_resource_reservation(
                    authorization=get_auth(),
                    reservation_id=reservation_id,
                )
            except rawapi.ApiException as e:
                error_code, message = parse_api_error(e)
                raise ResourceReservationError(message, error_code=error_code) from e
        return cls(raw)

    def __init__(self, raw: rawapi.ResourceReservation) -> None:
        self._raw = raw

    def __repr__(self) -> str:
        return (
            f"ResourceReservation(id={self.id!r}, status={self.status!r}, "
            f"expires_at={self.expires_at!r})"
        )

    @property
    def id(self) -> str:
        """Reservation id for renew, release, and job start."""
        return self._raw.id

    @property
    def status(self) -> ReservationStatus:
        """Current reservation status."""
        return ReservationStatus(self._raw.status)

    @property
    def requested_at(self) -> datetime:
        """When the reservation was requested."""
        return self._raw.requested_at

    @property
    def started_at(self) -> datetime | None:
        """When the reservation was started."""
        return self._raw.started_at

    @property
    def reserved_at(self) -> datetime | None:
        """When the reservation was reserved."""
        return self._raw.reserved_at

    @property
    def released_at(self) -> datetime | None:
        """When the reservation was released."""
        return self._raw.released_at

    @property
    def expires_at(self) -> datetime:
        """When the reservation lease expires."""
        return self._raw.expires_at

    def refresh(self) -> None:
        """Reload reservation state from the API."""
        self._raw = ResourceReservation.get(self.id)._raw

    def renew_lease(self) -> None:
        """
        Extend the reservation lease (120 seconds from now on the server).

        Raises:
            ResourceReservationError: On failure, including ``quota_exceeded`` which
                may release the reservation server-side.
        """
        with get_api() as api:
            try:
                api.renew_resource_reservation_lease(
                    authorization=get_auth(),
                    reservation_id=self.id,
                    body={},
                )
            except rawapi.ApiException as e:
                error_code, message = parse_api_error(e)
                raise ResourceReservationError(message, error_code=error_code) from e
        self._raw = self._raw.model_copy(
            update={"expires_at": self._lease_expires_at()}
        )

    def release(self) -> None:
        """Release reserved compute and stop idle lease renewal.

        Idempotent if already released on the server; API errors still propagate.
        """
        self.stop_auto_renew()
        with get_api() as api:
            try:
                api.release_resource_reservation(
                    authorization=get_auth(),
                    reservation_id=self.id,
                    body={},
                )
            except rawapi.ApiException as e:
                error_code, message = parse_api_error(e)
                raise ResourceReservationError(message, error_code=error_code) from e
        self.refresh()

    def wait_until_ready(
        self,
        *,
        poll_interval_s: float = DEFAULT_READY_POLL_INTERVAL_S,
        timeout_s: float | None = None,
    ) -> None:
        """
        Poll until ``status`` is :attr:`ReservationStatus.RESERVED`.

        Parameters:
            poll_interval_s: Seconds between status polls.
            timeout_s: Optional timeout; raises :exc:`TimeoutError` when exceeded.

        Raises:
            ResourceReservationError: If the reservation enters a terminal failure state.
            TimeoutError: When ``timeout_s`` is exceeded.
        """
        deadline = None if timeout_s is None else time.monotonic() + timeout_s
        while True:
            self.refresh()
            if self.status is ReservationStatus.RESERVED:
                return
            if self.status in self._TERMINAL_STATUSES:
                raise ResourceReservationError(
                    f"Reservation {self.id!r} ended with status {self.status.value!r}",
                    error_code=self.status.value,
                )
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Reservation {self.id!r} not ready within {timeout_s}s "
                    f"(status={self.status.value!r})"
                )
            time.sleep(poll_interval_s)

    def wait_until_released(
        self,
        *,
        poll_interval_s: float = DEFAULT_READY_POLL_INTERVAL_S,
        timeout_s: float | None = None,
    ) -> None:
        """
        Poll until ``status`` is :attr:`ReservationStatus.RELEASED`.

        Release is asynchronous on the server — call this after :meth:`release`
        if you need to confirm compute is reclaimed and quota consumption has stopped.

        Parameters:
            poll_interval_s: Seconds between status polls.
            timeout_s: Optional timeout; raises :exc:`TimeoutError` when exceeded.

        Raises:
            ResourceReservationError: If the reservation enters ``failed`` or ``failing``.
            TimeoutError: When ``timeout_s`` is exceeded.
        """
        deadline = None if timeout_s is None else time.monotonic() + timeout_s
        while True:
            self.refresh()
            if self.status is ReservationStatus.RELEASED:
                return
            if self.status in self._RELEASE_FAILURE_STATUSES:
                raise ResourceReservationError(
                    f"Reservation {self.id!r} ended with status {self.status.value!r}",
                    error_code=self.status.value,
                )
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Reservation {self.id!r} not released within {timeout_s}s "
                    f"(status={self.status.value!r})"
                )
            time.sleep(poll_interval_s)

    def start_auto_renew(
        self, *, max_idle_seconds: float = DEFAULT_MAX_IDLE_SECONDS
    ) -> None:
        """
        Renew the lease in a background thread until :meth:`stop_auto_renew` is called,
        :meth:`release` is called, or ``max_idle_seconds`` of consecutive idle time
        elapses.

        :meth:`create` calls this automatically. Reaching ``max_idle_seconds`` stops
        renewal but does not release the reservation. The idle timer restarts each time
        a job finishes (when using :meth:`Mesh.run`, :meth:`Simulation.run`, or
        :func:`keep_reservation_alive`).

        Parameters:
            max_idle_seconds: Maximum consecutive idle time between jobs for automatic
                renewal.
        """
        _get_current_client()._acquire_auto_renew_lease_keeper(
            self.id,
            max_idle_seconds=max_idle_seconds,
        )

    def stop_auto_renew(self) -> None:
        """Stop idle lease renewal started by :meth:`create` or :meth:`start_auto_renew`."""
        _get_current_client()._release_auto_renew_lease_keeper(self.id)


def resolve_resource_reservation_id(
    resource_reservation: ResourceReservation | str | None,
) -> str | None:
    """Return the reservation id from an explicit reservation or id string."""
    if resource_reservation is None:
        return None
    if isinstance(resource_reservation, str):
        return resource_reservation
    return resource_reservation.id


def build_start_job_request(
    resource_reservation: ResourceReservation | str | None,
) -> rawapi.StartJobRequest:
    """Build a start-job request body, optionally attaching a resource reservation."""
    rid = resolve_resource_reservation_id(resource_reservation)
    if rid is None:
        return rawapi.StartJobRequest()
    return rawapi.StartJobRequest(
        resourceReservationId=rid,
    )


@contextmanager
def keep_reservation_alive(
    resource_reservation: ResourceReservation | str | None,
) -> Generator[None, None, None]:
    """
    Keep a reservation lease alive during a blocking operation.

    Acquires job-scoped renewal for *resource_reservation*, pausing the idle timer until
    the context exits, then resets the idle timer. Use when calling
    :meth:`GeometryBuilder.start`, :meth:`Mesh.start`, or :meth:`Simulation.start`
    and polling with :meth:`~allsolve.job.JobMixin.is_running` yourself instead of
    :meth:`GeometryBuilder.run`, :meth:`Mesh.run`, or :meth:`Simulation.run`.

    If *resource_reservation* is ``None``, this context manager is a no-op.
    """
    rid = resolve_resource_reservation_id(resource_reservation)
    if rid is None:
        yield
        return

    client = _get_current_client()
    client._acquire_job_lease_keeper(rid)
    try:
        yield
    finally:
        client._release_job_lease_keeper(rid)
