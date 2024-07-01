import abc
from typing import Tuple as _tuple, Set as _set

import cv2
import numpy as np
import numpy.typing as npt
import typing_extensions
from ._utils import OnImg
from ._enums import *


class Image(abc.ABC):
    """
    Abstract base class for all image classes. Defines an image as a 2D array of unconstrained values.

    When plotting, the array can be normalised to a particular range.
    As the array may have certain conditions (bimodality, a specific range), every attribute lookup will check the array
    to ensure these properties have not been violated.

    Abstract Methods
    ----------------
    region
    copy
    normalise
    norm
    verify
    static
    dynamic

    Attributes
    ----------
    _data: array[int, [r, c]]
        The image data.
    _min: int_ | None
        The minimum allowed value in the image.
    _max: int_ | None
        The maximum allowed value in the image.

    Raises
    ------
    ValueError
        If the provided array is not 2D.
    TypeError
        If the array has an incorrect dtype.
    """

    @property
    def size(self) -> _tuple[int, int]:
        """
        Public access to the width and height of the image.

        Returns
        -------
        tuple[int, int]
            The image size in pixels.
        """
        r, c = self._data.shape
        return c, r

    @property
    def black(self) -> np.int_:
        """
        Public access to the value considered black.

        Returns
        -------
        int_
            The lowest value in the image.
        """
        if self._min is not None:
            return self._min
        return np.min(self._data)

    @property
    def white(self) -> np.int_:
        """
        Public access to the value considered white.

        Returns
        -------
        int_
            The highest value in the image.
        """
        if self._max is not None:
            return self._max
        return np.max(self._data)

    def __init__(self, data: npt.NDArray[np.int_], *, static_range: _tuple[np.int_, np.int_] = None):
        if len(data.shape) != 2:
            raise ValueError("Only 2D images are supported")
        elif data.dtype != np.int_:
            raise TypeError(f"Expected an integer array ({np.int_}), but got {data.dtype}")
        self._data = data
        if static_range is None:
            self._min = self._max = static_range
        else:
            self._min, self._max = static_range
        self._cheap()

    def __getattribute__(self, item: str):
        if item == "_cheap" or not item.startswith("_"):
            if (self._min is not None and self._max is not None) and np.any(
                    (self._data < self._min) | (self._data > self._max)
            ):
                raise TypeError(f"Array has been edited externally! Elements are out of static bounds")
        return super().__getattribute__(item)

    def __bool__(self) -> bool:
        self._cheap()
        return bool(np.any(self._data != self.black))

    def __getitem__(self, pos: _tuple[int, int]) -> np.int_:
        """
        Extract the colour from a particular pixel.

        Parameters
        ----------
        pos: tuple[int, int]
            The x-y position.

        Returns
        -------
        int_
            The pixel colour.

        Raises
        ------
        TypeError
            If the position is not a tuple of 2D cartesian co-ordinates.
        IndexError
            If the position is out of range.
        """
        self._cheap()
        if not isinstance(pos, tuple) or len(pos) != 2 or any(int(x) != x for x in pos):
            raise TypeError(f"Expected tuple of cartesian coordinates, got {pos}")
        elif any(c < 0 or c >= s for c, s in zip(pos, self.size)):
            raise IndexError(f"Position {pos} out of range")
        return self._data[pos[1], pos[0]]

    def __setitem__(self, pos: _tuple[int, int], value: np.int_):
        """
        Change the colour of a particular pixel.

        Parameters
        ----------
        pos: tuple[int, int]
            The x-y position.
        value: int_
            The pixel colour.

        Raises
        ------
        TypeError
            If the position is not a tuple of 2D cartesian co-ordinates.
        IndexError
            If the position is out of range.
        ValueError
            If the new colour cannot be verified.
        """
        if not isinstance(pos, tuple) or len(pos) != 2 or any(int(x) != x for x in pos):
            raise TypeError(f"Expected tuple of cartesian coordinates, got {pos}")
        elif any(c < 0 or c >= s for c, s in zip(pos, self.size)):
            raise IndexError(f"Position {pos} out of range")
        elif not self.verify(value):
            raise ValueError(f"Colour {value} is not valid")
        self._data[pos[1], pos[0]] = value

    def _cheap(self):
        pass

    def convert(self, dtype: npt.DTypeLike) -> np.ndarray:
        """
        Convert the underlying array to a new data type.

        Parameters
        ----------
        dtype: DType
            The new data type.

        Returns
        -------
        ndarray[dtype]
            The converted array.
        """
        return self._data.astype(dtype)

    def find(self, colour: np.int_) -> _tuple[np.ndarray, np.ndarray]:
        """
        Find the co-ordinates of a colour, in numpy advanced indexing format.

        Parameters
        ----------
        colour: int_
            The colour to search for.

        Returns
        -------
        tuple[ndarray[int_, [r]], [ndarray[int_, [c]]]]
            The co-ordinates of the colour.
        """
        return np.nonzero(self._data == colour)

    def replace(self, old: np.int_, new: np.int_):
        """
        Replace all instances of the old colour with the new colour.

        Parameters
        ----------
        old: int_
            The old colour to replace.
        new: int_
            The colour to replace it with.
        """
        self.replace_by(self.find(old), new)

    def find_replace(self, old: np.int_, new: np.int_) -> typing_extensions.Self:
        """
        Perform a `replace` operation, but on a new image.

        Parameters
        ----------
        old: int_
            The old colour to replace.
        new: int_
            The colour to replace it with.

        Returns
        -------
        Self
            A copy of this image, with the replace operation performed.
        """
        copy = self.copy()
        copy.replace(old, new)
        return copy

    def replace_by(self, co_ords: _tuple[np.ndarray, np.ndarray], new: np.int_):
        """
        Perform a replace operation, based on co-ordinates in numpy format.

        Parameters
        ----------
        co_ords: tuple[ndarray[int_, [r]], [ndarray[int_, [c]]]]
            The co-ordinates to replace.
        new: int_
            The new colour.

        Raises
        ------
        ValueError
            If the colour cannot be verified.
        """
        if not self.verify(new):
            raise ValueError(f"Invalid colour {new} for image")
        self._data[co_ords] = new

    def find_replace_by(self, co_ords: _tuple[np.ndarray, np.ndarray], new: np.int_) -> typing_extensions.Self:
        """
        Perform a `replace_by` operation, but on a new image.

        Parameters
        ----------
        co_ords: tuple[ndarray[int_, [r]], [ndarray[int_, [c]]]]
            The co-ordinates to replace.
        new: int_
            The new colour.

        Returns
        -------
        Self
            A copy of this image, with the replace operation performed.
        """
        copy = self.copy()
        copy.replace_by(co_ords, new)
        return copy

    def get_colours(self) -> _set[np.int_]:
        """
        Return the unique colours in the image.

        Returns
        -------
        set[int_]
            The set of unique colours in the image.
        """
        return set(np.unique(self._data))

    @OnImg.decorate(default=ReferBehavior.REFER)
    def data(self) -> npt.NDArray[np.int_]:
        """
        Get the underlying image array.

        Returns
        -------
        ndarray[int_, [r, c]]
            The image array.
        """
        return self._data

    @abc.abstractmethod
    @OnImg.decorate(default=ReferBehavior.REFER)
    def region(self, start: _tuple[int, int], end: _tuple[int, int]) -> typing_extensions.Self:
        """
        Extract a square region from the image.

        Parameters
        ----------
        start: tuple[int, int]
            The top left corner.
        end: tuple[int, int]
            The bottom right corner.

        Returns
        -------
        Self
            The extracted region.
        """
        pass

    @abc.abstractmethod
    def copy(self) -> typing_extensions.Self:
        """
        Copy the image.

        Returns
        -------
        Self
            The deep-copied image.
        """
        pass

    @abc.abstractmethod
    def normalise(self, i: int) -> int:
        """
        Normalise am integer to the colour range of the image.

        Parameters
        ----------
        i: int
            The number to normalise.

        Returns
        -------
        int
            The normalised colour.
        """
        pass

    @abc.abstractmethod
    def norm(self) -> typing_extensions.Self:
        """
        Return a normalised version of the image.

        Returns
        -------
        Self
            The normalised image.
        """
        pass

    @abc.abstractmethod
    def verify(self, colour: np.int_) -> bool:
        """
        Verify the colour is valid.

        Parameters
        ----------
        colour: int_
            The colour to test.

        Returns
        -------
        bool
            Whether the colour is valid.
        """
        pass

    @abc.abstractmethod
    def static(self, minima: np.int_, maxima: np.int_) -> typing_extensions.Self:
        """
        Make a new image using a static range.

        Parameters
        ----------
        minima: int_
            The lowest value in the range.
        maxima: int_
            The highest value in the range.

        Returns
        -------
        Self
            The static image.
        """
        pass

    @abc.abstractmethod
    def dynamic(self) -> typing_extensions.Self:
        """
        Make a new image removing the static range.

        Returns
        -------
        Self
            The new image, without any static range.
        """
        pass

    @staticmethod
    def _range(i: npt.ArrayLike, o_min: int, o_max: int, n_min: int, n_max: int) -> npt.ArrayLike:
        i = np.float_(i)
        o_r = (o_max - o_min)
        n_r = (n_max - n_min)
        min_reduced = (i - o_min)
        normalised = min_reduced * n_r
        ratio = normalised / o_r
        converted = ratio + n_min
        return np.int_(converted)


