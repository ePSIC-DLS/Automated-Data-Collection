import typing
from typing import Tuple as _tuple

import cv2
import numpy as np

try:
    import typing_extensions
except ModuleNotFoundError:
    typing_extensions = typing

from .. import Grey, Colour
from .._aliases import *
from .._enums import *
from ._bases import RGB, MultiModal, Greyscale, Bimodal, Image
from ._transformations import ColourTransform, GreyTransform
from ._drawings import Drawing


class FullDepthImage(RGB, MultiModal[Colour]):
    """
    Concrete RGB, Multimodal image.

    Attributes
    ----------
    transform: ColourTransform[FullDepthImage]
        The transformation object to allow for editing and transforming the image.
    drawing: Drawing[Colour]
        The drawing object to allow for editing and painting the image.
    """
    __init__ = RGB.__init__
    transform = ColourTransform["FullDepthImage"]()
    drawing = Drawing[Colour]()

    def demote(self, keep: Channel) -> "GreyscaleImage":
        return GreyscaleImage(self.channel.copy(keep), data_order=self._order)

    def downchannel(self, bg: Colour, fg: Colour, *,
                    invalid_handler: BimodalBehaviour = None) -> "BimodalFullDepthImage":
        if invalid_handler is None:
            return BimodalFullDepthImage(self._data, bg, fg, data_order=self._order)
        if invalid_handler == BimodalBehaviour.BG:
            keep = fg
            remaining = bg
        else:
            keep = bg
            remaining = fg
        r_mask = np.where(self._data[:, :, 0] == keep["r"], 1, 0)
        g_mask = np.where(self._data[:, :, 1] == keep["g"], 1, 0)
        b_mask = np.where(self._data[:, :, 2] == keep["b"], 1, 0)
        masked_image = r_mask & g_mask & b_mask
        keep_points = np.nonzero(masked_image)
        new = np.zeros_like(self._data)
        new[:, :, :] = remaining.items(self._order)
        new[keep_points] = keep.items(self._order)
        return BimodalFullDepthImage(new, bg, fg, data_order=self._order)

    @classmethod
    def from_file(cls, filename: str, *, data_order=RGBOrder.BGR) -> typing_extensions.Self:
        """
        Alternate constructor for loading the array from a file.

        Parameters
        ----------
        filename: str
            The name of the file to open.
        data_order: RGBOrder
            The order the channels are in.

        Returns
        -------
        Self
            The image formed from the loaded array.
        """
        return cls(cv2.imread(filename, cv2.IMREAD_COLOR), data_order=data_order)

    @classmethod
    def blank(cls, size: _tuple[int, int], data_order=RGBOrder.BGR) -> typing_extensions.Self:
        """
        Alternate constructor for creating a pure black image.

        Parameters
        ----------
        size: tuple[int, int]
            The x-y size of the resulting image.
        data_order: RGBOrder
            The order the channels are in.

        Returns
        -------
        Self
            A pure black image.
        """
        return cls(np.zeros((size[1], size[0], 3)), data_order=data_order)


class GreyscaleImage(Greyscale, MultiModal[Grey]):
    """
    Concrete Greyscale, Multimodal image.

    Attributes
    ----------
    transform: ColourTransform[GreyscaleImage]
        The transformation object to allow for editing and transforming the image.
    greyscale_transform: GreyTransform[GreyscaleImage]
        The transformation object to allow for performing greyscale-specific transformations on the image.
    drawing: Drawing[Grey]
        The drawing object to allow for editing and painting the image.
    """
    __init__ = Greyscale.__init__
    transform = ColourTransform["GreyscaleImage"]()
    greyscale_transform = GreyTransform["GreyscaleImage"]()
    drawing = Drawing[Grey]()

    def downchannel(self, bg: Grey, fg: Grey, *, invalid_handler: BimodalBehaviour = None) -> "BimodalGreyscaleImage":
        if invalid_handler is None:
            return BimodalGreyscaleImage(self._data, bg, fg, data_order=self._order)
        if invalid_handler == BimodalBehaviour.BG:
            keep = fg
            remaining = bg
        else:
            keep = bg
            remaining = fg
        masked_image = np.where(self._data == keep["r"], 1, 0)
        keep_points = np.nonzero(masked_image)
        new = np.zeros_like(self._data)
        new[:, :, :] = remaining.items(self._order)
        new[keep_points] = keep.items(self._order)
        return BimodalGreyscaleImage(new, bg, fg, data_order=self._order)

    def promote(self) -> FullDepthImage:
        w, h = self.size
        data = np.zeros((h, w, 3))
        data[:, :, 0] = self.channel.copy("r")
        data[:, :, 1] = self.channel.copy("g")
        data[:, :, 2] = self.channel.copy("b")
        return FullDepthImage(data, data_order=self._order)

    @classmethod
    def from_file(cls, filename: str, *, data_order=RGBOrder.BGR) -> typing_extensions.Self:
        """
        Alternate constructor for loading the array from a file.

        Parameters
        ----------
        filename: str
            The name of the file to open.
        data_order: RGBOrder
            The order the channels are in.

        Returns
        -------
        Self
            The image formed from the loaded array.
        """
        return cls(cv2.imread(filename, cv2.IMREAD_GRAYSCALE), data_order=data_order)

    @classmethod
    def blank(cls, size: _tuple[int, int], data_order=RGBOrder.BGR) -> typing_extensions.Self:
        """
        Alternate constructor for creating a pure black image.

        Parameters
        ----------
        size: tuple[int, int]
            The x-y size of the resulting image.
        data_order: RGBOrder
            The order the channels are in.

        Returns
        -------
        Self
            A pure black image.
        """
        return cls(np.zeros(size[::-1]), data_order=data_order)


