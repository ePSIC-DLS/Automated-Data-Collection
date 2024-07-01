from enum import Enum as _Base, auto as _member
import cv2 as _image


class ReferBehavior(_Base):
    """
    Enumeration to represent the types of behaviour that can be applied to a mutable attribute.

    Members
    -------
    REFER
        Any changes will affect the parent.
    COPY
        Any changes will not affect the parent.
    """
    REFER = _member()
    COPY = _member()


class Channel(_Base):
    """
    Enumeration to represent the colour channels in a colour image.

    Members
    -------
    R
    G
    B
    """
    R = _member()
    G = _member()
    B = _member()


class ColourConvert(_Base):
    """
    Enumeration to represent the different ways to convert a multimodal image to bimodal.

    Members
    -------
    TO_BG
        Invalid colours go to the background colour.
    TO_FG
        Invalid colours go to the foreground colour.
    """
    TO_BG = _member()
    TO_FG = _member()


class XAxis(_Base):
    """
    Enumeration to represent the different x-axis extremes.

    Members
    -------
    LEFT
    RIGHT
    """
    LEFT = _member()
    RIGHT = _member()


class YAxis(_Base):
    """
    Enumeration to represent the different y-axis extremes.

    Members
    -------
    TOP
    BOTTOM
    """
    TOP = _member()
    BOTTOM = _member()


class AABBCorner(_Base):
    """
    Enumeration to represent the different corners of an Axis-Aligned Bounding-Box.

    Each corner can be formatted using 'l' for lowercase, 'u' for uppercase, 't' for titlecase, per axis side.
    Therefore, a format code of 'l' is identical to a format code for 'll', and both will convert the x-axis and the
    y-axis to lowercase.

    Members
    -------
    TOP_LEFT
    TOP_RIGHT
    BOTTOM_LEFT
    BOTTOM_RIGHT
    """
    TOP_LEFT = _member()
    TOP_RIGHT = _member()
    BOTTOM_LEFT = _member()
    BOTTOM_RIGHT = _member()

    def __format__(self, format_spec: str) -> str:
        if format_spec == "":
            return str(self)
        invalid = ValueError(f"AABBCorner has no format for {format_spec!r}")
        chars = len(format_spec)
        if chars == 1:
            return format(self, f"{format_spec}{format_spec}")
        elif chars == 2:
            build = ""
            for comp, mod in zip(self.name.split("_"), format_spec):
                if mod == "l":
                    build = f"{build}{comp.lower()}"
                elif mod == "t":
                    build = f"{build}{comp.title()}"
                elif mod == "u":
                    build = f"{build}{comp.upper()}"
                else:
                    raise invalid
            return build
        raise invalid

    def x(self) -> XAxis:
        """
        Find the x-axis corner of the Axis-Aligned Bounding-Box.

        Returns
        -------
        XAxis
            The corner in the horizontal axis.
        """
        if "LEFT" in self.name:
            return XAxis.LEFT
        return XAxis.RIGHT

    def y(self) -> YAxis:
        """
        Find the y-axis corner of the Axis-Aligned Bounding-Box.

        Returns
        -------
        YAxis
            The corner in the vertical axis.
        """
        if "TOP" in self.name:
            return YAxis.TOP
        return YAxis.BOTTOM


class FillBehaviour(_Base):
    """
    Enumeration to represent the various default values for the fill of a drawn shape.

    Members
    -------
    OUTLINE
        Fill by the foreground (outline) colour.
    NONE
        No fill.
    FIXED
        The shape will be filled with a known colour.
    """
    OUTLINE = _member()
    NONE = _member()
    FIXED = _member()


class Equality(_Base):
    """
    Enumeration to represent the ways thresholding behaviour will handle equality.

    Members
    -------
    LT
        Will perform the same as the 'less than' behaviour.
    GT
        Will perform the same as the 'greater than' behaviour.
    """
    LT = _member()
    GT = _member()


class MorphologicalShape(_Base):
    """
    Enumeration to represent the different morphological shapes.

    Members
    -------
    RECT
    CROSS
    ELLIPSE
    """
    RECT = _member()
    CROSS = _member()
    ELLIPSE = _member()

    def to_cv2(self) -> int:
        """
        Method to convert a member to the cv2 equivalent.

        Returns
        -------
        int
            The cv2 equivalent of this kernel shape.
        """
        if self == self.RECT:
            return _image.MORPH_RECT
        elif self == self.CROSS:
            return _image.MORPH_CROSS
        elif self == self.ELLIPSE:
            return _image.MORPH_ELLIPSE
