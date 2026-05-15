# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from typing import Dict, List, Tuple, TYPE_CHECKING
from typing_extensions import Self

import allsolve_rawapi as rawapi

from ..api import check_for_project_api_key, get_api, get_auth
from ..util import NotInitializedError, prevent_deleted
from .conversions import BooleanValue

if TYPE_CHECKING:
    from allsolve.region import Region


class InteractionParameter:
    """
    InteractionParameter is a class for managing interaction parameters.
    """

    @classmethod
    def _from_rawapi(cls, parameter: rawapi.InteractionParameter) -> Self:
        return cls(
            definition=parameter.definition,
            value=parameter.value,
        )

    def __init__(
        self, definition: str, value: str | None = None, ascii_value: str | None = None
    ):
        """
        Initialize an interaction parameter.

        Parameters:
            definition: The definition of the parameter.
            value: The value of the parameter (as a string).
            ascii_value: If provided, converts the string to ASCII char array format.
                For example, "fieldOutputFilterTypeNone" becomes "[102, 105, 101, ...]".
                Mutually exclusive with value.
        """
        if value is None and ascii_value is None:
            raise ValueError("Either value or ascii_value must be provided")
        if value is not None and ascii_value is not None:
            raise ValueError("Cannot provide both value and ascii_value")

        self._definition = definition
        if ascii_value is not None:
            # Convert string to ASCII char array format: "[102, 105, 101, ...]"
            ascii_codes = [str(ord(char)) for char in ascii_value]
            self._value: str = f"[{', '.join(ascii_codes)}]"
        else:
            # At this point, value is guaranteed to be not None due to the check above
            assert value is not None, "value must be provided if ascii_value is None"
            self._value = value

    @property
    def value(self) -> str:
        """
        Get the value of the parameter.
        """
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        """
        Set the value of the parameter.
        """
        self._value = value

    @property
    def definition(self) -> str:
        """
        Get the definition of the parameter.
        """
        return self._definition

    def _to_rawapi(self) -> rawapi.InteractionParameter:
        return rawapi.InteractionParameter(
            definition=self.definition,
            value=self._value,
        )

    def __str__(self) -> str:
        return (
            f"InteractionParameter(definition={self.definition}, value={self._value})"
        )


