import functools

from ..grammar import OpCodes, disassemble
from typing import List as _list
from ._value import Value
import typing


class Chunk:

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
        if not code:
            raise ValueError("No code to write")
        self._count += len(code)
        self._code.extend(map(lambda x: getattr(x, "value", x), code))
        self._lines.extend((line,) * len(code))

    def add(self, v: Value) -> int:
        self._constants.append(v)
        self._c_max += 1
        return self._c_max

    def constant(self, i: int) -> Value:
        return self._constants[i]

    def line(self, i: int) -> int:
        return self._lines[i]

    def disassemble(self, name: str):
        i, n = 0, len(self._code)
        print(f"{name:=^{len(name) + 6}}")
        while i < n:
            i = self.dissassemble_line(i, "\n")

    def dissassemble_line(self, index: int, end: str, output: typing.Callable[[str], None] = None) -> int:
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
