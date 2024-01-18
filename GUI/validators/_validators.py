import abc as _abc
import math as _math
from typing import (Generic as _Gen, Any as _Any, Iterable as _Iter, Hashable as _SupportsHash, Union as _Two,
                    Callable as _Func)

from ._constants import _T1, _T2, _Flag, _Num, Include


class _Error(Exception):

    def __init__(self, reason: str):
        self._msg = reason
        super().__init__(reason)

    def __str__(self) -> str:
        return f"Validation Error: {self._msg}"


class Validator(_Gen[_T1], _abc.ABC):
    """
    Abstract base class to represent a validator for a piece of data.

    Convention states when a validator is converted to a string, a question mark is placed after the finished condition.

    Provides format codes such that any specification replaces the 'v' term by 'v' and then the format code all in
    parentheses. The special format code '?' removes the question mark.

    Examples::

        validator = ValueValidator(6)
        print(f"{validator}") # outputs "v == 6?"
        print(f"{validator:i}") # outputs "(vi) == 6?"
        print(f"{validator:_#@}") # outputs "(v_#@) == 6?"
        print(f"all({validator:_i})?") # outputs "all((v_i) == 6?)?"
        print(f"all({validator:_i?})?") # outputs "all((v_i) == 6)?"
    """

    def __format__(self, format_spec: str) -> str:
        if format_spec == "":
            return str(self)
        remove = False
        if "?" in format_spec:
            format_spec = format_spec.replace("?", "")
            remove = True
        string = str(self).replace("v", f"(v{format_spec})")
        if remove:
            string = string[:-1]
        return string

    @_abc.abstractmethod
    def __str__(self) -> str:
        pass

    @_abc.abstractmethod
    def validate(self, ans: _T1) -> None:
        """
        Validates the data against the constraint provided by this validator.

        :param ans: The data to validate.
        :raises _Error: If the data is not valid.
        """
        pass


class TrueValidator(Validator[_Any]):
    """
    Special form of a validator that passes all data. Useful when translation between data types is validation enough.
    """

    def __str__(self) -> str:
        return "True?"

    def validate(self, ans: _T1) -> None:
        return


class MixinValidator(Validator[_T1], _Gen[_T1], _abc.ABC):
    """
    Abstract base class to represent a validator that affects the result of an inner validator in some way.

    Any attribute lookup searches the internal validator.

    :var Validator[_T1] _v: The inner validator.
    """

    def __init__(self, inner: Validator[_T1]):
        self._v = inner

    def __getattr__(self, item: str):
        return getattr(self._v, item)

    def validate(self, ans: _T1) -> None:
        self._v.validate(ans)


class UnionMixinValidator(MixinValidator[_Two[_T1, _T2]], _Gen[_T1, _T2]):
    """
    Concrete mixin to have multiple different validators that are *all* valid.

    :var Validator[_T2] _v2: The second inner validator.
    """

    def __init__(self, v1: Validator[_T1], v2: Validator[_T2]):
        super().__init__(v1)
        self._v2 = v2

    def __str__(self) -> str:
        return f"({self._v1:?} | {self._v2:?})?"

    def __getattr__(self, item: str):
        try:
            return super().__getattr__(item)
        except AttributeError:
            return getattr(self._v2, item)

    def validate(self, ans: _Two[_T1, _T2]) -> None:
        """
        Validates the data against both constraints - exiting on success.

        :param ans: The answer to validate.
        :raises _Error: If both constraints are violated.
        """
        try:
            super().validate(ans)
        except _Error:
            self._v2.validate(ans)


class IterableMixinValidator(MixinValidator[_T1], _Gen[_T1]):
    """
    Concrete mixin to check a validator on all elements of an iterable.
    """

    def __str__(self) -> str:
        return f"all({self._v:_i?})?"

    def validate(self, ans: _Iter[_T1]) -> None:
        """
        Validates each element of the data against the constraint.

        :param ans: An iterable of elements to validate.
        :raises _Error: If any element fails.
        """
        for i, elem in enumerate(ans):
            try:
                super().validate(elem)
            except _Error:
                raise _Error(f"Element {i} ({elem}) failed test '{self._v}'")


