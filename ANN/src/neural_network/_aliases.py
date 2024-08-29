"""
Common aliases for neural networks

Attributes
----------
Number: ArrayLike
    A number is defined as a scalar or an array of numbers.
Vector: Ndarray[float_, (x)]
    A vector is defined as a 1-dimensional array of floats.
DualAble: Callable[[Number], Number]
    A dual-able function takes a number and returns another number.
"""
import numpy as _np
from numpy import typing as _npt
from typing import Callable as _Func

Number = _npt.ArrayLike
Vector = _npt.NDArray[_np.float_]
DualAble = _Func[[Number], Number]
