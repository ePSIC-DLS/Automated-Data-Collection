import abc as _abc
import functools as _functools
from enum import Enum as _Base
from typing import Tuple as _tuple


class TokenType(_Base):
    """
    Enumeration to represent the different types of tokens that the language can recognise.

    Members
    -------
    ERR
        Error Token.
    NUM
        Number literal in base 10.
    IDENTIFIER
        Variable name token.
    KEYWORD
        Any recognised keyword.
    EOF
        Recognised by the empty string, it represents the end of the file.
    EOL
        Recognised by the newline character, it represents the end of a statement.
    STRING
        Recognised by the speech mark, it represents a string literal.
    PATH
        Recognised by the apostrophe, it represents a path literal.
    HEX
        Recognised by a backslash and then an x, it represents a number literal in base 16.
    BIN
        Recognised by a backslash and then a b, it represents a number literal in base 2.
    SEPARATE
        Recognised by a comma, it represents a separator character.
    ACCESS
        Recognised by a dot, it represents getting a property.
    ASSIGN
        Recognised by an equal sign, it represents setting a value.
    OUTPUT
        Recognised by a question mark, it represents outputting a value to the console.
    START_CALL
        Recognised by a left bracket, it represents beginning a function call or a bracketed expression.
    END_CALL
        Recognised by a right bracket, it represents ending a function call or a bracketed expression.
    START_LIST
        Recognised by a left square bracket, it represents beginning an array.
    END_LIST
        Recognised by a right square bracket, it represents ending an array.
    START_BLOCK
        Recognised by a left brace, it represents beginning a new lexical scope.
    END_BLOCK
        Recognised by a right brace, it represents ending the current lexical scope
    NEG
        Recognised by a minus sign, it is a unary operator.
    INV
        Recognised by an exclamation mark, it is a unary operator.
    POW
        Recognised by a chevron, it is a binary operator.
    PLUS
        Recognised by a plus, it is a binary operator.
    COMBINE
        Recognised by a vertical bar, it is a binary operator.
    EQ
        Recognised by two equal signs, it represents an equality comparison between two values.
    LT
        Recognised by a less than sign, it represents an ordered comparison between two values.
    GT
        Recognised by a greater than sign, it represents an ordered comparison between two values.
    NEQ
        Recognised by an exclamation mark and an equals sign, it represents an equality comparison between two values.
    LTE
        Recognised by a less than sign and an equals sign, it represents an ordered comparison between two values.
    GTE
        Recognised by a greater than sign and an equals sign, it represents an ordered comparison between two values.
    """
    ERR = "#"
    NUM = "##"
    IDENTIFIER = "###"
    KEYWORD = "####"

    EOF = ""
    EOL = "\n"
    STRING = "\""
    PATH = "\'"
    HEX = "\\x"
    BIN = "\\b"
    SEPARATE = ","
    ACCESS = "."
    ASSIGN = "="
    OUTPUT = "?"

    START_CALL = "("
    END_CALL = ")"
    START_LIST = "["
    END_LIST = "]"
    START_BLOCK = "{"
    END_BLOCK = "}"

    NEG = "-"
    INV = "!"
    POW = "^"
    PLUS = "+"
    COMBINE = "|"
    EQ = "=="
    LT = "<"
    GT = ">"
    NEQ = "!="
    LTE = "<="
    GTE = ">="


SYMBOLS_TYPE = {member.value: member for member in TokenType if "#" not in member.value}
TYPE_SYMBOLS = {v: k for k, v in SYMBOLS_TYPE.items()}


