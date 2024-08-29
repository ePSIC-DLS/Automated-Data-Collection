import abc
import typing
import enum
from typing import Optional as _None, List as _list
from ._stack import Stack

T = typing.TypeVar("T")


class Interpreter(abc.ABC):
    """
    Abstract base class for interpreters.

    All methods are abstract.
    """
    stack: Stack["Value"]

    @abc.abstractmethod
    def new_frame(self, fn, vs: Stack["Value"]):
        """
        Change the active call frame.

        Parameters
        ----------
        fn: Function
            The function being called, as the base of the stack.
        vs: Stack[Value]
            The stack of values to use as the stack.
        """
        pass

    @abc.abstractmethod
    def error(self, msg: str) -> bool:
        """
        Raise an error.

        Parameters
        ----------
        msg: str
            The error message.

        Returns
        -------
        bool
            A flag for whether the error occurred.
            Will always be true, but is used for when the call-site returns a flag for whether an error occurred.
        """
        pass


class ValueType(enum.Enum):
    """
    Enumeration to represent the various types of values - note that this is the languages's notion of type.

    Members
    -------
    NUM
        Any generic number type.
    BOOL

    VOID
        Represents no value (same as python's NoneType type)
    STRING

    LIST

    OBJECT
        Any complex object (which would be heap-allocated in a non-memory managed language)
    """
    NUM = enum.auto()
    BOOL = enum.auto()
    VOID = enum.auto()
    STRING = enum.auto()
    LIST = enum.auto()
    OBJECT = enum.auto()


