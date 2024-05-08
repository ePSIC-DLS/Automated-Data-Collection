import abc as _abc
from enum import auto as _member, Enum as _Base
from typing import (Iterator as _iter, List as _list, Optional as _None, Tuple as _tuple, Type as _type,
                    TypeVar as _GenVar, Union as _Union)

from .. import _predicates as _p, _tokens as _t, OpCodes as _Byte
from ...utils import Chunk as _Chunk, objs as _objects

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
    CMP = _member()
    ASSIGN = _member()
    TERM = _member()
    EXPONENT = _member()
    PREFIX = _member()
    CALL = _member()


class FuncType(_Base):
    SCRIPT = _member()
    FUNCTION = _member()
    GENERATOR = _member()


class Compiler:
    class Local:

        @property
        def name(self) -> _t.Token:
            return self._name

        @property
        def depth(self) -> int:
            return self._depth

        @depth.setter
        def depth(self, depth: int):
            if self._depth != -1:
                raise ValueError("Cannot set depth on local with pre-set depth")
            self._depth = depth

        def __init__(self, name: _t.Token, depth: int):
            self._name = name
            self._depth = depth

        def __str__(self) -> str:
            return f"L({self._name} @ {self._depth})"

    @property
    def scope_depth(self) -> int:
        return self._depth

    @property
    def function(self) -> _objects.Function:
        return self._function

    @property
    def enclosing(self) -> _None["Compiler"]:
        return self._enclosing

    @enclosing.setter
    def enclosing(self, value: "Compiler"):
        self._enclosing = value

    def __init__(self, owner: "Consumer", ty: FuncType, enclosing: "Compiler" = None):
        self._enclosing = enclosing
        self._count = 1
        self._depth = 0
        self._locals: _list[Compiler.Local] = [Compiler.Local(_t.IdentifierToken("", 0, 0), 0)]
        self._owner = owner
        if ty == FuncType.GENERATOR:
            self._function = _objects.Generator()
        else:
            self._function = _objects.Function()
        self.type = ty

    def __iter__(self) -> _iter["Compiler.Local"]:
        yield from reversed(self._locals)

    def __enter__(self) -> None:
        self.begin()

    def __exit__(self, exc_type: _type[Exception], exc_val: Exception, exc_tb):
        self.end()

    def __len__(self) -> int:
        return len(self._locals) - 1

    def begin(self):
        self._depth += 1

    def end(self):
        self._depth -= 1
        while self._count > 0 and self._locals[-1].depth > self._depth:
            self._locals.pop()
            self._count -= 1
            self._owner.emit(_Byte.POP)

    def add_local(self, local: "Compiler.Local"):
        self._locals.append(local)
        self._count += 1

    def pop(self):
        self._owner.emit_return()
        # if not self._owner.errored:
        #     self._function.raw.disassemble(self._function.name.raw or "top-level")

    def iterate(self) -> _iter[_tuple[int, "Compiler.Local"]]:
        i_l_map = enumerate(self._locals)
        yield from reversed(tuple(i_l_map))

    def mark(self):
        if self._depth == 0:
            return
        self._locals[-1].depth = self._depth


class Consumer(_abc.ABC):
    """
    Abstract class for a consumer that will analyse a token stream and return an AST.

    All methods are abstract.
    """
    chunk: _Chunk
    compiler: Compiler
    errored: bool

    @_abc.abstractmethod
    def expr(self, precedence: Precedence = None):
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
    def buffer(self):
        pass

    @_abc.abstractmethod
    def block(self):
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
    def get_precedence(self) -> int:
        """
        Find the precedence of the current expression.

        Returns
        -------
        Precedence
            The precedence of the current expression.
        """
        pass

    @_abc.abstractmethod
    def consume(self, expected: _type[_T], message: str, *, predicate: _p.Predicate[_T] = None) -> _T:
        """
        This will check to see if the next token is expected, then consume it.

        If not expected, it will report an error.

        Generics
        --------
        _T: Token
            The token type to expect.

        Parameters
        ----------
        expected: type[_T]
            The type of token to expect. This is the type returned.
        message: str
            The error message to report when an unexpected token is found.
        predicate: Predicate[_T] | None
            The filter to apply to the token for extra information.

        Returns
        -------
        _T
            The consumed token.
        """
        pass

    @_abc.abstractmethod
    def consume_type(self, expected: _t.TokenType, message: str) -> _t.Token:
        """
        This will check to see if the next token is expected, then consume it.

        If not expected, it will report an error.

        Parameters
        ----------
        expected: TokenType
            The type of token to expect.
        message: str
            The error message to report when an unexpected token is found.

        Returns
        -------
        Token
            The consumed token.
        """
        pass

    @_abc.abstractmethod
    def match(self, *expected: _t.TokenType, predicate: _p.Predicate = None) -> bool:
        """
        Parse a series of matches.

        This will advance past the consumed token.

        Parameters
        ----------
        *expected: TokenType
            The expected types. Any of these can match.
        predicate: Predicate | None
            The additional filter to apply to the token.

        Returns
        -------
        bool
            Whether the token was consumed.
        """
        pass

    @_abc.abstractmethod
    def check(self, *expected: _t.TokenType, predicate: _p.Predicate = None) -> bool:
        """
        Parse a series of matches.

        This will not advance past the consumed token.

        Parameters
        ----------
        *expected: TokenType
            The expected types. Any of these can match.
        predicate: Predicate | None
            The additional filter to apply to the token.

        Returns
        -------
        bool
            Whether the token is found.
        """
        pass

    @_abc.abstractmethod
    def emit(self, *code: _Union[int, _Byte]):
        pass

    @_abc.abstractmethod
    def emit_return(self, byte=_Byte.RETURN):
        pass

    @_abc.abstractmethod
    def emit_loop(self, start: int):
        pass

    @_abc.abstractmethod
    def emit_jump(self, instruction: _Byte) -> int:
        pass

    @_abc.abstractmethod
    def patch_jump(self, index: int):
        pass

    @_abc.abstractmethod
    def error(self, msg: str):
        pass

    @_abc.abstractmethod
    def pop(self) -> _objects.Function:
        pass
