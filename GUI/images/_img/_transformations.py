import functools
import operator
import typing
from typing import Tuple as _tuple, List as _list

import cv2
import numpy as np
import numpy.typing as npt

try:
    import typing_extensions
except ModuleNotFoundError:
    typing_extensions = typing

from .. import Grey, Colour
from .._aliases import *
from .._enums import *
from ._utils import Mutate as Mutation
from ._bases import MultiModal

RGBT = typing.TypeVar("RGBT", bound=MultiModal[Colour])
GreyT = typing.TypeVar("GreyT", bound=MultiModal[Grey])
TransT = typing.TypeVar("TransT", MultiModal[Colour], MultiModal[Grey])


class ThresholdBehaviour:
    """
    Class to describe how a thresholding value can be applied to an image.

    Attributes
    ----------
    _type: ThresholdBehaviourType
        The type of the behaviour.
        The 'src' type means that the behaviour will return its input.
        The 'ext' type means that the behaviour will return its external value.
        The 'pin' type means that the behaviour will return the threshold value used.
    _value: int | None
        The stored value of the threshold.

    Raises
    ------
    ValueError
        If the value is specified when the type is 'src', or not specified otherwise.
    ArithmeticError
        If the value is not between 0-255.
    """

    @property
    def type(self) -> ThresholdBehaviourType:
        """
        Public access to the type.

        Returns
        -------
        ThresholdBehaviourType
            The type of the behaviour.
        """
        return self._type

    @property
    def value(self) -> typing.Optional[int]:
        """
        Public access to the value.

        Returns
        -------
        int | None
            The external stored value.
        """
        return self._value

    def __init__(self, ty: ThresholdBehaviourType, value: int = None):
        self._type = ty
        self._value = value
        if ty == "src":
            if value is not None:
                raise ValueError("'src' behaviour should have no external value")
        else:
            if value is None:
                raise ValueError(f"{ty!r} behaviour should have an external value")
            elif value < 0 or value > 255:
                raise ArithmeticError(f"External value must be between 0 and 255, got {value}")

    def __str__(self) -> str:
        return f"{self._type}: {self._value if self._value is not None else ''}"

    def __eq__(self, other: "ThresholdBehaviour") -> bool:
        """
        Compare the two behaviours.

        If the types and values are identical, they are equal.

        Parameters
        ----------
        other: ThresholdBehaviour
            The other behaviour to compare with.

        Returns
        -------
        bool
            Whether the two behaviours are equivalent.
        """
        if not isinstance(other, ThresholdBehaviour):
            return NotImplemented
        return self.type == other.type and self.value == other.value

    def handle(self, src: np.ndarray) -> npt.ArrayLike:
        """
        Handle the input.

        Parameters
        ----------
        src: np.ndarray

        Returns
        -------
        npt.ArrayLike
            The value to use as the thresholding output.
        """
        if self._type == "src":
            return src
        return self._value


