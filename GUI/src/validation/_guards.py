import abc
import typing
from typing import Tuple as _tuple
from decimal import Decimal

from ._enums import *

try:
    import typing_extensions
except ModuleNotFoundError:
    typing_extensions = typing

T = typing.TypeVar("T")
Ts = typing_extensions.TypeVarTuple("Ts")
Num = typing.TypeVar("Num", int, float)

__all__ = [
    "ValueValidator", "ContainerValidator", "UpperBoundValidator", "DynamicUpperBoundValidator",
    "LowerBoundValidator", "DynamicLowerBoundValidator", "RangeValidator", "FactorValidator", "IntegerValidator",
    "TypeValidator", "MemoryValidator"
]


class Error(Exception):
    """
    Validation error
    """
    pass


class Base(typing.Generic[T], abc.ABC):
    """
    Abstract base validation class.

    Can be converted to a string and has a `validate` method that should raise an error on failed validation.

    Abstract Methods
    ----------------
    __str__
    validate

    Generics
    --------
    T: Any
        The dtype of data to validate.
    """

    @abc.abstractmethod
    def __str__(self) -> str:
        pass

    @abc.abstractmethod
    def validate(self, data: T) -> None:
        """
        Validate the incoming data.

        Parameters
        ----------
        data: T
            The data to validate.

        Raises
        ------
        Error
            Upon failure.
        """
        pass


class Pass(Base[T]):
    """
    A concrete validator that passes any input. Is still generic.
    """

    def __str__(self) -> str:
        return "True"

    def validate(self, data: T) -> None:
        pass


class Mixin(Base[T], typing.Generic[T], abc.ABC):
    """
    A 'mixin' class that has an internal validator that it calls and, in some way, mutates the result of.

    Abstract Methods
    ----------------
    __str__

    Attributes
    ----------
    _v: Base[T]
        The validator to apply.
    """

    def __init__(self, inner: Base[T]):
        self._v = inner

    def validate(self, data: T) -> None:
        self._v.validate(data)


class UnionMixin(Mixin, typing.Generic[typing_extensions.Unpack[Ts]]):
    """
    A mixin that will pass the data if at least one validator passes the test.

    As there is no way to correctly type the generic, it must be specified prior to creation.
    E.G. UnionMixin[int, int, int](...)

    Generics
    --------
    *Ts: Any
        The internal validators' dtypes.

    Attributes
    ----------
    _vs: tuple[Base, ...]
        The validators to apply. The internal dtypes of the bases matches Ts.
    """

    @property
    def validators(self) -> _tuple[Base, ...]:
        """
        Public access to the internal validators.

        Returns
        -------
        tuple[*Ts]
            The validators to apply.
        """
        return self._vs

    def __init__(self, *validators: Base):
        self._vs = validators
        super().__init__(validators[0])

    def __str__(self) -> str:
        return f" | ".join(map(str, self._vs))

    def validate(self, data: typing.Union[typing_extensions.Unpack[Ts]]) -> None:
        """
        Run the data against the internal validators, exiting when one passes. If none pass, raise the last exception.

        Parameters
        ----------
        data: Union[*Ts]
            The data to validate.

        Raises
        ------
        Error
            The error raised by the final validator if none pass.
        """
        stored_err: typing.Optional[Error] = None
        for v in self._vs:
            try:
                v.validate(data)
                break
            except Error as err:
                stored_err = err
        else:
            raise stored_err


