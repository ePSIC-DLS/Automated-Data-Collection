import functools
import typing
from typing import Optional as _None, Tuple as _tuple

import numpy as np

from ._aliases import *

Expr = typing.Union["DualNumber", Number]

__all__ = ["Expr", "DualNumber", "DualFunction", "derive", "ActivationFunction", "LossFunction"]


class DualNumber:
    """
    A way of implementing automatic differentiation.

    A dual number is in the form `z = a + bε` where `ε ≠ 0` but `ε ^ 2 = 0`.
    It has a unique property such that operators defined on it obey derivative rules for the epsilon component.

    Attributes
    ----------
    _x: Number
        The regular component.
    _dx: Number
        The derivative of the regular component.

    Raises
    ------
    TypeError
        If the second argument is a Dual Number.
    """

    @property
    def real(self) -> Number:
        """
        Public access to the `a` component of the dual number.

        Returns
        -------
        Number
            The regular component.
        """
        return self._x

    @property
    def derivative(self) -> Number:
        """
        Public access to the `b` component of the dual number.

        Returns
        -------
        Number
            The derivative of the regular component.
        """
        return self._dx

    def __new__(cls, x: Number, y: Number) -> "DualNumber":
        if isinstance(y, DualNumber):
            raise TypeError(f"Dual derivative?? {x = !s}, {y = !s}")
        if isinstance(x, DualNumber):
            print(f"Dual real -> {x = !s}, {y = !s}")
            return DualNumber(x.real, x.derivative * y)
        return super().__new__(cls)

    def __init__(self, x: Number, dx: Number):
        self._x = x
        self._dx = dx

    def __getitem__(self, item: Number) -> Number:
        """
        Extract an item out of the `a` component array.

        Parameters
        ----------
        item: Number
            The index to extract.

        Returns
        -------
        Number
            The extracted item.
        """
        return np.asarray(self._x)[item]

    def __setitem__(self, key: Number, value: Number):
        """
        Edit an item in the `a` component array.

        Parameters
        ----------
        key: Number
            The index to edit.
        value: Number
            The new value.
        """
        np.asarray(self._x)[key] = value

    def __len__(self) -> int:
        return (np.asarray(self._x).shape or (1,))[0]

    def __str__(self) -> str:
        return f"{self._x} + {self._dx}ε"

    def __pos__(self) -> "DualNumber":
        """
        Convert the Dual Number to its positive form.

        Returns
        -------
        DualNumber
            The number multiplied by 1.
        """
        return DualNumber(+self._x, +self._dx)

    def __neg__(self) -> "DualNumber":
        """
        Convert the Dual Number to its negative form.

        Returns
        -------
        DualNumber
            The number multiplied by -1.
        """
        return DualNumber(-self._x, -self._dx)

    def __eq__(self, other: Expr) -> bool:
        """
        Compare two `DualNumber` instances for equality. Note that like other binary operators, can also take a Number.

        Parameters
        ----------
        other: Expr
            The expression to compare to. This only compares the `a` components.
        """
        if (other := self._cast(other)) is not None:
            return self.real == other.real
        return NotImplemented

    def __lt__(self, other: Expr) -> bool:
        """
        Compare two `DualNumber` instances for minima. Note that like other binary operators, can also take a Number.

        Parameters
        ----------
        other: Expr
            The expression to compare to. This only compares the `a` components.
        """
        if (other := self._cast(other)) is not None:
            return self.real < other.real
        return NotImplemented

    def __gt__(self, other: Expr) -> bool:
        """
        Compare two `DualNumber` instances for maxima. Note that like other binary operators, can also take a Number.

        Parameters
        ----------
        other: Expr
            The expression to compare to. This only compares the `a` components.
        """
        if (other := self._cast(other)) is not None:
            return self.real > other.real
        return NotImplemented

    def __le__(self, other: Expr) -> bool:
        """
        Compare two `DualNumber` instances for equality or minima.

        Note that like other binary operators, can also take a Number.

        Parameters
        ----------
        other: Expr
            The expression to compare to. This only compares the `a` components.
        """
        if (other := self._cast(other)) is not None:
            return self.real <= other.real
        return NotImplemented

    def __ge__(self, other: Expr) -> bool:
        """
        Compare two `DualNumber` instances for equality or maxima.

        Note that like other binary operators, can also take a Number.

        Parameters
        ----------
        other: Expr
            The expression to compare to. This only compares the `a` components.
        """
        if (other := self._cast(other)) is not None:
            return self.real >= other.real
        return NotImplemented

    def __add__(self, other: Expr) -> "DualNumber":
        """
        Add two `DualNumber` instances. Note that like other binary operators, can also take a Number.

        Parameters
        ----------
        other: Expr
            The expression to add. This follows the derivative rule `z0 + z1 = (a0 + a1) + (b0 + b1)ε`.
        """
        if (other := self._cast(other)) is not None:
            return DualNumber(self.real + other.real, self.derivative + other.derivative)
        return NotImplemented

    def __radd__(self, other: Number) -> "DualNumber":
        return self + other

    def __sub__(self, other: Expr) -> "DualNumber":
        """
        Subtract two `DualNumber` instances. Note that like other binary operators, can also take a Number.

        Parameters
        ----------
        other: Expr
            The expression to subtract. This follows the derivative rule `z0 - z1 = z0 + -z1`.
        """
        if (other := self._cast(other)) is not None:
            return self + -other
        return NotImplemented

    def __rsub__(self, other: Expr) -> "DualNumber":
        if (other := self._cast(other)) is not None:
            return other + -self
        return NotImplemented

    def __mul__(self, other: Expr) -> "DualNumber":
        """
        Multiply two `DualNumber` instances. Note that like other binary operators, can also take a Number.

        Parameters
        ----------
        other: Expr
            The expression to multiply. This follows the derivative rule `z0 * z1 = (a0 * a1) + (b0 * a1 + a0 * b0)ε`.
        """
        if (other := self._cast(other)) is not None:
            return DualNumber(self.real * other.real, self.derivative * other.real + self.real * other.derivative)
        return NotImplemented

    def __rmul__(self, other: Expr) -> "DualNumber":
        if (other := self._cast(other)) is not None:
            return self * other
        return NotImplemented

    def __truediv__(self, other: Expr) -> "DualNumber":
        """
        Divide two `DualNumber` instances. Note that like other binary operators, can also take a Number.

        Parameters
        ----------
        other: Expr
            The expression to divide. This follows the derivative rule
            `z0 / z1 = (a0 / a1) + ((b0 * a1 - a0 * b0) / a1 ^ 2)ε`.
        """
        if (other := self._cast(other)) is not None:
            return DualNumber(self.real / other.real,
                              (self.derivative * other.real - self.real * other.derivative) / other.real ** 2)
        return NotImplemented

    def __rtruediv__(self, other: Expr) -> "DualNumber":
        if (other := self._cast(other)) is not None:
            return other / self
        return NotImplemented

    def __pow__(self, power: Expr, modulo=None) -> "DualNumber":
        """
        Exponent two `DualNumber` instances. Note that like other binary operators, can also take a Number.

        Parameters
        ----------
        power: Expr
            The expression to raise this DualNumber to. This follows the derivative rule
            `z0 ^ z1 = (a0 ^ a1) + (a0 ^ a1 * log(a0) * b1 + a1 * a0 ^ (a1 - 1) * b1)ε`.
        """
        if (other := self._cast(power)) is not None:
            real = self.real ** other.real
            if isinstance(power, DualNumber):
                d1 = (real * np.log(self.real) * other.derivative)
            else:
                d1 = 0
            return DualNumber(real, d1 + (other.real * self.real ** (other.real - 1) * self.derivative))
        return NotImplemented

    def __rpow__(self, other: Expr) -> "DualNumber":
        if (other := self._cast(other)) is not None:
            return other ** self
        return NotImplemented

    @classmethod
    def _cast(cls, other: Expr) -> _None["DualNumber"]:
        if isinstance(other, DualNumber):
            return other
        try:
            other = DualNumber.from_real(np.float_(other))
        except TypeError:
            return
        else:
            return other

    @classmethod
    def from_real(cls, real: Number, *, derivable=False) -> "DualNumber":
        """
        Alternate constructor for a DualNumber from a singular `a` component.

        Parameters
        ----------
        real: Number
            The `a` component.
        derivable: bool
            Whether the `b` component is 1. Defaults to False.

        Returns
        -------
        DualNumber
            The constructed dual number.
        """
        return DualNumber(real, np.ones_like(real) * int(derivable))


