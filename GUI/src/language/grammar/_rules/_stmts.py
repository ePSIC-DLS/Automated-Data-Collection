import abc as _abc

from ._utils import *
from ._prefix import VarRule
from .. import _tokens as _t, OpCodes as _Byte, _predicates as _p
from ...utils import vals as _v


class StmtRule(_abc.ABC):
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
    def parse(self, parser: Consumer, token: _t.KeywordToken):
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

    def get_precedence(self) -> Precedence:
        """
        Find the precedence of this rule.

        Returns
        -------
        Precedence
            The precedence of this rule.
        """
        return Precedence.STATEMENT


class VarDef(StmtRule):

    def parse(self, parser: Consumer, token: _t.KeywordToken):
        var = self.parse_var(parser, "Expected variable name")
        parser.consume_type(_t.TokenType.ASSIGN, "Expected {lookup} to assign values to variables")
        parser.expr()
        self.def_var(parser, var)

    def get_precedence(self) -> Precedence:
        return Precedence.DECLARATION

    @classmethod
    def parse_var(cls, parser: Consumer, message: str) -> int:
        string = parser.consume(_t.IdentifierToken, message).src
        cls.dec_var(parser)
        if parser.compiler.scope_depth > 0:
            return 0
        return parser.chunk.add(_v.String(string))

    @classmethod
    def def_var(cls, parser: Consumer, var: int):
        if parser.compiler.scope_depth > 0:
            parser.compiler.mark()
            return
        parser.emit(_Byte.DEF_GLOBAL, var)

    @classmethod
    def dec_var(cls, parser: Consumer):
        if parser.compiler.scope_depth == 0:
            return
        name = parser.peek(0)
        c_depth = parser.compiler.scope_depth
        for local in parser.compiler:
            if local.depth != -1 and local.depth < c_depth:
                break
            if local.name.src == name.src:
                parser.error(f"Already a variable called {name.src!r} in this scope")
        cls.add_local(parser.compiler, name)

    @classmethod
    def add_local(cls, cmp: Compiler, name: _t.Token):
        cmp.add_local(cmp.Local(name, -1))


class LoopStmt(StmtRule):

    def parse(self, parser: Consumer, token: _t.KeywordToken):
        with parser.compiler:
            parser.consume_type(_t.TokenType.START_CALL, "Expected {lookup} to start loop clauses")
            self.init(parser)
            parser.consume_type(_t.TokenType.SEPARATE, "Expected {lookup} between clauses")

            start = len(parser.chunk)
            parser.expr()
            parser.consume_type(_t.TokenType.SEPARATE, "Expected {lookup} between clauses")
            exit_ = parser.emit_jump(_Byte.FALSEY_JUMP)
            parser.emit(_Byte.POP)

            body = parser.emit_jump(_Byte.ALWAYS_JUMP)
            incr = len(parser.chunk)
            parser.expr()
            parser.emit(_Byte.POP)

            parser.consume_type(_t.TokenType.END_CALL, "Expected {lookup} to end loop clauses")
            parser.emit_loop(start)
            parser.patch_jump(body)

            parser.consume_type(_t.TokenType.START_BLOCK, "Expected {lookup} to begin a loop")
            parser.block()
            parser.emit_loop(incr)
            parser.patch_jump(exit_)

    @classmethod
    def init(cls, parser: Consumer):
        parser.consume(_t.KeywordToken, "Expected {filter} for the loop variable",
                       predicate=_p.KeywordPredicate(_t.KeywordType.VAR_DEF))
        var = VarDef.parse_var(parser, "Expected loop variable name")
        parser.consume_type(_t.TokenType.ASSIGN, "Expected {lookup} to assign values to variables")
        parser.expr()
        VarDef.def_var(parser, var)


class IterableStmt(StmtRule):

    def parse(self, parser: Consumer, token: _t.KeywordToken):
        with parser.compiler:
            parser.consume_type(_t.TokenType.START_CALL, "Expected {lookup} to start loop clauses")
            LoopStmt.init(parser)
            last = len(parser.compiler)
            advance_check = len(parser.chunk)
            parser.emit(_Byte.ADVANCE)
            parser.emit(_Byte.SET_LOCAL, last)
            parser.consume_type(_t.TokenType.END_CALL, "Expected {lookup} to end loop clauses")
            parser.consume_type(_t.TokenType.START_BLOCK, "Expected {lookup} to begin a loop")
            parser.block()
            parser.emit_loop(advance_check)


