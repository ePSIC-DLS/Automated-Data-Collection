import abc
import operator
import typing
from typing import List as _list, Optional as _None, Tuple as _tuple
from ._enums import *
from ...images import AABBCorner

import numpy as np
import numpy.typing as npt

__all__ = ["Pattern", "Point", "Stroke", "Design", "Raster", "Snake", "Spiral", "Grid", "Random"]


def _line(xy1: _tuple[int, int], xy2: _tuple[int, int], endpoint=False) -> _tuple[np.ndarray, np.ndarray]:
    x_diff, y_diff = xy2[0] - xy1[0], xy2[1] - xy1[1]
    x_sign = np.sign(x_diff)
    y_sign = np.sign(y_diff)
    if x_diff == 0:
        return (np.arange(xy1[1], xy2[1] + (int(endpoint) * y_sign), y_sign),
                np.array([xy1[0]] * np.abs(y_diff + (int(endpoint) * y_sign))))
    elif y_diff == 0:
        return (np.array([xy1[1]] * np.abs(x_diff + (int(endpoint) * x_sign))),
                np.arange(xy1[0], xy2[0] + (int(endpoint) * x_sign), x_sign))
    if np.abs(x_diff) > np.abs(y_diff):
        x_diff = np.abs(x_diff)
        yx = xy1[1] * x_diff + x_diff // 2
        first = np.arange(xy1[0], xy2[0] + (int(endpoint) * x_sign), x_sign)
        second = np.arange(yx, yx + (x_diff + int(endpoint)) * y_diff, y_diff) // x_diff
    else:
        y_diff = np.abs(y_diff)
        xy = xy1[0] * y_diff + y_diff // 2
        first = np.arange(xy, xy + (y_diff + int(endpoint)) * x_diff, x_diff) // y_diff
        second = np.arange(xy1[1], xy2[1] + (int(endpoint) * y_sign), y_sign)
    return second, first


class Pattern(abc.ABC):

    @abc.abstractmethod
    def __contains__(self, other: _tuple[int, int]) -> bool:
        pass

    @abc.abstractmethod
    def __repr__(self) -> str:
        pass

    @abc.abstractmethod
    def decode(self) -> npt.NDArray[np.int_]:
        pass

    @abc.abstractmethod
    def index(self, elem: _tuple[int, int]) -> int:
        pass


class Point(Pattern):

    def __init__(self, pos: _tuple[int, int]):
        self._point = list(pos)

    def __contains__(self, other: _tuple[int, int]) -> bool:
        return all(sc == oc for sc, oc in zip(self._point, other))

    def __repr__(self) -> str:
        return f"<{', '.join(map(str, self._point))}>"

    def decode(self) -> npt.NDArray[np.int_]:
        return np.array([self._point], dtype=np.int_)

    def index(self, elem: _tuple[int, int]) -> int:
        return 0


class Stroke(Pattern):

    def __init__(self, start: _tuple[int, int], end: _tuple[int, int], endpoint=False):
        self._start = start
        self._end = end
        self._inclusive = endpoint

    def __repr__(self) -> str:
        return f"{Point(self._start)!r} -> {Point(self._end)!r} ({'I' if self._inclusive else 'E'})"

    def __contains__(self, other: _tuple[int, int]) -> bool:
        all_points = self.decode()
        xs, ys = all_points[:, 0], all_points[:, 1]
        valid_x = xs == other[0]
        valid_y = ys == other[1]
        valid_mask = valid_x & valid_y
        return np.any(valid_mask)

    def decode(self) -> npt.NDArray[np.int_]:
        return np.c_[_line(self._start, self._end, self._inclusive)][:, ::-1].astype(np.int_)

    def index(self, elem: _tuple[int, int]) -> int:
        all_points = self.decode()
        xs, ys = all_points[:, 0], all_points[:, 1]
        valid_x = xs == elem[0]
        valid_y = ys == elem[1]
        valid_mask = valid_x & valid_y
        for i, flag in enumerate(valid_mask):
            if flag:
                return i

    def reverse(self) -> "Stroke":
        return Stroke(self._end, self._start)


P = typing.TypeVar("P", bound=Pattern)


