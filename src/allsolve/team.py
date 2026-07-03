# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

import allsolve_rawapi as rawapi
from .api import get_api, get_auth


def get_teams() -> list[rawapi.Team]:
    """
    Get teams available to the API user.

    Returns teams the API user is a member of that have active team credits.
    Use this to discover valid ``team_id`` values for :meth:`~allsolve.Project.create`
    and :meth:`~allsolve.ResourceReservation.create` when team credits enforcement
    is active and the user belongs to more than one team.

    Returns:
        Teams the API user can assign projects to.
    """
    with get_api() as api:
        return api.get_teams(authorization=get_auth()).teams
