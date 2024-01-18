import typing

from . import grammar, nodes


class CursorStack:
    """
    Class to represent a backtracking cursor. Allows for creating a backtracking parser.

    Using a combination of the "branch", "undo" and "save" methods allows for full control over the correct nodes to
    spawn based on the token stream.

    Example::

        stack = CursorStack()
        stack.branch() #we're not sure about what path to take here
        try:
            execute_some_code_that_modifies_cursor_position()
        except:
            stack.undo() #wasn't the correct choice, go back to previous position
        else:
            stack.save() #was the correct choice, remove the 'branching' cursor but retain its position

    :var list[int] _stack: The stack of cursor positions.
    """

    @property
    def cursor(self) -> int:
        """
        Public access to the most recent cursor.

        :return: The value of the last element in the stack.
        """
        return self._stack[-1]

    @cursor.setter
    def cursor(self, value: int):
        """
        Public access to modifying the most recent cursor.

        :param value: The new value of the last element in the stack.
        """
        self._stack[-1] = value

    def __init__(self):
        self._stack = [0]

    def __str__(self) -> str:
        build = []
        stack = self._stack.copy()
        for _ in self._stack:
            pos = stack.pop()
            if stack:
                hist = "no history."
            else:
                hist = "history: "
            build.append(f"Cursor @ {pos} with {hist}")
        return "".join(build)

    def save(self):
        """
        Saves the progress of the most recent cursor into its history.

        Acts like merging branches – the penultimate element (the 'history' cursor) has its value updated to be the
        final element (the 'current' cursor).
        """
        if len(self._stack) == 1:
            return
        most_recent = self._stack.pop()
        self.cursor = most_recent

    def undo(self):
        """
        Backtracks to the penultimate element (the 'history').
        """
        if len(self._stack) == 1:
            raise ValueError("No undo history")
        self._stack.pop()

    def branch(self):
        """
        Spawns a new cursor at the position of the most recent.
        """
        self._stack.append(self.cursor)


class ParsingError(Exception):
    """
    Custom exception to implement a syntax error in PAL code.
    """

    @property
    def node(self) -> nodes.ErrorNode:
        """
        Public access to the error node that caused this exception.

        :return: An error node representing the incorrect token and a message
        """
        return self._src

    def __init__(self, src: nodes.ErrorNode):
        self._src = src
        super().__init__(src.message)


