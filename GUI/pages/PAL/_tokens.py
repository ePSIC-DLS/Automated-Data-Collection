import abc
import enum
from modular_qt import microscope, validators


class TokenType(enum.Enum):
    """
    Enumeration to represent all types of token.

    :cvar NUM:
    :cvar EOF:
    :cvar KEYWORD:
    :cvar CLICK:
    :cvar FILE:
    :cvar ERROR:
    :cvar ASSIGN:
    :cvar IDENTIFIER:
    :cvar START_CALL:
    :cvar END_CALL:
    :cvar SEPARATOR:
    :cvar ACCESS:
    :cvar ENUM:
    :cvar START_GROUP:
    :cvar END_GROUP:
    """
    NUM = enum.auto()
    EOF = enum.auto()
    KEYWORD = enum.auto()
    CLICK = enum.auto()
    FILE = enum.auto()
    ERROR = enum.auto()
    ASSIGN = enum.auto()
    IDENTIFIER = enum.auto()
    START_CALL = enum.auto()
    END_CALL = enum.auto()
    SEPARATOR = enum.auto()
    ACCESS = enum.auto()
    ENUM = enum.auto()
    START_GROUP = enum.auto()
    END_GROUP = enum.auto()
    STR = enum.auto()


class IdentifierType(enum.Enum):
    """
    Enumeration to represent the different types of identifier.

    :cvar UNKNOWN:
    :cvar FUNCTION:
    :cvar HARDWARE:
    :cvar KEY:
    :cvar VARIABLE:
    """
    UNKNOWN = enum.auto()
    FUNCTION = enum.auto()
    HARDWARE = enum.auto()
    KEY = enum.auto()
    VARIABLE = enum.auto()


class KeywordType(enum.Enum):
    """
    Enumeration to represent the different keywords in PAL.

    :cvar WRITE:
    :cvar READ:
    :cvar SAMPLE:
    :cvar BW_T:
    :cvar BW_E:
    :cvar GROUP:
    :cvar INTERACT:
    :cvar TIGHTEN:
    :cvar SCAN:
    :cvar ALL:
    :cvar SHAPE_RECTANGLE:
    :cvar SHAPE_PLUS:
    :cvar SHAPE_ELLIPSE:
    :cvar MINMAX:
    :cvar MIN:
    :cvar MAX:
    :cvar NONE:
    :cvar ON:
    :cvar OFF:
    :cvar ALGORITHM_MANHATTAN:
    :cvar ALGORITHM_EUCLIDEAN:
    :cvar ALGORITHM_MINKOWSKI:
    :cvar LOOP:
    """
    WRITE = enum.auto()
    READ = enum.auto()
    SAMPLE = enum.auto()
    BW_T = enum.auto()
    BW_E = enum.auto()
    GROUP = enum.auto()
    INTERACT = enum.auto()
    TIGHTEN = enum.auto()
    SCAN = enum.auto()
    ALL = enum.auto()
    SHAPE_RECTANGLE = enum.auto()
    SHAPE_PLUS = enum.auto()
    SHAPE_ELLIPSE = enum.auto()
    MINMAX = enum.auto()
    MIN = enum.auto()
    MAX = enum.auto()
    NONE = enum.auto()
    ON = enum.auto()
    OFF = enum.auto()
    ALGORITHM_MANHATTAN = enum.auto()
    ALGORITHM_EUCLIDEAN = enum.auto()
    ALGORITHM_MINKOWSKI = enum.auto()
    LOOP = enum.auto()


TYPE_SYMBOLS = {
    TokenType.EOF: "",
    TokenType.CLICK: "@",
    TokenType.FILE: "\"",
    TokenType.ENUM: "\'",
    TokenType.ASSIGN: "=",
    TokenType.SEPARATOR: ",",
    TokenType.START_CALL: "(",
    TokenType.END_CALL: ")",
    TokenType.ACCESS: ".",
    TokenType.START_GROUP: "{",
    TokenType.END_GROUP: "}",
    TokenType.STR: "%"
}

SYMBOLS_TYPE = {v: k for k, v in TYPE_SYMBOLS.items()}