class Invalidator(MixinValidator[_T1], _Gen[_T1]):
    """
    Concrete mixin to pass when a validator fails.

    Useful for creating quick reversed validators (v not in (1, 2, 3)) without polluting the namespace.
    """

    def __str__(self) -> str:
        return f"not {self._v}"

    def validate(self, ans: _T1) -> None:
        """
        Inverts the validation of the data.

        :param ans: The answer to validate.
        :raises _Error: If the inner validator passes.
        """
        try:
            super().validate(ans)
        except _Error:
            return
        raise _Error(f"Expected {ans} to fail test '{self._v}'")


class ContainerValidator(Validator[_T1], _Gen[_T1]):
    """
    Concrete Validator to check if the data is in the given values.

    :var tuple[_T1,...] _vals: The values to check.
    :var str _str: The string representation of the values.
    """

    @property
    def values(self) -> tuple[_T1, ...]:
        """
        Public access to the container of values.

        :return: The values to check.
        """
        return self._vals

    def __init__(self, *values: _T1):
        self._vals = values
        self._str = ", or ".join(map(repr, values))

    def __str__(self) -> str:
        return f"v ∈ {self._vals}?"

    def validate(self, ans: _T1) -> None:
        """
        Validates the data against the specified values.

        :param ans: The data to validate.
        :raises _Error: If the data is not in the given values.
        """
        if ans not in self._vals:
            raise _Error(f"Expected {ans} to be either: {self._str}")

    @classmethod
    def bool(cls) -> "ContainerValidator[str]":
        """
        Alternate constructor to find all possibilities for boolean values from a string.

        :return: The container validator.
        """
        return cls("true", "false", "True", "False")


class ValueValidator(Validator[_T1], _Gen[_T1]):
    """
    Concrete Validator to check if the data is equal to the given value.

    :var _T1 _ans: The correct data.
    """

    @property
    def answer(self) -> _T1:
        """
        Public access to the answer for this validator.

        :return: The correct data.
        """
        return self._ans

    def __init__(self, correct: _T1):
        self._ans = correct

    def __str__(self) -> str:
        return f"v == {self._ans}?"

    def validate(self, ans: _T1) -> None:
        """
        Validates the data against the single value for this validator.

        :param ans: The data to validate.
        :raises _Error: If the data and the answer are not identical.
        """
        if ans != self._ans:
            raise _Error(f"Expected {ans} to be equal to {self._ans}")


class FlagValidator(Validator[_Flag], _Gen[_Flag]):
    """
    Concrete Validator to check if the answer is within the given flag value.

    :var _Flag _member: The flag value.
    """

    @property
    def flag(self) -> _Flag:
        """
        Public access to the flag member to check the data for.

        :return: The flag value.
        """
        return self._member

    def __init__(self, member: _Flag):
        self._member = member

    def __str__(self) -> str:
        return f"v & {self._member}?"

    def validate(self, ans: _T1) -> None:
        """
        Validates the data against the given flag.

        :param ans: The data to validate.
        :raises _Error: If the member is not part of the data.
        """
        if not (ans & self._member):
            raise _Error(f"Expected {self._member} to be a part of {ans}")


class UpperBoundValidator(Validator[_Num], _Gen[_Num]):
    """
    Concrete Validator to check for a ceiling value for the data.

    Acts like an open-start range.
    :var _Num _max: The maximum value in the range.
    :var bool _include: Whether the endpoint is included.
    :var str _cmp: The string representation of the comparison.
    """

    @property
    def maximum(self) -> _Num:
        """
        Public access to the ceiling value.

        :return: The maximum value in the range.
        """
        return self._max

    @property
    def inclusive(self) -> bool:
        """
        Public access to the inclusivity of the range.

        :return: Whether the endpoint is included.
        """
        return self._include

    def __init__(self, highest: _Num, inclusive=True):
        self._max = highest
        self._include = inclusive
        self._cmp = "<=" if inclusive else "<"

    def __str__(self) -> str:
        return f"v {self._cmp} {self._max}?"

    def validate(self, ans: _T1) -> None:
        """
        Validates the data against the open-start range provided by this validator.

        :param ans: The data to validate.
        :raises _Error: If the data is higher than the given maximum.
        """
        if ans >= self._max:
            if self._include and ans == self._max:
                return
            eq = "(or equal to)" if self._include else "(and not equal to)"
            raise _Error(f"Expected {ans} to be less than {eq} {self._max}")


