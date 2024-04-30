import enum
from typing import Dict as _dict, List as _list

from ._errors import *
from ._interpreter import Interpreter
from ..grammar import GetExpr, GroupExpr, nodes, ReturnStmt, tokens


class State(enum.Flag):
    """
    Bitwise enumeration to represent various states the resolver can be in.

    Note that these states are useful for semantic scoping of statements - for example, a loop could be represented as
    'breakable' state, which means that all 'break' statements are allowed. This same state can then be used for
    'switch' statements, without needing a separate 'SwitchType' and 'LoopType' enumerations.

    Members
    -------
    RETURNABLE
        Indicates a state where a return statement is valid.
    """
    RETURNABLE = enum.auto()


class Resolver(nodes.NodeWalker[None]):
    """
    Concrete node walker that does not return any data but performs semantic analysis.

    This is useful for closure scoping (variable resolution), statement scoping (see the `State` enum), and static type
    checking.

    Attributes
    ----------
    _scopes: list[dict[str, bool]]
        The current scopes. It is a stack mapping name to boolean, where False indicates declared, and True indicates
        defined. A variable must be defined before it can be used.
    _exec: Interpreter
        The interpreter to use. It allows for variable resolution by mapping resolver scope to interpreter scope.
    _state: State
        The current semantic state.
    """

    def __init__(self, executor: Interpreter):
        self._scopes: _list[_dict[str, bool]] = []
        self._exec = executor
        self._state = State(0)

    def resolve(self, *statements: nodes.Node):
        """
        Resolve all statements provided.

        Parameters
        ----------
        *statements: Node
            The nodes to analyse.
        """
        for stmt in statements:
            stmt.accept(self)

    def begin_scope(self):
        """
        Push a new scope to the scope stack.
        """
        self._scopes.append({})

    def end_scope(self):
        """
        Pop the newest scope from the scope stack.
        """
        self._scopes.pop()

    def declare(self, name: tokens.IdentifierToken):
        """
        Declare a variable. Declaration means "I know this variable exists, but it is unfinished".

        Parameters
        ----------
        name: IdentifierToken
            The variable name to declare.

        Raises
        ------
        ResolutionError
            If a variable in that scope already exists.
        """
        if self._scopes:
            scope = self._scopes[-1]
            if name.src in scope:
                raise ResolutionError(name, f"Duplicate variable {name.src!r}")
            scope[name.src] = False

    def define(self, name: tokens.IdentifierToken):
        """
        Define a variable. Definition means "This already existing variable is now finished".

        Parameters
        ----------
        name: IdentifierToken
            The variable name to declare.
        """
        if self._scopes:
            self._scopes[-1][name.src] = True

    def resolve_local(self, var: nodes.VariableExpr, name: tokens.IdentifierToken):
        """
        Resolve a local variable. This means to contact the interpreter to mark the exact scope for this usage.

        Parameters
        ----------
        var: VariableExpr
            The variable expression (usage of a variable) to resolve.
        name: IdentifierToken
            The name of the variable being resolved.
        """
        max_depth = len(self._scopes)
        for i, mapping in zip(range(max_depth - 1, -1, -1), reversed(self._scopes)):
            if name.src in mapping:
                self._exec.resolve(var, max_depth - 1 - i)
                return

    def resolve_function(self, callee: nodes.FunctionStmt):
        """
        Resolve a function declaration.

        This will put the resolver in a `RETURNABLE` state until the block has finished.

        Parameters
        ----------
        callee: FunctionStmt
            The function object node.
        """
        self._state |= State.RETURNABLE
        self.begin_scope()
        for param in callee.parameters:
            self.declare(param)
            self.define(param)
        self.resolve(*callee.body)
        self.end_scope()
        self._state &= ~State.RETURNABLE

    def visit_block_stmt(self, node: nodes.BlockStmt) -> None:
        """
        Concrete visitation of a block statement.

        This will spawn a new scope, resolve all statements, then discard the scope.

        Parameters
        ----------
        node: BlockStmt
            The node to resolve.
        """
        self.begin_scope()
        self.resolve(*node.stmts)
        self.end_scope()

    def visit_variable_stmt(self, node: nodes.VariableStmt) -> None:
        """
        Concrete visitation of a variable statement.

        This will declare the variable, resolve the initializer, then define the variable.

        Parameters
        ----------
        node: VariableStmt
            The node to resolve.
        """
        self.declare(node.src)
        self.resolve(node.value)
        self.define(node.src)

    def visit_variable_expr(self, node: nodes.VariableExpr) -> None:
        """
        Concrete visitation of a variable expression.

        This will check for the variable being declared, then resolve the local variable.

        Note that this function is only run when a local variable is visited, as global variables are not resolved.

        Parameters
        ----------
        node: VariableExpr
            The node to resolve.
        """
        if self._scopes:
            if not self._scopes[-1].get(node.identifier, True):
                raise ResolutionError(node.src, "Cannot read local variable in its own initializer")
            self.resolve_local(node, node.src)

    def visit_set_expr(self, node: nodes.SetExpr) -> None:
        """
        Concrete visitation of a set expression.

        This will resolve the value, make sure the target is a variable, then resolve the local variable.

        Parameters
        ----------
        node: SetExpr
            The node to resolve.

        Raises
        ------
        ResolutionError
            If the target is not a variable.
        """
        self.resolve(node.source)
        target = node.sink
        if not isinstance(target, nodes.VariableExpr):
            raise ResolutionError(node.src, "Can only assign to variables")
        self.resolve_local(target, target.src)

    def visit_function_stmt(self, node: nodes.FunctionStmt) -> None:
        """
        Concrete visitation of a function expression.

        This will declare and define the name, then resolve the function.

        Parameters
        ----------
        node: FunctionStmt
            The node to resolve.
        """
        self.declare(node.src)
        self.define(node.src)
        self.resolve_function(node)

    def visit_number_expr(self, node: nodes.NumberExpr) -> None:
        """
        Concrete visitation of a number expression.

        This will do nothing, as number expression contains no resolvable data.

        Parameters
        ----------
        node: NumberExpr
            The node to resolve.
        """
        pass

    def visit_keyword_expr(self, node: nodes.KeywordExpr) -> None:
        """
        Concrete visitation of a keyword expression.

        This will do nothing, as keyword expression contains no resolvable data.

        Parameters
        ----------
        node: KeywordExpr
            The node to resolve.
        """
        pass

    def visit_unary_expr(self, node: nodes.UnaryExpr) -> None:
        """
        Concrete visitation of a unary expression.

        This will resolve the operand.

        Parameters
        ----------
        node: UnaryExpr
            The node to resolve.
        """
        self.resolve(node.expr)

    def visit_binary_expr(self, node: nodes.BinaryExpr) -> None:
        """
        Concrete visitation of a binary expression.

        This will resolve the operands.

        Parameters
        ----------
        node: BinaryExpr
            The node to resolve.
        """
        self.resolve(node.left)
        self.resolve(node.right)

    def visit_string_expr(self, node: nodes.StringExpr) -> None:
        """
        Concrete visitation of a string expression.

        This will do nothing, as string expression contains no resolvable data.

        Parameters
        ----------
        node: StringExpr
            The node to resolve.
        """
        pass

    def visit_path_expr(self, node: nodes.PathExpr) -> None:
        """
        Concrete visitation of a path expression.

        This will do nothing, as path expression contains no resolvable data.

        Parameters
        ----------
        node: PathExpr
            The node to resolve.
        """
        pass

    def visit_call_expr(self, node: nodes.CallExpr) -> None:
        """
        Concrete visitation of a call expression.

        This will resolve the target and the arguments.

        Parameters
        ----------
        node: CallExpr
            The node to resolve.
        """
        self.resolve(node.callee)
        self.resolve(node.args)

    def visit_collection_expr(self, node: nodes.CollectionExpr) -> None:
        """
        Concrete visitation of a collection expression.

        This will resolve each element.

        Parameters
        ----------
        node: CollectionExpr
            The node to resolve.
        """
        for item in node.items:
            self.resolve(item)

    def visit_get_expr(self, node: GetExpr) -> None:
        """
        Concrete visitation of an access expression.

        This will resolve the target.

        Parameters
        ----------
        node: GetExpr
            The node to resolve.
        """
        self.resolve(node.source)

    def visit_group_expr(self, node: GroupExpr) -> None:
        """
        Concrete visitation of a grouped expression.

        This will resolve the target.

        Parameters
        ----------
        node: GroupExpr
            The node to resolve.
        """
        self.resolve(node.expr)

    def visit_loop_stmt(self, node: nodes.LoopStmt) -> None:
        """
        Concrete visitation of a loop statement.

        This will resolve the amount (if available) and the body.

        Parameters
        ----------
        node: LoopStmt
            The node to resolve.
        """
        if node.amount is not None:
            self.resolve(node.amount)
        self.resolve(node.code)

    def visit_sleep_stmt(self, node: nodes.SleepStmt) -> None:
        """
        Concrete visitation of a wait statement.

        This will resolve the amount.

        Parameters
        ----------
        node: SleepStmt
            The node to resolve.
        """
        self.resolve(node.delay)

    def visit_keyword_stmt(self, node: nodes.KeywordStmt) -> None:
        """
        Concrete visitation of a keyword statement.

        This will do nothing, as a keyword statement contains no resolvable data.

        Parameters
        ----------
        node: KeywordStmt
            The node to resolve.
        """
        pass

    def visit_return_stmt(self, node: ReturnStmt) -> None:
        """
        Concrete visitation of a return statement.

        This will resolve the value (if available).

        Parameters
        ----------
        node: ReturnStmt
            The node to resolve.

        Raises
        ------
        ResolutionError
            If the resolver is not in a returnable state.
        """
        if not (self._state & State.RETURNABLE):
            raise ResolutionError(node.src, "Can only return from functions")
        if node.value is not None:
            self.resolve(node.value)
