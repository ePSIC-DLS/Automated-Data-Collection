import typing
from typing import Tuple as _tuple

import numpy as np

from . import _image as imgs
from ._enums import *


class Line:
    """
    Class to represent a line overlaid on an image.

    Attributes
    ----------
    _start: ndarray[int, (2)]
        The starting line co-ordinate. Note that it is a ndarray due to line operations requiring a vector.
    _end: ndarray[int, (2)]
        The ending line co-ordinate. Much like `_start`, it is an array for identical reasons.
    _valid: Callable[[ArrayLike, float, int], float]
        The validity function.
    """

    def __init__(self, xy1: _tuple[int, int], xy2: _tuple[int, int], validity_measure: ValidityMeasure):
        self._start = np.array(xy1)
        self._end = np.array(xy2)
        self._valid = validity_measure.to_func()

    def slope(self) -> float:
        """
        Calculate the line's gradient assuming the equation `y = mx + c`. This calculates `m = (y1 - y0)/(x1 - x0)`.

        Returns
        -------
        float
            The slope of rise over run.
        """
        if self._end[1] == self._start[1]:
            return np.inf
        return np.divide.reduce(self._end[::-1] - self._start[::-1])

    def intercept(self, with_: "Line") -> float:
        """
        Calculate the intercept angle between two lines.

        Parameters
        ----------
        with_: Line
            The colliding line.

        Returns
        -------
        float
            The angle of intercept in degrees.
        """
        m2 = with_.slope()
        m1 = self.slope()
        if np.isinf(m1) or np.isinf(m2):
            return np.rad2deg(np.arctan(0))
        denom = (1 + m1 * m2)
        if denom == 0:
            return 90
        tan = (m2 - m1) / denom
        return np.rad2deg(np.arctan(tan))

    def length(self) -> float:
        """
        The diagonal length of the line.

        Returns
        -------
        float
            The line's length.
        """
        return np.linalg.norm(self._end - self._start)

    def expand(self, size: int = None) -> _tuple[np.ndarray, np.ndarray]:
        """
        Expands the line across a square of known size.

        Parameters
        ----------
        size: int | None
            The size of the square to expand to.
            If not given, will expand based on the largest dimension of the line.

        Returns
        -------
        tuple[ndarray[int, x], ndarray[int, x]]
            The lines full co-ordinates, expressed in numpy advanced indexing format.
        """
        if size is None:
            size = max(max(self._start), max(self._end))

        def _line() -> _tuple[np.ndarray, np.ndarray]:
            xy1, xy2 = self._start, self._end
            x_diff, y_diff = xy2[0] - xy1[0], xy2[1] - xy1[1]
            x_sign = np.sign(x_diff)
            y_sign = np.sign(y_diff)
            if x_diff == 0:
                return np.arange(xy1[1], xy2[1], y_sign), np.array([xy1[0]] * np.abs(y_diff))
            elif y_diff == 0:
                return np.array([xy1[1]] * np.abs(x_diff)), np.arange(xy1[0], xy2[0], x_sign)
            if np.abs(x_diff) > np.abs(y_diff):
                x_diff = np.abs(x_diff)
                yx = xy1[1] * x_diff + x_diff // 2
                first = np.arange(xy1[0], xy2[0], x_sign)
                second = np.arange(yx, yx + x_diff * y_diff, y_diff) // x_diff
            else:
                y_diff = np.abs(y_diff)
                xy = xy1[0] * y_diff + y_diff // 2
                first = np.arange(xy, xy + y_diff * x_diff, x_diff) // y_diff
                second = np.arange(xy1[1], xy2[1], y_sign)
            return second, first

        ys, xs = _line()
        all_points = np.zeros((ys.shape[0], 2), dtype=np.int_)
        all_points[:, 0] = ys
        all_points[:, 1] = xs
        y_mask = np.where((ys >= 0) & (ys < size), 1, 0)
        x_mask = np.where((xs >= 0) & (xs < size), 1, 0)
        p_mask = y_mask & x_mask
        all_points = all_points[p_mask.astype(np.bool_)]
        return all_points[:, 0], all_points[:, 1]

    def validity(self, template: imgs.GreyImage) -> float:
        """
        Calculate the validity of this line based on a template image.

        This measure how well the line fits the template image by measuring standard deviation under the line.

        Parameters
        ----------
        template: GreyImage
            The image to measure against.

        Returns
        -------
        float
            The validity measure acting on the standard deviation of the line.
            Note it takes the line's standard deviation is compared against the normalised intensities (|L - μ| for
            line L and mean μ).

            If this value is -1, then the validity cannot be measured.

        Raises
        ------
        TypeError
            If the image is not square.
        """
        w, h = template.size
        if w != h:
            raise TypeError("Expected square image")
        grey = template.data()
        ys, xs = self.expand(w)
        num_points = ys.shape[0] or xs.shape[0]
        if num_points == 0:
            return -1
        all_points = np.zeros((num_points, 2), dtype=np.int_)
        all_points[:, 0] = ys
        all_points[:, 1] = xs
        length = np.linalg.norm(all_points[-1] - all_points[0])
        if length == 0:
            return -1
        snippet = grey[ys, xs]
        return self._valid(np.abs(snippet - np.mean(snippet)), np.std(snippet), num_points)

    @classmethod
    def from_angle(cls, start: _tuple[int, int], length: int, angle: int, axis: Axis, growth: Direction,
                   validity: ValidityMeasure) -> "Line":
        """
        Alternate constructor to construct a line from an angle and a length.

        Parameters
        ----------
        start: tuple[int, int]
            The starting co-ordinate of the line.
        length: int
            The magnitude of the line.
        angle: int
            The angle the line should make with the x and y axes.
        axis: Axis
            What axis to grow the line in.
        growth: Direction
            How to grow the line. An INCREASING direction means it grows down or right; whereas a DECREASING direction
            means it grows up or left.
        validity: ValidityMeasure
            The measure of validity for the line.

        Returns
        -------
        Line
            The constructed line.
        """
        rad = np.deg2rad(angle)
        cmps = np.cos(rad), np.sin(rad)
        if axis == Axis.X:
            cmps = cmps[::-1]
        x = int(length * cmps[0])
        y = int(length * cmps[1])
        xy1 = start

        def _form_end() -> _tuple[int, int]:
            if growth == Direction.DECREASING:
                return xy1[0] - x, xy1[1] - y
            return xy1[0] + x, xy1[1] + y

        def _end_growable() -> bool:
            if growth == Direction.DECREASING:
                return all(e > 0 for e in end)
            return all(e < length for e in end)

        end = _form_end()
        while _end_growable():
            xy1 = end
            end = _form_end()
        return Line(start, end, validity)


