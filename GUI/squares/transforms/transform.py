"""
Allows transformation of images
"""
from __future__ import annotations
import cv2
import numpy as np

from .enums import *
from ..image import Image


class Transform:
    """
    Namespace class for transforms
    """

    @staticmethod
    def regular(img: Image, mode: TransformModes, input_coords: list[tuple[int, int]],
                output_coords: list[tuple[int, int]]) -> Image:
        """
        Performs non-morphological transforms
        :param img: The image to transform
        :param mode: The type of transform
        :param input_coords: The reference points in the old image
        :param output_coords: The reference points in the transformed image
        :return: The transformed image
        :raise ValueError: If number of reference points is unequal, or if there's too few
        """
        inlen = len(input_coords)
        if inlen != len(output_coords):
            raise ValueError("Must have input coords same length as output coords")
        if mode == TransformModes.AFFINE and inlen != 3:
            raise ValueError("Affine transforms have 3 reference points")
        elif mode == TransformModes.PERSPECTIVE and inlen != 4:
            raise ValueError("Perspective transforms must have 4 reference points")
        transform, warp = mode.value
        size = tuple(reversed(img.shape))
        matrix = transform(np.float32(input_coords), np.float32(output_coords))
        return Image(warp(img.image, matrix, size))

    @staticmethod
    def morphological(img: Image, mode: Morphs, kernel_shape: int, kernel_size: tuple[int, int], *, kernel_scale=1,
                      iterations=1) -> Image:
        """
        Performs morphological transforms
        :param img: The image to transform
        :param mode: The morphological transform to do
        :param kernel_shape: The shape of the kernel (see cv2 Morph Shapes)
        :param kernel_size: The size of the kernel
        :param kernel_scale: The non-zero value in the kernel (as it's usually normalised)
        :param iterations: The number of iterations to perform
        :return: The transformed Image
        """
        kernel = cv2.getStructuringElement(kernel_shape, kernel_size) * kernel_scale
        if mode == Morphs.ERODE:
            res = cv2.erode(img.image, kernel, iterations=iterations)
        elif mode == Morphs.DILATE:
            res = cv2.dilate(img.image, kernel, iterations=iterations)
        else:
            res = cv2.morphologyEx(img.image, mode.value, kernel, iterations=iterations)
        return Image(res)
