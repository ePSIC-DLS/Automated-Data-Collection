import enum
import typing

import numpy as np

from modular_qt import utils as scans, cv_oop as sq


class BBox(enum.Enum):
    LEFT_TOP = enum.auto()
    LEFT_MIDDLE = enum.auto()
    LEFT_BOTTOM = enum.auto()

    MIDDLE_TOP = enum.auto()
    MIDDLE_MIDDLE = enum.auto()
    MIDDLE_BOTTOM = enum.auto()

    RIGHT_TOP = enum.auto()
    RIGHT_MIDDLE = enum.auto()
    RIGHT_BOTTOM = enum.auto()

    CENTRE = MIDDLE_MIDDLE


class ScanSite:
    """
    Class to represent a specific site (region) to scan in a given resolution.

    :var _tl tuple[int, int]: The top left corner.
    :var _br tuple[int, int]: The bottom right corner.
    :var _size int: The scan resolution – each 'image' would be _size x _size.
    """

    @property
    def region_size(self) -> tuple[int, int]:
        """
        The size of the captured region (in pixels, regardless of resolution)

        :return: The width and height of the area.
        """
        (left, top), (right, bottom) = self._tl, self._br
        return abs(right - left), abs(bottom - top)

    @property
    def scan_size(self) -> tuple[int, int]:
        """
        The resolution of the scan.

        :return: The square size of the image.
        """
        return self._size, self._size

    def __init__(self, top_left: tuple[int, int], bottom_right: tuple[int, int], resolution: int):
        (l_guess, t_guess), (r_guess, b_guess) = top_left, bottom_right
        l, r = min(l_guess, r_guess), max(l_guess, r_guess)
        t, b = min(t_guess, b_guess), max(t_guess, b_guess)
        self._tl = (l, t)
        self._br = (r, b)
        self._size = resolution

    def __repr__(self) -> str:
        return f"ScanSite({self._tl}, {self._br}, {self._size})"

    def extract_point(self, corner: BBox) -> tuple[int, int]:
        """
        Method to extract a specific point, captured by a bounding box.

        :param corner: The Bounding Box to extract.
        :return: Horizontal and vertical value.
        """
        le, mh, re = self._tl[0], (self._tl[0] + self._br[0]) // 2, self._br[0]
        te, mv, be = self._tl[1], (self._tl[1] + self._br[1]) // 2, self._br[1]
        if corner == BBox.LEFT_TOP:
            return le, te
        elif corner == BBox.LEFT_MIDDLE:
            return le, mv
        elif corner == BBox.LEFT_BOTTOM:
            return le, be
        elif corner == BBox.MIDDLE_TOP:
            return mh, te
        elif corner == BBox.MIDDLE_MIDDLE:
            return mh, mv
        elif corner == BBox.MIDDLE_BOTTOM:
            return mh, be
        elif corner == BBox.RIGHT_TOP:
            return re, te
        elif corner == BBox.RIGHT_MIDDLE:
            return re, mv
        elif corner == BBox.RIGHT_BOTTOM:
            return re, be

    def conv_to(self, new_size: int) -> "ScanSite":
        """
        Convert a site to a new resolution.

        :param new_size: The new resolution.
        :return: The site with modified co-ordinates. Region size will stay the same.
        """
        r = new_size / self._size
        (left, top), (right, bottom) = self._tl, self._br
        return ScanSite((int(left * r), int(top * r)), (int(right * r), int(bottom * r)), new_size)

    @classmethod
    def from_point(cls, point: tuple[int, int, BBox], size: tuple[int, int], resolution: int) -> "ScanSite":
        x, y, box = point
        if box == BBox.LEFT_TOP:
            left, top = x, y
            right, bottom = x + size[0], y + size[1]
        elif box == BBox.LEFT_MIDDLE:
            left, top = x, y - size[1] // 2
            right, bottom = x + size[0], y + size[1] // 2
        elif box == BBox.LEFT_BOTTOM:
            left, top = x, y - size[1]
            right, bottom = x + size[0], y
        elif box == BBox.MIDDLE_TOP:
            left, top = x - size[0] // 2, y
            right, bottom = x + size[0] // 2, y + size[1]
        elif box == BBox.MIDDLE_MIDDLE:
            left, top = x - size[0] // 2, y - size[1] // 2
            right, bottom = x + size[0] // 2, y + size[1] // 2
        elif box == BBox.MIDDLE_BOTTOM:
            left, top = x - size[0] // 2, y - size[1]
            right, bottom = x + size[0] // 2, y
        elif box == BBox.RIGHT_TOP:
            left, top = x - size[0], y
            right, bottom = x, y + size[1]
        elif box == BBox.RIGHT_MIDDLE:
            left, top = x - size[0], y - size[1] // 2
            right, bottom = x, y + size[1] // 2
        else:
            left, top = x - size[0], y - size[1]
            right, bottom = x, y
        return cls((left, top), (right, bottom), resolution)


class Cluster:

    def __init__(self, colour: sq.Colour, extremes: tuple[tuple[int, int], tuple[int, int]], in_resolution: int,
                 background: sq.Image):
        self._colour = colour
        self._bbox = ScanSite(*extremes, resolution=in_resolution)
        self._divisions: list[ScanSite] = []
        self._img = background

    def divide(self, indv_size: int, overlap: float):
        if not (0 <= overlap <= 1):
            raise ValueError("Expected overlap to be a percentage")
        if any(dim <= indv_size for dim in self._bbox.region_size):
            self._divisions.append(self._bbox)
            return
        overlap_amount = int(overlap * indv_size)
        for offset in ((0, 0), (overlap_amount, 0), (0, overlap_amount), (overlap_amount, overlap_amount)):
            self._divisions.extend(self._split(indv_size, offset))

    def tighten(self, match: float, *, strict=True):
        if not (0 <= match <= 1):
            raise ValueError("Expected overlap to be a percentage")
        for region in self._divisions[:]:
            w, h = region.region_size
            num_pixels = int(match * w * h) + int(not strict)
            square = self._img.extract_region(region.extract_point(BBox.LEFT_TOP),
                                              region.extract_point(BBox.RIGHT_BOTTOM))
            co_ordinates = square.search(self._colour)
            if co_ordinates.shape[0] < num_pixels:
                self._divisions.remove(region)

    def _split(self, size: int, offset: tuple[int, int]) -> typing.Iterator[ScanSite]:
        res = self._bbox.scan_size[0]
        min_x, min_y = self._bbox.extract_point(BBox.LEFT_TOP)
        max_x, max_y = self._bbox.extract_point(BBox.RIGHT_BOTTOM)
        curr_y = min_y + offset[1]
        while curr_y + size <= max_y:
            curr_x = min_x + offset[0]
            while curr_x + size <= max_x:
                yield ScanSite.from_point((curr_x, curr_y, BBox.LEFT_TOP), (size, size), res)
                curr_x += size
            curr_y += size