class Design(abc.ABC, typing.Generic[P]):

    def __init__(self, size: _tuple[int, int], coverage: _tuple[float, float]):
        self._size = size
        self._cov = coverage

    def __getitem__(self, item: str):
        if item == "coverage":
            return self._cov
        raise KeyError(f"{type(self).__name__} has no parameter {item!r}")

    @abc.abstractmethod
    def draw(self) -> np.ndarray:
        pass

    @abc.abstractmethod
    def encode(self) -> _list[P]:
        pass


class Continuous(Design[Stroke], abc.ABC):

    def __init__(self, size: _tuple[int, int], start: AABBCorner, coverage: _tuple[float, float]):
        super().__init__(size, coverage)
        self._start = start

    def __getitem__(self, item: str):
        if item == "start":
            return self._start
        return super().__getitem__(item)

    def _setup(self) -> _tuple[_tuple[int, int, int], _tuple[int, int, int]]:
        if self._start.x() == "left":
            x_info = 0, int(self._cov[0] * self._size[0]) - 1, 1
        else:
            x_info = self._size[0] - 1, int((1 - self._cov[0]) * self._size[0]), -1
        if self._start.y() == "top":
            y_info = 0, int(self._cov[1] * self._size[1]) - 1, 1
        else:
            y_info = self._size[1] - 1, int((1 - self._cov[1]) * self._size[1]), -1
        return x_info, y_info


class Discrete(Design[Point], abc.ABC):
    pass


class Raster(Continuous):

    def __init__(self, size: _tuple[int, int], skip: int, start: AABBCorner,
                 orientation: typing.Literal["along x", "along y"], coverage: _tuple[float, float]):
        super().__init__(size, start, coverage)
        self._skip = skip
        self._dir = orientation

    def __getitem__(self, item: str):
        if item == "skip":
            return self._skip
        elif item == "orientation":
            return self._dir
        return super().__getitem__(item)

    def draw(self) -> np.ndarray:
        binary = np.zeros(self._size[::-1], dtype=np.uint8)
        skip = self._skip + 1
        (sx, ex, x_sign), (sy, ey, y_sign) = self._setup()
        if self._dir == "along x":
            binary[np.arange(sy, ey + y_sign, skip * y_sign), sx:ex + x_sign:x_sign] = 255
        else:
            binary[sy:ey + y_sign:y_sign, np.arange(sx, ex + x_sign, skip * x_sign)] = 255
        return binary

    def encode(self) -> _list[Stroke]:
        pattern = []
        skip = self._skip + 1
        (sx, ex, x_sign), (sy, ey, y_sign) = self._setup()
        if self._dir == "along x":
            pattern.extend(Stroke((sx, curr), (ex, curr), True) for curr in range(sy, ey + y_sign, skip * y_sign))
        else:
            pattern.extend(Stroke((curr, sy), (curr, ey), True) for curr in range(sx, ex + x_sign, skip * x_sign))
        return pattern


class Snake(Continuous):

    def __init__(self, size: _tuple[int, int], skip: int, start: AABBCorner,
                 orientation: typing.Literal["along x", "along y"], coverage: _tuple[float, float]):
        super().__init__(size, start, coverage)
        self._skip = skip
        self._dir = orientation

    def __getitem__(self, item: str):
        if item == "skip":
            return self._skip
        elif item == "orientation":
            return self._dir
        return super().__getitem__(item)

    def draw(self) -> np.ndarray:
        binary = np.zeros(self._size[::-1], dtype=np.uint8)
        skip = self._skip + 1
        (sx, ex, x_sign), (sy, ey, y_sign) = self._setup()
        if self._dir == "along x":
            binary[np.arange(sy, ey + y_sign, skip * y_sign), sx:ex + x_sign:x_sign] = 255
        else:
            binary[sy:ey + y_sign:y_sign, np.arange(sx, ex + x_sign, skip * x_sign)] = 255
        return binary

    def encode(self) -> _list[Stroke]:
        pattern = []
        skip = self._skip + 1
        (sx, ex, x_sign), (sy, ey, y_sign) = self._setup()
        if self._dir == "along x":
            for curr in range(sy, ey + y_sign, skip * y_sign):
                pattern.append(Stroke((sx, curr), (ex, curr), True))
                sx, ex = ex, sx
        else:
            for curr in range(sx, ex + x_sign, skip * x_sign):
                pattern.append(Stroke((curr, sy), (curr, ey), True))
                sy, ey = ey, sy
        return pattern


