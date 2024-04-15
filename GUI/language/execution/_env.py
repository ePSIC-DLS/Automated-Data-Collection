import typing
from typing import Dict as _dict, Optional as _None


class EnvironmentChain:
    """
    Class to represent a variable environment within an interpreter.

    This is implemented as a chain, allowing for nested environments (such as local variables in functions).

    Attributes
    ----------
    _parent: EnvironmentChain | None
        The outer environment that this environment is attached to.
    _vars: dict[str, object]
        The variables that this environment knows.
    """

    @property
    def parent(self) -> _None["EnvironmentChain"]:
        """
        Public access to the parent environment.

        Returns
        -------
        EnvironmentChain | None
            The outer environment that this environment is attached to.
        """
        return self._parent

    def __init__(self, parent: "EnvironmentChain" = None):
        self._parent = parent
        self._vars: _dict[str, object] = {}

    def __contains__(self, item: str) -> bool:
        return item in self._vars

    def __iter__(self) -> typing.Iterator[object]:
        yield from self._vars.values()

    def __str__(self) -> str:
        return f"{self._vars}"

    def get_at(self, name: str, i=0) -> object:
        """
        Get an environment variable by name. Supports grabbing from nested environments.

        Parameters
        ----------
        name: str
            The name of the variable.
        i: int
            The ancestor index. Use 1 for parent, 2 for grandparent, etc. The default is 0, to represent self.

        Returns
        -------
        object
            The value of the variable.

        Raises
        ------
        NameError
            If the variable name does not exist.
        """
        if i == 0:
            if name not in self._vars:
                raise NameError(f"Variable {name!r} is not defined")
            return self._vars[name]
        return self._ancestor(i).get_at(name)

    def set_at(self, name: str, value: object, i=0, *, create=False):
        """
        Assign an environment variable by name. Supports assigning to nested environments.

        Parameters
        ----------
        name: str
            The name of the variable.
        value: object
            The value to set to.
        i: int
            The ancestor index. Use 1 for parent, 2 for grandparent, etc. The default is 0, to represent self.
        create: bool
            Flag to represent whether a new variable is created, or an existing variable is assigned to.

        Raises
        ------
        NameError
            If the variable name does not exist.
        ValueError
            If the value is None (the language does not support a null value).
        """
        if i == 0:
            if name not in self._vars and not create:
                raise NameError(f"Variable {name!r} is not defined")
            elif value is None:
                raise ValueError(f"Cannot assign a null value")
            self._vars[name] = value
        else:
            self._ancestor(i).set_at(name, value)

    def _ancestor(self, i: int) -> "EnvironmentChain":
        if i <= 0:
            raise ValueError("Invalid parent")
        obj = self
        for _ in range(i):
            obj = obj.parent
        return obj
