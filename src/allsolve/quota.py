# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

import allsolve_rawapi as rawapi
from .api import get_api, get_auth


def get_quota() -> rawapi.OrganizationQuota:
    """
    Get the organization's quota information.

    Returns the current quota status including core hours,
    used core seconds, and concurrent core limits.
    """
    with get_api() as api:
        return api.get_organization_quota(
            authorization=get_auth(),
        )
