"""
A module for Regions Of Interest (ROIs) in rectangular, elliptical, and polygonal shape
"""
from __future__ import annotations
import abc
import operator
import typing

import cv2
import numpy as np


class ROI(abc.ABC):
    """
    An ABC to represent a ROI in its base form

    :var _data numpy.ndarray | None: The data stored in the ROI
    """

    @property
    @abc.abstractmethod
    def surface(self) -> np.ndarray:
        """
        Public getter for the shape of the ROI as a ndarray
        :return: An array with 1 being the shape of the ROI, and 0 being dead space
        """
        pass

    @property
    @abc.abstractmethod
    def centre(self) -> tuple[int, int]:
        """
        Public getter for the centre point of the ROI, expressed as two integers
        :return: The x,y co-ordinate for the centre
        """
        pass

    @property
    def data(self) -> np.ndarray | None:
        """
        Public getter for the data of the ROI
        :return: The _data instance variable
        """
        if self._data is None:
            return None
        return self._data.copy()

    def __init__(self, data: np.ndarray = None):
        """
        Sets up the base ROI attributes
        :param data: The data to use
        """
        self._data = data

    @abc.abstractmethod
    def apply(self, image: np.ndarray) -> typing.Self:
        """
        Applies the ROI to a specific image pattern
        :param image: The data of the image
        :return: A new ROI, with its data being the image data
        """
        pass


class Rect(ROI):
    """
    A rectangular region of interest

    :var _size tuple[int,int]: The size of the rect in terms of width, height
    """

    @property
    def centre(self) -> tuple[int, int]:
        return self._size[0] // 2, self._size[1] // 2

    @property
    def surface(self) -> np.ndarray:
        return cv2.rectangle(np.zeros((self._size[1], self._size[0]), dtype=np.uint8), (0, 0), self._size,
                             (1, 1, 1), -1)

    @property
    def size(self) -> tuple[int, int]:
        """
        Public getter for the size of the ROI
        :return: The width and height of the Rect
        """
        return self._size

    def __init__(self, width: int, height: int, *, on: np.ndarray = None):
        """
        Sets up rectangular ROI
        :param width: The x-axis size
        :param height: The y-axis size
        :param on: The image to apply this data to
        """
        super().__init__(on)
        self._size = width, height

    def apply(self, image: np.ndarray) -> typing.Self:
        return Rect(*self._size, on=image)

    @classmethod
    def square(cls, size: int, *, on: np.ndarray = None) -> typing.Self:
        """
        Alternative constructor for creating a square ROI
        :param size: The width of the square (will also be the height)
        :param on: The image data to apply this ROI to
        :return: The Rect formed
        """
        return cls(size, size, on=on)


class Ellipse(ROI):
    """
    An elliptical Region of Interest

    :var _r tuple[int,int]: The radius of the ellipse
    """

    @property
    def centre(self) -> tuple[int, int]:
        return self._r

    @property
    def surface(self) -> np.ndarray:
        return cv2.ellipse(np.zeros((self._r[1] * 2, self._r[0] * 2), dtype=np.uint8), self._r, self._r,
                           0, 0, 360, (1, 1, 1), -1)

    @property
    def radius(self) -> tuple[int, int]:
        """
        Public getter for the ellipse's radius
        :return: The _r instance variable
        """
        return self._r

    def __init__(self, radius: tuple[int, int], *, on: np.ndarray = None):
        """
        Sets up elliptical ROI
        :param radius: The radius in both x and y directions
        :param on: The image to apply this data to
        """
        super().__init__(on)
        self._r = radius

    def apply(self, image: np.ndarray) -> typing.Self:
        return Ellipse(self._r, on=image)


class Polygon(ROI):
    """
    A Region of Interest mapped out as any polygon.
    Can be regular, irregular, concave or convex.

    :var _offsets tuple[tuple[int,int],...]: The relative offsets of each point from the centre
    :var _centre tuple[int,int]: A singular point representing the centre
    :var _w int: The overall width of the polygon
    :var _h int: The overall height of the polygon
    """

    @property
    def centre(self) -> tuple[int, int]:
        return self._centre

    @property
    def surface(self) -> np.ndarray:
        return cv2.polylines(np.zeros((self._h, self._w), dtype=np.uint8), self._points, True,
                             (1, 1, 1), -1)

    @property
    def size(self) -> tuple[int, int]:
        """
        Public getter for the size of the polygon
        :return: The width and height of the ROI
        """
        return self._w, self._h

    def __init__(self, centre: tuple[int, int], *offsets: tuple[int, int], on: np.ndarray = None):
        """
        Sets up the polygon
        :param centre: The centre point
        :param offsets: The offsets from the centre
        :param on: The image to apply this data to
        :raise ValueError: If there are less than 3 offsets
        """
        if len(offsets) < 3:
            raise ValueError("Expected at least 3 points to form a polygon")

        super().__init__(on)
        if centre == (0, 0):
            self._points = tuple(np.array(p) for p in offsets)
        else:
            self._points = tuple(map(lambda tup: np.array(tuple(map(operator.add, centre, tup))), offsets))
        self._offsets = offsets
        self._centre = centre
        self._w = Polygon.delta_axis(operator.itemgetter(0), self._points)
        self._h = Polygon.delta_axis(operator.itemgetter(1), self._points)

    def apply(self, image: np.ndarray) -> typing.Self:
        return Polygon(self._centre, *self._offsets, on=image)

    def points(self) -> typing.Generator[np.ndarray, None, None]:
        """
        Generator for each point of the polygon (to save memory)
        :return: Yields each point in turn
        """
        for arr in self._points:
            yield arr.copy()

    def find_offsets(self) -> typing.Generator[tuple[int, int], None, None]:
        """
        Generator for each offset from the centre (useful for rotations)
        :return: Yields each offset in turn
        """
        yield from self._offsets

    @staticmethod
    def delta_axis(access: operator.itemgetter, points: tuple[np.ndarray[int], ...]) -> int:
        """
        Finds the difference between the smallest and largest values along an axis
        :param access: The accessor for the axis
        :param points: The series of points to perform axes measurements on
        :return: The range of the axis
        """
        return access(max(points, key=access)) - access(min(points, key=access))

