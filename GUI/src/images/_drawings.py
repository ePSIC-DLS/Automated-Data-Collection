import typing
from typing import Optional as _None, Tuple as _tuple, Type as _type

import cv2
import numpy as np
import typing_extensions

from ._bases import Image
from ._enums import *
from ._utils import OnHasImg


class BaseArtist:
    """
    Base artist designed to store state for subclasses.

    Attributes
    ----------
    _img: Image
        The image to draw on.
    _fill_type: FillBehaviour
        The type of fill behaviour.
    _fill_colour: int_ | None
        The colour to use in fill behaviour. Is only non-None when the fill type is fixed.
    """

    @property
    def instance(self) -> _None[Image]:
        """
        Public access to the stored Image instance.

        Returns
        -------
        Image
            The image to draw on.
        """
        return self._img

    @instance.setter
    def instance(self, value: Image):
        self._img = value

    @property
    def fill(self) -> typing.Union[FillBehaviour, np.int_]:
        """
        The default fill colour.

        Returns
        -------
        FillBehaviour | int_
            The fill colour. If the colour is not defined, the type is used.
        """
        if self._fill_type == FillBehaviour.FIXED:
            return self._fill_colour
        return self._fill_type

    @fill.setter
    def fill(self, value: typing.Union[FillBehaviour, np.int_]):
        if value == FillBehaviour.FIXED:
            raise ValueError("Cannot have fixed fill type with no value")
        elif isinstance(value, (np.int_, int)):
            self._fill_colour = np.int_(value)
            self._fill_type = FillBehaviour.FIXED
        else:
            self._fill_colour = None
            self._fill_type = value

    def __init__(self, img: Image = None):
        self._img: _None[Image] = img
        self._fill_type = FillBehaviour.OUTLINE
        self._fill_colour: _None[np.int_] = None

    def __get__(self, instance: _None[Image], owner: _type[Image]) -> typing_extensions.Self:
        self._img = instance
        return self

    def _get_default_fill(self, fg: np.int_) -> _None[np.int_]:
        if self._fill_type == FillBehaviour.OUTLINE:
            return fg
        else:
            return self._fill_colour

    def _check(self, *points: _tuple[int, int], colours: _tuple[_None[np.int_], ...] = ()):
        for i in points:
            _ = self._img[i]
        for colour in colours:
            if colour is not None:
                if not self._img.verify(colour):
                    raise ValueError(f"Cannot use colour {colour} on the chosen image")


class LineArtist(BaseArtist):
    """
    Concrete artist designed to draw lines.
    """

    @OnHasImg.decorate(default=ReferBehavior.REFER)
    def line(self, pt1: _tuple[int, int], pt2: _tuple[int, int], colour: np.int_):
        """
        Draw a line between two points.

        Parameters
        ----------
        pt1: tuple[int, int]
            The first point.
        pt2: tuple[int, int]
            The second point.
        colour: int_
            The colour to draw the line in. Must be valid for the image.

        Raises
        ------
        IndexError
            If any point is out of range.
        ValueError
            If the colour is invalid.
        """
        self._check(pt1, pt2, colours=(colour,))
        data = self._img.data()
        cv2.line(data, pt1, pt2, (float(colour),) * 3)


