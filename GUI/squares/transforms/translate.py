"""
Allows translation of images
"""
from __future__ import annotations
import cv2
import numpy as np

from ..image import Image


class Translate:
    """
    Namespace class for translations
    """

    @staticmethod
    def image(img: Image, x: int, y: int) -> Image:
        """
        Translates an image
        :param img: The image to translate
        :param x: horizontal displacement
        :param y: vertical displacement
        :return: The translated image
        """
        size = tuple(reversed(img.shape))
        matrix = np.float32(((1, 0, x), (0, 1, y)))
        return Image(cv2.warpAffine(img.image, matrix, size))
