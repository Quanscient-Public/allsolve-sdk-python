# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import time
from base64 import b64decode
from typing import Any, Dict, List

_EXPIRY_TOLERANCE_S = 60


class AccessToken:
    def __init__(
        self,
        user_id: str,
        project_id: str | None,
        scopes: List[str],
        issued_at_unix: int,
        expires_in_seconds: int,
    ):
        self.user_id = user_id
        self.project_id = project_id
        self.scopes = scopes
        self.issued_at_unix = issued_at_unix
        self.expires_in_seconds = expires_in_seconds

    def __repr__(self) -> str:
        return (
            f"AccessToken(user_id={self.user_id!r}, "
            f"project_id={self.project_id!r}, "
            f"scopes={self.scopes!r}, "
            f"expires_in_seconds={self.expires_in_seconds})"
        )

    def __str__(self) -> str:
        return self.__repr__()


def parse_jwt_payload(token: str) -> Dict[str, Any]:
    base64_url = token.split(".")[1]
    base64_str = base64_url.replace("-", "+").replace("_", "/")

    padding = len(base64_str) % 4
    if padding:
        base64_str += "=" * (4 - padding)

    decoded = b64decode(base64_str)
    json_str = decoded.decode("utf-8")
    return json.loads(json_str)


def is_access_token_payload(payload: Any) -> bool:
    return (
        isinstance(payload, dict)
        and isinstance(payload.get("sub"), str)
        and isinstance(payload.get("exp"), (int, float))
        and isinstance(payload.get("iat"), (int, float))
        and isinstance(payload.get("scope"), str)
    )


def parse_access_token(token: str) -> AccessToken:
    payload = parse_jwt_payload(token)

    if not is_access_token_payload(payload):
        raise ValueError("Invalid access token")

    exp = int(payload["exp"])
    iat = int(payload["iat"])

    if exp < time.time() - _EXPIRY_TOLERANCE_S:
        raise ValueError(
            f"Access token has expired (exp={exp}). "
            "Check that your system clock is correct."
        )

    return AccessToken(
        issued_at_unix=iat,
        expires_in_seconds=exp - iat,
        scopes=payload["scope"].split(" "),
        user_id=payload["sub"],
        project_id=payload.get("projectId"),
    )
