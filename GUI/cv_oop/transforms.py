"""
Various transformations to apply to images.

Can be geometric (such as scaling), morphological (such as erosion), or thresholding.
"""
import functools
import operator
import typing

import cv2
import numpy as np

from ._enums import *
from ._images import Image


def rotate(img: Image, theta: int, *, centre: tuple[int, int] = None) -> Image:
    """
    Rotate an image by the given angle (in degrees).

    :param img: The image to rotate.
    :param theta: The angle to rotate by.
    :param centre: The centre point of rotation. Default is the middle point of the image.
    :return: New rotated image.
    """
    w, h = img.size
    if centre is None:
        centre = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(centre, theta, 1)
    cos = np.abs(matrix[0, 0])
    sin = np.abs(matrix[0, 1])
    nw = int(w * cos + h * sin)
    nh = int(w * sin + h * cos)
    matrix[0, 2] += nw / 2 - centre[0]
    matrix[1, 2] += nh / 2 - centre[1]
    image = cv2.warpAffine(img.get_channeled_image(), matrix, (nw, nh))
    return img.from_(image)


def scale(img: Image, x_scale: int, y_scale: int, *, interpolation: int = None) -> Image:
    """
    Scale an image by the specified x and y factor.

    :param img: The image to scale.
    :param x_scale: The horizontal scaling factor.
    :param y_scale: The vertical scaling factor.
    :param interpolation: The interpolation to use. Default is to use the best for the scale factor.
    :return: The scaled image.
    :raises ValueError: If any scale factor is zero or if the interpolation is invalid.
    """
    w, h = img.size
    if interpolation not in {None, cv2.INTER_CUBIC, cv2.INTER_AREA, cv2.INTER_LINEAR}:
        raise ValueError("Expected interpolation to be linear, cubic, or area")
    elif not x_scale or not y_scale:
        raise ValueError("Cannot scale by 0")
    if interpolation is None:
        interpolation = cv2.INTER_AREA if x_scale < 0 or y_scale < 0 else cv2.INTER_LINEAR
    image = cv2.resize(img.get_channeled_image(), (h * y_scale, w * x_scale), interpolation=interpolation)
    return img.from_(image)


def translate(img: Image, x: int, y: int) -> Image:
    """
    Translate an image by the specified horizontal and vertical deviation.

    :param img: The image to translate.
    :param x: The horizontal deviation.
    :param y: The vertical deviation.
    :return: The translated image.
    """
    matrix = np.float32([[1, 0, x], [0, 1, y]])
    image = cv2.warpAffine(img.get_channeled_image(), matrix, img.size)
    return img.from_(image)


def flip(img: Image, by: Axis) -> Image:
    """
    Flip an image in the specified axis.

    :param img: The image to flip.
    :param by: The axis to flip in.
    :return: A new flipped image.
    """
    is_x, is_y = bool(by & Axis.X), bool(by & Axis.Y)
    if is_x and is_y:
        code = -1
    elif not (is_x or is_y):
        raise ValueError("Expected to flip in at least one axis")
    else:
        code = int(is_x)
    flipped = cv2.flip(img.get_channeled_image(), code)
    return img.from_(flipped)


def global_threshold(img: Image, threshold: int, mode: ThresholdMode, algorithm=ThresholdDeterminer.MANUAL, *,
                     maximum: int = None) -> Image:
    """
    Apply a singular threshold value to an image.

    :param img: The image to threshold.
    :param threshold: The thresholding value. If using a determiner, it is custom to leave it at zero.
    :param mode: The thresholding mode.
    :param algorithm: The algorithm to use to determine the thresholding value. Default is to use the value provided.
    :param maximum: The maximum value to use for binary thresholding.
    :return: The thresholded image.
    :raises ValueError: If the maximum value is used when not needed (or vice versa).
    :raises TypeError: If the image isn't greyscale.
    :raises ArithmeticError: If the maximum (when provided) or thresholding value isn't between 0 and 255.
    """
    return region_threshold(img, (threshold, threshold), mode, maximum=maximum, pick=0)