class ThresholdType:
    """
    A type of thresholding that contains behaviours for '<' the value, '==' the value, and '>' the value.

    This thresholding type can store an internal threshold value for when at least one behaviour uses the 'pin' type.

    Attributes
    ----------
    _lt: ThresholdBehaviour
        The < (less than) behaviour to use.
    _gt: ThresholdBehaviour
        The > (greater than) behaviour to use.
    _eq: ThresholdBehaviour
        The == (equal to) behaviour to use.
    _threshold: int | None
        The stored threshold value from any 'pin' type behaviours.

    Parameters
    ----------
    less_than_behaviour: ThresholdBehaviour
        The behaviour to use for data less than the threshold value.
    greater_than_behaviour: ThresholdBehaviour
        The behaviour to use for data greater than the threshold value.
    equal_to_behaviour: ThresholdBehaviour | EqDefaults (default is "lt")
        The behaviour to use for data equal to the threshold value.
        It can either be its own unique value, or instead mimic the greater than or less than behaviour.

    Raises
    ------
    ValueError
        If the 'equal to' behaviour is invalid.
        If there are multiple pin types with differing threshold values.
    """

    @property
    def threshold(self) -> int:
        """
        Public access to the stored threshold value.

        Returns
        -------
        int
            The thresholding value stored by any behaviours with a 'pin' type.

        Raises
        ------
        AttributeError
            If the threshold value is None (there are no 'pin type' behaviours.)
        """
        if self._threshold is None:
            raise AttributeError("No thresholding behaviour defined")
        return self._threshold

    @property
    def less_than(self) -> ThresholdBehaviour:
        """
        Public access to the < behaviour.

        Returns
        -------
        ThresholdBehaviour
            The 'less than' behaviour.
        """
        return self._lt

    @property
    def equal_to(self) -> ThresholdBehaviour:
        """
        Public access to the == behaviour.

        Returns
        -------
        ThresholdBehaviour
            The 'equal to' behaviour.
        """
        return self._eq

    @property
    def greater_than(self) -> ThresholdBehaviour:
        """
        Public access to the > behaviour.

        Returns
        -------
        ThresholdBehaviour
            The 'greater than' behaviour.
        """
        return self._gt

    def __init__(self, less_than_behaviour: ThresholdBehaviour, greater_than_behaviour: ThresholdBehaviour,
                 equal_to_behaviour: typing.Union[ThresholdBehaviour, EqDefaults] = "lt"):
        self._lt, self._gt = less_than_behaviour, greater_than_behaviour
        if equal_to_behaviour == "lt":
            self._eq = self._lt
        elif equal_to_behaviour == "gt":
            self._eq = self._gt
        elif isinstance(equal_to_behaviour, ThresholdBehaviour):
            self._eq = equal_to_behaviour
        else:
            raise ValueError(f"Invalid equality behaviour {equal_to_behaviour}")
        behaviours = (self._lt, self._gt, self._eq)
        thresholds = tuple(filter(lambda b: b.type == "pin", behaviours))
        try:
            if not functools.reduce(operator.eq, thresholds) and len(thresholds) > 1:
                raise ValueError(f"Cannot have conflicting thresholds")
        except TypeError:
            pass
        self._threshold: typing.Optional[int] = thresholds[0].value if thresholds else None

    @classmethod
    def bimodal(cls, minima: int, maxima: int, *, invert=False, eq: EqDefaults = "lt") -> "ThresholdType":
        """
        Shortcut constructor for creating a ThresholdType that converts an image to a bimodal image.

        Parameters
        ----------
        minima: int
            The value to use when the image is less than the thresholding value.
        maxima: int
            The value to use when the image is greater than the thresholding value.
        invert: bool (default is False)
            Whether to invert the behaviour, such that the minima becomes the maxima and the maxima becomes the minima.
        eq: EqDefaults (default is "lt")
            What behaviour to use for equality.

        Returns
        -------
        ThresholdType
            The constructed type.
        """
        if invert:
            lt, gt = (ThresholdBehaviour("ext", maxima), ThresholdBehaviour("ext", minima))
        else:
            lt, gt = (ThresholdBehaviour("ext", minima), ThresholdBehaviour("ext", maxima))
        return cls(lt, gt, eq)

    @classmethod
    def binary(cls, *, invert=False, eq: EqDefaults = "lt") -> "ThresholdType":
        """
        Shortcut constructor for creating a bimodal ThresholdType that creates a binary image.

        Parameters
        ----------
        invert: bool (default is False)
            Whether to invert the behaviour, such that the maxima is 0 and the minima is 255.
        eq: EqDefaults (default is "lt")
            The behaviour to use for equality.

        Returns
        -------
        ThresholdType
            The constructed type.
        """
        return cls.bimodal(0, 255, invert=invert, eq=eq)

    @classmethod
    def floor(cls, pin_val: int, *, eq: EqDefaults = "lt") -> "ThresholdType":
        """
        Shortcut constructor for creating a ThresholdType that caps the maximum value as the threshold.

        Parameters
        ----------
        pin_val: int
            The threshold value to use.
        eq: EqDefaults (default is "lt")
            The behaviour to use for equality.

        Returns
        -------
        ThresholdType
            The constructed type.
        """
        return cls(ThresholdBehaviour("src"), ThresholdBehaviour("pin", pin_val), eq)

    @classmethod
    def ceil(cls, pin_val: int, *, eq: EqDefaults = "lt") -> "ThresholdType":
        """
        Shortcut constructor for creating a ThresholdType that caps the minimum value as the threshold.

        Parameters
        ----------
        pin_val: int
            The threshold value to use.
        eq: EqDefaults (default is "lt")
            The behaviour to use for equality.

        Returns
        -------
        ThresholdType
            The constructed type.
        """
        return cls(ThresholdBehaviour("pin", pin_val), ThresholdBehaviour("src"), eq)

    @classmethod
    def source(cls, *, invert=False, eq: EqDefaults = "lt") -> "ThresholdType":
        """
        Shortcut constructor for creating a ThresholdType that only keeps the pixels less than the threshold.

        Parameters
        ----------
        invert: bool (default is False)
            Whether to invert the type such that the pixels greater than the threshold are kept.
        eq: EqDefaults (default is "lt")
            The behaviour to use for equality.

        Returns
        -------
        ThresholdType
            The constructed type.
        """
        if invert:
            lt, gt = (ThresholdBehaviour("src"), ThresholdBehaviour("ext", 0))
        else:
            lt, gt = (ThresholdBehaviour("ext", 0), ThresholdBehaviour("src"))
        return cls(lt, gt, eq)


