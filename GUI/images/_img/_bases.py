import abc
import typing
from typing import Set as _set, Tuple as _tuple

import cv2
import numpy as np

try:
    import typing_extensions
except ModuleNotFoundError:
    typing_extensions = typing

from .. import Grey, Colour
from .._aliases import *
from .._enums import *
from .._errors import *
from ._utils import Reference

CType = typing.TypeVar("CType", bound=Colour)


class Image(abc.ABC, typing.Generic[CType]):
    """
    An abstract base class for 2D images that use an underlying array for the pixel values.

    Images can be multimodal or bimodal, RGB or greyscale.

    Generics
    --------
    CType: Colour
        The colour type of the image.

    Abstract Methods
    ----------------
    __setitem__
    get_colours
    find_colour
    replace_by
    copy
    get_channels
    verify_colour
    region
    _verify_type

    Attributes
    ----------
    _data: np.ndarray[`uint8`]
        The image data for channel values between 0-255.
    _order: RGBOrder (default is `BGR`)
        The order of the image. The default aligns with cv2 standard.

    Raises
    ------
    ColourOverflowError
        If the channels overflow.
    """

    @property
    def size(self) -> _tuple[int, int]:
        """
        Public access for the size of the image.

        This is the number of columns (width) and rows (height) of the underlying array.

        Returns
        -------
        tuple[int, int]
            The width and height of the image.
        """
        h, w, *c = self._data.shape
        return w, h

    @property
    def order(self) -> RGBOrder:
        """
        Public access for the order of the image data.

        Returns
        -------
        RGBOrder
            The order of the channels.
        """
        return self._order

    def __init__(self, arr: np.ndarray, *, data_order=RGBOrder.BGR):
        if np.any(arr < 0):
            indices = tuple(zip(*np.nonzero(arr < 0)))
            raise ColourOverflowError(f"Expected all channels to be positive (found negatives at {indices})")
        elif np.any(arr > 255):
            indices = tuple(zip(*np.nonzero(arr > 255)))
            raise ColourOverflowError(f"Expected all channels to be 8-bit (overflowing at {indices})")
        self._data = arr.astype(np.uint8)
        self._order = data_order

    def __str__(self) -> str:
        build = []
        for row in self._data:
            line = []
            for colour in row:
                line.append(str(Colour.spawn(colour, order=self._order)))
            build.append(f"| {' '.join(line)} |")
        return "\n".join(build)

    def __bool__(self) -> bool:
        return bool(self._data.any())

    def __getitem__(self, pos: _tuple[int, int]) -> CType:
        """
        Get a single pixel colour.

        Parameters
        ----------
        pos: tuple[int, int]
            The position of the pixel; uses cartesian convention.

        Returns
        -------
        CType
            The pixel colour.

        Raises
        ------
        TypeError
            If the position is not a tuple of two integers (or .0 floats).
        IndexError
            If the position is out of range.
        """
        if not isinstance(pos, tuple) or len(pos) != 2 or any(int(x) != x for x in pos):
            raise TypeError(f"Expected tuple of cartesian coordinates, got {pos}")
        elif any(c < 0 or c >= s for c, s in zip(pos, self.size)):
            raise IndexError(f"Position {pos} out of range")
        return Colour.spawn(self._data[int(pos[1]), int(pos[0])], order=self._order)

    def __delitem__(self, pos: _tuple[int, int]):
        """
        Set the pixel colour to black.

        Parameters
        ----------
        pos: tuple[int, int]
            The position to clear.

        See Also
        --------
        __setitem__
        """
        self[pos] = Grey(0)

    @abc.abstractmethod
    def __setitem__(self, pos: _tuple[int, int], colour: CType):
        """
        Set the pixel colour at that position.

        Parameters
        ----------
        pos: tuple[int, int]
            The position to change.
        colour: CType
            The colour value for the position.

        Raises
        ------
        TypeError
            If the position is not a tuple of two integers (or .0 floats).
            If the colour is not a valid colour for this image.
        IndexError
            If the position is out of range.
        """
        pass

    def convert_image(self, convert: np.dtype) -> np.ndarray:
        """
        Convert the image from the `uint8` format to a different data type.

        Parameters
        ----------
        convert: numpy.dtype
            The data type to convert to.

        Returns
        -------
        np.ndarray
            A *copy* of the original data.
        """
        return self._data.astype(convert)

    def replace(self, old: CType, new: CType):
        """
        Replace the old colour with the new colour. This will mutate the original data.

        Parameters
        ----------
        old: CType
            The old colour to replace.
        new: CType
            The new colour to replace by.
        """
        self.replace_by(self.find_colour(old), new)

    def find_replace(self, old: CType, new: CType) -> typing_extensions.Self:
        """
        Perform a `replace` operation, on a copy of the original image.

        Parameters
        ----------
        old: CType
            The old colour to replace.
        new: CType
            The new colour to replace by.

        Returns
        -------
        Self
            A copy of the original image, where the old colour was replaced by the new colour.
        """
        copy = self.copy()
        copy.replace(old, new)
        return copy

    def find_replace_by(self, points: _tuple[np.ndarray, np.ndarray], new: CType) -> typing_extensions.Self:
        """
        Perform a `replace_by` operation, on a copy of the original image.

        Parameters
        ----------
        points: np.ndarray (1-dimensional, any integer dtype)
            The points to change.
        new: CType
            The new colour to replace by.

        Returns
        -------
        Self
            A copy of the original image, where the old colour was replaced by the new colour.
        """
        copy = self.copy()
        copy.replace_by(points, new)
        return copy

    @abc.abstractmethod
    def get_colours(self) -> typing.Iterator[CType]:
        """
        Get all the colours used in this image.

        Yields
        ------
        CType
            The colour instances used in this image.
        """
        pass

    @abc.abstractmethod
    def find_colour(self, colour: CType) -> _tuple[np.ndarray, np.ndarray]:
        """
        Get all the points where the colour appears.

        The points are in numpy-indexing format, such that it is a tuple of arrays, one for row-values and one for
        column-values.

        Parameters
        ----------
        colour: CType
            The colour to find.

        Returns
        -------
        tuple[np.ndarray, np.ndarray] (both are 1-dimensional of any integer dtype)
            The points where the colour appears.

        Raises
        ------
        ValueError
            If the colour doesn't appear.
        """
        pass

    @abc.abstractmethod
    def replace_by(self, points: _tuple[np.ndarray, np.ndarray], new: CType):
        """
        Similar to `replace` but rather than acting on a colour, it acts on a series of points.

        These points are in numpy-indexing format, such that it is a tuple of arrays, one for row-values and one for
        column-values. This is for direct compatibility with the `find_colour` function.

        Parameters
        ----------
        points: tuple[np.ndarray, np.ndarray] (both are 1-dimensional of any integer dtype)
            The points to replace.
        new: CType
            The colour to make those points.
        """
        pass

    @abc.abstractmethod
    def copy(self) -> typing_extensions.Self:
        """
        Deep-copy the image and its metadata - any operations performed on this copy will not affect the original.

        Returns
        -------
        Self
            This instance, deep-copied.
        """
        pass

    @abc.abstractmethod
    def get_channels(self, in_order: RGBOrder = None) -> np.ndarray:
        """
        Get the data of the image in a 3D array, showing channel values.

        As it is a re-order, any changes made to this array will not affect the original.

        Parameters
        ----------
        in_order: RGBOrder (default is this instance's order)
            The order in which to display the channels.

        Returns
        -------
        np.ndarray
            (3-dimensional of `uint8` dtype. Shaped into (`h`, `w`, 3) for height `h` and width `w`)
            The data of the image, organised into channels.
        """
        pass

    @abc.abstractmethod
    def verify_colour(self, colour: Colour) -> bool:
        """
        Verify that the colour is valid for this image.

        This validation is also undertaken in any methods that change the colour of pixels in the image.

        Parameters
        ----------
        colour: Colour
            The colour to check.

        Returns
        -------
        bool
            Whether the colour is valid.
        """
        pass

    @abc.abstractmethod
    def region(self, start: _tuple[int, int], end: _tuple[int, int]) -> typing_extensions.Self:
        """
        Find a ROI (Region Of Interest) in the image.

        Parameters
        ----------
        start: tuple[int, int]
            The starting cartesian coordinates. This is assumed to be the top left corner.
        end: tuple[int,int]
            The ending cartesian coordinates. This is assumed to be the bottom right corner.

        Returns
        -------
        Self
            A new image with the same metadata as this instance, but only covering the specified region.
        """
        pass

    @Reference.decorate(default=ReferenceBehaviour.REFER)
    def image(self) -> np.ndarray:
        """
        Get the underlying image array from this image.

        Returns
        -------
        np.ndarray (has the same shape as the input array of this image, but with the dtype `uint8`)
            The underlying image data.
        """
        return self._data

    @abc.abstractmethod
    def _verify_type(self, image: typing.Type["Image"]) -> bool:
        pass

    def _pos_check(self, pos: _tuple[int, int], colour: CType):
        if not isinstance(pos, tuple) or len(pos) != 2 or any(int(x) != x for x in pos):
            raise TypeError(f"Expected tuple of cartesian coordinates, got {pos}")
        elif any(c < 0 or c >= s for c, s in zip(pos, self.size)):
            raise IndexError(f"Position {pos} out of range")
        elif not isinstance(colour, Colour):
            raise TypeError(f"Expected an RGB colour, got {colour}")
        elif not self.verify_colour(colour):
            raise TypeError(f"Cannot use colour {colour} in this image")


