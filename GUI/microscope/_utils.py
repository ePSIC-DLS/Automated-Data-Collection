import abc
import enum
import functools
import time
import typing
from typing import Tuple as _tuple

__all__ = ["ONLINE", "Key", "AptKind", "ImagingMode", "Detector", "Lens", "Axis", "Driver", "ScanType", "FullScan",
           "AreaScan"]

R = typing.TypeVar("R")
Inst = typing.TypeVar("Inst")

ONLINE = False


class Switch(typing.Generic[R]):

    def __init__(self, old: R, switch: typing.Callable[[R], None], delay: float):
        self._old = old
        self._switch = switch
        self._delay = delay

    def __call__(self, new: R):
        self._switch(new)
        if self._delay:
            time.sleep(self._delay)

    def __enter__(self) -> None:
        return

    def __exit__(self, exc_type: typing.Type[Exception], exc_val: Exception, exc_tb):
        self(self._old)


class Key(typing.Generic[Inst, R]):

    @property
    def delay(self) -> float:
        return self._delay

    @delay.setter
    def delay(self, value: float):
        if value < 0:
            raise ValueError("Delay must be positive")
        elif self._delay:
            raise ValueError("Already set delay")
        self._delay = value

    def __init__(self, getter: typing.Callable[[Inst], R]):
        self._getter = getter
        self._name = getter.__name__
        self._setter: typing.Optional[typing.Callable[[Inst, R], None]] = None
        self._switch: typing.Optional[Switch[R]] = None
        self._delay = 0.0

    def __get__(self, instance: Inst, owner: typing.Type[Inst]) -> R:
        r_val = self._getter(instance)
        if self._delay:
            time.sleep(self._delay)
        if self._setter is not None:
            self._switch = Switch(r_val, functools.partial(self._setter, instance), self._delay)
        return r_val

    def __set__(self, instance: Inst, value: R) -> None:
        if self._setter is None:
            raise ValueError(f"Property {self._name} is read-only")
        self._setter(instance, value)
        if self._delay:
            time.sleep(self._delay)
        self._switch = Switch(value, functools.partial(self._setter, instance), self._delay)

    def setter(self, fn: typing.Callable[[Inst, R], None]) -> "Key":
        if self._setter is not None:
            raise ValueError(f"Property {self._name} already has a setter")
        elif fn.__name__ != self._name:
            raise ValueError(f"Expected setter to have name '{self._name}'")
        self._setter = fn
        return self

    def switch(self, to: R) -> Switch[R]:
        self._switch(to)
        return self._switch


class ScanType(abc.ABC):

    @property
    def size(self) -> _tuple[int, int]:
        return self._size

    def __init__(self, size: _tuple[int, int]):
        if any(s <= 0 for s in size):
            raise ValueError("Expected natural scan size")
        self._size = size

    @abc.abstractmethod
    def rect(self) -> _tuple[int, int, int, int]:
        pass


class FullScan(ScanType):

    def rect(self) -> _tuple[int, int, int, int]:
        return 0, self._size[0] - 1, 0, self._size[1] - 1


class AreaScan(ScanType):

    def __init__(self, full_size: _tuple[int, int], rect_size: _tuple[int, int], offset=(0, 0)):
        super().__init__(full_size)
        if any(r < 0 for r in rect_size):
            raise ValueError("Rect size must be positive")
        self._w, self._h = rect_size
        self._l, self._t = offset
        self._r, self._b = self._l + self._w, self._t + self._h

    def rect(self) -> _tuple[int, int, int, int]:
        return self._l, self._r - 1, self._t, self._b - 1

    @classmethod
    def from_corners(cls, full_size: _tuple[int, int], tl: _tuple[int, int], br: _tuple[int, int]) -> "AreaScan":
        le, to = tl
        ri, bo = br
        return cls(full_size, (ri - le, bo - to), (le, to))


class AptKind(enum.Enum):
    CL1 = 0
    CL2 = 1
    HC = 3
    SA = 4
    ENT = 5
    HX = 6
    BF = 7


class ImagingMode(enum.Enum):
    TEM = 0
    STEM = 1


class Detector(enum.Enum):
    ADF1 = 10
    ADF2 = 14
    BF = 11
    ABF = 18


class Lens(enum.Enum):
    CL1 = 0
    CL2 = 1
    CL3 = 2
    CM = 3
    OL_COARSE = 6
    OL_FINE = 7
    OM1 = 8
    OM2 = 9
    IL1 = 10
    IL2 = 11
    IL3 = 12
    IL4 = 13
    PL1 = 14
    PL2 = 15
    PL3 = 16
    FL_COARSE = 19
    FL_FINE = 20
    FL_RATIO = 21


class Axis(enum.Enum):
    X = enum.auto()
    Y = enum.auto()
    Z = enum.auto()


class Driver(enum.Enum):
    MOTOR = 0
    PIEZO = 1
