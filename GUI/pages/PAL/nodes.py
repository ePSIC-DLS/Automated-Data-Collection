import abc

from . import grammar
import typing

Token = typing.TypeVar('Token', bound=grammar.Token)


class Node(typing.Generic[Token], abc.ABC):
    """
    Abstract base class representing an AST node to be executed. Generic on Token.

    Has format option 'v' to only retrieve a value representation of the node.

    :var Token _t: The token at the heart of this AST node.
    """

    @property
    def src(self) -> Token:
        """
        Public access to the node's source token.

        :return: The token at the heart of this AST node.
        """
        return self._t

    def __init__(self, token: Token):
        self._t = token

    def __format__(self, format_spec: str) -> str:
        if format_spec == "v":
            return self._t.src
        raise ValueError(f"Unknown format option {format_spec!r}")

    @abc.abstractmethod
    def __str__(self) -> str:
        pass


class ErrorNode(Node[grammar.ErrorToken]):
    """
    A concrete subclass representing an error has occurred.
    """

    @property
    def message(self) -> str:
        """
        Public access to a specially formed error message.

        :return: The error message with line and column information.
        """
        r, c = self._t.position
        return f"{self._t.err} at {r}:{c}"

    def __str__(self) -> str:
        return f"Error ({self.message}) at {self._t.position}"

    @classmethod
    def from_unknown(cls, token: grammar.Token, message: str) -> "ErrorNode":
        """
        Alternate constructor to construct an error node from an unknown error.

        :param token: The token to turn into an error token.
        :param message: The error message to use.
        :return: An error node with an error token at the given token's position and with given error message.
        """
        err = grammar.ErrorToken(message, *token.position)
        return cls(err)


class Expr(Node[Token], typing.Generic[Token]):
    """
    Generic subclass representing an expression.
    """

    def __new__(cls, token: Token, *args, **kwargs):
        """
        Instance-based constructor for special expressions created by specific token types.

        :param token: The heart of the expression.
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        """
        if cls is Expr:
            if args:
                return GroupExpr(token, *args)
            elif isinstance(token, grammar.KeywordToken):
                return KeywordExpr(token)
            elif isinstance(token, grammar.EnumToken):
                return EnumExpr(token)
            elif isinstance(token, grammar.NumberToken):
                return NumberExpr(token)
            elif isinstance(token, grammar.FileToken):
                return FileExpr(token)
            elif isinstance(token, grammar.StringToken):
                return StringExpr(token)
        return super().__new__(cls)

    def __str__(self) -> str:
        return f"{self._t.token_type.name!r} expression at {self._t.position}"


class KeywordExpr(Expr[grammar.KeywordToken]):
    """
    Special expression representing a keyword used as an expression.

    Enhances the 'v' format option to specify it is a keyword, and adds the 'k' format option to use old 'v'.
    """

    def __format__(self, format_spec: str) -> str:
        if format_spec == "k":
            return super().__format__("v")
        old = super().__format__(format_spec)
        if format_spec == "v":
            old = f"Keyword {old}"
        return old


class EnumExpr(Expr[grammar.EnumToken]):
    """
    Special expression representing an enumeration.

    Enhances the 'v' format option to specify it is an enum member, and adds the 'm' format option to use old 'v'.
    """

    def __format__(self, format_spec: str) -> str:
        if format_spec == "m":
            return super().__format__("v")
        old = super().__format__(format_spec)
        if format_spec == "v":
            old = f"Enum member {old[1:-1]}"
        return old


class FileExpr(Expr[grammar.FileToken]):
    """
    Special expression representing a file path.

    Enhances the 'v' format option to specify it is a file path, and adds the 'p' format option to use old 'v'.
    """

    @property
    def path(self) -> str:
        """
        Shortcut property to return the token's source.

        :return: The source path for this token.
        """
        return self._t.src

    def __format__(self, format_spec: str) -> str:
        if format_spec == "p":
            return super().__format__("v")
        old = super().__format__(format_spec)
        if format_spec == "v":
            old = f"Path {old[1:-1]}"
        return old


class StringExpr(Expr[grammar.StringToken]):
    """
    Special expression representing a string.

    Enhances the 'v' option to specify it is a string, and adds the 'r' format option to use old 'v'.
    """

    def __format__(self, format_spec: str) -> str:
        if format_spec == "r":
            return super().__format__("v")
        old = super().__format__(format_spec)
        if format_spec == "v":
            old = f"String {old[1:-1]}"
        return old


