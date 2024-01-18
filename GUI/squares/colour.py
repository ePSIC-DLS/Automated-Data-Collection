"""
Classes to represent a colour
"""
from __future__ import annotations

import itertools
import typing

import cv2
import numpy as np
from .enums import *


class Colour:
    """
    Class to represent a singular colour as an RGB value

    :var _r int: The red amount
    :var _g int: The green amount
    :var _b int: The blue amount
    """

    WRAP_ORDER = ("r", "g", "b")

    def __init__(self, r: int, g: int, b: int, wrap=Wrapping.RAISE):
        """
        Initializes the red, green, and blue components
        :param r: Red component
        :param g: Green component
        :param b: Blue component
        :param wrap: The wrapping mode to use (default is no wrapping)
        :raise ValueError: If any colour isn't between 0 and 255
        """
        colour = dict(r=r, g=g, b=b)
        if wrap == Wrapping.TRUNC:
            for k, v in colour.items():
                colour[k] = min(v, 255)
        elif wrap == Wrapping.WRAP or wrap == Wrapping.WRAP_SEQ:
            for k, look in zip(itertools.cycle(type(self).WRAP_ORDER),
                               type(self).WRAP_ORDER[1:] + type(self).WRAP_ORDER):
                if colour[k] > 255:
                    colour[look] += colour[k] - 255
                    colour[k] = 255
                    if wrap == Wrapping.WRAP:
                        break
        if any(c > 255 or c < 0 for c in colour.values()):
            raise ValueError(f"Colour must be between 0 and 255 (got {tuple(colour.values())})")
        self._colour = colour

    def __str__(self) -> str:
        """
        Turn an RGB colour into a hex string
        :return: The hex string
        """

        def hexer(i: int) -> str:
            """
            Turn a single component into a 2-letter hex string
            :param i: The integer component
            :return: A 2-character hex string
            """
            return f"{hex(i)[2:]:0>2}"

        return f"#{''.join(map(hexer, self._colour.values()))}"

    def __getitem__(self, item: typing.Literal["r", "g", "b"]) -> int:
        """
        Gets a specific colour stream
        :param item: A colour name
        :return: The colour stream
        :raise TypeError: If item isn't a str
        :raise ValueError: If item isn't (r, g, b)
        """
        if not isinstance(item, str):
            raise TypeError("Invalid type for []")
        try:
            return self._colour[item]
        except KeyError as e:
            raise ValueError(f"Unknown colour {item!r}") from e

    def __eq__(self, other: "Colour | "
                            "str | "
                            "tuple[tuple[int, int, int], RGBOrder] | "
                            "tuple[tuple[int, int, int], HSVOrder] | "
                            "Colours") -> bool:
        if isinstance(other, tuple):
            raise_ = False
            if len(other) != 2:
                raise_ = True
            else:
                colour, order = other
                if not isinstance(colour, tuple) or not isinstance(order, RGBOrder | HSVOrder):
                    raise_ = True
                if len(colour) != 3:
                    raise_ = True
                if isinstance(order, RGBOrder):
                    return self.all(order) == colour
                elif isinstance(order, HSVOrder):
                    return self.to_hsv(order) == colour
            if raise_:
                raise ValueError("Invalid tuple form. Must be a tuple of 3 integers and an order (either RGB or HSV)")
        elif isinstance(other, Colour):
            return self.all(RGBOrder.RGB) == other.all(RGBOrder.RGB)
        elif isinstance(other, str):
            from tkinter import Label as _Tk, TclError as _Err
            raise_ = False
            try:
                _Tk(bg=other)
            except _Err:
                raise_ = True
            if raise_:
                raise ValueError(f"Unknown colour code {other}")
            return str(self).lower() == other.lower()
        elif isinstance(other, Colours):
            return self.is_colour(other)
        return NotImplemented

    def to_hsv(self, order: HSVOrder) -> tuple[int, int, int]:
        """
        Convert RGB to HSV
        :param order: The order in which to return the HSV colours
        :return: Integers for HSV colour
        """
        hsv = list(cv2.cvtColor(np.uint8([[list(reversed(self._colour.values()))]]), cv2.COLOR_BGR2HSV)[0][0])
        i1, i2, i3 = order.value
        return hsv[i1], hsv[i2], hsv[i3]

    def all(self, order: RGBOrder) -> tuple[int, int, int]:
        """
        Get raw colour tuple
        :param order: The order in which to return the RGB colours
        :return: Integers for RGB colour stored
        """
        c1, c2, c3 = order.value
        return self._colour[c1], self._colour[c2], self._colour[c3]

    def is_colour(self, colour: Colours, at_strength=1.0, at_lightness=0.0) -> bool:
        """
        Method to check if this colour is created using the specified member of the colours enum
        :param colour: The colour to check
        :param at_strength: The specified strength
        :param at_lightness: The specified lightness
        :return: Whether the colour is the specified enumeration colour
        """
        return self == Colour.from_colour(colour, at_strength, at_lightness)

    def strengthen(self, amount: int, type_=Increase.BY, domain=Domain.MAX) -> typing.Self:
        """
        Method to increase the strength of a colour in many ways
        :param amount: The amount to increase by
        :param type_: Whether it is adding, multiplying or becoming that value
        :param domain: How many components should be affected
        :return: The new colour
        """
        return self._increase(self.strengthen, amount, type_, domain, invert=False)

    def brighten(self, amount: int, type_=Increase.BY, domain=Domain.MAX) -> typing.Self:
        """
        Method to increase the brightness of a colour in many ways
        :param amount: The amount to increase by
        :param type_: Whether it is adding, multiplying or becoming that value
        :param domain: How many components should be affected
        :return: The new colour
        """
        return self._increase(self.brighten, amount, type_, domain, invert=True)

    def _increase(self, callback: typing.Callable[[int, Increase, Domain], typing.Self], amount: int, type_: Increase,
                  domain=Domain.MAX, *, invert: bool) -> typing.Self:
        """
        Internal function to do the heavy lifting of strengthening or brightening a colour.
        :param callback: The source of the call.
        :param amount: The amount to increase by.
        :param type_: Whether it is adding, multiplying or becoming that value.
        :param domain: How many components should be affected.
        :param invert: Whether the increase should affect the specified component, or the other components.
        :return: The new colour.
        """
        if (amount < 0 and type_ != Increase.BY) or not isinstance(amount, int):
            raise ValueError("Specified increase must be a positive whole number")

        _r, _g, _b = self._colour.values()

        def _handle(colour: int) -> int:
            if type_ == Increase.BY:
                return colour + amount
            elif type_ == Increase.TO:
                return amount
            elif type_ == Increase.FACTOR:
                return colour * amount

        def _process(comp: int) -> typing.Self:
            if _r == comp:
                return callback(amount, type_, Domain.R)
            if _g == comp:
                return callback(amount, type_, Domain.G)
            if _b == comp:
                return callback(amount, type_, Domain.B)

        if domain == Domain.R:
            if invert:
                return type(self)(_r, _handle(_g), _handle(_b))
            return type(self)(_handle(_r), _g, _b)
        elif domain == Domain.G:
            if invert:
                return type(self)(_handle(_r), _g, _handle(_b))
            return type(self)(_r, _handle(_g), _b)
        elif domain == Domain.B:
            if invert:
                return type(self)(_handle(_r), _handle(_g), _b)
            return type(self)(_r, _g, _handle(_b))
        elif domain == Domain.MAX:
            return _process(max(self.all(RGBOrder.RGB)))
        elif domain == Domain.MIN:
            return _process(min(self.all(RGBOrder.RGB)))
        elif domain == Domain.ALL:
            return type(self)(*map(_handle, self.all(RGBOrder.RGB)))

    @classmethod
    def from_colour(cls, colour: Colours, strength=1.0, lightness=0.0) -> typing.Self:
        """
        Alternative constructor for passing in a colour type and getting an RGB.
        :param colour: The colour to recreate.
        :param strength: The strength of the active colours.
        :param lightness: The strength of the inactive colours.
        :return: The created colour.
        :raise NameError: If using a strength and lightness combination that can be created from a known Colours enum.
        :raise ValueError: If colour couldn't be created.
        """
        if strength == 0 or lightness == 1:
            raise NameError("For white, use Colours.WHITE. For black use Colours.BLACK")
        red = green = blue = lightness * 255
        if colour & Colours.RED:
            red = strength * 255
        if colour & Colours.GREEN:
            green = strength * 255
        if colour & Colours.BLUE:
            blue = strength * 255
        try:
            return cls(int(red), int(green), int(blue))
        except ValueError as err:
            raise ValueError("Lightness and strength must be between 1 and 0") from err

    @classmethod
    def from_str(cls, code: str) -> typing.Self:
        """
        Alternative constructor for passing in a tkinter colour string and re-creating that colour
        :param code: The 6 character hex string prefaced by a '#'
        :return: The colour represented by the string
        :raise ValueError: If string is incorrectly formatted
        """
        if len(code) != 7:
            raise ValueError("String should be 7 characters long")
        elif code[0] != "#" and any(c.lower() not in {*map(str, range(10), "a", "b", "c", "d", "e", "f")}
                                    for c in code):
            raise ValueError("String should be valid tkinter colour")
        code = code[1:]
        r, g, b = (code[i:i + 2] for i in range(0, 6, 2))
        return cls(int(r, 16), int(g, 16), int(b, 16))

    @classmethod
    def shift(cls, first: typing.Self, last: typing.Self, step=Domain.B, by=1) \
            -> typing.Generator[typing.Self, None, None]:
        """
        Create a colour range from first to last (including both).
        :param first: The starting colour.
        :param last: The ending colour.
        :param step: The colour domain to increase by a specified amount each time.
        :param by: The amount to increase by.
        :return: Yield each colour in turn.
        """

        def _handle(tup: tuple[int, int, int]) -> tuple[int, int, int]:
            _r, _g, _b = tup
            if step == Domain.R:
                return _r + by, _g, _b
            elif step == Domain.G:
                return _r, _g + by, _b
            elif step == Domain.B:
                return _r, _g, _b + by
            elif step == Domain.MAX or step == Domain.MIN:
                index = (max if step == Domain.MAX else min)(range(3), key=tup.__getitem__)
                return _r + int(index == 0) * by, _b + int(index == 1) * by, _b + int(index == 2) * by
            elif step == Domain.ALL:
                return _r + by, _g + by, _b + by

        curr = first
        while curr != last:
            yield curr
            curr = cls(*_handle(curr.all(RGBOrder.RGB)))
        yield last