class RectArtist(BaseArtist):
    """
    Concrete artist to draw rectangles.
    """

    @OnHasImg.decorate(default=ReferBehavior.REFER)
    def size(self, corner: _tuple[int, int], size: _tuple[int, int], outline: np.int_, *, fill: np.int_ = ...,
             position=AABBCorner.TOP_LEFT, safe=False):
        """
        Draw a rectangle from a known corner and the size.

        Parameters
        ----------
        corner: tuple[int, int]
            The known corner position.
        size: tuple[int, int]
            The size of the rectangle.
        outline: int_
            The colour to draw the rectangle's line in. Must be valid for the image.
        fill: int_
            The fill colour. If not defined, the default behaviour is used.
        position: AABBCorner
            The known corner identifier.
        safe: bool
            Whether the rectangle should be safely drawn - a safe rectangle will only draw up to the edges of the image.

        Raises
        ------
        IndexError
            If any point is out of range.
        ValueError
            If the colour is invalid.
        """
        if position.x() == XAxis.LEFT:
            left = corner[0]
        else:
            left = corner[0] - size[0]
        if position.y() == YAxis.TOP:
            top = corner[1]
        else:
            top = corner[1] - size[1]
        right = left + size[0]
        bottom = top + size[1]
        self._check((left, top), (right, bottom), colours=(outline, fill))
        data = self._img.data()
        if fill is ...:
            fill = self._get_default_fill(outline)
        if safe:
            w, h = self._img.size
            left = max(0, left)
            top = max(0, top)
            right = min(w - 1, right)
            bottom = min(h - 1, bottom)
        data[top, left:right + 1] = outline
        data[bottom, left:right + 1] = outline
        data[top:bottom + 1, left] = outline
        data[top:bottom + 1, right] = outline
        if fill is not None:
            data[top + 1:bottom, left + 1:right] = fill

    @OnHasImg.decorate(default=ReferBehavior.REFER)
    def corners(self, c1: _tuple[int, int], c2: _tuple[int, int], outline: np.int_, *, fill: np.int_ = ...,
                corners=(AABBCorner.TOP_LEFT, AABBCorner.BOTTOM_RIGHT), safe=False):
        """
        Draw a rectangle from two diagonal known corners.

        Parameters
        ----------
        c1: tuple[int, int]
            The first known corner position.
        c2: tuple[int, int]
            The second known corner position.
        outline: int_
            The colour to draw the rectangle's line in. Must be valid for the image.
        fill: int_
            The fill colour. If not defined, the default behaviour is used.
        corners: tuple[AABBCorner, AABBCorner]
            The known corner identifiers.
        safe: bool
            Whether the rectangle should be safely drawn - a safe rectangle will only draw up to the edges of the image.

        Raises
        ------
        IndexError
            If any point is out of range.
        ValueError
            If the colour is invalid.
            If the chosen corners cannot form a rectangle.
        """
        if corners[0].x() == corners[1].x() or corners[0].y() == corners[1].y():
            raise ValueError(f"Cannot form rectangle from {corners[0]:l} to {corners[1]:l}")
        if corners[0].x() == XAxis.LEFT:
            left, right = c1[0], c2[0]
        else:
            left, right = c2[0], c1[0]
        if corners[0].y() == YAxis.TOP:
            top, bottom = c1[1], c2[1]
        else:
            top, bottom = c2[1], c1[1]
        self.size((left, top), (right - left, bottom - top), outline, fill=fill, safe=safe)

    @OnHasImg.decorate(default=ReferBehavior.REFER)
    def centre(self, centre: _tuple[int, int], size: _tuple[int, int], outline: np.int_, *, fill: np.int_ = ...,
               safe=False):
        """
        Draw a rectangle from the centre and the size.

        Parameters
        ----------
        centre: tuple[int, int]
            The centre position.
        size: tuple[int, int]
            The size of the rectangle.
        outline: int_
            The colour to draw the rectangle's line in. Must be valid for the image.
        fill: int_
            The fill colour. If not defined, the default behaviour is used.
        safe: bool
            Whether the rectangle should be safely drawn - a safe rectangle will only draw up to the edges of the image.

        Raises
        ------
        IndexError
            If any point is out of range.
        ValueError
            If the colour is invalid.
        """
        left, right = centre[0] - size[0], centre[0] + size[0]
        top, bottom = centre[1] - size[1], centre[1] + size[1]
        self.corners((left, top), (right, bottom), outline, fill=fill, safe=safe)


class SquareArtist(BaseArtist):
    """
    Concrete artist to draw squares.

    Attributes
    ----------
    _r: RectArtist
        The rectangular artist used to draw squares.
    """

    def __init__(self, rect: RectArtist):
        super().__init__(rect.instance)
        self._r = rect

    @OnHasImg.decorate(default=ReferBehavior.REFER)
    def size(self, corner: _tuple[int, int], size: int, outline: np.int_, *, fill: np.int_ = ...,
             position=AABBCorner.TOP_LEFT, safe=False):
        """
        Draw a square from a known corner and the size.

        Parameters
        ----------
        corner: tuple[int, int]
            The known corner position.
        size: int
            The size of the square.
        outline: int_
            The colour to draw the square's line in. Must be valid for the image.
        fill: int_
            The fill colour. If not defined, the default behaviour is used.
        position: AABBCorner
            The known corner identifier.
        safe: bool
            Whether the square should be safely drawn - a safe square will only draw up to the edges of the image.

        Raises
        ------
        IndexError
            If any point is out of range.
        ValueError
            If the colour is invalid.
        """
        self._r.size(corner, (size, size), outline, fill=fill, position=position, safe=safe)

    @OnHasImg.decorate(default=ReferBehavior.REFER)
    def centre(self, centre: _tuple[int, int], size: int, outline: np.int_, *, fill: np.int_ = ..., safe=False):
        """
        Draw a square from the centre and the size.

        Parameters
        ----------
        centre: tuple[int, int]
            The centre position.
        size: int
            The size of the rectangle.
        outline: int_
            The colour to draw the square's line in. Must be valid for the image.
        fill: int_
            The fill colour. If not defined, the default behaviour is used.
        safe: bool
            Whether the square should be safely drawn - a safe square will only draw up to the edges of the image.

        Raises
        ------
        IndexError
            If any point is out of range.
        ValueError
            If the colour is invalid.
        """
        self._r.centre(centre, (size, size), outline, fill=fill, safe=safe)


