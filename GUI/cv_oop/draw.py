"""
Various functions for drawing on an image.

All co-ordinates are cartesian, and each function will provide an image if not provided.
"""
import typing

import cv2
import numpy as np

from . import Image, Colour
from ._enums import *


def line(pt1: tuple[int, int], pt2: tuple[int, int], colour: Colour, img: Image = None) -> Image:
    """
    Draw a line onto the specified image.

    :param pt1: The first point on the line.
    :param pt2: The second point on the line.
    :param colour: The colour of the line.
    :param img: The image to draw on. If not provided, it will generate an image large enough.
    :return: A new image with the line drawn on it.
    :raises ValueError: If the colour isn't greyscale but the image is.
    :raises IndexError: If any point in the shape is a negative number.
    """
    if any(pos < 0 for pos in (*pt1, *pt2)):
        raise IndexError("Cannot create line at negative indices")
    if img is None:
        img = Image.blank((max(pt1[1], pt2[1]) + 1, max(pt1[0], pt2[0]) + 1))
    if img.colour_mode == CMode.GREY and not colour.is_grey():
        raise ValueError("Can only draw greyscale colours on greyscale images")
    new = cv2.line(img.get_channeled_image(), pt1, pt2, colour.all(img.colour_order))
    return img.from_(new)