class KeywordType(_Base):
    """
    Enumeration to represent the different types of keywords that the language can recognise.

    Members
    -------
    SURVEY
        Recognised by 'Scan', it represents taking a survey image.
    SEGMENT
        Recognised by 'Cluster', it represents using DBSCAN to cluster an image.
    FILTER
        Recognised by 'filter', it represents filtering the valid clusters using a known python script.
    INTERACT
        Recognised by 'mark', it represents interacting with the cluster manager.
    MANAGE
        Recognised by 'Tighten', it represents tightening and exporting all managed grids.
    SCAN
        Recognised by 'Search', it represents taking a deep scan over all grids.
    D_CORRECT
        Recognised by 'drift', it represents the drift correction.
    E_CORRECT
        Recognised by 'emission', it represents the emission correction.
    F_CORRECT
        Recognised by 'focus', it represents the focus correction.
    L1_NORM
        Recognised by 'Manhattan', it represents Manhattan distance calculation (the L1 norm of a vector).
    L2_NORM
        Recognised by 'Euclidean', it represents Euclidean distance calculation (the L2 norm of a vector).
    LP_NORM
        Recognised by 'Minkowski', it represents Minkowski distance calculation (the norm of a vector).
    ON
        Recognised by 'true', it represents the truthy boolean.
    OFF
        Recognised by 'false', it represents the falsey boolean.
    NULL
        Recognised by 'void', it represents an absence of a value.
    VAR_DEF
        Recognised by 'var', it represents variable definition.
    FUNC_DEF
        Recognised by 'func', it represents function definition.
    GEN_DEF
        Recognised by 'iter', it represents generator definition.
    ENUM_DEF
        Recognised by 'namespace', it represents an enumeration definition.
    LOOP_RANGE
        Recognised by 'for', it represents iteration using a c-style for loop.
    LOOP_ITER
        Recognised by 'foreach', it represents iteration using a python-style for loop.
    DELAY
        Recognised by 'wait', it represents delaying for a certain amount of time.
    EXIT
        Recognised by 'return', it represents exiting from a function.
    """
    SURVEY = "Scan"
    SEGMENT = "Cluster"
    FILTER = "filter"
    INTERACT = "Mark"
    MANAGE = "Tighten"
    SCAN = "Search"

    D_CORRECT = "drift"
    E_CORRECT = "emission"
    F_CORRECT = "focus"
    L1_NORM = "Manhattan"
    L2_NORM = "Euclidean"
    LP_NORM = "Minkowski"
    ON = "true"
    OFF = "false"
    NULL = "void"

    VAR_DEF = "var"
    FUNC_DEF = "func"
    GEN_DEF = "iter"
    ENUM_DEF = "namespace"
    LOOP_RANGE = "for"
    LOOP_ITER = "foreach"
    DELAY = "wait"
    EXIT = "return"


KEYWORDS_TYPE = {member.value: member for member in KeywordType}
TYPE_KEYWORDS = {v: k for k, v in KEYWORDS_TYPE.items()}


class Token:
    """
    Base token (also representing a symbol token).

    Attributes
    ----------
    _type: TokenType
        The particular token type.
    _value: str
        The lexeme (source string) of the token.
    _pos: tuple[int, int]
        The line and column of the token.
    """

    @property
    def token_type(self) -> TokenType:
        """
        Public access to the token type.

        Returns
        -------
        TokenType
            The particular token type.
        """
        return self._type

    @property
    def src(self) -> str:
        """
        Public access to the token source.

        Returns
        -------
        str
            The token's lexeme.
        """
        return self._value

    @property
    def position(self) -> _tuple[int, int]:
        """
        Public access to the token position.

        Returns
        -------
        tuple[int, int]
            The line and column of the token.
        """
        return self._pos

    @property
    def rc_ref(self) -> str:
        """
        Public access to a formatted version of the token's position.

        Returns
        -------
        str
            The line and column of the token in the form 'row:column'.
        """
        return ":".join(map(str, self._pos))

    def __init__(self, ty: TokenType, value: str, line: int, col: int):
        self._type = ty
        self._value = value
        self._pos = line, col

    def __str__(self) -> str:
        return f"Symbol {self._value!r} ({self._type.name} Token) at {self.rc_ref}"

    @staticmethod
    def from_symbol(symbol: str, line: int, col: int) -> "Token":
        """
        Method to construct a symbol token from the known symbol.

        Parameters
        ----------
        symbol: str
            The symbol encountered.
        line: int
            The line number of the symbol.
        col: int
            The column number of the symbol.

        Returns
        -------
        Token
            A symbol token, if the symbol is known, an error token if otherwise.
        """
        if (ty := SYMBOLS_TYPE.get(symbol)) is not None:
            return Token(ty, symbol, line, col)
        return ErrorToken(f"Unknown symbol {symbol!r}", line, col)

    @staticmethod
    def eof(line: int) -> "Token":
        """
        Special constructor for the EOF symbol.

        Parameters
        ----------
        line: int
            The last line of the program.

        Returns
        -------
        Token
            The EOF symbol token.
        """
        return Token.from_symbol(TYPE_SYMBOLS[TokenType.EOF], line + 1, 0)


