import abc as _abc
import enum as _enum
from functools import reduce as _reduce
from typing import (Generic as _Gen, Type as _Type, Iterable as _Iter, Union as _Two, Sequence as _SupportsGetItem,
                    Sized as _SupportsLen)

from PyQt5.Qt import Qt as _QEnums

from ._constants import _TS, _TD1, _TD2, _Enum, _K, UnaryOperator, BinaryOperator


class _Error(Exception):

    def __init__(self, reason: str):
        self._msg = reason
        super().__init__(reason)

    def __str__(self) -> str:
        return f"Translation Error: {self._msg}"


class Translator(_Gen[_TS, _TD1], _abc.ABC):
    """
    Abstract base class to translate between two data types.
    """

    @_abc.abstractmethod
    def __str__(self) -> str:
        pass

    @_abc.abstractmethod
    def translate(self, ans: _TS) -> _TD1:
        """
        Main method to translate between the two data types specified.

        :param ans: The data to be translated.
        :return: The translated data.
        """
        pass


class MixinTranslator(Translator[_TS, _TD1], _Gen[_TS, _TD1], _abc.ABC):
    """
    Abstract base class to represent a translator that uses the result of an inner translator in some way.

    Any attribute lookup searches the internal translator.

    :var Translator[_TS, _TD1] _t: The inner translator.
    """

    def __init__(self, inner: Translator[_TS, _TD1]):
        self._t = inner

    def __getattr__(self, item: str):
        return getattr(self._t, item)

    def translate(self, ans: _TS) -> _TD1:
        return self._t.translate(ans)


class UnionMixinTranslator(MixinTranslator[_TS, _Two[_TD1, _TD2]], _Gen[_TS, _TD1, _TD2]):
    """
    Concrete mixin to have multiple different translations that are *all* valid.

    :var Translator[_TD2] _t2: The second inner translator.
    """

    def __init__(self, t1: Translator[_TS, _TD1], t2: Translator[_TS, _TD2]):
        super().__init__(t1)
        self._t2 = t2

    def __str__(self) -> str:
        return f"({self._t1} | {self._t2})?"

    def __getattr__(self, item: str):
        try:
            return super().__getattr__(item)
        except AttributeError:
            return getattr(self._t2, item)

    def translate(self, ans: _TS) -> _Two[_TD1, _TD2]:
        """
        Translates the data into one of the two data types - exiting on success.

        :param ans: The data to translate.
        :return: The translated data.
        :raises _Error: If the data cannot be translated.
        """
        try:
            return super().translate(ans)
        except _Error:
            return self._t2.translate(ans)


class IterableMixinTranslator(MixinTranslator[_TS, _TD1], _Gen[_TS, _TD1]):
    """
    Concrete mixin to translate all elements of an iterable.
    """

    def __str__(self) -> str:
        return f"map({self._t}, v)"

    def translate(self, ans: _Iter[_TS]) -> _Iter[_TD1]:
        """
        Translates all elements of the iterable by using the inner translator.

        :param ans: An iterable of elements to translate.
        :return: An iterable of translated elements.
        """
        for i, elem in enumerate(ans):
            try:
                yield self._t.translate(elem)
            except _Error:
                raise _Error(f"Element {i} ({elem}) cannot be translated via '{self._t}'")


class EnumTranslator(Translator[str, _Enum], _Gen[_Enum]):
    """
    Concrete translator to translate a string representing an enum member into the exact member.

    :var Type[_Enum] _CT: The current enumeration.
    """

    @property
    def enum(self) -> _Type[_Enum]:
        """
        Public access to the enumeration to typecast to.

        :return: The current enumeration.
        """
        return self._CT

    def __init__(self, cls: _Type[_Enum]):
        self._CT = cls

    def __str__(self) -> str:
        return f"{self._CT}.v"

    def translate(self, ans: str) -> _Enum:
        """
        Translate a string into the matching enum member. Will handle flag types automatically.

        :param ans: The member to translate.
        :return: The enum member.
        """
        if issubclass(self._CT, _enum.Flag) and "|" in ans:
            return _reduce(lambda x, y: x | y, map(self.translate, ans.split("|")))
        try:
            return self._CT[ans]
        except KeyError:
            raise _Error(f"{ans} is not a valid {self._CT} member") from None