class DualFunction:
    """
    Class-based functor to enact the chain rule based on existing functions.

    Attributes
    ----------
    _f: DualAble
        The normal function.
    _df: DualAble
        The derived function.
    """

    def __init__(self, f: DualAble, df: DualAble):
        self._f = f
        self._df = df
        functools.update_wrapper(self, f)

    def __call__(self, x: Expr) -> Expr:
        if isinstance(x, DualNumber):
            return DualNumber(self._f(x.real), self._df(x.real) * x.derivative)
        return self._f(x)


def derivative(f: DualFunction) -> typing.Callable[[Number], Number]:
    """
    Decorator to automatically calculate the derivative of the input.

    Parameters
    ----------
    f: DualFunction
        The function to calculate the chain rule.

    Returns
    -------
    Callable[[Number], Number]
        The wrapper to calculate the derivative of the provided function.
    """

    @functools.wraps(f)
    def _operator(x: Number) -> Number:
        return f(DualNumber.from_real(x, derivable=True)).derivative

    return _operator


def derive(f: DualFunction, x: Number) -> Number:
    """
    Shorthand to automatically calculate the derivative of a function at a specified input.

    Note that this differs from the `derivative` decorator as it does not create an intermediary callable.

    Parameters
    ----------
    f: DualFunction
        The function to derive.
    x: Number
        The input to take the derivative at.

    Returns
    -------
    Number
        The derivative.
    """
    return derivative(f)(x)