class LowerBoundValidator(Validator[_Num], _Gen[_Num]):
    """
    Concrete Validator to check for a floor value for the data.

    Acts like an open-end range.
    :var _Num _min: The minimum value in the range.
    :var bool _include: Whether the endpoint is included.
    :var str _cmp: The string representation of the comparison.
    """

    @property
    def minimum(self) -> _Num:
        """
        Public access to the floor value.

        :return: The minimum value in the range.
        """
        return self._min

    @property
    def inclusive(self) -> bool:
        """
        Public access to the inclusivity of the range.

        :return: Whether the endpoint is included.
        """
        return self._include

    def __init__(self, lowest: _Num, inclusive=True):
        self._min = lowest
        self._include = inclusive
        self._cmp = ">=" if inclusive else ">"

    def __str__(self) -> str:
        return f"{self._min} {self._cmp} v?"

    def validate(self, ans: _T1) -> None:
        """
        Validates the data against the open-end range provided by this validator.

        :param ans: The data to validate.
        :raises _Error: If the data is lower than the given minimum.
        """
        if ans <= self._min:
            if self._include and ans == self._min:
                return
            eq = "(or equal to)" if self._include else "(and not equal to)"
            raise _Error(f"Expected {ans} to be greater than {eq} {self._min}")


class RangeValidator(UnionMixinValidator[_Num, _Num], _Gen[_Num]):
    """
    Special form of the UnionMixin that combines both a ceiling and floor validator.
    """

    @property
    def bounds(self) -> tuple[_Num, _Num]:
        """
        The lower and upper bounds of the validator.

        :return: The floor and ceiling values.
        """
        return self.minimum, self.maximum

    @property
    def includes(self) -> Include:
        """
        Public access to the bounds of the range.

        :return: The include specification.
        """
        bounds = Include.NONE
        if self._v.inclusive:
            bounds |= Include.LOW
        if self._v2.inclusive:
            bounds |= Include.HIGH
        return bounds

    def __init__(self, low: _Num, high: _Num, includes=Include.LOW | Include.HIGH):
        lower = LowerBoundValidator(low, bool(includes & Include.LOW))
        upper = UpperBoundValidator(high, bool(includes & Include.HIGH))
        super().__init__(lower, upper)

    def __str__(self) -> str:
        return f"({self._v:?} & {self._v2:?})?"

    def validate(self, ans: _Num) -> None:
        try:
            self._v.validate(ans)
            self._v2.validate(ans)
        except _Error:
            raise _Error(f"Expected {ans} to be between {self.minimum} and {self.maximum}")

    @classmethod
    def power(cls, base: _Num, exp: int, *, signed=False,
              includes=Include.LOW | Include.HIGH) -> "RangeValidator[_Num]":
        """
        Shortcut constructor to construct a range based on a power sequence.

        :param base: The base to count in.
        :param exp: The exponent to calculate.
        :param signed: Whether the range is signed from -(base ** exp) to +(base ** exp)
        :param includes: The 'include' specification.
        :return: The range validator.
        """
        if base <= 0:
            raise ValueError(f"Expected positive base")
        high = base ** exp
        return cls(-high * int(signed), high, includes=includes)

    @classmethod
    def bitstream(cls, num_bits: int, *, signed=False) -> "RangeValidator[int]":
        """
        Shortcut constructor to construct a range based on a specified bitstream value.

        Can also act as a storage validator - if an integer passes the validator then the number of bits to represent
        that integer is known.
        :param num_bits: The number of bits to use per endpoint.
        :param signed: Whether to use two's complement representation.
        :return: The range validator.
        """
        return cls.power(2, num_bits - int(signed), signed=signed, includes=Include.LOW)


