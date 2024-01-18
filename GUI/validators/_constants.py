import enum
import typing

__all__ = ["_lowers", "_uppers", "_nums", "_file_path_chars", "_T1", "_T2", "_K", "_TS", "_TD1", "_TD2", "_Enum",
           "_Flag", "_Num", "Include", "UnaryOperator", "BinaryOperator"]

_lowers = set("abcdefghijklmnopqrstuvwxyz")
_uppers = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
_nums = set("1234567890")
_file_path_chars = {"_", "/", ".", "-", ":"}

_T1 = typing.TypeVar("_T1")
_T2 = typing.TypeVar("_T2")
_K = typing.TypeVar("_K")
_TS = typing.TypeVar("_TS")
_TD1 = typing.TypeVar("_TD1")
_TD2 = typing.TypeVar("_TD2")
_Enum = typing.TypeVar("_Enum", bound=enum.Enum)
_Flag = typing.TypeVar("_Flag", bound=enum.Flag)
_Num = typing.TypeVar("_Num", int, float)


class Include(enum.Flag):
    """
    Enumeration to represent boundary conditions for values. These are different ways to include the boundaries.

    :cvar LOW:
    :cvar HIGH:
    :cvar NONE:
    """
    LOW = enum.auto()
    HIGH = enum.auto()

    NONE = LOW & HIGH


class UnaryOperator(enum.Enum):
    NEGATIVE = "-"
    POSITIVE = "+"
    INVERT = "~"


class BinaryOperator(enum.Enum):
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    TRUE_DIVISION = "/"
    FLOOR_DIVISION = "//"
    EXPONENT = "**"
    MATRIX_MULTIPLICATION = "@"
    BITWISE_OR = "|"
    BITWISE_AND = "&"
    BITWISE_XOR = "^"
