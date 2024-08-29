import typing_extensions
import cv2
import numpy as np
from typing import Tuple as _tuple

from ._bases import BiModal, Grey, MultiModal, RGB
from ._enums import *
from ._drawings import Artist
from ._edits import ColourTransform, GreyTransform


class RGBImage(RGB, MultiModal):
    """
    A concrete image representing a full colourspace with no limitations on colour count.

    Attributes
    ----------
    drawings: Artist
        The artist that can draw on the image.
    transform: ColourTransform
        The transformer that can edit this image.
    """
    drawings = Artist()
    transform = ColourTransform()

    def demote(self) -> "GreyImage":
        return GreyImage(self._data.copy(), static_range=self._min if self._min is None else (self._min, self._max))

    def downchannel(self, bg: np.int_, fg: np.int_, *, invalid: ColourConvert = None) -> "BiModal":
        if invalid is None:
            return RGBBimodal(self._data.copy(), bg, fg,
                              static_range=self._min if self._min is None else (self._min, self._max))
        keep, remaining = (fg, bg) if invalid == ColourConvert.TO_BG else (bg, fg)
        new = np.ones_like(self._data) * remaining
        new[np.nonzero(self._data == keep)] = keep
        return RGBBimodal(new, bg, fg, static_range=self._min if self._min is None else (self._min, self._max))

    def norm(self) -> typing_extensions.Self:
        norm = self._range(self._data, int(self.black), int(self.white), 0, 2 ** 24 - 1)
        return RGBImage(norm, static_range=self._min if self._min is None else (0, 2 ** 24 - 1))

    @classmethod
    def from_file(cls, path: str, *, do_static=False) -> "RGBImage":
        """
        Alternative constructor to create an image from a file.

        Parameters
        ----------
        path: str
            The path to the file.
        do_static: bool
            Whether the image should have a static range of intensities.

        Returns
        -------
        RGBImage
            The created image.

        Raises
        ------
        FileNotFoundError
            If the file doesn't exist.
        """
        arr = cv2.imread(path, cv2.IMREAD_COLOR)
        if arr is None:
            raise FileNotFoundError(f"File {path!r} not found")
        arr = np.uint32(arr)
        r = arr[:, :, 2] << 16
        g = arr[:, :, 1] << 8
        b = arr[:, :, 0]
        return cls((r | g | b).astype(np.int_), static_range=(0, 2 ** 24 - 1) if do_static else None)

    @classmethod
    def blank(cls, size: _tuple[int, int], black: np.int_ = 0, *, static_range: _tuple[int, int] = None) -> "RGBImage":
        """
        Alternative constructor to create a blank image.

        Parameters
        ----------
        size: tuple[int, int]
            The size of the blank image.
        black: int_
            The intensity representing a black pixel.
        static_range: tuple[int, int] | None
            The static range of the image.

        Returns
        -------
        RGBImage
            The blank image.
        """
        return cls(np.ones((size[1], size[0]), dtype=np.int_) * black, static_range=static_range)


class GreyImage(Grey, MultiModal):
    """
    A concrete image representing a greyscale colourspace with no limitations on colour count.

    Attributes
    ----------
    drawings: Artist
        The artist that can draw on the image.
    transform: ColourTransform
        The transformer that can edit this image.
    grey_transform: GreyTransform
        The transformer for greyscale-specific operations.
    """
    drawings = Artist()
    transform = ColourTransform()
    grey_transform = GreyTransform()

    def promote(self) -> RGBImage:
        return RGBImage(self._data.copy(), static_range=self._min if self._min is None else (self._min, self._max))

    def downchannel(self, bg: np.int_, fg: np.int_, *, invalid: ColourConvert = None) -> "BiModal":
        if invalid is None:
            return GreyBimodal(self._data.copy(), bg, fg,
                               static_range=self._min if self._min is None else (self._min, self._max))
        keep, remaining = (fg, bg) if invalid == ColourConvert.TO_BG else (bg, fg)
        new = np.ones_like(self._data) * remaining
        new[np.nonzero(self._data == keep)] = keep
        return GreyBimodal(new, bg, fg, static_range=self._min if self._min is None else (self._min, self._max))

    def norm(self) -> typing_extensions.Self:
        return GreyImage(self._range(self._data, int(self.black), int(self.white), 0, 255),
                         static_range=self._min if self._min is None else (0, 255))

    @classmethod
    def from_file(cls, path: str, *, do_static=False) -> "GreyImage":
        """
        Alternative constructor to create an image from a file.

        Parameters
        ----------
        path: str
            The path to the file.
        do_static: bool
            Whether the image should have a static range of intensities.

        Returns
        -------
        GreyImage
            The created image.

        Raises
        ------
        FileNotFoundError
            If the file doesn't exist.
        """
        arr = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if arr is None:
            raise FileNotFoundError(f"File {path!r} not found")
        return cls(np.int_(arr), static_range=(0, 255) if do_static else None)

    @classmethod
    def blank(cls, size: _tuple[int, int], black: np.int_ = 0, *, static_range: _tuple[int, int] = None) -> "GreyImage":
        """
        Alternative constructor to create a blank image.

        Parameters
        ----------
        size: tuple[int, int]
            The size of the blank image.
        black: int_
            The intensity representing a black pixel.
        static_range: tuple[int, int] | None
            The static range of the image.

        Returns
        -------
        GreyImage
            The blank image.
        """
        return cls(np.ones((size[1], size[0]), dtype=np.int_) * black, static_range=static_range)


