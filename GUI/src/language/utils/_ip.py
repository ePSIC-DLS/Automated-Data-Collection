from typing import Optional as _None


class InstructionPointer:

    def __init__(self, *instructions: int):
        if not instructions:
            raise ValueError("Instructions cannot be empty")
        self._code = instructions
        self._i = 0

    def advance(self) -> int:
        self._i += 1
        return self.peek()

    def peek(self, by=1) -> _None[int]:
        if by <= 0:
            raise ValueError("Peek must be a lookahead")
        if self._i >= len(self._code):
            return None
        return self._code[self._i + (by - 1)]

    def previous(self) -> int:
        if self._i == 0:
            raise ValueError("Pointer is at start")
        return self._code[self._i - 1]

    def at(self) -> int:
        return self._i

    def jump(self, jump: int):
        self._i += jump