class MultiModal(Image[CType], abc.ABC, typing.Generic[CType]):
    """
    An abstract class for 2D images that can contain any number of colours.

    These colours can be RGB or greyscale.

    Generics
    --------
    CType: Colour
        The colour type of the image.

    Abstract Methods
    ----------------
    __setitem__
    get_colours
    find_colour
    replace_by
    get_channels
    verify_colour
    _verify_type
    downchannel

    Raises
    ------
    ColourOverflowError
        If the channels overflow.
    """

    def __add__(self, other: typing.Union["MultiModal[CType]", "Bimodal[CType]"]) -> typing_extensions.Self:
        """
        Adds two images together. This will add the channel values together.

        Parameters
        ----------
        other: MultiModal[CType] | Bimodal[CType]
            The other image to add. Note that they must have the same CType to be added.

        Returns
        -------
        Self
            The combined image.

        Raises
        ------
        ValueError
            If the image sizes do not match.
        """
        if not isinstance(other, (MultiModal, Bimodal)) or not self._verify_type(type(other)):
            return NotImplemented
        if self.size != other.size:
            raise ValueError(f"Image sizes must match ({self.size} != {other.size})")
        return type(self)(cv2.add(self.image.reference(), other.image.reference()))

    def __radd__(self, other: "Bimodal[CType]") -> typing_extensions.Self:
        """
        Adds a bimodal image to this image, upchannelling the result to a MultiModal image.

        Parameters
        ----------
        other: Bimodal[CType]
            The other image to add. Note that it must have the same CType to be added.

        Returns
        -------
        Self
            The combined image.

        Raises
        ------
        ValueError
            If the image sizes do not match.
        """
        return self + other

    def __sub__(self, other: typing.Union["MultiModal[CType]", "Bimodal[CType]"]) -> typing_extensions.Self:
        """
        Subtracts two images together. This will subtract the channel values from each other.

        Parameters
        ----------
        other: MultiModal[CType] | Bimodal[CType]
            The other image to subtract. Note that they must have the same CType to be subtracted.

        Returns
        -------
        Self
            The combined image.

        Raises
        ------
        ValueError
            If the image sizes do not match.
        """
        if not isinstance(other, (MultiModal, Bimodal)) or not self._verify_type(type(other)):
            return NotImplemented
        if self.size != other.size:
            raise ValueError(f"Image sizes must match ({self.size} != {other.size})")
        return type(self)(cv2.subtract(self.image.reference(), other.image.reference()))

    def __rsub__(self, other: "Bimodal[CType]") -> typing_extensions.Self:
        """
        Subtracts a bimodal image from this image, upchannelling the result to a MultiModal image.

        Parameters
        ----------
        other: Bimodal[CType]
            The other image to subtract. Note that it must have the same CType to be subtracted.

        Returns
        -------
        Self
            The combined image.

        Raises
        ------
        ValueError
            If the image sizes do not match.
        """
        if not isinstance(other, Bimodal) or not self._verify_type(type(other)):
            return NotImplemented
        if self.size != other.size:
            raise ValueError(f"Image sizes must match ({other.size} != {self.size})")
        return type(self)(cv2.subtract(other.image.reference(), self.image.reference()))

    def copy(self) -> typing_extensions.Self:
        return type(self)(self._data.copy(), data_order=self._order)

    @abc.abstractmethod
    def downchannel(self, bg: CType, fg: CType, *, invalid_handler: BimodalBehaviour = None) -> "Bimodal[CType]":
        """
        Downchannels the image to be a bimodal image using only the foreground and background colours.

        Parameters
        ----------
        bg: CType
            The background colour. Any non-foreground colour will become this background colour.
        fg: CType
            The foreground colour. This must appear.
        invalid_handler: BimodalBehaviour
            The handler for invalid colours in the source image. Default is to leave them in, raising errors.

        Returns
        -------
        Bimodal[CType]
            A bimodal image using the foreground and background colours.
        """
        pass

    def region(self, start: _tuple[int, int], end: _tuple[int, int]) -> typing_extensions.Self:
        (sx, sy), (ex, ey) = start, end
        return type(self)(self._data[sy:ey + 1, sx:ex + 1], data_order=self._order)


