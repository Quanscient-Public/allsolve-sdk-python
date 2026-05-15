# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import List, Optional, Union, Tuple
from typing_extensions import Self
from allsolve.util import prevent_deleted
import allsolve_rawapi as rawapi
from .api import get_api, get_auth, check_for_project_api_key


class ExpressionType(Enum):
    """
    Type of a shared expression.

    Used when creating or filtering :class:`SharedExpression` objects
    (variables, functions, and interpolated functions).
    """

    EXPRESSION = rawapi.SharedExpressionType.EXPRESSION
    """A simple expression or variable."""

    INTERPOLATED_FUNCTION = rawapi.SharedExpressionType.INTERPOLATEDFUNCTION
    """A function defined by discrete data points with interpolation between them."""

    FUNCTION = rawapi.SharedExpressionType.FUNCTION
    """An analytic function with named arguments."""


class ExpressionArg(rawapi.SharedExpressionArg):
    def __init__(
        self,
        name: str,
        index: int,
        values: Optional[List[Union[float, int]]] = None,
    ):
        super().__init__(name=name, index=index, values=values)


class SharedExpression:
    """
    SharedExpression is for managing shared expressions.

    The "Shared" means that they are stored in the system so that they can referred to
    in other places using their identifier.
    """

    @classmethod
    def _create(
        cls,
        name: str,
        expression_type: ExpressionType = ExpressionType.EXPRESSION,
        description: str = "",
        expression: Optional[str | float | int] = None,
        args: Optional[List[ExpressionArg] | List[rawapi.SharedExpressionArg]] = None,
        values: Optional[List[Union[float, int]]] = None,
        cubic_interpolation: Optional[bool] = None,
        project_id: str | None = None,
    ) -> Self:
        """
        Create a new shared expression.
        """
        if expression is not None:
            expression = str(expression)

        project_id = check_for_project_api_key(project_id)

        shared_expression = None
        with get_api() as api:
            if args is not None:
                args = [
                    rawapi.SharedExpressionArg(
                        name=arg.name,
                        index=arg.index,
                        values=arg.values,
                    )
                    for arg in args
                ]

            shared_expression = api.create_shared_expression(
                authorization=get_auth(),
                project_id=project_id,
                shared_expression_update=rawapi.SharedExpressionUpdate(
                    name=name,
                    type=expression_type.value,
                    description=description,
                    expression=expression,
                    args=args,
                    values=values,
                    cubicInterpolation=cubic_interpolation,
                ),
            )
        return cls(project_id, shared_expression)

    @classmethod
    def get(cls, expr_id: str, project_id: str | None = None) -> Self:
        """
        Get a shared expression by its ID.
        """
        project_id = check_for_project_api_key(project_id)
        with get_api() as api:
            shared_expression = api.get_shared_expression(
                authorization=get_auth(),
                project_id=project_id,
                expr_id=expr_id,
            )
        return cls(project_id, shared_expression)

    @classmethod
    def get_all(cls, project_id: str | None = None) -> List[Self]:
        """
        Get all shared expressions in a project.
        """
        project_id = check_for_project_api_key(project_id)
        with get_api() as api:
            shared_expressions = api.get_shared_expressions(
                authorization=get_auth(),
                project_id=project_id,
            )
            return [
                cls(
                    project_id,
                    shared_expression,
                )
                for shared_expression in shared_expressions
            ]

    def __init__(
        self, project_id: str, shared_expression: rawapi.SharedExpression
    ) -> None:
        self._project_id = project_id
        self._shared_expression = shared_expression
        self._deleted: bool = False
        self._uncommitted_update: rawapi.SharedExpressionUpdate | None = None

    @property
    @prevent_deleted
    def id(self) -> str:
        """
        Get the ID of the shared expression.
        """
        return self._shared_expression.id

    @property
    @prevent_deleted
    def name(self) -> str:
        """
        Get the name of the shared expression.
        """
        return self._get_current_state().name

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
    def description(self) -> str:
        """
        Get the description of the shared expression.
        """
        return self._get_current_state().description

    @description.setter
    @prevent_deleted
    def description(self, description: str) -> None:
        """
        Set the description of the shared expression.
        Use save() to commit the change.
        """
        self._current_uncommitted_update().description = description

    @property
    @prevent_deleted
    def type(self) -> rawapi.SharedExpressionType:
        """
        Get the type of the shared expression.
        """
        return self._get_current_state().type

    @type.setter
    @prevent_deleted
    def type(self, expression_type: rawapi.SharedExpressionType) -> None:
        """
        Set the type of the shared expression.
        Use save() to commit the change.
        """
        self._current_uncommitted_update().type = expression_type

    @property
    @prevent_deleted
    def origin(self) -> Optional[str]:
        """
        Get the origin (original shared expression ID if this is a copy).
        """
        return self._get_current_state().origin

    @origin.setter
    @prevent_deleted
    def origin(self, origin: Optional[str]) -> None:
        """
        Set the origin of the shared expression.
        Use save() to commit the change.
        """
        self._current_uncommitted_update().origin = origin

    @property
    @prevent_deleted
    def args(self) -> Optional[List[rawapi.SharedExpressionArg]]:
        """
        Get the arguments of the shared expression.
        """
        return self._get_current_state().args

    @args.setter
    @prevent_deleted
    def args(self, args: Optional[List[rawapi.SharedExpressionArg]]) -> None:
        """
        Set the arguments of the shared expression.
        Use save() to commit the change.
        """
        self._current_uncommitted_update().args = args

    @property
    @prevent_deleted
    def expression(self) -> Optional[str]:
        """
        Get the expression string.
        """
        return self._get_current_state().expression

    @expression.setter
    @prevent_deleted
    def expression(self, expression: Optional[str]) -> None:
        """
        Set the expression string.
        Use save() to commit the change.
        """
        self._current_uncommitted_update().expression = expression

    @property
    @prevent_deleted
    def values(self) -> Optional[List[Union[float, int]]]:
        """
        Get the values of the shared expression.
        """
        return self._get_current_state().values

    @values.setter
    @prevent_deleted
    def values(self, values: Optional[List[Union[float, int]]]) -> None:
        """
        Set the values of the shared expression.
        Use save() to commit the change.
        """
        self._current_uncommitted_update().values = values

    @property
    @prevent_deleted
    def cubic_interpolation(self) -> Optional[bool]:
        """
        Get whether cubic spline interpolation is used (for interpolated functions).
        When True, values are interpolated using a natural cubic spline.
        When False or None, linear interpolation is used.
        """
        return self._get_current_state().cubic_interpolation

    @cubic_interpolation.setter
    @prevent_deleted
    def cubic_interpolation(self, cubic_interpolation: Optional[bool]) -> None:
        """
        Set whether cubic spline interpolation is used.
        Use save() to commit the change.
        """
        self._current_uncommitted_update().cubic_interpolation = cubic_interpolation

    @prevent_deleted
    def delete(self) -> None:
        """
        Delete the shared expression.
        """
        with get_api() as api:
            api.delete_shared_expression(
                authorization=get_auth(),
                project_id=self._project_id,
                expr_id=self.id,
            )
        self._deleted = True

    @prevent_deleted
    def save(self) -> None:
        """
        Explicitly save the changes to the cloud made by
        setting properties like `name`, `description`, `type`, `expression`,
        `args`, `origin`, `values` and `cubic_interpolation`.
        """
        if self._uncommitted_update is None:
            return

        project_id = check_for_project_api_key(self._project_id)
        expression_update = self._current_uncommitted_update()

        with get_api() as api:
            api.update_shared_expression(
                authorization=get_auth(),
                project_id=project_id,
                expr_id=self.id,
                shared_expression_update=expression_update,
            )

            self._uncommitted_update = None

            self._shared_expression = api.get_shared_expression(
                authorization=get_auth(),
                project_id=self._project_id,
                expr_id=self.id,
            )

    @prevent_deleted
    def _current_uncommitted_update(self) -> rawapi.SharedExpressionUpdate:
        """Get the current uncommitted update for the shared expression."""
        if self._shared_expression is None:
            raise ValueError("SharedExpression is not initialized")
        if self._uncommitted_update is None:
            self._uncommitted_update = rawapi.SharedExpressionUpdate(
                name=self._shared_expression.name,
                type=self._shared_expression.type,
                description=self._shared_expression.description,
                origin=self._shared_expression.origin,
                args=self._shared_expression.args,
                expression=self._shared_expression.expression,
                values=self._shared_expression.values,
                cubicInterpolation=self._shared_expression.cubic_interpolation,
            )

        return self._uncommitted_update

    @prevent_deleted
    def _get_current_state(
        self,
    ) -> rawapi.SharedExpression | rawapi.SharedExpressionUpdate:
        """Get the current state of the shared expression."""
        if self._uncommitted_update is not None:
            return self._uncommitted_update
        return self._shared_expression

    def __str__(self) -> str:
        return f"SharedExpression(name={self.name}, id={self.id}, type={self.type})"