class Value(abc.ABC, typing.Generic[T]):
    """
    Abstract base class representing the value of a variable.

    The basic value implementation has no operators defined, is always truthy, and cannot be called.

    Generics
    --------
    T
        The python type of the value

    Abstract Methods
    ----------------
    __str__


    Attributes
    ----------
    NAME: str
        The name of the class according to the namespace.
    _vt: ValueType
        The type of the value according to the namespace.
    _value: T
        The raw python value.
    """
    NAME = "Obj"

    @property
    def raw(self) -> T:
        """
        Public access to the underlying python value.

        Returns
        -------
        T
            The raw python value.
        """
        return self._value

    def __init__(self, vt: ValueType, vv: T):
        self._vt = vt
        self._value = vv

    @abc.abstractmethod
    def __str__(self) -> str:
        pass

    def is_true(self) -> bool:
        """
        Determine the truthiness of the value.

        Returns
        -------
        bool
            For a default value, this is always true.
        """
        return True

    def negate(self) -> "Value":
        """
        Negate the value.

        Returns
        -------
        Value
            The negated value.

        Raises
        ------
        TypeError
            If the value cannot be negated. For a default value, this is always raised.
        """
        raise TypeError(f"{self.NAME} objects cannot be negated")

    def invert(self) -> "Value":
        """
        Invert the value.

        Returns
        -------
        Value
            The inverted value.

        Raises
        ------
        TypeError
            If the value cannot be inverted. For a default value, this is always raised.
        """
        raise TypeError(f"{self.NAME} objects cannot be inverted")

    def call(self, interpreter: Interpreter, count: int) -> bool:
        """
        Call the value, using the given interpreter and argument count.

        Parameters
        ----------
        interpreter: Interpreter
            The interpreter to execute instructions.
        count: int
            The number of arguments provided.

        Returns
        -------
        bool
            Whether the type can be called.
        """
        return False

    def power(self, other: "Value") -> _None["Value"]:
        """
        Perform the calculation x ^ y. This is dubbed "x to the power of y", even if "power of" makes no logical sense.

        Parameters
        ----------
        other: Value
            The value to raise this value by.

        Returns
        -------
        Value | None
            The result of the operation. This is None if the calculation cannot be performed between two types, which
            will always be the case with a default value.
        """
        return

    def r_power(self, other: "Value") -> _None["Value"]:
        """
        Perform the calculation x ^ y, when `type(x).power` returns None.

        Parameters
        ----------
        other: Value
            The value to be raised by this value.

        Returns
        -------
        Value | None
            The result of the operation. This is None if the calculation cannot be performed between two types, which
            will always be the case with a default value.
        """
        return

    def add(self, other: "Value") -> _None["Value"]:
        """
        Perform the calculation x + y. This is dubbed "x add y", even if "add" makes no logical sense.

        Parameters
        ----------
        other: Value
            The value to add.

        Returns
        -------
        Value | None
            The result of the operation. This is None if the calculation cannot be performed between two types, which
            will always be the case with a default value.
        """
        return

    def r_add(self, other: "Value") -> _None["Value"]:
        """
        Perform the calculation x add y, when `type(x).add` returns None.

        Parameters
        ----------
        other: Value
            The value to add.

        Returns
        -------
        Value | None
            The result of the operation. This is None if the calculation cannot be performed between two types, which
            will always be the case with a default value.
        """
        return

    def sub(self, other: "Value") -> _None["Value"]:
        """
        Perform the calculation x - y. This is dubbed "x subtract y", even if "subtract" makes no logical sense.

        Parameters
        ----------
        other: Value
            The value to subtract.

        Returns
        -------
        Value | None
            The result of the operation. This is None if the calculation cannot be performed between two types, which
            will always be the case with a default value.
        """
        return

    def r_sub(self, other: "Value") -> _None["Value"]:
        """
        Perform the calculation x - y, when `type(x).sub` returns None.

        Parameters
        ----------
        other: Value
            The value to subtract this value from.

        Returns
        -------
        Value | None
            The result of the operation. This is None if the calculation cannot be performed between two types, which
            will always be the case with a default value.
        """
        return

    def mix(self, other: "Value") -> _None["Value"]:
        """
        Perform the calculation x | y. This is dubbed "x mixed with y", even if "mixed with" makes no logical sense.

        Parameters
        ----------
        other: Value
            The value to mix this value with.

        Returns
        -------
        Value | None
            The result of the operation. This is None if the calculation cannot be performed between two types, which
            will always be the case with a default value.
        """
        return

    def r_mix(self, other: "Value") -> _None["Value"]:
        """
        Perform the calculation x | y, when `type(x).mix` returns None.

        Parameters
        ----------
        other: Value
            The value to be mixed with this value.

        Returns
        -------
        Value | None
            The result of the operation. This is None if the calculation cannot be performed between two types, which
            will always be the case with a default value.
        """
        return

    def equal(self, other: "Value") -> _None["Value"]:
        """
        Perform the calculation x == y.

        Note that this has no `r_equal` function, as when "x == y" fails, "y == x" is equivalent.

        Parameters
        ----------
        other: Value
            The value to compare this value with.

        Returns
        -------
        Value | None
            The result of the operation. This is None if the calculation cannot be performed between two types, which
            will always be the case with a default value.
        """
        return

    def less(self, other: "Value") -> _None["Value"]:
        """
        Perform the calculation x < y.

        Note that this has no `r_less` function, as when "x < y" fails, "y > x" is equivalent.

        Parameters
        ----------
        other: Value
            The value to compare this value with.

        Returns
        -------
        Value | None
            The result of the operation. This is None if the calculation cannot be performed between two types, which
            will always be the case with a default value.
        """
        return

    def more(self, other: "Value") -> _None["Value"]:
        """
        Perform the calculation x > y.

        Note that this has no `r_more` function, as when "x > y" fails, "y < x" is equivalent.

        Parameters
        ----------
        other: Value
            The value to compare this value with.

        Returns
        -------
        Value | None
            The result of the operation. This is None if the calculation cannot be performed between two types, which
            will always be the case with a default value.
        """
        return


