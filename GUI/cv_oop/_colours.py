"""
Module to represent a colour that can be represented with an RGB tuple.

Every colour is immutable and can be used as keys in a dictionary.
"""
import functools
import itertools
import operator
import typing

from ._enums import *


class Colour:
    """
    Class to represent a colour from an RGB tuple.

    :var Wrap _wrap: The type of wrapping to apply to input values.
    :var dict[str, int] _colours: The RGB values.
    """

    def __init__(self, r: int, g: int, b: int, wrap=Wrap.RAISE, wrap_order=RGBOrder.RGB):
        self._wrap = wrap
        self._colours = dict(r=r, g=g, b=b)
        if wrap == Wrap.TRUNCATE:
            self._colours.update(dict(zip(self._colours, map(lambda i: min(i, 255), self._colours.values()))))
        elif wrap == Wrap.WRAP:
            for c, n in zip(wrap_order.value, wrap_order.value[1:]):
                if self._colours[c] > 255:
                    self._colours[n] += self._colours[c] - 255
                    self._colours[c] = 255
            self._colours = {k: int(v) for k, v in self._colours.items()}
        if not all(0 <= c <= 255 for c in self._colours.values()):
            raise ValueError(f"Expected all colours to be between 0 and 255 inclusive, got {self._colours}")

    def __str__(self) -> str:
        def _to_hex(val: int) -> str:
            return f"{val:02X}"

        return f"#{''.join(map(_to_hex, self._colours.values()))}"

    def __bool__(self) -> bool:
        return any(self._colours.values())

    def __getitem__(self, key: typing.Literal["r", "g", "b"]) -> int:
        """
        Get a specific colour channel.

        :param key: Colour channel to get.
        :return: The value of the colour channel.
        :raises TypeError: If key isn't r, g or b.
        """
        try:
            return self._colours[key]
        except KeyError:
            raise TypeError(f"Colour indices must be 'r', 'g' or 'b'") from None

    def __eq__(self, other: typing.Union["Colour", tuple[int, int, int, RGBOrder], Colours]) -> bool:
        """
        Compare two colours. Handles alternate constructors implicitly.

        :param other: The other colour to compare against – can also be arguments to an alternative constructor.
        :return: Whether the two colours are equal.
        """
        if isinstance(other, Colours):
            return self == Colour.from_known(other)
        elif isinstance(other, tuple):
            try:
                return self == Colour.from_order(*other)
            except TypeError as err:
                raise ValueError(f"Expected colour to be tuple of RGB colours and an order") from err
        elif isinstance(other, Colour):
            return self.all() == other.all()
        return NotImplemented

    def __gt__(self, other: Colours) -> bool:
        """
        Method to check whether the known colour's channels are the strongest in this colour.

        :param other: The colour to extract channels from.
        :return: Whether the strongest component is in the channels extracted.
        :raises ValueError: If the colour is black.
        """
        if other == Colours.BLACK:
            raise ValueError("Cannot check for greyscale colours using BLACK")
        largest_value = max(self._colours.values())
        r_comp = g_comp = b_comp = True
        if other & Colours.RED:
            r_comp = largest_value == self["r"]
        if other & Colours.GREEN:
            g_comp = largest_value == self["g"]
        if other & Colours.BLUE:
            b_comp = largest_value == self["b"]
        return r_comp and g_comp and b_comp

    def __add__(self, other: "Colour") -> "Colour":
        """
        Adds two colours together, channel by channel.

        Wrapping isn't done from this operation – invalid values will raise an error.
        :param other: The other colour.
        :return: A colour with each channel being the sum of the corresponding channels in each colour.
        """
        if not isinstance(other, Colour):
            return NotImplemented
        return Colour(*map(operator.add, self.all(), other.all()))

    def __mul__(self, other: int) -> "Colour":
        """
        Scales a colour.

        Wrapping isn't done from this operation – invalid values will raise an error.
        :param other: The integer to scale by.
        :return: The new colour.
        """
        if not isinstance(other, int):
            return NotImplemented
        return Colour(*map(operator.mul, self.all(), itertools.repeat(other)))

    def __floordiv__(self, other: int) -> "Colour":
        """
        Scales a colour in all channels through integer division.

        :param other: The divisor.
        :return: A new colour with smaller values.
        """
        return Colour(*map(operator.floordiv, self.all(), itertools.repeat(other)))

    def __matmul__(self, other: tuple[float, typing.Literal["r", "g", "b"]]) -> "Colour":
        """
        Shorthand for self.strengthen(other[0], other[1], Increase.BY).

        Has automatic percentage handling for isinstance(other[0], float).
        :param other: The 'strengthen' specification.
        :return: A new colour strengthened the way specified.
        :raises TypeError: If the specification is invalid.
        """
        if not isinstance(other, tuple):
            return NotImplemented
        amount, mode = self._matmul(other)
        return self.strengthen(amount, other[1], mode)

    def __rmatmul__(self, other: tuple[float, typing.Literal["r", "g", "b"]]) -> "Colour":
        """
        Shorthand for self.brighten(other[0], other[1], Increase.BY).

        Has automatic percentage handling for isinstance(other[0], float).
        :param other: The 'brighten' specification.
        :return: A new colour brightened the way specified.
        :raises TypeError: If the specification is invalid.
        """
        if not isinstance(other, tuple):
            return NotImplemented
        amount, mode = self._matmul(other)
        return self.brighten(amount, other[1], mode)

    def __xor__(self, other: tuple[int, typing.Literal["r", "g", "b"]]) -> "Colour":
        """
        Shorthand for self.strengthen(other[0], other[1], Increase.FACTOR).

        :param other: The 'strengthen' specification.
        :return: A new colour strengthened the way specified.
        :raises TypeError: If the specification is invalid.
        """
        if not isinstance(other, tuple):
            return NotImplemented
        elif len(other) != 2 or not isinstance(other[0], int) or other[1] not in {"r", "g", "b"}:
            raise TypeError("Addition of colour must be a tuple of integer and domain")
        amount, domain = other
        return self.strengthen(amount, domain, Increase.FACTOR)

    def __rxor__(self, other: tuple[int, typing.Literal["r", "g", "b"]]) -> "Colour":
        """
        Shorthand for self.brighten(other[0], other[1], Increase.FACTOR).

        :param other: The 'brighten' specification.
        :return: A new colour brightened the way specified.
        :raises TypeError: If the specification is invalid.
        """
        if not isinstance(other, tuple):
            return NotImplemented
        elif len(other) != 2 or not isinstance(other[0], int) or other[1] not in {"r", "g", "b"}:
            raise TypeError("Addition of colour must be a tuple of integer and domain")
        amount, domain = other
        return self.brighten(amount, domain, Increase.FACTOR)

    def __invert__(self) -> "Colour":
        """
        Find the complement of this colour, such that the strength becomes the brightness.

        :return: A colour strengthened by this colour's brightness and brightened by this colour's strength
        """
        return Colour(abs(255 - self["r"]), abs(255 - self["g"]), abs(255 - self["b"]))

    def __and__(self, other: "Colour") -> "Colour":
        """
        Combine two colours by filtering the non-common components.

        As the filter takes the value of the LHS, this is non-commutative
        :param other: The other colour to combine.
        :return: A combined colour.
        """
        return Colour(self["r"] if other["r"] else 0, self["g"] if other["g"] else 0, self["b"] if other["b"] else 0)

    __rmul__ = __mul__

    def __hash__(self) -> int:
        return hash(self.all())

    def all(self, order=RGBOrder.RGB) -> tuple[int, int, int]:
        """
        Get RGB values in a specified order.

        :param order: The order to extract in.
        :return: Each channel in the order specified.
        """
        return self._colours[order.value[0]], self._colours[order.value[1]], self._colours[order.value[2]]

    def strengthen(self, amount: int, domain: typing.Literal["r", "g", "b"], mode=Increase.BY) -> "Colour":
        """
        Increase a singular domain of the colour. Returns a new colour.

        Wrapping isn't done from this operation – invalid values will raise an error.
        :param amount: The amount to increase the domain by.
        :param domain: The domain to increase.
        :param mode: The type of the increase to do.
        :return: The new colour with the domain increased.
        :raises ValueError: If the amount is incompatible with the mode, or domain isn't r, g, or b.
        """
        if amount < 0 and mode != Increase.BY:
            raise ValueError(f"Expected amount to be positive, got {amount}")
        elif domain not in {"r", "g", "b"}:
            raise ValueError("Domain must be either 'r', 'g' or 'b'")
        elif mode == Increase.FACTOR and amount == 0:
            raise ValueError("Use mode TO to reduce domain to 0")
        elif mode == Increase.BY and amount == 0:
            raise ValueError("Combination has no effect")
        colours = self._colours.copy()
        if mode == Increase.BY:
            colours[domain] += amount
        elif mode == Increase.TO:
            colours[domain] = amount
        elif mode == Increase.FACTOR:
            colours[domain] *= amount
        elif mode == Increase.BY_PERCENTAGE or mode == Increase.TO_PERCENTAGE:
            if not 0 <= amount <= 100:
                raise ValueError("Expected percentage to be between 0 and 100")
            mode = Increase.BY if mode == Increase.BY_PERCENTAGE else Increase.TO
            return self.strengthen(int(colours[domain] * (amount / 100)), domain, mode)
        return Colour(**colours)

    def brighten(self, amount: int, domain: typing.Literal["r", "g", "b"], mode=Increase.BY) -> "Colour":
        """
        Strengthen the two domains not specified by domain.

        :param amount: The amount to increase the other domains by.
        :param domain: The domain to leave.
        :param mode: The type of the increase to do.
        :return: The new colour with the other domains increased.
        """
        if domain == "r":
            g = self.strengthen(amount, "g", mode)["g"]
            b = self.strengthen(amount, "b", mode)["b"]
            return Colour(self["r"], g, b)
        elif domain == "g":
            r = self.strengthen(amount, "r", mode)["r"]
            b = self.strengthen(amount, "b", mode)["b"]
            return Colour(r, self["g"], b)
        elif domain == "b":
            r = self.strengthen(amount, "r", mode)["r"]
            g = self.strengthen(amount, "g", mode)["g"]
            return Colour(r, g, self["b"])
        raise ValueError("Domain must be either 'r', 'g' or 'b'")

    def is_grey(self) -> bool:
        """
        Checks if the colour is a greyscale colour

        Alias for self > Colours.WHITE
        :return: Whether all components of the image are identical
        """
        return self["r"] == self["g"] == self["b"]

    @staticmethod
    def _matmul(other: tuple[float, typing.Literal["r", "g", "b"]]) -> tuple[int, Increase]:
        if len(other) != 2 or not isinstance(other[0], (int, float)) or other[1] not in {"r", "g", "b"}:
            raise TypeError("Addition of colour must be a tuple of number and domain")
        if isinstance(other[0], float):
            amount = int(other[0] * 100)
            mode = Increase.BY_PERCENTAGE
        else:
            amount = other[0]
            mode = Increase.BY
        return amount, mode

    @classmethod
    def from_known(cls, colour: Colours, strength=1.0, brightness=0.0) -> "Colour":
        """
        Alternate constructor for using a Colours value.

        :param colour: The known colour to use.
        :param strength: The strength of the nonzero domains in the colour.
        :param brightness: The strength of the zero domains in the colour.
        :return: A colour constructed from the known colour, at specific strength.
        :raises NameError: If the strength and brightness make a known colour, or if grey usage is incorrect.
        :raises ValueError: If the strength and brightness aren't between 0 and 1
        """
        if strength == 0.0 or brightness == 1.0:
            raise NameError("For white, use Colours.WHITE. For black, use Colours.BLACK")
        elif (colour == Colours.WHITE and brightness != 0.0) or (colour == Colours.BLACK and strength != 1.0):
            name = colour.name
            domains = ("brightness", "strength")
            is_white = colour == Colours.WHITE
            no_effect = domains[not is_white]
            effect = domains[is_white]
            raise NameError(f"Greys cannot be made with {name} and {no_effect}, use {effect} instead")
        r = g = b = brightness * 255
        if colour & Colours.RED:
            r = strength * 255
        if colour & Colours.GREEN:
            g = strength * 255
        if colour & Colours.BLUE:
            b = strength * 255
        try:
            return Colour(int(r), int(g), int(b))
        except ValueError as err:
            raise ValueError("Expected strength and brightness to be between 0 and 1") from err

    @classmethod
    def from_order(cls, i1: int, i2: int, i3: int, order: RGBOrder, wrap=Wrap.RAISE) -> "Colour":
        """
        Alternate constructor for constructing the RGB colour from a known order.

        This saves user re-ordering of the input parameters.
        :param i1: First value of the colour.
        :param i2: Second value of the colour.
        :param i3: Third value of the colour.
        :param order: The order of the values. This will be the wrapping order.
        :param wrap: The wrapping type.
        :return: A new colour from the re-arranged values.
        :raises TypeError: If the order isn't an RGBOrder.
        """
        if not isinstance(order, RGBOrder):
            raise TypeError(f"Expected order to be RGBOrder, got {type(order)}")
        values = (i1, i2, i3)
        mapping = {k: values[order.value.find(k)] for k in order.value}
        return Colour(**mapping, wrap=wrap, wrap_order=order)

    @classmethod
    def sequence(cls, start: "Colour", stop: "Colour", step=1, order=RGBOrder.BGR, do_last=True) \
            -> typing.Iterator["Colour"]:
        """
        Static method to create a generator that yields colours between start and stop.

        :param start: The starting colour.
        :param stop: The ending colour.
        :param step: The value to increase the lowest denomination by.
        :param order: The order to increase in.
        :param do_last: Whether to include the last value in the range.
        :return: A generator yielding colours between start and stop.
        """
        curr = start
        start_red = order.value[0] == "r"
        start_green = order.value[0] == "g"
        start_blue = order.value[0] == "b"
        while curr != stop:
            yield curr
            r, g, b = curr.all()
            if start_red:
                r += step
            elif start_green:
                g += step
            elif start_blue:
                b += step
            curr = cls(r, g, b, Wrap.WRAP, order)
        if do_last:
            yield stop

    @classmethod
    def colours(cls, order=RGBOrder.BGR, *, red=True, green=True, blue=True) -> typing.Iterator["Colour"]:
        """
        Yield all colours between black and white, in a particular order.

        :param order: The order in which to increment colours.
        :param red: Flag to decide whether to include the red channel.
        :param green: Flag to decide whether to include the green channel.
        :param blue: Flag to decide whether to include the blue channel.
        :return: A generator for all colours between black and white
        """
        if not (red or green or blue):
            raise ValueError("Must specify at least one channel")
        black = cls(0, 0, 0)
        reds = cls.sequence(black, cls(255, 0, 0) if red else black, order=RGBOrder.RGB)
        greens = cls.sequence(black, cls(0, 255, 0) if green else black, order=RGBOrder.GRB)
        blues = cls.sequence(black, cls(0, 0, 255) if blue else black)
        if order == RGBOrder.RGB:
            product = (blues, greens, reds)
        elif order == RGBOrder.RBG:
            product = (greens, blues, reds)
        elif order == RGBOrder.GBR:
            product = (reds, blues, greens)
        elif order == RGBOrder.GRB:
            product = (blues, reds, greens)
        elif order == RGBOrder.BRG:
            product = (greens, reds, blues)
        else:
            product = (reds, greens, blues)
        yield from map(functools.partial(functools.reduce, operator.add), itertools.product(*product))

    @classmethod
    def colour_space(cls, colour: Colours) -> typing.Iterator["Colour"]:
        """
        Iterate over every single possible created colour that can be formed from the specified known colour.

        :param colour: The known colour to create the space around.
        :return: A generator that yields each possible colour, as long as it can be formed from the specified colour.
        :raises ValueError: If the colour is black.
        """
        if colour == Colours.BLACK:
            raise ValueError("Cannot create greyscale colours by using BLACK")
        elif colour == Colours.WHITE:
            yield from (Colour(i, i, i) for i in range(1, 256))
        else:
            for strength in range(100, 0, -1):
                strength /= 100
                for brightness in range(0, 100):
                    brightness /= 100
                    if int(strength * 255) >= int(brightness * 255):
                        yield cls.from_known(colour, strength, brightness)