class Variable(SharedExpression):
    """
    A variable expression in the project.
    Variables are SharedExpressions with type EXPRESSION.
    """

    @classmethod
    def create(
        cls,
        name: str,
        expression: str | float | int,
        description: str = "",
        project_id: str | None = None,
    ) -> Self:
        """
        Create a variable in the project.

        Parameters:
            name: The name of the variable.
            expression: The expression of the variable.
            description: The description of the variable.
            project_id: The ID of the project.

        Returns:
            The created variable.
        """
        if expression is not None:
            expression = str(expression)

        return cls._create(
            name=name,
            expression=expression,
            expression_type=ExpressionType.EXPRESSION,
            description=description,
            project_id=project_id,
        )

    @classmethod
    def get_all(cls, project_id: str | None = None) -> List[Self]:
        """
        Get all variables in a project.
        """
        all_expressions = SharedExpression.get_all(project_id=project_id)
        return [
            cls(expr._project_id, expr._shared_expression)
            for expr in all_expressions
            if expr.type == ExpressionType.EXPRESSION.value
        ]

    @classmethod
    def get_by_name(cls, name: str, project_id: str | None = None) -> Self | None:
        """
        Get a variable by its name.
        Returns None if no variable matches the given name.

        Parameters:
            name: The name of the variable.
            project_id: The ID of the project.

        Returns:
            The variable that matches the given name.
        """
        all_variables = cls.get_all(project_id=project_id)
        matching_variables = [var for var in all_variables if var.name == name]
        if len(matching_variables) == 0:
            return None
        if len(matching_variables) > 1:
            raise ValueError(f"Multiple variables found with name {name}")
        return matching_variables[0]


