from . import _tokens as _t
import abc as _abc
from typing import TypeVar as _GenVar, Generic as _Gen, Tuple as _tuple, Optional as _None

_T = _GenVar("_T", bound=_t.Token)
_R = _GenVar("_R")


class Node(_Gen[_T], _abc.ABC):
    """
    Abstract Base Class for all Node types.

    A walker can visit each node.

    Generics
    --------
    _T: Token
        The token type of the node

    Abstract Methods
    ----------------
    __str__
    accept

    Attributes
    ----------
    _t: _T
        The token that is the main part for this node.
    """

    @property
    def src(self) -> _T:
        """
        Public access to the node's source.

        Returns
        -------
        _T
            The main part of the node.
        """
        return self._t

    def __init__(self, token: _T):
        self._t = token

    def __hash__(self) -> int:
        return hash(self._t.token_type)

    @_abc.abstractmethod
    def __str__(self) -> str:
        pass

    @_abc.abstractmethod
    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        """
        Visit this node.

        Generics
        --------
        _R
            The return type of the visitor.

        Parameters
        ----------
        visitor: NodeWalker[_R]
            The walker who can visit this node.

        Returns
        -------
        _R
            The return value of the visitor.
        """
        pass


class ErrorNode(Node[_t.ErrorToken]):
    """
    Concrete class representing an error node.

    Bound Generics
    --------------
    _T: ErrorToken
    """

    def __str__(self) -> str:
        return f"SyntaxError: {self._t.message}"

    @classmethod
    def from_unknown_error(cls, token: _t.Token, message: str) -> "ErrorNode":
        """
        Alternate constructor to represent an error node formed from a non-error token.

        Parameters
        ----------
        token: Token
            The non-error token.
        message: str
            The cause of the error.

        Returns
        -------
        ErrorNode
            The error node.
        """
        return cls(_t.ErrorToken(message, *token.position))

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        pass


class Expr(Node[_T], _Gen[_T], _abc.ABC):
    """
    Abstract Base Class for all expression nodes types.

    Abstract Methods
    ----------------
    accept
    """

    def __str__(self) -> str:
        return f"{self._t.token_type} expression at {self._t.rc_ref}"


class NumberExpr(Expr[_t.BaseNumToken]):
    """
    Concrete expression representing a number node.

    Bound Generics
    --------------
    _T: BaseNumToken
    """

    @property
    def value(self) -> float:
        """
        Shortcut access to the token's value.

        Returns
        -------
        float
            The token's value.
        """
        return self._t.value

    def __init__(self, token: _t.BaseNumToken):
        super().__init__(token)

    def __str__(self) -> str:
        return f"{self._t.value} ({self._t.number_type} type) at {self._t.rc_ref}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_number_expr(self)


class VariableExpr(Expr[_t.IdentifierToken]):
    """
    Concrete expression representing a variable node.

    Bound Generics
    --------------
    _T: IdentifierToken
    """

    @property
    def identifier(self) -> str:
        """
        Shortcut access to the token's identifier.

        Returns
        -------
        str
            The token's lexeme.
        """
        return self._t.src

    def __str__(self) -> str:
        return f"GET {self.identifier!r} at {self._t.rc_ref}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_variable_expr(self)


class KeywordExpr(Expr[_t.KeywordToken]):
    """
    Concrete expression representing a keyword node.

    Bound Generics
    --------------
    _T: KeywordToken
    """

    def __str__(self) -> str:
        return f"{self._t.keyword_type.name} keyword at {self._t.rc_ref}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_keyword_expr(self)


class UnaryExpr(Expr[_t.Token]):
    """
    Concrete expression representing a unary expression node.

    A unary expression only contains one operand:
        >>>-1

    Bound Generics
    --------------
    _T: Token

    Attributes
    ----------
    _operand: Expr
        The operand of the expression.
    """

    @property
    def operator_type(self) -> _t.TokenType:
        """
        Shortcut access to the token's type.

        Returns
        -------
        TokenType
            The type of the token.
        """
        return self._t.token_type

    @property
    def expr(self) -> Expr:
        """
        Public access to the expression.

        Returns
        -------
        Expr
            The operand of the expression.
        """
        return self._operand

    def __init__(self, token: _t.Token, operand: Expr):
        super().__init__(token)
        self._operand = operand

    def __str__(self) -> str:
        return f"{self.operator_type.name} ({self._operand}) at {self._t.rc_ref}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_unary_expr(self)