class NumberExpr(Expr[grammar.NumberToken]):
    """
    Special expression representing a numerical value.

    Enhances the 'v' format option to correctly handle the type.
    """

    @property
    def value(self) -> float:
        """
        Shortcut property to return the token's value.

        :return: The token's numerical value.
        """
        return self._t.value

    @property
    def num_type(self) -> typing.Union[typing.Type[float], typing.Type[int]]:
        """
        Public access to the type of numerical value represented.

        :return: The class of the numerical value represented in the token.
        """
        return type(self._t.value)

    def __format__(self, format_spec: str) -> str:
        if format_spec == "v":
            return f"{self._t.value}"
        return super().__format__(format_spec)


class GroupExpr(Expr[grammar.Token]):
    """
    Special expression representing a group of expressions.

    Enhances the 'v' option to instead display all grouped expressions.

    :var tuple[Expr, ...] _items: All expressions contained in the group.
    """

    @property
    def items(self) -> tuple[Expr, ...]:
        """
        Public access to the grouped items.

        :return: All expressions contained in the group.
        """
        return self._items

    def __init__(self, token: grammar.Token, *items: Expr):
        super().__init__(token)
        self._items = items

    def __format__(self, format_spec: str) -> str:
        old = super().__format__(format_spec)
        if format_spec == "v":
            sur = grammar.TYPE_SYMBOLS[grammar.TokenType.START_GROUP], grammar.TYPE_SYMBOLS[grammar.TokenType.END_GROUP]
            old = f"{sur[0]}{', '.join(f'{elem:v}' for elem in self._items)}{sur[1]}"
        return old

    def __str__(self) -> str:
        return super().__str__().replace("expression", f"expression consisting of {self:v}")


class CallStmt(Node[grammar.IdentifierToken]):
    """
    A concrete subclass representing a call to a function.

    :var GroupExpr _args: The arguments provided.
    """

    @property
    def args(self) -> tuple[Expr, ...]:
        """
        Shortcut property to return the group's contents.

        :return: The arguments provided.
        """
        return self._args.items

    def __init__(self, token: grammar.IdentifierToken, *args: Expr):
        super().__init__(token)
        self._args = GroupExpr(token, *args)

    def __str__(self) -> str:
        return f"Calling {self._t.identifier} at {self._t.position} using args {self._args:v}"


class KeywordStmt(Node[grammar.KeywordToken]):
    """
    A concrete subclass representing a keyword as a statement.

    :var dict[str, Expr] _context: Any special contextual information.
    """

    @property
    def information(self) -> dict[str, Expr]:
        """
        Public access to any information provided in the grammar.

        :return: Any special contextual information.
        """
        return self._context.copy()

    def __init__(self, token: grammar.KeywordToken, **context: Expr):
        super().__init__(token)
        self._context = context

    def __str__(self) -> str:
        context = "; ".join(f"{k} = {v:v}" for k, v in self._context.items())
        return f"{self._t.type.name} statement at {self._t.position} with context: ({context})"


class SetStmt(Node[grammar.IdentifierToken]):
    """
    A concrete subclass representing setting a variable.

    :var Expr _value: The new value of the variable.
    """

    @property
    def value(self) -> Expr:
        """
        Public access to the value.

        :return: The new value of the variable.
        """
        return self._value

    def __init__(self, token: grammar.IdentifierToken, value: Expr):
        super().__init__(token)
        self._value = value

    def __str__(self) -> str:
        return f"Setting {self._t.identifier} to {self._value:v}"


class SetKeyStmt(SetStmt):
    """
    Special set statement for representing setting a microscope variable.

    Has a composite token as the source, which represents the full name to pass to the microscope, has the line of the
    microscope hardware, and the column of the microscope key.

    :var IdentifierToken _h: The hardware token.
    :var IdentifierToken _k: The key token.
    """

    @property
    def target(self) -> grammar.IdentifierToken:
        """
        Public access to the microscope hardware target.

        :return: The hardware token.
        """
        return self._h

    @property
    def key(self) -> grammar.IdentifierToken:
        """
        Public access to the variable to set.

        :return: The key token.
        """
        return self._k

    def __init__(self, hardware: grammar.IdentifierToken, key: grammar.IdentifierToken, value: Expr):
        self._h, self._k = hardware, key
        composite = grammar.IdentifierToken(f"{hardware.identifier}.{key.identifier}", hardware.position[0],
                                            key.position[1], False)
        super().__init__(composite, value)