class FunctionStmt(StmtRule):

    def parse(self, parser: Consumer, token: _t.KeywordToken):
        if parser.compiler.type != FuncType.SCRIPT:
            parser.error("Function nesting is not supported")
            return
        glob_var = VarDef.parse_var(parser, "Expected function name")
        parser.compiler.mark()
        self.func(parser, FuncType.FUNCTION)
        VarDef.def_var(parser, glob_var)

    def get_precedence(self) -> Precedence:
        return Precedence.DECLARATION

    @classmethod
    def func(cls, parser: Consumer, ty: FuncType):
        parser.compiler = Compiler(parser, ty, parser.compiler)
        parser.compiler.begin()
        parser.consume_type(_t.TokenType.START_CALL, "Expected {lookup} to start parameter definition")
        while not parser.match(_t.TokenType.END_CALL):
            parser.compiler.function.add_param()
            VarDef.def_var(parser, VarDef.parse_var(parser, "Expected parameter name"))
            if not parser.check(_t.TokenType.END_CALL):
                parser.consume_type(_t.TokenType.SEPARATE, "Expected {lookup} between parameters")
        parser.consume_type(_t.TokenType.START_BLOCK, "Expected {lookup} to begin function block")
        parser.block()
        fn = parser.pop()
        parser.emit(_Byte.CONSTANT, parser.chunk.add(fn))


class IterDecl(StmtRule):

    def parse(self, parser: Consumer, token: _t.KeywordToken):
        if parser.compiler.type != FuncType.SCRIPT:
            parser.error("Generator nesting is not supported")
            return
        glob_var = VarDef.parse_var(parser, "Expected generator name")
        parser.compiler.mark()
        FunctionStmt.func(parser, FuncType.GENERATOR)
        VarDef.def_var(parser, glob_var)

    def get_precedence(self) -> Precedence:
        return Precedence.DECLARATION


class ReturnRule(StmtRule):

    def parse(self, parser: Consumer, token: _t.KeywordToken):
        if parser.compiler.type == FuncType.SCRIPT:
            parser.error("Can only return from inside functions")
            return
        byte = _Byte.RETURN if parser.compiler.type == FuncType.FUNCTION else _Byte.YIELD
        if parser.check(_t.TokenType.EOL):
            parser.emit_return(byte)
        else:
            parser.expr()
            parser.emit(byte)


class WaitRule(StmtRule):

    def parse(self, parser: Consumer, token: _t.KeywordToken):
        parser.expr()
        parser.emit(_Byte.SLEEP)


class KeywordStmt(StmtRule):

    def parse(self, parser: Consumer, token: _t.KeywordToken):
        if token.keyword_type == _t.KeywordType.SURVEY:
            parser.emit(_Byte.SCAN)
        elif token.keyword_type == _t.KeywordType.SEGMENT:
            parser.emit(_Byte.CLUSTER)
        elif token.keyword_type == _t.KeywordType.FILTER:
            parser.emit(_Byte.FILTER)
        elif token.keyword_type == _t.KeywordType.INTERACT:
            parser.emit(_Byte.MARK)
        elif token.keyword_type == _t.KeywordType.MANAGE:
            parser.emit(_Byte.TIGHTEN)
        elif token.keyword_type == _t.KeywordType.SCAN:
            parser.emit(_Byte.SEARCH)


class EnumDecl(StmtRule):

    def parse(self, parser: Consumer, token: _t.KeywordToken):
        if parser.compiler.type != FuncType.SCRIPT:
            parser.error("Enumeration nesting is not supported")
        enum = parser.consume(_t.IdentifierToken, "Expected enum name")
        name = parser.chunk.add(_v.String(enum.src))
        VarDef.dec_var(parser)
        parser.emit(_Byte.ENUM, name)
        VarDef.def_var(parser, name)
        VarRule.parse_var(parser, enum, False)
        parser.consume_type(_t.TokenType.START_BLOCK, "Expected {lookup} to start enumeration definition")
        while not parser.match(_t.TokenType.END_BLOCK):
            parser.buffer()
            m_name = parser.consume(_t.IdentifierToken, "Expected member name").src
            name = parser.chunk.add(_v.String(m_name))
            parser.emit(_Byte.DEF_FIELD, name)
            parser.buffer()
            if not parser.check(_t.TokenType.END_BLOCK):
                parser.consume_type(_t.TokenType.SEPARATE, "Expected {lookup} between members")
        parser.emit(_Byte.POP)

    def get_precedence(self) -> Precedence:
        return Precedence.DECLARATION
