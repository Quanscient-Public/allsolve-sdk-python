# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from typing import TYPE_CHECKING, List

import allsolve_rawapi as rawapi
from typing_extensions import Self

from allsolve.api import check_for_project_api_key, get_api, get_auth
from allsolve.util import prevent_deleted

if TYPE_CHECKING:
    from allsolve.physics.physic import Physic

DEFAULT_PHYSICS_SET_NAME = "Physics 1"


class PhysicsSet:
    """
    PhysicsSet is for managing named physics sets in a project.

    Each project has a default physics set. Additional named sets can be created
    to hold alternative physics configurations. Use :meth:`add_physics` to
    create physics in a specific set.
    """

    @classmethod
    def create(
        cls,
        name: str,
        description: str | None = None,
        project_id: str | None = None,
    ) -> Self:
        """
        Create a new physics set.

        Args:
            name: The name of the physics set.
            description: Optional description of the physics set.
            project_id: The ID of the project.

        Returns:
            The created PhysicsSet.
        """
        project_id = check_for_project_api_key(project_id)

        with get_api() as api:
            physics_set = api.create_physics_set(
                authorization=get_auth(),
                project_id=project_id,
                new_physics_set=rawapi.NewPhysicsSet(
                    name=name,
                    description=description,
                ),
            )
        return cls(project_id, physics_set)

    @classmethod
    def get(cls, physics_set_id: str, project_id: str | None = None) -> Self:
        """
        Get a physics set by its ID.
        """
        project_id = check_for_project_api_key(project_id)
        with get_api() as api:
            physics_set = api.get_physics_set(
                authorization=get_auth(),
                project_id=project_id,
                physics_set_id=physics_set_id,
            )
        return cls(project_id, physics_set)

    @classmethod
    def get_all(cls, project_id: str | None = None) -> List[Self]:
        """
        Get all physics sets in a project.
        """
        project_id = check_for_project_api_key(project_id)
        with get_api() as api:
            physics_sets = api.get_physics_sets(
                authorization=get_auth(),
                project_id=project_id,
            )
            return [cls(project_id, physics_set) for physics_set in physics_sets]

    @classmethod
    def get_default(cls, project_id: str | None = None) -> Self:
        """
        Get the default physics set for a project.
        """
        for physics_set in cls.get_all(project_id=project_id):
            if physics_set.is_default:
                return physics_set
        raise ValueError("No default physics set found in project")

    @classmethod
    def copy_physics_set(
        cls,
        physics_set_id: str,
        name: str | None = None,
        project_id: str | None = None,
    ) -> Self:
        """
        Create a copy of a physics set.

        Args:
            physics_set_id: The ID of the physics set to copy.
            name: Optional name for the copied physics set.
            project_id: The ID of the project.

        Returns:
            The copied PhysicsSet.
        """
        project_id = check_for_project_api_key(project_id)

        copy_request = rawapi.CopyRequest(name=name) if name is not None else None
        with get_api() as api:
            physics_set = api.copy_physics_set(
                authorization=get_auth(),
                project_id=project_id,
                physics_set_id=physics_set_id,
                copy_request=copy_request,
            )
        return cls(project_id, physics_set)

    def __init__(self, project_id: str, physics_set: rawapi.PhysicsSet) -> None:
        self._project_id = project_id
        self._physics_set = physics_set
        self._deleted: bool = False
        self._uncommitted_update: rawapi.PhysicsSetUpdate | None = None

    @property
    @prevent_deleted
    def id(self) -> str:
        """Get the ID of the physics set."""
        return self._physics_set.id

    @property
    @prevent_deleted
    def name(self) -> str | None:
        """Get the name of the physics set."""
        if self._physics_set.name is not None:
            return self._physics_set.name
        if self.is_default:
            return DEFAULT_PHYSICS_SET_NAME
        return None

    @name.setter
    @prevent_deleted
    def name(self, name: str) -> None:
        """Set the name of the physics set."""
        if self.is_default:
            raise ValueError("Cannot rename the default physics set")
        self._current_uncommitted_update().name = name
        self._save()

    @property
    @prevent_deleted
    def description(self) -> str | None:
        """Get the description of the physics set."""
        return self._physics_set.description

    @description.setter
    @prevent_deleted
    def description(self, description: str | None) -> None:
        """Set the description of the physics set."""
        if self.is_default:
            raise ValueError("Cannot update the default physics set")
        self._current_uncommitted_update().description = description
        self._save()

    @property
    @prevent_deleted
    def is_default(self) -> bool:
        """Whether this is the project's default physics set."""
        return self._physics_set.is_default

    @prevent_deleted
    def add_physics(self, physic: "Physic") -> "Physic":
        """
        Add a physics definition to this physics set.

        Example::

            physics_set = project.create_physics_set(name="alt_physics")
            solid = physics_set.add_physics(
                allsolve.Physics.SolidMechanics(target=beam_region)
            )
        """
        from allsolve.physics.physic import Physic

        if not isinstance(physic, Physic):
            raise ValueError("physic must be a Physic instance")
        if self.is_default and self._physics_set.name is None:
            self._ensure_default_name()
        return physic._create_bound(
            project_id=self._project_id,
            physics_set_id=self.id,
        )

    @prevent_deleted
    def copy(self, name: str | None = None) -> Self:
        """Create a copy of this physics set."""
        return self.__class__.copy_physics_set(
            physics_set_id=self.id,
            name=name,
            project_id=self._project_id,
        )

    @prevent_deleted
    def delete(self) -> None:
        """Delete the physics set."""
        if self.is_default:
            raise ValueError("Cannot delete the default physics set")
        with get_api() as api:
            api.delete_physics_set(
                authorization=get_auth(),
                project_id=self._project_id,
                physics_set_id=self.id,
            )
        self._deleted = True

    @prevent_deleted
    def _ensure_default_name(self) -> None:
        """Persist :data:`DEFAULT_PHYSICS_SET_NAME` when the default set is first used."""
        project_id = check_for_project_api_key(self._project_id)

        with get_api() as api:
            api.update_physics_set(
                authorization=get_auth(),
                project_id=project_id,
                physics_set_id=self.id,
                physics_set_update=rawapi.PhysicsSetUpdate(
                    name=DEFAULT_PHYSICS_SET_NAME,
                    description=self._physics_set.description,
                ),
            )

            self._physics_set = api.get_physics_set(
                authorization=get_auth(),
                project_id=project_id,
                physics_set_id=self.id,
            )

    @prevent_deleted
    def _save(self) -> None:
        """Save changes made by setting properties."""
        if self._uncommitted_update is None:
            return

        project_id = check_for_project_api_key(self._project_id)
        physics_set_update = self._current_uncommitted_update()

        with get_api() as api:
            api.update_physics_set(
                authorization=get_auth(),
                project_id=project_id,
                physics_set_id=self.id,
                physics_set_update=physics_set_update,
            )

            self._uncommitted_update = None

            self._physics_set = api.get_physics_set(
                authorization=get_auth(),
                project_id=project_id,
                physics_set_id=self.id,
            )

    @prevent_deleted
    def _current_uncommitted_update(self) -> rawapi.PhysicsSetUpdate:
        """Get the current uncommitted update for the PhysicsSet."""
        if self._uncommitted_update is None:
            if self._physics_set.name is None:
                raise ValueError("Cannot update the default physics set")
            self._uncommitted_update = rawapi.PhysicsSetUpdate(
                name=self._physics_set.name,
                description=self._physics_set.description,
            )

        return self._uncommitted_update

    def __str__(self) -> str:
        return (
            f"PhysicsSet(name={self.name}, id={self.id}, is_default={self.is_default})"
        )


def resolve_physics_set_id(
    physics_set: PhysicsSet | str | None,
) -> str | None:
    """Return the physics set id from a PhysicsSet object or id string."""
    if physics_set is None:
        return None
    if isinstance(physics_set, str):
        return physics_set
    return physics_set.id