class Function(SharedExpression):
    """
    A function expression in the project.
    Functions are SharedExpressions with type FUNCTION.
    """

    @classmethod
    def create(
        cls,
        name: str,
        args: List[str],
        expression: str,
        description: str = "",
        project_id: str | None = None,
    ) -> Self:
        """
        Create a function in the project.

        Parameters:
            name: The name of the function.
            args: The arguments of the function.
            expression: The expression of the function.
            description: The description of the function.
            project_id: The ID of the project.

        Returns:
            The created function.
        """
        return cls._create(
            name=name,
            expression=expression,
            expression_type=ExpressionType.FUNCTION,
            args=[ExpressionArg(name=arg, index=i) for i, arg in enumerate(args)],
            description=description,
            project_id=project_id,
        )

    @classmethod
    def get_all(cls, project_id: str | None = None) -> List[Self]:
        """
        Get all functions in a project.
        """
        all_expressions = SharedExpression.get_all(project_id=project_id)
        return [
            cls(expr._project_id, expr._shared_expression)
            for expr in all_expressions
            if expr.type == ExpressionType.FUNCTION.value
        ]

    @classmethod
    def get_by_name(cls, name: str, project_id: str | None = None) -> Self | None:
        """
        Get a function by its name.
        Returns None if no function matches the given name.

        Parameters:
            name: The name of the function.
            project_id: The ID of the project.

        Returns:
            The function that matches the given name.

        """
        all_functions = cls.get_all(project_id=project_id)
        matching_functions = [func for func in all_functions if func.name == name]
        if len(matching_functions) == 0:
            return None
        if len(matching_functions) > 1:
            raise ValueError(f"Multiple functions found with name {name}")
        return matching_functions[0]


class InterpolatedFunction(SharedExpression):
    """
    An interpolated function expression in the project.
    Interpolated functions are SharedExpressions with type INTERPOLATED_FUNCTION.
    """

    @classmethod
    def create(
        cls,
        name: str,
        args: List[Tuple[str, List[float]]],
        values: List[float],
        description: str = "",
        cubic_interpolation: bool | None = None,
        project_id: str | None = None,
    ) -> Self:
        """
        Create an interpolated function in the project.

        Parameters:
            name: The name of the interpolated function.
            args: The arguments of the interpolated function.
            values: The values of the interpolated function.
            description: The description of the interpolated function.
            cubic_interpolation: If True, values are interpolated using a natural
                cubic spline. If False or None, linear interpolation is used.
            project_id: The ID of the project.

        Returns:
            The created interpolated function.
        """
        return cls._create(
            name=name,
            expression_type=ExpressionType.INTERPOLATED_FUNCTION,
            args=[
                ExpressionArg(name=arg[0], index=i, values=arg[1])
                for i, arg in enumerate(args)
            ],
            values=values,
            cubic_interpolation=cubic_interpolation,
            description=description,
            project_id=project_id,
        )

    @classmethod
    def get_all(cls, project_id: str | None = None) -> List[Self]:
        """
        Get all interpolated functions in a project.
        """
        all_expressions = SharedExpression.get_all(project_id=project_id)
        return [
            cls(expr._project_id, expr._shared_expression)
            for expr in all_expressions
            if expr.type == ExpressionType.INTERPOLATED_FUNCTION.value
        ]

    @classmethod
    def get_by_name(cls, name: str, project_id: str | None = None) -> Self | None:
        """
        Get an interpolated function by its name.
        Returns None if no interpolated function matches the given name.

        Parameters:
            name: The name of the interpolated function.
            project_id: The ID of the project.

        Returns:
            The interpolated function that matches the given name.
        """
        all_interpolated_functions = cls.get_all(project_id=project_id)
        matching_interpolated_functions = [
            func for func in all_interpolated_functions if func.name == name
        ]
        if len(matching_interpolated_functions) == 0:
            return None
        if len(matching_interpolated_functions) > 1:
            raise ValueError(f"Multiple interpolated functions found with name {name}")
        return matching_interpolated_functions[0]
