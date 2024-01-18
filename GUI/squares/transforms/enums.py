"""
Important enumerations for transforms
"""

import enum as _enum

import cv2 as _cv2


class ThresholdTypes(_enum.Enum):
    """
    The types of thresholding that can be done

    :cvar GT_MAX_LTE_0: goes to a maximum value for above the threshold, 0 otherwise (binary thresholding)
    :cvar GT_0_LTE_MAX: goes to 0 for above the threshold, a maximum value otherwise (inverted binary thresholding)
    :cvar GT_THRESH_LTE_SRC: min(threshold, source) (truncating thresholding)
    :cvar GT_SRC_LTE_0: stays the same for above the threshold, 0 otherwise (to zero thresholding)
    :cvar GT_0_LTE_SRC: goes to 0 for above the threshold, stays the same otherwise (inverted to zero thresholding)
    """
    GT_MAX_LTE_0 = _cv2.THRESH_BINARY
    GT_0_LTE_MAX = _cv2.THRESH_BINARY_INV
    GT_THRESH_LTE_SRC = _cv2.THRESH_TRUNC
    GT_SRC_LTE_0 = _cv2.THRESH_TOZERO
    GT_0_LTE_SRC = _cv2.THRESH_TOZERO_INV


class ThresholdAdaptors(_enum.Enum):
    """
    Differing adaptive thresholding methods

    :cvar MEAN:
    :cvar GAUSSIAN:
    """
    MEAN = _cv2.ADAPTIVE_THRESH_MEAN_C
    GAUSSIAN = _cv2.ADAPTIVE_THRESH_GAUSSIAN_C


class ThresholdDeterminers(_enum.Enum):
    """
    Differing global threshold determiners

    :cvar OTSU:
    :cvar TRIANGLE:
    """
    OTSU = _cv2.THRESH_OTSU
    TRIANGLE = _cv2.THRESH_TRIANGLE


class TransformModes(_enum.Enum):
    """
    Different ways to perform transformations

    :cvar AFFINE:
    :cvar PERSPECTIVE:
    """
    AFFINE = _cv2.getAffineTransform, _cv2.warpAffine
    PERSPECTIVE = _cv2.getPerspectiveTransform, _cv2.warpPerspective


class Morphs(_enum.Enum):
    """
    Different morphological transformations that can be performed

    :cvar ERODE:
    :cvar DILATE:
    :cvar OPEN:
    :cvar CLOSE:
    :cvar GRADIENT:
    :cvar WHITEHAT:
    :cvar BLACKHAT:
    """
    ERODE = 0
    DILATE = 1
    OPEN = _cv2.MORPH_OPEN
    CLOSE = _cv2.MORPH_CLOSE
    GRADIENT = _cv2.MORPH_GRADIENT
    WHITEHAT = _cv2.MORPH_TOPHAT
    BLACKHAT = _cv2.MORPH_BLACKHAT