class InteractionBase:
    """
    InteractionBase is a base class for interactions and output interactions in a project.
    """

    definition_id: str = ""
    physics_definition_id: str | None = None
    target_definition_ids: Dict[str, str] = {}
    """Mapping of Python parameter name to target definition ID."""

    optional_target_definition_ids: set[str] = set()
    """Set of target param names that are optional (may be omitted)."""

    auto_determined_targets: set[str] = set()
    """Set of target param names that are auto-determined by the solver."""

    @classmethod
    def _from_rawapi(
        cls,
        project_id: str | None,
        interaction: rawapi.Interaction,
        physics_id: str | None = None,
        simulation_id: str | None = None,
    ) -> Self:
        instance = cls.__new__(cls)
        InteractionBase.__init__(
            instance,
            name=interaction.name,
            project_id=project_id,
            interaction=interaction,
            physics_id=physics_id,
            simulation_id=simulation_id,
        )
        return instance

    def __init__(
        self,
        name: str | None = None,
        enabled: "BooleanValue | None" = None,
        parameters: List[InteractionParameter] | None = None,
        *,
        namespace: str | None = None,
        targets: "Dict[str, Region | str | None] | None" = None,
        project_id: str | None = None,
        interaction: rawapi.Interaction | None = None,
        physics_id: str | None = None,
        simulation_id: str | None = None,
    ) -> None:
        self._project_id = project_id
        self._physics_id = physics_id
        self._simulation_id = simulation_id
        self._interaction = interaction
        self._deleted: bool = False
        self._uncommitted_update: rawapi.InteractionUpdate | None = None
        if interaction is None:
            self._spec_name = name
            self._spec_enabled = enabled
            self._spec_namespace = namespace
            self._spec_target_region_ids: Dict[str, str] = {}
            if targets is not None:
                for param_name, t in targets.items():
                    resolved = self._resolve_target_region_id(t)
                    if resolved is not None:
                        self._spec_target_region_ids[param_name] = resolved
            self._spec_parameters = parameters or []
            self._definition_id = self.definition_id
        else:
            self._spec_name = None
            self._spec_enabled = None
            self._spec_namespace = None
            self._spec_target_region_ids = {}
            self._spec_parameters = []
            self._definition_id = interaction.definition
            self._validate()

    def _ensure_bound(self) -> rawapi.Interaction:
        if self._interaction is None:
            raise NotInitializedError("Interaction is not initialized")
        return self._interaction

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
    def physics_definition(self) -> str | None:
        return self.physics_definition_id

    @property
    @prevent_deleted
    def id(self) -> str:
        """
        Get the ID of the interaction.
        """
        interaction = self._ensure_bound()
        return interaction.id

    @property
    @prevent_deleted
    def name(self) -> str:
        """
        Get the name of the interaction.
        """
        interaction = self._ensure_bound()
        return interaction.name

    @name.setter
    @prevent_deleted
    def name(self, name: str) -> None:
        """
        Set the name of the shared expression.
        Use save() to commit the change.
        """
        self._current_uncommitted_update().name = name

    @property
    @prevent_deleted
    def definition(self) -> str:
        """
        Get the definition of the interaction.
        """
        if self._interaction is not None:
            return self._interaction.definition
        return self._definition_id

    @property
    @prevent_deleted
    def enabled(self) -> bool:
        """
        Get whether the interaction is enabled.
        """
        interaction = self._ensure_bound()
        return interaction.enabled

    @enabled.setter
    @prevent_deleted
    def enabled(self, enabled: bool) -> None:
        """
        Set whether the interaction is enabled.
        Use save() to commit the change.
        """
        self._current_uncommitted_update().enabled = enabled

    @property
    @prevent_deleted
    def namespace(self) -> str | None:
        """
        Get the namespace of the interaction.
        """
        if self._interaction is not None:
            return self._interaction.namespace
        return self._spec_namespace

    @namespace.setter
    @prevent_deleted
    def namespace(self, namespace: str | None) -> None:
        """
        Set the namespace of the interaction.
        Use save() to commit the change.
        """
        self._current_uncommitted_update().namespace = namespace

    @prevent_deleted
    def target_region_id(self, target_definition: str | None = None) -> str | None:
        """
        Get the targets of the interaction.
        """
        interaction = self._ensure_bound()
        if interaction.targets is None:
            return None
        for target in interaction.targets:
            if target_definition is None or target.definition == target_definition:
                return target.region
        return None

    @prevent_deleted
    def set_target_region_id(
        self, region_id: str, target_definition: str | None = None
    ) -> None:
        """
        Set the target region ID for a specific target definition.
        Use save() to commit the change.

        Parameters:
            region_id: The region ID to set.
            target_definition: The target definition to update. If None, updates the first target.
        """
        self._ensure_bound()
        update = self._current_uncommitted_update()
        if update.targets is None:
            update.targets = []

        # Try to find and update existing target
        for target in update.targets:
            if target_definition is None or target.definition == target_definition:
                target.region = region_id
                return

        # If no matching target found
        raise ValueError(f"Target definition '{target_definition}' not found")

    @property
    @prevent_deleted
    def parameters(self) -> List[InteractionParameter]:
        """
        Get the parameters of the interaction.
        """
        interaction = self._ensure_bound()
        if interaction.parameters is None:
            return []
        return [
            InteractionParameter._from_rawapi(parameter)
            for parameter in interaction.parameters
        ]

    @parameters.setter
    @prevent_deleted
    def parameters(self, parameters: List[InteractionParameter]) -> None:
        """
        Set the parameters of the interaction.
        Use save() to commit the change.
        """
        interaction = self._ensure_bound()
        existing_params = interaction.parameters or []

        if len(parameters) != len(existing_params):
            raise ValueError(
                f"Parameters list length mismatch: expected {len(existing_params)}, got {len(parameters)}"
            )

        for i, (new_param, existing_param) in enumerate(
            zip(parameters, existing_params)
        ):
            if new_param.definition != existing_param.definition:
                raise ValueError(
                    f"Parameter definition mismatch at index {i}: "
                    f"expected '{existing_param.definition}', got '{new_param.definition}'"
                )

        self._current_uncommitted_update().parameters = [
            param._to_rawapi() for param in parameters
        ]

    @prevent_deleted
    def save(self) -> None:
        """
        Save the changes to the cloud made by
        setting properties like `name`, `enabled`, `target_region_id`, or `parameters`.
        """
        interaction = self._ensure_bound()
        if self._uncommitted_update is None:
            return

        project_id = check_for_project_api_key(self._project_id)
        interaction_update = self._current_uncommitted_update()

        with get_api() as api:
            api.update_interaction(
                authorization=get_auth(),
                project_id=project_id,
                interaction_id=self.id,
                physics_id=self._physics_id,
                simulation_id=self._simulation_id,
                interaction_update=interaction_update,
            )

        self._interaction = rawapi.Interaction(
            id=interaction.id,
            name=interaction_update.name,
            namespace=interaction_update.namespace,
            definition=interaction.definition,
            enabled=interaction_update.enabled,
            targets=interaction_update.targets,
            parameters=interaction_update.parameters,
            createdAt=interaction.created_at,
        )
        self._uncommitted_update = None

    def _validate(self) -> None:
        if self._physics_id is None:
            raise ValueError("Interaction is not associated with a physics")

    @prevent_deleted
    def _current_uncommitted_update(self) -> rawapi.InteractionUpdate:
        """Get the current uncommitted update for the Interaction."""
        interaction = self._ensure_bound()
        if self._uncommitted_update is None:
            self._uncommitted_update = rawapi.InteractionUpdate(
                name=interaction.name,
                namespace=interaction.namespace,
                enabled=interaction.enabled,
                targets=[
                    rawapi.InteractionTarget(
                        definition=target.definition,
                        region=target.region,
                    )
                    for target in (interaction.targets or [])
                ],
                parameters=[
                    rawapi.InteractionParameter(
                        definition=param.definition,
                        value=param.value,
                    )
                    for param in (interaction.parameters or [])
                ],
            )

        return self._uncommitted_update

    @prevent_deleted
    def delete(self) -> None:
        """
        Delete the interaction from the project.
        """
        self._ensure_bound()
        project_id = check_for_project_api_key(self._project_id)
        with get_api() as api:
            api.delete_interaction(
                authorization=get_auth(),
                project_id=project_id,
                interaction_id=self.id,
                physics_id=self._physics_id,
                simulation_id=self._simulation_id,
            )
        self._deleted = True

    def __str__(self) -> str:
        if self._interaction is None:
            return f"Interaction(definition={self.definition})"
        return (
            f"Interaction(id={self.id}, name={self.name}, definition={self.definition})"
        )


