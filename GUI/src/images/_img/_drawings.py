import itertools
import typing
from typing import Tuple as _tuple, Set as _set

import cv2
import numpy as np

try:
    import typing_extensions
except ModuleNotFoundError:
    typing_extensions = typing

from .. import Colour
from .._enums import *
from .._aliases import *
from ._utils import Mutate as Mutation, BoundMutate as BoundMutation
from ._bases import Image

T = typing.TypeVar("T", bound=Colour)


def line(img: Image[T], pt1: _tuple[int, int], pt2: _tuple[int, int], colour: T, *,
         co_ords: _set[_tuple[int, int]] = None):
    """
    Draws a line on the image.

    Generics
    --------
    T: Colour
        The `CType` of the image (which should be the colour of the line)

    Parameters
    ----------
    img: Image[T]
        The image to draw on.
    pt1: tuple[int, int]
        The coordinates of the first point.
    pt2: tuple[int, int]
        The coordinates of the second point.
    colour: T
        The colour of the line.
    co_ords: set[tuple[int, int]]
            The list of co_ordinates for the line. Note that this is *filled* by this function.
    """
    if co_ords is None:
        co_ords = set()
    Drawing.check(img, pt1, pt2, colours=(colour,))
    img.image.reference()[:, :, :] = cv2.line(img.image(), pt1, pt2, colour.items(img.order))
    co_ord_points = np.zeros_like(img.image())
    co_ord_points[:, :, :] = cv2.line(co_ord_points, pt1, pt2, (255, 255, 255))
    co_ords.update((x, y) for y, x, _ in zip(*np.nonzero(co_ord_points)))


