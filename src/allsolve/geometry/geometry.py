# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
import sys
from typing import List, TextIO
from typing_extensions import Self

from allsolve.geometry.geometry_element import GDS2ImportConfig, GeometryElement
from ..util import deprecated, prevent_deleted
from ..job_mixin import JobMixin
import allsolve_rawapi as rawapi
from allsolve_rawapi.exceptions import ServiceException
from ..api import get_api, get_auth, check_for_project_api_key
from ..file import upload_parts
from ..job import Job
import pathlib


class Geometry(JobMixin):
    """
    Geometry for a project.
    """

    @classmethod
    @deprecated("Use geometry pipeline version V2 for new projects")
    def create(
        cls,
        geometry_imports: List[GeometryElement.ImportGeometry],
        project_id: str,
    ) -> Self:
        """
        Create a new geometry element in the given project.
        Uploads the geometry file to the project.

        .. deprecated::
            Use geometry pipeline version V2 for new projects.

        Parameters:
            geometry_imports: A list of geometry import objects.
                Currently only one geometry import per project is supported.
            project_id: The id of the project where the new geometry element should be created.

        Returns:
            The created geometry element.
        """
        project_id = check_for_project_api_key(project_id)

        if len(geometry_imports) == 0:
            raise ValueError("At least one geometry import is required")

        if len(geometry_imports) > 1:
            raise ValueError("Only one geometry import is supported at the moment")

        geometry_import = geometry_imports[0]

        geometry = None
        geometry_element = None

        with get_api() as api:
            new_element_payload = rawapi.NewGeometryElement(
                name=geometry_import.file_name,
                elem=rawapi.NewGeoFileImport(
                    type=geometry_import.file_type,
                    name=geometry_import.file_name,
                    size=geometry_import.file_size,
                ),
            )

            geometry_element = api.create_geometry_element(
                authorization=get_auth(),
                project_id=project_id,
                new_geometry_element=new_element_payload,
            )
            geometry = cls(project_id, geometry_import.filepath, geometry_element)
        geometry._upload()

        if geometry_import.file_type == rawapi.GeometryFileType.GDS2:

            # Wait for layer generation job to finish
            with get_api() as api:
                response = api.get_geometry_elements(
                    authorization=get_auth(),
                    project_id=project_id,
                )
                if response is None or len(response) == 0:
                    raise ValueError("No geometry elements found")
                job_id = response[0].job_id

            if job_id is not None:
                job = Job(project_id, job_id)
                while job.is_running(refresh_delay_s=1):
                    pass
                if job.get_status() != Job.SUCCESS:
                    raise ValueError("Failed to read layers from GDSII file")

            if geometry_import.config is not None and isinstance(
                geometry_import.config, GDS2ImportConfig
            ):
                # Update GDS2 config after layer generation job is finished
                if geometry_element.elem is not None:
                    geometry_element.elem.gds2_config = (
                        geometry_import.config._to_rawapi()
                    )
                    geometry_element.elem.unit = geometry_import.config.unit
                    with get_api() as api:
                        api.update_geometry_element(
                            authorization=get_auth(),
                            project_id=project_id,
                            geometry_element=geometry_element,
                        )

        return geometry

    @classmethod
    def get(cls, project_id: str) -> List[Self]:
        """
        Get list of Geometry objects in the given project.
        Currently only one Geometry per project is supported.

        Parameters:
            project_id: The ID of the project. Can be omitted if project API key is used.

        Returns:
            A list of Geometry objects.
        """
        project_id = check_for_project_api_key(project_id)

        try:
            with get_api() as api:
                response = api.get_geometry_elements(
                    authorization=get_auth(),
                    project_id=project_id,
                )
                if response is None:
                    return []
                return [cls(project_id, None, geometry) for geometry in response]
        except ServiceException as e:
            if "multiple geometry elements found" in str(e.body):
                raise ValueError(
                    "This project contains multiple geometry elements, which is not supported "
                    "by GeometryPipelineVersion.V1 in the SDK. "
                    "Please use GeometryPipelineVersion.V2 for projects with multiple geometry elements."
                ) from None
            raise

    @classmethod
    def delete_geometry(cls: type[Self], project_id: str) -> None:
        """
        Delete the geometry from the project.
        """
        project_id = check_for_project_api_key(project_id)
        with get_api() as api:
            api.delete_geometry_elements(
                authorization=get_auth(),
                project_id=project_id,
            )

    def __init__(
        self, project_id: str, filepath: str | None, geometry: rawapi.GeometryElement
    ) -> None:
        self._project_id: str = project_id
        self._filepath: str | None = filepath
        self._geometry: rawapi.GeometryElement = geometry
        self._deleted: bool = False
        self._job: Job | None = None

    @property
    @prevent_deleted
    def id(self) -> str:
        """Get the ID of the geometry element."""
        return self._geometry.id

    @property
    @prevent_deleted
    def name(self) -> str:
        """Get the name of the geometry element."""
        return self._geometry.name

    @property
    @prevent_deleted
    def file_uploaded_at(self) -> datetime | None:
        """Get the time the geometry file was uploaded."""
        return self._geometry.file_uploaded_at

    @prevent_deleted
    @deprecated("Use geometry pipeline version V2 for new projects")
    def start(self) -> None:
        """
        Start processing the imported geometry file.

        .. deprecated::
            Use geometry pipeline version V2 for new projects.
        """
        project_id = check_for_project_api_key(self._project_id)

        with get_api() as api:
            response = api.start_processing_geometry(
                authorization=get_auth(),
                project_id=project_id,
                body={},
            )
            job_id = response.job_id
            self._job = Job(self._project_id, job_id)

    @prevent_deleted
    @deprecated("Use geometry pipeline version V2 for new projects")
    def run(self, print_logs: bool = False, refresh_delay_s: float = 1) -> None:
        """
        Processes the imported geometry file and returns when the processing is complete.

        .. deprecated::
            Use geometry pipeline version V2 for new projects.

        Parameters:
            print_logs: If True, print logs to the console.
            refresh_delay_s: Optional delay in seconds between checking the status of the job.
        """
        self.start()
        while self.is_running(refresh_delay_s=refresh_delay_s):
            if print_logs:
                self.print_new_loglines()
        if print_logs:
            self.print_new_loglines()

    @prevent_deleted
    def abort(self) -> None:
        """
        Abort the processing of the geometry file.
        """
        return super().abort()

    @prevent_deleted
    def get_status(self) -> str | None:
        """
        Get the status of the processing of the geometry file.

        Returns:
            The status of the processing of the geometry file.
        """
        return super().get_status()

    @prevent_deleted
    def is_running(self, refresh_delay_s: float | None = None) -> bool:
        """
        Check if the processing of the geometry file is running.

        Parameters:
            refresh_delay_s: Optional delay in seconds between checking the status of the job.

        Returns:
            True if the processing of the geometry file is running, False otherwise.
        """
        return super().is_running(refresh_delay_s)

    @prevent_deleted
    def refresh_status(self, delay_s: float = 1) -> str | None:
        """
        Refresh the status of the processing of the geometry file.

        Parameters:
            delay_s: Optional delay in seconds between checking the status of the job.

        Returns:
            The status of the processing of the geometry file.
        """
        return super().refresh_status(delay_s)

    @prevent_deleted
    def get_logs(self, limit: int = 100) -> List[str]:
        """
        Get the logs of the processing of the imported geometry file.

        Parameters:
            limit: Optional maximum number of logs to return.

        Returns:
            A list of log messages.
        """
        return super().get_logs(limit)

    @prevent_deleted
    def print_new_loglines(self, file: TextIO = sys.stdout, limit: int = 100) -> None:
        """
        Print the new log lines of the processing of the imported geometry file.

        Parameters:
            file: Optional file to print the logs to.
            limit: Optional maximum number of logs to print.
        """
        return super().print_new_loglines(file, limit)

    @prevent_deleted
    def delete(self) -> None:
        """
        Delete the geometry from the project.
        """
        project_id = check_for_project_api_key(self._project_id)
        self.__class__.delete_geometry(project_id)
        self._deleted = True

    @prevent_deleted
    def _upload(self) -> rawapi.InputFile:
        """
        Upload the geometry file to the project.
        Note: This is called automatically when a geometry is created.
        """
        if self._filepath is None:
            raise ValueError("Geometry file path is not set")

        with get_api() as api:
            url_info = api.get_file_upload_urls(
                authorization=get_auth(), project_id=self._project_id, file_id=self.id
            )

        file = pathlib.Path(self._filepath)
        if not file.is_file():
            raise FileNotFoundError(f"Geometry file not found: {self._filepath}")

        with open(file, "rb") as f:
            completion = upload_parts(f, url_info)

        with get_api() as api:
            response = api.mark_file_uploaded(
                authorization=get_auth(),
                project_id=self._project_id,
                file_id=self.id,
                file_upload_completion=completion,
            )
            self._geometry.file_uploaded_at = response.file_uploaded_at

        return response

    def __str__(self) -> str:
        status = self.get_status()
        return (
            f"Geometry(name={self.name}, id={self.id}, "
            f"file_uploaded_at={self.file_uploaded_at}, job_status={status})"
        )