class RGBBimodal(RGB, BiModal):
    """
    A concrete image representing a full colourspace with at most two colours.

    Attributes
    ----------
    drawings: Artist
        The artist that can draw on the image.
    transform: ColourTransform
        The transformer that can edit this image.
    """
    drawings = Artist()
    transform = ColourTransform()
    __getattribute__ = BiModal.__getattribute__

    def demote(self) -> "GreyBimodal":
        return GreyBimodal(self._data.copy(), self._bg, self._fg,
                           static_range=self._min if self._min is None else (self._min, self._max))

    def upchannel(self) -> RGBImage:
        return RGBImage(self._data.copy(), static_range=self._min if self._min is None else (self._min, self._max))

    def norm(self) -> typing_extensions.Self:
        normalised = RGBImage(self._range(self._data, int(self.black), int(self.white), 0, 2 ** 24 - 1))
        c1, c2 = normalised.get_colours()
        return RGBBimodal(normalised.data(), c1, c2, static_range=self._min if self._min is None else (c1, c2))

    @classmethod
    def blank(cls, size: _tuple[int, int], exp_fg: np.int_, black: np.int_ = 0, *,
              static_range: _tuple[int, int] = None) -> "RGBBimodal":
        """
        Alternative constructor to create a blank image.

        Parameters
        ----------
        size: tuple[int, int]
            The size of the blank image.
        exp_fg: int_
            The expected foreground colour.
        black: int
            The intensity representing a black pixel.
        static_range: tuple[int, int] | None
            The static range of the image.

        Returns
        -------
        RGBBimodal
            The blank image.
        """
        return cls(np.ones((size[1], size[0]), dtype=np.int_) * black, black, exp_fg, static_range=static_range)


class GreyBimodal(Grey, BiModal):
    """
   A concrete image representing a greyscale colourspace with at most two colours.

   Attributes
   ----------
   drawings: Artist
       The artist that can draw on the image.
   transform: ColourTransform
       The transformer that can edit this image.
   grey_transform: GreyTransform
       The transformer for greyscale-specific operations.
   """
    drawings = Artist()
    transform = ColourTransform()
    grey_transform = GreyTransform()

    def promote(self) -> RGBBimodal:
        return RGBBimodal(self._data.copy(), self._bg, self._fg,
                          static_range=self._min if self._min is None else (self._bg, self._fg))

    def upchannel(self) -> GreyImage:
        return GreyImage(self._data.copy(), static_range=self._min if self._min is None else (self._min, self._max))

    def norm(self) -> typing_extensions.Self:
        normalised = GreyImage(self._range(self._data, int(self.black), int(self.white), 0, 255))
        c1, c2 = normalised.get_colours()
        return GreyBimodal(normalised.data(), c1, c2, static_range=self._min if self._min is None else (c1, c2))

    @classmethod
    def blank(cls, size: _tuple[int, int], exp_fg: np.int_, black: np.int_ = 0, *,
              static_range: _tuple[int, int] = None) -> "GreyBimodal":
        """
        Alternative constructor to create a blank image.

        Parameters
        ----------
        size: tuple[int, int]
            The size of the blank image.
        exp_fg: int_
            The expected foreground colour.
        black: int
            The intensity representing a black pixel.
        static_range: tuple[int, int] | None
            The static range of the image.

        Returns
        -------
        GreyImage
            The blank image.
        """
        return cls(np.ones((size[1], size[0]), dtype=np.int_) * black, black, exp_fg, static_range=static_range)
