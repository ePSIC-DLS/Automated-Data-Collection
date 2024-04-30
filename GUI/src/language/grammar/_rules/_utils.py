import abc as _abc
from enum import Enum as _Base, auto as _member
from typing import overload as _overload, Type as _type, TypeVar as _GenVar, Union as _Union

from .. import _tokens as _t, _predicates as _p, _nodes as _n

_T = _GenVar("_T", bound=_t.Token)


class Precedence(_Base):
    """
    Enumeration for the precedence of nodes.

    Members
    -------
    DECLARATION

    STATEMENT

    GROUP

    ASSIGN

    EXPONENT

    PREFIX

    CALL

    """
    DECLARATION = _member()
    STATEMENT = _member()
    GROUP = _member()
    ASSIGN = _member()
    EXPONENT = _member()
    PREFIX = _member()
    CALL = _member()


class Consumer(_abc.ABC):
    """
    Abstract class for a consumer that will analyse a token stream and return an AST.

    All methods are abstract.
    """

    @_abc.abstractmethod
    def expr(self, precedence: Precedence = None) -> _n.Expr:
        """
        Method to parse an expression of a particular precedence.

        Parameters
        ----------
        precedence: Precedence | None
            The precedence level required.

        Returns
        -------
        Expr
            The expression found.
        """
        pass

    @_abc.abstractmethod
    def block(self) -> _n.BlockStmt:
        """
        Method to parse a block of code.

        Returns
        -------
        BlockStmt
            The parsed block.
        """
        pass

    @_abc.abstractmethod
    def advance(self) -> _t.Token:
        """
        Progress the consumer by one token.

        Returns
        -------
        Token
            The token just parsed.
        """
        pass

    @_abc.abstractmethod
    def peek(self, by=1) -> _t.Token:
        """
        View (but don't progress the consumer) by a certain number of tokens.

        Parameters
        ----------
        by: int
            The number of tokens to step by. Default is 1.

        Returns
        -------
        Token
            The observed token.
        """
        pass

    @_abc.abstractmethod
    def get_precedence(self) -> Precedence:
        """
        Find the precedence of the current expression.

        Returns
        -------
        Precedence
            The precedence of the current expression.
        """
        pass

    @_abc.abstractmethod
    @_overload
    def consume(self, expected: _type[_T], message: str, *, predicate: _p.Predicate = None) -> _T:
        pass

    @_abc.abstractmethod
    @_overload
    def consume(self, expected: _t.TokenType, message: str, *, predicate: _p.Predicate = None) -> _t.Token:
        pass

    @_abc.abstractmethod
    def consume(self, expected: _Union[_t.TokenType, _type[_T]], message: str, *,
                predicate: _p.Predicate = None) -> _Union[_t.Token, _T]:
        """
        Consume a particular type, that follows a particular predicate.

        Generics
        --------
        _T: Token
            The type of token to parse.

        Parameters
        ----------
        expected: Token | type[_T]
            The expected token type. Use an actual subclass of Token to guarantee that subclass as output.
        message: str
            The error message if that type is not found.
        predicate: Predicate
            The additional filter to apply to the token.

        Returns
        -------
        Token | _T
            The consumed token. Note that when an actual subclass is provided, then a token of that type is returned.
        """
        pass

    @_abc.abstractmethod
    def match(self, *expected: _Union[_t.TokenType, _type[_t.Token]]) -> bool:
        """
        Parse a series of matches.

        This will advance past the consumed token.

        Parameters
        ----------
        *expected: TokenType | type[Token]
            The expected types. Any of these can match.

        Returns
        -------
        bool
            Whether the token was consumed.
        """
        pass

    @_abc.abstractmethod
    def check(self, *expected: _Union[_t.TokenType, _type[_t.Token]]) -> bool:
        """
        Parse a series of matches.

        This will not advance past the consumed token.

        Parameters
        ----------
        *expected: TokenType | type[Token]
            The expected types. Any of these can match.

        Returns
        -------
        bool
            Whether the token is found.
        """
        pass
