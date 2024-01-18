"""
Utility functions and classes
"""
from __future__ import annotations

import enum
import functools
import typing
from tkinter import DoubleVar as _Float, IntVar as _Int
from tkinter import messagebox as mtk
import numpy as np
import h5py

T = typing.TypeVar("T", covariant=True)
R = typing.TypeVar("R")


def check_controls(index: int) -> typing.Callable[..., R]:
    """
    Decorator wrapper to check control values of the GUI, then switch to a specific canvas
    :param index: The canvas **index** to switch to
    :return: The decorator
    """

    def wrapper(f: typing.Callable[..., R]) -> typing.Callable[..., R]:
        """
        Decorator to perform the role intended by the wrapper
        :param f: The function to decorate
        :return: The decorated function
        """

        @functools.wraps(f)
        def _inside(*args, **kwargs) -> R:
            self = args[0]
            args = args[1:]
            had_to = 0
            invalid = []
            for spin, name in zip(self.get_controls(), ("Low Thresh", "High Thresh", "Epsilon", "Min Samples")):
                if not spin.validate():
                    had_to += 1
                    invalid.append(repr(name))
            if had_to == 0:
                self.switch_to_page(index)
                self.go()
                return f(self, *args, **kwargs)
            else:
                mtk.showwarning("Value Warning", f"Spinbox(es) {', '.join(invalid)} are out of bounds")

        return _inside

    return wrapper


def singleton(c: typing.Type[R]) -> typing.Callable[..., R]:
    """
    Decorator to create a singleton
    :param c: The type to make a singleton
    :return: The singleton constructor
    """
    instance: typing.Optional[R] = None

    @functools.wraps(c)
    def _inner(*args, forget=False, **kwargs) -> R:
        nonlocal instance
        if instance is None or forget:
            instance = c(*args, **kwargs)
        return instance

    return _inner


def tk_singleton(c: typing.Type[R]) -> typing.Callable[..., R]:
    """
    Decorator to create a singleton of a tkinter app – will lift the tkinter application when called (and not forgotten)
    :param c: The type to make a singleton
    :return: The singleton constructor
    """
    instance: typing.Optional[R] = None

    @functools.wraps(c)
    def _inner(*args, forget=False, **kwargs) -> R:
        nonlocal instance
        if instance is None or forget:
            instance = c(*args, **kwargs)
        else:
            instance.lift()
        return instance

    return _inner


def save_arr_to_file(arr: np.ndarray, path: str, tl: tuple[int, int], br: tuple[int, int]):
    with h5py.File(path, "w") as out:
        dset = out.create_dataset("captured square", data=arr)
        dset.attrs["top left"] = tl
        dset.attrs["bottom right"] = br


class LazyLinSpace:
    """
    Non-evaluated version of a Linspace from numpy

    :var _start float: The starting value
    :var _stop float: The ending value
    :var _begin bool: Whether to include the starting value
    :var _end bool: Whether to include the ending value
     """

    @property
    def bounds(self) -> tuple[float, float]:
        """
        The starting and ending points of the linspace
        :return: start, stop
        """
        return self._start, self._stop

    @property
    def do_start(self) -> bool:
        """
        Public access for the inclusions (at the start)
        :return: Whether to include the starting value
        """
        return self._begin

    @property
    def do_end(self) -> bool:
        """
        Public access for the inclusions (at the end)
        :return: Whether to include the ending value
        """
        return self._end

    def __init__(self, start: float, stop: float, *, begin=True, end=True):
        self._start = start
        self._stop = stop
        self._begin = begin
        self._end = end

    def __contains__(self, item: float) -> bool:
        if self._begin and self._end:
            return self._start <= item <= self._stop
        elif self._begin:
            return self._start <= item < self._stop
        elif self._end:
            return self._start < item <= self._stop
        return self._start < item < self._stop


class DynamicLazyLinSpace(LazyLinSpace):
    """
    Special form to have a Linspace with a dynamic start and end

    :var _start_point tkinter.IntVar | tkinter.DoubleVar: The starting variable
    :var _end_point tkinter.IntVar | tkinter.DoubleVar: The ending variable
    """

    @property
    def _start(self) -> float:
        return float(self._start_point.get())

    @_start.setter
    def _start(self, value: float):
        self._start_point.set(value)

    @property
    def _stop(self) -> float:
        return float(self._end_point.get())

    @_stop.setter
    def _stop(self, value: float):
        self._end_point.set(value)

    def __init__(self, start: typing.Union[_Float, _Int], stop: typing.Union[_Float, _Int], *, begin=True, end=True):
        self._start_point = start
        self._end_point = stop
        super().__init__(start.get(), stop.get(), begin=begin, end=end)


@typing.runtime_checkable
class SupportsContains(typing.Protocol[T]):
    """
    Protocol to check if something supports the '__contains__' magic method
    """

    def __contains__(self, item: T) -> bool:
        pass


class BBox(enum.Flag):
    """
    Bounding box enum designed to represent the bounds of an object

    :cvar LEFT:
    :cvar RIGHT:
    :cvar TOP:
    :cvar BOTTOM:
    """
    LEFT = 1
    RIGHT = 2
    TOP = 4
    BOTTOM = 8


class ScanSite:
    """
    Class to represent a specific site to scan on the microscope

    :var _survey_tl numpy.ndarray: The top left corner.
    :var _survey_br numpy.ndarray: The bottom right corner.
    :var _survey_size int: The resolution of the scan.
    """

    def __init__(self, tl: tuple[int, int], br: tuple[int, int], size: int):
        self._survey_tl = np.array(tl)
        self._survey_br = np.array(br)
        self._survey_size = size

    def __str__(self) -> str:
        return f"BBox: {self._survey_tl} -> {self._survey_br} @ {self._survey_size}"

    def __hash__(self) -> int:
        return hash((self.corner(BBox.LEFT | BBox.TOP), self.corner(BBox.RIGHT | BBox.BOTTOM), self._survey_size))

    def corner(self, corner: BBox) -> tuple[int, int]:
        """
        Find a corner of the bounding box
        :param corner: The corner to return
        :return: The co-ordinates of the corner
        :raise ValueError: If the specified corner doesn't actually make up a corner
        """
        x_val = y_val = -1
        if corner & BBox.LEFT:
            x_val = self._survey_tl[1]
        if corner & BBox.RIGHT:
            if x_val != -1:
                raise ValueError("Cannot gather both left and right")
            x_val = self._survey_br[1]
        if corner & BBox.TOP:
            y_val = self._survey_tl[0]
        if corner & BBox.BOTTOM:
            if y_val != -1:
                raise ValueError("Cannot gather both top and bottom")
            y_val = self._survey_br[0]
        if x_val == -1 or y_val == -1:
            raise ValueError("Must gather an x-value and a y-value")
        return int(y_val), int(x_val)

    def conv_to(self, new_size: int) -> "ScanSite":
        """
        Returns a new site, scaled to the relevant size
        :param new_size: The size to scale to
        :return: The new site
        """
        ratio = new_size / self._survey_size
        new_tl = self._survey_tl * ratio
        new_br = self._survey_br * ratio
        return ScanSite((int(new_tl[0]), int(new_tl[1])), (int(new_br[0]), int(new_br[1])), new_size)


class EventProxy:

    def __init__(self, **kwargs):
        self.x = kwargs.get("x")
        self.y = kwargs.get("y")
        self.focus = kwargs.get("focus")
        self.set_from_callback = kwargs.get("set_from_callback")
        self.colour = kwargs.get("colour")
