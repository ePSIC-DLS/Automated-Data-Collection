"""
Allows rotation of images and ROIs
"""
from __future__ import annotations
import cv2
import numpy as np

from .scale import Scale
from .. import ROIs
from ..image import Image


class Rotate:
    """
    Namespace class for rotations
    """

    @staticmethod
    def image(img: Image, theta: int, *, scale=1, centre: tuple[int, int] = None) -> Image:
        """
        Rotates an Image - will automatically resize the remaining image to not crop any
        :param img: The Image
        :param theta: Angle to rotate by (assumes degrees like cv2)
        :param scale: Any scaling that should be performed
        :param centre: The centre point of rotation
        :return: The rotated image
        """
        w, h = img.shape
        if centre is None:
            centre = (w / 2, h / 2)
        matrix = cv2.getRotationMatrix2D(centre, theta, scale)
        cos = np.abs(matrix[0, 0])
        sin = np.abs(matrix[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))
        matrix[0, 2] += (new_w / 2) - centre[0]
        matrix[1, 2] += (new_h / 2) - centre[1]
        return Image(cv2.warpAffine(img.image, matrix, (new_w, new_h)))

    @staticmethod
    def region(region: ROIs.ROI, theta: int, *, scale=1) -> ROIs.ROI:
        """
        Rotates a ROI
        :param region: the ROI
        :param theta: Angle to rotate by (assumes degrees like cv2)
        :param scale: Any scaling that should be performed
        :return: The rotated ROI
        :raise ValueError: If trying to rotate a Rect a non-90 degree value
        """
        theta = np.deg2rad(theta)
        r = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
        if isinstance(region, ROIs.Rect):
            if theta % 90 != 0:
                raise ValueError("Rect ROI must be Axis-Aligned")
            theta %= 360
            w, h = region.size
            if theta == 90 or theta == 270:
                new = ROIs.Rect(h, w, on=region.data)
            else:
                new = region.apply(region.data)
            return new if scale == 1 else Scale.region(new, (scale, scale))
        elif isinstance(region, ROIs.Ellipse):
            radius = np.array(region.radius)
            rot_radius = radius @ r.T
            new = ROIs.Ellipse((int(rot_radius[0]), int(rot_radius[1])), on=region.data)
            return new if scale == 1 else Scale.region(new, (scale, scale))
        elif isinstance(region, ROIs.Polygon):
            polygon = np.array(list(region.find_offsets()))
            new_polygon = polygon @ r.T
            new = ROIs.Polygon(region.centre, *new_polygon, on=region.data)
            return new if scale == 1 else Scale.region(new, (scale, scale))
