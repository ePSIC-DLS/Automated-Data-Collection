import functools

from ..grammar import OpCodes, disassemble
from typing import List as _list
from ._value import Value
import typing


class Chunk:
    """
    Class to represent a series of bytecode instructions that can be executed.

    Attributes
    ----------
    _code: list[int]
        The instructions to be executed. Note that they are reduced down to integers, so that the operations are
        homogenous with the operands.
    _constants: list[Value]
        The constants that this chunk has. Note that when loading a constant, the index is saved in the instruction list
        as an operand.
    _lines: list[int]
        The line numbers of each instruction.
    _count: int
        The number of instructions this chunk has.
    _c_max: int
        The index of the most recently added constant.
    """

    def __init__(self):
        self._code: _list[int] = []
        self._constants: _list[Value] = []
        self._lines: _list[int] = []
        self._count = 0
        self._c_max = -1

    def __iter__(self) -> int:
        yield from self._code

    def __len__(self) -> int:
        return self._count

    def __setitem__(self, i: int, value: int) -> None:
        self._code[i] = value

    def write(self, *code: typing.Union[OpCodes, int], line: int):
        """
        Write a series of instructions to the chunk. Note that they are all assumed to be on the same line.

        Parameters
        ----------
        *code: OpCodes | int
            The instructions to write.
        line: int
            The line number that the instructions appear in the source code.

        Raises
        ------
        ValueError
            If there are no instructions.
        """
        if not code:
            raise ValueError("No code to write")
        self._count += (count := len(code))
        self._code.extend(map(lambda x: getattr(x, "value", x), code))
        self._lines.extend((line,) * count)

    def add(self, v: Value) -> int:
        """
        Add a value to the chunk.

        Parameters
        ----------
        v: Value
            The value to add.

        Returns
        -------
        int
            The index of the value added.
        """
        self._constants.append(v)
        self._c_max += 1
        return self._c_max

    def constant(self, i: int) -> Value:
        """
        Retrieve a constant from the chunk.

        Parameters
        ----------
        i: int
            The index of the constant.

        Returns
        -------
        Value
            The constant at that particular index.
        """
        return self._constants[i]

    def line(self, i: int) -> int:
        """
        Retrieve the line number of a particular instruction.

        Parameters
        ----------
        i: int
            The index of the instruction.

        Returns
        -------
        int
            The line number at that particular index.
        """
        return self._lines[i]

    def disassemble(self, name: str):
        """
        Disassemble a chunk using the given name.

        This will output all instructions in the chunk, with a header for the given name.

        Parameters
        ----------
        name: str
            The name of the chunk to output.
        """
        i, n = 0, len(self._code)
        print(f"{name:=^{len(name) + 6}}")
        while i < n:
            i = self.disassemble_line(i, "\n")

    def disassemble_line(self, index: int, end: str, output: typing.Callable[[str], None] = None) -> int:
        """
        Disassemble a particular instruction, based on the index.

        Parameters
        ----------
        index: int
            The index of the instruction to disassemble.
        end: str
            The final output.
        output: Callable[[str], None] | None
            The output function. If not defined, will use the `print` function, with a fixed ending string of a space.

        Returns
        -------
        int
            The next index to disassemble.
        """
        passthrough = output
        if output is None:
            output = functools.partial(print, end=" ")
        output(f"{index:04}")
        line = self._lines[index]
        if index and self._lines[index - 1] == line:
            output("|".rjust(4))
        else:
            output(f"{line:04}")
        i = index + disassemble(self._code, index, list(map(str, self._constants)), end, passthrough)
        if passthrough is None:
            output(end)
        return i
