import enum
import typing
from sys import stderr
from typing import Dict as _dict, Optional as _None, Type as _type

from ..grammar import OpCodes, OpCodes as _Byte, Precedence, Predicate, rules, tokens
from ..utils import Chunk, vals, objs

_T = typing.TypeVar("_T", bound=tokens.Token)


class TokenLandMark(enum.Enum):
    PREVIOUS = enum.auto()
    CURRENT = enum.auto()


class Parser(rules.Consumer):

    @property
    def chunk(self) -> Chunk:
        return self._compiler.function.raw

    @property
    def compiler(self) -> rules.Compiler:
        return self._compiler

    @compiler.setter
    def compiler(self, compiler: rules.Compiler):
        self._compiler = compiler
        if compiler.type != rules.FuncType.SCRIPT:
            compiler.function.set_name(self.peek(0).src)

    @property
    def errored(self) -> bool:
        return self._error

    def __init__(self, *stream: tokens.Token, output: typing.Callable[[str], str]):
        self._print = output
        self._tokens = stream
        self._i = 0
        self._error = self._panic = False
        self._compiler = rules.Compiler(self, rules.FuncType.SCRIPT)
        self._pre_syms: _dict[tokens.TokenType, rules.PrefixRule] = {
            tokens.TokenType.NUM: rules.NumberRule(), tokens.TokenType.STRING: rules.CharRule(vals.String),
            tokens.TokenType.PATH: rules.CharRule(vals.Path), tokens.TokenType.IDENTIFIER: rules.VarRule(),
            tokens.TokenType.NEG: rules.UnaryOperatorRule(), tokens.TokenType.INV: rules.UnaryOperatorRule(),
            tokens.TokenType.START_CALL: rules.GroupRule(), tokens.TokenType.START_LIST: rules.ListRule()
        }
        self._post_syms: _dict[tokens.TokenType, rules.InfixRule] = {
            tokens.TokenType.POW: rules.BinaryOperatorRule(rules.Precedence.EXPONENT),
            tokens.TokenType.NEG: rules.BinaryOperatorRule(rules.Precedence.TERM),
            tokens.TokenType.PLUS: rules.BinaryOperatorRule(rules.Precedence.TERM),
            tokens.TokenType.COMBINE: rules.BinaryOperatorRule(rules.Precedence.TERM),
            tokens.TokenType.EQ: rules.BinaryOperatorRule(rules.Precedence.CMP),
            tokens.TokenType.NEQ: rules.BinaryOperatorRule(rules.Precedence.CMP),
            tokens.TokenType.LT: rules.BinaryOperatorRule(rules.Precedence.CMP),
            tokens.TokenType.GT: rules.BinaryOperatorRule(rules.Precedence.CMP),
            tokens.TokenType.LTE: rules.BinaryOperatorRule(rules.Precedence.CMP),
            tokens.TokenType.GTE: rules.BinaryOperatorRule(rules.Precedence.CMP),
            tokens.TokenType.OUTPUT: rules.PrintRule(), tokens.TokenType.START_CALL: rules.CallRule(),
            tokens.TokenType.ACCESS: rules.Get()
        }
        self._pre_words: _dict[tokens.KeywordType, rules.PrefixRule] = {
            tokens.KeywordType.ON: rules.KeywordRule(), tokens.KeywordType.OFF: rules.KeywordRule(),
            tokens.KeywordType.NULL: rules.KeywordRule(), tokens.KeywordType.D_CORRECT: rules.CharRule(vals.Correction),
            tokens.KeywordType.E_CORRECT: rules.CharRule(vals.Correction),
            tokens.KeywordType.F_CORRECT: rules.CharRule(vals.Correction),
            tokens.KeywordType.L1_NORM: rules.CharRule(vals.Algorithm),
            tokens.KeywordType.L2_NORM: rules.CharRule(vals.Algorithm),
            tokens.KeywordType.LP_NORM: rules.CharRule(vals.Algorithm)
        }
        self._post_words: _dict[tokens.KeywordType, rules.InfixRule] = {

        }
        self._stmts: _dict[tokens.KeywordType, rules.StmtRule] = {
            tokens.KeywordType.VAR_DEF: rules.VarDef(), tokens.KeywordType.LOOP_RANGE: rules.LoopStmt(),
            tokens.KeywordType.FUNC_DEF: rules.FunctionStmt(), tokens.KeywordType.EXIT: rules.ReturnRule(),
            tokens.KeywordType.DELAY: rules.WaitRule(), tokens.KeywordType.SURVEY: rules.KeywordStmt(),
            tokens.KeywordType.SEGMENT: rules.KeywordStmt(), tokens.KeywordType.FILTER: rules.KeywordStmt(),
            tokens.KeywordType.INTERACT: rules.KeywordStmt(), tokens.KeywordType.MANAGE: rules.KeywordStmt(),
            tokens.KeywordType.SCAN: rules.KeywordStmt(), tokens.KeywordType.GEN_DEF: rules.IterDecl(),
            tokens.KeywordType.LOOP_ITER: rules.IterableStmt(), tokens.KeywordType.ENUM_DEF: rules.EnumDecl()
        }

    def _error_at(self, token: typing.Union[tokens.Token, TokenLandMark], message: str) -> None:
        if self._panic:
            return
        if token == TokenLandMark.CURRENT:
            self._error_at(self.peek(), message)
            return
        elif token == TokenLandMark.PREVIOUS:
            self._error_at(self.peek(0), message)
            return

        loc = token.rc_ref if token.token_type != tokens.TokenType.EOF else "end"
        self._print(f"Syntax Error: {message} at {loc}")
        self._error = self._panic = True

    def _sync(self):
        self._panic = False
        while (token := self.peek()).token_type != tokens.TokenType.EOF:
            if self.peek(0).token_type == tokens.TokenType.EOL:
                return
            elif isinstance(token, tokens.KeywordToken):
                if token.keyword_type in {
                    tokens.KeywordType.SURVEY, tokens.KeywordType.SEGMENT, tokens.KeywordType.FILTER,
                    tokens.KeywordType.INTERACT, tokens.KeywordType.MANAGE, tokens.KeywordType.SCAN,
                    tokens.KeywordType.VAR_DEF, tokens.KeywordType.FUNC_DEF, tokens.KeywordType.GEN_DEF,
                    tokens.KeywordType.LOOP_RANGE, tokens.KeywordType.LOOP_ITER, tokens.KeywordType.DELAY,
                    tokens.KeywordType.EXIT,
                }:
                    return
            self.advance()

    def run(self) -> _None[objs.Function]:
        while self.peek().token_type != tokens.TokenType.EOF:
            self._scan()
        func = self.pop()
        return func if not self._error else None

    def pop(self) -> objs.Function:
        func = self._compiler.function
        self._compiler.pop()
        self._compiler = self._compiler.enclosing
        return func

    def _scan(self):
        self.buffer()
        self._decl()

    def buffer(self):
        while self.check(tokens.TokenType.EOL):
            self.advance()

    def error(self, msg: str):
        self._error_at(TokenLandMark.PREVIOUS, msg)

    def emit(self, *code: typing.Union[int, OpCodes]):
        self.chunk.write(*code, line=self.peek(0).position[0])

    def emit_return(self, byte=OpCodes.RETURN):
        self.emit(OpCodes.NULL)
        self.emit(byte)

    def emit_jump(self, instruction: _Byte) -> int:
        self.emit(instruction, 0xFFFF)
        return len(self.chunk) - 1

    def patch_jump(self, index: int):
        jump = len(self.chunk) - index - 1
        self.chunk[index] = jump

    def emit_loop(self, start: int):
        offset = len(self.chunk) - start + 2
        self.emit(OpCodes.LOOP, offset)

    def peek(self, by=1) -> tokens.Token:
        by -= 1
        try:
            return self._tokens[self._i + by]
        except IndexError:
            return self._tokens[-1]

    def advance(self) -> tokens.Token:
        self._i += 1
        return self.peek(0)

    def check(self, *expected: tokens.TokenType, predicate: Predicate = None) -> bool:
        token = self.peek()
        for exp in expected:
            if token.token_type != exp:
                return False
        return predicate is None or predicate(token)

    def match(self, *expected: tokens.TokenType, predicate: Predicate = None) -> bool:
        if self.check(*expected, predicate=predicate):
            self.advance()
            return True
        return False

    def consume_type(self, expected: tokens.TokenType, message: str) -> tokens.Token:
        if self.match(expected):
            return self.peek(0)
        message = message.format(lookup=repr(tokens.TYPE_SYMBOLS[expected]))
        self._error_at(TokenLandMark.CURRENT, message)
        return self.peek()

    def consume(self, expected: _type[_T], message: str, *, predicate: Predicate[_T] = None) -> _T:
        curr = self.peek()
        if isinstance(curr, expected) and (predicate is None or predicate(curr)):
            self.advance()
            return curr
        message = message.format(filter=predicate)
        self._error_at(TokenLandMark.CURRENT, message)
        return curr

    def _decl(self):
        self._stmt()
        if not self.check(tokens.TokenType.EOF):
            self.consume_type(tokens.TokenType.EOL, "Expected a {lookup} between statements")
        if self._panic:
            self._sync()

    def _stmt(self):
        token = self.peek()
        if isinstance(token, tokens.KeywordToken):
            parser = self._stmts.get(token.keyword_type)
            if parser is not None:
                self.advance()
                parser.parse(self, token)
                return
        self.expr()
        self.emit(OpCodes.POP)

    def expr(self, precedence: Precedence = None):
        p_val = 0 if precedence is None else precedence.value
        token = self.advance()
        if isinstance(token, tokens.ErrorToken):
            self._error_at(TokenLandMark.PREVIOUS, token.message)
            return
        elif token.token_type in {tokens.TokenType.EOF, tokens.TokenType.EOL}:
            self._error_at(token, "Expected expression")
            return
        if isinstance(token, tokens.KeywordToken):
            parser = self._pre_words.get(token.keyword_type)
            exp_type = f"PAL_KEYWORD_{token.keyword_type.name}"
        else:
            parser = self._pre_syms.get(token.token_type)
            exp_type = f"PAL_{token.token_type.name}"
        if parser is None:
            self._error_at(token, f"Unknown expression {exp_type!r}")
            return
        assign = p_val <= rules.Precedence.ASSIGN.value
        parser.parse(self, token, assign)
        while p_val < self.get_precedence():
            token = self.peek()
            if isinstance(token, tokens.ErrorToken):
                self._error_at(token, token.message)
                return
            if isinstance(token, tokens.KeywordToken):
                parser = self._post_words.get(token.keyword_type)
            else:
                parser = self._post_syms.get(token.token_type)
            self.advance()
            parser.parse(self, token, assign)
            if assign and self.match(tokens.TokenType.ASSIGN):
                self._error_at(TokenLandMark.PREVIOUS, "Invalid assignment target")

    def get_precedence(self) -> int:
        token = self.peek()
        if isinstance(token, tokens.KeywordToken):
            parser = self._post_words.get(token.keyword_type)
        else:
            parser = self._post_syms.get(token.token_type)
        return parser.get_precedence().value if parser is not None else 0

    def block(self):
        while not self.check(tokens.TokenType.END_BLOCK) and not self.check(tokens.TokenType.EOF):
            self.buffer()
            if self.check(tokens.TokenType.END_BLOCK) or self.check(tokens.TokenType.EOF):
                break
            self._decl()
        self.consume_type(tokens.TokenType.END_BLOCK, "Expected {lookup} to end a block")
