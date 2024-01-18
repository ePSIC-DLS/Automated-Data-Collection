import abc
import functools
import typing

import numpy as np


class Dual(abc.ABC):
    """
    Class to represent the output of a function and the output of its derivative at the same input point.

    Any number can be represented by the dual '(x, 0)' where x is the number.

    :var _v float: The value of the function.
    :var _dv float: The value of the function's derivative.

    Examples::

        f(x) = x^2 + 2x + 3
        ∴ f'(x) = 2x + 2
        f((x, 0)) = (f(x), 0)
        f((x, 1)) = (f(x), f'(x))
        (18, 8) is (f(3), f'(3))
    """

    @abc.abstractmethod
    def __new__(cls, v: "Number", dv: "Number"):
        if isinstance(v, np.ndarray) and isinstance(dv, np.ndarray):
            return DualArray(v, dv)
        elif isinstance(v, (float, int)) and isinstance(dv, (float, int)):
            return DualNumber(v, dv)
        raise TypeError(f"Both inputs should be the same type (got {type(v) = } & {type(dv) = })")

    @property
    def x(self) -> "Number":
        """
        Public access to the value.
        :return: The value of the function.
        """
        return self._v

    @property
    def dx(self) -> "Number":
        """
        Public access to the derivative.
        :return: The value of the function's derivative.
        """
        return self._dv

    def __init__(self, v: "Number", dv: "Number"):
        self._v = v
        self._dv = dv

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.x}, {self.dx})"

    def __pos__(self) -> "Dual":
        return self

    def __neg__(self) -> "Dual":
        return -1 * self

    @staticmethod
    def _operator(fn: typing.Callable[["Dual", "Dual"], "Dual"]) \
            -> typing.Callable[["Dual", typing.Union["Dual", float, "Vector"]], "Dual"]:
        """
        Decorator to register a method as an operator – allows for float usage and handles NotImplemented throwing.
        :param fn: The wrapped function.
        :return: An 'operator' function.
        """

        @functools.wraps(fn)
        def _inner(self: "Dual", other: typing.Union["Dual", float, "Vector"]) -> "Dual":
            if isinstance(other, Dual):
                return fn(self, other)
            elif isinstance(other, (float, int)):
                return fn(self, DualNumber.from_number(other))
            elif isinstance(other, np.ndarray):
                return fn(self, DualArray.from_array(other))
            return NotImplemented

        return _inner

    @staticmethod
    def _roperator(fn: typing.Callable[["Dual", "Dual"], "Dual"]) \
            -> typing.Callable[["DualNumber", typing.Union[float, "Vector"]], "Dual"]:
        """
        Decorator to register a method as an RHS operator – parses to Dual and handles NotImplemented throwing.
        :param fn: The wrapped function.
        :return: An RHS 'operator' function.
        """

        def _inner(self: "Dual", other: typing.Union[float, "Vector"]) -> "Dual":
            if isinstance(other, (float, int)):
                return fn(DualNumber.from_number(other), self)
            elif isinstance(other, np.ndarray):
                return fn(DualArray.from_array(other), self)
            return NotImplemented

        return _inner

    @_operator
    def __add__(self, other: typing.Union["Dual", float, "Vector"]) -> "Dual":  # added union for type inspection
        return Dual(self.x + other.x, self.dx + other.dx)

    @_operator
    def __sub__(self, other: typing.Union["Dual", float, "Vector"]) -> "Dual":  # added union for type inspection
        return self + -other

    @_operator
    def __mul__(self, other: typing.Union["Dual", float, "Vector"]) -> "Dual":  # added union for type inspection
        """
        Handles the product rule.
        :param other: The dual number to use as the multiplier.
        :return: The new dual.
        """
        return Dual(self.x * other.x, self.dx * other.x + self.x * other.dx)

    @_operator
    def __truediv__(self, other: typing.Union["Dual", float, "Vector"]) -> "Dual":  # added union for type inspection
        """
        Handles the quotient rule.
        :param other: The dual number to use as the dividend.
        :return: The new dual.
        """
        return Dual(self.x / other.x, (self.dx * other.x - self.x * other.dx) / other.x ** 2)

    @_operator
    def __pow__(self, other: typing.Union["Dual", float, "Vector"]) -> "Dual":  # added union for type inspection
        value = self.x ** other.x
        return Dual(value, value * np.log(self.x) * other.dx + other.x * self.x ** (other.x - 1) * self.dx)

    __radd__ = __add__
    __rsub__ = _roperator(__sub__)
    __rmul__ = __mul__
    __rtruediv__ = _roperator(__truediv__)
    __rpow__ = _roperator(__pow__)


class DualNumber(Dual):
    """
    Specialist subclass of dual to represent scalars.
    """

    def __new__(cls, v: "Number", dv: "Number"):
        return object.__new__(cls)

    @classmethod
    def from_number(cls, num: float) -> "DualNumber":
        """
        Alternative constructor to give the dual '(x, 0)'.
        :param num: The x to use.
        :return: The dual '(x, 0)'.
        """
        return cls(num, 0)


class DualArray(Dual):
    """
    Specialist subclass of dual to represent vectors.
    """

    @property
    def x(self) -> "Vector":
        return self._X

    @property
    def dx(self) -> "Vector":
        return self._DX

    def __new__(cls, v: "Vector", dv: "Vector"):
        return object.__new__(cls)

    def __init__(self, v_bar: "Vector", dv_bar: "Vector"):
        super().__init__(0, 0)
        self._X = v_bar
        self._DX = dv_bar

    @classmethod
    def from_array(cls, arr: "Vector") -> "DualArray":
        """
        Alternative constructor to give the dual '(x_, 0_)', where _ means vector.
        :param arr: The x_ to use.
        :return: The dual '(x_, 0_)'
        """
        return cls(arr, np.zeros(arr.shape))