def blur(img: RGBT, kernel_size: _tuple[int, int]):
    """
    Blurs an image using 2D convolution.

    It will create a normalised kernel and apply the 2D convolution algorithm using that kernel. This means that for a
    5 × 5 kernel size, the actual kernel consists only of 1 / 25.

    Generics
    --------
    RGBT: MultiModal[Colour]
        The RGB image type.

    Parameters
    ----------
    img: RGBT
        The image to be blurred.
    kernel_size: tuple[int, int]
        The shape of the kernel.
    """
    ColourTransform.check(*kernel_size)
    kernel = np.ones(kernel_size, np.float32) / (kernel_size[0] * kernel_size[1])
    img.image.reference()[:] = cv2.filter2D(img.convert_image(np.float32), -1, kernel)


def gaussian_blur(img: RGBT, kernel_size: _tuple[int, int], sigma=(0, 0)):
    """
    Blurs an image using a Gaussian Kernel.

    Generics
    --------
    RGBT: MultiModal[Colour]
        The RGB image type.

    Parameters
    ----------
    img: RGBT
        The image to be blurred.
    kernel_size: tuple[int, int]
        The shape of the kernel.
    sigma: tuple[int, int]
        The standard deviation values to use. Using 0 in any axis means automatically calculate the best value from the
        kernel shape.
    """
    ColourTransform.check(*kernel_size)
    img.image.reference()[:] = cv2.GaussianBlur(img.convert_image(np.float32), kernel_size, sigmaX=sigma[0],
                                                sigmaY=sigma[1])


def sharpen(img: RGBT, kernel_size: int, scale=1, delta=0):
    """
    Sharpens an image using Laplacian derivatives.

    Generics
    --------
    RGBT: MultiModal[Colour]
        The RGB image type.

    Parameters
    ----------
    img: RGBT
        The image to be blurred.
    kernel_size: int
        The shape of the kernel. As laplacian derivatives use a square kernel, this is automatically upgraded to
        (`x`, `x`) for any x.
    scale: int
        The scaling factor to apply to the kernel.
    delta: int
        The factor to add to every element of the kernel.

    Raises
    ------
    ValueError
        If scale is not a natural number.
    """
    ColourTransform.check(kernel_size)
    if scale <= 0:
        raise ValueError("Expected a positive scale")
    img.image.reference()[:] = cv2.Laplacian(img.convert_image(np.float32), -1, ksize=kernel_size, scale=scale,
                                             delta=delta)


def median_blur(img: RGBT, kernel_size: int):
    """
    Blurs an image using a median blur kernel.

    Generics
    --------
    RGBT: MultiModal[Colour]
        The RGB image type.

    Parameters
    ----------
    img: RGBT
        The image to be blurred.
    kernel_size: int
        The shape of the kernel.
    """
    ColourTransform.check(kernel_size)
    img.image.reference()[:] = cv2.medianBlur(img.convert_image(np.float32), kernel_size)


def brightness_contrast_update(img: RGBT, contrast: float, brightness: int):
    """
    Enhances a colour image's brightness and contrast

    Generics
    --------
    RGBT: MultiModal[Colour]
        The RGB image type.

    Parameters
    ----------
    img: RGBT
        The image to be blurred.
    contrast: float
        The contrast to update by. This should be a natural number.
    brightness: int
        The brightness to update by. This should be a number between -255 and 255.

    Raises
    ------
    ValueError
        If contrast or brightness are out of range. For contrast this means zero or below, for brightness this means
        the absolute value is larger than 255.
    """
    if contrast <= 0:
        raise ValueError("Contrast must be larger than 0")
    elif not (-255 <= brightness <= 255):
        raise ValueError("Brightness must be between -255 and 255")
    brightness += round(255 * (1 - contrast) / 2)
    img.image.reference()[:] = cv2.addWeighted(img.image(), contrast, img.image(), 0, brightness)


