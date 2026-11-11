# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from enum import Enum
from typing import TYPE_CHECKING, List, TextIO
import sys
import time
import warnings
import allsolve_rawapi as rawapi
from .api import get_api, get_auth
from .resource_reservation import keep_reservation_alive
from .util import JobError

if TYPE_CHECKING:
    from ._job_mixin import JobMixin
    from .mesh import Mesh
    from .resource_reservation import ResourceReservation
    from .simulation import Simulation

LOG_MAX_LIMIT = 25000
MAX_LOG_REQUESTS_WHILE_RUNNING = 10
DEFAULT_DELAY_S = 1
MAX_JOB_IDS_PER_REQUEST = 10_000


def _dedupe_job_ids(job_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for job_id in job_ids:
        if job_id not in seen:
            seen.add(job_id)
            result.append(job_id)
    return result


def _chunk_list(items: list[str], chunk_size: int) -> list[list[str]]:
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


class OnError(Enum):
    """Controls error handling after a job completes.

    Used with the ``on_error`` parameter of :meth:`GeometryBuilder.build`,
    :meth:`Mesh.run`, :meth:`MeshInstance.run`, :meth:`Simulation.run`, and
    :meth:`Project.copy`.

    Example:
    ```python
    geometry_builder.build(on_error=allsolve.OnError.STRICT)
    mesh.run(on_error=allsolve.OnError.STRICT)
    sim.run(on_error=allsolve.OnError.STRICT)
    ```
    """

    IGNORE = "ignore"
    """Never raise on job failure. Use :meth:`get_status` to inspect the result manually."""

    RAISE = "raise"
    """Raise :exc:`JobError` on hard failures, but tolerate partial or non-fatal outcomes.

    What counts as tolerable depends on the entity:

    - **Geometry** and **project copy**: nothing is tolerated — only ``SUCCESS`` is accepted.
    - **Mesh**: ``PARTIAL_SUCCESS`` is tolerated (low-quality mesh, may still be usable in some cases).
    - **Simulation**: ``PARTIAL_SUCCESS`` and ``ABORTED`` are tolerated
      (partial results may still be available).
    """

    STRICT = "strict"
    """Raise :exc:`JobError` unless the job status is exactly ``SUCCESS``."""


class Job:
    """
    Job for a project.

    Jobs are created when a geometry or a mesh is processed, or when a simulation is run.
    """

    # Job status constants
    SUCCESS = rawapi.JobStatusType.SUCCESS
    RUNNING = rawapi.JobStatusType.RUNNING
    ABORTED = rawapi.JobStatusType.ABORTED
    ABORTING = rawapi.JobStatusType.ABORTING
    ERROR = rawapi.JobStatusType.ERROR
    FAILING = rawapi.JobStatusType.FAILING
    PROCESSING_OUTPUT = rawapi.JobStatusType.PROCESSING_OUTPUT
    QUEUED = rawapi.JobStatusType.QUEUED
    SUBMITTED = rawapi.JobStatusType.SUBMITTED
    PARTIAL_SUCCESS = rawapi.JobStatusType.PARTIAL_SUCCESS
    STARTING = rawapi.JobStatusType.STARTING
    NOT_STARTED = None

    @classmethod
    def refresh_statuses(
        cls,
        jobs: Iterable[Job],
        *,
        delay_s: float = 0,
    ) -> None:
        """
        Refresh cached status on multiple :class:`Job` instances.

        Prefer this over calling :meth:`refresh_status` on each job when polling
        several jobs in the same loop iteration.

        Jobs whose IDs are omitted from the server response keep their previous
        :attr:`_job_status` (or :attr:`NOT_STARTED` via :meth:`get_status` if never
        refreshed).
        """
        job_list = list(jobs)
        if not job_list:
            return
        if delay_s > 0:
            time.sleep(delay_s)

        by_project: dict[str, list[Job]] = defaultdict(list)
        for job in job_list:
            if job.id:
                by_project[job._project_id].append(job)

        for project_id, project_jobs in by_project.items():
            unique_ids = _dedupe_job_ids([j.id for j in project_jobs])
            statuses = cls._fetch_statuses(project_id, unique_ids)
            for job in project_jobs:
                if job.id in statuses:
                    job._job_status = statuses[job.id]

    def abort(self) -> None:
        with get_api() as api:
            api.abort_job(
                authorization=get_auth(),
                project_id=self._project_id,
                job_id=self._job_id,
                body={},
            )

    def __init__(self, project_id: str, job_id: str) -> None:
        """
        Initialize a Job instance.

        job_id: ID of the job to track
        project_id: ID of the project containing the job
        """
        self._job_id: str = job_id
        self._project_id: str = project_id
        self._job_status: rawapi.JobStatus | None = None
        self._deleted: bool = False
        self._log_events: List[rawapi.JobLogEvent] = []
        self._last_printed_event_index: int | None = None
        self._last_downloaded_event_id: int | None = None

    @property
    def id(self) -> str:
        """Get the job ID"""
        return self._job_id

    def _refresh(self) -> None:
        """Refresh the job status from the server"""
        if self._job_id is None:
            return

        with get_api() as api:
            job = api.get_job_status(
                authorization=get_auth(),
                project_id=self._project_id,
                job_id=self._job_id,
            )
            self._job_status = job

    def get_status(self) -> str | None:
        """
        Get the current status of the job.

        Returns:
            The status of the job.
        """
        job = self._job_status
        if job is None:
            return Job.NOT_STARTED

        return job.status

    def refresh_status(self, delay_s: float = DEFAULT_DELAY_S) -> str | None:
        """
        Refresh the status of the job from the server.

        Parameters:
            delay_s: Optional time to wait before refreshing the status

        Returns:
            The status of the job.
        """
        if delay_s > 0:
            time.sleep(delay_s)
        self._refresh()

        job = self._job_status
        if job is None:
            return Job.NOT_STARTED

        return job.status

    def is_running(self, refresh_delay_s: float | None = None) -> bool:
        """
        Check if the job is still running.

        Without ``refresh_delay_s`` this returns the last known status and does
        not ask the server. To poll in a loop, pass ``refresh_delay_s``.

        Parameters:
            refresh_delay_s: Wait this many seconds, then refresh the status
                from the server before checking it.

        Returns:
            True if the job is still running, False otherwise.
        """
        if refresh_delay_s is None:
            status = self.get_status()
        else:
            status = self.refresh_status(delay_s=refresh_delay_s)

        return status not in (
            Job.SUCCESS,
            Job.ERROR,
            Job.ABORTED,
            Job.PARTIAL_SUCCESS,
        )

    def _get_logs(
        self,
        before_id: int | None = None,
        after_id: int | None = None,
        limit: int = 100,
    ) -> List[rawapi.JobLogEvent]:
        """
        Get log events from the server

        Parameters:
            before_id: Optional event ID to get logs before
            after_id: Optional event ID to get logs after
            limit: Optional maximum number of logs to retrieve

        Returns:
            A list of log events.
        """
        if limit > LOG_MAX_LIMIT:
            limit = LOG_MAX_LIMIT

        with get_api() as api:
            return api.get_job_logs(
                authorization=get_auth(),
                project_id=self._project_id,
                job_id=self._job_id,
                before_id=before_id,
                after_id=after_id,
                limit=limit,
            )

    def get_logs(self, limit: int = 100) -> List[str]:
        """
        Download new log events and return all log messages downloaded so far.

        Parameters:
            limit: Optional maximum number of logs to retrieve

        Returns:
            A list of log messages.
        """
        if limit > LOG_MAX_LIMIT:
            limit = LOG_MAX_LIMIT

        last_id = self._last_downloaded_event_id
        events = self._get_logs(after_id=last_id, limit=limit)
        if last_id is not None:
            # The backend returns only events after after_id. If it did not,
            # the uncapped loop in print_new_loglines would never end for a
            # finished job.
            events = [event for event in events if event.id > last_id]

        if len(events) > 0:
            self._last_downloaded_event_id = events[-1].id
            self._log_events.extend(events)

        return [log.message for log in self._log_events]

    def print_new_loglines(
        self, file: TextIO = sys.stdout, limit: int | None = None
    ) -> None:
        """
        Print new log lines to the specified output

        Parameters:
            file: Optional file to print the logs to.
            limit: Optional maximum number of new log lines to print.
                If None, print all new log lines. While the job is running,
                one call prints at most the lines of a few requests.
        """
        max_requests = MAX_LOG_REQUESTS_WHILE_RUNNING if self.is_running() else None
        self._print_new_loglines(file, limit, max_requests)

    def _print_new_loglines(
        self, file: TextIO, limit: int | None, max_requests: int | None
    ) -> None:
        requests = 0
        remaining = limit
        while True:
            start_index = 0
            if self._last_printed_event_index is not None:
                start_index = self._last_printed_event_index + 1

            unprinted = self._log_events[start_index:]
            if remaining is not None:
                unprinted = unprinted[: max(remaining, 0)]
                remaining -= len(unprinted)

            for event in unprinted:
                print(event.message, file=file)

            self._last_printed_event_index = start_index + len(unprinted) - 1

            if remaining is not None and remaining <= 0:
                break
            if max_requests is not None and requests >= max_requests:
                break
            requests += 1

            previous_count = len(self._log_events)
            self.get_logs(
                limit=LOG_MAX_LIMIT if remaining is None else max(remaining, 100)
            )
            if len(self._log_events) == previous_count:
                break

    def get_status_reason(self) -> str | None:
        """
        Get the reason for the current job status, if available

        Returns:
            The reason for the current job status, if available.
        """
        job = self._job_status
        if job is None:
            return ""

        return job.status_reason

    def __str__(self) -> str:
        return f"Job(id={self.id})"

    @classmethod
    def _fetch_statuses(
        cls, project_id: str, job_ids: list[str]
    ) -> dict[str, rawapi.JobStatus]:
        unique_ids = _dedupe_job_ids(job_ids)
        if not unique_ids:
            return {}

        result: dict[str, rawapi.JobStatus] = {}
        with get_api() as api:
            for chunk in _chunk_list(unique_ids, MAX_JOB_IDS_PER_REQUEST):
                response = api.get_job_statuses(
                    authorization=get_auth(),
                    project_id=project_id,
                    get_job_statuses_request=rawapi.GetJobStatusesRequest(jobIds=chunk),
                )
                for status in response.statuses:
                    result[status.job_id] = status
        return result


def refresh_statuses(
    items: Iterable[JobMixin | Job],
    *,
    delay_s: float = 0,
) -> None:
    """
    Refresh the status of many simulations, meshes, mesh instances or jobs at once.

    One request for each project gets the status of all items that are running.
    Items that are not running are skipped. After the call, ``get_status()`` and
    ``is_running()`` (without ``refresh_delay_s``) return the new status.

    Use this in your own polling loop, for example to write the logs of each item
    to a different file. To start and wait without your own loop, use
    :func:`run_meshes` or :func:`run_simulations`.

    Example:
    ```python
    for sim in sims:
        sim.start()
    while any(sim.is_running() for sim in sims):
        allsolve.refresh_statuses(sims, delay_s=5)
        for sim in sims:
            sim.print_new_loglines(file=log_files[sim.name])
    ```

    Parameters:
        items: Simulations, meshes, mesh instances or jobs, in one or more projects.
        delay_s: Wait this many seconds before the request.
    """
    jobs: list[Job] = []
    for item in items:
        job = item if isinstance(item, Job) else item._get_job()
        if job is not None and job.id and item.is_running():
            jobs.append(job)
    if not jobs:
        return
    if delay_s > 0:
        time.sleep(delay_s)

    by_project: dict[str, list[Job]] = defaultdict(list)
    for job in jobs:
        by_project[job._project_id].append(job)

    for project_id, project_jobs in by_project.items():
        statuses = Job._fetch_statuses(project_id, [job.id for job in project_jobs])
        for job in project_jobs:
            if job.id in statuses:
                job._job_status = statuses[job.id]
            else:
                job._refresh()


def run_meshes(
    meshes: Iterable[Mesh],
    *,
    include_overrides: bool = False,
    refresh_delay_s: float = 5,
    on_error: OnError = OnError.IGNORE,
    print_logs: bool = False,
    print_status: bool = False,
    resource_reservation: ResourceReservation | str | None = None,
) -> None:
    """
    Process many meshes at the same time and return when all of them are complete.

    All meshes are started first. Then one request for each project gets the
    status of all running meshes, until all of them are complete. If an instance
    fails to start, the other instances are still started and processed, and a
    :exc:`JobError` that names the instance is raised at the end, whatever
    ``on_error`` is. If no instance starts, the first start error is raised at once.

    Example:
    ```python
    allsolve.run_meshes([mesh_a, mesh_b], include_overrides=True, on_error=allsolve.OnError.STRICT)
    ```

    Parameters:
        meshes: The meshes to process.
        include_overrides: If True, also process all variable-override instances of
            each mesh. A simulation that sweeps variable overrides needs them. If
            False, process only the default instance, as :meth:`Mesh.run` does.
        refresh_delay_s: Delay in seconds between status checks.
        on_error: Controls error handling after all jobs complete.
            ``OnError.IGNORE`` (default) — never raises for a job status; use
            ``get_status()`` to check. A start error still raises (see above).
            ``OnError.RAISE`` — raises :exc:`JobError` unless the status of each
            instance is ``SUCCESS`` or ``PARTIAL_SUCCESS``.
            ``OnError.STRICT`` — raises :exc:`JobError` unless the status of each
            instance is exactly ``SUCCESS``.
            The error names each instance that failed.
        print_logs: If True, print the logs of all instances to the console.
        print_status: If True, print the status of an instance when it changes.
        resource_reservation: Optional reservation for the jobs
            (:class:`~allsolve.resource_reservation.ResourceReservation` or id
            string). Renews the reservation lease for the full duration of this call.
    """
    mesh_list = list(meshes)
    entries: list[tuple[str, JobMixin]] = []
    start_errors: list[tuple[str, Exception]] = []
    started_meshes = []
    with keep_reservation_alive(resource_reservation):
        for mesh in mesh_list:
            entry_count = len(entries)
            _start_entry(
                entries,
                start_errors,
                f"mesh '{mesh.name}'",
                mesh,
                lambda: mesh.start(resource_reservation=resource_reservation),
            )
            if include_overrides:
                try:
                    overrides = mesh.get_overrides()
                except Exception as e:
                    _add_start_error(
                        start_errors, f"mesh '{mesh.name}' overrides", e, stacklevel=3
                    )
                    overrides = []
                for instance in overrides:
                    _start_entry(
                        entries,
                        start_errors,
                        f"mesh '{mesh.name}' instance {instance.id}",
                        instance,
                        lambda: instance.start(
                            resource_reservation=resource_reservation
                        ),
                    )
            if len(entries) > entry_count:
                started_meshes.append(mesh)
        _raise_if_none_started(entries, start_errors)
        _wait_for_entries(entries, refresh_delay_s, print_logs, print_status)
        for mesh in started_meshes:
            mesh.refresh()
    _raise_on_failed_entries(
        "Meshing",
        entries,
        start_errors,
        on_error,
        (Job.SUCCESS, Job.PARTIAL_SUCCESS),
    )


def run_simulations(
    simulations: Iterable[Simulation],
    *,
    refresh_delay_s: float = 5,
    on_error: OnError = OnError.IGNORE,
    print_logs: bool = False,
    print_status: bool = False,
    resource_reservation: ResourceReservation | str | None = None,
) -> None:
    """
    Run many simulations at the same time and return when all of them are complete.

    All simulations are started first. Then one request for each project gets the
    status of all running simulations, until all of them are complete. If a
    simulation fails to start, the other simulations are still started and run, and
    a :exc:`JobError` that names the simulation is raised at the end, whatever
    ``on_error`` is. If no simulation starts, the first start error is raised at once.

    Example:
    ```python
    allsolve.run_simulations([sim_tx, sim_rx], on_error=allsolve.OnError.STRICT)
    ```

    Parameters:
        simulations: The simulations to run.
        refresh_delay_s: Delay in seconds between status checks.
        on_error: Controls error handling after all jobs complete.
            ``OnError.IGNORE`` (default) — never raises for a job status; use
            ``get_status()`` to check. A start error still raises (see above).
            ``OnError.RAISE`` — raises :exc:`JobError` unless the status of each
            simulation is ``SUCCESS``, ``PARTIAL_SUCCESS`` or ``ABORTED``.
            ``OnError.STRICT`` — raises :exc:`JobError` unless the status of each
            simulation is exactly ``SUCCESS``.
            The error names each simulation that failed.
        print_logs: If True, print the logs of all simulations to the console.
        print_status: If True, print the status of a simulation when it changes.
        resource_reservation: Optional reservation for the jobs
            (:class:`~allsolve.resource_reservation.ResourceReservation` or id
            string). Renews the reservation lease for the full duration of this call.
    """
    entries: list[tuple[str, JobMixin]] = []
    start_errors: list[tuple[str, Exception]] = []
    with keep_reservation_alive(resource_reservation):
        for simulation in simulations:
            _start_entry(
                entries,
                start_errors,
                f"simulation '{simulation.name}'",
                simulation,
                lambda: simulation.start(resource_reservation=resource_reservation),
            )
        _raise_if_none_started(entries, start_errors)
        _wait_for_entries(entries, refresh_delay_s, print_logs, print_status)
    _raise_on_failed_entries(
        "Simulations",
        entries,
        start_errors,
        on_error,
        (Job.SUCCESS, Job.PARTIAL_SUCCESS, Job.ABORTED),
    )


def _status_name(status: str | None) -> str:
    if status is None:
        return "not started"
    return str(getattr(status, "value", status))


def _start_entry(
    entries: list[tuple[str, JobMixin]],
    start_errors: list[tuple[str, Exception]],
    label: str,
    item: JobMixin,
    start: Callable[[], object],
    warn: bool = True,
) -> None:
    job = item._get_job()
    try:
        start()
    except Exception as e:
        if item._get_job() is job:
            _add_start_error(start_errors, label, e, warn=warn)
    if item._get_job() is not job:
        entries.append((label, item))


def _add_start_error(
    start_errors: list[tuple[str, Exception]],
    label: str,
    error: Exception,
    stacklevel: int = 4,
    warn: bool = True,
) -> None:
    start_errors.append((label, error))
    if warn:
        warnings.warn(f"Could not start {label}: {error!r}", stacklevel=stacklevel)


def _raise_if_none_started(
    entries: list[tuple[str, JobMixin]], start_errors: list[tuple[str, Exception]]
) -> None:
    if start_errors and not entries:
        raise start_errors[0][1]


def _print_new_loglines_once(item: JobMixin) -> None:
    job = item._get_job()
    if job is None:
        return
    job._print_new_loglines(sys.stdout, None, 1 if job.is_running() else None)


def _wait_for_entries(
    entries: list[tuple[str, JobMixin]],
    refresh_delay_s: float,
    print_logs: bool,
    print_status: bool,
) -> None:
    active = list(entries)
    printed: dict[int, str | None] = {}
    while True:
        for label, item in active:
            if print_logs:
                _print_new_loglines_once(item)
            if print_status:
                status = item.get_status()
                if printed.get(id(item), "") != status:
                    print(f"{label}: {_status_name(status)}")
                    printed[id(item)] = status
        active = [(label, item) for label, item in active if item.is_running()]
        if not active:
            return
        refresh_statuses([item for _, item in active], delay_s=refresh_delay_s)


def _raise_on_failed_entries(
    kind: str,
    entries: list[tuple[str, JobMixin]],
    start_errors: list[tuple[str, Exception]],
    on_error: OnError,
    accepted_on_raise: tuple[str, ...],
) -> None:
    failed: list[tuple[str, JobMixin]] = []
    if on_error is not OnError.IGNORE:
        accepted = (Job.SUCCESS,) if on_error is OnError.STRICT else accepted_on_raise
        failed = [
            (label, item)
            for label, item in entries
            if item.get_status() not in accepted
        ]
    if not failed and not start_errors:
        return

    details = [f"{label}: not started ({error!r})" for label, error in start_errors]
    for label, item in failed:
        job = item._get_job()
        reason = job.get_status_reason() if job is not None else None
        detail = f"{label}: {_status_name(item.get_status())}"
        details.append(f"{detail} ({reason})" if reason else detail)
    status: str | None = Job.NOT_STARTED
    status_reason = None
    if failed:
        status = failed[0][1].get_status()
        first_job = failed[0][1]._get_job()
        status_reason = first_job.get_status_reason() if first_job else None
    raise JobError(
        f"{kind} failed: " + ", ".join(details),
        status=status,
        status_reason=status_reason,
    ) from (start_errors[0][1] if start_errors else None)