class CombinationMixin(Mixin, typing.Generic[typing_extensions.Unpack[Ts]]):
    """
    A mixin that will pass the data if the specified number of internal validators passed.

    As there is no way to correctly type the generic, it must be specified prior to creation.
    E.G. CombinationMixin[int, int, int](...)

    In `OR` mode (the default) this is very similar to a `UnionMixin`, except that it does not exit on first success,
    therefore making it (on average) slower.

    Generics
    --------
    *Ts: Any
        The internal validators' dtypes.

    Attributes
    ----------
    _vs: tuple[Base, ...]
        The validators to apply. The internal dtypes of the bases matches Ts.
    _mode: UnionType
        The union mode.
    _num_validators: int
        The number of validators to pass in order for the end result to pass.
    _sym: str
        The symbol to describe the combination.
    """

    @property
    def validators(self) -> _tuple[Base, ...]:
        """
        Public access to the internal validators.

        Returns
        -------
        tuple[Base, ...]
            The validators to apply.
        """
        return self._vs

    def __init__(self, *validators: Base, mode=UnionType.OR):
        self._vs = validators
        self._mode = mode
        if mode == UnionType.OR:
            self._num_validators = -1
            self._sym = "|"
        elif mode == UnionType.AND:
            self._num_validators = len(validators)
            self._sym = "&"
        elif mode == UnionType.XOR:
            self._num_validators = 1
            self._sym = "^"
        else:
            raise TypeError("Unsupported union type")
        super().__init__(validators[0])

    def __str__(self) -> str:
        return f" {self._sym} ".join(map(str, self._vs))

    def validate(self, data: typing.Union[typing_extensions.Unpack[Ts]]) -> None:
        """
        Count the number of passed validations, and check it against the expected number.

        Parameters
        ----------
        data: Union[*Ts]
            The data to validate.

        Raises
        ------
        Error
            If the number of passes is not the expected amount.
        """

        def _count() -> typing.Iterator[int]:
            for v in self._vs:
                try:
                    v.validate(data)
                except Error:
                    yield 0
                else:
                    yield 1

        num_passed = sum(_count())
        if self._mode == UnionType.OR:
            if num_passed == 0:
                raise Error(f"Expected at least one validator to pass {data}")
        elif num_passed != self._num_validators:
            raise Error(f"Expected exactly {self._num_validators} validators to pass {data}")


class BranchedMixin(Mixin, typing.Generic[typing_extensions.Unpack[Ts]]):
    """
    A mixin that will have multiple stored validation methods, but only one active at any time.

    As there is no way to correctly type the generic, it must be specified prior to creation.
    E.G. BranchedMixin[int, int, int](...)

    Generics
    --------
    *Ts: Any
        The internal validators' dtypes.

    Attributes
    ----------
    _vs: tuple[Base, ...]
        The validators to apply. The internal dtypes of the bases matches Ts.
    _i: int
        The currently selected index.
    """

    @property
    def branch(self) -> int:
        """
        Public access to the branch index.

        Returns
        -------
        int
            The index of the currently selected branch.
        """
        return self._i

    @branch.setter
    def branch(self, value: int):
        if not 0 <= value < self._max:
            raise ValueError(f"Expected branch number between 0 and {self._max - 1} (got {value})")
        self._i = value
        self._v = self._vs[value]

    @property
    def branches(self) -> _tuple[Base, ...]:
        """
        Public access to the internal validators.

        Returns
        -------
        tuple[Base, ...]
            The validators to apply.
        """
        return self._vs

    def __init__(self, *validators: Base, branch=0):
        self._max = len(validators)
        self._i = branch
        self._vs = validators
        super().__init__(validators[branch])

    def __str__(self) -> str:
        elems = ", ".join(map(str, self._vs))
        return f"({elems})[{self._i}]"


class IterableMixin(Mixin[typing.Iterable[T]], typing.Generic[T]):
    """
    Mixin that only passes the data if all elements pass the criteria.
    """

    def __str__(self) -> str:
        return f"all({self._v})"

    def validate(self, data: typing.Iterable[T]) -> None:
        for elem in data:
            super().validate(elem)


class InverseMixin(Mixin[T], typing.Generic[T]):
    """
    Mixin that only passes the data if the internal validator fails.
    """

    def __str__(self) -> str:
        return f"not({self._v})"

    def validate(self, data: T) -> None:
        """
        Invalidate the input data.

        Parameters
        ----------
        data: T
            The data to invalidate.

        Raises
        ------
        Error
            If the data passes the internal validator (if it is validated, hence this mixin's function of invalidating
            data)
        """
        try:
            super().validate(data)
        except Error:
            return
        raise Error(f"Expected {data!r} to fail {self._v}")


class ValueValidator(Base[T], typing.Generic[T]):
    """
    Concrete validator that checks for equality to a certain value.

    Attributes
    ----------
    _check: T
        The value to check against.
    """

    @property
    def value(self) -> T:
        """
        Public access to the value.

        Returns
        -------
        T
            The value to check against.
        """
        return self._check

    def __init__(self, value: T):
        self._check = value

    def __str__(self) -> str:
        return f"v == {self._check}"

    def validate(self, data: T) -> None:
        """
        Validate the input data.

        Parameters
        ----------
        data: T
            The data to validate.

        Raises
        ------
        Error
            If the data is not equal to the expected value.
        """
        if self._check != data:
            raise Error(f"Expected {data!r} to be equal {self._check}")


