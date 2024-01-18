"""
Module to represent an image that can be represented with a numpy array.

Encapsulates various cv2 functions as methods in a class.
"""
import functools
import operator
import typing
import warnings

import cv2
import numpy as np

from ._colours import Colour
from ._enums import *
from modular_qt.validators import Include


class Image:
    """
    Class to represent a single image. Has methods to encapsulate cv2 functions.

    :var CMode _colour_type: The colour representation of the image.
    :var Wrap _wrapping: The wrapping mode used. Allows for storing RGB images in only 2D.
    :var RGBOrder _order: The order of the colours in the image.
    :var numpy.ndarray _image: The image stored.
    """

    @property
    def colour_mode(self) -> CMode:
        """
        Public access to the colour mode.

        :return: The colour representation of the image.
        """
        return self._colour_type

    @property
    def colour_order(self) -> RGBOrder:
        """
        Public access to the colour order.

        :return: The order the channels are in.
        """
        return self._order

    @property
    def wrap(self) -> bool:
        """
        Public access to the wrapping.

        :return: Whether an RGB image is stored in 2D.
        """
        return self._wrapping == Wrap.WRAP

    @property
    def size(self) -> tuple[int, int]:
        """
        Public access to the shape of the image. Reverses the numpy conventions.

        :return: The shape of the image in the form (width, height).
        """
        shape = self._image.shape
        return shape[1], shape[0]

    @property
    def image(self) -> np.ndarray:
        """
        Public access to the image. Modifying this image won't affect the original image. Converts the image to float32.

        :return: A float32 version of the channeled image.
        """
        return self.get_image(np.float32)

    @property
    def transform(self):
        """
        Public access to a transformation object, allowing for transformations to update this object.

        :return: A transformer that updates this image with every transformation.
        """
        from . import transforms

        def _post(s: "SrcUpdater"):
            self._image = s.image.image.astype(self._image.dtype)

        class SrcUpdater(transforms.Transformer):
            """
            Special subclass that will affect the original image with every transformation.
            """
            _update = _post

        return SrcUpdater(self)

    @property
    def draw(self):
        """
        Public access to a drawing object, allowing for drawings to update this object.

        :return: A drawing that updates this image with every transformation.
        """
        from . import draw

        def _post(s: "SrcUpdater"):
            self._image = s.image.image.astype(self._image.dtype)

        class SrcUpdater(draw.Drawing):
            """
            Special subclass that will affect the original image with every transformation.
            """
            _update = _post

        return SrcUpdater(self)

    def __init__(self, data: np.ndarray, *, auto_wrap=False, colour=CMode.RGB, data_order=RGBOrder.BGR):
        shape = data.shape
        dims = len(shape)
        if colour == CMode.GREY:
            if auto_wrap:
                raise ValueError("Cannot have a greyscale image with wrapping")
            elif dims == 3 and (np.any(data[:, :, 0] != data[:, :, 1]) or np.any(data[:, :, 1] != data[:, :, 2])):
                raise ValueError("Cannot have 3 dimensional greyscale image")
        elif not auto_wrap and np.any(data > 255):
            raise ValueError("No colour channels should be larger than 255 without wrapping")
        elif np.any(data < 0):
            raise ValueError("No colour channels should be less than 0")
        if dims == 2:
            zeroes = np.zeros((shape[0], shape[1], 3), np.uint64)
            zeroes[:, :, 0] = data
            if not auto_wrap:
                zeroes[:, :, 1] = data
                zeroes[:, :, 2] = data
            data = zeroes
        elif dims != 3:
            raise ValueError(f"Dimensionality mismatch. Should be 2 or 3 dimensional data - got {dims}")
        elif shape[2] != 3:
            raise ValueError(f"Channel mismatch. Should have 3 channels - got {shape[2]}")
        self._colour_type = colour
        self._wrapping = Wrap.WRAP if auto_wrap else Wrap.RAISE
        self._order = data_order
        self._image = data.copy()

    def __bool__(self) -> bool:
        return np.any(self._image)

    def __getitem__(self, item: tuple[int, int]) -> Colour:
        """
        Gets a single pixel's colour. Based on cartesian coordinates, not numpy coordinates.

        :param item: The index of the pixel.
        :return: The colour from the pixel.
        :raises TypeError: If item isn't a tuple of two integers.
        """
        if not isinstance(item, tuple) or len(item) != 2 or not all(isinstance(c, int) for c in item):
            raise TypeError("Item must be a tuple of two co-ordinates")
        getter = functools.partial(self._image.item, item[1], item[0])
        return Colour.from_order(getter(0), getter(1), getter(2), self._order, wrap=(self._wrapping, self._order))

    def __setitem__(self, key: tuple[int, int], value: Colour):
        """
        Changes a single pixel's colour. Based on cartesian coordinates, not numpy coordinates.

        :param key: The index of the pixel.
        :param value: The new colour of the pixel.
        :raises TypeError: If item isn't a tuple of two integers, or if the new colour isn't a colour.
        :raises ValueError: If the new colour isn't a valid colour for the image's colour mode.
        """
        if not isinstance(key, tuple) or len(key) != 2 or not all(isinstance(c, int) for c in key):
            raise TypeError("Key must be a tuple of two co-ordinates")
        elif not isinstance(value, Colour):
            raise TypeError("Value must be a colour")
        if self._colour_type == CMode.GREY and not value.is_grey():
            raise ValueError("Expected greyscale image to have all colour channels the same")
        for i, order in enumerate(self._order.value):
            self._image[key[1], key[0], i] = value[order]

    def __invert__(self) -> "Image":
        """
        Inverts a binary image such that all white pixels become black and vice versa.

        :return: A new binary image.
        :raises TypeError: If the image isn't binary.
        """
        if self.is_binary():
            return Image((self._image == 0) * 255, colour=CMode.GREY, data_order=self._order)
        raise TypeError("Can only invert binary images")

    def is_binary(self) -> bool:
        """
        Method to check if an image is binary (a greyscale image only in black and white).

        :return: Whether a greyscale image only contains 0 and 255.
        """
        b = self._image == 0
        w = self._image == 255
        return self._colour_type == CMode.GREY and np.all(b | w)

    def is_bimodal(self) -> bool:
        """
        Method to check if an image is bimodal (only consisting of two colours).

        :return: Whether an image is bimodal.
        """
        unique_rows = np.unique(self._image.reshape(-1, 3), axis=0)
        return unique_rows.shape[0] == 2

    def colour_space(self) -> typing.Iterator[Colour]:
        """
        Method to find the individual colours within the image.

        :return: Yields the colours one by one.
        """
        for colour_row in np.unique(self._image.reshape(-1, 3), axis=0):
            yield Colour.from_order(*colour_row, order=self._order, wrap=self._wrapping)

    def copy(self) -> "Image":
        """
        Deepcopy the image.

        :return: The same image.
        """
        return Image(self._image.copy(), auto_wrap=self.wrap, colour=self._colour_type, data_order=self._order)

    def from_(self, data: np.ndarray) -> "Image":
        """
        Acts like an alternative constructor, but uses existing instance to copy metadata to new image.

        :param data: The new data to use.
        :return: An image with the new data but the current settings.
        """
        return Image(data, auto_wrap=self.wrap, colour=self._colour_type, data_order=self._order)

    def to_greyscale(self, important_channel: typing.Literal["r", "g", "b"]) -> "Image":
        """
        Convert the image to greyscale.

        :param important_channel: The channel to use as the greyscale channel.
        :return: A new greyscale image.
        """
        if self._colour_type == CMode.GREY:
            return self.copy()
        return Image(self.extract_channel(important_channel), colour=CMode.GREY, data_order=self._order)

    def to_rgb(self) -> "Image":
        """
        Convert the image to RGB.

        :return: A new RGB image.
        """
        if self._colour_type == CMode.RGB:
            return self.copy()
        return Image(self._image, auto_wrap=self.wrap, data_order=self._order)

    def get_channeled_image(self, reorder: RGBOrder = None) -> np.ndarray:
        """
        Method to convert even a wrapped image to a 3D numpy array with each channel being valid colour ranges.

        :param reorder: A way to reorder the channels. Defaults to no reordering.
        :return: A 3D numpy array.
        :raises ValueError: If even after handling wrapping, colour range isn't valid.
        """
        if reorder is None:
            reorder = self._order
        order_map = {self._order.value.index(channel): reorder.value.index(channel) for channel in {"r", "g", "b"}}
        w, h = self.size
        img = np.zeros((h, w, 3))
        for channel in order_map:
            img[:, :, channel] = self._image[:, :, order_map[channel]]
        if self.wrap:
            for i, j in ((0, 1), (1, 2), (2, 0), (0, 1), (1, 2)):
                y_256, x_256 = np.where(img[:, :, i] > 255)
                img[y_256, x_256, j] += img[y_256, x_256, i] - 255
                img[y_256, x_256, i] = 255
        if np.any((img > 255) | (img < 0)):
            raise ValueError("Invalid channel values. Must be between 0 and 255")
        return img.astype(np.uint8)

    def get_image(self, dtype: np.dtype) -> np.ndarray:
        """
        Gets the image in a certain data type.

        :param dtype: The data type to convert to.
        :return: The underlying numpy array typecast.
        """
        return self._image.astype(dtype)

    def get_raw(self) -> np.ndarray:
        """
        Gets the raw underlying numpy array. Modifying this will modify the image.

        :return: The underlying numpy array.
        """
        return self._image

    def get_summed(self) -> np.ndarray:
        """
        Sums all colours within the image. Will undo any wrapping first, such that greyscale images are multiplied by 3.

        :return: A 2D numpy array where each element is the sum of the colours at that co-ordinate.
        """
        channels = self.get_channeled_image()
        return np.sum(channels, axis=2)

    def extract_channel(self, channel: typing.Literal["r", "g", "b"]) -> np.ndarray:
        """
        Extracts a singular channel from the image.

        :param channel: The colour channel to extract.
        :return: A 2D array of the specified channel across the image.
        """
        channels = self.get_channeled_image()
        return channels[:, :, self._order.value.find(channel)]

    def extract_region(self, start: tuple[int, int], end: tuple[int, int], *, x_spec=Include.LOW | Include.HIGH,
                       y_spec=Include.LOW | Include.HIGH) -> "Image":
        """
        Method to extract a specific ROI to look at. Will transform it into an image.

        Any modifications that affect the ROI will affect the original image.
        :param start: The starting cartesian co-ordinates.
        :param end: The ending cartesian co-ordinates.
        :param x_spec: The inclusivity of the x-axis.
        :param y_spec: The inclusivity of the y-axis.
        :return: An Image containing the data this image contains at the specified region.
        """
        (y_start, x_start), (y_end, x_end) = start, end
        if not (x_spec & Include.LOW):
            x_start += 1
        if x_spec & Include.HIGH:
            x_end += 1
        if not (y_spec & Include.LOW):
            y_start += 1
        if y_spec & Include.HIGH:
            y_end += 1
        return self.from_(self._image[y_start:y_end, x_start:x_end])

    def corner_points(self, algorithm: CornerAlgorithm, size: int, ap_size: int, metric: float, *,
                      accuracy=0.01) -> np.ndarray:
        """
        Method to find the corners of the image.

        :param algorithm: The method of searching.
        :param size: The size of the results – in Harris, it is the block size. In Shi-Tomasi, it is the corner count.
        :param ap_size: The aperture size – In Harris, it is the kernel size. In Shi-Tomasi, it is the minimum distance.
        :param metric: The accuracy metric – in Harris, it is 'k'. In Shi-Tomasi, it is the quality level.
        :param accuracy: The percentage of the largest value in the Harris detection to use as a threshold.
        :return: A 2-element tuple containing the cartesian co-ordinates of the points.
        """
        if self._colour_type == CMode.RGB:
            raise TypeError("Can only detect corners in greyscale images")
        elif not 0 <= accuracy <= 1:
            raise ValueError("Accuracy must be between 0 and 1")
        elif size < 0 or ap_size <= 0 or metric <= 0:
            raise ValueError("All parameters must be positive")
        image = self.extract_channel("r").astype(np.float32)
        if algorithm == CornerAlgorithm.HARRIS:
            self.check_kernel(ap_size, size)
            corners = cv2.cornerHarris(image, size, ap_size, metric)
            corners = cv2.dilate(corners, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
            threshold = accuracy * corners.max()
            points = np.array(tuple(zip(*np.where(corners > threshold)))[::-1])
        else:
            if accuracy != 0.01:
                warnings.warn(UserWarning("Accuracy does not affect Shi-Tamasi algorithm"))
            corners = cv2.goodFeaturesToTrack(image, size, metric, ap_size).astype(np.int64)
            points = corners.reshape(-1, 2)
        return points

    def edge_detection(self, minimum: int, maximum: int, k_size: int) -> "Image":
        """
        Perform edge detection on the image by using the Canny method.

        :param minimum: The minimum intensity.
        :param maximum: The maximum intensity.
        :param k_size: The size of the kernel to use. It should be odd and positive.
        :return: An image with only edges remaining.
        :raises TypeError: If the image isn't greyscale.
        :raises ValueError: If the kernel size isn't odd and positive.
        """
        if self._colour_type == CMode.RGB:
            raise TypeError("Edge detection only works on greyscale images")
        self.check_kernel(k_size)
        return Image(
            cv2.Canny(self.get_channeled_image()[:, :, 0], minimum, maximum, apertureSize=k_size, L2gradient=True),
            auto_wrap=self.wrap, colour=CMode.GREY, data_order=self._order
        )

    def vertical_edges(self, k_size: int) -> "Image":
        """
        Perform edge detection on the image by using Sobel derivatives.

        This version is designed to use x-derivatives to compute the vertical lines.
        :param k_size: The size of the kernel to use. It should be odd and positive.
        :return: An image with only vertical edges remaining.
        :raises TypeError: If the image isn't greyscale.
        :raises ValueError: If the kernel size isn't odd and positive.
        """
        if self._colour_type == CMode.RGB:
            raise TypeError("Edge detection only works on greyscale images")
        self.check_kernel(k_size)
        return Image(cv2.Sobel(self.extract_channel("r"), -1, 1, 0, ksize=k_size), auto_wrap=self.wrap,
                     colour=CMode.GREY, data_order=self._order)

    def horizontal_edges(self, k_size: int) -> "Image":
        """
        Perform edge detection on the image by using Sobel derivatives.

        This version is designed to use y-derivatives to compute the horizontal lines.
        :param k_size: The size of the kernel to use. It should be odd and positive.
        :return: An image with only horizontal edges remaining.
        :raises TypeError: If the image isn't greyscale.
        :raises ValueError: If the kernel size isn't odd and positive.
        """
        if self._colour_type == CMode.RGB:
            raise TypeError("Edge detection only works on greyscale images")
        self.check_kernel(k_size)
        return Image(cv2.Sobel(self.extract_channel("r"), -1, 0, 1, ksize=k_size), auto_wrap=self.wrap,
                     colour=CMode.GREY, data_order=self._order)

    def find(self, match: typing.Union[Colour, Colours], *, keep_colour=True) -> "Image":
        """
        Create a bimodal image where non-black pixels are the locations of the found colour.

        The image will be binary if 'keep_colour' is False.
        :param match: The colour to find. Allows for inexact matching by passing in a known colour.
        :param keep_colour: Flag for representing if the search should dismiss the colour.
        :return: A binary image, where black represents no match, and white represents a match
        """
        co_ordinates = self.search(match)
        ys = co_ordinates[:, 1]
        xs = co_ordinates[:, 0]
        if keep_colour:
            shape = self._image.shape
        else:
            shape = self.size[::-1]
        zeroes = np.zeros(shape, dtype=np.uint8)
        if keep_colour:
            zeroes[ys, xs] = self._image[ys, xs]
        else:
            zeroes[ys, xs] = 255
        return Image(zeroes, auto_wrap=self.wrap, data_order=self._order, colour=self._colour_type)

    def replace(self, old: typing.Union[Colour, Colours], new: typing.Union[Colour, Colours]):
        """
        Replaces the specified old colour with the specified new colour.

        Warning – this will undo wrapping on the affected indices!
        :param old: The old colour to replace. Allows for passing in a known colour.
        :param new: The new colour to replace. Allows for passing in a known colour.
        """
        if isinstance(new, Colours):
            new = Colour.from_known(new)
        co_ordinates = self.search(old)
        ys = co_ordinates[:, 1]
        xs = co_ordinates[:, 0]
        self._image[ys, xs] = new.all(self._order)

    def find_replace(self, old: typing.Union[Colour, Colours], new: typing.Union[Colour, Colours]) -> "Image":
        """
        Completes a find operation, then replaces the white with the specified new colour.

        Output will be a bimodal image of black and the new colour.

        Shortcut for::

            new_image = old_image.find(old)
            new_image.replace(Colours.WHITE, new)
        :param old: The old colour to identify.
        :param new: The new colour to replace the old with.
        :return: A new bimodal image.
        """
        new_image = self.find(old, keep_colour=False)
        new_image.replace(Colours.WHITE, new)
        return new_image

    def search(self, colour: typing.Union[Colour, Colours]) -> np.ndarray:
        """
        Search through the image for all co-ordinates of the given colour

        :param colour: The colour to search for. Supports inexact matching through known colours.
        :return: A 2D numpy array containing the cartesian co-ordinates of the given colour.
        """
        if isinstance(colour, Colours):
            colour_sequence = tuple(Colour.colour_space(colour))
        else:
            colour_sequence = (colour,)
        places = []
        image = self.get_channeled_image()
        for match in colour_sequence:
            rgb_match = match.all(self._order)
            r_or_g_or_b = np.where(image == rgb_match, 255, 0)
            if not np.any(r_or_g_or_b):
                continue
            r = r_or_g_or_b[:, :, 0]
            g = r_or_g_or_b[:, :, 1]
            b = r_or_g_or_b[:, :, 2]
            result = r & g & b
            points = np.where(result == 255)
            places.append((tuple(points[1]), tuple(points[0])))
        xs = sum(map(operator.itemgetter(0), places), start=())
        ys = sum(map(operator.itemgetter(1), places), start=())
        return np.array(list(zip(xs, ys)))

    def blur(self, kernel_size: tuple[int, int]):
        """
        Perform normalised averaging on the image by 2D convolution.

        :param kernel_size: The shape of the kernel to use. It should be odd and positive.
        :raises ValueError: If the kernel size isn't odd and positive.
        """
        self.check_kernel(*kernel_size)
        kernel = np.ones(kernel_size, np.float32) / (kernel_size[0] * kernel_size[1])
        self._image = cv2.filter2D(self.image, -1, kernel)

    def gaussian_blur(self, kernel_size: tuple[int, int], sigma=(0, 0)):
        """
        Averages the image using a Gaussian kernel.

        :param kernel_size: The size of the kernel. It should be odd and positive.
        :param sigma: The standard deviation in the x and y directions.
        :raises ValueError: If the kernel size isn't odd and positive.
        """
        self.check_kernel(*kernel_size)
        self._image = cv2.GaussianBlur(self.image, kernel_size, sigmaX=sigma[0], sigmaY=sigma[1])

    def median_blur(self, kernel_size: int):
        """
        Averages the image by taking the median.

        :param kernel_size: The size of the kernel. It should be odd and positive.
        :raises ValueError: If the kernel size isn't odd and positive.
        """
        self.check_kernel(kernel_size)
        self._image = cv2.medianBlur(self.image, kernel_size)

    def sharpen(self, kernel_size: int, scale=1, delta=0):
        """
        Performs the Laplacian of the image to sharpen the lines within the image.

        :param kernel_size: The size of the kernel to use. It should be odd and positive.
        :param scale: The optional scale to apply to the values.
        :param delta: The optional value to add to the image.
        :raises ValueError: If the kernel size isn't odd and positive.
        """
        self.check_kernel(kernel_size)
        self._image = cv2.Laplacian(self.image, -1, ksize=kernel_size, scale=scale, delta=delta)

    def update_contrast(self, contrast: float, brightness: int):
        """
        Updates the contrast and brightness of the image using weighted addition.

        :param contrast: The new contrast (must be larger than 0, with 1 meaning no change).
        :param brightness: The new brightness (must be between -255 and 255, with 0 meaning no change).
        :raises ValueError: If the contrast or brightness isn't valid.
        """
        if contrast <= 0:
            raise ValueError("Contrast must be larger than 0")
        elif not (-255 <= brightness <= 255):
            raise ValueError("Brightness must be between -255 and 255")
        brightness += round(255 * (1 - contrast) / 2)
        self._image = cv2.addWeighted(self.image, contrast, self.image, 0, brightness)

    @staticmethod
    def check_kernel(*kernel_size: int):
        """
        Helper method to check if a kernel is valid shape.

        A valid kernel is odd and positive in all directions.
        :param kernel_size: The size of the kernel.
        :raises ValueError: If the kernel is an invalid shape.
        """
        if not all(k % 2 and k > 0 for k in kernel_size):
            raise ValueError("Kernel size should be positive and odd")

    @classmethod
    def from_file(cls, filename: str, mode=cv2.IMREAD_COLOR, wrap=False, data_order=RGBOrder.BGR) -> "Image":
        """
        Alternative constructor for loading an image from a file.

        :param filename: The path to the file.
        :param mode: The image loading mode, either cv2.IMREAD_COLOR or cv2.IMREAD_GRAYSCALE.
        :param wrap: Whether to wrap the image.
        :param data_order: The order of the colours.
        :return: The loaded image.
        :raises ValueError: If the mode is invalid.
        """
        if mode not in {cv2.IMREAD_COLOR, cv2.IMREAD_GRAYSCALE}:
            raise ValueError("Mode must be cv2.IMREAD_COLOR or cv2.IMREAD_GRAYSCALE")
        img = cv2.imread(filename, mode)
        return cls(img, auto_wrap=wrap, colour=CMode.GREY if mode == cv2.IMREAD_GRAYSCALE else CMode.RGB,
                   data_order=data_order)

    @classmethod
    def blank(cls, size: tuple[int, int], colour=CMode.RGB) -> "Image":
        """
        Alternative constructor for creating a blank image of a given size.

        :param size: The size to create the image.
        :param colour: Whether it is registered as greyscale or RGB.
        :return: A new image, that is all black.
        """
        return Image(np.zeros((size[0], size[1], 3)), colour=colour)

    @staticmethod
    def _binary_op(cv2_func: typing.Callable[[np.ndarray, typing.Union[np.ndarray, float]], np.ndarray],
                   bitwise=False) -> typing.Callable[["Image", typing.Union["Image", float]], "Image"]:
        def binary_op(self: "Image", other: typing.Union["Image", float]) -> "Image":
            """
            Wrapper for binary operations.

            Will find the channeled image for both this image and the other, then will perform the relevant function.
            :param self: The original image. (LHS of the operator).
            :param other: The other image. (RHS of the operator).
            :return: The modified image.
            """
            if not isinstance(other, (Image, int, float)):
                return NotImplemented
            other_binary = isinstance(other, (int, float)) or other.is_binary()
            if bitwise and not (self.is_binary() and other_binary):
                raise TypeError("Can only perform bitwise operations on binary images")
            image = other.get_channeled_image(self._order) if isinstance(other, Image) else other
            mode = self._colour_type
            if isinstance(other, Image):
                if CMode.RGB in {self._colour_type, other.colour_mode}:
                    mode = CMode.RGB
                else:
                    mode = CMode.GREY
            result = cv2_func(self.get_channeled_image(), image)
            if bitwise:
                result = result[:, :, 0]
            return Image(result, colour=mode, data_order=self._order)

        return binary_op

    __add__ = _binary_op(cv2.add)
    __sub__ = _binary_op(cv2.subtract)
    __mul__ = _binary_op(cv2.multiply)
    __truediv__ = _binary_op(cv2.divide)
    __and__ = _binary_op(cv2.bitwise_and, True)
    __or__ = _binary_op(cv2.bitwise_or, True)
    __xor__ = _binary_op(cv2.bitwise_xor, True)