class Number(Value[float]):
    """
    Concrete value type to represent numerical values.

    Bound Generics
    --------------
    T: float
    """
    NAME = "Num"

    def __init__(self, num: float):
        super().__init__(ValueType.NUM, float(num))

    def __str__(self) -> str:
        return f"{self._value:.3e}"

    def is_int(self) -> bool:
        """
        Determine whether this value is an integer value.

        Returns
        -------
        bool
            Whether this value is a whole number.
        """
        return self._value == int(self._value)

    def is_true(self) -> bool:
        """
        Determine the truthiness of the integer.

        Returns
        -------
        bool
            Whether the value is non-zero.
        """
        return self._value != 0

    def negate(self) -> "Value":
        """
        Flip the sign of the value.

        Returns
        -------
        Number
            A number with a flipped sign but same magnitude as this instance.
        """
        return Number(-self._value)

    def power(self, other: "Value") -> _None["Value"]:
        """
        Perform the calculation x * (10 ** y).

        Parameters
        ----------
        other: Value
            The power of 10 to shift this integer by.

        Returns
        -------
        Number | None
            The shifted integer.
            Note that this is only defined when y is an integer, and will return None otherwise.
        """
        if isinstance(other, Number) and other.is_int():
            return Number(self._value * 10 ** other.raw)
        return super().power(other)

    def add(self, other: "Value") -> _None["Value"]:
        """
        Perform the calculation x + y.

        Parameters
        ----------
        other: Value
            The number to add to this instance.

        Returns
        -------
        Number | None
            The sum of the input numbers.
            Note that this is only defined when y is a number, and will return None otherwise.
        """
        if isinstance(other, Number):
            return Number(self._value + other.raw)
        return super().add(other)

    def sub(self, other: "Value") -> _None["Value"]:
        """
        Perform the calculation x - y.

        Parameters
        ----------
        other: Value
            The number to subtract from this instance.

        Returns
        -------
        Number | None
            The difference of the input numbers.
            Note that this is only defined when y is a number, and will return None otherwise.
        """
        if isinstance(other, Number):
            return Number(self._value - other.raw)
        return super().add(other)

    def mix(self, other: "Value") -> _None["Value"]:
        """
        Perform the calculation x | y.

        Parameters
        ----------
        other: Value
            The number to bitwise-or with this instance.

        Returns
        -------
        Number | None
            The bitwise-or of the input numbers.
            Note that this is only defined when both x and y are integers, and will return None otherwise.
        """
        if isinstance(other, Number) and other.is_int() and self.is_int():
            return Number(int(self._value) | int(other.raw))
        return super().mix(other)

    def equal(self, other: "Value") -> _None["Value"]:
        """
        Determine if two numbers are equal.

        Parameters
        ----------
        other: Value
            The number to compare with this instance.

        Returns
        -------
        Bool | None
            Whether the two numbers are equal.
            Note that this is only defined when y is a number, and will return None otherwise.
        """
        if isinstance(other, Number):
            return Bool(self._value == other.raw)
        return super().add(other)

    def less(self, other: "Value") -> _None["Value"]:
        """
        Determine if two numbers are linearly-ordered in ascending order.

        Parameters
        ----------
        other: Value
            The number to compare with this instance.

        Returns
        -------
        Bool | None
            Whether this instance is numerically lower than the provided instance.
            Note that this is only defined when y is a number, and will return None otherwise.
        """
        if isinstance(other, Number):
            return Bool(self._value < other.raw)
        return super().add(other)

    def more(self, other: "Value") -> _None["Value"]:
        """
        Determine if two numbers are linearly-ordered in descending order.

        Parameters
        ----------
        other: Value
            The number to compare with this instance.

        Returns
        -------
        Bool | None
            Whether this instance is numerically greater than the provided instance.
            Note that this is only defined when y is a number, and will return None otherwise.
        """
        if isinstance(other, Number):
            return Bool(self._value > other.raw)
        return super().add(other)


class Bool(Value[bool]):
    """
    Concrete value type to represent boolean (true/false) values.

    Bound Generics
    --------------
    T: bool
    """
    NAME = "Boolean"

    def __init__(self, state: bool):
        super().__init__(ValueType.BOOL, state)

    def __str__(self) -> str:
        return "on" if self._value else "off"

    def is_true(self) -> bool:
        """
        Determine the truthiness of the boolean.

        Returns
        -------
        bool
            The underlying python value.
        """
        return self._value

    def invert(self) -> "Value":
        """
        Determine the logical-not of the boolean.

        Returns
        -------
        Bool
            A boolean value with the truthiness inverted.
        """
        return Bool(not self._value)

    def equal(self, other: "Value") -> _None["Value"]:
        """
        Determine if two booleans are equal.

        Parameters
        ----------
        other: Value
            The number to compare with this instance.

        Returns
        -------
        Bool | None
            Whether the two booleans are equal. A boolean can also be equal to the numerical value 1.
            Note that this is only defined when y is a boolean or a number, and will return None otherwise.
        """
        if isinstance(other, Bool):
            return Bool(self._value == other.raw)
        elif isinstance(other, Number):
            return Bool(other.raw == 1)
        return super().add(other)


class Nil(Value[None]):
    """
    Concrete value to represent a null-value (an absence of value).

    Bound Generics
    --------------
    T: NoneType
    """
    NAME = "None"

    def __init__(self):
        super().__init__(ValueType.VOID, None)

    def __str__(self) -> str:
        return f"NilVal"

    def is_true(self) -> bool:
        """
        Determine the truthiness of a nil-value.

        Returns
        -------
        bool
            False. A lack of value is never true.
        """
        return False

    def equal(self, other: "Value") -> _None["Value"]:
        """
        Determine if two absences are equal.

        Parameters
        ----------
        other: Value
            The absence to compare with this instance.

        Returns
        -------
        Bool | None
            Whether the input parameter is null. This uses the python convention that None is None, as opposed to the
            IEEE convention that NaN is not NaN. This is because the Nil type isn't just Not-A-Number, but rather it's
            Not-Anything.
        """
        return Bool(isinstance(other, Nil))