def adaptive_threshold(img: Image, method: ThresholdAdaptor, block: int, c: int, maximum: int, *,
                       invert=False) -> Image:
    """
    Apply adaptive thresholding to an image – will calculate a new threshold value per pixel.

    Adaptive thresholding only works on binary thresholding.
    :param img: The image to threshold.
    :param method: The adaptation algorithm.
    :param block: The block size (number of pixels to use) in the algorithm. (Should be odd and positive)
    :param c: The constant to subtract for each found threshold.
    :param maximum: The maximum value.
    :param invert: Whether to perform inverted binary thresholding.
    :return: The thresholded image.
    :raises TypeError: If the image isn't greyscale.
    :raises ArithmeticError: If the maximum isn't between 0 and 255.
    :raises ValueError: If the block size is even or negative.
    """
    if img.colour_mode == CMode.RGB:
        raise TypeError("Can only threshold greyscale images")
    if not (0 <= maximum <= 255):
        raise ArithmeticError("Maximum must be between 0 and 255")
    Image.check_kernel(block)
    mode = method.value
    type_ = cv2.THRESH_BINARY if not invert else cv2.THRESH_BINARY_INV
    image = cv2.adaptiveThreshold(img.extract_channel("r"), maximum, type_, mode, blockSize=block, C=c)
    return img.from_(image)


def morphological_transform(img: Image, transform: Transform, size: tuple[int, int], shape: int, *, k_scale=1,
                            iterations=1) -> Image:
    """
    Apply a morphological transform to the image.

    :param img: The image to transform.
    :param transform: The morphological transform to apply.
    :param size: The size of the kernel.
    :param shape: The shape of the kernel (should be a cv2 kernel shape).
    :param k_scale: The nonzero values within the kernel (fits into an uint8).
    :param iterations: The number of iterations to apply.
    :return: The transformed image.
    :raises ValueError: If the scale overflowed its datatype or is 0, or if the kernel shape is invalid.
    :raises TypeError: If the image isn't greyscale.
    """
    if k_scale < 1 or k_scale > 255:
        raise ValueError("k_scale must be between 1 and 255")
    elif img.colour_mode == CMode.RGB:
        raise TypeError("Morphological transformations only accept greyscale images")
    elif shape not in {cv2.MORPH_RECT, cv2.MORPH_CROSS, cv2.MORPH_ELLIPSE}:
        raise ValueError("Invalid kernel shape")
    kernel = cv2.getStructuringElement(shape, size) * k_scale
    if transform == Transform.ERODE:
        func = functools.partial(cv2.erode, kernel=kernel, iterations=iterations)
    elif transform == Transform.DILATE:
        func = functools.partial(cv2.dilate, kernel=kernel, iterations=iterations)
    else:
        func = functools.partial(cv2.morphologyEx, kernel=kernel, iterations=iterations, op=transform.value)
    image = func(img.get_channeled_image())
    return img.from_(image)


def expose_lines(img: Image, direction: Axis, size=2) -> Image:
    """
    Expose directional lines on a binary image.

    :param img: The image to capture.
    :param direction: The axes in which to expose.
    :param size: The size of the lines to expose.
    :return: A new image with the specified lines exposed.
    """
    if not img.is_binary():
        raise TypeError("Line extraction only works on binary images")
    stages = []
    if direction & Axis.X:
        stages.append((1, size))
    if direction & Axis.Y:
        stages.append((size, 1))
    if not stages:
        raise ValueError("Expected to expose at least one axis")
    results = [Image(np.zeros(img.size[::-1]), colour=CMode.GREY)]
    for k_size in stages:
        results.append(morphological_transform(img, Transform.OPEN, k_size, cv2.MORPH_RECT))
    return functools.reduce(operator.or_, results)


def binarise(img: Image, important_channel: typing.Literal["r", "g", "b"], turning_point: int, *,
             use_greater_equal=False, great_to_white=True) -> Image:
    """
    Convert any image to a binary image by using global thresholding.

    :param img: The image to convert.
    :param important_channel: The channel to use in greyscale conversion.
    :param turning_point: The threshold value.
    :param use_greater_equal: Flag for whether the end value is included in the "greater than" behaviour.
    :param great_to_white: Flag to customise "greater than" behaviour. True converts "greater than" values to white.
    :return: A new binary image.
    """
    binary = ThresholdMode.GT_MAX_LTE_0 if great_to_white else ThresholdMode.GT_0_LTE_MAX
    if use_greater_equal:
        turning_point -= 1
    return global_threshold(img.to_greyscale(important_channel), turning_point, binary, maximum=255)


