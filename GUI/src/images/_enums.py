from enum import Enum as _Base, auto as _member, Flag as _Bitwise
from . import _aliases
import cv2 as _image
from typing import Tuple as _tuple


class WrapMode(_Base):
    """
    Enumeration to represent the different ways in which colour wrapping works.

    This allows for a value that overflows the channel to be handled in different ways.

    Members
    -------
    TRUNCATE
        Will truncate the channel to be capped at 255.
    SPILL
        Will let the remainder spill into the next channel.
    OVERFLOW
        Will act like bitstream overflowing - the final value is the original value mod 255.
    """
    TRUNCATE = _member()
    SPILL = _member()
    OVERFLOW = _member()


class ColourMode(_Base):
    """
    Enumeration to represent the different bit-depths for a colour.

    Members
    -------
    GREYSCALE
        8-bit depth, represents a greyscale colour (can only be 0 - 255).
    FULLDEPTH
        24-bit depth (3 8-bit channels), to allow for any RGB combination.
    """
    GREYSCALE = _member()
    FULLDEPTH = _member()


class RGBOrder(_Base):
    """
    Enumeration to represent the permutations of 'RGB'.

    Members
    -------
    RGB

    RBG

    GBR

    GRB

    BRG

    BGR
    """
    RGB = _member()
    RBG = _member()
    GBR = _member()
    GRB = _member()
    BRG = _member()
    BGR = _member()

    def items(self) -> _tuple[_aliases.Channel, _aliases.Channel, _aliases.Channel]:
        """
        Method to extract the characters in the order.

        Returns
        -------
        tuple[Channel, Channel, Channel]
            The characters in the order. The order of the tuple is the permutation of the channels.
        """
        if self == RGBOrder.RGB:
            return "r", "g", "b"
        elif self == RGBOrder.RBG:
            return "r", "b", "g"
        elif self == RGBOrder.GBR:
            return "g", "b", "r"
        elif self == RGBOrder.GRB:
            return "g", "r", "b"
        elif self == RGBOrder.BRG:
            return "b", "r", "g"
        else:
            return "b", "g", "r"

    def next(self) -> _tuple[_aliases.Channel, _aliases.Channel, _aliases.Channel]:
        """
        Method to extract the characters of the *next* permutation.

        The next permutation takes the first channel and shifts it to the end.

        Returns
        -------
        tuple[Channel, Channel, Channel]
            The characters in the next order. The order of the tuple is the permutation of the channels.
        """
        if self == RGBOrder.RGB:
            member = RGBOrder.GBR
        elif self == RGBOrder.RBG:
            member = RGBOrder.BGR
        elif self == RGBOrder.GBR:
            member = RGBOrder.BRG
        elif self == RGBOrder.GRB:
            member = RGBOrder.RBG
        elif self == RGBOrder.BRG:
            member = RGBOrder.RGB
        else:
            member = RGBOrder.GRB
        return member.items()

    def index(self, channel: _aliases.Channel) -> int:
        """
        Returns the index of the channel in the order.

        Parameters
        ----------
        channel: Channel
            The channel to index.

        Returns
        -------
        int
            The index of the channel provided.
        """
        return self.name.lower().index(channel)


class KnownColour(_Bitwise):
    """
    Bitwise enumeration to represent the colour constants known.

    Members
    -------
    RED

    GREEN

    BLUE
    """
    RED = _member()
    GREEN = _member()
    BLUE = _member()


class AdaptiveThresholdAlgorithm(_Base):
    """
    Enumeration to represent the threshold algorithms used for adaptive thresholding.

    Members
    -------
    GAUSSIAN

    MEAN

    """
    GAUSSIAN = _member()
    MEAN = _member()

    def to_cv2(self) -> int:
        """
        Method to convert a member to the cv2 equivalent.

        Returns
        -------
        int
            The cv2 equivalent of this adaptive threshold algorithm.
        """
        if self == self.GAUSSIAN:
            return _image.ADAPTIVE_THRESH_GAUSSIAN_C
        elif self == self.MEAN:
            return _image.ADAPTIVE_THRESH_MEAN_C


