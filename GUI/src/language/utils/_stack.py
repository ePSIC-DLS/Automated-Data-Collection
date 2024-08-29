import typing
from typing import List as _list

T = typing.TypeVar("T")


class Stack(typing.Generic[T]):
    """
    Class to represent a stack of items, with a defined top and bottom to allow for linking stacks.

    Generics
    --------
    T
        The value type.

    Attributes
    ----------
    _stack: list[T]
        The actual stack, implemented as a list.
    _min: int
        The lowest index of the stack.
    _max: int
        The highest index of the stack.
    """

    @property
    def top(self) -> int:
        """
        Public access to the top index of the stack.

        Returns
        -------
        int
            The highest index of the stack.
        """
        return self._max

    @top.setter
    def top(self, value: int):
        if value < len(self._stack) - 1:
            self._stack = self._stack[:value]
        self._max = value

    @property
    def bottom(self) -> int:
        """
        Public access to the bottom index of the stack.

        Returns
        -------
        int
            The lowest index of the stack.
        """
        return self._min

    def __init__(self, offset=0):
        self._stack: _list[T] = []
        self._min, self._max = offset, 0

    def __str__(self) -> str:
        build = []
        for i, elem in enumerate(self._stack):
            if i == self._min:
                build.append(f"|{elem}")
            elif i == self._max:
                build.append(f"{elem}|")
            else:
                build.append(f"{elem}")
        return f"{{{', '.join(build)}}}"

    def __iter__(self) -> typing.Iterator[T]:
        yield from self._stack[self._min:self._max]

    def __getitem__(self, offset: int) -> T:
        if self._min + offset >= self._max:
            raise IndexError("Stack overflow")
        return self._stack[self._min + offset]

    def __setitem__(self, offset: int, value: T) -> None:
        self._stack[self._min + offset] = value

    def __lshift__(self, other: int) -> "Stack[T]":
        new = Stack(self._max - other)
        for elem in self._stack:
            new.push(elem)
        return new

    def push(self, item: T):
        """
        Push a new item to the stack, changing the top.

        Parameters
        ----------
        item: T
            The item to push.
        """
        self._stack.append(item)
        self._max += 1

    def pop(self) -> T:
        """
        Pop the top item from the stack, changing the top.

        Returns
        -------
        T
            The top item from the stack.
        """
        self._max -= 1
        return self._stack.pop()

    def peek(self, depth=0) -> T:
        """
        Peek a certain depth down the stack.

        Parameters
        ----------
        depth: int
            The number of items to peek down.
            By default, this is 0 which means the top item.

        Returns
        -------
        T
            The item at the peeked index.
        """
        if not (self._min <= self._max - depth - 1 < self._max):
            raise ValueError("Invalid peek index")
        return self._stack[self._max - depth - 1]
