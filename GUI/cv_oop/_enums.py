"""
Common enumerations used throughout the package.
"""
import enum as _enum

import cv2 as _cv2


class Wrap(_enum.Enum):
    """
    Enumeration that characterises different wrapping behaviour.

    :cvar RAISE: No wrapping, no handling.
    :cvar TRUNCATE: No wrapping, handle by truncating.
    :cvar WRAP: Wrap one loop, handle by truncating and wrapping overflow.
    """
    RAISE = _enum.auto()
    TRUNCATE = _enum.auto()
    WRAP = _enum.auto()


class RGBOrder(_enum.Enum):
    """
    Enumeration that characterises different ways to store RGB values.

    :cvar RGB:
    :cvar RBG:
    :cvar GRB:
    :cvar GBR:
    :cvar BGR:
    :cvar BRG:
    """
    RGB = "rgb"
    RBG = "rbg"
    GRB = "grb"
    GBR = "gbr"
    BGR = "bgr"
    BRG = "brg"


class Colours(_enum.Flag):
    """
    Enumeration that characterises different common colours. They can be combined by |, and filtered by &.

    WHITE and BLACK are shorthands for combining all and none of the colours respectively.
    :cvar RED:
    :cvar GREEN:
    :cvar BLUE:
    :cvar BLACK:
    :cvar WHITE:
    """
    RED = _enum.auto()
    GREEN = _enum.auto()
    BLUE = _enum.auto()

    BLACK = RED & GREEN & BLUE
    WHITE = RED | GREEN | BLUE


class Increase(_enum.Enum):
    """
    Enumeration that characterises different ways to increase a value.

    :cvar TO: Expresses the new value should become the old value.
    :cvar BY: Expresses an addition between the old value and the new value.
    :cvar FACTOR: Expresses a multiplication between the old value and the new value.
    :cvar TO_PERCENTAGE: The same as TO, but the new value is thought to be a percentage of the old value.
    :cvar BY_PERCENTAGE: The same as BY, but the new value is thought to be a percentage of the old value.
    """
    TO = _enum.auto()
    BY = _enum.auto()
    FACTOR = _enum.auto()
    TO_PERCENTAGE = _enum.auto()
    BY_PERCENTAGE = _enum.auto()


class CMode(_enum.Enum):
    """
    Enumeration that characterises different colour modes.

    :cvar GREY:
    :cvar RGB:
    """
    GREY = _enum.auto()
    RGB = _enum.auto()


class CornerAlgorithm(_enum.Enum):
    """
    Enumeration that characterises different ways to capture corners.

    :cvar HARRIS:
    :cvar SHI_TOMASI:
    """
    HARRIS = _enum.auto()
    SHI_TOMASI = _enum.auto()


class Axis(_enum.Flag):
    """
    Enumeration that characterises different ways to flip an image. They can be combined by |, and filtered by &.

    :cvar X:
    :cvar Y:
    """
    X = _enum.auto()
    Y = _enum.auto()


class ThresholdMode(_enum.Enum):
    """
    Enumeration that characterises different thresholding types.

    :cvar GT_MAX_LTE_0: Larger than the threshold value goes to MAX, otherwise 0 (binary).
    :cvar GT_0_LTE_MAX: Larger than the threshold value goes to 0, otherwise MAX (inverted binary).
    :cvar GT_SRC_LTE_0: Larger than the threshold value stays the same, otherwise 0 (to zero).
    :cvar GT_0_LTE_SRC: Larger than the threshold value goes to 0, otherwise stays the same (inverted to zero).
    :cvar GT_THRESH_LTE_SRC: Represents max(threshold value, pixel value) (truncation).
    """
    GT_MAX_LTE_0 = _cv2.THRESH_BINARY
    GT_0_LTE_MAX = _cv2.THRESH_BINARY_INV
    GT_SRC_LTE_0 = _cv2.THRESH_TOZERO
    GT_0_LTE_SRC = _cv2.THRESH_TOZERO_INV
    GT_THRESH_LTE_SRC = _cv2.THRESH_TRUNC


class ThresholdDeterminer(_enum.Enum):
    """
    Enumeration that characterises different ways to algorithmically determine the threshold value.

    :cvar MANUAL:
    :cvar OTSU:
    :cvar TRIANGLE:
    """
    MANUAL = 0
    OTSU = _cv2.THRESH_OTSU
    TRIANGLE = _cv2.THRESH_TRIANGLE


class ThresholdAdaptor(_enum.Enum):
    """
    Enumeration that characterises different algorithms to use in adaptive thresholding.

    :cvar MEAN:
    :cvar GAUSSIAN:
    """
    MEAN = _cv2.ADAPTIVE_THRESH_MEAN_C
    GAUSSIAN = _cv2.ADAPTIVE_THRESH_GAUSSIAN_C


class Transform(_enum.Enum):
    """
    Enumeration that characterises different morphological transformations.

    :cvar ERODE:
    :cvar DILATE:
    :cvar OPEN:
    :cvar CLOSE:
    :cvar GRADIENT:
    :cvar WHITEHAT:
    :cvar BLACKHAT:
    """
    ERODE = _cv2.MORPH_ERODE
    DILATE = _cv2.MORPH_DILATE
    OPEN = _cv2.MORPH_OPEN
    CLOSE = _cv2.MORPH_CLOSE
    GRADIENT = _cv2.MORPH_GRADIENT
    WHITEHAT = _cv2.MORPH_TOPHAT
    BLACKHAT = _cv2.MORPH_BLACKHAT


class Corner(_enum.Enum):
    """
    Enumeration that characterises different places in which a corner can reside.

    Also includes the centre.
    :cvar TOP_LEFT:
    :cvar TOP_MID:
    :cvar TOP_RIGHT:
    :cvar MID_LEFT:
    :cvar MID_MID:
    :cvar MID_RIGHT:
    :cvar BOTTOM_LEFT:
    :cvar BOTTOM_MID:
    :cvar BOTTOM_RIGHT:
    :cvar CENTRE: An alias for MID_MID.
    """
    TOP_LEFT = _enum.auto()
    TOP_MID = _enum.auto()
    TOP_RIGHT = _enum.auto()
    MID_LEFT = _enum.auto()
    MID_MID = _enum.auto()
    MID_RIGHT = _enum.auto()
    BOTTOM_LEFT = _enum.auto()
    BOTTOM_MID = _enum.auto()
    BOTTOM_RIGHT = _enum.auto()

    CENTRE = MID_MID
