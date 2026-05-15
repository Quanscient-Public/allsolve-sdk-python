# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from typing import List, Tuple
from typing_extensions import Self
from allsolve.expression import Variable
from allsolve.util import prevent_deleted
import allsolve_rawapi as rawapi
from .api import get_api, get_auth, check_for_project_api_key


class VariableOverrides:
    """
    VariableOverrides is for managing variable overrides.
    It can be used to override a value of a single or multiple variables
    in a project, or to create a sweep over variables.
    """

    @classmethod
    def create(
        cls,
        name: str,
        overrides: List[
            Tuple[Variable | str, str | float | int | List[str | float | int]]
        ],
        override_type: rawapi.SharedExpressionOverrideType = rawapi.SharedExpressionOverrideType.SWEEP,
        sweep_type: rawapi.SweepType | None = None,
        project_id: str | None = None,
    ) -> Self:
        """
        Create a new VariableOverrides.

        Args:
            name: The name of the set of variable overrides.
            overrides: A list of overrides of the VariableOverrides.
                The first element of the tuple is the variable to override.
                The variable can be a Variable object or a string with the name of the variable.
                The second element is the new value for the variable.
                The value can be a string, float, int, or list of strings, floats, or ints.
            override_type: The type of the VariableOverrides. Normal or Sweep.
            project_id: The ID of the project.

        Returns:
            The created VariableOverrides.
        """
        project_id = check_for_project_api_key(project_id)

        override_list = cls._convert_override_list_tuples(overrides, project_id)
        if override_type == rawapi.SharedExpressionOverrideType.SWEEP:
            if sweep_type is None:
                sweep_type = rawapi.SweepType.SPECIFIC_VALUES

        new_overrides = [
            rawapi.SharedExpressionOverride(
                sharedExpressionId=override[0],
                type=override_type,
                expression=override[1],
            )
            for override in override_list
        ]

        with get_api() as api:

            override_set = api.create_override_set(
                authorization=get_auth(),
                project_id=project_id,
                new_override_set=rawapi.NewOverrideSet(
                    name=name,
                    type=override_type,
                    overrides=new_overrides,
                    sweepType=sweep_type,
                ),
            )
        return cls(project_id, override_set)

    @classmethod
    def get(cls, variable_overrides_id: str, project_id: str | None = None) -> Self:
        """
        Get a VariableOverrides by its ID.
        """
        project_id = check_for_project_api_key(project_id)
        with get_api() as api:
            override_set = api.get_override_set(
                authorization=get_auth(),
                project_id=project_id,
                override_set_id=variable_overrides_id,
            )
        return cls(project_id, override_set)

    @classmethod
    def get_all(cls, project_id: str | None = None) -> List[Self]:
        """
        Get all VariableOverrides in a project.
        """
        project_id = check_for_project_api_key(project_id)
        with get_api() as api:
            override_sets = api.get_override_sets(
                authorization=get_auth(),
                project_id=project_id,
            )
            return [
                cls(
                    project_id,
                    override_set,
                )
                for override_set in override_sets
            ]

    @classmethod
    def _convert_override_list_tuples(
        cls,
        overrides: List[
            Tuple[Variable | str, str | float | int | List[str | float | int]]
        ],
        project_id: str,
    ) -> List[Tuple[str, str]]:
        override_list: List[Tuple[str, str]] = []
        for variable, value in overrides:
            if isinstance(variable, str):
                var: Variable | None = Variable.get_by_name(variable, project_id)
                if var is None:
                    raise ValueError(
                        f"Variable {variable} not found in project {project_id}"
                    )
                variable = var
            if not isinstance(variable, Variable):
                raise ValueError(f"Variable {variable} is not a variable.")

            override_value = (
                f"[{', '.join(map(str, value))}]"
                if isinstance(value, list)
                else str(value)
            )
            override_list.append((variable.id, override_value))

        return override_list

    def __init__(self, project_id: str, override_set: rawapi.OverrideSet) -> None:
        self._project_id = project_id
        self._override_set = override_set
        self._deleted: bool = False
        self._uncommitted_update: rawapi.OverrideSetUpdate | None = None

    @property
    @prevent_deleted
    def id(self) -> str:
        """
        Get the ID of the VariableOverrides.
        """
        return self._override_set.id

    @property
    @prevent_deleted
    def name(self) -> str:
        """
        Get the name of the VariableOverrides.
        """
        return self._override_set.name

    @name.setter
    @prevent_deleted
    def name(self, name: str) -> None:
        """
        Set the name of the VariableOverrides.
        """
        self._current_uncommitted_update().name = name
        self._save()

    @property
    @prevent_deleted
    def type(self) -> rawapi.SharedExpressionOverrideType:
        """
        Get the type of the VariableOverrides.
        """
        return self._override_set.type

    @property
    @prevent_deleted
    def sweep_type(self) -> rawapi.SweepType | None:
        """
        Get the sweep type of the VariableOverrides. Only valid for sweep overrides.
        """
        return self._override_set.sweep_type

    @sweep_type.setter
    @prevent_deleted
    def sweep_type(self, sweep_type: rawapi.SweepType | None) -> None:
        """
        Set the sweep type of the VariableOverrides. Only valid for sweep overrides.
        """
        if self.type != rawapi.SharedExpressionOverrideType.SWEEP:
            raise ValueError("Sweep type is only valid for sweep overrides.")

        self._current_uncommitted_update().sweep_type = sweep_type
        self._save()

    @property
    @prevent_deleted
    def overrides(self) -> List[Tuple[Variable, str]]:
        """
        Get the overrides of the VariableOverrides.
        The list is a copy of the overrides in the VariableOverrides.
        It the list is modified, use overrides setter to save the change.
        The list is a list of tuples, where the first element is the variable
        and the second is the new value for the variable.
        """
        return [
            (
                Variable.get(override.shared_expression_id, self._project_id),
                override.expression,
            )
            for override in self._override_set.overrides
        ]

    @overrides.setter
    @prevent_deleted
    def overrides(
        self,
        overrides: List[
            Tuple[Variable | str, str | float | int | List[str | float | int]]
        ],
    ) -> None:
        """
        Set the overrides of the VariableOverrides.
        """
        override_list = self._convert_override_list_tuples(overrides, self._project_id)
        self._current_uncommitted_update().overrides = [
            rawapi.SharedExpressionOverride(
                id=None,
                sharedExpressionId=override[0],
                type=self.type,
                expression=override[1],
            )
            for override in override_list
        ]
        self._save()

    @prevent_deleted
    def delete(self) -> None:
        """
        Delete the VariableOverrides.
        """
        with get_api() as api:
            api.delete_override_set(
                authorization=get_auth(),
                project_id=self._project_id,
                override_set_id=self.id,
            )
        self._deleted = True

    @prevent_deleted
    def _save(self) -> None:
        """
        Save the changes to the cloud made by
        setting properties `name` and `overrides`.
        """
        if self._uncommitted_update is None:
            return

        project_id = check_for_project_api_key(self._project_id)
        override_set_update = self._current_uncommitted_update()

        with get_api() as api:
            api.update_override_set(
                authorization=get_auth(),
                project_id=project_id,
                override_set_id=self.id,
                override_set_update=override_set_update,
            )

            self._uncommitted_update = None

            self._override_set = api.get_override_set(
                authorization=get_auth(),
                project_id=self._project_id,
                override_set_id=self.id,
            )

    @prevent_deleted
    def _current_uncommitted_update(self) -> rawapi.OverrideSetUpdate:
        """Get the current uncommitted update for the VariableOverrides."""
        if self._override_set is None:
            raise ValueError("VariableOverrides is not initialized")
        if self._uncommitted_update is None:
            self._uncommitted_update = rawapi.OverrideSetUpdate(
                name=self._override_set.name,
                overrides=self._override_set.overrides,
                sweepType=self._override_set.sweep_type,
            )

        return self._uncommitted_update

    def __str__(self) -> str:
        return f"VariableOverrides(name={self.name}, id={self.id}, type={self.type})"
