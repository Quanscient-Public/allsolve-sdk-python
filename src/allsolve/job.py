# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import List, TextIO
import sys
import time
import allsolve_rawapi as rawapi
from .api import get_api, get_auth

LOG_MAX_LIMIT = 25000
DEFAULT_DELAY_S = 1


class OnError(Enum):
    """Controls error handling after a job completes.

    Used with the ``on_error`` parameter of :meth:`GeometryBuilder.build`,
    :meth:`Mesh.run`, :meth:`MeshInstance.run`, and :meth:`Simulation.run`.

    Example::

        geometry_builder.build(on_error=allsolve.OnError.STRICT)
        mesh.run(on_error=allsolve.OnError.STRICT)
        sim.run(on_error=allsolve.OnError.STRICT)
    """

    IGNORE = "ignore"
    """Never raise on job failure. Use :meth:`get_status` to inspect the result manually."""

    RAISE = "raise"
    """Raise :exc:`JobError` on hard failures, but tolerate partial or non-fatal outcomes.

    What counts as tolerable depends on the entity:

    - **Geometry**: nothing is tolerated — only ``SUCCESS`` is accepted.
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

        Parameters:
            refresh_delay_s: Optional time to wait before checking the status

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
        self, before_id=None, after_id=None, limit=100
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
        Get log messages, starting from where we left off previously

        Parameters:
            limit: Optional maximum number of logs to retrieve

        Returns:
            A list of log messages.
        """
        if limit > LOG_MAX_LIMIT:
            limit = LOG_MAX_LIMIT

        events = self._get_logs(
            after_id=self._last_downloaded_event_id,
            limit=limit,
        )

        if len(events) > 0:
            self._last_downloaded_event_id = events[-1].id
            self._log_events = self._log_events + events

        return [log.message for log in self._log_events]

    def print_new_loglines(self, file: TextIO = sys.stdout, limit: int = 100) -> None:
        """
        Print new log lines to the specified output

        Parameters:
            file: Optional file to print the logs to.
            limit: Optional maximum number of logs to retrieve and print.
        """
        if limit > LOG_MAX_LIMIT:
            limit = LOG_MAX_LIMIT

        messages = self.get_logs(limit=limit)

        start_index = 0
        if self._last_printed_event_index is not None:
            start_index = self._last_printed_event_index + 1

        for message in messages[start_index:]:
            print(message, file=file)

        self._last_printed_event_index = len(messages) - 1

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
