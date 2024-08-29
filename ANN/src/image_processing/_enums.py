from enum import Enum as _Base, auto as _member, Flag as _Bit
from typing import Callable as _Func
from numpy.typing import ArrayLike as _Array
from numpy import count_nonzero as _valid


class Axis(_Base):
    """
    Enumeration to represent the image axes available.

    Members
    -------
    X

    Y

    """
    X = _member()
    Y = _member()


class Direction(_Base):
    """
    Enumeration representing the direction in which to grow a line.

    Members
    -------
    INCREASING
        Growth in the positive direction (addition).
    DECREASING
        Growth in the negative direction (subtraction).
    """
    INCREASING = _member()
    DECREASING = _member()


class DebugLevel(_Bit):
    """
    Bitwise enumeration to represent the debug level.

    Members
    -------
    ON_CHANGE
        Output on every change.
    ON_UPDATE
        Output only when the maximum value is updated.
    """
    ON_CHANGE = _member()
    ON_UPDATE = _member()


class ValidityMeasure(_Base):
    """
    Enumeration to represent the measure of validity in images.

    Members
    -------
    LE

    EQ

    GE

    LT

    GT

    NE

    ONE_MINUS_LE

    ONE_MINUS_EQ

    ONE_MINUS_GE

    ONE_MINUS_LT

    ONE_MINUS_GT

    ONE_MINUS_NE

    """
    LE = _member()
    EQ = _member()
    GE = _member()
    LT = _member()
    GT = _member()
    NE = _member()
    ONE_MINUS_LE = _member()
    ONE_MINUS_EQ = _member()
    ONE_MINUS_GE = _member()
    ONE_MINUS_LT = _member()
    ONE_MINUS_GT = _member()
    ONE_MINUS_NE = _member()

    def to_func(self) -> _Func[[_Array, float, int], float]:
        """
        Convert the validity measure to an appropriate callable measure.

        Returns
        -------
        Callable[[ArrayLike, float, int], float]
            The measure implemented as a function.
        """
        if self == self.LE:
            def _inner(line: _Array, mean: float, length: int) -> float:
                return _valid(line <= mean) / length
        elif self == self.EQ:
            def _inner(line: _Array, mean: float, length: int) -> float:
                return _valid(line == mean) / length
        elif self == self.GE:
            def _inner(line: _Array, mean: float, length: int) -> float:
                return _valid(line >= mean) / length
        elif self == self.LT:
            def _inner(line: _Array, mean: float, length: int) -> float:
                return _valid(line < mean) / length
        elif self == self.GT:
            def _inner(line: _Array, mean: float, length: int) -> float:
                return _valid(line > mean) / length
        elif self == self.NE:
            def _inner(line: _Array, mean: float, length: int) -> float:
                return _valid(line != mean) / length
        elif self == self.ONE_MINUS_LE:
            le = self.LE.to_func()

            def _inner(line: _Array, mean: float, length: int) -> float:
                return 1 - le(line, mean, length)
        elif self == self.ONE_MINUS_EQ:
            eq = self.EQ.to_func()

            def _inner(line: _Array, mean: float, length: int) -> float:
                return 1 - eq(line, mean, length)
        elif self == self.ONE_MINUS_GE:
            ge = self.GE.to_func()

            def _inner(line: _Array, mean: float, length: int) -> float:
                return 1 - ge(line, mean, length)
        elif self == self.ONE_MINUS_LT:
            lt = self.LT.to_func()

            def _inner(line: _Array, mean: float, length: int) -> float:
                return 1 - lt(line, mean, length)
        elif self == self.ONE_MINUS_GT:
            gt = self.GT.to_func()

            def _inner(line: _Array, mean: float, length: int) -> float:
                return 1 - gt(line, mean, length)
        else:
            ne = self.NE.to_func()

            def _inner(line: _Array, mean: float, length: int) -> float:
                return 1 - ne(line, mean, length)
        return _inner