KEYWORDS_TYPE = {
    "save": KeywordType.WRITE,
    "recall": KeywordType.READ,
    "scan": KeywordType.SAMPLE,
    "threshold": KeywordType.BW_T,
    "edge": KeywordType.BW_E,
    "cluster": KeywordType.GROUP,
    "click": KeywordType.INTERACT,
    "tighten": KeywordType.TIGHTEN,
    "search": KeywordType.SCAN,
    "all": KeywordType.ALL,
    "rect": KeywordType.SHAPE_RECTANGLE,
    "cross": KeywordType.SHAPE_PLUS,
    "ellipse": KeywordType.SHAPE_ELLIPSE,
    "both": KeywordType.MINMAX,
    "min": KeywordType.MIN,
    "max": KeywordType.MAX,
    "null": KeywordType.NONE,
    "true": KeywordType.ON,
    "false": KeywordType.OFF,
    "Manhattan": KeywordType.ALGORITHM_MANHATTAN,
    "Euclidean": KeywordType.ALGORITHM_EUCLIDEAN,
    "Minkowski": KeywordType.ALGORITHM_MINKOWSKI,
    "repeat": KeywordType.LOOP
}

TYPE_KEYWORDS = {v: k for k, v in KEYWORDS_TYPE.items()}

FUNCTIONS = {"gss_blur", "blur", "sharpen", "median", "open", "close", "gradient", "i_gradient", "e_gradient"}

HARDWARE = {"global", "apt", "detector", "deflector", "eos", "feg", "gun", "ht", "lens", "scan", "stage"}

VARIABLES: dict[str, validators.Pipeline] = {
    "lowest_colour": validators.xmpls.colour,
    "highest_colour": validators.xmpls.colour,
    "invert": validators.xmpls.checkbox,
    "epsilon": validators.xmpls.epsilon,
    "minimum_samples": validators.xmpls.minimum_samples,
    "algorithm": validators.xmpls.algorithm,
    "square": validators.xmpls.checkbox,
    "power": validators.xmpls.power,
    "overlap": validators.xmpls.overlap,
    "padding": validators.xmpls.padding,
    "cluster_size": validators.xmpls.size,
    "min_cluster_height": validators.xmpls.size,
    "match": validators.xmpls.match,
    "merlin": validators.xmpls.checkbox,
    "session": validators.xmpls.file_path,
    "sample": validators.xmpls.file_path,
    "scan_size": validators.xmpls.scan_size,
    "exposure_time": validators.xmpls.exposure,
    "bit_depth": validators.xmpls.bit_depth,
    "save_path": validators.xmpls.save_path,
    "captures": validators.xmpls.captures
}

KEYS: dict[str, dict[str, validators.Pipeline]] = {
    "global": microscope.Microscope.validators(),
    "apt": microscope.Apt.validators(),
    "detector": microscope.Det.validators(),
    "deflector": microscope.Def.validators(),
    "eos": microscope.Eos.validators(),
    "feg": microscope.Feg.validators(),
    "gun": microscope.Gun.validators(),
    "ht": microscope.Ht.validators(),
    "lens": microscope.Len.validators(),
    "scan": microscope.Scan.validators(),
    "stage": microscope.Stage.validators()
}

STATEMENTS = {KeywordType.WRITE, KeywordType.READ, KeywordType.SAMPLE, KeywordType.BW_T, KeywordType.BW_E,
              KeywordType.GROUP, KeywordType.INTERACT, KeywordType.TIGHTEN, KeywordType.SCAN, KeywordType.LOOP}

EXPRS = {KeywordType.SAMPLE, KeywordType.BW_T, KeywordType.GROUP, KeywordType.SCAN, KeywordType.ON, KeywordType.OFF,
         KeywordType.ALGORITHM_MINKOWSKI, KeywordType.ALGORITHM_EUCLIDEAN, KeywordType.ALGORITHM_MANHATTAN,
         KeywordType.SHAPE_PLUS, KeywordType.SHAPE_ELLIPSE, KeywordType.SHAPE_RECTANGLE}

ESTIMATORS = {KeywordType.NONE, KeywordType.MINMAX, KeywordType.MIN, KeywordType.MAX}


