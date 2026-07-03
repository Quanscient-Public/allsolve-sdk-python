# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

import allsolve_rawapi as rawapi
from .api import get_api, get_auth


def get_quota() -> rawapi.OrganizationQuota:
    """
    Get the organization's quota information.

    Returns the current quota status including credits,
    used credits, concurrent core limits, whether team credits
    enforcement is active (``team_quota_enforcement_active``), and
    per-team quota for teams the API user belongs to (``teams``).
    """
    with get_api() as api:
        return api.get_organization_quota(
            authorization=get_auth(),
        )
