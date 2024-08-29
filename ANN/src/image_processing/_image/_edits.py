import functools
import operator
from typing import Optional as _None, Tuple as _tuple, Type as _type

import cv2
import numpy as np
import typing_extensions

from ._bases import Image
from ._enums import *
from ._utils import OnHasImg, ThresholdBehaviour, ThresholdType


class BaseTransform:
    """
    Base artist designed to store state for subclasses.

    Attributes
    ----------
    _img: Image
        The image to transform.
    """

    @property
    def instance(self) -> _None[Image]:
        """
        Public access to the stored Image instance.

        Returns
        -------
        Image
            The image to Transform.
        """
        return self._img

    @instance.setter
    def instance(self, value: Image):
        self._img = value

    def __init__(self, img: Image = None):
        self._img: _None[Image] = img

    def __get__(self, instance: _None[Image], owner: _type[Image]) -> typing_extensions.Self:
        self._img = instance
        return self

    @staticmethod
    def _check(*sizes: int):
        if not all(s % 2 and s > 0 for s in sizes):
            raise ValueError("Kernel size should be odd and positive")


class BlurTransform(BaseTransform):
    """
    Concrete transformation that blurs the image.
    """

    @OnHasImg.decorate(default=ReferBehavior.COPY)
    def basic(self, k_size: _tuple[int, int]):
        """
        Perform blurring by 2D convolution with a normalised box kernel.

        Parameters
        ----------
        k_size: tuple[int, int]
            The size of the kernel. Should be odd and positive.

        Raises
        ------
        ValueError
            If the kernel size is invalid.
        """
        self._check(*k_size)
        kernel = np.ones(k_size, dtype=np.float32) / functools.reduce(operator.mul, k_size)
        self._img.data()[:, :] = cv2.filter2D(self._img.convert(np.float32), -1, kernel)

    @OnHasImg.decorate(default=ReferBehavior.COPY)
    def gaussian(self, k_size: _tuple[int, int], sigma=(0, 0)):
        """
        Perform blurring by 2D convolution with a gaussian kernel.

        Parameters
        ----------
        k_size: tuple[int, int]
            The size of the kernel. Should be odd and positive.
        sigma: tuple[int, int]
            The standard deviation in x and y. Use 0 for an axis to automatically calculate the best value.

        Raises
        ------
        ValueError
            If the kernel size is invalid.
        """
        self._check(*k_size)
        self._img.data()[:, :] = cv2.GaussianBlur(self._img.convert(np.float32), k_size, sigmaX=sigma[0],
                                                  sigmaY=sigma[1])

    @OnHasImg.decorate(default=ReferBehavior.COPY)
    def median(self, k_size: int):
        """
        Perform median blurring

        Parameters
        ----------
        k_size: int
            The square size of the kernel. Should be odd and positive.

        Raises
        ------
        ValueError
            If the kernel size is invalid.
        """
        self._check(k_size)
        self._img.data()[:, :] = cv2.medianBlur(self._img.convert(np.float32), k_size)


class SharpenTransform(BaseTransform):
    """
    Concrete transformation that sharpens the image.
    """

    @OnHasImg.decorate(default=ReferBehavior.COPY)
    def sharpen(self, k_size: int, scale=1, delta=0):
        """
        Sharpen the image using laplacian derivatives.

        Parameters
        ----------
        k_size: int
            The kernel size. Should be odd and positive.
        scale: int
            The kernel factor. Should be natural.
        delta: int
            The kernel term. The resulting kernel is made from multiplying by `scale` and adding `delta`.

        Raises
        ------
        ValueError
            If the kernel size is invalid.
            If the scale is not natural.
        """
        self._check(k_size)
        if scale <= 0:
            raise ValueError("Scale should be a natural number")
        self._img.data()[:, :] = cv2.Laplacian(self._img.convert(np.float32), -1, ksize=k_size, scale=scale,
                                               delta=delta)


