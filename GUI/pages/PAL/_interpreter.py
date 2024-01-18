import time
import typing

from . import grammar, nodes


class ExecutionFinished(Exception):
    """
    Special error for when an interpreter has fully executed a loop.
    """

    def __init__(self):
        pass


class Interpreter:
    """
    Class to implement an interpreter for PAL nodes.

    Will sequentially run through all nodes, and execute them one by one. Errors aren't handled and will cause the
    interpreter to halt.

    :var tuple[Node, ...] _nodes: The full stream of nodes.
    :var Iterator[Node] _pointer: A generator that yields a singular node at a time.
    :var int _delay: The delay time between repetitions.
    :var int _repeats: The number of repetitions remaining.
    :var bool _loop: Whether looping is allowed.
    :var Callable[str, Callable[[Any], None]] _mic: The microscope variable setter function.
    :var dict[KeywordType, Callable[..., None]] _keywords: The PAL keyword functions.
    :var dict[str, Callable[[Any], None]] _variables: The PAL variable setters.
    :var dict[str, Callable[..., None]] _functions: The PAL functions.
    :var Node | None _node: The current node being executed.
    """

    @property
    def location(self) -> str:
        """
        Public access to the current location of the interpreter.

        :return: The string location formatted as row:column
        """
        r, c = self._node.src.position
        return f"{r}:{c}"

    def __init__(self, *stream: nodes.Node, mic_setter: typing.Callable[[str], typing.Callable[[typing.Any], None]],
                 keywords: dict[grammar.KeywordType, typing.Callable[..., None]],
                 variables: dict[str, typing.Callable[[typing.Any], None]],
                 functions: dict[str, typing.Callable[..., None]]):
        self._nodes = stream
        self._pointer = iter(stream)
        self._delay = self._repeats = 0
        self._loop = True
        self._mic = mic_setter
        self._keywords = keywords
        self._variables = variables
        self._functions = functions
        self._node: typing.Optional[nodes.Node] = None

    def run(self):
        """
        Main entry point to the execution cycle.

        Will continuously loop until nodes have been exhausted.
        """
        while True:
            try:
                node = self._node = next(self._pointer)
                if isinstance(node, nodes.KeywordStmt):
                    self._keyword(node)
                elif isinstance(node, nodes.SetStmt):
                    self._set(node)
                elif isinstance(node, nodes.CallStmt):
                    self._call(node)
                else:
                    raise TypeError(f"Invalid node {node.__class__}")
            except StopIteration:
                break

    def _keyword(self, node: nodes.KeywordStmt):
        key_func = self._keywords[node.src.type]
        kwargs = self._eval(**node.information)
        if node.src.type == grammar.KeywordType.LOOP:
            if not self._repeats:
                if self._loop:
                    self._repeats = kwargs.get("amount", -1)
                    self._delay = kwargs.get("delay", 0)
                    self._loop = False
                else:
                    raise StopIteration()
            else:
                self._repeats -= 1
            self._pointer = iter(self._nodes)
            time.sleep(self._delay)
            return
        key_func(**kwargs)

    def _set(self, node: nodes.SetStmt):
        if isinstance(node, nodes.SetKeyStmt):
            func_finder = self._mic
        else:
            func_finder = self._variables.get
        target = func_finder(node.src.src)
        target(self._eval(value=node.value)["value"])

    def _call(self, node: nodes.CallStmt):
        function = self._functions[node.src.src]
        args = self._eval(**{f"arg_{i}": arg for i, arg in enumerate(node.args)}).values()
        function(*args)

    def _eval(self, **exprs: nodes.Expr) -> dict[str, typing.Any]:
        evaluated = {}
        for name, expr in exprs.items():
            if isinstance(expr, nodes.EnumExpr):
                evaluated[name] = f"{expr:m}"
            elif isinstance(expr, nodes.GroupExpr):
                evaluated[name] = tuple(self._eval(**{f"arg_{i}": arg for i, arg in enumerate(expr.items)}).values())
            elif isinstance(expr, nodes.FileExpr):
                evaluated[name] = f"{expr:p}"
            elif isinstance(expr, nodes.NumberExpr):
                evaluated[name] = f"{expr:v}"
            elif isinstance(expr, nodes.KeywordExpr):
                evaluated[name] = f"{expr:k}"
            elif isinstance(expr, nodes.StringExpr):
                evaluated[name] = f"{expr:r}"
            else:
                raise TypeError(f"Invalid expression type {expr.__class__}")
        return evaluated