class BinaryExpr(Expr[_t.Token]):
    """
    Concrete expression representing a binary expression node.

    A binary expression contains two operands:
        >>> 1 + 1

    Bound Generics
    --------------
    _T: Token

    Attributes
    ----------
    _LHS: Expr
        The left expression.
    _RHS: Expr
        The right expression.
    """

    @property
    def operator_type(self) -> _t.TokenType:
        """
        Shortcut access to the token's type.

        Returns
        -------
        TokenType
            The type of the token.
        """
        return self._t.token_type

    @property
    def left(self) -> Expr:
        """
        Public access to the left expression.

        Returns
        -------
        Expr
            The expression on the left-hand side of the operation.
        """
        return self._LHS

    @property
    def right(self) -> Expr:
        """
        Public access to the right expression.

        Returns
        -------
        Expr
            The expression on the right-hand side of the operation.
        """
        return self._RHS

    def __init__(self, token: _t.Token, left: Expr, right: Expr):
        super().__init__(token)
        self._LHS, self._RHS = left, right

    def __str__(self) -> str:
        return f"{self.operator_type.name} ({self._LHS}, {self._RHS}) at {self._t.rc_ref}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_binary_expr(self)


class StringExpr(Expr[_t.StringToken]):
    """
    Concrete expression representing a string node.

    Bound Generics
    --------------
    _T: StringToken
    """

    def __str__(self) -> str:
        return f"String {self._t.raw!r} at {self._t.rc_ref}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_string_expr(self)


class PathExpr(Expr[_t.PathToken]):
    """
    Concrete expression representing a path node.

    Bound Generics
    --------------
    _T: PathToken
    """

    def __str__(self) -> str:
        return f"Path {self._t.raw!r} at {self._t.rc_ref}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_path_expr(self)


class CallExpr(Expr[_t.Token]):
    """
    Concrete expression representing a call node.

    Bound Generics
    --------------
    _T: Token

    Attributes
    ----------
    _focus: Expr
        The callee expression.
    _args: CollectionExpr
        The arguments provided to the function.
    """

    @property
    def callee(self) -> Expr:
        """
        Public access to the callee expression.

        Returns
        -------
        Expr
            The subject of the call.
        """
        return self._focus

    @property
    def args(self) -> "CollectionExpr":
        """
        Public access to the arguments provided to the function.

        Returns
        -------
        CollectionExpr
            The arguments, in a format that can be evaluated by the DSL
        """
        return self._args

    def __init__(self, subject: Expr, *args: Expr):
        super().__init__(subject.src)
        self._focus = subject
        self._args = CollectionExpr(subject.src, *args)

    def __str__(self) -> str:
        return f"CALL ({self._focus}) using {self._args}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_call_expr(self)


class CollectionExpr(Expr[_t.Token]):
    """
    Concrete expression to represent a collection of items.

    Bound Generics
    --------------
    _T: Token

    Attributes
    ----------
    _items: tuple[Expr, ...]
        The items in the collection.
    """

    @property
    def items(self) -> _tuple[Expr, ...]:
        """
        Public access to the items in the collection.

        Returns
        -------
        tuple[Expr, ...]
            The grouped items.
        """
        return self._items

    def __init__(self, token: _t.Token, *items: Expr):
        super().__init__(token)
        self._items = items

    def __str__(self) -> str:
        mid = "; ".join(map(lambda x: f"({x})", self._items))
        return f"List ({mid}) at {self._t.rc_ref}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_collection_expr(self)