def rotate(img: RGBT, theta: float):
    """
    Rotate an image by the given angle.

    Generics
    --------
    RGBT: MultiModal[Colour]
        The RGB image type.

    Parameters
    ----------
    img: RGBT
        The image to be blurred.
    theta: float
        The clockwise angle measured in degrees.
    """
    w, h = img.size
    centre = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(centre, theta, 1)
    cos = np.abs(matrix[0, 0])
    sin = np.abs(matrix[0, 1])
    nw = int(w * cos + h * sin)
    nh = int(w * sin + h * cos)
    matrix[0, 2] += nw / 2 - centre[0]
    matrix[1, 2] += nh / 2 - centre[1]
    img.image.reference()[:] = cv2.warpAffine(img.image(), matrix, (nw, nh))


def threshold(img: GreyT, mode: ThresholdType, pin: int = None):
    """
    Thresholds the greyscale image such that one singular threshold value is applied.

    The type of thresholding determines what happens for elements less than, equal to, and greater than this value.

    Generics
    --------
    GreyT: MultiModal[Grey]
        The greyscale image type.

    Parameters
    ----------
    img: GreyT
        The greyscale image to threshold.
    mode: ThresholdType
        The type of thresholding to perform.
    pin: int | None
        The threshold value. Should only be provided if the type does not provide one.

    Raises
    ------
    AttributeError
        If the type does not provide a threshold and the `pin` parameter is unspecified.
    ValueError
        If the type does provide a threshold and the `pin` parameter is specified.
    ArithmeticError
        If the `pin` parameter is not 0-255 (if unspecified, this error does not occur).
    """
    try:
        new_threshold = mode.threshold
    except AttributeError:
        if pin is None:
            raise
        new_threshold = pin
    else:
        if pin is not None:
            raise ValueError("Two conflicting thresholds. Either use the threshold parameter or set the threshold "
                             "on the thresholding type")
    if new_threshold < 0 or new_threshold > 255:
        raise ArithmeticError(f"Thresholding value must be between 0 and 255, got {new_threshold}")
    image = img.image.reference()
    gt = image > new_threshold
    eq = image == new_threshold
    lt = image < new_threshold
    for behaviour, mask in zip((mode.less_than, mode.equal_to, mode.greater_than), (lt, eq, gt)):
        image[mask] = behaviour.handle(image[mask])


def region_threshold(img: GreyT, in_bounds: ThresholdBehaviour, out_bounds: ThresholdBehaviour,
                     in_threshold: int = None, out_threshold: int = None):
    """
    Thresholds the greyscale image such that there is a range of valid values rather than a singular value.

    Generics
    --------
    GreyT: MultiModal[Grey]
        The greyscale image type.

    Parameters
    ----------
    img: GreyT
        The greyscale image to threshold.
    in_bounds: ThresholdBehaviour
        The behaviour to use when the image is within the specified range.
    out_bounds: ThresholdBehaviour
        The behaviour to use when the image is outside the specified range.
    in_threshold: int | None
        The threshold value for in-bounds behaviour. Should only be provided if the behaviour does not provide one.
    out_threshold: int | None
        The threshold value for out-bounds behaviour. Should only be provided if the behaviour does not provide one.

    Raises
    ------
    ValueError
        If the in-bounds and out-of-bounds behaviour are identical.
        If there are conflicting threshold values.
    AttributeError
        If there is no way to determine a behaviours threshold value.
    ArithmeticError
        If any threshold value is not 0-255.
    """
    if in_bounds == out_bounds:
        raise ValueError("Must have different behaviour for in and out of bounds")
    pin: _list[int] = []
    for pos, behav, thrsh in zip(("in", "out-of"), (in_bounds, out_bounds), (in_threshold, out_threshold)):
        if behav.type != "pin":
            if thrsh is None:
                raise AttributeError(f"No threshold value defined for {pos}-bound behaviour")
            new_threshold = thrsh
        else:
            if pin is not None:
                raise ValueError(f"Two conflicting thresholds for {pos}-bound behaviour. Either use the {pos}_threshold"
                                 f" parameter or set the threshold on the {pos}_bounds behaviour")
            new_threshold = behav.value
        pin.append(new_threshold)
    if not all(0 <= x <= 255 for x in pin):
        raise ArithmeticError(f"Expected all thresholds to be between 0 and 255. Got {pin}")
    image = img.image.reference()
    out = (image > pin[1]) | (image < pin[0])
    in_ = ~out
    image[out] = out_bounds.handle(image[out])
    image[in_] = in_bounds.handle(image[in_])


