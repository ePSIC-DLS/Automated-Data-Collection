from typing import Optional as _None


class InstructionPointer:
    """
    A class to represent a pointer to a series of instructions.

    Attributes
    ----------
    _code: tuple[int, ...]
        The instructions to point to.
    _i: int
        The current instruction index.

    Raises
    ------
    ValueError
        If no instructions are specified.
    """

    def __init__(self, *instructions: int):
        if not instructions:
            raise ValueError("Instructions cannot be empty")
        self._code = instructions
        self._i = 0

    def advance(self) -> int:
        """
        Advance the pointer forward.

        Returns
        -------
        int
            The instruction just passed.
        """
        self._i += 1
        return self.peek()

    def peek(self, by=1) -> _None[int]:
        """
        Peek at the next instruction.

        Parameters
        ----------
        by: int
            The number of instructions to skip.

        Returns
        -------
        int | None
            The instruction at the correct index after skipping. None if the instruction goes beyond the pointer.

        Raises
        ------
        ValueError
            If the peek is not a natural number.
        """
        if by <= 0:
            raise ValueError("Peek must be a lookahead")
        if self._i >= len(self._code):
            return
        return self._code[self._i + (by - 1)]

    def previous(self) -> int:
        """
        Peek at the previous instruction.

        Returns
        -------
        int
            The previous instruction.

        Raises
        ------
        ValueError
            If the previous instruction is non-existent.
        """
        if self._i == 0:
            raise ValueError("Pointer is at start")
        return self._code[self._i - 1]

    def at(self) -> int:
        """
        Find the current working index.

        Returns
        -------
        int
            The index of the next instruction to execute.
        """
        return self._i

    def jump(self, jump: int):
        """
        Skip over a series of instructions.

        Parameters
        ----------
        jump: int
            The number of instructions to skip.
        """
        self._i += jump