class QtCheckState(Translator[bool, _QEnums.CheckState]):
    """
    Concrete translator to translate a boolean result to a check state.
    """

    def __str__(self) -> str:
        return f"{_QEnums.CheckState}"

    def translate(self, ans: bool) -> _QEnums.CheckState:
        """
        Translate a boolean into the matching check state.

        :param ans: The state to translate.
        :return: The check state.
        """
        if ans:
            return _QEnums.Checked
        return _QEnums.Unchecked


class TypeTranslator(Translator[_TS, _TD1], _Gen[_TS, _TD1]):
    """
    Concrete translator to translate between two types.

    :var _Type[TD1] _cls: The output type.
    """

    @property
    def dest_type(self) -> _Type[_TD1]:
        """
        Public access to the destination type.

        :return: The output type.
        """
        return self._cls

    def __init__(self, cls: _Type[_TD1]):
        self._cls = cls

    def __str__(self) -> str:
        return f"{self._cls}(v)"

    def translate(self, ans: _TS) -> _TD1:
        try:
            return self._cls(ans)
        except Exception:
            raise _Error(f"Cannot translate {ans} to {self._cls}")


class StrBoolTranslator(TypeTranslator[str, bool]):
    """
    Special form of a type translator that correctly handles 'false' as the falsey boolean.
    """

    def __init__(self):
        super().__init__(bool)

    def translate(self, ans: str) -> bool:
        """
        Translates between a string and a boolean, while correctly handling the string representations of booleans.

        :param ans: The string to be translated.
        :return: The boolean result of the string.
        """
        if ans.lower() == "false":
            ans = ""
        return super().translate(ans)


class PositionTranslator(Translator[_SupportsGetItem[_TD1], _TD1], _Gen[_TD1, _K]):
    """
    Concrete Translator that accesses data at a position.

    :var _K _i: The index to access the data from.
    """

    @property
    def index(self) -> _K:
        """
        Public access to the position.

        :return: The index to access the data from.
        """
        return

    def __init__(self, position: _K):
        self._i = position

    def __str__(self) -> str:
        return f"v[{self._i}]"

    def translate(self, ans: _SupportsGetItem[_TD1]) -> _TD1:
        try:
            return ans[self._i]
        except Exception:
            raise _Error(f"{self._i} is an invalid position for {ans}")


class PropertyTranslator(Translator[_TS, _TD1], _Gen[_TS, _TD1]):
    """
    Concrete Translator that accesses an attribute of the data.

    :var str _name: The property name to access. Must be a valid identifier that is public (cannot start with _).
    """

    @property
    def property(self) -> str:
        """
        Public access to the attribute name.

        :return: The property name to access.
        """
        return self._name

    def __init__(self, prop_name: str):
        if not prop_name.isidentifier() or prop_name.startswith("_"):
            raise ValueError(f"Expected valid identifier, got {prop_name}")
        self._name = prop_name

    def __str__(self) -> str:
        return f"v.{self._name}"

    def translate(self, ans: _TS) -> _TD1:
        """
        Translates the data by accessing a public attribute.

        :param ans: The object.
        :return: The value of the attribute.
        """
        try:
            return getattr(ans, self._name)
        except AttributeError:
            raise _Error(f"{type(ans)} has no attribute {self._name!r}")


class MethodCallerTranslator(PropertyTranslator[_TS, _TD1], _Gen[_TS, _TD1]):
    """
    Special form of a property translator that will access a method and call it.
    """

    def __str__(self) -> str:
        return f"{super().__str__()}()"

    def translate(self, ans: _TS) -> _TD1:
        func = super().translate(ans)
        try:
            return func()
        except Exception as err:
            raise _Error(f"Error when calling {ans}.{self._name}: {type(err), err}")


