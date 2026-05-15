# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

import io
import pathlib
from typing import BinaryIO

import allsolve_rawapi as rawapi

from .api import (
    check_for_project_api_key,
    get_allow_insecure_http,
    get_api,
    get_auth,
    get_http_session,
)
from .http_transfer import CONNECT_TIMEOUT_S, TRANSFER_TIMEOUT_S, validate_url_scheme


def create_file(
    filepath: pathlib.Path,
    size: int,
    project_id: str | None = None,
    simulation_id: str | None = None,
) -> rawapi.InputFile:
    project_id = check_for_project_api_key(project_id)

    with get_api() as api:
        return api.create_file(
            authorization=get_auth(),
            project_id=project_id,
            simulation_id=simulation_id,
            new_file_upload=rawapi.NewFileUpload(
                name=filepath.name,
                size=size,
            ),
        )


def upload_file(
    filepath: pathlib.Path,
    handle: rawapi.InputFile,
    project_id: str | None = None,
) -> None:
    project_id = check_for_project_api_key(project_id)

    with get_api() as api:
        url_info = api.get_file_upload_urls(
            authorization=get_auth(),
            project_id=project_id,
            file_id=handle.id,
        )

    with open(filepath, "rb") as f:
        completion = upload_parts(f, url_info)

    with get_api() as api:
        api.mark_file_uploaded(
            authorization=get_auth(),
            project_id=project_id,
            file_id=handle.id,
            file_upload_completion=completion,
        )


def upload_bytes(
    data: bytes, handle: rawapi.InputFile, project_id: str | None = None
) -> None:
    project_id = check_for_project_api_key(project_id)

    with get_api() as api:
        url_info = api.get_file_upload_urls(
            authorization=get_auth(),
            project_id=project_id,
            file_id=handle.id,
        )

    completion = upload_parts(io.BytesIO(data), url_info)

    with get_api() as api:
        api.mark_file_uploaded(
            authorization=get_auth(),
            project_id=project_id,
            file_id=handle.id,
            file_upload_completion=completion,
        )


def upload_parts(
    data: BinaryIO, info: rawapi.FileUploadUrls
) -> rawapi.FileUploadCompletion:
    completion = rawapi.FileUploadCompletion(parts=[])
    session = get_http_session()
    allow_insecure = get_allow_insecure_http()

    for _i, url in enumerate(info.upload_urls):
        validate_url_scheme(url, allow_insecure)
        r = session.put(
            url,
            data=data.read(info.max_part_size),
            timeout=(CONNECT_TIMEOUT_S, TRANSFER_TIMEOUT_S),
        )
        if r.status_code >= 400:
            r.raise_for_status()
        else:
            completion.parts.append(
                rawapi.FileUploadCompletedPart(eTag=r.headers["ETag"])
            )

    return completion


def delete_file(
    handle: rawapi.InputFile | rawapi.SimulationInputFile,
    project_id: str | None = None,
) -> None:
    """
    Delete an extra input file from the project.

    Parameters:
        handle: An ``InputFile`` returned by file creation helpers, or a
            ``SimulationInputFile`` of type ``extraInputFile`` returned by
            ``Simulation.get_input_files()``.
        project_id: The project ID. Can be omitted when using a project API key.

    Raises:
        TypeError: If *handle* is a ``SimulationInputFile`` whose type is not
            ``extraInputFile`` (output references cannot be deleted this way).
        ValueError: If *handle* is an ``extraInputFile`` link but has no
            ``source_extra_input_file_id``.
    """
    if isinstance(handle, rawapi.SimulationInputFile):
        if handle.type != rawapi.SimulationInputFileType.EXTRAINPUTFILE:
            raise TypeError(
                f"SimulationInputFile of type '{handle.type.value}' cannot be "
                f"deleted with delete_file(); only 'extraInputFile' links are "
                f"supported. Remove other types by updating the simulation's "
                f"input file list instead."
            )
        if not handle.source_extra_input_file_id:
            raise ValueError(
                "SimulationInputFile has type 'extraInputFile' but "
                "source_extra_input_file_id is not set."
            )
        file_id = handle.source_extra_input_file_id
    else:
        file_id = handle.id

    project_id = check_for_project_api_key(project_id)
    with get_api() as api:
        api.delete_file(
            authorization=get_auth(),
            project_id=project_id,
            file_id=file_id,
        )