class Bimodal(Image[CType], abc.ABC, typing.Generic[CType]):
    """
    An abstract class for 2D images that can contain at most two colours. These colours must be specified at creation.

    These colours can be RGB or greyscale. Whenever a public operation is performed (or a magic method), the image is
    checked for only the foreground and background colours appearing.

    Generics
    --------
    CType: Colour
        The colour type of the image.

    Abstract Methods
    ----------------
    __setitem__
    get_colours
    find_colour
    replace_by
    get_channels
    verify_colour
    _verify_type
    upchannel
    _gc

    Attributes
    ----------
    _bg: CType
        The background colour of the image.
    _fg: CType
        The foreground colour of the image.
    _colours: set[CType]
        The set of colours in the image.

    Raises
    ------
    ColourOverflowError
        If the channels overflow.
    """
    _gc = Image.get_colours

    @property
    def colours(self) -> _set[CType]:
        """
        The colours of the image. This will be a set, for O(1) container checks.

        Returns
        -------
        set[CType]
            The foreground and background colours of the image.
        """
        return self._colours

    @property
    def fg(self) -> CType:
        """
        Public access to the foreground colour.

        Returns
        -------
        CType
            The foreground colour of the image.
        """
        return self._fg

    @property
    def bg(self) -> CType:
        """
        Public access to the background colour.

        Returns
        -------
        CType
            The background colour of the image.
        """
        return self._bg

    def __init__(self, arr: np.ndarray, background: CType, foreground: CType, *, data_order=RGBOrder.BGR):
        super().__init__(arr, data_order=data_order)
        self._bg, self._fg = background, foreground
        self._colours = {self._fg, self._bg}
        self.cheap_op()

    def __str__(self) -> str:
        self.cheap_op()
        return super().__str__()

    def __bool__(self) -> bool:
        self.cheap_op()
        return super().__bool__()

    def __getattribute__(self, item: str):
        if not item.startswith("_"):
            colours = set(self._gc())
            if len(colours) > 1 and (self._fg not in colours or self._bg not in colours):
                raise TypeError(f"Background and foreground don't match expected values. "
                                f"Expected: {str(self._bg), str(self._fg)}, got: {tuple(map(str, colours))}")
        return super().__getattribute__(item)

    def __or__(self, other: "Bimodal[CType]") -> typing_extensions.Self:
        """
        Compute the union of two bimodal images. These images must have the same two colours.

        This is similar to a bitwise or, such that areas where the foreground colour appears in either image will be
        present in this image.

        The operation *may not* be commutative; as the requirement is that the same two colours *appear*, not that the
        foreground and background are identical (such that a binary image with a white background is compatible with a
        binary image with a black background, as they both contain only back and white).

        Parameters
        ----------
        other: Bimodal[CType]
            The other image to combine.

        Returns
        -------
        Self
            The combined image, that has the foreground areas of both images.

        Raises
        ------
        ValueError
            If the image sizes do not match.
        TypeError
            If the two images do not have the same colour.
        """
        if not isinstance(other, Bimodal) or not self._verify_type(type(other)):
            return NotImplemented
        self._bin_check(other)
        fg_points = other.find_colour(other.fg)
        return self.find_replace_by(fg_points, other.fg)

    def __and__(self, other: "Bimodal[CType]") -> typing_extensions.Self:
        """
        Compute the intersection of two bimodal images. These images must have the same two colours.

        This is similar to a bitwise and, such that areas where the foreground colour appears in both images will be
        present in this image.

        The operation *may not* be commutative; as the requirement is that the same two colours *appear*, not that the
        foreground and background are identical (such that a binary image with a white background is compatible with a
        binary image with a black background, as they both contain only back and white).

        Parameters
        ----------
        other: Bimodal[CType]
            The other image to filter.

        Returns
        -------
        Self
            The combined image; that has the foreground areas only present in both images.

        Raises
        ------
        ValueError
            If the image sizes do not match.
        TypeError
            If the two images do not have the same colour.
        """
        if not isinstance(other, Bimodal) or not self._verify_type(type(other)):
            return NotImplemented
        self._bin_check(other)
        s_fg_points = np.array(tuple(zip(*self.find_colour(self._fg))))
        o_fg_points = np.array(tuple(zip(*other.find_colour(other.fg))))
        matches, = np.nonzero(np.bitwise_and.reduce(s_fg_points == o_fg_points, axis=1))
        co_ords = s_fg_points[matches]
        ys = co_ords[:, 0]
        xs = co_ords[:, 1]
        new = self.find_replace(self._fg, self._bg)
        return new.find_replace_by((ys, xs), self._fg)

    def __xor__(self, other: "Bimodal[CType]") -> typing_extensions.Self:
        """
        Compute the exclusive or of two bimodal images. These images must have the same two colours.

        This is similar to a bitwise xor, such that areas where the foreground colour appears in only one image will be
        present in this image.

        The operation *may not* be commutative; as the requirement is that the same two colours *appear*, not that the
        foreground and background are identical (such that a binary image with a white background is compatible with a
        binary image with a black background, as they both contain only back and white).

        Parameters
        ----------
        other: Bimodal[CType]
            The other image to combine with.

        Returns
        -------
        Self
            The combined image; that has the foreground areas only present in one images.

        Raises
        ------
        ValueError
            If the image sizes do not match.
        TypeError
            If the two images do not have the same colour.
        """
        if not isinstance(other, Bimodal) or not self._verify_type(type(other)):
            return NotImplemented
        self._bin_check(other)
        o_fg_points = np.array(tuple(zip(*other.find_colour(other.fg))))
        s_fg_points = np.array(tuple(zip(*self.find_colour(self._fg))))
        matches, = np.nonzero(np.bitwise_xor.reduce(s_fg_points != o_fg_points, axis=1))
        co_ords = s_fg_points[matches]
        ys = co_ords[:, 0]
        xs = co_ords[:, 1]
        new = self.find_replace(self._fg, self._bg)
        return new.find_replace_by((ys, xs), self._fg)

    def __invert__(self) -> typing_extensions.Self:
        """
        Will invert the image such that the foreground areas become the background areas (and vice versa).

        It will then invert the foreground and background colours - so the foreground colour becomes the background
        colour and vice versa.

        This means that:
            >>> self.find_colour(self.fg) == (~self).find_colour((~self).bg)

        Returns
        -------
        Self
            The inverted image.
        """
        try:
            fg_points = self.find_colour(self._fg)
        except ValueError:
            fg_points = (np.array([], dtype=np.uint8), np.array([], dtype=np.uint8))
        try:
            bg_points = self.find_colour(self._bg)
        except ValueError:
            bg_points = (np.array([], dtype=np.uint8), np.array([], dtype=np.uint8))
        all_bg = self.find_replace_by(fg_points, self._bg)
        all_bg.replace_by(bg_points, self._fg)
        return type(self)(all_bg.image.reference(), self._fg, self._bg, data_order=self._order)

    def copy(self) -> typing_extensions.Self:
        return type(self)(self._data.copy(), self._bg, self._fg, data_order=self._order)

    @abc.abstractmethod
    def upchannel(self) -> MultiModal[CType]:
        """
        Upchannels the image to be a multimodal image.

        Returns
        -------
        MultiModal[CType]
            A multimodal image using the foreground and background colours of this image.
        """
        pass

    def region(self, start: _tuple[int, int], end: _tuple[int, int]) -> typing_extensions.Self:
        (sx, sy), (ex, ey) = start, end
        return type(self)(self._data[sy:ey + 1, sx:ex + 1], self._bg, self._fg, data_order=self._order)

    def _bin_check(self, other: "Bimodal[CType]"):
        if self.size != other.size:
            raise ValueError(f"Image sizes must match ({self.size} != {other.size})")
        elif (self._fg not in other.colours or self._bg not in other.colours or
              other.fg not in self.colours or other.bg not in self.colours):
            s_colours = tuple(map(str, self.colours))
            o_colours = tuple(map(str, other.colours))
            raise TypeError(f"Image colours must match ({s_colours} != {o_colours})")

    def verify_colour(self, colour: Colour) -> bool:
        return colour in self._colours

    def cheap_op(self):
        """
        A public method that does nothing.
        This is a cheap operation performed on this image to get during magic methods, or non-public methods. This is to
        trigger the image check.
        """
        pass