class ErrorToken(Token):
    """
    Token subclass to represent an error token.
    """

    @property
    def message(self) -> str:
        """
        The error message.

        Returns
        -------
        str
            The token's lexeme combined with its formatted position.
        """
        return f"{self._value} at {self.rc_ref}"

    def __init__(self, message: str, line: int, col: int):
        super().__init__(TokenType.ERR, message, line, col)

    def __str__(self) -> str:
        return f"Error: {self._value!r} at {self.rc_ref}"


class MatchedToken(Token, _abc.ABC):
    """
    Abstract base class for tokens that are surrounded with a particular symbol.

    Abstract Methods
    ----------------
    __init__
    """

    @property
    def raw(self) -> str:
        """
        The raw lexeme of the token.

        Returns
        -------
        str
            The source string without the surrounding symbols.
        """
        return self._value[1:-1]

    @_abc.abstractmethod
    def __init__(self, ty: TokenType, value: str, line: int, col: int, pair: str):
        super().__init__(ty, f"{pair}{value}{pair}", line, col)

    def __str__(self) -> str:
        return f"{self.raw!r} ({self.token_type.name} Token) at {self.rc_ref}"


class StringToken(MatchedToken):
    """
    Concrete matched token for a string.
    """

    def __init__(self, value: str, line: int, col: int):
        super().__init__(TokenType.STRING, value, line, col, TYPE_SYMBOLS[TokenType.STRING])


class PathToken(MatchedToken):
    """
    Concrete matched token for a path.
    """

    def __init__(self, value: str, line: int, col: int):
        super().__init__(TokenType.PATH, value, line, col, TYPE_SYMBOLS[TokenType.PATH])


class KeywordToken(Token):
    """
    Token subclass to represent a particular keyword.
    """

    @property
    def keyword_type(self) -> KeywordType:
        """
        The particular keyword type.

        Returns
        -------
        KeywordType
            The type of keyword stored.
        """
        return KEYWORDS_TYPE[self._value]

    def __init__(self, value: str, line: int, col: int):
        super().__init__(TokenType.KEYWORD, value, line, col)

    def __str__(self) -> str:
        return f"Keyword {self._value!r} ({self.keyword_type.name} Token) at {self.rc_ref}"


class IdentifierToken(Token):
    """
    Token subclass to represent any variable identifier.
    """

    def __init__(self, value: str, line: int, col: int):
        super().__init__(TokenType.IDENTIFIER, value, line, col)

    def __str__(self) -> str:
        return f"Identifier {self._value!r} at {self.rc_ref}"


class BaseNumToken(Token, _abc.ABC):
    """
    Abstract base class for tokens that represent a numeric value.

    Abstract Methods
    ----------------
    __init__

    Attributes
    ----------
    BASE_MAP: dict[int, str]
        A mapping from base to string name.

    _num: str
        The name of the base.
    _transform: Callable[[str], int]
        The transformation from string to integer value.
    """
    BASE_MAP = {
        16: "Hexadecimal",
        2: "Binary",
        10: "Denary"
    }

    @property
    def value(self) -> float:
        """
        Public access to the numerical value.

        Returns
        -------
        float
            The numerical value, upcasted to a float.
        """
        return self._transform(self._value)

    @property
    def number_type(self) -> str:
        """
        The type of numeric value.

        Returns
        -------
        str
            The string representing the base.
        """
        return self._num

    @_abc.abstractmethod
    def __init__(self, ty: TokenType, code: str, line: int, col: int, base: int):
        self._num = self.BASE_MAP[base]
        self._transform = _functools.partial(int, base=base)
        super().__init__(ty, code, line, col)

    def __str__(self) -> str:
        return f"{float(self.value)!r} ({self._num} Token) at {self.rc_ref}"


class HexToken(BaseNumToken):
    """
    Concrete number token representing a hexadecimal integer.
    """

    def __init__(self, nibbles: str, line: int, col: int):
        super().__init__(TokenType.HEX, nibbles, line, col, 16)


class BinToken(BaseNumToken):
    """
    Concrete number token representing a binary integer.
    """

    def __init__(self, bits: str, line: int, col: int):
        super().__init__(TokenType.BIN, bits, line, col, 2)


class NumToken(BaseNumToken):
    """
    Concrete number token representing a denary value. This can be a float or an integer
    """

    @property
    def value(self) -> float:
        return self._v

    def __init__(self, digits: float, line: int, col: int):
        self._v = digits
        super().__init__(TokenType.NUM, str(digits), line, col, 10)