class Rectangle(typing.Generic[T]):
    """
    A rectangle creator.

    Uses the `SupportsInst` protocol.

    Generics
    --------
    T: Colour
        The `CType` of the instance and the colour of the shape (both fill and outline).

    Attributes
    ----------
    _inst: Image[T]
        The image to draw on.
    """

    @property
    def instance(self) -> Image[T]:
        """
        Public access to the image.

        Returns
        -------
        Image[T]
            The image to draw on.
        """
        return self._inst

    @instance.setter
    def instance(self, inst: Image[T]):
        self._inst = inst

    def __init__(self, inst: Image[T]):
        self._inst = inst

    @BoundMutation.decorate(default=ReferenceBehaviour.REFER)
    def from_corners(self, c1: _tuple[int, int], c2: _tuple[int, int], outline: T, *,
                     fill: typing.Optional[T] = ..., corners=(AABBCorner.TOP_LEFT, AABBCorner.BOTTOM_RIGHT),
                     co_ords: _set[_tuple[int, int]] = None):
        """
        Method to create a rectangle from two corners. These corners must be on opposite x-y sides.

        Parameters
        ----------
        c1: tuple[int, int]
            The first corner.
        c2: tuple[int, int]
            The second corner.
        outline: T
            The outline (perimeter) colour of the rectangle.
        fill: T | None
            The fill (area) colour of the rectangle. Defaults to the outline colour.
        corners: tuple[AABBCorner, AABBCorner]
            The two corners that the rectangle is created from. Default is top left and bottom right.
        co_ords: set[tuple[int, int]]
            The list of co_ordinates for the rectangle. Note that this is *filled* by this function.

        Raises
        ------
        ValueError
            If the corners of the rectangle are invalid.
            If the corner positions of the rectangle cannot be created (i.e. right being 3 and left being 7)
        """
        img = self.instance
        if fill is ...:
            fill = outline
        if co_ords is None:
            co_ords = set()
        Drawing.check(img, c1, c2, colours=(outline, fill))
        a, b = corners
        if a.x() == b.x() or a.y() == b.y():
            raise ValueError(f"Cannot create valid rectangle from {a:ll} and {b:ll}")
        if a.x() == "left":
            left, right = c1[0], c2[0]
        else:
            left, right = c2[0], c1[0]
        if a.y() == "top":
            top, bottom = c1[1], c2[1]
        else:
            top, bottom = c2[1], c1[1]
        if left >= right or top >= bottom:
            raise ValueError(f"Cannot have rectangle where {(left, top)} >= {(right, bottom)}")
        raw = img.image.reference()
        co_ord_points = np.zeros_like(img.image())
        if fill is not None:
            raw[:, :, :] = cv2.rectangle(raw, (left, top), (right, bottom), fill.items(img.order), -1)
            co_ord_points[:, :, :] = cv2.rectangle(co_ord_points, (left, top), (right, bottom), (255, 255, 255), -1)
        raw[:, :, :] = cv2.rectangle(raw, (left, top), (right, bottom), outline.items(img.order))
        co_ord_points[:, :, :] = cv2.rectangle(co_ord_points, (left, top), (right, bottom), (255, 255, 255))
        co_ords.update((x, y) for y, x, _ in zip(*np.nonzero(co_ord_points)))

    @BoundMutation.decorate(default=ReferenceBehaviour.REFER)
    def from_size(self, corner: _tuple[int, int, AABBCorner], size: _tuple[int, int], outline: T, *,
                  fill: typing.Optional[T] = ..., co_ords: _set[_tuple[int, int]] = None):
        """
        Method to create a rectangle from one known corner and a known size.

        Parameters
        ----------
        corner: tuple[int, int, AABBCorner]
            The corner of the rectangle.
        size: tuple[int, int]
            The width and height of the rectangle.
        outline: T
            The outline (perimeter) colour of the rectangle.
        fill: T | None
            The fill (area) colour of the rectangle. Defaults to the outline colour.
        co_ords: set[tuple[int, int]]
            The list of co_ordinates for the rectangle. Note that this is *filled* by this function.
        """
        p_x, p_y, pos = corner
        if pos.x() == "left":
            left, right = p_x, p_x + size[0]
        else:
            left, right = p_x - size[0], p_x
        if pos.y() == "top":
            top, bottom = p_y, p_y + size[1]
        else:
            top, bottom = p_y - size[1], p_y
        self.from_corners((left, top), (right, bottom), outline, fill=fill, co_ords=co_ords)

    @BoundMutation.decorate(default=ReferenceBehaviour.REFER)
    def from_centre(self, centre: _tuple[int, int], size: _tuple[int, int], outline: T, *,
                    fill: typing.Optional[T] = ..., co_ords: _set[_tuple[int, int]] = None):
        """
        Method to create a rectangle from the centre position and size.

        Parameters
        ----------
        centre: tuple[int, int]
            The centre position of the rectangle.
        size: tuple[int, int]
            The width and height of the rectangle.
        outline: T
            The outline (perimeter) colour of the rectangle.
        fill: T | None
            The fill (area) colour of the rectangle. Defaults to the outline colour.
        co_ords: set[tuple[int, int]]
            The list of co_ordinates for the rectangle. Note that this is *filled* by this function.
        """
        tl = (centre[0] - size[0] // 2, centre[1] - size[1] // 2)
        br = (centre[0] + size[0] // 2, centre[1] + size[1] // 2)
        self.from_corners(tl, br, outline, fill=fill, co_ords=co_ords)


class Square(typing.Generic[T]):
    """
    A square creator.

    Uses the `SupportsInst` protocol, but is essentially a wrapper around a `Rectangle` object, using `int` for sizes.

    Generics
    --------
    T: Colour
        The `CType` of the instance and the colour of the shape (both fill and outline).

    Attributes
    ----------
    _r: Rectangle[T]
        The wrapped rectangle.
    """

    @property
    def instance(self) -> Image[T]:
        """
        Public access to the instance of the wrapped rectangle object.

        Returns
        -------
        Image[T]
            The wrapped rectangle.
        """
        return self._r.instance

    @instance.setter
    def instance(self, inst: Image[T]):
        self._r.instance = inst

    def __init__(self, rect: Rectangle[T]):
        self._r = rect

    @BoundMutation.decorate(default=ReferenceBehaviour.REFER)
    def from_size(self, corner: _tuple[int, int, AABBCorner], size: int, outline: T, *,
                  fill: typing.Optional[T] = ..., co_ords: _set[_tuple[int, int]] = None):
        """
        A wrapper for `Rectangle.from_size`.

        Parameters
        ----------
        corner: tuple[int, int, AABBCorner]
            The corner of the square.
        size: int
            The width of the square. It is also the height.
        outline: T
            The outline (perimeter) colour of the square.
        fill: T | None
            The fill (area) colour of the square. Defaults to the outline colour.
        co_ords: set[tuple[int, int]]
            The list of co_ordinates for the square. Note that this is *filled* by this function.
        """
        self._r.from_size(corner, (size, size), outline, fill=fill, co_ords=co_ords)

    @BoundMutation.decorate(default=ReferenceBehaviour.REFER)
    def from_centre(self, centre: _tuple[int, int], size: int, outline: T, *, fill: typing.Optional[T] = ...,
                    co_ords: _set[_tuple[int, int]] = None):
        """
        A wrapper for `Rectangle.from_centre`.

        Parameters
        ----------
        centre: tuple[int, int]
            The centre of the square.
        size: int
            The width of the square. It is also the height.
        outline: T
            The outline (perimeter) colour of the square.
        fill: T | None
            The fill (area) colour of the square. Defaults to the outline colour.
        co_ords: set[tuple[int, int]]
            The list of co_ordinates for the square. Note that this is *filled* by this function.
        """
        self._r.from_centre(centre, (size, size), outline, fill=fill, co_ords=co_ords)


class SafeRect(Rectangle[T]):
    """
    Special subclass to represent a rectangle that will respect the bounds of the image.

    It will draw itself as a series of lines if the requested co-ordinates are outside the image's bounds.
    """

    @BoundMutation.decorate(default=ReferenceBehaviour.REFER)
    def from_corners(self, c1: _tuple[int, int], c2: _tuple[int, int], outline: T, *,
                     fill: typing.Optional[T] = ..., corners=(AABBCorner.TOP_LEFT, AABBCorner.BOTTOM_RIGHT),
                     co_ords: _set[_tuple[int, int]] = None):
        """
        Method to safely create a rectangle from two corners. These corners must be on opposite x-y sides.

        Parameters
        ----------
        c1: tuple[int, int]
            The first corner.
        c2: tuple[int, int]
            The second corner.
        outline: T
            The outline (perimeter) colour of the rectangle.
        fill: T | None
            The fill (area) colour of the rectangle. Defaults to the outline colour.
        corners: tuple[AABBCorner, AABBCorner]
            The two corners that the rectangle is created from. Default is top left and bottom right.
        co_ords: set[tuple[int, int]]
            The list of co_ordinates for the rectangle. Note that this is *filled* by this function.

        Raises
        ------
        ValueError
            If the corners of the rectangle are invalid.
            If the corner positions of the rectangle cannot be created (i.e. right being 3 and left being 7)
        """
        try:
            super().from_corners(c1, c2, outline, fill=fill, corners=corners, co_ords=co_ords)
        except IndexError:
            if co_ords is None:
                co_ords = set()
            img = self.instance
            if fill is ...:
                fill = outline
            w, h = img.size
            a, b = corners
            if a.x() == "left":
                left, right = max(0, c1[0]), min(c2[0], w - 1)
            else:
                left, right = max(0, c2[0]), min(c1[0], w - 1)
            if a.y() == "top":
                top, bottom = max(0, c1[1]), min(c2[1], h - 1)
            else:
                top, bottom = max(0, c2[1]), min(c1[1], h - 1)
            co_ord_points = np.zeros_like(img.image())
            if fill is not None:
                img.image.reference()[:, :, :] = cv2.rectangle(img.image(), (left, top), (right, bottom),
                                                               fill.items(img.order), -1)
                co_ord_points[:, :, :] = cv2.rectangle(co_ord_points, (left, top), (right, bottom), (255, 255, 255), -1)
            co_ords.update((x, y) for y, x, _ in zip(*np.nonzero(co_ord_points)))
            line(img, (left, top), (right, top), outline, co_ords=co_ords)
            line(img, (right, top), (right, bottom), outline, co_ords=co_ords)
            line(img, (left, bottom), (right, bottom), outline, co_ords=co_ords)
            line(img, (left, top), (left, bottom), outline, co_ords=co_ords)


class SafeSquare(Square[T]):
    """
    Special subclass to represent a square that will respect the bounds of the image.

    It will draw itself as a series of lines if the requested co-ordinates are outside the image's bounds.
    """

    def __init__(self, rect: SafeRect[T]):
        super().__init__(rect)


def arc(img: Image[T], centre: _tuple[int, int], radius: _tuple[int, int], extent: int, outline: T, *, start=0,
        fill: typing.Optional[T] = ..., co_ords: _set[_tuple[int, int]] = None):
    """
    Draw an arc onto the image. All angles are considered to be counter-clockwise (which is the path the line takes).

    Generics
    --------
    T: Colour
        The `CType` of the image (which should be the colour of the arc)

    Parameters
    ----------
    img: Image[T]
        The image to draw onto.
    centre: tuple[int, int]
        The centre of the arc.
    radius: tuple[int, int]
        The arc radius.
    extent: int
        The degree of travel in degrees. This is *not* the ending angle of the arc, but satisfies the equation:
        >>>start + extent == end
    outline: T
        The outline (perimeter) colour of the arc.
    start: int
        The starting angle in degrees.
    fill: T | None
        The fill (area) colour of the arc. Defaults to the outline colour.
    co_ords: set[tuple[int, int]]
        The list of co_ordinates for the arc. Note that this is *filled* by this function.

    Raises
    ------
    ValueError
        If `start` is not natural, or `extent` is not positive.
        If `start` is larger than 259, or `extent` is larger than 360.
    """
    if co_ords is None:
        co_ords = set()
    end = start + extent
    if fill is ...:
        fill = outline
    if start < 0 or extent <= 0:
        raise ValueError(f"Start and extent must be non-negative")
    elif start >= 360 or extent > 360:
        raise ValueError(f"Internal ellipse angle is 360 degrees")
    (cx, cy), (rx, ry) = centre, radius
    Drawing.check(img, centre, (cx + rx, cy), (cx + rx, cy + ry), (cx, cy + ry), (cx - rx, cy + ry), (cx - rx, cy),
                  (cx - ry, cy - ry), (cx, cy - ry), (cx + rx, cy - ry), colours=(outline, fill))
    raw = img.image.reference()
    co_ord_points = np.zeros_like(raw)
    if fill is not None:
        raw[:, :, :] = cv2.ellipse(raw, centre, radius, extent, start, end, fill.items(img.order), -1)
        co_ord_points[:, :, :] = cv2.ellipse(co_ord_points, centre, radius, extent, start, end, (255, 255, 255), -1)
    raw[:, :, :] = cv2.ellipse(raw, centre, radius, extent, start, end, outline.items(img.order))
    co_ord_points[:, :, :] = cv2.ellipse(co_ord_points, centre, radius, extent, start, end, (255, 255, 255))
    co_ords.update((x, y) for y, x, _ in zip(*np.nonzero(co_ord_points)))


def ellipse(img: Image[T], centre: _tuple[int, int], radius: _tuple[int, int], outline: T, *,
            fill: typing.Optional[T] = ..., co_ords: _set[_tuple[int, int]] = None):
    """
    Draw an ellipse onto the image.

    For validation purposes, an ellipse is considered to be an arc with a 360-degree extent.

    Generics
    --------
    T: Colour
        The `CType` of the image (which should be the colour of the ellipse)

    Parameters
    ----------
    img: Image[T]
        The image to draw onto.
    centre: tuple[int, int]
        The centre of the ellipse.
    radius: tuple[int, int]
        The ellipse radius.
    outline: T
        The outline (perimeter) colour of the ellipse.
    fill: T | None
        The fill (area) colour of the ellipse. Defaults to the outline colour.
    co_ords: set[tuple[int, int]]
        The list of co_ordinates for the arc. Note that this is *filled* by this function.
    """
    arc(img, centre, radius, 360, outline, fill=fill, co_ords=co_ords)


def circle(img: Image[T], centre: _tuple[int, int], radius: int, outline: T, *, fill: typing.Optional[T] = ...,
           co_ords: _set[_tuple[int, int]] = None):
    """
    Draw a circle onto the image.

    This is a wrapper for an `ellipse` with the radius as an integer.

    Generics
    --------
    T: Colour
        The `CType` of the image (which should be the colour of the circle)

    Parameters
    ----------
    img: Image[T]
        The image to draw onto.
    centre: tuple[int, int]
        The centre of the circle.
    radius: int
        The circle radius.
    outline: T
        The outline (perimeter) colour of the circle.
    fill: T | None
        The fill (area) colour of the circle. Defaults to the outline colour.
    co_ords: set[tuple[int, int]]
            The list of co_ordinates for the circle. Note that this is *filled* by this function.
    """
    ellipse(img, centre, (radius, radius), outline, fill=fill, co_ords=co_ords)


class Polygon(typing.Generic[T]):
    """
       A generic n-sided polygon creator.

       Uses the `SupportsInst` protocol.

       Generics
       --------
       T: Colour
           The `CType` of the instance and the colour of the shape (both fill and outline).

       Attributes
       ----------
       _inst: Image[T]
           The image to draw on.
       """

    @property
    def instance(self) -> Image[T]:
        """
        Public access to the image.

        Returns
        -------
        Image[T]
            The image to draw on.
        """
        return self._inst

    @instance.setter
    def instance(self, inst: Image[T]):
        self._inst = inst

    def __init__(self, inst: Image[T]):
        self._inst = inst

    @BoundMutation.decorate(default=ReferenceBehaviour.REFER)
    def from_vertices(self, outline: T, v1: _tuple[int, int], v2: _tuple[int, int], v3: _tuple[int, int],
                      *v_r: _tuple[int, int], fill: typing.Optional[T] = ..., co_ords: _set[_tuple[int, int]] = None):
        """
        Draw the polygon from the raw location of the vertices.

        Parameters
        ----------
        outline: T
            The outline (perimeter) colour of the polygon.
        v1: tuple[int, int]
            The first vertex of the polygon.
        v2: tuple[int, int]
            The second vertex of the polygon.
        v3: tuple[int, int]
            The third vertex of the polygon.
        *v_r: tuple[int, int]
            The remaining vertices of the polygon.
        fill: T | None
            The fill (area) colour of the polygon. Defaults to the outline colour.
        co_ords: set[tuple[int, int]]
            The list of co_ordinates for the polygon. Note that this is *filled* by this function.
        """
        if co_ords is None:
            co_ords = set()
        img = self.instance
        vrtcs = (v1, v2, v3, *v_r)
        points = np.array(vrtcs, dtype=np.int32).reshape(1, -1, 2)
        if fill is ...:
            fill = outline
        Drawing.check(img, *vrtcs, colours=(outline, fill))
        raw = img.image.reference()
        co_ord_points = np.zeros_like(raw)
        if fill is not None:
            raw[:, :, :] = cv2.fillPoly(raw, points, fill.items(img.order))
            co_ord_points[:, :, :] = cv2.fillPoly(co_ord_points, points, (255, 255, 255))
        raw[:, :, :] = cv2.polylines(raw, points, True, outline.items(img.order))
        co_ord_points[:, :, :] = cv2.polylines(co_ord_points, points, True, (255, 255, 255))
        co_ords.update((x, y) for y, x, _ in zip(*np.nonzero(co_ord_points)))

    @BoundMutation.decorate(default=ReferenceBehaviour.REFER)
    def from_relative(self, corner: _tuple[int, int, AABBCorner], outline: T, o1: _tuple[int, int],
                      o2: _tuple[int, int], o3: _tuple[int, int], *o_r: _tuple[int, int],
                      fill: typing.Optional[T] = ..., co_ords: _set[_tuple[int, int]] = None):
        """
        Draw the polygon from the relative location of the vertices, with respect to a given corner.

        Parameters
        ----------
        corner: tuple[int, int, AABBCorner]
            The known corner.
        outline: T
            The outline (perimeter) colour of the polygon.
        o1: tuple[int, int]
            The first vertex of the polygon.
        o2: tuple[int, int]
            The second vertex of the polygon.
        o3: tuple[int, int]
            The third vertex of the polygon.
        *o_r: tuple[int, int]
            The remaining vertices of the polygon.
        fill: T | None
            The fill (area) colour of the polygon. Defaults to the outline colour.
        co_ords: set[tuple[int, int]]
            The list of co_ordinates for the polygon. Note that this is *filled* by this function.
        """
        c_x, c_y, pos = corner
        if pos.x() == "left":
            def _x(x: int) -> int:
                if x < 0:
                    raise ValueError("Left corner must have all positive x-offsets")
                return x + c_x
        else:
            def _x(x: int) -> int:
                if x > 0:
                    raise ValueError("Right corner must have all negative x-offsets")
                return x - c_x
        if pos.y() == "top":
            def _y(y: int) -> int:
                if y < 0:
                    raise ValueError("Top corner must have all positive y-offsets")
                return y + c_y
        else:
            def _y(y: int) -> int:
                if y > 0:
                    raise ValueError("Bottom corner must have all negative y-offsets")
                return y - c_y

        def _abs(xy: _tuple[int, int]) -> _tuple[int, int]:
            return _x(xy[0]), _y(xy[1])

        return self.from_vertices(outline, *map(_abs, (o1, o2, o3, *o_r)), fill=fill, co_ords=co_ords)

    @BoundMutation.decorate(default=ReferenceBehaviour.REFER)
    def from_centre(self, centre: _tuple[int, int], outline: T, o1: _tuple[int, int], o2: _tuple[int, int],
                    o3: _tuple[int, int], *o_r: _tuple[int, int], fill: typing.Optional[T] = ...,
                    co_ords: _set[_tuple[int, int]] = None):
        """
        Draw the polygon from the relative location of the vertices, with respect to the centre.

        Parameters
        ----------
        centre: tuple[int, int]
            The midpoint.
        outline: T
            The outline (perimeter) colour of the polygon.
        o1: tuple[int, int]
            The first vertex of the polygon.
        o2: tuple[int, int]
            The second vertex of the polygon.
        o3: tuple[int, int]
            The third vertex of the polygon.
        *o_r: tuple[int, int]
            The remaining vertices of the polygon.
        fill: T | None
            The fill (area) colour of the polygon. Defaults to the outline colour.
        co_ords: set[tuple[int, int]]
            The list of co_ordinates for the polygon. Note that this is *filled* by this function.
        """

        def _abs(xy: _tuple[int, int]) -> _tuple[int, int]:
            return xy[0] + centre[0], xy[1] + centre[1]

        return self.from_vertices(outline, *map(_abs, (o1, o2, o3, *o_r)), fill=fill, co_ords=co_ords)


def cross(img: Image[T], centre: _tuple[int, int], length: int, outline: T, *, shape=CrossShape.DIAGONAL,
          co_ords: _set[_tuple[int, int]] = None):
    """
    Draw a cross on the image. The cross-shape is customisable.

    Generics
    --------
    T: Colour
        The `CType` of the image (which should be the colour of the lines in the cross)

    Parameters
    ----------
    img: Image[T]
        The image to draw on.
    centre: tuple[int, int]
        The midpoint of the cross.
    length: int
        The line length. The lines are drawn such that the centre point is `length // 2` pixels away from the line end.
    outline: T
        The colour of the lines that make up the cross.
    shape: CrossShape (default is `DIAGONAL`)
        The shape of the cross.
    co_ords: set[tuple[int, int]]
        The list of co_ordinates for the lines. Note that this is *filled* by this function.
    """
    c_x, c_y = centre
    r = length // 2
    if shape == CrossShape.DIAGONAL:
        line(img, (c_x - r, c_y - r), (c_x + r, c_y + r), outline, co_ords=co_ords)
        line(img, (c_x + r, c_y - r), (c_x - r, c_y + r), outline, co_ords=co_ords)
    elif shape == CrossShape.ALIGNED:
        line(img, (c_x - r, c_y), (c_x + r, c_y), outline, co_ords=co_ords)
        line(img, (c_x, c_y - r), (c_x, c_y + r), outline, co_ords=co_ords)


def square_spiral(img: Image[T], start: _tuple[int, int], initial_length: int, colour: T, *, growth=1,
                  x_order: _tuple[XDir, XDir] = ("right", "left"), y_order: _tuple[YDir, YDir] = ("up", "down"),
                  co_ords: _set[_tuple[int, int]] = None):
    """
    Draw a spiral, where the lines aren't curved, but rather sharp edges.

    The effect looks like a discontinuous function, but the overall shape is still connected.

    Generics
    --------
    T: Colour
        The `CType` of the image (which should be the colour of the lines)

    Parameters
    ----------
    img: Image[T]
        The image to draw on.
    start: tuple[int, int]
        The start point of the first line.
    initial_length: int
        The starting line length. This will slowly increase with every line.
    colour: T
        The line colour for the spiral.
    growth: int (default is 1)
        The number of pixels to add to the length with each drawn line.
    x_order: tuple[XDir, XDir]
        The order in which to draw the horizontal lines. This should contain two unique values.
    y_order: tuple[YDir, YDir]
        The order in which to draw the vertical lines. This should contain two unique values.
    co_ords: set[tuple[int, int]]
        The list of co_ordinates for the lines. Note that this is *filled* by this function.

    Raises
    ------
    ValueError
        If growth or length is not natural numbers.
        If the x or y order is not unique.
    """
    if growth < 1:
        raise ValueError(f"Expected a natural number for spiral growth, got {growth}")
    elif initial_length < 1:
        raise ValueError(f"Expected a natural number for spiral length, got {initial_length}")
    for d, order in zip(("x", "y"), (x_order, y_order)):
        if len(order) != len(set(order)):
            raise ValueError(f"Expected a unique {d}-order, got {order}")

    def _order():
        i = False
        while True:
            yield x_order[int(i)]
            yield y_order[int(i)]
            i = not i

    steps = itertools.cycle(_order())
    step = next(steps)
    point = start
    Drawing.check(img, start, (start[0] + initial_length, start[1]), (start[0] - initial_length, start[1]),
                  (start[0], start[1] + initial_length), (start[0], start[1] - initial_length), colours=(colour,))

    bounds = img.size

    def _valid() -> bool:
        valid = True

        def _edit(new: _tuple[int, int]):
            nonlocal valid
            if any(n < 0 or n >= b for n, b in zip(new, bounds)):
                valid = False

        _loop(_edit)
        return valid

    def _loop(post: typing.Callable[[_tuple[int, int]], None]):
        direction = step
        end_length = initial_length
        test = point

        for _ in range(4):
            p_x, p_y = test
            if direction == "right":
                new = (p_x + end_length, p_y)
            elif direction == "up":
                new = (p_x, p_y - end_length)
            elif direction == "left":
                new = (p_x - end_length, p_y)
            else:
                new = (p_x, p_y + end_length)
            post(new)
            direction = next(steps)
            test = new
            end_length += growth

    while _valid():
        def _change(new: _tuple[int, int]):
            nonlocal initial_length, point
            line(img, point, new, colour, co_ords=co_ords)
            initial_length += growth
            point = new

        _loop(_change)


class Drawing(typing.Generic[T]):
    """
    Class to combine all drawing functions.

    This will have attributes with the same name as the drawing functions, but are instead `Mutate` decorators.

    This obeys the `HasInst` protocol.

    Generics
    --------
    T: Colour
        The `CType` of the image (which should be the colour all drawings).

    Attributes
    ----------
    _inst: Image[T]
        The image instance bound to this object.
    """

    @property
    def instance(self) -> Image[T]:
        """
        Public access to the image instance.

        Returns
        -------
        Image[T]
            The image instance bound to this object.

        Raises
        ------
        UnboundLocalError
            If the transform is unbound.
        """
        if self._inst is None:
            raise UnboundLocalError("Transform has no instance")
        return self._inst

    @property
    def rect(self) -> Rectangle[T]:
        """
        Public access to the rectangle instance.

        Returns
        -------
        Rectangle[T]
            The rectangle instance bound to this object's instance.

        Raises
        ------
        UnboundLocalError
            If the transform is unbound.
        """
        return Rectangle(self.instance)

    @property
    def safe_rect(self) -> SafeRect[T]:
        """
        Public access to the safe rectangle instance.

        Returns
        -------
        SafeRect[T]
            The safe rectangle instance bound to this object's instance.

        Raises
        ------
        UnboundLocalError
            If the transform is unbound.
        """
        return SafeRect(self.instance)

    @property
    def square(self) -> Square[T]:
        """
        Public access to the square instance.

        Returns
        -------
        Square[T]
            The square instance bound to this object's instance.

        Raises
        ------
        UnboundLocalError
            If the transform is unbound.
        """
        return Square(self.rect)

    @property
    def safe_square(self) -> SafeSquare[T]:
        """
        Public access to the safe square instance.

        Returns
        -------
        SafeSquare[T]
            The safe square instance bound to this object's instance.

        Raises
        ------
        UnboundLocalError
            If the transform is unbound.
        """
        return SafeSquare(self.safe_rect)

    @property
    def polygon(self) -> Polygon[T]:
        """
        Public access to the polygon instance.

        Returns
        -------
        Polygon[T]
            The polygon instance bound to this object's instance.

        Raises
        ------
        UnboundLocalError
            If the transform is unbound.
        """
        return Polygon(self.instance)

    def __init__(self):
        self._inst: typing.Optional[Image[T]] = None

    def __get__(self, instance: Image[T], owner: typing.Type[Image[T]]) -> "Drawing[T]":
        if instance is None:
            return self
        self._inst = instance
        return self

    line = Mutation(line, default=ReferenceBehaviour.REFER)
    arc = Mutation(arc, default=ReferenceBehaviour.REFER)
    ellipse = Mutation(ellipse, default=ReferenceBehaviour.REFER)
    circle = Mutation(circle, default=ReferenceBehaviour.REFER)
    cross = Mutation(cross, default=ReferenceBehaviour.REFER)
    spiral = Mutation(square_spiral, default=ReferenceBehaviour.REFER)

    @staticmethod
    def check(img: Image[T], *pos: _tuple[int, int], colours: _tuple[T, ...] = ()):
        """
        Checks if the positions and colours are invalid for the given image type.

        This is called by all drawing functions.

        Parameters
        ----------
        img: Image[T]
            The image to validate against.
        *pos: tuple[int, int]
            The positions to check.
        colours: tuple[T, ...]
            The colours to check.

        Raises
        ------
        IndexError
            If any position is invalid.
        ValueError
            If any colour is invalid.
        """
        for i in pos:
            _ = img[i]
        for colour in colours:
            if colour is not None:
                if not img.verify_colour(colour):
                    raise ValueError(f"Cannot use colour {colour} on the chosen image")