class SetExpr(Expr[_t.Token]):
    """
    Concrete expression to represent an assignment.

    Bound Generics
    --------------
    _T: Token

    Attributes
    ----------
    _target: Expr
        The variable to assign the expression to.
    _value: Expr
        The value to use.
    """

    @property
    def sink(self) -> Expr:
        """
        Public access to the value sink.

        Returns
        -------
        Expr
            The variable to assign the expression to.
        """
        return self._target

    @property
    def source(self) -> Expr:
        """
        Public access to the value source.

        Returns
        -------
        Expr
            The value to use.
        """
        return self._value

    def __init__(self, start: _t.Token, var: Expr, value: Expr):
        super().__init__(start)
        self._target = var
        self._value = value

    def __str__(self) -> str:
        return f"SET ({self._target}) to ({self._value}) at {self._t.rc_ref}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_set_expr(self)


class GetExpr(Expr[_t.Token]):
    """
    Concrete expression to represent accessing a property.

    Bound Generics
    --------------
    _T: Token

    Attributes
    ----------
    _name: IdentifierToken
        The property name.
    _src: Expr
        The expression to get the property from.
    """

    @property
    def source(self) -> Expr:
        """
        Public access to the property source.

        Returns
        -------
        Expr
            The expression to get the property from.
        """
        return self._src

    @property
    def prop(self) -> str:
        """
        Shortcut access to the property name

        Returns
        -------
        str
            The property name's lexeme.
        """
        return self._name.src

    def __init__(self, token: _t.Token, src: Expr, name: _t.IdentifierToken):
        super().__init__(token)
        self._name = name
        self._src = src

    def __str__(self) -> str:
        return f"GET ({self._name}) FROM ({self._src}) at {self._t.rc_ref}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_get_expr(self)


class GroupExpr(Expr[_t.Token]):
    """
    Concrete expression to represent a lower precedence expression, wrapped in a higher precedence expression.

    Bound Generics
    --------------
    _T: Token

    Attributes
    ----------
    _grouped: Expr
        The expression in the group.
    """

    @property
    def expr(self) -> Expr:
        """
        Public access to the expression.

        Returns
        -------
        Expr
            The grouped expression.
        """
        return self._grouped

    def __init__(self, token: _t.Token, item: Expr):
        super().__init__(token)
        self._grouped = item

    def __str__(self) -> str:
        return f"GROUPED {self._grouped} at {self._t.rc_ref}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_group_expr(self)


class VariableStmt(Node[_t.IdentifierToken]):
    """
    Concrete node representing a variable declaration.

    Bound Generics
    --------------
    _T: IdentifierToken

    Attributes
    ----------
    _value: Expr
        The initial value for the variable.
    """

    @property
    def value(self) -> Expr:
        """
        Public access to the value.

        Returns
        -------
        Expr
            The initial value for the variable.
        """
        return self._value

    def __init__(self, token: _t.IdentifierToken, value: Expr):
        super().__init__(token)
        self._value = value

    def __str__(self) -> str:
        return f"DEF {self._t.src!r} = ({self._value}) at {self._t.rc_ref}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_variable_stmt(self)


class FunctionStmt(Node[_t.IdentifierToken]):
    """
    Concrete node representing a function or generator declaration.

    Bound Generics
    --------------
    _T: IdentifierToken

    Attributes
    ----------
    _params: tuple[IdentifierToken, ...]
        The parameter names.
    _code: BlockStmt
        The block of code the function executes.
    _is_generator: bool
        Whether this function is a generator or a pure function
    """

    @property
    def parameters(self) -> _tuple[_t.IdentifierToken, ...]:
        """
        Public access to the function's parameter names.

        Returns
        -------
        tuple[IdentifierToken, ...]
            The parameter names.
        """
        return self._params

    @property
    def body(self) -> _tuple[Node, ...]:
        """
        Shortcut access to the block of code.

        Returns
        -------
        tuple[Node, ...]
            The statements from the block of code.
        """
        return self._code.stmts

    @property
    def code(self) -> "BlockStmt":
        """
        Public access to the function's code.

        Returns
        -------
        BlockStmt
            The block of code this function executes
        """
        return self._code

    def __init__(self, name: _t.IdentifierToken, params: _tuple[_t.IdentifierToken, ...], block: "BlockStmt"):
        super().__init__(name)
        self._params = params
        self._code = block

    def __str__(self) -> str:
        params = ", ".join(map(lambda x: f"{x.src!r}", self._params))
        return f"DEF {self._t.src!r} with input ({params}) and code {self._code}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_function_stmt(self)