class ActivationFunction:
    """
    Class-based decorator to represent an activation function used in forwards propagation.

    Note that this provides the callable syntax to represent the `a` component, and the indexing syntax to represent the
    `b` component.

    Attributes
    ----------
    _fn: Callable[[DualNumber], DualNumber]
        The function to use.
    """

    @property
    def original(self) -> typing.Callable[[DualNumber], DualNumber]:
        """
        Public access to the original function.

        Returns
        -------
        Callable[[DualNumber], DualNumber]
            The function to use.
        """
        return self._fn

    def __init__(self, fn: typing.Callable[[DualNumber], DualNumber]):
        self._fn = fn
        functools.update_wrapper(self, fn)

    def __repr__(self) -> str:
        return self.__name__

    def __call__(self, x: Number) -> Number:
        """
        Calculate the result of the wrapped function and return the `a` component.

        Parameters
        ----------
        x: Number
            The input.

        Returns
        -------
        Number
            The regular component of the wrapped function at the point `x`.
        """
        return self._fn(DualNumber.from_real(x)).real

    def __getitem__(self, item: Number) -> Number:
        """
        Calculate the result of the wrapped function and return the `b` component.

        Parameters
        ----------
        item: Number
            The input.

        Returns
        -------
        Number
            The derivative of the regular component of the wrapped function at the point `item`.
        """
        return self._fn(DualNumber.from_real(item, derivable=True)).derivative


class LossFunction:
    """
    Class-based decorator to represent a loss function used in backwards propagation.

    Attributes
    ----------
    _fn: Callable[[DualNumber, DualNumber], DualNumber]
        The function to use.
        Note that it takes the actual result and predicted result as arguments.
    """

    @property
    def original(self) -> typing.Callable[[DualNumber, DualNumber], DualNumber]:
        """
        Public access to the original function.

        Returns
        -------
        Callable[[DualNumber, DualNumber], DualNumber]
            The function to use.
        """
        return self._fn

    def __init__(self, fn: typing.Callable[[DualNumber, DualNumber], DualNumber]):
        self._fn = fn
        functools.update_wrapper(self, fn)

    def __repr__(self) -> str:
        return self.__name__

    def __call__(self, a: Number, p: Number) -> Number:
        """
        Calculate the result of the wrapped function and return the `a` component.

        Parameters
        ----------
        a: Number
            The actual result.
        p: Number
            The predicted result.

        Returns
        -------
        Number
            The regular component of the wrapped function at the point `a, p`.
        """
        a, p = self._sanitise(a, p)
        return self._fn(a, p).real

    def __getitem__(self, item: _tuple[Number, Number]) -> Number:
        """
        Calculate the result of the wrapped function and return the `b` component.

        Parameters
        ----------
        item: tuple[Number, Number]
            The actual and predicted result.

        Returns
        -------
        Number
            The derivative of the regular component of the wrapped function (with respect to `p`) at the point `item`.
        """
        a, p = self._sanitise(*item)
        return self._fn(a, p).derivative

    @staticmethod
    def _sanitise(a: Number, p: Number) -> _tuple[DualNumber, DualNumber]:
        arr_a = np.asarray(a)
        arr_p = np.asarray(p)
        if arr_a.shape != arr_p.shape:
            raise TypeError("Expected parameters to have equal shapes")
        return DualNumber.from_real(arr_a), DualNumber.from_real(arr_p, derivable=True)
