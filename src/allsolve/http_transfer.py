# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

"""HTTP transfer defaults: timeouts and URL validation for uploads/downloads."""

from __future__ import annotations

from typing import BinaryIO

from urllib.parse import urlparse

CONNECT_TIMEOUT_S = 30
TRANSFER_TIMEOUT_S = 600


def validate_url_scheme(url: str, allow_insecure_http: bool) -> None:
    """Reject non-HTTPS URLs except localhost or when *allow_insecure_http* is set."""
    parsed = urlparse(url)
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
        f"Refusing to follow URL with scheme {scheme!r}. "
        "Expected HTTPS. If using a local development server, "
        "pass allow_insecure_http=True when creating the Client."
    )


def stream_response_to_file(
    response,
    file_obj: BinaryIO,
    *,
    chunk_size: int = 8192,
) -> int:
    """Stream an HTTP response body to *file_obj*.

    When the response includes ``Content-Length``, verify that the full body
    was received. This catches interrupted downloads that end without error.
    """
    bytes_written = 0
    for chunk in response.iter_content(chunk_size=chunk_size):
        if chunk:
            file_obj.write(chunk)
            bytes_written += len(chunk)

    content_length = response.headers.get("Content-Length")
    if content_length is not None:
        expected = int(content_length)
        if bytes_written != expected:
            raise OSError(
                f"Incomplete download: received {bytes_written} bytes, "
                f"expected {expected} bytes"
            )
    return bytes_written