def adaptive_threshold(img: GreyT, method: AdaptiveThresholdAlgorithm, block_size: int, c: int,
                       maximum: int, *, invert=False):
    """
    Perform adaptive thresholding, such that each group of pixels receives an optimised thresholding value.

    Generics
    --------
    GreyT: MultiModal[Grey]
        The greyscale image type.

    Parameters
    ----------
    img: GreyT
        The image to threshold.
    method: AdaptiveThresholdAlgorithm
        The algorithm to use to determine the optimal threshold value per group.
    block_size: int
        The group size.
    c: int
        The constant to add to each group's result.
    maximum: int
        The value to send each group's invalid pixels to.
    invert: bool
        Whether to invert the result. Defaults to False.

    Raises
    ------
    ArithmeticError
        If the maximum is not between 0 and 255.
    """
    if not (0 <= maximum <= 255):
        raise ArithmeticError(f"Expected maximum between o and 255, got {maximum}")
    ColourTransform.check(block_size)
    mode = cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY
    img.image.reference()[:] = cv2.adaptiveThreshold(img.image(), maximum, method.to_cv2(), mode,
                                                     blockSize=block_size, C=c)


def transform(img: GreyT, mode: MorphologicalTransform, kernel_size: _tuple[int, int],
              shape: MorphologicalShape, scale=1, repeats=1):
    """
    Apply a morphological transformation to the image.

    Note that these work better on binary images.

    Generics
    --------
    GreyT: MultiModal[Grey]
        The greyscale image type.

    Parameters
    ----------
    img: GreyT
        The greyscale image to threshold.
    mode: MorphologicalTransform
        The type of transform to apply.
    kernel_size: tuple[int, int]
        The size of the kernel to convolve with the image.
    shape: MorphologicalShape
        The shape of the kernel to convolve with the image. Note that this shape determines which elements are 'on' (1)
        and has nothing to do with the `shape` property of numpy arrays.
    scale: int
        The scaling factor to apply to the kernel.
    repeats: int
        The number of times to apply the transformation.

    Raises
    ------
    ValueError
        If the scale is below 1 or greater than 255.
    """
    if scale < 1 or scale > 255:
        raise ValueError("Kernel scale must be between 1 and 255")
    ColourTransform.check(*kernel_size)
    kernel = cv2.getStructuringElement(shape.to_cv2(), kernel_size) * scale
    if mode == MorphologicalTransform.ERODE:
        func = functools.partial(cv2.erode, kernel=kernel, iterations=repeats)
    elif mode == MorphologicalTransform.DILATE:
        func = functools.partial(cv2.dilate, kernel=kernel, iterations=repeats)
    else:
        func = functools.partial(cv2.morphologyEx, kernel=kernel, iterations=repeats, op=mode.to_cv2())
    img.image.reference()[:] = func(img.image())


def contrast_update(img: GreyT, size: _tuple[int, int], shape: MorphologicalShape, scale=1,
                    repeats=1):
    """
    Use a combination of whitehat and blackhat transforms to update the contrast of a greyscale image.

    Generics
    --------
    GreyT: MultiModal[Grey]
        The greyscale image type.

    Parameters
    ----------
    img: GreyT
        The greyscale image to threshold.
    size: tuple[int, int]
        The size of the kernel to convolve with the image.
    shape: MorphologicalShape
        The shape of the kernel to convolve with the image. Note that this shape determines which elements are 'on' (1)
        and has nothing to do with the `shape` property of numpy arrays.
    scale: int
        The scaling factor to apply to the kernel.
    repeats: int
        The number of times to apply the transformation.

    Raises
    ------
    ValueError
        If the scale is below 1 or greater than 255.
    """
    for _ in range(repeats):
        orig = img
        pre_top = img.copy()
        transform(img, MorphologicalTransform.WHITEHAT, size, shape, scale=scale)
        post_top = img.copy()
        img = pre_top
        transform(img, MorphologicalTransform.BLACKHAT, size, shape, scale=scale)
        post_bottom = img.copy()
        img = orig
        img.image.reference()[:] += post_top - post_bottom


