import abc as _abc
from typing import Generic as _Gen, TypeVar as _GenVar, Type as _type

from ._utils import *
from .. import _tokens as _t, OpCodes as _Byte
from ...utils import vals as _v

_T = _GenVar("_T", bound=_t.Token)


class PrefixRule(_Gen[_T], _abc.ABC):
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
    def parse(self, parser: Consumer, token: _T, allowed_assignment: bool):
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


class NumberRule(PrefixRule[_t.BaseNumToken]):
    """
    Concrete rule for parsing number literals in any base.

    Bound Generics
    --------------
    _E: NumberExpr

    _T: BaseNumToken
    """

    def parse(self, parser: Consumer, token: _t.BaseNumToken, allowed_assignment: bool):
        parser.emit(_Byte.CONSTANT, parser.chunk.add(_v.Number(token.value)))


class UnaryOperatorRule(PrefixRule[_t.Token]):
    """
    Concrete rule for parsing any unary operator.

    Bound Generics
    --------------
    _E: UnaryExpr

    _T: Token
    """

    def parse(self, parser: Consumer, token: _t.Token, allowed_assignment: bool):
        parser.expr(self.get_precedence())
        if token.token_type == _t.TokenType.NEG:
            parser.emit(_Byte.NEGATE)
        elif token.token_type == _t.TokenType.INV:
            parser.emit(_Byte.INVERT)


class GroupRule(PrefixRule[_t.Token]):
    """
    Concrete rule for parsing a grouped expression.

    Bound Generics
    --------------
    _E: GroupExpr

    _T: Token
    """

    def parse(self, parser: Consumer, token: _t.Token, allowed_assignment: bool):
        parser.expr()
        parser.consume_type(_t.TokenType.END_CALL, "Expected {lookup} to end grouping")


class KeywordRule(PrefixRule[_t.KeywordToken]):
    """
    Concrete rule for parsing a grouped expression.

    Bound Generics
    --------------
    _E: GroupExpr

    _T: Token
    """

    def parse(self, parser: Consumer, token: _t.KeywordToken, allowed_assignment: bool):
        if token.keyword_type == _t.KeywordType.ON:
            parser.emit(_Byte.TRUE)
        elif token.keyword_type == _t.KeywordType.OFF:
            parser.emit(_Byte.FALSE)
        elif token.keyword_type == _t.KeywordType.NULL:
            parser.emit(_Byte.NULL)


class CharRule(PrefixRule[_t.StringToken]):

    def __init__(self, cls: _type[_v.Value[str]]):
        self._cls = cls

    def parse(self, parser: Consumer, token: _t.Token, allowed_assignment: bool):
        src = token.raw if isinstance(token, _t.StringToken) else token.src
        parser.emit(_Byte.CONSTANT, parser.chunk.add(self._cls(src)))


class VarRule(PrefixRule[_t.IdentifierToken]):

    def parse(self, parser: Consumer, token: _t.IdentifierToken, allowed_assignment: bool):
        self.parse_var(parser, token, allowed_assignment)

    @classmethod
    def parse_var(cls, parser: Consumer, token: _t.IdentifierToken, allowed_assignment: bool):
        if (constant := cls.resolve(parser, token)) != -1:
            get, set_ = _Byte.GET_LOCAL, _Byte.SET_LOCAL
        else:
            constant = parser.chunk.add(_v.String(token.src))
            get, set_ = _Byte.GET_GLOBAL, _Byte.SET_GLOBAL
        if allowed_assignment and parser.match(_t.TokenType.ASSIGN):
            parser.expr()
            code = set_
        else:
            code = get
        parser.emit(code, constant)

    @classmethod
    def resolve(cls, parser: Consumer, token: _t.IdentifierToken) -> int:
        for i, local in parser.compiler.iterate():
            if local.name.src == token.src:
                if local.depth == -1:
                    parser.error("Cannot read local variable in its own initializer")
                return i
        return -1


class ListRule(PrefixRule[_t.Token]):

    def parse(self, parser: Consumer, token: _T, allowed_assignment: bool):
        array = parser.chunk.add(_v.Array())
        parser.emit(_Byte.CONSTANT, array)
        while not parser.match(_t.TokenType.END_LIST):
            parser.expr()
            parser.emit(_Byte.DEF_ELEM, array)
            if not parser.check(_t.TokenType.END_LIST):
                parser.consume_type(_t.TokenType.SEPARATE, "Expected {lookup} between elements")
