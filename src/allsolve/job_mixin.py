# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from typing import List, TextIO
import sys

from .job import Job


class JobMixin:
    """
    Mixin class that provides common job-related methods for classes that manage a Job instance.

    Classes using this mixin should have a `_job` attribute of type `Job | None`.
    Subclasses can override `_get_job()` to customize job retrieval logic.
    """

    def _get_job(self) -> Job | None:
        """
        Get the job instance. Can be overridden by subclasses to customize job retrieval.

        Returns:
            The Job instance, or None if no job is available.
        """
        return getattr(self, "_job", None)

    def abort(self) -> None:
        """
        Abort the processing of the job.
        """
        job = self._get_job()
        if job is None:
            return
        job.abort()

    def get_status(self) -> str | None:
        """
        Get the status of the processing of the job.

        Returns:
            The status of the processing, or Job.NOT_STARTED if no job exists.
        """
        job = self._get_job()
        if job is None:
            return Job.NOT_STARTED

        return job.get_status()

    def is_running(self, refresh_delay_s: float | None = None) -> bool:
        """
        Check if the processing of the job is running.

        Parameters:
            refresh_delay_s: Optional delay in seconds between checking the status of the job.

        Returns:
            True if the processing is running, False otherwise.
        """
        job = self._get_job()
        if job is None:
            return False

        return job.is_running(refresh_delay_s)

    def refresh_status(self, delay_s: float = 1) -> str | None:
        """
        Refresh the status of the processing of the job.

        Parameters:
            delay_s: Optional delay in seconds between checking the status of the job.

        Returns:
            The status of the processing, or Job.NOT_STARTED if no job exists.
        """
        job = self._get_job()
        if job is None:
            return Job.NOT_STARTED

        return job.refresh_status(delay_s)

    def get_logs(self, limit: int = 100) -> List[str]:
        """
        Get the logs of the processing of the job.

        Parameters:
            limit: Optional maximum number of logs to return.

        Returns:
            A list of log messages, or an empty list if no job exists.
        """
        job = self._get_job()
        if job is None:
            return []

        return job.get_logs(limit=limit)

    def print_new_loglines(self, file: TextIO = sys.stdout, limit: int = 100) -> None:
        """
        Print the new log lines of the processing of the job.

        Parameters:
            file: Optional file to print the logs to.
            limit: Optional maximum number of logs to print.
        """
        job = self._get_job()
        if job is None:
            return

        job.print_new_loglines(file, limit)
