import abc
import enum
import typing
from typing import List as _list, Optional as _None, Dict as _dict, Type as _type

from ._chunk import Chunk
from ._ip import InstructionPointer
from ._stack import Stack
from ._value import Interpreter, String, Value, ValueType, Number, Nil


class ObjType(enum.Enum):
    """
    Enumeration representing the various complex-object types in the language.

    Members
    -------
    FUNCTION_SRC
        A user-defined function.
    FUNCTION_NAT
        A python-defined function imported into the STL (native function).
    ITERABLE_SRC
        A user-defined generator.
    ITERABLE_NAT
        A python-defined generator imported into the STL (native generator).
    INST_SRC
        A user-defined enumeration.
    INST_NAT
        A python-defined enumeration imported into the STL (native enumeration).
    NATIVE
        A python-defined instance imported into the STL (native instance).
    """
    FUNCTION_SRC = enum.auto()
    FUNCTION_NAT = enum.auto()
    ITERABLE_SRC = enum.auto()
    ITERABLE_NAT = enum.auto()
    INST_SRC = enum.auto()
    INST_NAT = enum.auto()
    NATIVE = enum.auto()


T = typing.TypeVar("T")


class Obj(Value[T], abc.ABC, typing.Generic[T]):
    """
    An abstract base class representing a complex-object type.

    Attributes
    ----------
    _ot: ObjType
        The complex-object type.
    """

    def __init__(self, ot: ObjType, ov: T):
        super().__init__(ValueType.OBJECT, ov)
        self._ot = ot


class Function(Obj[Chunk]):
    """
    Concrete complex-object type representing a user-defined function.

    Bound Generics
    --------------
    T: Chunk

    Attributes
    ----------
    _name: String
        The name of the function.
    _arity: int
        The number of parameters the function has.
    """
    NAME = "FnObj"

    @property
    def name(self) -> String:
        """
        Public access to the function's name.

        Returns
        -------
        String
            The name of the function.
        """
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
        """
        Execute the function's bytecode. This will launch a new frame in the interpreter.

        Parameters
        ----------
        interpreter: Interpreter
            The interpreter to execute the function.
        count: int
            The argument count. Note this is expected to be the same as the function's arity.

        Returns
        -------
        bool
            Always True, as the function can be called. Note that even if the function errors before calling (such as
            through arity issues), it will still return True.
        """
        if count != self._arity:
            return interpreter.error(f"{self} expected {self._arity} arguments, got {count}")
        interpreter.new_frame(self, interpreter.stack << (count + 1))
        return True

    def set_name(self, name: str):
        """
        Set the name of the function.

        Parameters
        ----------
        name: str
            The new name of the function.
        """
        self._name = String(name)

    def add_param(self):
        """
        Add a parameter to the function.
        """
        self._arity += 1


class NativeFunc(Obj[typing.Callable[[int, _list[Value]], Value]]):
    """
    Concrete complex-object type representing a native function.

    Note the native function is expected to receive an argument count and an argument list, then return a value type.
    If the argument count is not the expected value, the function should raise an error.

    Bound Generics
    --------------
    T: Callable[[int, _list[Value]], Value]
    """
    NAME = "BuiltinFn"

    def __init__(self, shadow: typing.Callable[[int, _list[Value]], Value]):
        super().__init__(ObjType.FUNCTION_NAT, shadow)

    def __str__(self) -> str:
        return f"<PyFunc {self._value.__name__}>"

    def call(self, interpreter: Interpreter, count: int) -> bool:
        """
        Execute the python function. As it has no bytecode, it converts the interpreter's stack to an arg list.

        Parameters
        ----------
        interpreter: Interpreter
            The interpreter to execute the function.
        count: int
            The argument count. Note this is expected to be the correct value for the argument count parameter.

        Returns
        -------
        bool
            Always True, as the function can be called. Note that even if the function errors before calling (such as
            through arity issues), it will still return True.
        """
        stack = list(interpreter.stack << count)
        res = self._value(count, stack)
        if res is None:
            res = Nil()
        if count:
            interpreter.stack.top -= count + 1
        else:
            interpreter.stack.pop()
        interpreter.stack.push(res)
        return True


