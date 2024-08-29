import abc as _abc
from enum import auto as _member, Enum as _Base
from typing import (Iterator as _iter, Optional as _None, Tuple as _tuple, Type as _type,
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

    CMP

    ASSIGN

    TERM

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
    """
    Enumeration to represent various function types.

    Members
    -------
    SCRIPT

    FUNCTION

    GENERATOR

    """
    SCRIPT = _member()
    FUNCTION = _member()
    GENERATOR = _member()


class Compiler:
    """
    Class representing a variable compiler. This compiler resolves scoping of local variables.

    A compiler can be used as a context manager to create a new scope for a limited time.
    To create a new scope, it begins by increasing the scope depth, and ends by decreasing it back to its original
    level, as well as popping all local variables.

    Attributes
    ----------
    _enclosing: Compiler | None
        The enclosing compiler. As compilers can be nested, so can scopes.
    _count: int
        The number of local variables defined in this compiler.
    _depth: int
        The current scope depth of this compiler. Note that this allows two ways to nest variables - compiler nesting
        (when creating functions and generators) and increasing the scope depth (when creating other local scopes).
    _locals: list[Local]
        The local variables defined in this compiler.
    _owner: Consumer
        The consumer that owns this compiler.
    _function: Function | Generator
        The function or generator that defines this compiler.
    _type: FuncType
        The function type for this compiler.
    """

    class Local:
        """
        Class representing a local variable.

        Attributes
        ----------
        _name: Token
            The token representing the name of the variable.
        _depth: int
            The scope depth of the variable. It is -1 if this variable is declared but not defined.
        """

        @property
        def name(self) -> _t.Token:
            """
            Public access to the name of the variable.

            Returns
            -------
            Token
                The token representing the name of the variable.
            """
            return self._name

        @property
        def depth(self) -> int:
            """
            Public access to the scope depth of the variable.

            Returns
            -------
            int
                The scope depth of the variable. It is -1 if this variable is declared but not defined.
            """
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
        """
        Public access to the compiler's scope depth.

        Returns
        -------
        int
            The current scope depth of this compiler, which will be the depth of all defined locals until changed.
        """
        return self._depth

    @property
    def function(self) -> _Union[_objects.Function, _objects.Generator]:
        """
        Public access to the chunk-based object for this compiler.

        Returns
        -------
        Function | Generator
            The function or generator that defines this compiler.
        """
        return self._function

    @property
    def enclosing(self) -> _None["Compiler"]:
        """
        Public access to this compiler's parent scope.

        Returns
        -------
        Compiler | None
            The enclosing compiler.
        """
        return self._enclosing

    @enclosing.setter
    def enclosing(self, value: "Compiler"):
        self._enclosing = value

    @property
    def type(self) -> FuncType:
        """
        Public access to the particular compiler type.

        Returns
        -------
        FuncType
            The function type for this compiler.
        """
        return self._type

    def __init__(self, owner: "Consumer", ty: FuncType, enclosing: "Compiler" = None):
        self._enclosing = enclosing
        self._count = 1
        self._depth = 0
        self._locals = [Compiler.Local(_t.IdentifierToken("", 0, 0), 0)]
        self._owner = owner
        if ty == FuncType.GENERATOR:
            self._function = _objects.Generator()
        else:
            self._function = _objects.Function()
        self._type = ty

    def __iter__(self) -> _iter["Compiler.Local"]:
        yield from reversed(self._locals)

    def __enter__(self) -> None:
        self.begin()

    def __exit__(self, exc_type: _type[Exception], exc_val: Exception, exc_tb):
        self.end()

    def __len__(self) -> int:
        return len(self._locals) - 1

    def begin(self):
        """
        Increases the scope depth to mark a new scope beginning.
        """
        self._depth += 1

    def end(self):
        """
        Decreases the scope depth to mark a new scope ending. Will also pop all local variables created in the scope.
        """
        self._depth -= 1
        while self._count > 0 and self._locals[-1].depth > self._depth:
            self._locals.pop()
            self._count -= 1
            self._owner.emit(_Byte.POP)

    def add_local(self, local: "Compiler.Local"):
        """
        Adds a local variable to the current scope.

        Parameters
        ----------
        local: Local
            The local variable to add.
        """
        self._locals.append(local)
        self._count += 1

    def pop(self):
        """
        Pops this function by emitting a return.
        """
        self._owner.emit_return()
        # if not self._owner.errored:
        #     self._function.raw.disassemble(self._function.name.raw or "top-level")

    def iterate(self) -> _iter[_tuple[int, "Compiler.Local"]]:
        """
        Iterates over the local variables defined in this compiler.

        This will go in reverse order from the most nested scope to the least.

        Yields
        ------
        tuple[int, Local]
            The local variable and its index in the compiler.
        """
        i_l_map = enumerate(self._locals)
        yield from reversed(tuple(i_l_map))

    def mark(self):
        """
        Marks the most recently added local variable as defined.
        """
        if self._depth == 0:
            return
        self._locals[-1].depth = self._depth


class Consumer(_abc.ABC):
    """
    Abstract class for a consumer that will analyse a token stream and emit a bytecode representation.

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
        """
        pass

    @_abc.abstractmethod
    def buffer(self):
        """
        Method to act as a parsing buffer for new lines.

        As the language uses new lines as statement ends, this ensures that successive new lines after a scope are not
        perceived as a syntax error.
        """
        pass

    @_abc.abstractmethod
    def block(self):
        """
        Method to parse a block of code.
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
        int
            The precedence of the current expression.
        """
        pass

    @_abc.abstractmethod
    def consume(self, expected: _type[_T], message: str, *, predicate: _p.Predicate[_T] = None) -> _T:
        """
        This will check to see if the next token is expected, then consume it.

        If not expected, it will report an error.

        Within the message, the predicate can be accessed by using `{filter}`.

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

        Within the message, the parsing token of the type can be accessed by using `{lookup}`.

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
        """
        Emit a series of instructions

        Parameters
        ----------
        *code: int | OpCodes
            The instructions to emit. Note that while opcodes are actual instructions (and integers are operands), they
            are demoted to integers to be emitted.
        """
        pass

    @_abc.abstractmethod
    def emit_return(self, byte=_Byte.RETURN):
        """
        Signal the end of a series of instructions by emitting a return value.

        Parameters
        ----------
        byte: OpCodes
            The type of return to emit. Note that it is expected for this to be a `RETURN` or a `YIELD`.
        """
        pass

    @_abc.abstractmethod
    def emit_loop(self, start: int):
        """
        Emit a loop instruction. Note that while jumps have to be patched later, loops know their jump when emitted.

        Parameters
        ----------
        start: int
            The starting index of the loop. This is used to work out the number of instructions to jump.
        """
        pass

    @_abc.abstractmethod
    def emit_jump(self, instruction: _Byte) -> int:
        """
        Emit a jump instruction. Note that the operand also emitted is a placeholder, as the jump is unknown.

        Parameters
        ----------
        instruction: OpCodes
            The type of jump to emit.

        Returns
        -------
        int
            The index of the jump instruction, so that it can be patched later.
        """
        pass

    @_abc.abstractmethod
    def patch_jump(self, index: int):
        """
        Patch a jump instruction. This is when the placeholder instruction is fixed to know the exact jump.

        Parameters
        ----------
        index: int
            The index of the jump instruction.
        """
        pass

    @_abc.abstractmethod
    def error(self, msg: str):
        """
        Send the parser into an error-fuelled panic, with a message to the end user.

        Parameters
        ----------
        msg: str
            The error message.
        """
        pass

    @_abc.abstractmethod
    def pop(self) -> _objects.Function:
        """
        Pop the function from the compiler. This signals the end of a function's scope.

        Returns
        -------
        Function
            The function who's scope just ended.
        """
        pass