class MultiModal(Image, abc.ABC):
    """
    A base class for multi-modal images. Multi-modal images are images with an unlimited number of colours.

    Abstract Methods
    ----------------
    downchannel
    copy
    normalise
    norm
    static
    dynamic
    """

    def __add__(self, other: "MultiModal") -> typing_extensions.Self:
        """
        Perform element-wise addition.

        This performs a cv2-based addition.

        Parameters
        ----------
        other: MultiModal
            The other image to add.

        Returns
        -------
        Self
            The combined image.

        Raises
        ------
        ValueError
            If the image sizes do not match.
        """
        self._cheap()
        if not isinstance(other, MultiModal):
            return NotImplemented
        if self.size != other.size:
            raise ValueError(f"Image sizes must match (got {self.size = } and {other.size = })")
        return type(self)(cv2.add(self.data(), other.data()),
                          static_range=self._min if self._min is None else (self._min, self._max))

    def __sub__(self, other: "MultiModal") -> typing_extensions.Self:
        """
        Perform element-wise subtraction.

        This performs a cv2-based subtraction.

        Parameters
        ----------
        other: MultiModal
            The other image to subtract.

        Returns
        -------
        Self
            The combined image.

        Raises
        ------
        ValueError
            If the image sizes do not match.
        """
        self._cheap()
        if not isinstance(other, MultiModal):
            return NotImplemented
        if self.size != other.size:
            raise ValueError(f"Image sizes must match (got {self.size = } and {other.size = })")
        return type(self)(cv2.subtract(self.data(), other.data()),
                          static_range=self._min if self._min is None else (self._min, self._max))

    @abc.abstractmethod
    def downchannel(self, bg: np.int_, fg: np.int_, *, invalid: ColourConvert = None) -> "BiModal":
        """
        Convert the image to a bimodal image.

        Parameters
        ----------
        bg: int_
            The background colour.
        fg: int_
            The foreground colour.
        invalid: ColourConvert | None
            How to handle invalid colours. If None, it will raise an error.

        Returns
        -------
        BiModal
            The bimodal image.
        """
        pass

    def copy(self) -> typing_extensions.Self:
        return type(self)(self._data.copy(), static_range=self._min if self._min is None else (self._min, self._max))

    @OnImg.decorate(default=ReferBehavior.REFER)
    def region(self, start: _tuple[int, int], end: _tuple[int, int]) -> typing_extensions.Self:
        (sx, sy), (ex, ey) = start, end
        return type(self)(self._data[sy:ey + 1, sx:ex + 1],
                          static_range=self._min if self._min is None else (self._min, self._max))

    def verify(self, colour: np.int_) -> bool:
        if self._min is not None and self._max is not None:
            return self._min <= colour <= self._max
        return True