Expr: typing.TypeAlias = typing.Union[float, DualNumber]
ArrExpr: typing.TypeAlias = typing.Union["Vector", DualArray]
Number: typing.TypeAlias = typing.Union["Vector", float]
T = typing.TypeVar("T", bound=typing.Union[Dual, float, "Vector"])


class Expression(typing.Generic[T]):
    """
    Decorator to create an expression that can be differentiated.

    :var _fn Callable[[T], T]: The procedure providing the expression.
    """

    def __init__(self, fn: typing.Callable[[T], T]):
        self._fn = fn
        functools.update_wrapper(self, fn)

    def __call__(self, x: T) -> T:
        return self._fn(x)

    @classmethod
    def register_function(cls, f_x: typing.Callable[[Number], Number], f_prime_x: typing.Callable[[Number], Number]) \
            -> "Expression":
        """
        Alternative constructor to form an Expression from a known function and its derivative.
        :param f_x: The function to register.
        :param f_prime_x: The derivative of the function.
        :return: New expression based on a function and its derivative.
        """

        @functools.wraps(f_x)
        def _inner(x: T) -> T:
            if isinstance(x, Dual):
                return Dual(f_x(x.x), f_prime_x(x.x) * x.dx)
            return Dual(f_x(x), f_prime_x(x)).x

        return Expression(_inner)


def derivative(fn: Expression[Dual]) -> typing.Callable[[Number], Number]:
    """
    Decorator to register an expression as one that automatically calculates the derivative.

    Will strip away the underlying expression and use an internal function.
    :param fn: The expression to calculate the derivative of.
    :return: A function that takes a float and returns the derivative of the expression at that point.

    Examples::

        @Expression[DualNumber]
        def poly(x: DualNumber) -> DualNumber:
             return x ** 2
        linear=derivative(poly)
        print(poly(DualNumber(3, 0))) # yields 'DualNumber(9,0)' (x^2)
        print(linear(3)) # yields 6 (2x)

        @derivative
        @Expression[DualNumber]
        def quadratic(x: DualNumber) -> DualNumber:
            return x**3
        print(quadratic(10)) # yields 300 (3x^2)
    """

    @functools.wraps(fn)
    def _inner(x: Number) -> Number:
        return fn(Dual(x, 1 if isinstance(x, (float, int)) else np.ones(x.shape))).dx

    return _inner


def derive(expr: Expression[Dual], x: Number) -> Number:
    """
    Convenience function to automatically derive the expression at the given point without having to create a new
    callable.

    Differences between this and derivative::

        import numpy as np
        sin = Expression.register_function(np.sin, np.cos)
        cos_pi = derivative(sin)(np.pi) # a new callable is created and then called to achieve the result
        cos_pi = derive(sin, np.pi) # no new callable is created; the value is extracted immediately
    :param expr: The expression to derive.
    :param x: The value to derive it at.
    :return: The value of the derivative of the expression at the given point.
    """
    return derivative(expr)(x)


Vector: typing.TypeAlias = np.ndarray[float]


class ActFunc:
    """
    Decorator to represent an activation function.
    The expression should take a vector, and return a vector. As it uses DualArray, it can be differentiated without
    the definition being written elsewhere.

    For given activation function f and given input vector X:
        * Use f(X) to get the result of the function.
        * Use f[X] to get the result of the derivative of the function.
    """

    def __init__(self, expr: typing.Callable[[Vector], Vector]):
        if not isinstance(expr, Expression):
            expr = Expression(expr)
        self._f = expr
        self._df = derivative(expr)
        functools.update_wrapper(self, expr)

    def __call__(self, x: Vector) -> Vector:
        val = self._f(DualArray.from_array(x))
        if isinstance(val, DualArray):
            val = val.x
        return val

    def __getitem__(self, x: Vector) -> Vector:
        """
        Find the derivative of the function at the point x.
        :param x: The input point.
        :return: The value of the derivative function.
        """
        return self._df(x)


class LossFunc:
    """
    Decorator to represent a loss function.
    The expression should take two vectors (actual and prediction), and return a vector.
    As it uses DualArray, it can be differentiated without the definition being written elsewhere.

    For given loss function f and given inputs T and Y:
        * Use f(T, Y) to get the result of the function.
        * Use f[T, Y] to get the result of the derivative of the function.
    """

    def __init__(self, expr: typing.Callable[[ArrExpr, ArrExpr], DualNumber]):
        self._f = expr
        self._df = lambda a, p: expr(DualArray(a, np.ones(a.shape)), DualArray.from_array(p)).dx
        functools.update_wrapper(self, self._f)

    def __call__(self, a: Vector, p: Vector) -> float:
        if a.shape[0] != p.shape[0]:
            raise ValueError("Expected target and prediction to have same shape")
        return self._f(DualArray.from_array(a), DualArray.from_array(p)).x

    def __getitem__(self, item: tuple[Vector, Vector]) -> float:
        """
        Find the derivative of the function at the point a, p.
        :param item: The two input points.
        :return: The value of the derivative function.
        """
        a, p = item
        if a.shape[0] != p.shape[0]:
            raise ValueError("Expected target and prediction to have same shape")
        return self._df(a, p)
