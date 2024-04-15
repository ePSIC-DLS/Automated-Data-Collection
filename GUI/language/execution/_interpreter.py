import time
import typing
from typing import Dict as _dict, Optional as _None

from . import _values as v
from ._env import EnvironmentChain
from ._errors import *
from ..grammar import GetExpr, GroupExpr, nodes, PathExpr, ReturnStmt, tokens


class Interpreter(v.Interpreter):
    """
    Concrete interpreter designed to execute nodes.

    Attributes
    ----------
    _env: EnvironmentChain
        The current environment
    _globals: EnvironmentChain
        The global environment.
    _locals: dict[int, int]
        Mapping from variable id to stack depth.
    _token: Token | None
        The source token of the current statement being executed.
    """

    @property
    def position(self) -> str:
        """
        Shortcut access to the current token's formatted position.

        Returns
        -------
        str
            The row-column formatted position of the current token.
        """
        return self._token.rc_ref

    @property
    def token(self) -> tokens.Token:
        """
        Public access to the current token.

        Returns
        -------
        Token
            The source token of the current statement being executed.
        """
        return self._token

    def __init__(self):
        self._env = self._globals = EnvironmentChain()
        self._locals: _dict[int, int] = {}
        self._token: _None[tokens.Token] = None

    def execute(self, *stream: nodes.Node):
        """
        Execute a stream of nodes.

        Parameters
        ----------
        stream: Node
            The nodes to execute.

        Raises
        ------
        RunTimeError
            If any errors occur during execution.
        """
        try:
            for node in stream:
                self.evaluate(node)
        except RunTimeError:
            raise
        except Exception as err:
            raise RunTimeError(self._token, err.args[0])

    def evaluate(self, node: nodes.Node) -> typing.Any:
        self._token = node.src
        return node.accept(self)

    def _lookup(self, name: str, expr: nodes.VariableExpr) -> object:
        distance = self._locals.get(id(expr))
        if distance is None:
            ans = self._globals.get_at(name)
        else:
            ans = self._env.get_at(name, distance)
        return ans

    def assign(self, name: str, value):
        self._env.set_at(name, value, create=True)

    def resolve(self, var: nodes.VariableExpr, depth: int):
        """
        Map a depth to a particular expression.

        Parameters
        ----------
        var: VariableExpr
            The variable expression to find the id of.
        depth: int
            The depth it resides at.
        """
        self._locals[id(var)] = depth

    def visit_number_expr(self, node: nodes.NumberExpr) -> object:
        """
        Concrete visitation of a number expression.

        Parameters
        ----------
        node: NumberExpr
            The node to visit.

        Returns
        -------
        float
            The value of the number.
        """
        return node.value

    def visit_variable_expr(self, node: nodes.VariableExpr) -> object:
        """
        Concrete visitation of a variable expression.

        Parameters
        ----------
        node: VariableExpr
            The node to visit.

        Returns
        -------
        object
            The value of the variable.
        """
        return self._lookup(node.identifier, node)

    def visit_keyword_expr(self, node: nodes.KeywordExpr) -> object:
        """
        Concrete visitation of a keyword expression.

        Parameters
        ----------
        node: KeywordExpr
            The node to visit.

        Returns
        -------
        str
            The keyword's identifier.
        """
        return node.src.src

    def visit_unary_expr(self, node: nodes.UnaryExpr) -> object:
        """
        Concrete visitation of a unary expression.

        Parameters
        ----------
        node: UnaryExpr
            The node to visit.

        Returns
        -------
        object
            The negation of the evaluated operand.
        """
        if node.operator_type == tokens.TokenType.NEG:
            return -self.evaluate(node.expr)

    def visit_binary_expr(self, node: nodes.BinaryExpr) -> object:
        """
        Concrete visitation of a binary expression.

        Parameters
        ----------
        node: BinaryExpr
            The node to visit.

        Returns
        -------
        object
            The left operand multiplied by 10 to the right operand.
        """
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        if node.operator_type == tokens.TokenType.POW:
            return left * 10 ** right

    def visit_string_expr(self, node: nodes.StringExpr) -> object:
        """
        Concrete visitation of a string expression.

        Parameters
        ----------
        node: StringExpr
            The node to visit.

        Returns
        -------
        str
            The raw string (no quotes included).
        """
        return node.src.raw

    def visit_path_expr(self, node: PathExpr) -> object:
        """
        Concrete visitation of a path expression.

        Parameters
        ----------
        node: PathExpr
            The node to visit.

        Returns
        -------
        str
            The path (quotes included).
        """
        return node.src.src

    def visit_call_expr(self, node: nodes.CallExpr) -> object:
        """
        Concrete visitation of a call expression.

        Parameters
        ----------
        node: CallExpr
            The node to visit.

        Returns
        -------
        object
            The return value of the function call.
        """
        callee = self.evaluate(node.callee)
        args = self.evaluate(node.args)
        env = callee.closure if isinstance(callee, v.Fobj) else self._env
        self._env = EnvironmentChain(env)
        ret = callee(self, *args)
        self._env = self._env.parent
        return ret

    def visit_collection_expr(self, node: nodes.CollectionExpr) -> object:
        """
        Concrete visitation of a collection expression.

        Parameters
        ----------
        node: CollectionExpr
            The node to visit.

        Returns
        -------
        list[object]
            The items in the collection.
        """
        return [self.evaluate(item) for item in node.items]

    def visit_set_expr(self, node: nodes.SetExpr) -> object:
        """
        Concrete visitation of an assignment expression.

        Parameters
        ----------
        node: SetExpr
            The node to visit.

        Returns
        -------
        object
            The new variable value.
        """
        value = self.evaluate(node.source)
        distance = self._locals.get(id(node))
        if distance is None:
            self._globals.set_at(node.sink.src.src, value)
        else:
            self._env.set_at(node.sink.src.src, value, distance)
        return value

    def visit_get_expr(self, node: GetExpr) -> object:
        """
        Concrete visitation of an access expression.

        Parameters
        ----------
        node: GetExpr
            The node to visit.

        Returns
        -------
        object
            The property of the variable.
        """
        obj = self.evaluate(node.source)
        return getattr(obj, node.prop)

    def visit_group_expr(self, node: GroupExpr) -> object:
        """
        Concrete visitation of a grouped expression.

        Parameters
        ----------
        node: GroupExpr
            The node to visit.

        Returns
        -------
        object
            The evaluated inner expression.
        """
        return self.evaluate(node.expr)

    def visit_variable_stmt(self, node: nodes.VariableStmt) -> None:
        """
        Concrete visitation of a variable declaration.

        This will create the variable in the environment and assign its value.

        Parameters
        ----------
        node: VariableStmt
            The node to visit.
        """
        value = self.evaluate(node.value)
        self._env.set_at(node.src.src, value, create=True)

    def visit_function_stmt(self, node: nodes.FunctionStmt) -> None:
        """
        Concrete visitation of a function declaration.

        This will create a variable (with the same name as the function) in the environment and assign it a `Fobj`.

        Parameters
        ----------
        node: FunctionStmt
            The node to visit.
        """
        self._env.set_at(node.src.src, v.Fobj(node, self._env), create=True)

    def visit_block_stmt(self, node: nodes.BlockStmt) -> None:
        """
        Concrete visitation of a block statement.

        This will create a new environment before executing the code within the block.

        Parameters
        ----------
        node: BlockStmt
            The node to visit.
        """
        self._env = EnvironmentChain(self._env)
        for stmt in node.stmts:
            self.evaluate(stmt)
        self._env = self._env.parent

    def visit_loop_stmt(self, node: nodes.LoopStmt) -> None:
        """
        Concrete visitation of a loop statement.

        This will repeatedly execute the block of code.

        Parameters
        ----------
        node: LoopStmt
            The node to visit.
        """
        if node.amount is None:
            while True:
                self.evaluate(node.code)
        else:
            n = self.evaluate(node.amount)
            if not isinstance(n, float) or int(n) != n:
                raise RunTimeError(node.src, "Expected an integer repetition amount")
            n = int(n)
            for _ in range(n):
                self.evaluate(node.code)

    def visit_sleep_stmt(self, node: nodes.SleepStmt) -> None:
        """
        Concrete visitation of a delay statement.

        This will delay for the number of seconds specified.

        Parameters
        ----------
        node: SleepStmt
            The node to visit.
        """
        delay = self.evaluate(node.delay)
        time.sleep(delay)

    def visit_keyword_stmt(self, node: nodes.KeywordStmt) -> None:
        """
        Concrete visitation of a keyword statement.

        This will do nothing, as each keyword is very different (there is a subclass in the GUI for this function)

        Parameters
        ----------
        node: KeywordStmt
            The node to visit.
        """
        pass

    def visit_return_stmt(self, node: ReturnStmt) -> None:
        """
        Concrete visitation of a return statement.

        Parameters
        ----------
        node: ReturnStmt
            The node to visit.

        Raises
        ------
        Return
            The specified return value.
        """
        if node.value is not None:
            raise Return(self.evaluate(node.value))
        raise Return()