class Spiral(Continuous):

    def __init__(self, size: _tuple[int, int], skip: int, start: AABBCorner,
                 orientation: typing.Literal["outside-in", "inside-out"], coverage: _tuple[float, float]):
        super().__init__(size, start, coverage)
        self._skip = skip
        self._orientation = orientation

    def __getitem__(self, item: str):
        if item == "skip":
            return self._skip
        elif item == "orientation":
            return self._orientation
        return super().__getitem__(item)

    def draw(self) -> np.ndarray:
        binary = np.zeros(self._size[::-1], dtype=np.uint8)
        skip = self._skip + 1
        (left, right, h_sign), (top, bottom, v_sign) = self._setup()
        complete = False

        def _dim_valid(minima: int, maxima: int, sign: int) -> bool:
            return (minima < maxima) if sign == 1 else (minima > maxima)

        while (_dim_valid(left + skip * h_sign, right - skip * h_sign, h_sign) and
               _dim_valid(top + skip * v_sign, bottom - skip * v_sign, v_sign)):
            binary[top, min(left, right):max(left, right) + 1] = 255
            if complete:
                bottom -= skip * v_sign
                if not _dim_valid(top, bottom, v_sign):
                    break
            binary[min(top, bottom):max(top, bottom) + 1, right] = 255
            if complete:
                left += skip * h_sign
                if not _dim_valid(left, right, h_sign):
                    break
            binary[bottom, min(left, right):max(left, right) + 1] = 255
            top += skip * v_sign
            if not _dim_valid(top, bottom, v_sign):
                break
            binary[min(top, bottom):max(top, bottom) + 1, left] = 255
            right -= skip * h_sign
            if not _dim_valid(left, right, h_sign):
                break
            complete = True
        return binary

    def encode(self) -> _list[Stroke]:
        pattern = []
        skip = self._skip + 1
        (left, right, h_sign), (top, bottom, v_sign) = self._setup()
        complete = False

        def _dim_valid(minima: int, maxima: int, sign: int) -> bool:
            return (minima < maxima) if sign == 1 else (minima > maxima)

        while (_dim_valid(left + skip * h_sign, right - skip * h_sign, h_sign) and
               _dim_valid(top + skip * v_sign, bottom - skip * v_sign, v_sign)):
            pattern.append(Stroke((left, top), (right, top)))
            if complete:
                bottom -= skip * v_sign
                if not _dim_valid(top, bottom, v_sign):
                    break
            pattern.append(Stroke((right, top), (right, bottom)))
            if complete:
                left += skip * h_sign
                if not _dim_valid(left, right, h_sign):
                    break
            pattern.append(Stroke((right, bottom), (left, bottom)))
            top += skip * v_sign
            if not _dim_valid(top, bottom, v_sign):
                break
            pattern.append(Stroke((left, bottom), (left, top)))
            right -= skip * h_sign
            if not _dim_valid(left, right, h_sign):
                break
            complete = True
        if self._orientation == "inside-out":
            pattern = [p.reverse() for p in pattern[::-1]]
        return pattern