class Generator(Function):
    """
    Special functional subclass representing a user-defined generator.

    Attributes
    ----------
    _stack: Stack[Value] | None
        The stack used when this function is called.
    _ip: InstructionPointer
        The pointer to the instruction sequence at the point of execution.
    """
    NAME = "Generator"

    @property
    def stack(self) -> Stack[Value]:
        """
        Public access to the value stack.

        Returns
        -------
        Stack[Value]
            The stack used when this function is called.
        """
        return self._stack

    @stack.setter
    def stack(self, value: Stack[Value]):
        self._stack = value

    @property
    def ip(self) -> InstructionPointer:
        """
        Public access to the instruction pointer.

        Returns
        -------
        InstructionPointer
            The pointer to the instruction sequence at the point of execution.
        """
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
        """
        Prime an iterator from the generator.

        This will update the stack of this instance.

        Parameters
        ----------
        interpreter: Interpreter
            The interpreter to use for stack information.
        count: int
            The argument count. Note this is expected to be the same as the function's arity.

        Returns
        -------
        bool
            Always True, as the generator can be called. Note that even if the generator errors before calling (such as
            through arity issues), it will still return True.
        """
        if count != self._arity:
            return interpreter.error(f"{self} expected {self._arity} arguments, got {count}")
        self._stack = interpreter.stack << (count + 1)
        interpreter.stack.push(Iterator(self))
        return True


class Iterator(Obj[Generator]):
    """
    Concrete complex-object type to represent a user-defined iterator.

    Bound Generics
    --------------
    T: Generator
    """
    NAME = "Iter"

    def __init__(self, src: Generator):
        super().__init__(ObjType.ITERABLE_SRC, src)

    def __str__(self) -> str:
        return f"<Primed Iterator {self._value.name}>"


class NativeIterator(Obj[typing.Iterator[Value]]):
    """
    Concrete complex-object type to represent a native iterator.

    Bound Generics
    --------------
    T: Iterator[Value]
    """
    NAME = "BuiltinIter"

    def __init__(self, shadow: typing.Iterator[Value]):
        super().__init__(ObjType.ITERABLE_NAT, shadow)

    def __str__(self) -> str:
        return f"<PyIterable {self._value.__name__}>"


class Enum(Obj[_list[String]]):
    """
    Concrete complex-object type to represent a user-defined enumeration.

    Bound Generics
    --------------
    T: List[String]

    Attributes
    ----------
    _name: String
        The name of the enumeration.
    """
    NAME = "Enumeration"

    def __init__(self, name: String):
        super().__init__(ObjType.INST_SRC, [])
        self._name = name

    def __str__(self) -> str:
        return f"<Enum {self._name}>"

    def set(self, src: String):
        """
        Add a new enumeration member.

        Parameters
        ----------
        src: String
            The new member to add.
        """
        self._value.append(src)

    def get(self, src: String) -> Number:
        """
        Retrieve the numerical value of the enumeration member.

        Parameters
        ----------
        src: String
            The member to retrieve.

        Returns
        -------
        Number
            The numerical index of the member.
        """
        return Number(self._value.index(src))


class NativeEnum(Obj[_dict[str, int]]):
    """
    Concrete complex-object type to represent a native enumeration.

    Bound Generics
    --------------
    T: dict[str, int]

    Attributes
    ----------
    _shadow: type[Enum]
        The python enumeration.
    """
    NAME = "BuiltinEnum"

    def __init__(self, shadow: _type[enum.Enum]):
        self._shadow = shadow
        super().__init__(ObjType.INST_NAT, {member.name: member.value for member in shadow})

    def __str__(self) -> str:
        return f"<PyEnum {self._shadow.__name__}>"

    def get(self, src: String) -> Number:
        """
        Get the numerical value of the enumeration member.

        Parameters
        ----------
        src: String
            The member to retrieve.

        Returns
        -------
        Number
            The numerical value of the member.
        """
        return Number(self._value[src.raw])


class NativeClass(Obj[object]):
    """
    Concrete complex-object type to represent a native object.

    Bound Generics
    --------------
    T: object
    """
    NAME = "BuiltinObj"

    def __init__(self, shadow):
        super().__init__(ObjType.NATIVE, shadow)

    def __str__(self) -> str:
        return f"<PyInstance {type(self._value).__name__}>"
