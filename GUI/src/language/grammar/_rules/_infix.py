import abc as _abc
from typing import Generic as _Gen, TypeVar as _GenVar

from ._utils import *
from .. import _tokens as _t, OpCodes as _Byte
from ...utils import vals as _v

_T = _GenVar("_T", bound=_t.Token)


class InfixRule(_Gen[_T], _abc.ABC):
    """
    Abstract base class for all rules that happen in the middle of parsing.

    Generics
    --------
    _T: Token
        The token type previously consumed.

    Abstract Methods
    ----------------
    parse
    get_precedence
    """

    @_abc.abstractmethod
    def parse(self, parser: Consumer, token: _T, allowed_assignment: bool):
        """
        Method for emitting the particular series of instructions that represent this rule.

        Parameters
        ----------
        parser: Consumer
            The consumer that is parsing.
        token: _T
            The token type previously consumed.
        allowed_assignment: bool
            Whether this rule can turn into an assignment (for instance "x.y" can turn into "x.y = 3", but "a * b" can't
            turn into "a * b = 3").
        """
        pass

    @_abc.abstractmethod
    def get_precedence(self) -> Precedence:
        """
        Find the precedence of this rule.

        Returns
        -------
        Precedence
            The precedence of this rule.
        """
        pass


class BinaryOperatorRule(InfixRule[_t.Token]):
    """
    Concrete rule for parsing binary expressions.

    Bound Generics
    --------------
    _T: Token

    Attributes
    ----------
    _p: Precedence
        The precedence of the operation.
    """

    def __init__(self, precedence: Precedence):
        self._p = precedence

    def parse(self, parser: Consumer, right: _t.Token, allowed_assignment: bool):
        parser.expr(self.get_precedence())
        if right.token_type == _t.TokenType.POW:
            parser.emit(_Byte.POWER)
        elif right.token_type == _t.TokenType.PLUS:
            parser.emit(_Byte.ADD)
        elif right.token_type == _t.TokenType.NEG:
            parser.emit(_Byte.SUB)
        elif right.token_type == _t.TokenType.COMBINE:
            parser.emit(_Byte.MIX)
        elif right.token_type == _t.TokenType.EQ:
            parser.emit(_Byte.EQUAL)
        elif right.token_type == _t.TokenType.NEQ:
            parser.emit(_Byte.EQUAL, _Byte.INVERT)
        elif right.token_type == _t.TokenType.LT:
            parser.emit(_Byte.LESS)
        elif right.token_type == _t.TokenType.GT:
            parser.emit(_Byte.MORE)
        elif right.token_type == _t.TokenType.LTE:
            parser.emit(_Byte.MORE, _Byte.INVERT)
        elif right.token_type == _t.TokenType.GTE:
            parser.emit(_Byte.LESS, _Byte.INVERT)

    def get_precedence(self) -> Precedence:
        return self._p


class PrintRule(InfixRule[_t.Token]):
    """
    Concrete rule for parsing postfix print expressions.

    Bound Generics
    --------------
    _T: Token
    """

    def parse(self, parser: Consumer, token: _T, allowed_assignment: bool):
        parser.emit(_Byte.PRINT)

    def get_precedence(self) -> Precedence:
        return Precedence.PREFIX


class CallRule(InfixRule[_t.Token]):
    """
    Concrete rule for parsing infix bracket expressions.

    Bound Generics
    --------------
    _T: Token
    """

    def parse(self, parser: Consumer, token: _T, allowed_assignment: bool):
        parser.emit(_Byte.CALL, self.list(parser))

    def get_precedence(self) -> Precedence:
        return Precedence.CALL

    @classmethod
    def list(cls, parser: Consumer) -> int:
        """
        Static method for collecting a series of expressions into an argument list.

        Parameters
        ----------
        parser: Consumer
            The consumer that is parsing.

        Returns
        -------
        int
            The number of arguments.
        """
        count = 0
        while not parser.match(_t.TokenType.END_CALL):
            parser.expr()
            count += 1
            if not parser.check(_t.TokenType.END_CALL):
                parser.consume_type(_t.TokenType.SEPARATE, "Expected {lookup} between arguments")
        return count


class Get(InfixRule[_t.Token]):
    """
    Concrete rule for parsing infix bracket expressions.

    Bound Generics
    --------------
    _T: Token
    """

    def parse(self, parser: Consumer, token: _T, allowed_assignment: bool):
        name = parser.chunk.add(_v.String(parser.consume(_t.IdentifierToken, "Expected field name").src))
        parser.emit(_Byte.GET_FIELD, name)

    def get_precedence(self) -> Precedence:
        return Precedence.CALL
