import abc as _abc
from typing import Generic as _Gen, TypeVar as _GenVar

from ._utils import *
from .. import _nodes as _n, _tokens as _t
from ._prefix import VariableRule

_E = _GenVar("_E", bound=_n.Expr)


class StmtRule(_Gen[_E], _abc.ABC):
    """
    Abstract base class for all rules aren't expressions.

    Generics
    --------
    _E: Expr
        The expression type returned.

    Abstract Methods
    ----------------
    parse
    get_precedence
    """

    @_abc.abstractmethod
    def parse(self, parser: Consumer, token: _t.KeywordToken) -> _E:
        """
        Parse this particular rule into a valid statement.

        Parameters
        ----------
        parser: Consumer
            The consumer that can parse tokens.
        token: KeywordToken
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


class KeyRule(StmtRule[_n.KeywordStmt]):
    """
    Concrete rule for parsing keyword statements.

    Bound Generics
    --------------
    _E: KeywordStmt
    """

    def parse(self, parser: Consumer, token: _t.KeywordToken) -> _n.KeywordStmt:
        return _n.KeywordStmt(token)

    def get_precedence(self) -> Precedence:
        return Precedence.STATEMENT


class VarRule(StmtRule[_n.VariableStmt]):
    """
    Concrete rule for parsing variable declarations.

    Bound Generics
    --------------
    _E: VariableStmt
    """

    def parse(self, parser: Consumer, token: _t.KeywordToken) -> _n.VariableStmt:
        name = parser.consume(_t.IdentifierToken, "Expected a variable name")
        parser.consume(_t.TokenType.ASSIGN, "Expected {lookup} to set a value")
        return _n.VariableStmt(name, parser.expr())

    def get_precedence(self) -> Precedence:
        return Precedence.DECLARATION


class FuncRule(StmtRule[_n.FunctionStmt]):
    """
    Concrete rule for parsing function declarations.

    Bound Generics
    --------------
    _E: FunctionStmt
    """

    def parse(self, parser: Consumer, token: _t.KeywordToken) -> _n.FunctionStmt:
        name = parser.consume(_t.IdentifierToken, "Expected a variable name")
        parser.consume(_t.TokenType.START_CALL, "Expected {lookup} to specify parameters")
        items = []
        while not parser.match(_t.TokenType.END_CALL):
            items.append(VariableRule().parse(parser, parser.consume(_t.IdentifierToken, "Expected a parameter name")))
            if not parser.check(_t.TokenType.END_CALL):
                parser.consume(_t.TokenType.SEPARATE, "Expected {lookup} between elements")
        return _n.FunctionStmt(name, tuple(expr.src for expr in items), parser.block())

    def get_precedence(self) -> Precedence:
        return Precedence.DECLARATION


class LoopRule(StmtRule[_n.LoopStmt]):
    """
    Concrete rule for parsing iteration statements.

    Bound Generics
    --------------
    _E: LoopStmt
    """

    def parse(self, parser: Consumer, token: _t.KeywordToken) -> _n.LoopStmt:
        if not parser.check(_t.TokenType.START_BLOCK):
            amount = parser.expr()
        else:
            amount = None
        code = parser.block()
        return _n.LoopStmt(token, code, amount)

    def get_precedence(self) -> Precedence:
        return Precedence.STATEMENT


class DelayRule(StmtRule[_n.SleepStmt]):
    """
    Concrete rule for parsing delay statements.

    Bound Generics
    --------------
    _E: SleepStmt
    """

    def parse(self, parser: Consumer, token: _t.KeywordToken) -> _n.SleepStmt:
        delay = parser.expr()
        return _n.SleepStmt(token, delay)

    def get_precedence(self) -> Precedence:
        return Precedence.STATEMENT


class ExitRule(StmtRule[_n.ReturnStmt]):
    """
    Concrete rule for parsing return statements.

    Bound Generics
    --------------
    _E: ReturnStmt
    """

    def parse(self, parser: Consumer, token: _t.KeywordToken) -> _n.ReturnStmt:
        if not parser.check(_t.TokenType.EOL):
            expr = parser.expr()
        else:
            expr = None
        return _n.ReturnStmt(token, expr)

    def get_precedence(self) -> Precedence:
        return Precedence.STATEMENT