class ContainerValidator(UnionMixin[T], typing.Generic[T]):
    """
    A special form of a union mixin that specifically works with multiple value validators.
    """

    @property
    def values(self) -> _tuple[T, ...]:
        """
        Public access to the values inside each value validator.

        Returns
        -------
        tuple[T, ...]
            The values to check against.
        """
        # noinspection PyUnresolvedReferences
        return tuple(checker.value for checker in self._vs)

    def __init__(self, *values: T):
        super().__init__(*map(ValueValidator, values))

    def __str__(self) -> str:
        return f"v in {self.values}"

    def validate(self, data: typing.Union[typing_extensions.Unpack[Ts]]) -> None:
        try:
            super().validate(data)
        except Error:
            raise Error(f"Expected {data!r} to be in {self.values}") from None


class UpperBoundValidator(Base[T], typing.Generic[T]):
    """
    A validator that checks if its input is below a certain level.

    Attributes
    ----------
    _limit: T
        The upper bound to check against.
    _inclusive: bool
        Whether the input is allowed to be the upper bound.
    _sym: str
        The symbol to describe the inequality.
    """

    @property
    def bound(self) -> T:
        """
        Public access to the upper bound.

        Returns
        -------
        T
            The upper bound to check against.
        """
        return self._limit

    @property
    def symbol(self) -> str:
        """
        Public access to the symbol associated with this instance.

        Returns
        -------
        str
            The symbol to describe the inequality.
        """
        return self._sym

    @property
    def inclusive(self) -> bool:
        """
        Public access to the inclusivity of the upper bound.

        Returns
        -------
        bool
            Whether the input is allowed to be the upper bound.
        """
        return self._inclusive

    def __init__(self, limit: T, *, inclusive=True):
        self._limit = limit
        self._inclusive = inclusive
        self._sym = "<=" if inclusive else "<"

    def __str__(self) -> str:
        return f"v {self._sym} {self._limit}"

    def validate(self, data: T) -> None:
        """
        Check if the input is valid.

        Parameters
        ----------
        data: T
            The input to validate.

        Raises
        ------
        Error
            If the input is larger than the limit (or equal to the limit if this instance is not inclusive).
        """
        if self._inclusive:
            bound = "less than or equal to"
            if data <= self._limit:
                return
        else:
            bound = "less than"
            if data < self._limit:
                return
        raise Error(f"Expected {data!r} to be {bound} than {self._limit}")


class DynamicUpperBoundValidator(UpperBoundValidator[T], typing.Generic[T]):
    """
    Special form of an upper bound validator that allows for a dynamic bound by calling a function.

    This function is expected to have no parameters, and as convention should have a chance to produce a different
    result on each call (i.e. using a regular upper bound validator is preferred over a function that always returns a
    constant)

    Attributes
    ----------
    _fn: Callable[[], T]
        The function to call to get the limit.
    """

    @property
    def _limit(self) -> T:
        return self._fn()

    @_limit.setter
    def _limit(self, value: T):
        pass

    def __init__(self, limit: typing.Callable[[], T], *, inclusive=True):
        self._fn = limit
        super().__init__(0, inclusive=inclusive)


class LowerBoundValidator(Base[T], typing.Generic[T]):
    """
    A validator that checks if its input is above a certain level.

    Attributes
    ----------
    _limit: T
        The lower bound to check against.
    _inclusive: bool
        Whether the input is allowed to be the lower bound.
    _sym: str
        The symbol to describe the inequality.
    """

    @property
    def bound(self) -> T:
        """
        Public access to the lower bound.

        Returns
        -------
        T
            The lower bound to check against.
        """
        return self._limit

    @property
    def symbol(self) -> str:
        """
        Public access to the symbol associated with this instance.

        Returns
        -------
        str
            The symbol to describe the inequality.
        """
        return self._sym

    @property
    def inclusive(self) -> bool:
        """
        Public access to the inclusivity of the lower bound.

        Returns
        -------
        bool
            Whether the input is allowed to be the lower bound.
        """
        return self._inclusive

    def __init__(self, limit: T, *, inclusive=True):
        self._limit = limit
        self._inclusive = inclusive
        self._sym = ">=" if inclusive else ">"

    def __str__(self) -> str:
        return f"v {self._sym} {self._limit}"

    def validate(self, data: T) -> None:
        """
        Check if the input is valid.

        Parameters
        ----------
        data: T
            The input to validate.

        Raises
        ------
        Error
            If the input is lower than the limit (or equal to the limit if this instance is not inclusive).
        """
        if self._inclusive:
            bound = "greater than or equal to"
            if data >= self._limit:
                return
        else:
            bound = "greater than"
            if data > self._limit:
                return
        raise Error(f"Expected {data!r} to be {bound} than {self._limit}")


