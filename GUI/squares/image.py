"""
Creates an image processing class
"""
from __future__ import annotations

import functools
import itertools
import typing

import cv2
import numpy as np

from . import ROIs
from .colour import Colour
from .enums import *


class Image:
    """
    Class to represent a cv2 image in an OOP method

    :var _image numpy.ndarray: The image to store
    """

    @property
    def image(self) -> np.ndarray:
        """
        Public getter for the image
        :return: The array for the image (converted to float32)
        """
        return self._image.astype(np.float32)

    @property
    def shape(self) -> tuple[int, int]:
        """
        Public access to the image dimensions.
        :return: Width, height
        """
        shape = self._image.shape
        return shape[1], shape[0]

    @property
    def colour_mode(self) -> CMODE:
        """
        The colour mode used
        :return: Black and White or RGB
        """
        g = self._image[:, :, 1]
        return CMODE.BW if np.all(g == self._image[:, :, 0]) and np.all(self._image[:, :, 2] == g) else CMODE.RGB

    def __init__(self, bgr_data: np.ndarray, *, auto_wrap=False):
        """
        Stores the data as an image
        :param bgr_data: the image to use
        """
        shape = bgr_data.shape
        if len(shape) == 2:
            zeros = np.zeros((*shape, 3))
            zeros[:, :, 0] = bgr_data
            if not auto_wrap:
                zeros[:, :, 1] = bgr_data
                zeros[:, :, 2] = bgr_data
            bgr_data = zeros
        elif len(shape) != 3:
            raise ValueError("Dimensionality mismatch. Image should be 2 or 3 dimensional")
        self._image = bgr_data.astype(np.uint)
        self._wrap = Wrapping.WRAP_SEQ if auto_wrap else Wrapping.RAISE

    def __getitem__(self, item: tuple[int, int]) -> Colour:
        """
        Gets a single pixel's colour
        :param item: a 2D co-ordinate
        :return: The colour at that pixel
        :raise TypeError: If item isn't a tuple
        :raise ValueError: If item doesn't have two items
        """
        if not isinstance(item, tuple):
            raise TypeError("Must index at a tuple")
        elif len(item) != 2:
            raise ValueError("Invalid tuple for indexing")
        item = tuple(reversed(item))
        getter = functools.partial(self._image.item, *item)
        return Colour(getter(2), getter(1), getter(0), self._wrap)

    def __setitem__(self, item: tuple[int, int], value: Colour):
        """
        Sets a single pixel's colour
        :param item: a 2D co-ordinate
        :param value: the colour at that pixel
        :raise TypeError: If item isn't a tuple or value isn't a colour
        :raise ValueError: If item doesn't have two items or colour has unique values
        """
        if not isinstance(item, tuple):
            raise TypeError("Must index at a tuple")
        elif len(item) != 2:
            raise ValueError("Invalid tuple for indexing")
        elif not isinstance(value, Colour):
            raise TypeError("Invalid value type")
        item = tuple(reversed(item))
        if self.colour_mode == CMODE.BW and not all(v == value["r"] for v in value.all(RGBOrder.RGB)):
            raise ValueError("Must have grayscale colour")
        for i, s in zip(range(3), RGBOrder.BGR.value):
            self._image.itemset((*item, i), value[s])

    def __add__(self, other: typing.Union[typing.Self, float]) -> typing.Self:
        """
        Handles Image + Image (using cv2 standard of overflow)
        :param other: The image or constant to use
        :return: A new image
        """
        if not isinstance(other, Image | float | int):
            return NotImplemented
        other = other.image if isinstance(other, Image) else other
        return type(self)(cv2.add(self._image, other))

    def __sub__(self, other: typing.Union[typing.Self, float]) -> typing.Self:
        """
        Handles Image – Image (using cv2 standard of overflow)
        :param other: The image or constant to use
        :return: A new image
        """
        if not isinstance(other, Image | float | int):
            return NotImplemented
        other = other.image if isinstance(other, Image) else other
        return type(self)(cv2.subtract(self._image, other))

    def __mul__(self, other: typing.Union[typing.Self, float]) -> typing.Self:
        """
        Handles Image * Image (using cv2 standard of overflow)
        :param other: The image or constant to use
        :return: A new image
        """
        if not isinstance(other, Image | float | int):
            return NotImplemented
        other = other.image if isinstance(other, Image) else other
        return type(self)(cv2.multiply(self._image, other))

    def __truediv__(self, other: typing.Union[typing.Self, float]) -> typing.Self:
        """
        Handles Image / Image (using cv2 standard of overflow)
        :param other: The image or constant to use
        :return: A new image
        """
        if not isinstance(other, Image | float | int):
            return NotImplemented
        other = other.image if isinstance(other, Image) else other
        return type(self)(cv2.divide(self._image, other))

    def __and__(self, other: typing.Union[typing.Self, float]) -> typing.Self:
        """
        Handles Image & Image (using cv2 standard of overflow)
        :param other: The image or constant to use
        :return: A new image
        """
        if not isinstance(other, Image | float | int):
            return NotImplemented
        other = other.image if isinstance(other, Image) else other
        return type(self)(cv2.bitwise_and(self._image, other))

    def __or__(self, other: typing.Union[typing.Self, float]) -> typing.Self:
        """
        Handles Image | Image (using cv2 standard of overflow)
        :param other: The image or constant to use
        :return: A new image
        """
        if not isinstance(other, Image | float | int):
            return NotImplemented
        other = other.image if isinstance(other, Image) else other
        return type(self)(cv2.bitwise_or(self._image, other))

    def __xor__(self, other: typing.Union[typing.Self, float]) -> typing.Self:
        """
        Handles Image ^ Image (using cv2 standard of overflow)
        :param other: The image or constant to use
        :return: A new image
        """
        if not isinstance(other, Image | float | int):
            return NotImplemented
        other = other.image if isinstance(other, Image) else other
        return type(self)(cv2.bitwise_xor(self._image, other))

    def __invert__(self) -> typing.Self:
        """
        Handles ~Image (using cv2 standard of overflow)
        :return: A new image
        """
        return type(self)(cv2.bitwise_not(self._image))

    def blend(self, img2: typing.Self, alpha: float) -> typing.Self:
        """
        Blends two images together by using linear interpolation (LERP) algorithm
        :param img2: The other image
        :param alpha: The percentage of the second image that should blend through
        :return: The image resulting from the blend
        """
        return type(self)(cv2.addWeighted(self._image, 1 - alpha, img2.image, alpha, 0))

    def mask(self, roi: ROIs.ROI) -> typing.Self:
        """
        Masks the image with a specific Region Of Interest (ROI)
        :param roi: the ROI to use
        :return: The image covered by that mask
        """
        return type(self)(cv2.bitwise_and(self._image, self._image, mask=roi.surface))

    def merge(self, other: typing.Self, depth: int) -> typing.Self:
        """
        Merges two images together using Laplacian pyramids
        :param other: The other image
        :param depth: The number of layers to use (more is better)
        :return: The new image that is a smooth merge of the input two
        """

        def make_merges() -> typing.Generator[np.ndarray, None, None]:
            """
            Merges each layer using hstack
            :return: Yields each merged layer
            """
            for im1, im2 in zip(self_pyr.form_layers(depth), other_pyr.form_layers(depth)):
                _, cols, _ = im1.image.shape
                yield np.hstack((im1.image[:, :cols // 2], im2.image[:, cols // 2:]))

        from .pyramid import Pyramid
        self_pyr = Pyramid(self, mode=PMODE.LAPLACIAN)
        other_pyr = Pyramid(other, mode=PMODE.LAPLACIAN)
        merges = make_merges()
        merged = next(merges)
        for merge in merges:
            merged = cv2.pyrUp(merged)
            merged = cv2.add(merged, merge)
        return type(self)(merged)

    def is_binary(self) -> bool:
        """
        Determines whether the image is a binary image
        :return: Whether the image has only two pixel values
        """
        b = self._image == 0
        w = self._image == 255
        return self.colour_mode == CMODE.BW and np.all(b | w)

    def edge_detection(self, minval: int, maxval: int, kernel_size: int) -> typing.Self:
        """
        Perform Canny edge detection on the image
        :param minval: The minimum intensity
        :param maxval: The maximum intensity
        :param kernel_size: The size of the kernel (or aperture) to use
        :return: A new image made of the edges
        """
        return type(self)(cv2.Canny(self._image, minval, maxval, apertureSize=kernel_size, L2gradient=True))

    def copy(self) -> typing.Self:
        """
        Deepcopy the image
        :return: The same image
        """
        return type(self)(self._image.copy(), auto_wrap=self._wrap == Wrapping.WRAP_SEQ)

    def to_colour(self, colour: CMODE, important: Domain) -> typing.Self:
        """
        Convert an image to a specified colour scheme.
        :param colour: The colour mode to use.
        :param important: The domain to isolate when going from RGB to greyscale.
        :return: A new image using the specified scheme.
        :raise ValueError: If domain is ALL when minimizing colour, or not ALL when maximizing colour.
        """
        if self.colour_mode == colour:
            return self.copy()
        elif colour == CMODE.BW:
            if important == Domain.ALL:
                raise ValueError("Cannot have all colours as important colour")
            elif important in (Domain.MAX, Domain.MIN):
                func, np_func = (max, np.max) if important == Domain.MAX else (min, np.min)
                b = self._image[:, :, 0]
                g = self._image[:, :, 1]
                r = self._image[:, :, 2]
                b_max = np_func(b)
                g_max = np_func(g)
                r_max = np_func(r)
                look_for = func(b_max, g_max, r_max)
                all_locals = locals()
                for k in ("b", "g", "r"):
                    if look_for == all_locals[f"{k}_max"]:
                        return type(self)(all_locals[k])
                raise LookupError("Unexpected error")
            return type(self)(self._image[:, :, 2 - important.value])
        if important != Domain.ALL:
            raise ValueError("Cannot choose important colour in greyscale image")
        return type(self)(self._image.copy())

    def get_channeled_image(self, reorder=RGBOrder.BGR) -> np.ndarray:
        """
        Obtain RGB channel numpy array
        :param reorder: The order to redistribute the colour channels
        :return: A numpy.ndarray with 3 channels – R, G, B. Each of these channels is restricted to 0-255
        """
        w, h = self.shape
        order_value = reorder.value
        img = np.zeros((h, w, 3))
        normal_map = ("b", "g", "r")
        order_map = tuple(map(normal_map.index, order_value))
        for i in range(3):
            img[:, :, i] = self._image[:, :, order_map[i]]
        order_mapping = {v: order_value.index(v) for v in order_value}
        arrays = dict(r=img[:, :, order_mapping["r"]], g=img[:, :, order_mapping["g"]], b=img[:, :, order_mapping["b"]])
        if self._wrap == Wrapping.WRAP_SEQ:
            for k, look in zip(itertools.cycle(Colour.WRAP_ORDER), Colour.WRAP_ORDER[1:] + Colour.WRAP_ORDER):
                mask = arrays[k] > 255
                if np.any(mask):
                    arrays[look][mask] += arrays[k][mask] - 255
                    arrays[k][mask] = 255
        for arr in arrays.values():
            if np.any(arr < 0) or np.any(arr > 255):
                raise ValueError("All colours must be between 0 and 255")
        return img.astype(np.uint8)

    def blur(self, kernel_size: tuple[int, int] = (0, 0), kernel: np.ndarray = None) -> typing.Self:
        """
        Blurs the image using 2D convolution
        :param kernel_size: The size of the kernel to convolve with
        :param kernel: The kernel to use (leave as one to automatically calculate the kernel)
        :return: A new averaged image
        :raise ValueError: If kernel_size is (0, 0) and there is no provided kernel
        """
        if kernel is None:
            if kernel_size == (0, 0):
                raise ValueError("Cannot create kernel with no size")
            kernel = np.ones(kernel_size, np.float32) / (kernel_size[0] * kernel_size[1])
        return type(self)(cv2.filter2D(self.image, -1, kernel))

    def gaussian_blur(self, kernel_size: tuple[int, int], sd: tuple[int, int] = (0, 0)) -> typing.Self:
        """
        Blurs the image using a gaussian kernel
        :param kernel_size: The size of the kernel (should be odd and positive)
        :param sd: The standard deviation in both x and y
        :return: A new blurred image
        :raise ValueError: If the kernel isn't odd and positive
        """
        if not all(k % 2 and k > 0 for k in kernel_size):
            raise ValueError("Kernel size should be positive and odd")
        return type(self)(cv2.GaussianBlur(self.image, kernel_size, *sd))

    def median_blur(self, square_size: int) -> typing.Self:
        """
        Blurs the image using a median kernel
        :param square_size: The size of the kernel (odd and positive)
        :return: A new blurred image
        :raise ValueError: If the kernel isn't odd and positive
        """
        if not (square_size % 2 and square_size > 0):
            raise ValueError("Kernel size should be positive and odd")
        return type(self)(cv2.medianBlur(self.image, square_size))

    def sharpen(self, k_size: int) -> typing.Self:
        """
        Sharpen an image using laplacian derivatives
        :param k_size: Size of kernel
        :return: A new image that has been sharpened
        :raise ValueError: When k size is less than 0 or even
        """
        if k_size % 2 == 0 or k_size < 1:
            raise ValueError("K size should be 1 or higher")
        return type(self)(cv2.Laplacian(self.image, ddepth=-1, ksize=k_size))

    def update_contrast(self, contrast: float, brightness: float) -> typing.Self:
        """
        Updated contrast and brightness by using weighted addition
        :param contrast: The new contrast
        :param brightness: The new brightness
        :return: The image resulting from the update
        """
        brightness += round(255 * (1 - contrast) / 2)
        return type(self)(cv2.addWeighted(self._image, contrast, self._image, 0, brightness))

    def get_raw(self) -> np.ndarray:
        """
        Public access to the raw underlying data
        :return: The image's data without any conversion – modifying this, will modify the image
        """
        return self._image

    def get_summed(self) -> np.ndarray:
        """
        Method to return a 2D array, where each element is the **sum** of the colours at that point.
        :return: A 2D numpy array
        """
        return self._image[:, :, 0] + self._image[:, :, 1] + self._image[:, :, 2]

    @classmethod
    def from_file(cls, filename: str, mode: int = cv2.IMREAD_COLOR, wrap=False) -> typing.Self:
        """
        Alternative constructor for loading an image from a file
        :param filename: The file to load
        :param mode: How to load it (cv2.IMREAD_<>)
        :param wrap: Whether to wrap the colours of the image or not
        :return: The loaded image
        """
        return cls(cv2.imread(filename, mode), auto_wrap=wrap)
