import enum
import functools
import typing
from typing import List as _list, Tuple as _tuple


class OpCodes(enum.Enum):
    CONSTANT = enum.auto()
    TRUE = enum.auto()
    FALSE = enum.auto()
    NULL = enum.auto()

    NEGATE = enum.auto()
    INVERT = enum.auto()
    POWER = enum.auto()
    ADD = enum.auto()
    SUB = enum.auto()
    EQUAL = enum.auto()
    LESS = enum.auto()
    MORE = enum.auto()
    MIX = enum.auto()
    PRINT = enum.auto()

    GET_GLOBAL = enum.auto()
    SET_GLOBAL = enum.auto()
    GET_LOCAL = enum.auto()
    SET_LOCAL = enum.auto()

    LOOP = enum.auto()
    FALSEY_JUMP = enum.auto()
    ALWAYS_JUMP = enum.auto()
    ADVANCE = enum.auto()

    POP = enum.auto()
    DEF_GLOBAL = enum.auto()
    ENUM = enum.auto()
    GET_FIELD = enum.auto()
    DEF_FIELD = enum.auto()
    DEF_ELEM = enum.auto()

    RETURN = enum.auto()
    CALL = enum.auto()
    YIELD = enum.auto()

    SLEEP = enum.auto()
    SCAN = enum.auto()
    CLUSTER = enum.auto()
    FILTER = enum.auto()
    MARK = enum.auto()
    TIGHTEN = enum.auto()
    SEARCH = enum.auto()


def opcode_is(dset: _tuple[str, ...], code: int) -> str:
    for n, v in zip(dset, map(lambda x: OpCodes[x].value, dset)):
        if code == v:
            return n
    return ""


SIMPLE = ("RETURN", "NEGATE", "POWER", "INVERT", "ADD", "SUB", "EQUAL", "LESS", "MORE", "TRUE", "FALSE", "POP", "PRINT",
          "NULL", "SLEEP", "SCAN", "CLUSTER", "FILTER", "MARK", "TIGHTEN", "SEARCH", "YIELD", "ADVANCE", "MIX")
CONSTANT = ("CONSTANT", "DEF_GLOBAL", "GET_GLOBAL", "SET_GLOBAL", "ENUM", "GET_FIELD", "DEF_FIELD", "DEF_ELEM")
BYTE = ("GET_LOCAL", "SET_LOCAL", "CALL")
JUMP_DOWN = ("FALSEY_JUMP", "ALWAYS_JUMP")
JUMP_UP = ("LOOP",)


def disassemble(instructions: _list[int], offset: int, values: _list[str], end: str,
                output: typing.Callable[[str], None] = None) -> int:
    if output is None:
        output = functools.partial(print, end=end)
    code = instructions[offset]
    if name := opcode_is(SIMPLE, code):
        output(name)
        return 1
    elif name := opcode_is(CONSTANT, code):
        constant = instructions[offset + 1]
        output(f"{name: <{len(name) + 2}} {constant:04}: {values[constant]}")
        return 2
    elif name := opcode_is(BYTE, code):
        slot = instructions[offset + 1]
        output(f"{name: <{len(name) + 2}} {slot:04}")
        return 2
    elif name := opcode_is(JUMP_DOWN, code):
        jump = instructions[offset + 1]
        output(f"{name: <{len(name) + 2}} {offset:04} -> {offset + 2 + jump:04}")
        return 2
    elif name := opcode_is(JUMP_UP, code):
        jump = instructions[offset + 1]
        output(f"{name: <{len(name) + 2}} {offset:04} -> {offset + 2 - jump:04}")
        return 2
