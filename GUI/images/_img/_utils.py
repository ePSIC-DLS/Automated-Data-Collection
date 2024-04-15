import abc
import functools
import typing
from .._enums import ReferenceBehaviour

try:
    import typing_extensions
except ModuleNotFoundError:
    typing_extensions = typing

P = typing_extensions.ParamSpec("P")


class SupportsCopy(typing.Protocol):
    """
    Protocol for supporting copy operations.
    """

    def copy(self) -> typing_extensions.Self:
        """
        Return a copy of the instance.

        Returns
        -------
        Self
            The deep-copy of the instance.
        """
        pass


T = typing.TypeVar("T", bound=SupportsCopy)


class HasInst(typing.Protocol[T]):
    """
    Protocol for supporting an attribute called `instance`

    Generics
    --------
    T: SupportsCopy
        The instance attribute - it should obey the `SupportsCopy` protocol.

    Attributes
    ----------
    instance: T
    """
    instance: T


Inst = typing.TypeVar("Inst")


class MutateCopy(abc.ABC, typing.Generic[P, T, Inst]):
    """
    Abstract decorator for either mutating data, or copying it.

    Used when a function has two forms - 'reference' form (changes the original) and 'copy' form (acts on a new object)

    Generics
    --------
    **P: Any
        The parameter specification of the wrapped function.
    T: SupportsCopy
        The return value of the wrapped function.
    Inst: Any
        The instance type.

    Attributes
    ----------
    _instance: Inst
        The bound instance.
    _refer: str
        The reference behaviour.
    _copy: str
        The copy behaviour.
    _mutate: Callable[P, T]
        The wrapped mutation function.
    _default: ReferenceBehaviour | None
        The default behaviour when called. If None, cannot call the decorator.
    """
    _instance: Inst
    _refer: str
    _copy: str
    _mutate: typing.Callable[P, T]

    def __init__(self, fn: typing.Callable, default: ReferenceBehaviour = None):
        self._mutate = fn
        self._default = default
        self._name = fn.__name__
        self._instance = None
        functools.update_wrapper(self, fn, assigned=("__module__", "__name__", "__qualname__", "__annotations__"))
        behaviour = "no default behaviour" if default is None else f"default behaviour of {default.name!r}"
        self.__doc__ = (f"A `{type(self).__name__}` function with {behaviour}.\n"
                        f"Note that 'REFER' means {self._refer}; 'COPY' means {self._copy}."
                        f"\n{fn.__doc__}")

    def __get__(self, instance, owner) -> typing_extensions.Self:
        self._instance = instance
        return self

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> typing.Optional[T]:
        """
        Executes the default behaviour of the decorator.

        Parameters
        ----------
        *args: Any
            The arguments to pass to the decorated function. Matches the positional arguments bound in P.
        **kwargs: Any
            The keyword arguments to pass to the decorated function. Matches the keyword arguments bound in P.

        Returns
        -------
        T | None
            The decorated function's return value.

        Raises
        ------
        TypeError
            If the default behaviour is `None`.
        """
        if self._default == ReferenceBehaviour.REFER:
            return self.reference(*args, **kwargs)
        elif self._default == ReferenceBehaviour.COPY:
            return self.copy(*args, **kwargs)
        raise TypeError(f"Property {self._name!r} has no default")

    @abc.abstractmethod
    def reference(self, *args: P.args, **kwargs: P.kwargs) -> typing.Optional[T]:
        """
        How the `REFER` behaviour is executed.

        Parameters
        ----------
        *args: Any
            The arguments to pass to the decorated function. Matches the positional arguments bound in P.
        **kwargs: Any
            The keyword arguments to pass to the decorated function. Matches the keyword arguments bound in P.


        Returns
        -------
        T | None
            The decorated function's return value.

        Raises
        ------
        UnboundLocalError
            If the instance is None.
        """
        pass

    @abc.abstractmethod
    def copy(self, *args: P.args, **kwargs: P.kwargs) -> typing.Optional[T]:
        """
        How the `COPY` behaviour is executed.

        Parameters
        ----------
        *args: Any
            The arguments to pass to the decorated function. Matches the positional arguments bound in P.
        **kwargs: Any
            The keyword arguments to pass to the decorated function. Matches the keyword arguments bound in P.


        Returns
        -------
        T | None
            The decorated function's return value.

        Raises
        ------
        UnboundLocalError
            If the instance is None.
        """
        pass

    @classmethod
    def decorate(cls, *, default: ReferenceBehaviour) -> typing.Callable[[typing.Callable], typing_extensions.Self]:
        """
        Static method for decorating a function. Use this when you want to provide a default.

        Parameters
        ----------
        default: ReferenceBehaviour
            The default behaviour to use.

        Returns
        -------
        Callable[[Callable, Self]
            A callable with only one argument that binds the specified default to the created instance.
        """
        return functools.partial(cls, default=default)


