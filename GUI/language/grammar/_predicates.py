from ._tokens import *
import abc
import typing

__all__ = ["Predicate", "VariablePredicate", "KeywordPredicate", "IntegerPredicate"]

T = typing.TypeVar("T", bound=Token)


class Predicate(typing.Generic[T], abc.ABC):
    """
    Abstract Base Class to represent any predicate to filter tokens.

    Generics
    --------
    T: Token
        The token type of the predicate.

    Abstract Methods
    ----------------
    __call__
    """

    @abc.abstractmethod
    def __call__(self, t: T) -> bool:
        pass


class VariablePredicate(Predicate[IdentifierToken]):
    """
    Concrete predicate to represent a particular variable name.

    Bound Generics
    --------------
    T: IdentifierToken

    Attributes
    ----------
    _src: str
        The name of the variable.
    """

    def __init__(self, identifier: str):
        self._src = identifier

    def __call__(self, t: IdentifierToken) -> bool:
        """
        Assess whether the token is a particular variable name.

        Parameters
        ----------
        t: IdentifierToken
            The variable token.

        Returns
        -------
        bool
            Whether the lexme of the token is the specified name.
        """
        return self._src == t.src


class KeywordPredicate(Predicate[KeywordToken]):
    """
    Concrete predicate to represent a particular keyword.

    Bound Generics
    --------------
    T: KeywordToken

    Attributes
    ----------
    _keyword_type: KeywordType
        The type of keyword.
    """

    def __init__(self, ty: KeywordType):
        self._keyword_type = ty

    def __call__(self, t: KeywordToken) -> bool:
        """
        Assess whether the token is a particular keyword.

        Parameters
        ----------
        t: KeywordToken
            The keyword token.

        Returns
        -------
        bool
            Whether the token's keyword type is the specified type.
        """
        return self._keyword_type == t.keyword_type


class IntegerPredicate(Predicate[NumToken]):
    """
    Concrete predicate to represent a float being an integer.

    Bound Generics
    --------------
    T: NumToken
    """

    def __call__(self, t: NumToken) -> bool:
        """
        Assess whether the token's value is an integer.

        Parameters
        ----------
        t: NumToken
            The number token.

        Returns
        -------
        bool
            Whether the truncated token value is equal to the full token value.
        """
        return int(t.value) == t.value


class BasePredicate(Predicate[BaseNumToken]):
    """
    Concrete predicate to represent a number being in a particular base.

    Bound Generics
    --------------
    T: BaseNumToken

    Attributes
    ----------
    _base: int
        The base expected
    _map: dict[str, int]
        The mapping from base name to base.
    """

    def __init__(self, base: int):
        self._base = base
        self._map = {v: k for k, v in BaseNumToken.BASE_MAP.items()}

    def __call__(self, t: BaseNumToken) -> bool:
        """
        Assess whether the token's base is expected.

        Parameters
        ----------
        t: BaseNumToken
            The number token.

        Returns
        -------
        bool
            Whether the base of the token is equal to the base expected.
        """
        return t.number_type == self._map[self._base]