class DynamicRangeValidator(Validator[_Num], _Gen[_Num]):
    """
    Concrete validator to represent a dynamic range of values.

    :var Callable[[], _Num] _l: The lowest possible value generator.
    :var Callable[[], _Num] _h: The highest possible value generator.
    :var Include _includes: The include specification.
    :var str _low: Easy to print lower bound.
    :var str _high: Easy to print upper bound.
    """

    def __init__(self, low_func: _Func[[], _Num], high_func: _Func[[], _Num], includes=Include.LOW | Include.HIGH):
        self._l = low_func
        self._h = high_func
        self._includes = includes
        self._low = "<=" if includes & Include.LOW else "<"
        self._high = "<=" if includes & Include.HIGH else "<"

    def __str__(self) -> str:
        return f"({self._l}() {self._low} v {self._high} {self._h}())?"

    def validate(self, ans: _Num) -> None:
        """
        Validate the data between the two function calls.

        :param ans: The data to validate
        :raises _Error: If the data does not lie between the range generated.
        """
        if ans <= (low := self._l()):
            if ans == low and not (self._includes & Include.LOW):
                raise _Error(f"Expected {ans} to be between the two values of {self._l} and {self._h}")
        elif ans >= (high := self._h()):
            if ans == high and not (self._includes & Include.HIGH):
                raise _Error(f"Expected {ans} to be between the two values of {self._l} and {self._h}")


class FactorValidator(Validator[_Num], _Gen[_Num]):
    """
    Concrete Validator for checking if the input data is a multiple of the specified number.

    :var _Num _stride: The modulus to check.
    """

    @property
    def mod(self) -> _Num:
        """
        Public access to the stride.

        :return: The modulus to check
        """
        return self._stride

    def __init__(self, mod: _Num):
        self._stride = mod

    def __str__(self) -> str:
        return f"v % {self._stride}?"

    def validate(self, ans: _Num) -> None:
        """
        Validates the data against the factor provided by this validator.

        :param ans: The data to validate.
        :raises _Error: If the data is not a multiple of the factor.
        """
        if not _math.isclose(ans - self._stride * int(ans / self._stride), 0):
            raise _Error(f"{ans} is not a multiple of {self._stride}")


class StrictIntValidator(Validator[float]):
    """
    Concrete Validator for checking if a float value can losslessly be narrowed to an integer
    """

    def __str__(self) -> str:
        return f"v ∈ Z?"

    def validate(self, ans: float) -> None:
        """
        Validates the data against its truncation.

        :param ans: The data to validate.
        :raises _Error: If the data is not equal to its truncation.
        """
        if int(ans) != ans:
            raise _Error(f"Expected {ans} to be an integer")


class UniqueValidator(Validator[_SupportsHash]):
    """
    Concrete Validator for checking if an iterable has unique values.
    """

    def __str__(self) -> str:
        return f"set(v) is v?"

    def validate(self, ans: _Iter[_SupportsHash]) -> None:
        """
        Validates the data against a set of all the elements.

        :param ans: The iterable to validate.
        :raises _Error: If any data appears more than once.
        """
        seen = set()
        for elem in ans:
            if elem in seen:
                raise _Error(f"Duplicate item ({elem}) found")
            seen.add(elem)


class StrictTypeValidator(Validator[_Any]):
    """
    Concrete Validator for checking whether an object is a specific type.

    :var type _cls: The type to check.
    """

    @property
    def target_type(self) -> type:
        """
        Public access to the target type.

        :return: The type to check.
        """
        return self._cls

    def __init__(self, target: type):
        self._cls = target

    def __str__(self) -> str:
        return f"v is {self._cls}?"

    def validate(self, ans: _Any) -> None:
        if not isinstance(ans, self._cls):
            raise _Error(f"Expected {ans} to be an instance of {self._cls}")