class ArcArtist(BaseArtist):
    """
    Concrete artist to draw rounded shapes.
    """

    @OnHasImg.decorate(default=ReferBehavior.REFER)
    def arc(self, centre: _tuple[int, int], radius: _tuple[int, int], extent: int, outline: np.int_, *, start=0,
            fill: np.int_ = ...):
        """
        Draw an arc across the image.

        Parameters
        ----------
        centre: tuple[int, int]
            The centre position.
        radius: tuple[int, int]
            The size of the arc.
        extent: int
            The angle to cover. This is not the ending angle, but rather an angular distance measured counter-clockwise.
        outline: int_
            The colour to draw the arc's line in. Must be valid for the image.
        fill: int_
            The fill colour. If not defined, the default behaviour is used.
        start: int
            The starting angle. Measured counter-clockwise.

        Raises
        ------
        IndexError
            If any point is out of range.
        ValueError
            If the colour is invalid.
            If the start is not between 0 and 359.
            If the extent is not between 1 and 360.
        """
        end = start + extent
        if start < 0 or extent <= 0:
            raise ValueError("Start and extent must be non-negative")
        elif start >= 360 or extent > 360:
            raise ValueError("Internal ellipse angle is 360 degrees")
        (cx, cy), (rx, ry) = centre, radius
        self._check(centre, (cx + rx, cy), (cx + rx, cy + ry), (cx, cy + ry), (cx - rx, cy + ry), (cx - rx, cy),
                    (cx - rx, cy - ry), (cx, cy - ry), (cx + rx, cy - ry), colours=(outline, fill))
        if fill is ...:
            fill = self._get_default_fill(outline)
        raw = self._img.data()
        if fill is not None:
            cv2.ellipse(raw, centre, radius, extent, start, end, (float(fill),) * 3, -1)
        cv2.ellipse(raw, centre, radius, extent, start, end, (float(outline),) * 3)

    @OnHasImg.decorate(default=ReferBehavior.REFER)
    def ellipse(self, centre: _tuple[int, int], radius: _tuple[int, int], outline: np.int_, *,
                fill: np.int_ = ...):
        """
        Draw an ellipse across the image. For the purposes of drawing, an ellipse is an arc with a 360 degree extent.

        Parameters
        ----------
        centre: tuple[int, int]
            The centre position.
        radius: tuple[int, int]
            The size of the ellipse from centre to edge.
        outline: int_
            The colour to draw the ellipse's line in. Must be valid for the image.
        fill: int_
            The fill colour. If not defined, the default behaviour is used.

        Raises
        ------
        IndexError
            If any point is out of range.
        ValueError
            If the colour is invalid.
        """
        self.arc(centre, radius, 360, outline, fill=fill)

    @OnHasImg.decorate(default=ReferBehavior.REFER)
    def circle(self, centre: _tuple[int, int], radius: int, outline: np.int_, *, fill: np.int_ = ...):
        """
        Draw a circle across the image.

        Parameters
        ----------
        centre: tuple[int, int]
            The centre position.
        radius: int
            The size of the circle from centre to edge.
        outline: int_
            The colour to draw the circle's line in. Must be valid for the image.
        fill: int_
            The fill colour. If not defined, the default behaviour is used.

        Raises
        ------
        IndexError
            If any point is out of range.
        ValueError
            If the colour is invalid.
        """
        self.ellipse(centre, (radius, radius), outline, fill=fill)


