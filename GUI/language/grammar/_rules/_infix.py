import abc as _abc
from typing import TypeVar as _GenVar, Generic as _Gen

from ._utils import *
from ._prefix import ListRule
from .. import _tokens as _t, _nodes as _n

_T = _GenVar("_T", bound=_t.Token)
_E = _GenVar("_E", bound=_n.Expr)


class InfixRule(_Gen[_E, _T], _abc.ABC):
    """
    Abstract base class for all rules that happen in the middle of parsing.

    Generics
    --------
    _E: Expr
        The expression type returned.
    _T: Token
        The token type previously consumed. Is usually the type of expression (as Expr is generic itself)

    Abstract Methods
    ----------------
    parse
    get_precedence
    """

    @_abc.abstractmethod
    def parse(self, parser: Consumer, left: _n.Expr, token: _T) -> _E:
        """
        Parse this particular rule into a valid expression.

        Parameters
        ----------
        parser: Consumer
            The consumer that can parse tokens.
        left: Expr
            The expression that comes just before this one.
        token: _T
            The previously consumed token.

        Returns
        -------
        _E
            The expression parsed from the token stream.
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


class BinaryOperatorRule(InfixRule[_n.BinaryExpr, _t.Token]):
    """
    Concrete rule for parsing binary expressions.

    Bound Generics
    --------------
    _E: BinaryExpr

    _T: Token

    Attributes
    ----------
    _p: Precedence
        The precedence of the operation.
    """

    def __init__(self, precedence: Precedence):
        self._p = precedence

    def parse(self, parser: Consumer, left: _n.Expr, right: _t.Token) -> _n.BinaryExpr:
        return _n.BinaryExpr(right, left, parser.expr(self.get_precedence()))

    def get_precedence(self) -> Precedence:
        return self._p


class CallRule(InfixRule[_n.CallExpr, _t.Token]):
    """
    Concrete rule for parsing function calls.

    Bound Generics
    --------------
    _E: CallExpr

    _T: Token
    """

    def parse(self, parser: Consumer, left: _n.Expr, token: _T) -> _n.CallExpr:
        items = ListRule.group(parser, _t.TokenType.END_CALL, "function arguments")
        return _n.CallExpr(left, *items)

    def get_precedence(self) -> Precedence:
        return Precedence.CALL


class SetRule(InfixRule[_n.SetExpr, _t.Token]):
    """
    Concrete rule for parsing assignment expressions.

    Bound Generics
    --------------
    _E: SetExpr

    _T: Token
    """

    def parse(self, parser: Consumer, left: _n.Expr, token: _t.Token) -> _n.SetExpr:
        return _n.SetExpr(token, left, parser.expr(self.get_precedence()))

    def get_precedence(self) -> Precedence:
        return Precedence.ASSIGN


class GetRule(InfixRule[_n.GetExpr, _t.Token]):
    """
    Concrete rule for parsing property access.

    Bound Generics
    --------------
    _E: GetExpr

    _T: Token
    """

    def parse(self, parser: Consumer, left: _n.Expr, token: _t.Token) -> _n.GetExpr:
        return _n.GetExpr(token, left, parser.consume(_t.IdentifierToken, "Expected a valid identifier to access"))

    def get_precedence(self) -> Precedence:
        return Precedence.CALL
