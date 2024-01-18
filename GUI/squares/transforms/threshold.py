"""
Allows thresholding of images
"""
from __future__ import annotations
import cv2

from .enums import *
from ..image import Image


class Threshold:
    """
    Namespace class for thresholds
    """

    @staticmethod
    def global_(img: Image, threshold: int, mode: ThresholdTypes, *, maximum: int = None,
                determiner: ThresholdDeterminers = None) -> Image:
        """
        Performs global thresholding
        :param img: The image to threshold
        :param threshold: The threshold value to use
        :param mode: The type of thresholding to perform
        :param maximum: The highest value (only applicable with binary thresholding)
        :param determiner: The determiner to use for the global threshold
        :return: The image after thresholding
        :raise AttributeError: If Image is not black and white
        :raise ValueError: If maximum is provided when not needed or not provided when needed
        :raise ArithmeticError: If maximum (when provided) or threshold are out of bounds (<0 or >255)
        """
        if img.colour_mode != Image.CMODE.BW:
            raise AttributeError("Can only threshold greyscale images")
        elif mode in (ThresholdTypes.GT_MAX_LTE_0, ThresholdTypes.GT_0_LTE_MAX):
            if maximum is None:
                raise ValueError("Binary thresholding needs a maximum")
            elif not (0 <= maximum <= 255):
                raise ArithmeticError("Maximum must be between 0 and 255")
        elif (mode in (ThresholdTypes.GT_THRESH_LTE_SRC, ThresholdTypes.GT_SRC_LTE_0, ThresholdTypes.GT_0_LTE_SRC)
              and maximum is not None):
            raise ValueError("Non-binary thresholding does not need a maximum")
        elif not (0 <= threshold <= 255):
            raise ArithmeticError("Threshold must be between 0 and 255")
        _, img = cv2.threshold(img.image, threshold, maximum or 0,
                               mode.value | (0 if determiner is None else determiner.value))
        return Image(img)

    @staticmethod
    def adaptive(img: Image, mode: ThresholdAdaptors, block: int, c: int, handler: ThresholdTypes, *,
                 maximum: int = None) -> "Image":
        """
        Performs adaptive thresholding
        :param img: The image to threshold
        :param mode: The adaptive thresholding
        :param block: The size of the block to use
        :param c: The constant to use
        :param handler:  The type of thresholding to perform
        :param maximum: The highest value (only applicable with binary thresholding)
        :return: The image after thresholding
        :raise AttributeError: If Image is not black and white
        :raise ValueError: If maximum is provided when not needed or not provided when needed
        :raise ArithmeticError: If maximum (when provided) is out of bounds (<0 or >255)
        """
        if img.colour_mode != Image.CMODE.BW:
            raise AttributeError("Can only threshold greyscale images")
        elif handler in (ThresholdTypes.GT_MAX_LTE_0, ThresholdTypes.GT_0_LTE_MAX):
            if maximum is None:
                raise ValueError("Binary thresholding needs a maximum")
            elif not (0 <= maximum <= 255):
                raise ArithmeticError("Maximum must be between 0 and 255")
        elif (handler in (ThresholdTypes.GT_THRESH_LTE_SRC, ThresholdTypes.GT_SRC_LTE_0, ThresholdTypes.GT_0_LTE_SRC)
              and maximum is not None):
            raise ValueError("Non-binary thresholding does not need a maximum")
        return Image(cv2.adaptiveThreshold(img.image, maximum or 0, mode.value, handler.value, blockSize=block, C=c))