class Interaction(InteractionBase):
    """
    Interaction is a class for managing interactions in a project.
    """

    @classmethod
    def create(
        cls,
        physics_id: str,
        name: str,
        definition: str,
        enabled: "BooleanValue | None" = None,
        project_id: str | None = None,
        parameters: List[InteractionParameter] | None = None,
        interaction_targets: List[Tuple[str, str]] | None = None,
        namespace: str | None = None,
    ) -> Self:
        """
        Create a new interaction for a physics in the project.

        Recommended to use the physics.add_interactions() method to create an interaction.
        First you need to add physics to the project.
        Example:
        ```python
        physic = project.add_physics(allsolve.Physics.SolidMechanics())
        physic.add_interactions([allsolve.Interaction.SolidMechanicsClamp(name="clamp", target=region_clamp_surface)])
        ```

        Parameters:
            physics_id: The ID of the physics this interaction belongs to.
            name: The name of the interaction.
            definition: The definition of the interaction (e.g., "clamp").
            enabled: The enabled expression for the interaction (bool or string).
            project_id: The ID of the project. Can be omitted if project API key is used.
            parameters: Optional list of interaction parameters.
            interaction_targets: Optional list of (definition_id, region_id) tuples.
            namespace: Optional namespace for the interaction.

        Returns:
            The created Interaction.
        """
        project_id = check_for_project_api_key(project_id)

        raw_targets: List[rawapi.InteractionTarget] = [
            rawapi.InteractionTarget(definition=defn, region=region)
            for defn, region in (interaction_targets or [])
        ]

        if enabled is None:
            enabled_bool = True
        elif isinstance(enabled, bool):
            enabled_bool = enabled
        else:
            enabled_bool = enabled != "0"

        with get_api() as api:
            interaction = api.create_interaction(
                authorization=get_auth(),
                project_id=project_id,
                physics_id=physics_id,
                new_interaction=rawapi.NewInteraction(
                    name=name,
                    namespace=namespace,
                    definition=definition,
                    enabled=enabled_bool,
                    targets=raw_targets,
                    parameters=(
                        [parameter._to_rawapi() for parameter in parameters or []]
                        if parameters
                        else []
                    ),
                ),
            )
        return cls._from_rawapi(
            project_id=project_id,
            interaction=interaction,
            physics_id=physics_id,
        )

    def _create_for_physics(
        self, physics_id: str, project_id: str | None = None
    ) -> "Interaction":
        if self._interaction is not None:
            raise ValueError("Interaction is already initialized")
        if self._spec_name is None:
            raise ValueError("Interaction name must be provided")

        interaction_targets: List[Tuple[str, str]] = [
            (defn_id, self._spec_target_region_ids[param_name])
            for param_name, defn_id in self.target_definition_ids.items()
            if param_name in self._spec_target_region_ids
        ]

        return self.__class__.create(
            physics_id=physics_id,
            name=self._spec_name,
            definition=self.definition,
            enabled=self._spec_enabled,
            project_id=project_id,
            parameters=self._spec_parameters,
            interaction_targets=interaction_targets or None,
            namespace=self._spec_namespace,
        )