class Rect:
    """
    Namespace class to have different rectangle drawing methods.
    """

    @staticmethod
    def corners(tl: tuple[int, int], br: tuple[int, int], colour: Colour, img: Image = None, *,
                fill: Colour = ...) -> Image:
        """
        Draw a rectangle by specifying the top left and bottom right co-ordinates.

        :param tl: The top left co-ordinate.
        :param br: The bottom right co-ordinate.
        :param colour: The colour of the outline.
        :param img: The image to draw on. If not provided, it will generate an image large enough.
        :param fill: The fill colour. Defaults to the same colour as the outline. Specify None for no fill.
        :return: A new image with the rectangle drawn on.
        :raises ValueError: If the colour isn't greyscale but the image is.
        :raises IndexError: If any point in the shape is a negative number.
        """
        tl = (min(tl[0], br[0]), min(tl[1], br[1]))
        br = (max(tl[0], br[0]), max(tl[1], br[1]))
        if any(pos < 0 for pos in (*tl, *br)):
            raise IndexError("Cannot create rectangle at negative indices")
        if img is None:
            img = Image.blank((br[1] + 1, br[0] + 1))
        if img.colour_mode == CMode.GREY and not colour.is_grey():
            raise ValueError("Can only draw greyscale colours on greyscale images")
        if fill is ...:
            fill = colour
        new = cv2.rectangle(img.get_channeled_image(), tl, br, colour.all(img.colour_order))
        if fill is not None:
            new = cv2.rectangle(new, (tl[0] + 1, tl[1] + 1), (br[0] - 1, br[1] - 1), fill.all(img.colour_order), -1)
        return img.from_(new)

    @staticmethod
    def size(pos: tuple[int, int], size: tuple[int, int], colour: Colour, img: Image = None,
             *, fill: Colour = ..., placement=Corner.TOP_LEFT) -> Image:
        """
        Draw a rectangle by specifying a corner and the size.

        :param pos: The position of the corner.
        :param size: The size of the rectangle in the form (width, height).
        :param colour: The colour of the outline.
        :param img: The image to draw on. If not provided, it will generate an image large enough.
        :param fill: The fill colour. Defaults to the same colour as the outline. Specify None for no fill.
        :param placement: The position of the corner.
        :return: A new image with the rectangle drawn on.
        :raises ValueError: If the colour isn't greyscale but the image is.
        :raises IndexError: If any point in the shape is a negative number.
        """
        if placement == Corner.TOP_LEFT:
            tl, br = pos, (pos[0] + size[0], pos[1] + size[1])
        elif placement == Corner.TOP_MID:
            tl, br = (pos[0] - size[0] // 2, pos[1]), (pos[0] + size[0] // 2, pos[1] + size[1])
        elif placement == Corner.TOP_RIGHT:
            tl, br = (pos[0] - size[0], pos[1]), (pos[0], pos[1] + size[1])
        elif placement == Corner.MID_LEFT:
            tl, br = (pos[0], pos[1] - size[1] // 2), (pos[0] + size[0], pos[1] + size[1] // 2)
        elif placement == Corner.MID_MID:
            tl, br = (pos[0] - size[0] // 2, pos[1] - size[1] // 2), (pos[0] + size[0] // 2, pos[1] + size[1] // 2)
        elif placement == Corner.MID_RIGHT:
            tl, br = (pos[0], pos[1] - size[1] // 2), (pos[0] + size[0], pos[1] + size[1] // 2)
        elif placement == Corner.BOTTOM_LEFT:
            tl, br = (pos[0], pos[1] - size[1]), (pos[0] + size[0], pos[1])
        elif placement == Corner.BOTTOM_MID:
            tl, br = (pos[0] - size[0] // 2, pos[1] - size[1]), (pos[0] + size[0] // 2, pos[1])
        else:
            tl, br = (pos[0] - size[0], pos[1] - size[1]), pos
        return Rect.corners(tl, br, colour, img, fill=fill)


rect = Rect.size


def square(pos: tuple[int, int], size: int, colour: Colour, img: Image = None,
           *, fill: Colour = ..., placement=Corner.TOP_LEFT) -> Image:
    """
    Shortcut method for drawing squares.

    See help(rect) for more information.
    """
    return rect(pos, (size, size), colour, img, fill=fill, placement=placement)


def arc(centre: tuple[int, int], radius: tuple[int, int], colour: Colour, extent: int, start=0, img: Image = None, *,
        fill: Colour = ...) -> Image:
    """
    Draw a section of an ellipse.

    :param centre: The arc's centre.
    :param radius: The radius of the arc in (width, height).
    :param colour: The colour of the outline.
    :param extent: How many degrees the arc should cover. Using 360 will have the same effect as calling 'ellipse'.
    :param start: The starting angle (in degrees).
    :param img: The image to draw on. If not provided, it will generate an image large enough.
    :param fill: The fill colour. Defaults to the same colour as the outline. Specify None for no fill.
    :return: A new image with the arc drawn.
    :raises ValueError: If the colour isn't greyscale but the image is, or if start or extent is invalid.
    :raises IndexError: If any point in the shape is a negative number.
    """
    start, end = start, start + extent
    if img is None:
        img = Image.blank((2 * radius[1] + 1, 2 * radius[0] + 1))
    if img.colour_mode == CMode.GREY and not colour.is_grey():
        raise ValueError("Can only draw greyscale colours on greyscale images")
    elif start < 0 or extent <= 0:
        raise ValueError("Extent and start must be non-negative")
    elif start + extent > 360:
        raise ValueError("Internal angle of ellipse only has 360 degrees")
    if any(pos < 0 for pos in (*centre, *radius)):
        raise IndexError("Cannot create ellipse at negative indices")
    if fill is ...:
        fill = colour
    new = cv2.ellipse(img.get_channeled_image(), centre, radius, extent, start, end, colour.all(img.colour_order))
    if fill is not None:
        fill_rgb = fill.all(img.colour_order)
        new = cv2.ellipse(new, centre, (radius[0] - 1, radius[1] - 1), extent, start, end, fill_rgb, -1)
        new = cv2.ellipse(new, (centre[0] + 1, centre[1]), (radius[0] - 1, radius[1] - 1), extent, start, end, fill_rgb)
        new = cv2.ellipse(new, (centre[0] - 1, centre[1]), (radius[0] - 1, radius[1] - 1), extent, start, end, fill_rgb)
        new = cv2.ellipse(new, (centre[0], centre[1] + 1), (radius[0] - 1, radius[1] - 1), extent, start, end, fill_rgb)
        new = cv2.ellipse(new, (centre[0], centre[1] - 1), (radius[0] - 1, radius[1] - 1), extent, start, end, fill_rgb)
    return img.from_(new)


def ellipse(centre: tuple[int, int], radius: tuple[int, int], colour: Colour, img: Image = None, *,
            fill: Colour = ...) -> Image:
    """
    Draws an ellipse (can be thought of as an arc extending from 0 to 360 degrees).

    :param centre: The centre of the ellipse.
    :param radius: The radius of the ellipse in the form (width, height).
    :param colour: The colour of the outline.
    :param img: The image to draw on. If not provided, it will generate an image large enough.
    :param fill: The fill colour. Defaults to the same colour as the outline. Specify None for no fill.
    :return: A new image with the ellipse drawn in.
    :raises ValueError: If the colour isn't greyscale but the image is.
    :raises IndexError: If any point in the shape is a negative number.
    """
    return arc(centre, radius, colour, 360, img=img, fill=fill)


def circle(centre: tuple[int, int], radius: int, colour: Colour, img: Image = None, *, fill: Colour = ...) -> Image:
    """
    Shortcut method for drawing circles.

    See help(ellipse) for more information.
    """
    return ellipse(centre, (radius, radius), colour, img, fill=fill)


def polygon(centre: tuple[int, int], colour: Colour, off1: tuple[int, int], off2: tuple[int, int],
            off3: tuple[int, int], *off: tuple[int, int], img: Image = None, fill: Colour = ...) -> Image:
    """
    Draws a polygon by specifying the centre and the relative offsets of the vertices.

    :param centre: The centre of the polygon.
    :param colour: The colour of the outline.
    :param off1: The first vertex offset.
    :param off2: The second vertex offset.
    :param off3: The third vertex offset.
    :param off: Any remaining vertex offsets.
    :param img: The image to draw on. If not provided, it will generate an image large enough.
    :param fill: The fill colour. Defaults to the same colour as the outline. Specify None for no fill.
    :return: A new image with the polygon drawn.
    :raises ValueError: If the colour isn't greyscale but the image is.
    :raises IndexError: If any point in the shape is a negative number.
    """
    offsets = np.array((off1, off2, off3, *off))
    points = np.array([(centre[0] + offset[0], centre[1] + offset[1]) for offset in offsets], np.int32)
    if np.any(points < 0):
        raise IndexError("Cannot create polygon at negative indices")
    inner_points = points.copy()
    inner_points[np.where(offsets <= 0)] += 1
    inner_points[np.where(offsets > 0)] -= 1
    left = min(points[:, 0])
    right = max(points[:, 0])
    top = min(points[:, 1])
    bottom = max(points[:, 1])
    if img is None:
        img = Image.blank(((right - left) + 1, (bottom - top) + 1))
    if img.colour_mode == CMode.GREY and not colour.is_grey():
        raise ValueError("Can only draw greyscale colours on greyscale images")
    if fill is ...:
        fill = colour
    new = cv2.polylines(img.get_channeled_image(), points.reshape(-1, 1, 2), True, colour.all(img.colour_order))
    if fill is not None:
        new = cv2.polylines(new, inner_points.reshape(-1, 1, 2), True, fill.all(img.colour_order), -1)
    return img.from_(new)


class Drawing:
    """
    Class to wrap an image up such that drawings can be applied to an instance variable.

    Drawings made won't affect the original image.

    :var Image _img: The captured image.
    """

    @property
    def image(self) -> Image:
        """
        Public access to the image.

        :return: The captured image.
        """
        return self._img

    def __init__(self, img: Image):
        self._img = img

    def _update(self):
        pass

    def line(self, pt1: tuple[int, int], pt2: tuple[int, int], colour: Colour) -> "Drawing":
        """
        Wrapper for the 'line' function. Will update the image accordingly.

        See help(line) for more information.
        :return: The instance itself so drawings can be stacked.
        """
        self._img = line(pt1, pt2, colour, self._img)
        self._update()
        return self

    def rect(self, pos: tuple[int, int], size: tuple[int, int], colour: Colour, *, fill: Colour = ...,
             placement=Corner.TOP_LEFT) -> "Drawing":
        """
        Wrapper for the 'rect' function. Will update the image accordingly.

        See help(rect) for more information.
        :return: The instance itself so drawings can be stacked.
        """
        self._img = rect(pos, size, colour, self._img, fill=fill, placement=placement)
        self._update()
        return self

    def square(self, pos: tuple[int, int], size: int, colour: Colour, *, fill: Colour = ...,
               placement=Corner.TOP_LEFT) -> "Drawing":
        """
        Wrapper for the 'square' function. Will update the image accordingly.

        See help(square) for more information.
        :return: The instance itself so drawings can be stacked.
        """
        self._img = square(pos, size, colour, self._img, fill=fill, placement=placement)
        self._update()
        return self

    def arc(self, centre: tuple[int, int], radius: tuple[int, int], colour: Colour, extent: int, start=0, *,
            fill: Colour = ...) -> "Drawing":
        """
        Wrapper for the 'arc' function. Will update the image accordingly.

        See help(arc) for more information.
        :return: The instance itself so drawings can be stacked.
        """
        self._img = arc(centre, radius, colour, extent, start, self._img, fill=fill)
        self._update()
        return self

    def ellipse(self, centre: tuple[int, int], radius: tuple[int, int], colour: Colour, *, fill: Colour = ...) \
            -> "Drawing":
        """
        Wrapper for the 'ellipse' function. Will update the image accordingly.

        See help(ellipse) for more information.
        :return: The instance itself so drawings can be stacked.
        """
        self._img = ellipse(centre, radius, colour, self._img, fill=fill)
        self._update()
        return self

    def circle(self, centre: tuple[int, int], radius: int, colour: Colour, *, fill: Colour = ...) -> "Drawing":
        """
        Wrapper for the 'circle' function. Will update the image accordingly.

        See help(circle) for more information.
        :return: The instance itself so drawings can be stacked.
        """
        self._img = circle(centre, radius, colour, self._img, fill=fill)
        self._update()
        return self

    def polygon(self, centre: tuple[int, int], colour: Colour, off1: tuple[int, int], off2: tuple[int, int],
                off3: tuple[int, int], *off: tuple[int, int], fill: Colour = ...) -> "Drawing":
        """
        Wrapper for the 'polygon' function. Will update the image accordingly.

        See help(polygon) for more information.
        :return: The instance itself so drawings can be stacked.
        """
        self._img = polygon(centre, colour, off1, off2, off3, *off, img=self._img, fill=fill)
        self._update()
        return self

    def pipeline(self, *commands: dict[str, typing.Any]):
        """
        Shortcut for applying various commands one after the other.

        Each command must have a 'name' key for the function to apply.
        :param commands: Keyword arguments to pass to each step individually.
        :raises KeyError: If a command doesn't have a 'name' key. Will do this check prior to any function calls.
        """
        fns = [getattr(self, kwargs.pop("name")) for kwargs in commands]
        for fn, kwargs in zip(fns, commands):
            if fn is self.polygon:
                try:
                    fn(kwargs["centre"], kwargs["colour"], kwargs["off1"], kwargs["off2"], kwargs["off3"],
                       *kwargs["off"], fill=kwargs["fill"])
                except KeyError as e:
                    raise TypeError(f"{fn} missing required argument {e.args[0]!r}") from None
            fn(**kwargs)