class SizeTranslator(Translator[_SupportsLen, int]):
    """
    Concrete translator that will translate an iterable into its size.
    """

    def __str__(self) -> str:
        return f"len(v)"

    def translate(self, ans: _SupportsLen) -> int:
        """
        Tanslates the data by taking its length.

        :param ans: The sized object to measure.
        :return: Its length.
        """
        return len(ans)


class UnaryTranslator(Translator[_TS, _TS], _Gen[_TS]):
    """
    Concrete translator to take a value and apply a unary operator to it.

    :var UnaryOperator _op: The operator to apply.
    """

    @property
    def operator(self) -> UnaryOperator:
        """
        Public access to the unary operator type.

        :return: The operator to apply.
        """
        return self._op

    def __init__(self, operator: UnaryOperator):
        self._op = operator

    def __str__(self) -> str:
        return f"{self._op.value}v"

    def translate(self, ans: _TS) -> _TS:
        """
        Translates the data by applying the specified unary operator.

        :param ans: The data to translate.
        :return: The translated data.
        """
        if self._op == UnaryOperator.INVERT:
            return ~ans
        elif self._op == UnaryOperator.POSITIVE:
            return +ans
        return -ans


class BinaryTranslator(Translator[_TS, _TS], _Gen[_TS]):
    """
    Concrete translator to take a value and apply a binary operator (with a fixed value) to it.

    :var BinaryOperator _op: The operator to apply.
    :var _TS _rhs: The value to use.
    :var bool _is_lhs: Whether to invert the positions of the operands.
    """

    @property
    def operator(self) -> BinaryOperator:
        """
        Public access to the binary operator type.

        :return: The operator to apply.
        """
        return self._op

    @property
    def value(self) -> _TS:
        """
        Public access to the value.

        :return: The value to use.
        """
        return self._rhs

    def __init__(self, operator: BinaryOperator, operand: _TS, *, invert_order=False):
        self._op = operator
        self._rhs = operand
        self._is_lhs = invert_order

    def __str__(self) -> str:
        if self._is_lhs:
            return f"{self._rhs} {self._op.value} v"
        return f"v {self._op.value} {self._rhs}"

    def translate(self, ans: _TS) -> _TD1:
        """
        Translate the data by applying a binary operator with a fixed value to it.

        :param ans: The data to translate.
        :return: The translated data.
        """
        if self._is_lhs:
            ans, self._rhs = self._rhs, ans
        try:
            if self._op == BinaryOperator.ADD:
                return ans + self._rhs
            elif self._op == BinaryOperator.SUBTRACT:
                return ans - self._rhs
            elif self._op == BinaryOperator.MULTIPLY:
                return ans * self._rhs
            elif self._op == BinaryOperator.TRUE_DIVISION:
                return ans / self._rhs
            elif self._op == BinaryOperator.FLOOR_DIVISION:
                return ans // self._rhs
            elif self._op == BinaryOperator.EXPONENT:
                return ans ** self._rhs
            elif self._op == BinaryOperator.MATRIX_MULTIPLICATION:
                return ans @ self._rhs
            elif self._op == BinaryOperator.BITWISE_OR:
                return ans | self._rhs
            elif self._op == BinaryOperator.BITWISE_AND:
                return ans & self._rhs
            elif self._op == BinaryOperator.BITWISE_XOR:
                return ans ^ self._rhs
        finally:
            if self._is_lhs:
                ans, self._rhs = self._rhs, ans


class FStringTranslator(BinaryTranslator[str]):
    """
    Special form of a binary translator that applies an f-string version of replacement for strings.

    Faster and saves memory compared to using repeated BinaryTranslators with the ADD operator.
    However, no formatting can be applied to values.
    """

    def __init__(self, string: str, *, replacement="{}"):
        super().__init__(BinaryOperator.ADD, string)
        self._r = replacement

    def __str__(self) -> str:
        return f"f\"{self._rhs.replace(self._r, '{v}')}\""

    def translate(self, ans: str) -> str:
        return self._rhs.replace(self._r, ans)