class BlockStmt(Node[_t.Token]):
    """
    Concrete node representing a block of code.

    Bound Generics
    --------------
    _T: Token

    Attributes
    ----------
    _code: tuple[Node, ...]
        The statements within the block.
    """

    @property
    def stmts(self) -> _tuple[Node, ...]:
        """
        Public access to the inside code.

        Returns
        -------
        tuple[Node, ...]
            The statements within the block.
        """
        return self._code

    def __init__(self, start: _t.Token, *stmts: Node):
        super().__init__(start)
        self._code = stmts

    def __str__(self) -> str:
        stmts = "\n".join(map(str, self._code))
        return f"BLOCK:(\n{stmts}\n) at {self._t.rc_ref}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_block_stmt(self)


class LoopStmt(Node[_t.KeywordToken]):
    """
    Concrete node representing a loop declaration.

    Bound Generics
    --------------
    _T: KeywordToken

    Attributes
    ----------
    _code: BlockStmt
        The block of code to execute repeatedly.
    _amount: Expr | None
        The number of times to repeat the code.
    """

    @property
    def amount(self) -> _None[Expr]:
        """
        Public access to the amount.

        Returns
        -------
        Expr | None
            The number of times to repeat the code.
        """
        return self._amount

    @property
    def body(self) -> _tuple[Node, ...]:
        """
        Shortcut access to the block of code.

        Returns
        -------
        tuple[Node, ...]
            The statements from the block of code.
        """
        return self._code.stmts

    @property
    def code(self) -> BlockStmt:
        """
        Public access to the function's code.

        Returns
        -------
        BlockStmt
            The block of code this function executes
        """
        return self._code

    def __init__(self, token: _t.KeywordToken, code: BlockStmt, times: _None[Expr]):
        super().__init__(token)
        self._code = code
        self._amount = times

    def __str__(self) -> str:
        amount = "forever" if self._amount is None else f"({self._amount}) times"
        return f"LOOP {amount}: {self._code}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_loop_stmt(self)


class SleepStmt(Node[_t.KeywordToken]):
    """
    Concrete node representing a wait statement.

    Bound Generics
    --------------
    _T: KeywordToken

    Attributes
    ----------
    _delay: Expr
        The number of seconds to wait for.
    """

    @property
    def delay(self) -> Expr:
        """
        Public access to the delay time.

        Returns
        -------
        Expr
            The number of seconds to wait for.
        """
        return self._delay

    def __init__(self, token: _t.KeywordToken, delay: Expr):
        super().__init__(token)
        self._delay = delay

    def __str__(self) -> str:
        return f"WAIT FOR ({self._delay}) seconds at {self._t.rc_ref}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_sleep_stmt(self)


class KeywordStmt(Node[_t.KeywordToken]):
    """
    Concrete node representing a keyword statement.

    Bound Generics
    --------------
    _T: KeywordToken
    """

    @property
    def keyword_type(self) -> _t.KeywordType:
        """
        Shortcut access to the keyword type.

        Returns
        -------
        KeywordType
            The keyword type of the token.
        """
        return self._t.keyword_type

    def __str__(self) -> str:
        return f"{self.keyword_type.name} statement at {self._t.rc_ref}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_keyword_stmt(self)


class ReturnStmt(Node[_t.KeywordToken]):
    """
    Concrete node representing a return statement

    Bound Generics
    --------------
    _T: KeywordToken

    Attributes
    ----------
    _value: Expr | None
        The return value.
    """

    @property
    def value(self) -> _None[Expr]:
        """
        Public access to the return value.

        Returns
        -------
        Expr | None
            The value to return.
        """
        return self._value

    def __init__(self, token: _T, value: Expr = None):
        super().__init__(token)
        self._value = value

    def __str__(self) -> str:
        return f"RETURN ({self._value}) at {self._t.rc_ref}"

    def accept(self, visitor: "NodeWalker[_R]") -> _R:
        return visitor.visit_return_stmt(self)