class Grid:
    """
    Manager class for a series of lines with x-angle deviations and y-angle deviations.

    Attributes
    ----------
    _size: int
        The size of the grid.
    _pitch: tuple[int, int]
        The distance between the lines from the x-axis and the y-axis.
    _validity: ValidityMeasure
        The validity measure to use for each line.
    """

    @property
    def lines(self) -> typing.Iterator[Line]:
        """
        Public access to all lines the grid contains. Note that this property is a generator.

        Yields
        ------
        Line
            The x-axis lines, then the y-axis lines.
        """
        yield from self._x_lines
        yield from self._y_lines

    @property
    def pairs(self) -> typing.Iterator[_tuple[Line, Line]]:
        """
        Public access to all pairs of lines the grid contains. Note that this property is a generator.

        Yields
        ------
        tuple[Line, Line]
            The xy-axis line pairs.
        """
        yield from zip(self._x_lines, self._y_lines)

    def __init__(self, size: int, angle: _tuple[int, int], pitch: _tuple[int, int], offset: _tuple[int, int],
                 line_validity: ValidityMeasure):
        self._size = size
        self._pitch = pitch
        self._validity = line_validity
        self._x_lines = self._populate(angle[0], pitch[0], offset[0], False)
        self._y_lines = self._populate(angle[1], pitch[1], offset[1], True)

    def _populate(self, angle: int, pitch: int, offset: int, row: bool) -> _tuple[Line, ...]:
        lines = []
        final = 0
        axis = Axis.Y if row else Axis.X
        for v in range(offset, self._size, pitch):
            if v < 0:
                continue
            if angle < 0:
                origin = (self._size - 1, v)
                growth = Direction.DECREASING
            else:
                origin = (0, v)
                growth = Direction.INCREASING
            if not row:
                origin = origin[::-1]
            line = Line.from_angle(origin, self._size, angle, axis, growth, self._validity)
            y_points, x_points = line.expand(self._size)
            lines.append(line)
            d_points = y_points if row else x_points
            if not final:
                final = d_points[-1]
        for v in range(final, offset, -pitch):
            if angle < 0:
                origin = (0, v)
                growth = Direction.INCREASING
            else:
                origin = (self._size - 1, v)
                growth = Direction.DECREASING
            if not row:
                origin = origin[::-1]
            line = Line.from_angle(origin, self._size, angle, axis, growth, self._validity)
            lines.append(line)
        return tuple(lines)

    def validity(self, template: imgs.GreyImage, direction: Axis) -> float:
        """
        Measure the validity of the whole grid. Note this is the average of the line validity.

        Parameters
        ----------
        template: GreyImage
            The template to measure the validity of.
        direction: Axis
            The axis to measure validity in.

        Returns
        -------
        float
            The average of all line validities in the specified direction. Any validity that is -1 (the invalid value)
            is discarded.
        """
        lines = self._x_lines if direction == Axis.X else self._y_lines
        return np.mean([validity for line in lines if (validity := line.validity(template)) != -1])

    def length(self) -> _tuple[int, int]:
        """
        Find the gap between lines.

        Returns
        -------
        tuple[int, int]
            The spacing between adjacent lines in each axis.
        """
        return self._pitch

    def angle(self) -> float:
        """
        Calculate the average interception angle of the grid. For a perfectly square grid this will return 90.

        Returns
        -------
        float
            The average interception angle of all lines in degrees.
        """
        return np.mean([abs(line1.intercept(line2)) for line1, line2 in self.pairs])

    def mask(self) -> np.ndarray:
        """
        Convert this grid to a masked array.

        Returns
        -------
        ndarray[bool_, (size, size)]
            The mask representing the grid. Note that the co-ordinates of each line are the true values in the array.
        """
        blank = np.zeros((self._size,) * 2, dtype=np.bool_)
        for line in self.lines:
            blank[line.expand(self._size)] = True
        return blank

    def to_matrix(self) -> np.ndarray:
        """
        Convert this grid to an affine transformation matrix.

        Returns
        -------
        ndarray[float_, (3,3)]
            The matrix that can skew and rotate this grid to make it perfect.
        """
        theta = np.deg2rad(self.angle())
        cos = np.cos(theta)
        sin = np.sin(theta)
        arr_rot = np.eye(3) * cos
        arr_rot[0, 1] = -sin
        arr_rot[1, 0] = sin
        arr_rot[2, 2] = 1
        arr_trans = np.eye(3)
        arr_trans[0, 1] = self._pitch[0]
        arr_trans[1, 0] = self._pitch[1]
        return arr_rot @ arr_trans