def edge_detection(img: GreyT, minimum: int, maximum: int, kernel_size: int):
    """
    Use the 'Canny' edge detection method to detect edges in the greyscale image.

    Generics
    --------
    GreyT: MultiModal[Grey]
        The greyscale image type.

    Parameters
    ----------
    img: GreyT
        The greyscale image to detect edges on.
    minimum: int
        The minimum intensity gradient for an edge to be detected. Any edges with intensity smaller than this are
        discarded, otherwise are only kept if connected to a 'sure edge'.
    maximum: int
        The maximum intensity gradient for an edge to be detected. Any edges with intensity larger than this are
        classified as a 'sure edge', otherwise are considered to be larger than the minimum.
    kernel_size: int
        The size of the kernel to convolve with the image. As it's a square kernel, this parameter is automatically
        converted to (`kernel_size`, `kernel_size`).
    """
    ColourTransform.check(kernel_size)
    img.image.reference()[:] = cv2.Canny(img.image(), minimum, maximum, apertureSize=kernel_size, L2gradient=True)


class Transform(typing.Generic[TransT]):
    """
    Generic transform attribute for images. Has no other methods, but its subclasses do.

    This obeys the `HasInst` protocol.

    Generics
    --------
    TransT: MultiModal[Colour] or MultiModal[Grey]
        The transformation image type.

    Attributes
    ----------
    _inst: TransT
        The image owner of this object.
    """

    @property
    def instance(self) -> TransT:
        """
        Public access to the owner.

        Returns
        -------
        TransT
            The image owner of this object.

        Raises
        ------
        UnboundLocalError
            If the instance is unbounded.
        """
        if self._inst is None:
            raise UnboundLocalError("Transform has no instance")
        return self._inst

    def __init__(self):
        self._inst: typing.Optional[TransT] = None

    def __get__(self, instance: TransT, owner: typing.Type[TransT]) -> typing_extensions.Self:
        if instance is None:
            return self
        self._inst = instance
        return self

    @staticmethod
    def check(*size: int):
        """
        Check for all sizes being a positive, odd number.

        Every transformation will call this with at least one of its parameters (usually a kernel_size).

        Parameters
        ----------
        *size: int
            The sizes to be checked

        Raises
        ------
        ValueError
            If any size is even or below one.
        """
        if not all(k % 2 and k > 0 for k in size):
            raise ValueError("Kernel size should be positive and odd")


class ColourTransform(Transform[RGBT]):
    """
    Concrete transform that contains transformations related to colour images.

    The attributes are the transformation functions generic on an `RBGT`, but instead are `Mutate` decorators.
    """
    blur = Mutation(blur, default=ReferenceBehaviour.COPY)
    gaussian_blur = Mutation(gaussian_blur, default=ReferenceBehaviour.COPY)
    sharpen = Mutation(sharpen, default=ReferenceBehaviour.COPY)
    median_blur = Mutation(median_blur, default=ReferenceBehaviour.COPY)
    brightness_contrast_update = Mutation(brightness_contrast_update, default=ReferenceBehaviour.COPY)
    rotate = Mutation(rotate, default=ReferenceBehaviour.COPY)


class GreyTransform(Transform[GreyT]):
    """
    Concrete transform that contains transformations related to greyscale images.

    The attributes are the transformation functions generic on an `GreyT`, but instead are `Mutate` decorators.
    """
    threshold = Mutation(threshold, default=ReferenceBehaviour.COPY)
    region_threshold = Mutation(region_threshold, default=ReferenceBehaviour.COPY)
    adaptive_threshold = Mutation(adaptive_threshold, default=ReferenceBehaviour.COPY)
    transform = Mutation(transform, default=ReferenceBehaviour.COPY)
    contrast_update = Mutation(contrast_update, default=ReferenceBehaviour.COPY)
    edge_detection = Mutation(edge_detection, default=ReferenceBehaviour.COPY)