class Grid(Discrete):

    def __init__(self, size: _tuple[int, int], gap: _tuple[int, int], shift: _tuple[int, int],
                 order: typing.Literal[
                     "row-major (++)", "row-major (-+)", "row-major (+-)", "row-major (--)",
                     "column-major (++)", "column-major (-+)", "column-major (+-)", "column-major (--)"
                 ],
                 coverage: _tuple[float, float]):
        super().__init__(size, coverage)
        self._gap = gap
        self._shift = shift
        self._order = order

    def __getitem__(self, item: str):
        if item == "gap":
            return self._gap
        elif item == "shift":
            return self._shift
        elif item == "order":
            return self._order
        return super().__getitem__(item)

    def draw(self) -> np.ndarray:
        binary = np.zeros(self._size[::-1], dtype=np.uint8)
        size = tuple(map(int, map(operator.mul, self._size, self._cov)))
        ys, xs = np.meshgrid(np.arange(self._shift[1], min(size[1] + self._shift[1], self._size[1]), self._gap[1]),
                             np.arange(self._shift[0], min(size[0] + self._shift[0], self._size[0]), self._gap[0]))
        binary[ys, xs] = 255
        return binary

    def encode(self) -> _list[Point]:
        pattern = []
        size = rows, cols = tuple(map(int, map(operator.mul, self._size, self._cov)))
        ys, xs = np.meshgrid(np.arange(self._shift[1], min(size[1] + self._shift[1], self._size[1]), self._gap[1]),
                             np.arange(self._shift[0], min(size[0] + self._shift[0], self._size[0]), self._gap[0]))
        if "row-major" in self._order:
            co_ords = ys * cols + xs
        else:
            co_ords = xs * rows + ys
        if "++" in self._order:
            invert_y = invert_x = False
        elif "-+" in self._order:
            invert_y = False
            invert_x = True
        elif "+-" in self._order:
            invert_y = True
            invert_x = False
        else:
            invert_y = invert_x = True
        y_indices, x_indices = np.unravel_index(np.argsort(co_ords, axis=None), co_ords.shape)
        pattern.extend(map(Point, zip(xs[y_indices[::(-1 if invert_y else 1)], x_indices[::(-1 if invert_x else 1)]],
                                      ys[y_indices[::(-1 if invert_y else 1)], x_indices[::(-1 if invert_x else 1)]])))
        return pattern


class Random(Discrete):

    def __init__(self, size: _tuple[int, int], r_type: RandomTypes, n: int, coverage: _tuple[float, float], **kwargs):
        super().__init__(size, coverage)
        self._r_type = r_type
        self._points: _None[_tuple[np.ndarray, np.ndarray]] = None
        self._n = n
        self._params = kwargs
        self._generator = np.random.default_rng()

    def __getitem__(self, item: str):
        if item == "r_type":
            return self._r_type
        elif item == "n":
            return self._n
        elif item in self._params:
            return self._params[item]
        return super().__getitem__(item)

    def draw(self) -> np.ndarray:
        binary = np.zeros(self._size[::-1], dtype=np.uint8)
        if not self._points:
            self._gen_points()
        ys, xs = self._points
        binary[ys, xs] = 255
        return binary

    def encode(self) -> _list[Point]:
        pattern = []
        seen = set()
        if not self._points:
            self._gen_points()
        for y, x in zip(*self._points):
            if (x, y) not in seen:
                seen.add((x, y))
                pattern.append(Point((x, y)))
        return pattern

    def _gen_points(self):
        size = tuple(map(int, map(operator.mul, self._size, self._cov)))
        if self._r_type == RandomTypes.EXP:
            points = self._generator.exponential(self._params["scale"], self._n * 2)
        elif self._r_type in {RandomTypes.LAPLACE, RandomTypes.LOGISTIC, RandomTypes.NORMAL}:
            if self._r_type == RandomTypes.LAPLACE:
                gen = self._generator.laplace
            elif self._r_type == RandomTypes.LOGISTIC:
                gen = self._generator.logistic
            else:
                gen = self._generator.normal
            points = gen(self._params["loc"], self._params["scale"], self._n * 2)
        elif self._r_type == RandomTypes.POISSON:
            points = self._generator.poisson(self._params["lam"], self._n * 2)
        else:
            points = self._generator.uniform(self._params["low"], self._params["high"], self._n * 2)
        if points.dtype == np.float64:
            powers = np.log10(np.abs(points)).astype(np.int_)
            max_dec = np.abs(np.min(powers))
            points = (points * 10 ** max_dec).astype(np.int_)
        points = points.reshape(-1, 2)
        y_mask = np.where((points[:, 0] >= 0) & (points[:, 0] < size[1]), 1, 0)
        x_mask = np.where((points[:, 1] >= 0) & (points[:, 1] < size[0]), 1, 0)
        p_mask = y_mask & x_mask
        points = points[np.nonzero(p_mask)]
        self._points = points[:, 0], points[:, 1]
