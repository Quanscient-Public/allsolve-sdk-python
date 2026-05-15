# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

"""HTTP transfer defaults: timeouts and URL validation for uploads/downloads."""

from __future__ import annotations

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