class RGB(Image[Colour], abc.ABC):
    """
    An abstract class for 2D images that can contain any colour.

    Bound Generics
    --------------
    CType: Colour

    Abstract Methods
    ----------------
    demote

    Raises
    ------
    TypeError
        If the underlying array isn't 3-dimensional.
    DepthError
        If the underlying array's third dimensional isn't 3.
    ColourOverflowError
        If the channels overflow.
    """

    def __init__(self, arr: np.ndarray, *, data_order=RGBOrder.BGR):
        if arr.ndim != 3:
            raise TypeError(f"Expected a 3-dimensional array, got {arr.ndim} instead")
        elif (channels := arr.shape[-1]) != 3:
            raise DepthError(3, channels)
        super().__init__(arr, data_order=data_order)

    def __setitem__(self, pos: _tuple[int, int], colour: Colour):
        self._pos_check(pos, colour)
        self._data[pos[1], pos[0]] = colour.items(self._order)

    def replace_by(self, points: _tuple[np.ndarray, np.ndarray], new: Colour):
        self.verify_colour(new)
        self._data[points] = new.items(self._order)

    def get_colours(self) -> typing.Iterator[Colour]:
        for colour in np.unique(self._data.reshape(-1, 3), axis=0):
            yield Colour.spawn(colour, order=self._order)

    def find_colour(self, colour: Colour) -> _tuple[np.ndarray, np.ndarray]:
        if colour not in self.get_colours():
            raise ValueError(f"{colour} doesn't appear")
        points = np.where(self._data == colour.items(self._order), 1, 0).astype(np.bool_)
        nonzero = np.nonzero(np.bitwise_and.reduce(points, axis=2))
        return nonzero[0], nonzero[1]

    def get_channels(self, in_order: RGBOrder = None) -> np.ndarray:
        if in_order is None:
            in_order = self._order
        s_map = {self._order.index(c): c for c in self._order.items()}
        n_map = {c: in_order.index(c) for c in self._order.items()}
        new = np.zeros(self._data.shape, dtype=np.uint8)
        for i in range(3):
            new[:, :, i] = self._data[:, :, n_map[s_map[i]]]
        return new

    @Reference.decorate(default=ReferenceBehaviour.REFER)
    def channel(self, channel: Channel) -> np.ndarray:
        """
        Get a single channel value from the array.

        Parameters
        ----------
        channel: Channel
            The channel to get.

        Returns
        -------
        np.ndarray (2-dimensional, `uint8` dtype, of shape (`w`, `h`) for width `w` and height `h`.
            The channel value across all pixels.
        """
        return self._data[:, :, self._order.index(channel)]

    @abc.abstractmethod
    def demote(self, keep: Channel) -> "Greyscale":
        """
        Demote the RGB image to a greyscale image. This will keep one channel value across all pixels.

        Parameters
        ----------
        keep: Channel
            The channel to keep.

        Returns
        -------
        Greyscale
            The greyscale image made from the selected channel across all pixels.
        """
        pass

    def _verify_type(self, colour: typing.Type[Image]) -> bool:
        return True

    def verify_colour(self, colour: Colour) -> bool:
        return True