class Token:
    """
    Base token class (represents a symbol token).

    :var TokenType _type: The type of token it is. Most subclasses have this predefined.
    :var str _value: The string source that created the token.
    :var tuple[int, int] _pos: The line and column of the token within the source code.
    """

    @property
    def position(self) -> tuple[int, int]:
        """
        Public access to the position.

        :return: The line and column of the token within the source code.
        """
        return self._pos

    @property
    def token_type(self) -> TokenType:
        """
        Public access to the token type.

        :return: The type of token it is.
        """
        return self._type

    @property
    def src(self) -> str:
        """
        Public access to the token's value.

        :return: The string source that created the token.
        """
        return self._value

    def __init__(self, ty: TokenType, value: str, line: int, col: int):
        self._type = ty
        self._value = value
        self._pos = (line, col)

    def __str__(self) -> str:
        return f"{self._type.name} Token({self._value!r}) at {self._pos}"

    @staticmethod
    def from_symbol(symbol: str, line: int, col: int) -> "Token":
        """
        Special symbol token constructor to construct a token from a known symbol.

        :param symbol: The symbol as a string source.
        :param line: The line number where the symbol occurs.
        :param col: The column position of the symbol on the line.
        :return: A base token if the symbol is known, an error token otherwise.
        """
        if (sym_type := SYMBOLS_TYPE.get(symbol)) is not None:
            return Token(sym_type, symbol, line, col)
        return ErrorToken(f"Unknown symbol: {symbol!r}", line, col)

    @staticmethod
    def eof(line: int) -> "Token":
        """
        Special form for creating an End Of File token.

        :param line: The last line of the file.
        :return: The EOF token (on a new line at column 0).
        """
        return Token.from_symbol(TYPE_SYMBOLS[TokenType.EOF], line + 1, 0)


class MatchedToken(Token, abc.ABC):
    """
    Abstract class to represent a singular token between two matched pairs.
    """

    @abc.abstractmethod
    def __init__(self, ty: TokenType, value: str, line: int, col: int, pair: tuple[str, str]):
        o, c = pair
        super().__init__(ty, f"{o}{value}{c}", line, col)


class FileToken(MatchedToken):
    """
    Special case of matched token representing a filepath.
    """

    def __init__(self, path: str, line: int, col: int):
        super().__init__(TokenType.FILE, path, line, col, (TYPE_SYMBOLS[TokenType.FILE],) * 2)


class EnumToken(MatchedToken):
    """
    Special case of matched token representing an enumeration.
    """

    def __init__(self, value: str, line: int, col: int):
        super().__init__(TokenType.ENUM, value, line, col, (TYPE_SYMBOLS[TokenType.ENUM],) * 2)


class StringToken(MatchedToken):
    """
    Special case of matched token representing a string.
    """

    def __init__(self, value: str, line: int, col: int):
        super().__init__(TokenType.STR, value, line, col, (TYPE_SYMBOLS[TokenType.STR],) * 2)


class KeywordToken(Token):
    """
    Special token representing a keyword.

    Type is locked at KEYWORD.
    """

    @property
    def type(self) -> KeywordType:
        """
        Public access to the type of keyword.

        :return: The keyword type this token represents.
        """
        return KEYWORDS_TYPE[self._value]

    def __init__(self, name: str, line: int, col: int):
        super().__init__(TokenType.KEYWORD, name, line, col)

    def __str__(self) -> str:
        return f"{self.type.name} {super().__str__()}"


class IdentifierToken(Token):
    """
    Special token representing an identifier.

    Type is locked at IDENTIFIER.

    :var bool _access: Whether the identifier is a key or not.
    """
    identifier = Token.src

    @property
    def type(self) -> IdentifierType:
        """
        Public access to the type of identifier.

        :return: The name identifier set this token belongs to.
        """
        if self._access:
            return IdentifierType.KEY
        elif self._value in VARIABLES:
            return IdentifierType.VARIABLE
        elif self._value in HARDWARE:
            return IdentifierType.HARDWARE
        elif self._value in FUNCTIONS:
            return IdentifierType.FUNCTION
        return IdentifierType.UNKNOWN

    def __init__(self, name: str, line: int, col: int, post_dot: bool):
        super().__init__(TokenType.IDENTIFIER, name, line, col)
        self._access = post_dot

    def __str__(self) -> str:
        return f"{self.type.name} {super().__str__()}"


class NumberToken(Token):
    """
    Special token representing a numerical value.

    Type is locked at NUM.

    :var type[int | float] _transform: The type of number represented by this token.
    """

    @property
    def value(self) -> float:
        """
        Public access to the numerical value.

        :return: A number from the token's value.
        """
        return self._transform(float(self._value))

    def __init__(self, value: float, line: int, col: int):
        self._transform = int if int(value) == value else float
        super().__init__(TokenType.NUM, f"{value}", line, col)

    @staticmethod
    def zero(line: int, col: int) -> "NumberToken":
        """
        Special form for creating a token representing zero.

        :param line: The line number of the zero.
        :param col: The column position of the zero on the line.
        :return: The number with an integer value of 0.
        """
        return NumberToken(0, line, col)


class ErrorToken(Token):
    """
    Special token representing a lexer error. The value is the error message.

    Type is locked at ERROR.
    """
    err = Token.src

    def __init__(self, message: str, line: int, col: int):
        super().__init__(TokenType.ERROR, message, line, col)
