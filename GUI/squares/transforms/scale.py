"""
Allows scaling of images and ROIs
"""
from __future__ import annotations
import cv2

from .. import ROIs
from ..image import Image


class Scale:
    """
    Namespace class for scaling
    """

    @staticmethod
    def image(img: Image, factor: tuple[int, int], *, force_interpolation: int = None) -> Image:
        """
        Allows scaling of images
        :param img: The image to scale
        :param factor: The x-y scale factor
        :param force_interpolation: Interpolation to use (if left as None, will automatically assume the best flag)
        :return: The scaled image
        :raise ValueError: If factor is 0 in any direction or if interpolation is not a correct value
        """
        if force_interpolation not in (None, cv2.INTER_LINEAR, cv2.INTER_AREA, cv2.INTER_CUBIC):
            raise ValueError("Expected interpolation flag to be INTER_LINEAR, INTER_AREA, INTER_CUBIC or None")
        elif not all(factor):
            raise ValueError("Cannot scale by 0")
        if force_interpolation is None:
            force_interpolation = cv2.INTER_LINEAR if all(f > 0 for f in factor) else cv2.INTER_AREA
        size = tuple(map(lambda x, y: x * y, img.shape, (factor[1], factor[0])))
        return Image(cv2.resize(img.image, size, interpolation=force_interpolation))

    @staticmethod
    def region(region: ROIs.ROI, factor: tuple[int, int]) -> ROIs.ROI:
        """
        Allows scaling of ROIs
        :param region: The ROI to scale
        :param factor: The x-y scale factor
        :return: The scaled ROI
        """
        gx, gy = factor
        if isinstance(region, ROIs.Rect):
            x, y = region.size
            return ROIs.Rect(x * gx, y * gy, on=region.data)
        elif isinstance(region, ROIs.Ellipse):
            x, y = region.radius
            return ROIs.Ellipse((x * gx, y * gy), on=region.data)
        elif isinstance(region, ROIs.Polygon):
            return ROIs.Polygon(region.centre, *map(lambda tup: (tup[0] * gx, tup[1] * gy),
                                                    region.find_offsets()), on=region.data)