class Greyscale(Image[Grey], abc.ABC):
    """
    An abstract class for 2D images that can contain only shades of grey.

    Bound Generics
    --------------
    CType: Grey

    Abstract Methods
    ----------------
    promote

    Raises
    ------
    TypeError
        If the underlying array isn't 2- or 3-dimensional.
    DepthError
        If the underlying array is 3-dimensional.
    ColourOverflowError
        If the channels overflow.
    """

    def __init__(self, arr: np.ndarray, *, data_order=RGBOrder.BGR):
        if arr.ndim not in {2, 3}:
            raise TypeError(f"Expected a 2-dimensional array, got {arr.ndim} instead")
        elif arr.ndim == 3:
            raise DepthError(1, arr.shape[-1])
        super().__init__(arr, data_order=data_order)

    def __setitem__(self, pos: _tuple[int, int], colour: Grey):
        self._pos_check(pos, colour)
        self._data[pos[1], pos[0]] = colour["r"]

    def replace_by(self, points: _tuple[np.ndarray, np.ndarray], new: Grey):
        self.verify_colour(new)
        self._data[points] = new["r"]

    def get_colours(self) -> typing.Iterator[Grey]:
        for colour in np.unique(self._data.flatten()):
            yield Grey(colour)

    def find_colour(self, colour: Colour) -> _tuple[np.ndarray, np.ndarray]:
        if colour not in self.get_colours():
            raise ValueError(f"{colour} doesn't appear")
        nonzero = np.nonzero(np.where(self._data == colour["r"], 1, 0).astype(np.bool_))
        return nonzero[0], nonzero[1]

    def get_channels(self, in_order: RGBOrder = None) -> np.ndarray:
        new = np.zeros((self._data.shape[0], self._data.shape[1], 3), dtype=np.uint8)
        for i in range(3):
            new[:, :, i] = self._data.copy()
        return new

    @Reference.decorate(default=ReferenceBehaviour.REFER)
    def channel(self, channel: Channel) -> np.ndarray:
        """
        Get a single channel value from the array.

        Parameters
        ----------
        channel: Channel
            The channel to get. As all channels are the same, this parameter is only validated as a channel.

        Returns
        -------
        np.ndarray (2-dimensional, `uint8` dtype, of shape (`w`, `h`) for width `w` and height `h`.
            The channel value across all pixels. As the underlying data is 2-dimensional, this is the *raw* array.
        """
        if channel not in "rgb":
            raise TypeError(f"Invalid channel {channel}")
        return self._data

    @abc.abstractmethod
    def promote(self) -> RGB:
        """
        Promote the greyscale image to an RGB image.

        This will promote the underlying to 3-dimensions, using the same value across all channels.

        Returns
        -------
        RGB
            The RGB image made from the only channel across all pixels.
        """
        pass

    def _verify_type(self, colour: typing.Type[Image]) -> bool:
        return issubclass(colour, Greyscale)

    def verify_colour(self, colour: Colour) -> bool:
        return isinstance(colour, Grey)