class BiModal(Image, abc.ABC):
    """
    A base class for bimodal images. Bimodal images are images with at most two colours.

    Abstract Methods
    ----------------
    upchannel
    copy
    normalise
    norm
    static
    dynamic

    Attributes
    ----------
    _bg: int_
        The background colour.
    _fg: int_
        The foreground colour.
    """

    @property
    def fg(self) -> np.int_:
        """
        Public access to the foreground colour.

        Returns
        -------
        int_
            The foreground colour.
        """
        return self._fg

    @property
    def bg(self) -> np.int_:
        """
        Public access to the background colour.

        Returns
        -------
        int_
            The background colour.
        """
        return self._bg

    def __init__(self, data: npt.NDArray[np.int_], exp_bg: np.int_, exp_fg: np.int_, *,
                 static_range: _tuple[np.int_, np.int_] = None):
        self._bg, self._fg = exp_bg, exp_fg
        super().__init__(data, static_range=static_range)
        if self._min is not None and self._max is not None:
            if (self._bg != self._min and self._bg != self._max) or (self._fg != self._min and self._fg != self._max):
                raise ValueError(f"Static range should be the minima and maxima in bimodal images "
                                 f"(got {self._fg = }, {self._bg = }, {self._min = }, {self._max = })")

    def __getattribute__(self, item: str):
        if item == "_cheap" or not item.startswith("_"):
            if np.any((self._data != self._fg) & (self._data != self._bg)):
                raise TypeError(f"Array has been edited externally! Invalid colours appear")
        return super().__getattribute__(item)

    def __or__(self, other: "BiModal") -> typing_extensions.Self:
        """
        Combine two bimodal images by combining foreground images similar to a bitwise or.

        Parameters
        ----------
        other: BiModal
            The other bimodal image.

        Returns
        -------
        Self
            The combined image.

        Raises
        ------
        ValueError
            If image sizes don't match.
        TypeError
            If the image colours don't match.
        """
        if not isinstance(other, BiModal):
            return NotImplemented
        self._meshable(other)
        fg_points = other.find(other.fg)
        return self.find_replace_by(fg_points, other.fg)

    def __and__(self, other: "BiModal") -> typing_extensions.Self:
        """
        Combine two bimodal images by combining foreground images similar to a bitwise and.

        Parameters
        ----------
        other: BiModal
            The other bimodal image.

        Returns
        -------
        Self
            The combined image.

        Raises
        ------
        ValueError
            If image sizes don't match.
        TypeError
            If the image colours don't match.
        """
        if not isinstance(other, BiModal):
            return NotImplemented
        self._meshable(other)
        co_ord = np.dtype([("y", np.int_), ("x", np.int_)])
        s_fg = np.argwhere(self._data == self._fg).astype(co_ord)
        o_fg = np.argwhere(other.data() == other.fg).astype(co_ord)
        comb = np.isin(s_fg, o_fg)
        ys = comb[:, 1]
        xs = comb[:, 0]
        mask = ys & xs
        co_ords = s_fg[mask]
        new = self.find_replace(self._fg, self._bg)
        return new.find_replace_by((co_ords[["y"]].astype(np.int_), co_ords[["x"]].astype(np.int_)), self._fg)

    def __xor__(self, other: "BiModal") -> typing_extensions.Self:
        """
        Combine two bimodal images by combining foreground images similar to a bitwise xor.

        Parameters
        ----------
        other: BiModal
            The other bimodal image.

        Returns
        -------
        Self
            The combined image.

        Raises
        ------
        ValueError
            If image sizes don't match.
        TypeError
            If the image colours don't match.
        """
        if not isinstance(other, BiModal):
            return NotImplemented
        self._meshable(other)
        co_ord = np.dtype([("y", np.int_), ("x", np.int_)])
        s_fg = np.argwhere(self._data == self._fg).astype(co_ord)
        o_fg = np.argwhere(other.data() == other.fg).astype(co_ord)
        comb = np.isin(s_fg, o_fg, invert=True)
        ys = comb[:, 1]
        xs = comb[:, 0]
        co_ords = s_fg[ys & xs]
        new = self.find_replace(self._fg, self._bg)
        return new.find_replace_by((co_ords[["y"]].astype(np.int_), co_ords[["x"]].astype(np.int_)), self._fg)

    def __invert__(self) -> typing_extensions.Self:
        """
        Invert both the order and the positions of the colours within the image.

        Returns
        -------
        Self
            The inverted image.
        """
        fg = self.find(self._fg)
        bg = self.find(self._bg)
        all_bg = self.find_replace_by(fg, self._bg)
        all_bg.replace_by(bg, self._fg)
        return type(self)(all_bg.data(), self._fg, self._bg,
                          static_range=self._min if self._min is None else (self._min, self._max))

    @abc.abstractmethod
    def upchannel(self) -> MultiModal:
        """
        Convert the image to a multimodal image.

        Returns
        -------
        MultiModal
            The converted image.
        """
        pass

    def copy(self) -> typing_extensions.Self:
        return type(self)(self._data.copy(), self._bg, self._fg,
                          static_range=self._min if self._min is None else (self._min, self._max))

    @OnImg.decorate(default=ReferBehavior.REFER)
    def region(self, start: _tuple[int, int], end: _tuple[int, int]) -> typing_extensions.Self:
        (sx, sy), (ex, ey) = start, end
        return type(self)(self._data[sy:ey + 1, sx:ex + 1], self._bg, self._fg,
                          static_range=self._min if self._min is None else (self._min, self._max))

    def get_colours(self) -> _set[np.int_]:
        return {self._bg, self._fg}

    def _meshable(self, other: "BiModal"):
        o_colours = other.get_colours()
        s_colours = self.get_colours()
        if self.size != other.size:
            raise ValueError(f"Image sizes must match (got {self.size = } and {other.size = })")
        elif s_colours != o_colours:
            raise TypeError(f"Image colours must match (got {s_colours = } and {o_colours = })")

    def verify(self, colour: np.int_) -> bool:
        return colour == self._bg or colour == self._fg