class BimodalFullDepthImage(Bimodal[Colour], RGB):
    """
    Concrete RGB, Bimodal image.

    Attributes
    ----------
    drawing: Drawing[Colour]
        The drawing object to allow for editing and painting the image.
    """
    _gc = RGB.get_colours
    drawing = Drawing[Colour]()

    def __init__(self, arr: np.ndarray, background: Colour, foreground: Colour, *, data_order=RGBOrder.BGR):
        RGB.__init__(self, arr, data_order=data_order)
        Bimodal.__init__(self, arr, background, foreground, data_order=data_order)

    def __setitem__(self, pos: _tuple[int, int], colour: Colour):
        self.cheap_op()
        super().__setitem__(pos, colour)

    def _verify_type(self, colour: typing.Type[Image]) -> bool:
        self.cheap_op()
        return super()._verify_type(colour)

    verify_colour = Bimodal.verify_colour

    def upchannel(self) -> FullDepthImage:
        return FullDepthImage(self._data.copy(), data_order=self._order)

    def demote(self, keep: Channel) -> "BimodalGreyscaleImage":
        return BimodalGreyscaleImage(self.channel.copy(keep), Grey(self._bg[keep]), Grey(self._fg[keep]),
                                     data_order=self._order)

    @classmethod
    def from_file(cls, filename: str, background: Colour, foreground: Colour, *, data_order=RGBOrder.BGR) \
            -> typing_extensions.Self:
        """
        Alternate constructor for loading the array from a file.

        Parameters
        ----------
        filename: str
            The name of the file to open.
        background: Colour
            The background colour expected in the image.
        foreground: Colour
            The foreground colour expected in the image.
        data_order: RGBOrder
            The order the channels are in.

        Returns
        -------
        Self
            The image formed from the loaded array.
        """
        return cls(cv2.imread(filename, cv2.IMREAD_COLOR), background, foreground, data_order=data_order)

    @classmethod
    def blank(cls, size: _tuple[int, int], foreground: Colour, data_order=RGBOrder.BGR) -> typing_extensions.Self:
        """
        Alternate constructor for creating a pure black image.

        Parameters
        ----------
        size: tuple[int, int]
            The x-y size of the resulting image.
        foreground: Colour
            The foreground colour expected in the image.
        data_order: RGBOrder
            The order the channels are in.

        Returns
        -------
        Self
            A pure black image.
        """
        return cls(np.zeros((size[1], size[0], 3)), Colour.spawn(0, data_order), foreground, data_order=data_order)


class BimodalGreyscaleImage(Bimodal[Grey], Greyscale):
    """
    Concrete Greyscale, Bimodal image.

    Attributes
    ----------
    drawing: Drawing[Grey]
        The drawing object to allow for editing and painting the image.
    """
    _gc = Greyscale.get_colours
    drawing = Drawing[Grey]()

    def __init__(self, arr: np.ndarray, background: Grey, foreground: Grey, *, data_order=RGBOrder.BGR):
        Bimodal.__init__(self, arr, background, foreground, data_order=data_order)
        Greyscale.__init__(self, arr, data_order=data_order)

    def __setitem__(self, pos: _tuple[int, int], colour: Colour):
        self.cheap_op()
        super().__setitem__(pos, colour)

    def is_binary(self) -> bool:
        """
        Method to check for a binary image.

        Returns
        -------
        bool
            Whether the image only contains back and white colours.
        """
        return self.colours == {Grey(0), Grey(255)}

    def _verify_type(self, colour: typing.Type[Image]) -> bool:
        self.cheap_op()
        return super()._verify_type(colour)

    verify_colour = Bimodal.verify_colour

    def upchannel(self) -> GreyscaleImage:
        return GreyscaleImage(self.image(), data_order=self._order)

    def promote(self) -> BimodalFullDepthImage:
        w, h = self.size
        data = np.zeros((h, w, 3))
        data[:, :, 0] = self.channel.copy("r")
        data[:, :, 1] = self.channel.copy("g")
        data[:, :, 2] = self.channel.copy("b")
        return BimodalFullDepthImage(data, self._bg, self._fg, data_order=self._order)

    @classmethod
    def from_file(cls, filename: str, background: Grey, foreground: Grey, *, data_order=RGBOrder.BGR) \
            -> typing_extensions.Self:
        """
        Alternate constructor for loading the array from a file.

        Parameters
        ----------
        filename: str
            The name of the file to open.
        background: Grey
            The background colour expected in the image.
        foreground: Grey
            The foreground colour expected in the image.
        data_order: RGBOrder
            The order the channels are in.

        Returns
        -------
        Self
            The image formed from the loaded array.
        """
        return cls(cv2.imread(filename, cv2.IMREAD_GRAYSCALE), background, foreground, data_order=data_order)

    @classmethod
    def blank(cls, size: _tuple[int, int], foreground: Grey, data_order=RGBOrder.BGR) -> typing_extensions.Self:
        """
        Alternate constructor for creating a pure black image.

        Parameters
        ----------
        size: tuple[int, int]
            The x-y size of the resulting image.
        foreground: Grey
            The foreground colour expected in the image.
        data_order: RGBOrder
            The order the channels are in.

        Returns
        -------
        Self
            A pure black image.
        """
        return cls(np.zeros(size[::-1]), Grey(0), foreground, data_order=data_order)