class DynamicLowerBoundValidator(LowerBoundValidator[T], typing.Generic[T]):
    """
    Special form of a lower bound validator that allows for a dynamic bound by calling a function.

    This function is expected to have no parameters, and as convention should have a chance to produce a different
    result on each call (i.e. using a regular lower bound validator is preferred over a function that always returns a
    constant)

    Attributes
    ----------
    _fn: Callable[[], T]
        The function to call to get the limit.
    """

    @property
    def _limit(self) -> T:
        return self._fn()

    @_limit.setter
    def _limit(self, value: T):
        pass

    def __init__(self, limit: typing.Callable[[], T], *, inclusive=True):
        self._fn = limit
        super().__init__(0, inclusive=inclusive)


# noinspection PyUnresolvedReferences
class RangeValidator(CombinationMixin[T], typing.Generic[T]):
    """
    A special form of a combination mixin that specifically works with an upper and lower bound validator.
    """

    @property
    def bounds(self) -> _tuple[T, T]:
        """
        Public access to the lower and upper bounds of the validator.

        Returns
        -------
        tuple[T, T]
            The lower and upper bound.
        """
        return self._vs[0].bound, self._vs[1].bound

    def __init__(self, lower: LowerBoundValidator[T], upper: UpperBoundValidator[T]):
        super().__init__(upper, lower, mode=UnionType.AND)

    def __str__(self) -> str:
        return f"{self._vs[0].bound} {self._vs[0].symbol} v {self._vs[1].symbol} {self._vs[1].bound}"

    def validate(self, data: T) -> None:
        """
        Checks that the data is valid for the upper and lower bounds.

        Parameters
        ----------
        data: T
            The data to validate.

        Raises
        ------
        Error
            If invalid.
        """
        try:
            super().validate(data)
        except Error:
            lower = " (exclusive) " if not self._vs[0].inclusive else " "
            upper = " (exclusive)" if not self._vs[1].inclusive else ""
            l_bound, u_bound = map(lambda v: v.bound, self._vs)
            raise Error(f"Expected {data!r} to be between {l_bound}{lower}and {u_bound}{upper}") from None

    @classmethod
    def known(cls, bounds: _tuple[T, T], *, l_bound=True, u_bound=True) -> "RangeValidator[T]":
        """
        Shortcut constructor to construct a range from a known value.

        Parameters
        ----------
        bounds: tuple[T, T]
            The lower and upper bound values.
        l_bound: bool
            Whether the lower bound is included (default is True).
        u_bound: bool
            Whether the upper bound is included (default is True).

        Returns
        -------

        """
        lower = LowerBoundValidator(bounds[0], inclusive=l_bound)
        upper = UpperBoundValidator(bounds[1], inclusive=u_bound)
        return cls(lower, upper)

    @classmethod
    def unknown(cls, bounds: _tuple[typing.Callable[[], T], typing.Callable[[], T]], *, l_bound=True, u_bound=True) \
            -> "RangeValidator[T]":
        """
        Shortcut constructor to construct a range from an unknown value (but a known function).

        Parameters
        ----------
        bounds: tuple[T, T]
            The lower and upper bound functions.
        l_bound: bool
            Whether the lower bound is included (default is True).
        u_bound: bool
            Whether the upper bound is included (default is True).

        Returns
        -------

        """
        lower = DynamicLowerBoundValidator(bounds[0], inclusive=l_bound)
        upper = DynamicUpperBoundValidator(bounds[1], inclusive=u_bound)
        return cls(lower, upper)


