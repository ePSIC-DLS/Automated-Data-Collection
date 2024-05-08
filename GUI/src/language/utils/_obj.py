import abc
import enum
import typing
from typing import List as _list, Optional as _None, Dict as _dict, Type as _type

from ._chunk import Chunk
from ._ip import InstructionPointer
from ._stack import Stack
from ._value import Interpreter, String, Value, ValueType, Number


class ObjType(enum.Enum):
    FUNCTION_SRC = enum.auto()
    FUNCTION_NAT = enum.auto()
    ITERABLE_SRC = enum.auto()
    ITERABLE_NAT = enum.auto()
    INST_SRC = enum.auto()
    INST_NAT = enum.auto()
    NATIVE = enum.auto()


T = typing.TypeVar("T")


class Obj(Value[T], abc.ABC, typing.Generic[T]):

    def __init__(self, ot: ObjType, ov: T):
        super().__init__(ValueType.OBJECT, ov)
        self._ot = ot


class Function(Obj[Chunk]):
    NAME = "FnObj"

    @property
    def name(self) -> String:
        return self._name

    def __init__(self):
        super().__init__(ObjType.FUNCTION_SRC, Chunk())
        self._name = String("")
        self._arity = 0

    def __str__(self) -> str:
        if not self._name:
            return f"<Script>"
        return f"<Function {self._name}>"

    def call(self, interpreter: Interpreter, count: int) -> bool:
        if count != self._arity:
            return interpreter.error(f"{self} expected {self._arity} arguments, got {count}")
        interpreter.new_frame(self, interpreter.stack << (count + 1))
        return True

    def set_name(self, name: str):
        self._name = String(name)

    def add_param(self):
        self._arity += 1


class NativeFunc(Obj[typing.Callable]):
    NAME = "BuiltinFn"

    def __init__(self, shadow: typing.Callable[[int, _list[Value]], Value]):
        super().__init__(ObjType.FUNCTION_NAT, shadow)

    def __str__(self) -> str:
        return f"<PyFunc {self._value.__name__}>"

    def call(self, interpreter: Interpreter, count: int) -> bool:
        stack = list(interpreter.stack << count)
        res = self._value(count, stack)
        if count:
            interpreter.stack.top -= count + 1
        else:
            interpreter.stack.pop()
        interpreter.stack.push(res)
        return True


class Generator(Function):
    NAME = "Generator"

    @property
    def stack(self) -> Stack[Value]:
        return self._stack

    @stack.setter
    def stack(self, value: Stack[Value]):
        self._stack = value

    @property
    def ip(self) -> InstructionPointer:
        return self._ip

    @ip.setter
    def ip(self, value: InstructionPointer):
        self._ip = value

    def __init__(self):
        super().__init__()
        self._stack: _None[Stack[Value]] = None
        self._ip: _None[InstructionPointer] = None

    def __str__(self) -> str:
        return f"<Un-Primed Iterator {self._name}>"

    def call(self, interpreter: Interpreter, count: int) -> bool:
        if count != self._arity:
            return interpreter.error(f"{self} expected {self._arity} arguments, got {count}")
        self._stack = interpreter.stack << (count + 1)
        interpreter.stack.push(Iterator(self))
        return True


class Iterator(Obj[Generator]):
    NAME = "Iter"

    def __init__(self, src: Generator):
        super().__init__(ObjType.ITERABLE_SRC, src)

    def __str__(self) -> str:
        return f"<Primed Iterator {self._value.name}>"


class NativeIterator(Obj[typing.Iterator[Value]]):
    NAME = "BuiltinIter"

    def __init__(self, shadow: typing.Iterator[Value]):
        super().__init__(ObjType.ITERABLE_NAT, shadow)

    def __str__(self) -> str:
        return f"<PyIterable {self._value.__name__}>"


class Enum(Obj[_list[String]]):
    NAME = "Enumeration"

    def __init__(self, name: String):
        super().__init__(ObjType.INST_SRC, [])
        self._name = name

    def __str__(self) -> str:
        return f"<Enum {self._name}>"

    def set(self, src: String):
        self._value.append(src)

    def get(self, src: String) -> Number:
        return Number(self._value.index(src))


class NativeEnum(Obj[_dict[str, int]]):
    NAME = "BuiltinEnum"

    def __init__(self, shadow: _type[enum.Enum]):
        self._shadow = shadow
        super().__init__(ObjType.INST_NAT, {member.name: member.value for member in shadow})

    def __str__(self) -> str:
        return f"<PyEnum {self._shadow.__name__}>"

    def get(self, src: String) -> Number:
        return Number(self._value[src.raw])


class NativeClass(Obj[object]):
    NAME = "BuiltinObj"

    def __init__(self, shadow):
        super().__init__(ObjType.NATIVE, shadow)

    def __str__(self) -> str:
        return f"<PyInstance {type(self._value).__name__}>"