class RGB(Image, abc.ABC):
    """
    Base class to represent an image capable of covering the full RGB colour space.

    Abstract Methods
    ----------------
    demote
    copy
    norm
    static
    dynamic
    """

    def channel(self, channel: Channel) -> npt.NDArray[np.int_]:
        """
        Get a particular colour channel.

        Parameters
        ----------
        channel: Channel
            The channel to extract

        Returns
        -------
        ndarray[int_, [r, c]]
            The array representing the colour channel.
        """
        data = self._data
        normalised = self.norm().data()
        if channel == Channel.R:
            mask = (normalised >= 0) & (normalised < 2 ** 8)
        elif channel == Channel.G:
            mask = (normalised >= 2 ** 8) & (normalised < 2 ** 16)
        else:
            mask = (normalised >= 2 ** 16) & (normalised < 2 ** 24)
        return data[mask]

    @abc.abstractmethod
    def demote(self) -> "Grey":
        """
        Demote this image to a greyscale colour space.

        Returns
        -------
        Grey
            The greyscale image.
        """
        pass

    def make_red(self, strength=1.0, brightness=0.0) -> np.int_:
        """
        Make a red colour.

        Parameters
        ----------
        strength: float
            The strength of the red - the weaker the colour, the closer to black it is.
        brightness: float
            The brightness of the red - the brighter the colour, the closer to white it is.

        Returns
        -------
        int_
            The red colour based on the black-white range of the image.

        Raises
        ------
        ValueError
            If strength is greater than 1 or less than or equal to 0.
            If brightness is greater than or equal to 1 or less than 0.
        """
        if not (0 < strength <= 1):
            raise ValueError("Strength can only be between 0 and 1. For strength 0, make a grey colour instead.")
        elif not (0 <= brightness < 1):
            raise ValueError("Brightness can only be between 0 and 1. For brightness 1, make a grey colour instead.")
        r = np.int_(strength * 255)
        g = np.int_(brightness * 255)
        b = np.int_(brightness * 255)
        return self._range(r << 16 | g << 8 | b, 0, 2 ** 24 - 1, int(self.black), int(self.white))

    def make_green(self, strength=1.0, brightness=0.0) -> np.int_:
        """
        Make a green colour.

        Parameters
        ----------
        strength: float
            The strength of the green - the weaker the colour, the closer to black it is.
        brightness: float
            The brightness of the green - the brighter the colour, the closer to white it is.

        Returns
        -------
        int_
            The green colour based on the black-white range of the image.

        Raises
        ------
        ValueError
            If strength is greater than 1 or less than or equal to 0.
            If brightness is greater than or equal to 1 or less than 0.
        """
        if not (0 < strength <= 1):
            raise ValueError("Strength can only be between 0 and 1. For strength 0, make a grey colour instead.")
        elif not (0 <= brightness < 1):
            raise ValueError("Brightness can only be between 0 and 1. For brightness 1, make a grey colour instead.")
        r = np.int_(brightness * 255)
        g = np.int_(strength * 255)
        b = np.int_(brightness * 255)
        return self._range(r << 16 | g << 8 | b, 0, 2 ** 24 - 1, int(self.black), int(self.white))

    def make_blue(self, strength=1.0, brightness=0.0) -> np.int_:
        """
        Make a blue colour.

        Parameters
        ----------
        strength: float
            The strength of the blue - the weaker the colour, the closer to black it is.
        brightness: float
            The brightness of the blue - the brighter the colour, the closer to white it is.

        Returns
        -------
        int_
            The blue colour based on the black-white range of the image.

        Raises
        ------
        ValueError
            If strength is greater than 1 or less than or equal to 0.
            If brightness is greater than or equal to 1 or less than 0.
        """
        if not (0 < strength <= 1):
            raise ValueError("Strength can only be between 0 and 1. For strength 0, make a grey colour instead.")
        elif not (0 <= brightness < 1):
            raise ValueError("Brightness can only be between 0 and 1. For brightness 1, make a grey colour instead.")
        r = np.int_(brightness * 255)
        g = np.int_(brightness * 255)
        b = np.int_(strength * 255)
        return self._range(r << 16 | g << 8 | b, 0, 2 ** 24 - 1, int(self.black), int(self.white))

    def make_grey(self, strength: float) -> np.int_:
        """
        Make a grey colour.

        Parameters
        ----------
        strength: float
            The strength of the grey - the stronger the colour, the closer to white it is.

        Returns
        -------
        int_
            The grey colour based on the black-white range of the image.

        Raises
        ------
        ValueError
            If strength is greater than 1 or less than 0.
        """
        if not (0 <= strength <= 1):
            raise ValueError("Strength can only be between 0 and 1")
        grey = np.int_(strength * 255)
        return self._range(grey << 16 | grey << 8 | grey, 0, 2 ** 24 - 1, int(self.black), int(self.white))

    def normalise(self, i: np.int_) -> int:
        return self._range(i, int(self.black), int(self.white), 0, 2 ** 24 - 1)


