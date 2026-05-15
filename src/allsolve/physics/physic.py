# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from typing import List, TYPE_CHECKING, cast

import allsolve_rawapi as rawapi

from allsolve.api import check_for_project_api_key, get_api, get_auth
from allsolve.util import NotInitializedError, prevent_deleted
from .interaction import Interaction

if TYPE_CHECKING:
    from allsolve.region import Region


class Field:
    """
    Field is a class for managing fields in a physic.
    """

    def __init__(self, field_id: str, definition: str):
        self._field_id = field_id
        self._definition = definition

    @property
    def id(self) -> str:
        return self._field_id

    @property
    def definition(self) -> str:
        return self._definition


class Fields:
    """
    Named container for physics fields.

    Supports attribute access, dict-style access, indexing, and iteration::

        physics.fields.displacement        # by definition name
        physics.fields["displacement"]     # dict-style
        physics.fields[0]                  # by index
        for field in physics.fields: ...   # iteration
    """

    def __init__(self, fields: List[Field]):
        self._fields = fields
        self._by_definition: dict[str, Field] = {f.definition: f for f in fields}

    def __getattr__(self, name: str) -> Field:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._by_definition[name]
        except KeyError:
            raise AttributeError(
                f"No field '{name}'. Available: {list(self._by_definition)}"
            )

    def __getitem__(self, key: "str | int") -> Field:
        if isinstance(key, int):
            return self._fields[key]
        return self._by_definition[key]

    def __iter__(self):
        return iter(self._fields)

    def __len__(self) -> int:
        return len(self._fields)

    def __repr__(self) -> str:
        return f"Fields({list(self._by_definition.keys())})"