class String(Value[str]):
    """
    A concrete value type to represent string values.

    Note that these strings are hashable and are comparable by using `==` in python, due to global variables needing a
    hash-table (dictionary) of String types.

    Bound Generics
    --------------
    T: str
    """
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
        """
        Determine the truthiness of a string.

        Returns
        -------
        bool
            Whether the string has content.
        """
        return bool(self._value)

    def add(self, other: "Value") -> _None["Value"]:
        """
        Concatenate two strings together.

        Parameters
        ----------
        other: Value
            The other string to concatenate.

        Returns
        -------
        String | None
            The concatenated string.
            Note that this is only defined when y is a string, and will return None otherwise.
        """
        if isinstance(other, String):
            return String(self._value + other.raw)
        return super().add(other)

    def equal(self, other: "Value") -> _None["Value"]:
        """
        Determine if two strings are equal.

        Parameters
        ----------
        other: Value
            The string to compare with this instance.

        Returns
        -------
        Bool | None
            Whether the strings have the same content.
            Note that this is only defined when y is a string, and will return None otherwise.
        """
        if isinstance(other, String):
            return Bool(self._value == other.raw)
        return super().equal(other)


class Path(Value[str]):
    """
    A concrete value type to represent a file-path.

    Bound Generics
    --------------
    T: str
    """
    NAME = "Path"

    @property
    def raw(self) -> str:
        return str(self)

    def __init__(self, chars: str):
        super().__init__(ValueType.STRING, chars)

    def __str__(self) -> str:
        return f"\'{self._value}\'"


class Correction(Value[str]):
    """
    Concrete value type to represent a hardware-correction.

    Bound Generics
    --------------
    T: str
    """
    NAME = "Correction"

    def __init__(self, value: str):
        super().__init__(ValueType.STRING, value)

    def __str__(self) -> str:
        return self._value


class Algorithm(Value[str]):
    """
    Concrete value type to represent a distance-algorithm.

    Bound Generics
    --------------
    T: str
    """
    NAME = "Algorithm"

    def __init__(self, value: str):
        super().__init__(ValueType.STRING, value)

    def __str__(self) -> str:
        return self._value


class Array(Value[_list[Value]]):
    """
    Concrete value type to represent an immutable list of values.

    Note that according to python, it is mutable but no code can access this mutability.
    As the language is dynamically typed (like python), the list does not have to be homogenous.

    Bound Generics
    --------------
    T: list[Value]
    """
    NAME = "Collection"

    def __init__(self, *items: Value):
        super().__init__(ValueType.LIST, list(items))

    def __str__(self) -> str:
        mid = ", ".join(map(str, self._value))
        return f"[{mid}]"

    def add_elem(self, elem: Value):
        """
        Programmatically add an element to the list. This is how the list is formed from bytecode.

        Parameters
        ----------
        elem: Value
            The element to add.
        """
        self._value.append(elem)

    def is_true(self) -> bool:
        """
        Determine the truthiness of a list.

        Returns
        -------
        bool
            Whether the list has content.
        """
        return bool(self._value)

    def invert(self) -> "Value":
        """
        Reverse the list.

        Returns
        -------
        Array
            The array with the underlying python implementation in reverse order.
        """
        return Array(*self._value[::-1])

    def mix(self, other: "Value") -> _None["Value"]:
        """
        Concatenate two lists together.

        Parameters
        ----------
        other: Value
            The array to concatenate with this instance.

        Returns
        -------
        Array | None
            The concatenated list.
            Note that this is only defined when y is a list, and will return None otherwise.
        """
        if isinstance(other, Array):
            return Array(*self._value, *other.raw)
        return super().mix(other)

    def equal(self, other: "Value") -> _None["Value"]:
        """
        Determine if two lists are equal.

        Parameters
        ----------
        other: Value
            The array to compare with this instance.

        Returns
        -------
        Bool | None
            Whether the two arrays have identical content.
            Note that this is only defined when y is a list, and will return None otherwise.
        """
        if isinstance(other, Array):
            return Bool(all(x.equal(y) for x, y in zip(self.raw, other.raw)))
        return super().equal(other)
