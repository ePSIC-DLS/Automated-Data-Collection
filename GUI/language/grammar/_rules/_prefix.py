import abc as _abc
from typing import TypeVar as _GenVar, Generic as _Gen, Tuple as _tuple, List as _list

from ._utils import *
from .. import _tokens as _t, _nodes as _n

_T = _GenVar("_T", bound=_t.Token)
_E = _GenVar("_E", bound=_n.Expr)


class PrefixRule(_Gen[_E, _T], _abc.ABC):
    """
    Abstract base class for all rules that happen at the start of parsing.

    Generics
    --------
    _E: Expr
        The expression type returned.
    _T: Token
        The token type previously consumed. Is usually the type of expression (as Expr is generic itself)

    Abstract Methods
    ----------------
    parse
    """

    @_abc.abstractmethod
    def parse(self, parser: Consumer, token: _T) -> _E:
        """
        Parse this particular rule into a valid expression.

        Parameters
        ----------
        parser: Consumer
            The consumer that can parse tokens.
        token: _T
            The previously consumed token.

        Returns
        -------
        _E
            The expression parsed from the token stream.
        """
        pass

    def get_precedence(self) -> Precedence:
        """
        Find the precedence of this rule.

        Returns
        -------
        Precedence
            The precedence of this rule.
        """
        return Precedence.PREFIX


class VariableRule(PrefixRule[_n.VariableExpr, _t.IdentifierToken]):
    """
    Concrete rule for parsing variable names.

    Bound Generics
    --------------
    _E: VariableExpr

    _T: IdentifierToken
    """

    def parse(self, parser: Consumer, token: _t.IdentifierToken) -> _n.VariableExpr:
        return _n.VariableExpr(token)


class KeywordRule(PrefixRule[_n.KeywordExpr, _t.KeywordToken]):
    """
    Concrete rule for parsing keyword expressions.

    Bound Generics
    --------------
    _E: KeywordExpr

    _T: KeywordToken
    """

    def parse(self, parser: Consumer, token: _t.KeywordToken) -> _n.KeywordExpr:
        return _n.KeywordExpr(token)


class NumberRule(PrefixRule[_n.NumberExpr, _t.BaseNumToken]):
    """
    Concrete rule for parsing number literals in any base.

    Bound Generics
    --------------
    _E: NumberExpr

    _T: BaseNumToken
    """

    def parse(self, parser: Consumer, token: _t.BaseNumToken) -> _n.NumberExpr:
        return _n.NumberExpr(token)


class StringRule(PrefixRule[_n.StringExpr, _t.StringToken]):
    """
    Concrete rule for parsing string literals.

    Bound Generics
    --------------
    _E: StringExpr

    _T: StringToken
    """

    def parse(self, parser: Consumer, token: _t.StringToken) -> _n.StringExpr:
        return _n.StringExpr(token)


class PathRule(PrefixRule[_n.PathExpr, _t.PathToken]):
    """
    Concrete rule for parsing path literals.

    Bound Generics
    --------------
    _E: PathExpr

    _T: PathToken
    """

    def parse(self, parser: Consumer, token: _t.PathToken) -> _n.PathExpr:
        return _n.PathExpr(token)


class ListRule(PrefixRule[_n.CollectionExpr, _t.Token]):
    """
    Concrete rule for parsing collection literals.

    Bound Generics
    --------------
    _E: CollectionExpr

    _T: Token
    """

    def parse(self, parser: Consumer, token: _t.Token) -> _n.CollectionExpr:
        return _n.CollectionExpr(token, *self.group(parser, _t.TokenType.END_LIST, "Array elements"))

    @staticmethod
    def group(parser: Consumer, end: _t.TokenType, context: str) -> _list[_n.Expr]:
        """
        Method that actually parses individual elements.

        Parameters
        ----------
        parser: Consumer
            The consumer that can parse tokens.
        end: TokenType
            The token that should be parsed to indicate the end of parsing.
        context: str
            The expression context.

        Returns
        -------
        list[Expr]
            The expressions parsed.
        """
        items = []
        while not parser.match(end):
            items.append(parser.expr())
            if not parser.check(end):
                parser.consume(_t.TokenType.SEPARATE, f"Expected {{lookup}} between {context}")
        return items


class UnaryOperatorRule(PrefixRule[_n.UnaryExpr, _t.Token]):
    """
    Concrete rule for parsing any unary operator.

    Bound Generics
    --------------
    _E: UnaryExpr

    _T: Token
    """

    def parse(self, parser: Consumer, token: _t.Token) -> _n.UnaryExpr:
        return _n.UnaryExpr(token, parser.expr(self.get_precedence()))


class GroupRule(PrefixRule[_n.GroupExpr, _t.Token]):
    """
    Concrete rule for parsing a grouped expression.

    Bound Generics
    --------------
    _E: GroupExpr

    _T: Token
    """

    def parse(self, parser: Consumer, token: _t.Token) -> _n.GroupExpr:
        group = _n.GroupExpr(token, parser.expr())
        parser.consume(_t.TokenType.END_CALL, "Expected {lookup} to end grouping")
        return group

    def get_precedence(self) -> Precedence:
        return Precedence.GROUP