class Reference(MutateCopy[P, T, object], typing.Generic[P, T]):
    """
    A concrete decorator for mutating or copying data.

    In this form, mutate means to return with some reference to the original, and copy means to return with no
    reference to the original.

    Bound Generics
    --------------
    I: object
    """
    _refer = "return a shallow copy (any changes *will* affect the original)"
    _copy = "return a deep copy (any changes *will not* affect the original)"

    def __init__(self, fn: typing.Callable[P, T], default: ReferenceBehaviour = None):
        super().__init__(fn, default)

    def reference(self, *args: P.args, **kwargs: P.kwargs) -> T:
        if self._instance is None:
            raise UnboundLocalError(f"Property {self._name!r} is unbound")
        return self._mutate(self._instance, *args, **kwargs)

    def copy(self, *args: P.args, **kwargs: P.kwargs) -> T:
        return self.reference(*args, **kwargs).copy()


class Mutate(MutateCopy[P, T, HasInst], typing.Generic[P, T]):
    """
    A concrete decorator for mutating or copying data.

    In this form, mutate means to not return but change the original, and copy means to return but not change the
    original.

    Bound Generics
    --------------
    I: object

    Attributes
    ----------
    _mutate: Callable[Concatenate[T, P], None]
        The mutation function. Note that this has no return value, but instead has an initial parameter for the
        `SupportsCopy` instance to act on.
    """
    _refer = "change the original (do not return anything)"
    _copy = "return an edited copy (do not change the original)"
    _mutate: typing.Callable[typing_extensions.Concatenate[T, P], None]

    def __init__(self, fn: typing.Callable[typing_extensions.Concatenate[T, P], None],
                 default: ReferenceBehaviour = None):
        super().__init__(fn, default)

    def reference(self, *args: P.args, **kwargs: P.kwargs) -> None:
        if self._instance is None:
            raise UnboundLocalError(f"Property {self._name!r} is unbound")
        self._mutate(self._instance.instance, *args, **kwargs)

    def copy(self, *args: P.args, **kwargs: P.kwargs) -> T:
        if self._instance is None:
            raise UnboundLocalError(f"Property {self._name!r} is unbound")
        new = self._instance.instance.copy()
        self._mutate(new, *args, **kwargs)
        return new


class BoundMutate(MutateCopy[P, T, HasInst], typing.Generic[P, T]):
    """
    A concrete decorator for mutating or copying data.

    In this form, mutate means to not return but change the original, and copy means to return but not change the
    original.

    Bound Generics
    --------------
    I: object

    Attributes
    ----------
    _mutate: Callable[Concatenate[HasInst[T], P], None]
        The mutation function. Note that this has no return value, but instead has an initial parameter for the
        `SupportsCopy` instance to act on.
    """
    _refer = "change the bound instance's instance (do not return anything)"
    _copy = "return an edited copy (do not change the bound instance's instance)"
    _mutate: typing.Callable[typing_extensions.Concatenate[HasInst[T], P], None]

    def __init__(self, fn: typing.Callable[typing_extensions.Concatenate[HasInst[T], P], None],
                 default: ReferenceBehaviour = None):
        super().__init__(fn, default)

    def reference(self, *args: P.args, **kwargs: P.kwargs) -> None:
        if self._instance is None:
            raise UnboundLocalError(f"Property {self._name!r} is unbound")
        self._mutate(self._instance, *args, **kwargs)

    def copy(self, *args: P.args, **kwargs: P.kwargs) -> T:
        old = self._instance.instance
        self._instance.instance = old.copy()
        self.reference(*args, **kwargs)
        new = self._instance.instance
        self._instance.instance = old
        return new