class Parser:
    """
    Class to implement a compiler from PAL tokens into AST nodes to be executed by an interpreter.

    Implements a backtracking parser. At any point in the PAL grammar where a token can create multiple nodes, progress
    is branched to create a safe flow of execution. This ensures any parse errors raised are caught and the cursor
    backtracked before the next branch is tried in its **own** safe branch. Upon successful node formation, progress is
    saved.

    For now, PAL grammar is simplified (all variables, keys, and functions are known at compile-time) such that no
    backtracking operations are *required*, but future expansions may change this.

    :var CursorStack _cursors: Main machinery for backtracking capability. See help(CursorStack) for usage.
    :var tuple[Token, ...] _stream: The full stream of tokens.
    :var Iterator[Token] _pointer: A generator that yields a singular token at a time.
    :var int _length: The length of the token stream. Is one less than the input length to bypass EOF parsing.
    :var str _estimation: The types of estimators.
    :var dict[type[Token], Callable[[Token], Node]] _stmt_map: The mapping of token types to their parse functions.
    """

    @property
    def _curr(self) -> grammar.Token:
        self._cursors.cursor += 1
        return next(self._pointer)

    @property
    def _prev(self) -> grammar.Token:
        if self._cursors.cursor == 0:
            raise ValueError("No previous")
        return self._stream[self._cursors.cursor - 1]

    @property
    def finished(self) -> bool:
        """
        Public access to whether the parser has finished compiling.

        :return: Whether the current cursor is at the end of the token stream.
        """
        return self._cursors.cursor >= self._length

    def __init__(self, *stream: grammar.Token):
        self._cursors = CursorStack()
        self._stream = stream
        self._pointer = iter(stream)
        self._length = len(stream) - 1  # -1 will make sure EOF isn't parsed
        self._estimation = f"({', '.join(repr(grammar.TYPE_KEYWORDS[ty]) for ty in grammar.ESTIMATORS)})"
        self._stmt_map: dict[typing.Type[grammar.Token], typing.Callable] = {
            grammar.KeywordToken: self._keyword,
            grammar.IdentifierToken: self._ident
        }

    def run(self) -> typing.Iterator[nodes.Node]:
        """
        Construct an iterator for the nodes generated from the token stream.

        :return: A generator yielding each node generated.
        :raises ParsingError: If any syntax error occurs.
        """
        while not self.finished:
            yield self._scan()

    def _scan(self) -> nodes.Node:
        token = self._curr
        if isinstance(token, grammar.ErrorToken):
            raise ParsingError(nodes.ErrorNode(token))
        try:
            return self._stmt_map[type(token)](token)
        except KeyError:
            raise ParsingError(nodes.ErrorNode.from_unknown(token, f"Invalid statement type {token.token_type.name!r}"))

    def _keyword(self, word: grammar.KeywordToken) -> nodes.KeywordStmt:
        key = word.type
        context = {}
        click = repr(grammar.TYPE_SYMBOLS[grammar.TokenType.CLICK])
        cluster_id = repr(grammar.TYPE_KEYWORDS[grammar.KeywordType.ALL])
        if key in {grammar.KeywordType.WRITE, grammar.KeywordType.READ}:
            context["path"] = self._consume(grammar.FileToken, "Expected file path to save to")
        elif key in {grammar.KeywordType.BW_E, grammar.KeywordType.BW_T}:
            if key == grammar.KeywordType.BW_E:
                self._consume(grammar.TokenType.CLICK, f"Expected {click} to preface kernel size")
                context["size"] = self._consume(grammar.NumberToken, "Expected kernel size to be a number")
            if self._match(grammar.TokenType.CLICK):
                keyword = self._consume(grammar.KeywordToken, f"Expected estimation type to be {self._estimation}")
                if keyword.type not in grammar.ESTIMATORS:
                    raise ParsingError(nodes.ErrorNode.from_unknown(
                        keyword, f"Expected estimation type to be {self._estimation}"))
                context["estimation"] = keyword
        elif key == grammar.KeywordType.INTERACT:
            self._consume(grammar.TokenType.CLICK, f"Expected {click} to preface ID")
            if not self._match(grammar.NumberToken, grammar.KeywordToken):
                raise ParsingError(nodes.ErrorNode.from_unknown(self._curr,
                                                                f"Expected cluster ID to be a number or {cluster_id}"))
            prev = self._prev
            if isinstance(prev, grammar.KeywordToken):
                if prev.type != grammar.KeywordType.ALL:
                    raise ParsingError(nodes.ErrorNode.from_unknown(prev, f"Expected cluster ID to be {cluster_id}"))
            context["dest"] = prev
        elif key == grammar.KeywordType.LOOP:
            if self._match(grammar.TokenType.NUM):
                context["amount"] = self._prev
            if self._match(grammar.TokenType.CLICK):
                context["delay"] = self._consume(grammar.NumberToken, "Expected delay to be a number")
        elif key not in grammar.STATEMENTS:
            raise ParsingError(nodes.ErrorNode.from_unknown(word, f"Invalid keyword statement {key.name!r}"))
        return nodes.KeywordStmt(word, **{k: nodes.Expr(v) for k, v in context.items()})

    def _ident(self, name: grammar.IdentifierToken) -> nodes.Node:
        assign = repr(grammar.TYPE_SYMBOLS[grammar.TokenType.ASSIGN])
        paren = repr(grammar.TYPE_SYMBOLS[grammar.TokenType.START_CALL])
        access = repr(grammar.TYPE_SYMBOLS[grammar.TokenType.ACCESS])
        var_type = name.type
        if var_type == grammar.IdentifierType.FUNCTION:
            self._consume(grammar.TokenType.START_CALL, f"Expected {paren} to call function")
            return nodes.CallStmt(name, *self._group(grammar.TokenType.END_CALL, name, "function call"))
        elif var_type == grammar.IdentifierType.VARIABLE:
            self._consume(grammar.TokenType.ASSIGN, f"Expected {assign} to assign to variable")
            return nodes.SetStmt(name, self._expr())
        elif var_type == grammar.IdentifierType.HARDWARE:
            self._consume(grammar.TokenType.ACCESS, f"Expected {access} to access hardware variables")
            key = self._consume(grammar.IdentifierToken, f"Expected variable name")
            if key.type != grammar.IdentifierType.KEY:
                raise ParsingError(nodes.ErrorNode.from_unknown(key, f"Expected hardware variable"))
            self._consume(grammar.TokenType.ASSIGN, f"Expected {assign} to assign to variable")
            return nodes.SetKeyStmt(name, key, self._expr())
        raise ParsingError(nodes.ErrorNode.from_unknown(name, f"Unknown identifier {name.identifier!r}"))

    def _expr(self) -> nodes.Expr:
        look = self._curr
        if isinstance(look, grammar.KeywordToken):
            if look.type in grammar.EXPRS:
                return nodes.KeywordExpr(look)
        elif isinstance(look, grammar.EnumToken):
            return nodes.EnumExpr(look)
        elif isinstance(look, grammar.NumberToken):
            return nodes.NumberExpr(look)
        elif isinstance(look, grammar.FileToken):
            return nodes.FileExpr(look)
        elif isinstance(look, grammar.StringToken):
            return nodes.StringExpr(look)
        elif look.token_type == grammar.TokenType.START_GROUP:
            return nodes.GroupExpr(look, *self._group(grammar.TokenType.END_GROUP, look, "group"))
        raise ParsingError(nodes.ErrorNode.from_unknown(look, f"Expected expression"))

    def _group(self, end: grammar.TokenType, start: grammar.Token, context: str) -> list[nodes.Expr]:
        sep = repr(grammar.TYPE_SYMBOLS[grammar.TokenType.SEPARATOR])
        args = []
        match_found = False
        while not self.finished and not self._match(end):
            args.append(self._expr())
            if not self._check(end):
                self._consume(grammar.TokenType.SEPARATOR, f"Expected {sep} to separate grouped items")
            else:
                match_found = True
        if self.finished and not match_found:
            raise ParsingError(nodes.ErrorNode.from_unknown(start, f"Unterminated {context}"))
        return args

    @typing.overload
    def _consume(self, expected: grammar.TokenType, failure: str) -> grammar.Token:
        pass

    @typing.overload
    def _consume(self, expected: typing.Type[nodes.Token], failure: str) -> nodes.Token:
        pass

    def _consume(self, expected: typing.Union[grammar.TokenType, typing.Type[nodes.Token]], failure: str) \
            -> typing.Union[grammar.Token, nodes.Token]:
        if self._match(expected):
            return self._prev
        raise ParsingError(nodes.ErrorNode.from_unknown(self._curr, failure))

    def _match(self, *types: typing.Union[grammar.TokenType, typing.Type[grammar.Token]]) -> bool:
        if any(map(self._check, types)):
            self._advance()
            return True
        return False

    def _check(self, test: typing.Union[grammar.TokenType, typing.Type[grammar.Token]]) -> bool:
        if isinstance(test, type):
            return isinstance(self._peek(), test)
        return self._peek().token_type == test

    def _peek(self, by=1) -> grammar.Token:
        by -= 1
        if self._cursors.cursor + by >= self._length:
            return self._stream[-1]
        return self._stream[self._cursors.cursor + by]

    def _advance(self):
        _ = self._curr