class PolygonArtist(BaseArtist):
    """
    Concrete artist to draw polygons.
    """

    @OnHasImg.decorate(default=ReferBehavior.REFER)
    def vertices(self, outline: np.int_, v1: _tuple[int, int], v2: _tuple[int, int], v3: _tuple[int, int],
                 *vr: _tuple[int, int], fill: np.int_ = ...):
        """
        Draw a polygon from the known vertex positions.

        Parameters
        ----------
        outline: int_
            The colour to draw the ellipse's line in. Must be valid for the image.
        v1: tuple[int, int]
            The first vertex position.
        v2: tuple[int, int]
            The second vertex position.
        v3: tuple[int, int]
            The third vertex position.
        *vr: tuple[int, int]
            The remaining vertex positions.
        fill: int_
            The fill colour. If not defined, the default behaviour is used.

        Raises
        ------
        IndexError
            If any point is out of range.
        ValueError
            If the colour is invalid.
        """
        self._check(v1, v2, v3, *vr, colours=(outline, fill))
        vrtcs = (v1, v2, v3, *vr)
        points = np.array(vrtcs, dtype=np.int32).reshape(1, -1, 2)
        raw = self._img.data()
        if fill is ...:
            fill = self._get_default_fill(outline)
        if fill is not None:
            cv2.fillPoly(raw, points, (float(fill),) * 3)
        cv2.polylines(raw, points, True, (float(outline),) * 3)

    @OnHasImg.decorate(default=ReferBehavior.REFER)
    def relative(self, corner: _tuple[int, int], outline: np.int_, r1: _tuple[int, int], r2: _tuple[int, int],
                 r3: _tuple[int, int], *rr: _tuple[int, int], fill: np.int_ = ..., position=AABBCorner.TOP_LEFT):
        """
        Draw a polygon from the relative positions of the vertices based on a known corner position.

        Parameters
        ----------
        corner: tuple[int, int]
            The corner position.
        outline: int_
            The colour to draw the ellipse's line in. Must be valid for the image.
        r1: tuple[int, int]
            The first vertex offset.
        r2: tuple[int, int]
            The second vertex offset.
        r3: tuple[int, int]
            The third vertex offset.
        *rr: tuple[int, int]
            The remaining vertex offsets.
        fill: int_
            The fill colour. If not defined, the default behaviour is used.
        position: AABBCorner
            The corner name.

        Raises
        ------
        IndexError
            If any point is out of range.
        ValueError
            If the colour is invalid.
            If the offsets contradict the corner (i.e. the y-offset of any point goes above the top corner).
        """
        cx, cy = corner
        if position.x() == XAxis.LEFT:
            def _x(i: int) -> int:
                if i < 0:
                    raise ValueError("All relative horizontal-offsets should be positive")
                return cx + i
        else:
            def _x(i: int) -> int:
                if i > 0:
                    raise ValueError("All relative horizontal-offsets should be negative")
                return cx + i
        if position.y() == YAxis.TOP:
            def _y(i: int) -> int:
                if i < 0:
                    raise ValueError("All relative vertical-offsets should be positive")
                return cy + i
        else:
            def _y(i: int) -> int:
                if i > 0:
                    raise ValueError("All relative vertical-offsets should be negative")
                return cy + i

        def _abs(xy: _tuple[int, int]) -> _tuple[int, int]:
            return _x(xy[0]), _y(xy[1])

        self.vertices(outline, *map(_abs, (r1, r2, r3, *rr)), fill=fill)

    @OnHasImg.decorate(default=ReferBehavior.REFER)
    def centre(self, centre: _tuple[int, int], outline: np.int_, r1: _tuple[int, int], r2: _tuple[int, int],
               r3: _tuple[int, int], *rr: _tuple[int, int], fill: np.int_ = ...):
        """
        Draw a polygon from the relative positions of the vertices based on the known centre position.

        Parameters
        ----------
        centre: tuple[int, int]
            The centre position.
        outline: int_
            The colour to draw the ellipse's line in. Must be valid for the image.
        r1: tuple[int, int]
            The first vertex offset.
        r2: tuple[int, int]
            The second vertex offset.
        r3: tuple[int, int]
            The third vertex offset.
        *rr: tuple[int, int]
            The remaining vertex offsets.
        fill: int_
            The fill colour. If not defined, the default behaviour is used.

        Raises
        ------
        IndexError
            If any point is out of range.
        ValueError
            If the colour is invalid.
        """
        cx, cy = centre

        def _abs(xy: _tuple[int, int]) -> _tuple[int, int]:
            x, y = xy
            return cx + x, cy + y

        self.vertices(outline, *map(_abs, (r1, r2, r3, *rr)), fill=fill)


class Artist(LineArtist, ArcArtist):
    """
    Concrete subclass able to access all drawing functions.
    """

    @property
    def rect(self) -> RectArtist:
        """
        Public access to the rectangular artist.

        Returns
        -------
        RectArtist
            The artist used to draw rectangles on the image.
        """
        x = RectArtist(self._img)
        x.fill = self.fill
        return x

    @property
    def square(self) -> SquareArtist:
        """
        Public access to the square artist.

        Returns
        -------
        SquareArtist
            The artist used to draw squares on the image.
        """
        return SquareArtist(self.rect)

    @property
    def polygon(self) -> PolygonArtist:
        """
        Public access to the polygon artist.

        Returns
        -------
        PolygonArtist
            The artist used to draw polygons on the image.
        """
        x = PolygonArtist(self._img)
        x.fill = self.fill
        return x