class Grey(Image, abc.ABC):
    """
    Base class to represent an image capable of covering the greyscale colour space.

    Abstract Methods
    ----------------
    promote
    copy
    norm
    static
    dynamic
    """

    def grey(self, i: int) -> npt.NDArray[np.int_]:
        """
        Extract a particular gray intensity colour.

        Parameters
        ----------
        i: int
            The grey intensity to extract.

        Returns
        -------
        ndarray[int_, [r, c]]
            The array representing the gray intensity colour.

        Raises
        ------
        ValueError
            If the intensity is not between 0 and 255
        """
        if not (0 <= i <= 255):
            raise ValueError("Intensity is between 0 and 255")
        normalised = self.norm().data()
        return self._data[normalised == i]

    def make_grey(self, strength: float) -> np.int_:
        """
        Make a grey colour.

        Parameters
        ----------
        strength: float
            The strength of the grey - the stronger the colour, the closer to white it is.

        Returns
        -------
        int_
            The grey colour based on the black-white range of the image.

        Raises
        ------
        ValueError
            If strength is greater than 1 or less than 0.
        """
        if not (0 <= strength <= 1):
            raise ValueError("Strength can only be between 0 and 1")
        return self._range(np.int_(strength * 255), 0, 255, int(self.black), int(self.white))

    @abc.abstractmethod
    def promote(self) -> RGB:
        """
        Convert the image to an image capable of handling the full RGB colour space.

        Returns
        -------
        RGB
            The full colour space image.
        """
        pass

    def normalise(self, i: int) -> int:
        return self._range(i, int(self.black), int(self.white), 0, 255)