class FactorValidator(Base[Num], typing.Generic[Num]):
    """
    A validator that checks if the input is a factor of the given value.

    Bound Generics
    --------------
    T: Num

    Generics
    --------
    Num: int or float
        The numerical data type to validate.

    Attributes
    ----------
    _stride: Num
        The data stride This is the right-hand side of the modulus operation.
    _accuracy: int
        The number of decimal places to consider for floating point types.
    """

    @property
    def mod(self) -> Num:
        """
        The stride (or factor) to check against.

        Returns
        -------
        Num
            The data stride.
        """
        return self._stride

    def __init__(self, mod: Num, *, accuracy=9):
        self._stride = mod
        self._accuracy = accuracy

    def __str__(self) -> str:
        return f"v % {self._stride}"

    def validate(self, data: Num) -> None:
        """
        Check if the division of the input data with the stride is an integer.

        Parameters
        ----------
        data: Num
            The data to validate.

        Raises
        ------
        Error
            If the input is not a valid multiple of the stride.
        """
        div = Decimal(f"{data:.{self._accuracy}f}") / Decimal(f"{self._stride:.{self._accuracy}f}")
        if int(div) != div:
            raise Error(f"Expected {data!r} to be a multiple of {self._stride}")


class IntegerValidator(Base[float]):
    """
    A validator that checks if a number is an integer.

    Bound Generics
    --------------
    T: float
    """

    def __str__(self) -> str:
        return "int(v) == v"

    def validate(self, data: float) -> None:
        """
        Check if the input float is an integer.

        Parameters
        ----------
        data: float
            The decimal to validate.

        Raises
        ------
        Error
            If the input is not the same as its truncated equivalent.
        """
        if int(data) != data:
            raise Error(f"Expected {data!r} to be an integer")


class TypeValidator(Base[T], typing.Generic[T]):
    """
    A validator that checks if input data is a specific type.

    Attributes
    ----------
    _type: Type[T]
        The type to check.
    _strict: bool
        Whether to strictly check for that type.
    """

    @property
    def target_type(self) -> typing.Type[T]:
        """
        Public access to the type.

        Returns
        -------
        Type[T]
            The type to check.
        """
        return self._type

    @property
    def strict(self) -> bool:
        """
        Public access to the inclusivity of the check.

        Returns
        -------
        bool
            Whether to strictly check for the type.
        """
        return self._strict

    def __init__(self, target: typing.Type[T], *, strict=False):
        self._type = target
        self._strict = strict

    def __str__(self) -> str:
        strict = " strictly " if self._strict else " "
        return f"v is{strict}{self._type}"

    def validate(self, data: T) -> None:
        """
        Check if the input data is the required type.

        Parameters
        ----------
        data: T
            The input data to validate.

        Raises
        ------
        Error
            If the input data is not an instance of the required type, or if it is not exactly the required type and
            strict mode is on.
        """
        if isinstance(data, self._type):
            if not self._strict:
                return
            elif type(data) is self._type:
                return
        strict = "and not a subclass instance" if self._strict else ""
        raise Error(f"Expected {data!r} to be an instance of {self._type} ({strict}). Got {type(data)}")


class MemoryValidator(Base[int]):
    """
    A validator that checks for the data size in memory of the input data.

    Bound Generics
    --------------
    T: int

    Attributes
    ----------
    _bits: int
        The maximum number of bits to use for the integer.

    Raises
    ------
    ValueError
        If the number of bits is negative.
    """

    @property
    def bit_size(self) -> int:
        """
        Public access to the maximum size.

        Returns
        -------
        int
            The maximum size in bits.
        """
        return self._bits

    @property
    def min(self) -> int:
        """
        Public access to the minimum value that the size can generate.

        Returns
        -------
        int
            The lowest number from the size. This is calculated using two's complement such that it is -(2 ** (n - 1))
            for size `n`.
        """
        return -(2 ** (self._bits - 1))

    @property
    def max(self) -> int:
        """
        Public access to the maximum value that the size can generate.

        Returns
        -------
        int
            The highest number from the size. This is calculated such that it is 2 ** n - 1 for size `n`.
        """
        return 2 ** self._bits - 1

    def __init__(self, num_bits: int):
        if num_bits < 0:
            raise ValueError(f"Expected positive number of bits (got {num_bits})")
        self._bits = num_bits

    def __str__(self) -> str:
        return f"v fits in {self._bits} bits"

    def validate(self, data: int) -> None:
        """
        Check the input data lies within the bitstream's range.

        Parameters
        ----------
        data: int
            The input data to validate.

        Raises
        ------
        Error
            If the input data cannot be constructed from the number of bits.
        """
        if not self.min <= data <= self.max:
            raise Error(f"Expected {data!r} to be represented by no more than {self._bits} bits")
