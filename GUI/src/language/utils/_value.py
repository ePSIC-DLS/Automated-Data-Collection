import abc
import typing
import enum
from typing import Optional as _None, List as _list
from ._stack import Stack

T = typing.TypeVar("T")


class Interpreter(abc.ABC):
    stack: Stack["Value"]

    @abc.abstractmethod
    def new_frame(self, fn, vs: Stack["Value"]):
        pass

    @abc.abstractmethod
    def error(self, msg: str) -> bool:
        pass


class ValueType(enum.Enum):
    NUM = enum.auto()
    BOOL = enum.auto()
    VOID = enum.auto()
    STRING = enum.auto()
    LIST = enum.auto()
    OBJECT = enum.auto()


class Value(abc.ABC, typing.Generic[T]):
    NAME = "Obj"

    @property
    def raw(self) -> T:
        return self._value

    def __init__(self, vt: ValueType, vv: T):
        self._vt = vt
        self._value = vv

    @abc.abstractmethod
    def __str__(self) -> str:
        pass

    def is_true(self) -> bool:
        return True

    def negate(self) -> "Value":
        raise TypeError(f"{self.NAME} objects cannot be negated")

    def invert(self) -> "Value":
        raise TypeError(f"{self.NAME} objects cannot be inverted")

    def call(self, interpreter: Interpreter, count: int) -> bool:
        return False

    def power(self, other: "Value") -> _None["Value"]:
        return

    def r_power(self, other: "Value") -> _None["Value"]:
        return

    def add(self, other: "Value") -> _None["Value"]:
        return

    def r_add(self, other: "Value") -> _None["Value"]:
        return

    def sub(self, other: "Value") -> _None["Value"]:
        return

    def r_sub(self, other: "Value") -> _None["Value"]:
        return

    def mix(self, other: "Value") -> _None["Value"]:
        return

    def r_mix(self, other: "Value") -> _None["Value"]:
        return

    def equal(self, other: "Value") -> _None["Value"]:
        return

    def less(self, other: "Value") -> _None["Value"]:
        return

    def more(self, other: "Value") -> _None["Value"]:
        return


class Number(Value[float]):
    NAME = "Num"

    def __init__(self, num: float):
        super().__init__(ValueType.NUM, float(num))

    def __str__(self) -> str:
        return f"{self._value:.3e}"

    def is_int(self) -> bool:
        return self._value == int(self._value)

    def is_true(self) -> bool:
        return self._value != 0

    def negate(self) -> "Value":
        return Number(-self._value)

    def power(self, other: "Value") -> _None["Value"]:
        if isinstance(other, Number) and other.is_int():
            return Number(self._value * 10 ** other.raw)
        return super().power(other)

    def add(self, other: "Value") -> _None["Value"]:
        if isinstance(other, Number):
            return Number(self._value + other.raw)
        return super().add(other)

    def sub(self, other: "Value") -> _None["Value"]:
        if isinstance(other, Number):
            return Number(self._value - other.raw)
        return super().add(other)

    def mix(self, other: "Value") -> _None["Value"]:
        if isinstance(other, Number) and other.is_int() and self.is_int():
            return Number(int(self._value) | int(other.raw))
        return super().mix(other)

    def equal(self, other: "Value") -> _None["Value"]:
        if isinstance(other, Number):
            return Bool(self._value == other.raw)
        return super().add(other)

    def less(self, other: "Value") -> _None["Value"]:
        if isinstance(other, Number):
            return Bool(self._value < other.raw)
        return super().add(other)

    def more(self, other: "Value") -> _None["Value"]:
        if isinstance(other, Number):
            return Bool(self._value > other.raw)
        return super().add(other)


class Bool(Value[bool]):
    NAME = "Boolean"

    def __init__(self, state: bool):
        super().__init__(ValueType.BOOL, state)

    def __str__(self) -> str:
        return "on" if self._value else "off"

    def is_true(self) -> bool:
        return self._value

    def invert(self) -> "Value":
        return Bool(not self._value)

    def equal(self, other: "Value") -> _None["Value"]:
        if isinstance(other, Bool):
            return Bool(self._value == other.raw)
        elif isinstance(other, Number):
            return Bool(other.raw == 1)
        return super().add(other)


class Nil(Value[None]):
    NAME = "None"

    def __init__(self):
        super().__init__(ValueType.VOID, None)

    def __str__(self) -> str:
        return f"NilVal"

    def is_true(self) -> bool:
        return False

    def equal(self, other: "Value") -> _None["Value"]:
        return Bool(isinstance(other, Nil))


class String(Value[str]):
    NAME = "Str"

    def __init__(self, chars: str):
        super().__init__(ValueType.STRING, chars)

    def __hash__(self) -> int:
        return hash(self._value)

    def __eq__(self, other: "String") -> bool:
        if not isinstance(other, String):
            return NotImplemented
        return self._value == other.raw

    def __str__(self) -> str:
        return f"\"{self._value}\""

    def is_true(self) -> bool:
        return bool(self._value)

    def add(self, other: "Value") -> _None["Value"]:
        if isinstance(other, String):
            return String(self._value + other.raw)
        return super().add(other)

    def equal(self, other: "Value") -> _None["Value"]:
        if isinstance(other, String):
            return Bool(self._value == other.raw)
        return super().equal(other)


class Path(Value[str]):
    NAME = "Path"

    @property
    def raw(self) -> str:
        return str(self)

    def __init__(self, chars: str):
        super().__init__(ValueType.STRING, chars)

    def __str__(self) -> str:
        return f"\'{self._value}\'"


class Correction(Value[str]):
    NAME = "Correction"

    def __init__(self, value: str):
        super().__init__(ValueType.STRING, value)

    def __str__(self) -> str:
        return self._value


class Algorithm(Value[str]):
    NAME = "Algorithm"

    def __init__(self, value: str):
        super().__init__(ValueType.STRING, value)

    def __str__(self) -> str:
        return self._value


class Array(Value[_list[Value]]):
    NAME = "Collection"

    def __init__(self, *items: Value):
        super().__init__(ValueType.LIST, list(items))

    def __str__(self) -> str:
        mid = ", ".join(map(str, self._value))
        return f"[{mid}]"

    def add_elem(self, elem: Value):
        self._value.append(elem)

    def is_true(self) -> bool:
        return bool(self._value)

    def invert(self) -> "Value":
        return Array(*self._value[::-1])

    def mix(self, other: "Value") -> _None["Value"]:
        if isinstance(other, Array):
            return Array(*self._value, *other.raw)
        return super().mix(other)

    def equal(self, other: "Value") -> _None["Value"]:
        if isinstance(other, Array):
            return Bool(all(x == y for x, y in zip(self.raw, other.raw)))