class ThresholdAlgorithm(_Base):
    """
    Enumeration to represent the different threshold algorithms used for finding the ideal threshold value.

    Members
    -------
    OTSU

    TRIANGLE

    """
    OTSU = _member()
    TRIANGLE = _member()

    def to_cv2(self) -> int:
        """
        Method to convert a member to the cv2 equivalent.

        Returns
        -------
        int
            The cv2 equivalent of this threshold algorithm.
        """
        if self == self.OTSU:
            return _image.THRESH_OTSU
        elif self == self.TRIANGLE:
            return _image.THRESH_TRIANGLE


class MorphologicalTransform(_Base):
    """
    Enumeration to represent the different morphological transformations that can be applied to a greyscale image.

    Members
    -------
    ERODE
        Perform erosion to an image, which is the thinning of the foreground.
    DILATE
        Perform dilation to an image, which is the thickening of the foreground.
    OPEN
        Perform erosion then dilation to an image, which will remove small noises.
    CLOSE
        Perform dilation then erosion to an image, which will close small foreground holes.
    GRADIENT
        Find the difference between the dilation and the erosion of an image.
    WHITEHAT
        Find the difference between the image and the opened version.
    BLACKHAT
        Find the difference between the closing version and the image.
    """
    ERODE = _member()
    DILATE = _member()
    OPEN = _member()
    CLOSE = _member()
    GRADIENT = _member()
    WHITEHAT = _member()
    BLACKHAT = _member()

    def to_cv2(self) -> int:
        """
        Method to convert a member to the cv2 equivalent.

        Returns
        -------
        int
            The cv2 equivalent of this morphological transformation.
        """
        if self == self.ERODE:
            return _image.MORPH_ERODE
        elif self == self.DILATE:
            return _image.MORPH_DILATE
        elif self == self.OPEN:
            return _image.MORPH_OPEN
        elif self == self.CLOSE:
            return _image.MORPH_CLOSE
        elif self == self.GRADIENT:
            return _image.MORPH_GRADIENT
        elif self == self.WHITEHAT:
            return _image.MORPH_TOPHAT
        elif self == self.BLACKHAT:
            return _image.MORPH_BLACKHAT


class MorphologicalShape(_Base):
    """
    Enumeration to represent the different kernel shapes for morphological transformations.

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


class AABBCorner(_Base):
    """
    Enumeration to represent the different corners of an Axis Aligned Bounding Box (AABB).

    Each corner can be formatted using 'l', 't', 'u' for representing lower, title, and upper case respectively.
    When only one is provided, it is applied to each word (separated by underscore in the name); when two are provided,
    each one is applied to its word.

    Members
    -------
    TOP_LEFT

    TOP_RIGHT

    BOTTOM_LEFT

    BOTTOM_RIGHT

    Examples
    --------
    >>>f"{AABBCorner.TOP_LEFT:l}"
        top left
    >>>f"{AABBCorner.TOP_LEFT:ut}"
        TOP Left
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

    def x(self) -> _aliases.XAxis:
        """
        Method to determine the X point of the corner.

        Returns
        -------
        XAxis
            The X point of the corner.
        """
        if "LEFT" in self.name:
            return "left"
        return "right"

    def y(self) -> _aliases.YAxis:
        """
        Method to determine the Y point of the corner.

        Returns
        -------
        YAxis
            The Y point of the corner.
        """
        if "TOP" in self.name:
            return "top"
        return "bottom"


class ReferenceBehaviour(_Base):
    """
    Enumeration to represent the different behaviour of reference functions.

    Members
    -------
    REFER

    COPY

    """
    REFER = _member()
    COPY = _member()


class CrossShape(_Base):
    """
    Enumeration to represent the different shapes for drawing a cross.

    Members
    -------
    DIAGONAL
        A traditional cross, the 'X' shape.
    ALIGNED
        An aligned cross, the '+' shape.
    """
    DIAGONAL = _member()
    ALIGNED = _member()


class BimodalBehaviour(_Base):
    """
    Enumeration to represent the different ways of handling invalid colours in a bimodal conversion.

    Members
    -------
    BG

    FG

    """
    BG = _member()
    FG = _member()