class NodeWalker(_abc.ABC, _Gen[_R]):
    """
    Abstract base class for structures that walk an Abstract Syntax Tree.

    All methods are abstract

    Generics
    --------
    _R
        The return value of all functions.
    """

    @_abc.abstractmethod
    def visit_number_expr(self, node: NumberExpr) -> _R:
        """
        Abstract method to walk over a number node and explore its features.

        Parameters
        ----------
        node: NumberExpr
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_variable_expr(self, node: VariableExpr) -> _R:
        """
        Abstract method to walk over a variable node and explore its features.

        Parameters
        ----------
        node: VariableExpr
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_keyword_expr(self, node: KeywordExpr) -> _R:
        """
        Abstract method to walk over a keyword expression node and explore its features.

        Parameters
        ----------
        node: KeywordExpr
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_unary_expr(self, node: UnaryExpr) -> _R:
        """
        Abstract method to walk over a unary expression node and explore its features.

        Parameters
        ----------
        node: UnaryExpr
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_binary_expr(self, node: BinaryExpr) -> _R:
        """
        Abstract method to walk over a binary expression node and explore its features.

        Parameters
        ----------
        node: BinaryExpr
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_string_expr(self, node: StringExpr) -> _R:
        """
        Abstract method to walk over a string node and explore its features.

        Parameters
        ----------
        node: StringExpr
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_path_expr(self, node: PathExpr) -> _R:
        """
        Abstract method to walk over a path node and explore its features.

        Parameters
        ----------
        node: PathExpr
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_call_expr(self, node: CallExpr) -> _R:
        """
        Abstract method to walk over a calling node and explore its features.

        Parameters
        ----------
        node: CallExpr
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_collection_expr(self, node: CollectionExpr) -> _R:
        """
        Abstract method to walk over a collection node and explore its features.

        Parameters
        ----------
        node: CollectionExpr
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_set_expr(self, node: SetExpr) -> _R:
        """
        Abstract method to walk over an assign node and explore its features.

        Parameters
        ----------
        node: SetExpr
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_get_expr(self, node: GetExpr) -> _R:
        """
        Abstract method to walk over a property access node and explore its features.

        Parameters
        ----------
        node: GetExpr
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_group_expr(self, node: GroupExpr) -> _R:
        """
        Abstract method to walk over a grouped node and explore its features.

        Parameters
        ----------
        node: GroupExpr
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_variable_stmt(self, node: VariableStmt) -> _R:
        """
        Abstract method to walk over a variable declaration node and explore its features.

        Parameters
        ----------
        node: VariableStmt
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_function_stmt(self, node: FunctionStmt) -> _R:
        """
        Abstract method to walk over a function node and explore its features.

        Parameters
        ----------
        node: FunctionStmt
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_block_stmt(self, node: BlockStmt) -> _R:
        """
        Abstract method to walk over a block node and explore its features.

        Parameters
        ----------
        node: BlockStmt
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_loop_stmt(self, node: LoopStmt) -> _R:
        """
        Abstract method to walk over a loop node and explore its features.

        Parameters
        ----------
        node: LoopStmt
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_sleep_stmt(self, node: SleepStmt) -> _R:
        """
        Abstract method to walk over a delay node and explore its features.

        Parameters
        ----------
        node: SleepStmt
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_keyword_stmt(self, node: KeywordStmt) -> _R:
        """
        Abstract method to walk over a keyword statement node and explore its features.

        Parameters
        ----------
        node: KeywordStmt
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass

    @_abc.abstractmethod
    def visit_return_stmt(self, node: ReturnStmt) -> _R:
        """
        Abstract method to walk over a return node and explore its features.

        Parameters
        ----------
        node: ReturnStmt
            The node to walk over.

        Returns
        -------
        _R
            The returned exploration.
        """
        pass