def update_contrast(img: Image, size: tuple[int, int], shape: int, *, k_scale=1) -> Image:
    """
    Update the contrast of the image by adding the tophat and then subtracting the blackhat.

    Introduces more noise as kernel size increases.
    :param img: The image to transform.
    :param size: The size of the kernel to use.
    :param shape: The shape of the kernel to use.
    :param k_scale: The scale to use for the kernel.
    :return: A new image with brigher birght areas and darker dark areas.
    """
    top = morphological_transform(img, Transform.WHITEHAT, size, shape, k_scale=k_scale)
    bottom = morphological_transform(img, Transform.BLACKHAT, size, shape, k_scale=k_scale)
    return img + top - bottom


def region_threshold(img: Image, threshold: tuple[int, int], mode: ThresholdMode, *, maximum: int = None,
                     pick: int = None) -> Image:
    """
    Apply a range of threshold values to an image. Any "greater than" behaviour means "out of bounds".

    :param img: The image to threshold.
    :param threshold: The thresholding value. If using a determiner, it is custom to leave it at zero.
    :param mode: The thresholding mode.
    :param maximum: The maximum value to use for binary thresholding.
    :param pick: The index to use in truncated thresholding.
    :return: The thresholded image.
    :raises ValueError: If the maximum value (or pick value) is used when not needed (or vice versa).
    :raises TypeError: If the image isn't greyscale.
    :raises ArithmeticError: If the maximum (when provided) or thresholding value isn't between 0 and 255.
    """
    if img.colour_mode == CMode.RGB:
        raise TypeError("Can only threshold greyscale images")

    if mode in {ThresholdMode.GT_MAX_LTE_0, ThresholdMode.GT_0_LTE_MAX}:
        if maximum is None:
            raise ValueError("Maximum should be specified for binary thresholding")
        elif maximum < 0 or maximum > 255:
            raise ArithmeticError("Maximum should be between 0 and 255")
    elif maximum is not None:
        raise ValueError("Maximum should only be specified for binary thresholding")
    elif mode == ThresholdMode.GT_THRESH_LTE_SRC and pick is None:
        raise ValueError("Pick should be specified for truncated thresholding")
    elif pick is not None:
        raise ValueError("Pick should only be specified for truncated thresholding")

    if any(t < 0 or t > 255 for t in threshold):
        raise ArithmeticError("Threshold should be between 0 and 255")

    image = img.extract_channel("r").copy()
    out_of_bounds = (image < threshold[0]) | (image > threshold[1])
    in_bounds = ~out_of_bounds
    if mode == ThresholdMode.GT_MAX_LTE_0:
        image[out_of_bounds] = 0
        image[in_bounds] = maximum
    elif mode == ThresholdMode.GT_0_LTE_MAX:
        image[out_of_bounds] = maximum
        image[in_bounds] = 0
    elif mode == ThresholdMode.GT_THRESH_LTE_SRC:
        image[out_of_bounds] = threshold[pick]
    elif mode == ThresholdMode.GT_0_LTE_SRC:
        image[out_of_bounds] = 0
    elif mode == ThresholdMode.GT_SRC_LTE_0:
        image[in_bounds] = 0
    return img.from_(image)


