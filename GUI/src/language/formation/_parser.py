import abc as _abc
import typing
from typing import Dict as _dict, Union as _Union, Type as _type, overload as _overload
from ..grammar import *

T = typing.TypeVar("T", bound=Token)


class ParserError(Exception):
    """
    Exception raised for syntax errors in the input.
    """

    def __init__(self, cause: ErrorNode):
        super().__init__(str(cause))


class Parser(Consumer):
    """
    Compiler to consume tokens and produce nodes. Uses the parsing rules (matched by token or keyword type).

    Attributes
    ----------
    _stream: tuple[Token, ...]
        The token stream to parse.
    _i: int
        The index of the current token.
    _max_i: int
        The maximum index that the index can parse.
    _pre_syms: dict[TokenType, PrefixRule]
        The prefix rules matched by token type.
    _mix_syms: dict[TokenType, InfixRule]
        The infix rules matched by token type.
    _pre_words: dict[KeywordType, PrefixRule]
        The prefix rules matched by keyword type - this is used when there are specific rules for different keywords.
    _mix_words: dict[KeywordType, InfixRule]
        The infix rules matched by keyword type - this is used when there are specific rules for different keywords.
    _key_stmts: dict[KeywordType, StmtRule]
        The statements matched by keyword type.
    """

    @property
    def finished(self) -> bool:
        """
        Determine if the parser has finished compiling.

        Returns
        -------
        bool
            Whether the maximum index has been reached.
        """
        return self._i >= self._max_i

    def __init__(self, *stream: Token):
        self._stream = stream
        self._i = -1
        self._max_i = len(self._stream) - 2
        self._pre_syms: _dict[TokenType, PrefixRule] = {
            TokenType.STRING: StringRule(), TokenType.NUM: NumberRule(), TokenType.BIN: NumberRule(),
            TokenType.HEX: NumberRule(), TokenType.IDENTIFIER: VariableRule(), TokenType.NEG: UnaryOperatorRule(),
            TokenType.START_LIST: ListRule(), TokenType.START_CALL: GroupRule(), TokenType.PATH: PathRule()
        }
        self._mix_syms: _dict[TokenType, InfixRule] = {
            TokenType.POW: BinaryOperatorRule(Precedence.EXPONENT), TokenType.START_CALL: CallRule(),
            TokenType.ASSIGN: SetRule(), TokenType.ACCESS: GetRule()
        }
        self._pre_words: _dict[KeywordType, PrefixRule] = {
            KeywordType.D_CORRECT: KeywordRule(), KeywordType.E_CORRECT: KeywordRule(),
            KeywordType.F_CORRECT: KeywordRule(), KeywordType.L1_NORM: KeywordRule(),
            KeywordType.L2_NORM: KeywordRule(), KeywordType.LP_NORM: KeywordRule(), KeywordType.ON: KeywordRule(),
            KeywordType.OFF: KeywordRule()
        }
        self._mix_words: _dict[KeywordType, InfixRule] = {

        }
        self._key_stmts: _dict[KeywordType, StmtRule] = {
            KeywordType.VAR_DEF: VarRule(), KeywordType.FUNC_DEF: FuncRule(), KeywordType.LOOP: LoopRule(),
            KeywordType.DELAY: DelayRule(), KeywordType.SURVEY: KeyRule(), KeywordType.SEGMENT: KeyRule(),
            KeywordType.FILTER: KeyRule(), KeywordType.INTERACT: KeyRule(), KeywordType.MANAGE: KeyRule(),
            KeywordType.SCAN: KeyRule(), KeywordType.EXIT: ExitRule()
        }

    def run(self) -> typing.Iterator[Node]:
        """
        Kicks off the parser, telling it to begin compiling.

        As this is an iterator, it allows for node-by-node extraction by repeatedly calling `next`.

        Yields
        ------
        Node
            The node parsed from the particular matching rule.
        """
        while not self.finished:
            self._buffer()
            yield self._scan()

    def _buffer(self):
        while self.match(TokenType.EOL):
            pass

    def _scan(self) -> Node:
        node = self._keyword()
        if not self.finished:
            self.consume(TokenType.EOL, "Expected {lookup} between statements")
        return node

    def _keyword(self) -> Node:
        token = self.peek()
        if isinstance(token, KeywordToken) and token.keyword_type in self._key_stmts:
            self.advance()
            return self._key_stmts[token.keyword_type].parse(self, token)
        return self.expr()

    def expr(self, precedence: Precedence = None) -> Expr:
        p_val = 0 if precedence is None else precedence.value
        token = self.advance()
        if isinstance(token, ErrorToken):
            raise ParserError(ErrorNode(token))
        elif token.token_type in {TokenType.EOF, TokenType.EOL}:
            raise ParserError(ErrorNode.from_unknown_error(token, "Expected expression"))
        if isinstance(token, KeywordToken):
            parser = self._pre_words.get(token.keyword_type)
            exp_type = f"PAL_KEYWORD_{token.keyword_type.name}"
        else:
            parser = self._pre_syms.get(token.token_type)
            exp_type = f"PAL_{token.token_type.name}"
        if parser is None:
            raise ParserError(ErrorNode.from_unknown_error(token, f"Unknown expression {exp_type!r}"))
        left = parser.parse(self, token)
        while p_val < self.get_precedence():
            token = self.peek()
            if isinstance(token, ErrorToken):
                raise ParserError(ErrorNode(token))
            if isinstance(token, KeywordToken):
                parser = self._mix_words.get(token.keyword_type)
            else:
                parser = self._mix_syms.get(token.token_type)
            self.advance()
            left = parser.parse(self, left, token)
        return left

    def block(self) -> BlockStmt:
        start = self.consume(TokenType.START_BLOCK, "Expected {lookup} to define a block")
        items = []
        while not self.match(TokenType.END_BLOCK):
            self._buffer()
            items.append(self._keyword())
            if not self.check(TokenType.END_BLOCK):
                self.consume(TokenType.EOL, "Expected {lookup} between statements")
        return BlockStmt(start, *items)

    def get_precedence(self) -> int:
        token = self.peek()
        if isinstance(token, KeywordToken):
            parser = self._mix_words.get(token.keyword_type)
        else:
            parser = self._mix_syms.get(token.token_type)
        return parser.get_precedence().value if parser is not None else 0

    def advance(self) -> Token:
        self._i += 1
        return self._stream[self._i]

    def peek(self, by=1) -> Token:
        if self._i + by > self._max_i:
            return self._stream[-1]
        return self._stream[self._i + by]

    @_abc.abstractmethod
    @_overload
    def consume(self, expected: _type[T], message: str, *, predicate: Predicate = None) -> T:
        pass

    @_abc.abstractmethod
    @_overload
    def consume(self, expected: TokenType, message: str, *, predicate: Predicate = None) -> Token:
        pass

    def consume(self, expected: _Union[TokenType, _type[T]], message: str, *, predicate: Predicate = None) -> \
            _Union[T, Token]:
        if isinstance(expected, TokenType):
            message = message.replace("{lookup}", repr(TYPE_SYMBOLS[expected]))
        prev = self.peek()
        error: typing.Optional[Token] = None
        if self.match(expected):
            if predicate is None or predicate(prev):
                return prev
            error = prev
        raise ParserError(ErrorNode.from_unknown_error(error or self.advance(), message))

    def match(self, *expected: _Union[TokenType, _type[Token]]) -> bool:
        if self.check(*expected):
            self.advance()
            return True
        return False

    def check(self, *expected: _Union[TokenType, _type[Token]]) -> bool:
        for res in expected:
            if isinstance(res, type):
                if not isinstance(self.peek(), res):
                    return False
            else:
                if self.peek().token_type != res:
                    return False
        return True