class BasicTransform(BaseTransform):
    """
    Concrete transformation that performs basic operations.
    """

    @OnHasImg.decorate(default=ReferBehavior.COPY)
    def translate(self, by: _tuple[int, int]):
        """
        Translate the image by a vector.

        Parameters
        ----------
        by: tuple[int, int]
            The translation vector.
        """
        mat = np.float32([[1, 0, by[0]], [0, 1, by[1]]])
        self._img.data()[:, :] = cv2.warpAffine(self._img.convert(np.float32), mat, self._img.size)

    @OnHasImg.decorate(default=ReferBehavior.COPY)
    def rotate(self, theta: float, anchor: _tuple[int, int] = None):
        """
        Rotate the image by a certain angle.

        Parameters
        ----------
        theta: float
            Rotation angle in degrees.
        anchor: tuple[int, int] | None
            The anchor point. Defaults to centre.

        Raises
        ------
        IndexError
            If the anchor point is invalid.
        """
        w, h = self._img.size
        if anchor is None:
            anchor = (w // 2 - 1, h // 2 - 1)
        else:
            _ = self._img[anchor]
        mat = cv2.getRotationMatrix2D(anchor, theta, 1)
        self._img.data()[:, :] = cv2.warpAffine(self._img.convert(np.float32), mat, self._img.size)


class ThresholdTransform(BaseTransform):
    """
    Concrete transformation to threshold the image.
    """

    @OnHasImg.decorate(default=ReferBehavior.COPY)
    def global_(self, mode: ThresholdType):
        """
        Perform global thresholding.

        Parameters
        ----------
        mode: ThresholdType
            The type of thresholding to apply.
        """
        data = self._img.data()
        for behaviour, mask in zip(
                (mode.less, mode.equal, mode.greater),
                (data < mode.threshold, data == mode.threshold, data > mode.threshold)
        ):
            data[mask] = behaviour.handle(data[mask])

    @OnHasImg.decorate(default=ReferBehavior.COPY)
    def region(self, in_bounds: ThresholdBehaviour, out_bounds: ThresholdBehaviour):
        """
        Perform global thresholding around a region of valid values.

        This divides the image into 'in range' and 'out of range' partitions.

        Parameters
        ----------
        in_bounds: ThresholdBehaviour
            The behaviour to apply to intensities in the range provided.
        out_bounds: ThresholdBehaviour
            The behaviour to apply to intensities out of the range provided.
        """
        data = self._img.data()
        out = (data > out_bounds.pin) | (data < in_bounds.pin)
        in_ = ~out
        data[out] = out_bounds.handle(data[out])
        data[in_] = in_bounds.handle(data[in_])

    @OnHasImg.decorate(default=ReferBehavior.COPY)
    def edge_detection(self, minima: int, maxima: int, k_size: int):
        """
        Binarise the image by using Canny edge detection.

        Parameters
        ----------
        minima: int
            The minimum intensity gradient for an edge to be detected. Any edges with intensity smaller than this are
            discarded, otherwise are only kept if connected to a 'sure edge'.
        maxima: int
            The maximum intensity gradient for an edge to be detected. Any edges with intensity larger than this are
            classified as a 'sure edge', otherwise are considered to be larger than the minimum.
        k_size: int
            The square kernel size. Should be odd and positive.

        Raises
        ------
        ValueError
            If the kernel size is invalid.
        """
        self._check(k_size)
        self._img.data()[:, :] = cv2.Canny(self._img.convert(np.float32), minima, maxima, apertureSize=k_size,
                                           L2gradient=True)


class MorphologicalTransform(BaseTransform):

    @OnHasImg.decorate(default=ReferBehavior.COPY)
    def erode(self, k_size: _tuple[int, int], shape: MorphologicalShape, scale=1, repeats=1):
        """
        Perform morphological erosion on the image.

        Erosion will erase the foreground.

        Parameters
        ----------
        k_size: tuple[int, int]
            The size of the kernel. Should be odd and positive.
        shape: MorphologicalShape
            The shape of the kernel.
        scale: int
            The kernel scale. Should be constrained to an unsigned 8-bit value.
        repeats: int
            The number of times to perform the erosion.

        Raises
        ------
        ValueError
            If the kernel size is invalid.
            If the scale cannot fit into eight bits.
        """
        if scale < 1 or scale > 255:
            raise ValueError("Kernel scale should be between 1 and 255")
        self._check(*k_size)
        kernel = cv2.getStructuringElement(shape.to_cv2(), k_size) * scale
        self._img.data()[:, :] = cv2.erode(self._img.convert(np.float32), kernel, iterations=repeats)

    @OnHasImg.decorate(default=ReferBehavior.COPY)
    def dilate(self, k_size: _tuple[int, int], shape: MorphologicalShape, scale=1, repeats=1):
        """
        Perform morphological dilation on the image.

        Dilation will enhance the foreground.

        Parameters
        ----------
        k_size: tuple[int, int]
            The size of the kernel. Should be odd and positive.
        shape: MorphologicalShape
            The shape of the kernel.
        scale: int
            The kernel scale. Should be constrained to an unsigned 8-bit value.
        repeats: int
            The number of times to perform the erosion.

        Raises
        ------
        ValueError
            If the kernel size is invalid.
            If the scale cannot fit into eight bits.
        """
        if scale < 1 or scale > 255:
            raise ValueError("Kernel scale should be between 1 and 255")
        self._check(*k_size)
        kernel = cv2.getStructuringElement(shape.to_cv2(), k_size) * scale
        self._img.data()[:, :] = cv2.dilate(self._img.convert(np.float32), kernel, iterations=repeats)

    @OnHasImg.decorate(default=ReferBehavior.COPY)
    def open(self, k_size: _tuple[int, int], shape: MorphologicalShape, scale=1, repeats=1):
        """
        Perform morphological opening on the image.

        Opening will perform erosion then dilation, to remove small salt (white) noise.

        Parameters
        ----------
        k_size: tuple[int, int]
            The size of the kernel. Should be odd and positive.
        shape: MorphologicalShape
            The shape of the kernel.
        scale: int
            The kernel scale. Should be constrained to an unsigned 8-bit value.
        repeats: int
            The number of times to perform the erosion.

        Raises
        ------
        ValueError
            If the kernel size is invalid.
            If the scale cannot fit into eight bits.
        """
        if scale < 1 or scale > 255:
            raise ValueError("Kernel scale should be between 1 and 255")
        self._check(*k_size)
        kernel = cv2.getStructuringElement(shape.to_cv2(), k_size) * scale
        self._img.data()[:, :] = cv2.morphologyEx(self._img.convert(np.float32), cv2.MORPH_OPEN, kernel,
                                                  iterations=repeats)

    @OnHasImg.decorate(default=ReferBehavior.COPY)
    def close(self, k_size: _tuple[int, int], shape: MorphologicalShape, scale=1, repeats=1):
        """
        Perform morphological closing on the image.

        Closing will perform dilation then erosion, to remove small pepper (black) noise.

        Parameters
        ----------
        k_size: tuple[int, int]
            The size of the kernel. Should be odd and positive.
        shape: MorphologicalShape
            The shape of the kernel.
        scale: int
            The kernel scale. Should be constrained to an unsigned 8-bit value.
        repeats: int
            The number of times to perform the erosion.

        Raises
        ------
        ValueError
            If the kernel size is invalid.
            If the scale cannot fit into eight bits.
        """
        if scale < 1 or scale > 255:
            raise ValueError("Kernel scale should be between 1 and 255")
        self._check(*k_size)
        kernel = cv2.getStructuringElement(shape.to_cv2(), k_size) * scale
        self._img.data()[:, :] = cv2.morphologyEx(self._img.convert(np.float32), cv2.MORPH_CLOSE, kernel,
                                                  iterations=repeats)

    @OnHasImg.decorate(default=ReferBehavior.COPY)
    def gradient(self, k_size: _tuple[int, int], shape: MorphologicalShape, scale=1, repeats=1):
        """
        Find the difference between the dilation and erosion of an image.

        Parameters
        ----------
        k_size: tuple[int, int]
            The size of the kernel. Should be odd and positive.
        shape: MorphologicalShape
            The shape of the kernel.
        scale: int
            The kernel scale. Should be constrained to an unsigned 8-bit value.
        repeats: int
            The number of times to perform the erosion.

        Raises
        ------
        ValueError
            If the kernel size is invalid.
            If the scale cannot fit into eight bits.
        """
        if scale < 1 or scale > 255:
            raise ValueError("Kernel scale should be between 1 and 255")
        self._check(*k_size)
        kernel = cv2.getStructuringElement(shape.to_cv2(), k_size) * scale
        self._img.data()[:, :] = cv2.morphologyEx(self._img.convert(np.float32), cv2.MORPH_GRADIENT, kernel,
                                                  iterations=repeats)

    @OnHasImg.decorate(default=ReferBehavior.COPY)
    def whitehat(self, k_size: _tuple[int, int], shape: MorphologicalShape, scale=1, repeats=1):
        """
        Find the difference between the image and its morphological opening.

        Parameters
        ----------
        k_size: tuple[int, int]
            The size of the kernel. Should be odd and positive.
        shape: MorphologicalShape
            The shape of the kernel.
        scale: int
            The kernel scale. Should be constrained to an unsigned 8-bit value.
        repeats: int
            The number of times to perform the erosion.

        Raises
        ------
        ValueError
            If the kernel size is invalid.
            If the scale cannot fit into eight bits.
        """
        if scale < 1 or scale > 255:
            raise ValueError("Kernel scale should be between 1 and 255")
        self._check(*k_size)
        kernel = cv2.getStructuringElement(shape.to_cv2(), k_size) * scale
        self._img.data()[:, :] = cv2.morphologyEx(self._img.convert(np.float32), cv2.MORPH_TOPHAT, kernel,
                                                  iterations=repeats)

    @OnHasImg.decorate(default=ReferBehavior.COPY)
    def blackhat(self, k_size: _tuple[int, int], shape: MorphologicalShape, scale=1, repeats=1):
        """
        Find the difference between the morphological closing of an image and itself.

        Parameters
        ----------
        k_size: tuple[int, int]
            The size of the kernel. Should be odd and positive.
        shape: MorphologicalShape
            The shape of the kernel.
        scale: int
            The kernel scale. Should be constrained to an unsigned 8-bit value.
        repeats: int
            The number of times to perform the erosion.

        Raises
        ------
        ValueError
            If the kernel size is invalid.
            If the scale cannot fit into eight bits.
        """
        if scale < 1 or scale > 255:
            raise ValueError("Kernel scale should be between 1 and 255")
        self._check(*k_size)
        kernel = cv2.getStructuringElement(shape.to_cv2(), k_size) * scale
        self._img.data()[:, :] = cv2.morphologyEx(self._img.convert(np.float32), cv2.MORPH_BLACKHAT, kernel,
                                                  iterations=repeats)


class ColourTransform(BasicTransform, SharpenTransform):
    """
    Concrete transformer that can access all non-greyscale operations.
    """

    @property
    def blur(self) -> BlurTransform:
        """
        Public access to the blurring transformations.

        Returns
        -------
        BlurTransform
            The transformer controlling blur operations
        """
        return BlurTransform(self._img)


class GreyTransform(MorphologicalTransform):
    """
    Concrete transformer that can access all greyscale operations.
    """

    @property
    def threshold(self) -> ThresholdTransform:
        """
        Public access to the thresholding transformations.

        Returns
        -------
        ThresholdTransform
            The transformer controlling thresholding operations.
        """
        return ThresholdTransform(self._img)
