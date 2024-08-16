import abc
import enum
import functools
import time
import typing
from typing import Tuple as _tuple
from .. import validation, load_settings

__all__ = [
    "ONLINE", "QD", "Key",
    "ScanType", "FullScan", "AreaScan",
    "TriggerSource", "TTLInput", "PixelClock", "TTLOutput",
    "AptKind", "ImagingMode", "Detector", "Lens", "Axis", "Driver", "TTLMode", "EdgeType"
]

R = typing.TypeVar("R")
Inst = typing.TypeVar("Inst")

configuration = load_settings("assets/config.json", microscope=validation.examples.any_bool,
                              engine_type=validation.examples.engine_type)
ONLINE = configuration["microscope"]
QD = configuration["engine_type"]


class Switch(typing.Generic[R]):
    """
    A context manager to represent a temporary change in a parameter's value.

    Generics
    --------
    R
        The value type.

    Attributes
    ----------
    _old: R
        The previous value to restore to.
    _switch: Callable[[R], None]
        The function to use to switch the value.
    _delay: float
        The delay in seconds between switching to normal control flow being resumed.
    """

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
    """
    Property-like decorator to automatically create a switch with each value.

    Generics
    --------
    Inst
        The instance bound to this property. Acts as 'self' for the bound getter.
    R
        The value data type.

    Attributes
    ----------
    _getter: Callable[[Inst], R]
        The wrapped function to get the data.
    _name: str
        The property name.
    _setter: Callable[[Inst, R], None] | None
        The wrapped function to set the data.
    _switch: Switch[R] | None
        The switcher used to control the value.
    _delay: float
        The delay in seconds between switching the value.
    """

    @property
    def delay(self) -> float:
        """
        Public access to the switch's delay.

        Returns
        -------
        float
            The delay for the switch.
        """
        return self._delay

    @delay.setter
    def delay(self, value: float):
        if value <= 0:
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
        """
        Publicly assign a setter.

        Parameters
        ----------
        fn: Callable[[Inst, R], None]
            The setter function.

        Returns
        -------
        Self
            The same instance.

        Raises
        ------
        ValueError
            If the setter already exists.
            If the setter has a different property name.
        """
        if self._setter is not None:
            raise ValueError(f"Property {self._name} already has a setter")
        elif fn.__name__ != self._name:
            raise ValueError(f"Expected setter to have name '{self._name}'")
        self._setter = fn
        return self

    def switch(self, to: R) -> Switch[R]:
        """
        Begin switching the value, then return the switch itself for use in a context manager.

        Note that this function shouldn't be called except in a context manager.

        Parameters
        ----------
        to: R
            The value to switch to.

        Returns
        -------
        Switch
            The switch of this object.
        """
        self._switch(to)
        return self._switch


class ScanType(abc.ABC):
    """
    Abstract Base Class for types of scans when considering QD scan engine.

    Abstract Methods
    ----------------
    rect

    Attributes
    ----------
    _size: tuple[int, int]
        The size of the scan.

    Raises
    ------
    ValueError
        If the scan size is not a natural number in any dimension.
    """

    @property
    def size(self) -> _tuple[int, int]:
        """
        Public access to the size of the full scan area.

        Returns
        -------
        tuple[int, int]
            The size of the scan.
        """
        return self._size

    def __init__(self, size: _tuple[int, int]):
        if any(s <= 0 for s in size):
            raise ValueError("Expected natural scan size")
        self._size = size

    @abc.abstractmethod
    def rect(self) -> _tuple[int, int, int, int]:
        """
        Method for determining scan rectangle based on QD specification.

        Returns
        -------
        tuple[int, int, int, int]
            A tuple representing starting x, ending x, starting y, and ending y.
        """
        pass


class FullScan(ScanType):
    """
    Concrete scan type for a full scan.
    """

    def rect(self) -> _tuple[int, int, int, int]:
        return 0, self._size[0], 0, self._size[1]


