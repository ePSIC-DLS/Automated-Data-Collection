import enum
import functools
import typing
from typing import List as _list, Tuple as _tuple


class OpCodes(enum.Enum):
    """
    Enumeration of all possible opcodes.

    Members
    -------
    CONSTANT
        Represent pushing a constant onto the stack.
    TRUE
        Represent creating a truthy constant.
    FALSE
        Represent creating a falsey constant.
    NULL
        Represent creating a null constant.
    NEGATE
        Represent negating the topmost value on the stack.
    INVERT
        Represent inverting the topmost value on the stack.
    POWER
        Represent performing a power operation on the two topmost values on the stack.
    ADD
        Represent adding the two topmost values on the stack.
    SUB
        Represent subtracting the two topmost values on the stack.
    EQUAL
        Represent equality checks on the two topmost values on the stack.
    LESS
        Represent ordered checks on the two topmost values on the stack.
    MORE
        Represent ordered checks on the two topmost values on the stack.
    MIX
        Represent mixing the two topmost values on the stack.
    PRINT
        Represent outputting the topmost value of the stack to the console.
    GET_GLOBAL
        Represent getting a global variable.
    SET_GLOBAL
        Represent setting a global variable.
    GET_LOCAL
        Represent getting a local variable.
    SET_LOCAL
        Represent setting a local variable.
    LOOP
        Represent jumping backwards through instructions, acting as iteration.
    FALSEY_JUMP
        Represent jumping forwards through instructions, only when the topmost stack value is falsey.
    ALWAYS_JUMP
        Represent jumping forwards through instructions, acting as a non-conditional jump.
    ADVANCE
        Represent advancing the topmost value on the stack (assumes it's an iterator).
    POP
        Represent forgetting the topmost value of the stack.
    DEF_GLOBAL
        Represent defining a global variable.
    ENUM
        Represent defining an enumerated type.
    GET_FIELD
        Represent getting a field from an enumerated type.
    DEF_FIELD
        Represent defining a field for an enumerated type.
    RETURN
        Represent exiting a function (or generator).
    CALL
        Represent calling a function (or generator).
    YIELD
        Represent pausing a generator, returning its value.
    SLEEP
        Represent delaying program execution.
    SCAN
        Has no known language implementation, but calls an external service (the GUI) for its function.
    CLUSTER
        Has no known language implementation, but calls an external service (the GUI) for its function.
    FILTER
        Has no known language implementation, but calls an external service (the GUI) for its function.
    MARK
        Has no known language implementation, but calls an external service (the GUI) for its function.
    TIGHTEN
        Has no known language implementation, but calls an external service (the GUI) for its function.
    SEARCH
        Has no known language implementation, but calls an external service (the GUI) for its function.
    """
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
    """
    Function to determine if a particular opcode belongs to a particular dataset.

    Parameters
    ----------
    dset: tuple[str, ...]
        The dataset of names to check for.
    code: int
        The opcode value to check.

    Returns
    -------
    str
        The name of the opcode. This will be an empty string if the opcode isn't in the dataset.
    """
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
    """
    Disassemble a particular instruction, based on a series of instructions and an offset.

    Note that it uses a list of instructions and an index (as opposed to a singular instruction) as this function
    returns a new offset to use for the next instruction therefore, each jump is inconsistent.

    Parameters
    ----------
    instructions: list[int]
        The series of instructions to index.
    offset: int
        The index of the instruction.
    values: list[str]
        The list of constant values.
    end: str
        The ending string to use (when no output function is provided).
    output: Callable[[str], None] | None
        The output function to use. When not provided, will use the `print` function with a fixed ending value.

    Returns
    -------
    int
        The new offset to use for the next instruction.
    """
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