class Physic:
    """
    Physic is a class for managing physics in a project.
    """

    definition_id: str = ""
    display_name: str = ""

    @classmethod
    def get_all(cls, project_id: str | None = None) -> List["Physic"]:
        """
        Get all physics in a project.

        Parameters:
            project_id: The ID of the project. Can be omitted if project API key is used.

        Returns:
            A list of Physics objects.
        """
        project_id = check_for_project_api_key(project_id)
        with get_api() as api:
            physics_list = api.get_physics(
                authorization=get_auth(),
                project_id=project_id,
            )
            return [cls._from_rawapi(project_id, physics) for physics in physics_list]

    @classmethod
    def _from_rawapi(cls, project_id: str, physics: rawapi.Physics) -> "Physic":
        from .generated.registries import PHYSICS_BY_DEFINITION

        subclass = PHYSICS_BY_DEFINITION.get(physics.definition, cls)
        instance = cast("Physic", subclass.__new__(subclass))
        Physic.__init__(instance)
        instance._project_id = project_id
        instance._physics = physics
        instance._definition_id = physics.definition
        instance._target_region_id = physics.target
        return instance

    @classmethod
    def create(
        cls,
        definition: str,
        project_id: str | None = None,
        target_region_id: str | None = None,
    ) -> "Physic":
        """
        Create a new physic.

        Parameters:
            definition: The definition of the physic (e.g., "solidMechanics").
            project_id: The ID of the project. Can be omitted if project API key is used.
            target_region_id: Optional target region ID.

        Returns:
            The created Physics.
        """
        project_id = check_for_project_api_key(project_id)

        with get_api() as api:
            response = api.create_physics(
                authorization=get_auth(),
                project_id=project_id,
                new_physics=rawapi.NewPhysics(
                    definition=definition,
                    target=target_region_id if target_region_id else None,
                ),
            )
        return cls._from_rawapi(project_id, response.physics)

    def __init__(
        self,
        target: "Region | str | None" = None,
    ) -> None:
        """
        Initialize a Physic instance.

        Parameters:
            target: A Region object or region ID string to assign as the target.
        """
        self._project_id: str | None = None
        self._physics: rawapi.Physics | None = None
        self._deleted: bool = False
        self._uncommitted_update: rawapi.PhysicsUpdate | None = None
        self._definition_id = self.definition_id
        self._target_region_id = self._resolve_target_region_id(target)

    def _create_bound(self, project_id: str | None = None) -> "Physic":
        if self._physics is not None:
            raise ValueError("Physic is already initialized")
        return self.__class__.create(
            definition=self.definition,
            project_id=project_id,
            target_region_id=self._target_region_id,
        )

    def _ensure_bound(self) -> rawapi.Physics:
        if self._physics is None:
            raise NotInitializedError("Physic is not initialized")
        return self._physics

    @staticmethod
    def _resolve_target_region_id(target: "Region | str | None") -> str | None:
        if target is None:
            return None
        if isinstance(target, str):
            return target
        region_id = getattr(target, "id", None)
        if region_id is None:
            raise ValueError("target must be a region id string or a Region with an id")
        return region_id

    @property
    @prevent_deleted
    def id(self) -> str:
        """
        Get the ID of the physic.
        """
        physics = self._ensure_bound()
        return physics.id

    @property
    @prevent_deleted
    def definition(self) -> str:
        """
        Get the definition of the physic.
        """
        if self._physics is not None:
            return self._physics.definition
        return self._definition_id

    @property
    @prevent_deleted
    def target_region_id(self) -> str | None:
        """
        Get the target region ID of the physic.
        """
        if self._physics is None:
            return self._target_region_id
        if self._uncommitted_update is not None:
            return self._uncommitted_update.target
        physics = self._ensure_bound()
        return physics.target

    @target_region_id.setter
    @prevent_deleted
    def target_region_id(self, target_region_id: str | None) -> None:
        """
        Set the target region ID of the physic.
        Use save() to commit the change.
        """
        self._ensure_bound()
        self._current_uncommitted_update().target = (
            target_region_id if target_region_id else None
        )

    @property
    @prevent_deleted
    def interactions(self) -> List[Interaction]:
        """
        Get the interactions of the physic.
        """
        return self.get_interactions()

    @prevent_deleted
    def get_interactions(self) -> List[Interaction]:
        """
        Get the interactions of the physic.
        """
        self._ensure_bound()
        self._refresh()

        physics = self._ensure_bound()
        if physics.interactions is None:
            return []
        from .generated.registries import get_interaction_class

        interactions: List[Interaction] = []
        for interaction in physics.interactions:
            subclass = get_interaction_class(self.definition, interaction.definition)
            if subclass is None:
                subclass = Interaction
            interactions.append(
                subclass._from_rawapi(
                    project_id=self._project_id,
                    interaction=interaction,
                    physics_id=self.id,
                )
            )
        return interactions

    @prevent_deleted
    def add_interactions(self, interactions: List[Interaction]) -> List[Interaction]:
        """
        Add interactions to this physic.
        """
        self._ensure_bound()
        if not isinstance(interactions, list):
            raise ValueError("interactions must be a list of Interaction instances")
        created: List[Interaction] = []
        for interaction in interactions:
            if not isinstance(interaction, Interaction):
                raise ValueError(
                    "All items in interactions must be Interaction instances"
                )
            if interaction.physics_definition is not None and (
                interaction.physics_definition != self.definition
            ):
                raise ValueError(
                    f"Interaction '{interaction.definition}' is not compatible with physics '{self.definition}'"
                )
            created.append(
                interaction._create_for_physics(
                    physics_id=self.id,
                    project_id=self._project_id,
                )
            )
        return created

    @prevent_deleted
    def interaction(self, definition: str) -> Interaction | None:
        """
        Get the interaction of the physic by interaction definition.
        """
        interactions = self.get_interactions()
        for interaction in interactions:
            if interaction.definition == definition:
                return interaction
        return None

    @property
    @prevent_deleted
    def fields(self) -> Fields:
        """
        Get the fields of the physic.

        Returns a :class:`Fields` container that supports attribute access,
        dict-style access, indexing, and iteration::

            physics.fields.displacement        # by definition name
            physics.fields["displacement"]     # dict-style
            physics.fields[0]                  # by index
        """
        physics = self._ensure_bound()
        field_list: List[Field] = []
        for field in physics.fields:
            if not field.field_id:
                raise ValueError("Physics field has no field_id")
            if not field.definition:
                raise ValueError("Physics field has no definition")
            field_list.append(
                Field(
                    field.field_id,
                    field.definition,
                )
            )
        return Fields(field_list)

    @prevent_deleted
    def get_field_interpolation_order(self, field_id: str | None = None) -> str | None:
        """
        Get the interpolation order for a field.

        Parameters:
            field_id: The ID of the field. If None, uses the first field.

        Returns:
            The interpolation order of the field, or None if not set.

        Raises:
            ValueError: If the physic has no fields or the field_id is not found.
        """
        physics = self._ensure_bound()
        # Check uncommitted update first
        fields = (
            self._uncommitted_update.fields
            if self._uncommitted_update is not None
            and self._uncommitted_update.fields is not None
            else physics.fields
        )

        if not fields:
            raise ValueError("Physic has no fields")

        if field_id is None:
            return fields[0].interpolation_order

        for field in fields:
            if field.field_id == field_id:
                return field.interpolation_order

        raise ValueError(f"Field with ID '{field_id}' not found")

    @prevent_deleted
    def set_field_interpolation_order(
        self, interpolation_order: str | int, field_id: str | None = None
    ) -> None:
        """
        Set the interpolation order for a field.
        Use save() to commit the change.

        Parameters:
            interpolation_order: The interpolation order to set.
            field_id: The ID of the field. If None, uses the first field.

        Raises:
            ValueError: If the physic has no fields or the field_id is not found.
        """
        physics = self._ensure_bound()
        if not physics.fields:
            raise ValueError("Physic has no fields")

        target_field_id = (
            field_id if field_id is not None else physics.fields[0].field_id
        )

        # Verify the field exists
        field_found = False
        for field in physics.fields:
            if field.field_id == target_field_id:
                field_found = True
                break

        if not field_found:
            raise ValueError(f"Field with ID '{field_id}' not found")

        if isinstance(interpolation_order, int):
            interpolation_order = str(interpolation_order)

        # Build updated fields list
        updated_fields = [
            rawapi.PhysicsField(
                fieldId=field.field_id,
                interpolationOrder=(
                    interpolation_order
                    if field.field_id == target_field_id
                    else field.interpolation_order
                ),
            )
            for field in physics.fields
        ]

        self._current_uncommitted_update().fields = updated_fields

    @prevent_deleted
    def save(self) -> None:
        """
        Explicitly save the changes to the cloud made by
        setting properties like `target_region_id` or `set_field_interpolation_order`.
        """
        physics = self._ensure_bound()
        if self._uncommitted_update is None:
            return

        project_id = check_for_project_api_key(self._project_id)
        physics_update = self._current_uncommitted_update()

        with get_api() as api:
            api.update_physics(
                authorization=get_auth(),
                project_id=project_id,
                physics_id=self.id,
                physics_update=physics_update,
            )

        self._physics = rawapi.Physics(
            id=physics.id,
            definition=physics.definition,
            target=physics_update.target,
            interactions=physics.interactions,
            fields=physics_update.fields,
        )
        self._uncommitted_update = None

    def _refresh(self) -> None:
        self._ensure_bound()
        project_id = check_for_project_api_key(self._project_id)
        with get_api() as api:
            physics_list = api.get_physics(
                authorization=get_auth(),
                project_id=project_id,
            )
            for physics in physics_list:
                if physics.id == self.id:
                    self._physics = physics
                    return
        raise ValueError(f"Physic with ID '{self.id}' not found")

    @prevent_deleted
    def _current_uncommitted_update(self) -> rawapi.PhysicsUpdate:
        """Get the current uncommitted update for the Physic."""
        physics = self._ensure_bound()
        if self._uncommitted_update is None:
            self._uncommitted_update = rawapi.PhysicsUpdate(
                target=physics.target,
                fields=[
                    rawapi.PhysicsField(
                        fieldId=field.field_id,
                        interpolationOrder=field.interpolation_order,
                    )
                    for field in physics.fields
                ],
            )

        return self._uncommitted_update

    @prevent_deleted
    def delete(self) -> None:
        """
        Delete the physic from the project.
        """
        self._ensure_bound()
        project_id = check_for_project_api_key(self._project_id)
        with get_api() as api:
            api.delete_physics(
                authorization=get_auth(),
                project_id=project_id,
                physics_id=self.id,
            )
        self._deleted = True

    def __str__(self) -> str:
        if self._physics is None:
            return f"Physic(definition={self.definition})"
        return f"Physic(id={self.id}, definition={self.definition})"
