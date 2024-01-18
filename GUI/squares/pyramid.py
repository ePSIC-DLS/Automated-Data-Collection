"""
Implements a pyramid (either Gaussian or Laplacian) of image quality
"""
from __future__ import annotations

import typing

from .image import Image, cv2
from .enums import *


class Pyramid:
    """
    Pyramid implementation that stores each requested layer

    :var _mode PMODE: The pyramid mode
    :var _i int: The current layer index (as pyramids are iterable)
    :var _length int: The number of layers
    :var _last Image: The last image created
    :var _levels list[Image]: Each image requested in series
    """

    @property
    def levels(self) -> int:
        """
        Public getter for the number of levels
        :return: The length of the pyramid
        """
        return self._length

    @property
    def current_level(self) -> Image:
        """
        Public getter for the last requested image
        :return: The _last instance variable
        """
        return self._last.copy()

    def __init__(self, original: Image, *, mode: PMODE):
        """
        Constructs the pyramid
        :param original: The image to use
        :param mode: The pyramid mode
        """
        self._mode = mode
        self._i = 0
        self._length = 1
        self._last = original.copy()
        self._levels = [self._last]

    def __iter__(self) -> typing.Self:
        """
        Initializes pyramid for iterating
        :return: The pyramid object
        """
        self._i = 0
        return self

    def __next__(self) -> Image:
        """
        Returns the next Image in the pyramid
        :return: The next image
        :raise StopIteration: If exhausted
        """
        if self._i >= self._length:
            raise StopIteration()
        self._i += 1
        return self._levels[self._i - 1].copy()

    def request_new_layer(self):
        """
        Requests and stores the next layer in the pyramid
        """
        image = self.form_next_layer()
        self._last = image.copy()
        self._levels.append(self._last)
        self._length += 1

    def request_layers(self, layers: int):
        """
        Requests and stores several layers in the pyramid
        :param layers: The number of layers to request
        :raise ValueError: if layers < 2
        """
        if layers < 2:
            raise ValueError("Cannot have less than 2 layers requested at a time. For 1 layer, "
                             "use Pyramid.request_new_layer")
        for _ in range(layers):
            self.request_new_layer()

    def form_final_layer(self, layers: int) -> Image:
        """
        Returns the final result of requesting layers (without storing)
        :param layers: The number of layers to request
        :return: The image at the final layer
        """
        image = None
        for img in self.form_layers(layers):
            image = img
        return image

    def form_layers(self, layers: int) -> typing.Generator[Image, None, None]:
        """
        Returns a generator for each requested layer (without storing any item in the generator)
        :param layers: The number of layers to request
        :return: Yields each layer's image in turn
        """
        if layers < 1:
            raise ValueError("Cannot form less than 1 layer")
        image = self._last.image
        for _ in range(layers):
            last_image = image
            image = cv2.pyrDown(last_image)
            if self._mode == PMODE.LAPLACIAN:
                upper = cv2.pyrUp(image)
                image = cv2.subtract(last_image, upper)
            yield Image(image)

    def form_next_layer(self) -> Image:
        """
        Convenience function to request the next layer (without storing)
        :return: The Image at the next layer
        """
        return self.form_final_layer(1)