class AreaScan(ScanType):
    """
    Concrete scan type for a subregion scan.

    Attributes
    ----------
    _w: int
        The width of the subregion.
    _h: int
        The height of the subregion.
    _l: int
        The left edge of the subregion.
    _r: int
        The right edge of the subregion.
    _t: int
        The top edge of the subregion.
    _b: int
        The bottom edge of the subregion.

    Raises
    ------
    ValueError
        If the rectangle size is negative.
    """

    def __init__(self, full_size: _tuple[int, int], rect_size: _tuple[int, int], offset=(0, 0)):
        super().__init__(full_size)
        if any(r < 0 for r in rect_size):
            raise ValueError("Rect size must be positive")
        self._w, self._h = rect_size
        self._l, self._t = offset
        self._r, self._b = self._l + self._w, self._t + self._h

    def rect(self) -> _tuple[int, int, int, int]:
        return self._l, self._r, self._t, self._b

    @classmethod
    def from_corners(cls, full_size: _tuple[int, int], tl: _tuple[int, int], br: _tuple[int, int]) -> "AreaScan":
        """
        Alternative constructor to create a subregion scan from the known corner positions.

        Parameters
        ----------
        full_size: tuple[int, int]
            The full scan size.
        tl: tuple[int, int]
            The top-left corner.
        br: tuple[int, int]
            The bottom-right corner.

        Returns
        -------
        AreaScan
            The created subregion scan.
        """
        le, to = tl
        ri, bo = br
        return cls(full_size, (ri - le, bo - to), (le, to))


class TriggerSource(abc.ABC):
    """
    Abstract Base Class for a type of source for the connected triggers.
    """

    @abc.abstractmethod
    def value(self) -> int:
        """
        Method for determining source value.

        Returns
        -------
        int
            The calculated source value.
        """
        pass


class TTLInput(TriggerSource):
    """
    Concrete Trigger Source for TTL input.

    Attributes
    ----------
    _source: int
        The TTL input source. Must follow `ttl_input` validation.
    """

    def __init__(self, source: int):
        validation.examples.ttl_input.validate(source)
        self._source = source

    def value(self) -> int:
        return self._source


class PixelClock(TriggerSource):
    """
    Concrete Trigger Source for a pixel clock.

    Attributes
    ----------
    _fall: bool
        Whether the trigger is based on a falling edge.

    Parameters
    ----------
    edge: EdgeType
        The type of edge to tigger on.
    """

    def __init__(self, edge: "EdgeType"):
        edge_type.validate(edge)
        self._fall = edge == EdgeType.FALLING

    def value(self) -> int:
        return 6 + int(self._fall)


class TTLOutput(TriggerSource):
    """
    Concrete Trigger Source for TTL output.

    Attributes
    ----------
    _source: int
        The TTL output source. Must follow `ttl_output` validation.
    """

    def __init__(self, source: int):
        validation.examples.ttl_output.validate(source)
        self._source = source

    def value(self) -> int:
        return self._source + 8


class AptKind(enum.Enum):
    """
    Enumeration to represent the different aperture kinds.

    Members
    -------
    CL1
    CL2
    HC
    SA
    ENT
    HX
    BF
    """
    CL1 = 0
    CL2 = 1
    HC = 3
    SA = 4
    ENT = 5
    HX = 6
    BF = 7


class ImagingMode(enum.Enum):
    """
    Enumeration to represent the different imaging modes.

    Members
    -------
    TEM
    STEM
    """
    TEM = 0
    STEM = 1


class Detector(enum.Enum):
    """
    Enumeration to represent the different detectors.

    Members
    -------
    ADF1
    ADF2
    BF
    ABF
    """
    ADF1 = 10
    ADF2 = 14
    BF = 11
    ABF = 18


class Lens(enum.Enum):
    """
    Enumeration to represent the different lens kinds.

    Members
    -------
    CL1
    CL2
    CL3
    CM
    OL_COARSE
    OL_FINE
    OM1
    OM2
    IL1
    IL2
    IL3
    IL4
    PL1
    PL2
    PL3
    FL_COARSE
    FL_FINE
    """
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
    # FL_RATIO = 21


class Axis(enum.Enum):
    """
    Enumeration to represent the different axes that the stage can move in.

    Members
    -------
    X
    Y
    Z
    """
    X = enum.auto()
    Y = enum.auto()
    Z = enum.auto()


class Driver(enum.Enum):
    """
    Enumeration to represent the different stage drivers.

    Members
    -------
    MOTOR
    PIEZO
    """
    MOTOR = 0
    PIEZO = 1


class TTLMode(enum.Enum):
    """
    Enumeration to represent the different modes for a TTL connection.

    Members
    -------
    OFF
    ON
    SOURCE
    SOURCE_TIMED
    SOURCE_TIMED_DELAY
    PULSE_TRAIN
    SOURCE_TRAIN
    """
    OFF = 0
    ON = 1
    SOURCE = 2
    SOURCE_TIMED = 3
    SOURCE_TIMED_DELAY = 4
    PULSE_TRAIN = 7
    SOURCE_TRAIN = 8


class EdgeType(enum.Enum):
    """
    Enumeration to represent the different edges of a clock signal.

    Members
    -------
    RISING
    FALLING
    """
    RISING = enum.auto()
    FALLING = enum.auto()


edge_type = validation.Pipeline.enum(EdgeType)