class Transformer:
    """
    Class to wrap an image up such that transformations can be applied to an instance variable.

    Transformations applied won't affect the original image.

    :var Image _img: The captured image.
    """

    @property
    def image(self) -> Image:
        """
        Public access to the image.

        :return: The captured image.
        """
        return self._img

    def __init__(self, img: Image):
        self._img = img

    def _update(self):
        pass

    def rotate(self, theta: int, *, centre: tuple[int, int] = None) -> "Transformer":
        """
        Wrapper for the 'rotate' function. Will update the image accordingly.

        See help(rotate) for more information.
        :return: The instance itself so that transformations can be stacked.
        """
        self._img = rotate(self._img, theta, centre=centre)
        self._update()
        return self

    def scale(self, x_scale: int, y_scale: int, *, interpolation: int = None) -> "Transformer":
        """
        Wrapper for the 'scale' function. Will update the image accordingly.

        See help(scale) for more information.
        :return: The instance itself so that transformations can be stacked.
        """
        self._img = scale(self._img, x_scale, y_scale, interpolation=interpolation)
        self._update()
        return self

    def translate(self, x: int, y: int) -> "Transformer":
        """
        Wrapper for the 'translate' function. Will update the image accordingly.

        See help(translate) for more information.
        :return: The instance itself so that transformations can be stacked.
        """
        self._img = translate(self._img, x, y)
        self._update()
        return self

    def flip(self, by: Axis) -> "Transformer":
        """
        Wrapper for the 'flip' function. Will update the image accordingly.

        See help(flip) for more information.
        :return: The instance itself so that transformations can be stacked.
        """
        self._img = flip(self._img, by)
        self._update()
        return self

    def global_threshold(self, threshold: int, mode: ThresholdMode, algorithm=ThresholdDeterminer.MANUAL, *,
                         maximum: int = None) -> "Transformer":
        """
        Wrapper for the 'global_threshold' function. Will update the image accordingly.

        See help(global_threshold) for more information.
        :return: The instance itself so that transformations can be stacked.
        """
        self._img = global_threshold(self._img, threshold, mode, algorithm, maximum=maximum)
        self._update()
        return self

    def adaptive_threshold(self, method: ThresholdAdaptor, block: int, c: int, maximum: int, *,
                           invert=False) -> "Transformer":
        """
        Wrapper for the 'adaptive_threshold' function. Will update the image accordingly.

        See help(adaptive_threshold) for more information.
        :return: The instance itself so that transformations can be stacked.
        """
        self._img = adaptive_threshold(self._img, method, block, c, maximum, invert=invert)
        self._update()
        return self

    def morphological_transform(self, transform: Transform, size: tuple[int, int], shape: int, *, k_scale=1,
                                iterations=1) -> "Transformer":
        """
        Wrapper for the 'morphological_transform' function. Will update the image accordingly.

        See help(morphological_transform) for more information.
        :return: The instance itself so that transformations can be stacked.
        """
        self._img = morphological_transform(self._img, transform, size, shape, k_scale=k_scale, iterations=iterations)
        self._update()
        return self

    def expose_lines(self, direction: Axis, size=2) -> "Transformer":
        """
        Wrapper for the 'expose_lines' function. Will update the image accordingly.

        See help(expose_lines) for more information.
        :return: The instance itself so that transformations can be stacked.
        """
        self._img = expose_lines(self._img, direction, size)
        self._update()
        return self

    def binarise(self, important_channel: typing.Literal["r", "g", "b"], turning_point: int, *,
                 use_greater_equal=False, great_to_white=True) -> "Transformer":
        """
        Wrapper for the 'binarise' function. Will update the image accordingly.

        See help(binarise) for more information.
        :return: The instance itself so that transformations can be stacked.
        """
        self._img = binarise(self._img, important_channel, turning_point, use_greater_equal=use_greater_equal,
                             great_to_white=great_to_white)
        self._update()
        return self

    def update_contrast(self, size: tuple[int, int], shape: int, *, k_scale=1) -> "Transformer":
        """
        Wrapper for the 'update_contrast' function. Will update the image accordingly.

        See help(update_contrast) for more information.
        :return: The instance itself so that transformations can be stacked.
        """
        self._img = update_contrast(self._img, size, shape, k_scale=k_scale)
        self._update()
        return self

    def region_threshold(self, threshold: tuple[int, int], mode: ThresholdMode, *, maximum: int = None,
                         pick: int = None) -> "Transformer":
        """
        Wrapper for the 'region_threshold' function. Will update the image accordingly.

        See help(region_threshold) for more information.
        :return: The instance itself so that transformations can be stacked.
        """
        self._img = region_threshold(self._img, threshold, mode, maximum=maximum, pick=pick)
        self._update()
        return self

    def pipeline(self, *commands: dict[str, typing.Any]):
        """
        Shortcut for applying various commands one after the other.

        Each command must have a 'name' key for the function to apply.
        :param commands: Keyword arguments to pass to each step individually.
        :raises KeyError: If a command doesn't have a 'name' key. Will do this check prior to any function calls.
        """
        fns = [getattr(self, kwargs.pop("name")) for kwargs in commands]
        for fn, kwargs in zip(fns, commands):
            fn(**kwargs)