class OutputInteraction(InteractionBase):
    """
    OutputInteraction is a class for managing output interactions in a simulation.
    """

    @classmethod
    def _from_rawapi(
        cls,
        project_id: str | None,
        interaction: rawapi.Interaction,
        physics_id: str | None = None,
        simulation_id: str | None = None,
    ) -> Self:
        instance = cls.__new__(cls)
        InteractionBase.__init__(
            instance,
            name=interaction.name,
            project_id=project_id,
            interaction=interaction,
            simulation_id=simulation_id,
        )
        return instance

    @classmethod
    def create(
        cls,
        simulation_id: str,
        name: str,
        definition: str,
        project_id: str | None = None,
        parameters: List[InteractionParameter] | None = None,
        enabled: bool = True,
        interaction_targets: List[Tuple[str, str]] | None = None,
    ) -> Self:
        """
        Create a new output interaction for a simulation.

        Parameters:
            simulation_id: The ID of the simulation this interaction belongs to.
            name: The name of the interaction.
            definition: The definition of the interaction (e.g., "fieldOutput").
            project_id: The ID of the project. Can be omitted if project API key is used.
            parameters: Optional list of interaction parameters.
            enabled: Whether the interaction is enabled (default: True).
            interaction_targets: Optional list of (definition_id, region_id) tuples.

        Returns:
            The created Interaction.
        """
        project_id = check_for_project_api_key(project_id)

        raw_targets: List[rawapi.InteractionTarget] = [
            rawapi.InteractionTarget(definition=defn, region=region)
            for defn, region in (interaction_targets or [])
        ]

        with get_api() as api:
            interaction = api.create_interaction(
                authorization=get_auth(),
                project_id=project_id,
                simulation_id=simulation_id,
                new_interaction=rawapi.NewInteraction(
                    name=name,
                    definition=definition,
                    enabled=enabled,
                    targets=raw_targets,
                    parameters=(
                        [parameter._to_rawapi() for parameter in parameters or []]
                        if parameters
                        else []
                    ),
                ),
            )
        return cls._from_rawapi(
            project_id=project_id,
            interaction=interaction,
            simulation_id=simulation_id,
        )

    def _create_for_simulation(
        self, simulation_id: str, project_id: str | None = None
    ) -> "OutputInteraction":
        if self._interaction is not None:
            raise ValueError("OutputInteraction is already initialized")
        if self._spec_name is None:
            raise ValueError("OutputInteraction name must be provided")
        if self._spec_enabled is None:
            enabled = True
        elif isinstance(self._spec_enabled, bool):
            enabled = self._spec_enabled
        else:
            enabled = str(self._spec_enabled) != "0"

        interaction_targets: List[Tuple[str, str]] = [
            (defn_id, self._spec_target_region_ids[param_name])
            for param_name, defn_id in self.target_definition_ids.items()
            if param_name in self._spec_target_region_ids
        ]

        return self.__class__.create(
            simulation_id=simulation_id,
            name=self._spec_name,
            definition=self.definition,
            project_id=project_id,
            parameters=self._spec_parameters,
            enabled=enabled,
            interaction_targets=interaction_targets or None,
        )

    def __init__(
        self,
        name: str | None = None,
        enabled: bool = True,
        parameters: List[InteractionParameter] | None = None,
        *,
        targets: "Dict[str, Region | str | None] | None" = None,
        project_id: str | None = None,
        interaction: rawapi.Interaction | None = None,
        simulation_id: str | None = None,
    ) -> None:
        super().__init__(
            name=name,
            enabled=enabled,
            parameters=parameters,
            targets=targets,
            project_id=project_id,
            interaction=interaction,
            simulation_id=simulation_id,
        )

    def _validate(self) -> None:
        if self._simulation_id is None:
            raise ValueError("OutputInteraction is not associated with a simulation")

    @prevent_deleted
    def __str__(self) -> str:
        if self._interaction is None:
            return f"OutputInteraction(definition={self.definition})"
        return f"OutputInteraction(id={self.id}, name={self.name}, definition={self.definition})"
