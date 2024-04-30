import abc
import inspect
import typing

from ._env import EnvironmentChain
from ._errors import *
from ..grammar import nodes, Token


class Interpreter(nodes.NodeWalker[object], abc.ABC):
    """
    Abstract, bare-bones interpreter.

    It is a node walker, that returns objects, and also tracks position.

    All methods are abstract.

    Attributes
    ----------
    position : str
        The formatted position of the current token.
    token: Token
        The source token from the statement being evaluated.
    """
    position: str
    token: Token

    @abc.abstractmethod
    def assign(self, name: str, value):
        """
        Assign a value to a variable.

        Parameters
        ----------
        name: str
            The variable name.
        value: Any
            The variable value.
        """
        pass

    @abc.abstractmethod
    def evaluate(self, node: nodes.Node) -> object:
        """
        Evaluate a node.

        Parameters
        ----------
        node: Node
            The currently visiting node.

        Returns
        -------
        object
            The evaluated value.
        """
        pass


class Fobj:
    """
    Implements a basic callable to represent function objects.

    Attributes
    ----------
    _src: FunctionStmt
        The source declaration.
    _closure: EnvironmentChain
        The environment chain at declaration, which has access to nonlocal variables.
    """

    @property
    def closure(self) -> EnvironmentChain:
        """
        Public access to the closure.

        Returns
        -------
        EnvironmentChain
            The environment chain at declaration, which has access to nonlocal variables.
        """
        return self._closure

    def __init__(self, src: nodes.FunctionStmt, closure: EnvironmentChain):
        self._src = src
        self._closure = closure

    def __call__(self, interpreter: "Interpreter", *args):
        """
        Evaluate a function call.

        Uses the interpreter to assign values to the parameters, then to execute the statements individually.
        Note that it does not execute the block statement, as that would create a further scope.

        Parameters
        ----------
        interpreter: Interpreter
            The interpreter to use.
        *args: Any
            Any positional arguments.

        Returns
        -------
        Any
            If there is a `Return` error raised, then it returns that value. If not, there is no return.

        Raises
        ------
        RunTimeError
            If the arity differs from the number of arguments.
        """
        if (exp := len(self._src.parameters)) != (acc := len(args)):
            raise RunTimeError(interpreter.token, f"Function expected {exp} argument(s), got {acc}")

        for name, value in zip(self._src.parameters, args):
            interpreter.assign(name.src, value)

        for stmt in self._src.body:
            try:
                interpreter.evaluate(stmt)
            except Return as err:
                return err.value


class Builtin:
    """
    Implements a basic callable to represent native function objects.

    This differs from a `Fobj` in that a `Fobj` will represent functions defined in the language, whereas a `Builtin`
    will represent functions defined in python (the native language).

    Attributes
    ----------
    _src: Callable
        The python function object.
    """

    def __init__(self, shadow: typing.Callable):
        self._src = shadow

    def __call__(self, interpreter: "Interpreter", *args):
        """
        Evaluate a native function call.

        Inputs the interpreter's position, then any evaluated arguments.

        Parameters
        ----------
        interpreter: Interpreter
            The interpreter to use.
        *args: Any
            Any positional arguments.

        Returns
        -------
        Any
            The return value of the native function call.

        Raises
        ------
        TypeError
            If the arity differs from the number of arguments.
        """
        params = inspect.signature(self._src).parameters
        a_l, p_l = len(args), len(params) - 1
        if a_l != p_l:
            raise TypeError(f"Function expected {p_l} argument(s), got {a_l}")
        return self._src(interpreter.position, *args)


class Iter:
    """
    Implements a basic structure to represent generator objects.

    Attributes
    ----------
    _src: FunctionStmt
        The source declaration.
    _closure: EnvironmentChain
        The environment chain at declaration, which has access to nonlocal variables.
    """

    @property
    def closure(self) -> EnvironmentChain:
        """
        Public access to the closure.

        Returns
        -------
        EnvironmentChain
            The environment chain at declaration, which has access to nonlocal variables.
        """
        return self._closure

    def __init__(self, src: nodes.FunctionStmt, closure: EnvironmentChain):
        self._src = src
        self._closure = closure

    def __call__(self, interpreter: "Interpreter", *args):
        """
        Evaluate a function call.

        Uses the interpreter to assign values to the parameters, then to execute the statements individually.
        Note that it does not execute the block statement, as that would create a further scope.

        Parameters
        ----------
        interpreter: Interpreter
            The interpreter to use.
        *args: Any
            Any positional arguments.

        Returns
        -------
        Any
            If there is a `Return` error raised, then it returns that value. If not, there is no return.

        Raises
        ------
        RunTimeError
            If the arity differs from the number of arguments.
        """
        if (exp := len(self._src.parameters)) != (acc := len(args)):
            raise RunTimeError(interpreter.token, f"Function expected {exp} argument(s), got {acc}")

        for name, value in zip(self._src.parameters, args):
            interpreter.assign(name.src, value)

        for stmt in self._src.body:
            try:
                interpreter.evaluate(stmt)
            except Return as err:
                return err.value
