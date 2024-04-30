import abc
import functools
import itertools
import operator
import typing
from typing import Dict as _dict, Tuple as _tuple

from ._aliases import *
from ._enums import *
from ._errors import *


class Colour(abc.ABC):
    """
    Abstract base class for a generic colour. Each colour has a particular order and three channels.

    Abstract Methods
    ----------------
    __invert__
    __add__
    __sub__
    __mul__
    __truediv__
    __eq__
    __contains__

    Attributes
    ----------
    _colours: dict[Channel, int]
        The colour channels.
    _channels: cycle[Channel]
        The channels in the colour, cyclic and in the order of the colour.
    _order: RGBOrder
        The order of the channels.

    Raises
    ------
    ColourOverflowError
        If any channels are invalid.
    """

    def __init__(self, r: int, g: int, b: int, order: RGBOrder):
        self._colours: _dict[Channel, int] = {"r": int(r), "g": int(g), "b": int(b)}
        self._channels = itertools.cycle(order.items())
        self._order = order
        if any(channel > 255 or channel < 0 for channel in self._colours.values()):
            raise ColourOverflowError.from_channels(self._colours)

    def __str__(self) -> str:
        return f"#{self['r']:02x}{self['g']:02x}{self['b']:02x}"

    def __getitem__(self, item: Channel) -> int:
        """
        Get the channel value specified.

        Parameters
        ----------
        item: Channel
            The channel to query.

        Returns
        -------
        int
            The channel value.

        Raises
        ------
        TypeError
            If the channel doesn't exist.
        """
        try:
            return self._colours[item]
        except KeyError:
            raise TypeError(f"Expected a valid RGB channel (r, g, b); got {item} instead.") from None

    def __bool__(self) -> bool:
        return any(self._colours.values())

    @abc.abstractmethod
    def __invert__(self) -> "Colour":
        """
        Invert the colour channels such that each channel becomes 255 - channel.

        This means the strength of a colour (the percentage of 255 that the dominant channels are) becomes its
        brightness (the percentage of 255 that the non-dominant channels are).

        Returns
        -------
        Self
            The inverted colour.
        """
        pass

    @abc.abstractmethod
    def __add__(self, other: typing.Union["Colour", int]) -> "Colour":
        """
        Add two colours together channel by channel.

        Provides support for adding an integer to each channel.

        Parameters
        ----------
        other: Colour | int
            The other colour to add to this one.

        Returns
        -------
        Self
            A colour created from the combination of the two colours. If it's an integer, it assumes it's a greyscale
            colour (the same value in each channel).
        """
        pass

    @abc.abstractmethod
    def __sub__(self, other: typing.Union["Colour", int]) -> "Colour":
        """
        Subtract two colours together channel by channel.

        Provides support for subtracting an integer from each channel.

        Parameters
        ----------
        other: Colour | int
            The other colour to subtract from this one.

        Returns
        -------
        Self
            A colour created from the difference of the two colours. If it's an integer, it assumes it's a greyscale
            colour (the same value in each channel).
        """
        pass

    @abc.abstractmethod
    def __mul__(self, other: int) -> "Colour":
        """
        Scales this colour by the given factor.

        Parameters
        ----------
        other: int
            The scale factor to multiply this colour's channels by.

        Returns
        -------
        Self
            A colour created from the scale of this colour by the specified scale factor.
        """
        pass

    def __rmul__(self, other: int) -> "Colour":
        return self * other

    @abc.abstractmethod
    def __truediv__(self, other: int) -> "Colour":
        """
        Shrinks this colour by the given factor.

        Parameters
        ----------
        other: int
            The scale factor to divide this colour's channels by. This performs floor division.

        Returns
        -------
        Self
            A colour created from the scale of this colour by the reciprocal of the specified scale factor.
        """
        pass

    def __floordiv__(self, other: int) -> "Colour":
        """
        Alias for `__truediv__`

        Parameters
        ----------
        other: int
            The scale factor to divide this colour's channels by. This performs floor division.

        Returns
        -------
        Self
            A colour created from the scale of this colour by the reciprocal of the specified scale factor.
        """
        return self / other

    @abc.abstractmethod
    def __eq__(self, other: typing.Union["Colour", KnownColour, _tuple[int, int, int, RGBOrder], int]) -> bool:
        """
        Checks if two colours are equivalent.

        Parameters
        ----------
        other: Colour | KnownColour | tuple[int, int, int, RGBOrder] | int
            The other colour to compare to. Supports alternate constructors implicitly.

        Returns
        -------
        bool
            Whether the two colours are equivalent.
        """
        pass

    @abc.abstractmethod
    def __contains__(self, item: KnownColour) -> bool:
        """
        Checks if this colour contains the known colour.

        Parameters
        ----------
        item: KnownColour
            The known colour to check.

        Returns
        -------
        bool
            Whether this colour can be constructed from the known colour.
        """
        pass

    def __iter__(self) -> typing.Iterator[int]:
        """
        Iterate over the colours, one channel at a time, in the order of this colour.

        Yields
        ------
        int
            The channel values.
        """
        for channel in self._order.items():
            yield self._colours[channel]

    def __next__(self) -> int:
        """
        Get the next channel value from previously requested. Creates an infinite iterator.

        Returns
        -------
        int
            The next channel value.
        """
        return self[next(self._channels)]

    def items(self, in_order: RGBOrder = None) -> _tuple[int, int, int]:
        """
        Retrieve all channel values in a particular order.

        Parameters
        ----------
        in_order: RGBOrder (default is this colour's order)
            The order to retrieve the channels in.

        Returns
        -------
        tuple[int, ...]
            The channel values in the requested order.
        """
        if in_order is None:
            in_order = self._order
        f, s, t = in_order.items()
        return self._colours[f], self._colours[s], self._colours[t]

    @classmethod
    def spawn(cls, values: typing.Union[typing.Iterable[int], int], order: RGBOrder) -> "Colour":
        """
        Alternate constructor to create a new colour (greyscale or RGB).

        If provided an iterable of at least two unique values, it will form an RGB colour using those channel values.
        When provided an iterable of one unique value (or an integer), it will form a Greyscale colour.

        Parameters
        ----------
        values: Iterable[int] | int
            The channel values to create the colour from.
        order: RGBOrder
            The order to reconstruct the colour using.

        Returns
        -------
        Colour
            The new colour created from the input values.
        """
        try:
            values = tuple(values)
        except TypeError:
            return GreyscaleColour(values)
        else:
            r, g, b = values
            if r == g == b:
                return GreyscaleColour(r)
            return FullDepthColour.from_order((r, g, b), order)


class FullDepthColour(Colour):
    """
    Concrete subclass representing a full RGB colour.

    Attributes
    ----------
    _wrap: WrapMode
        The wrapping type to use for the colour channels.

    Raises
    ------
    TypeError
        If the colour channels are all identical.
    """

    def __init__(self, r: int, g: int, b: int, *, wrapping: WrapMode = None, order=RGBOrder.RGB):
        colours = dict(r=r, g=g, b=b)
        self._wrap = wrapping
        if wrapping is not None:
            for value, c_name, n_name in zip(colours.values(), order.items(), order.next()):
                if value > 255:
                    if wrapping == WrapMode.OVERFLOW:
                        colours[c_name] %= 255
                    elif wrapping == WrapMode.SPILL:
                        colours[n_name] += value - 255
                        colours[c_name] = 255
                    else:
                        colours[c_name] = 255
        if len(set(colours.values())) == 1:
            raise TypeError(f"Cannot construct an RGB colour from identical channels. Use GreyscaleColour instead")
        super().__init__(**colours, order=order)

    def __hash__(self) -> int:
        return hash(str(self))

    def __invert__(self) -> "FullDepthColour":
        return FullDepthColour(**{k: 255 - v for k, v in self._colours.items()}, wrapping=self._wrap, order=self._order)

    def __and__(self, other: "FullDepthColour") -> "FullDepthColour":
        """
        Combine two colours by filtering. If there is a non-zero channel, take *this colour's* value for it.

        As it will always take *this colour's* value, it is a non-commutative operation.

        Parameters
        ----------
        other: FullDepthColour
            The other 3-channel colour to combine with.

        Returns
        -------
        FullDepthColour
            The filtered colour.
        """
        if not isinstance(other, FullDepthColour):
            return NotImplemented
        return FullDepthColour(**{k: self[k] if other[k] else 0 for k in self._colours}, wrapping=self._wrap,
                               order=self._order)

    def __add__(self, other: typing.Union["FullDepthColour", "GreyscaleColour"]) -> "FullDepthColour":
        if not isinstance(other, (FullDepthColour, GreyscaleColour)):
            return NotImplemented
        if isinstance(other, int):
            other = GreyscaleColour(other)
        return FullDepthColour(**{k: self[k] + other[k] for k in self._colours}, wrapping=self._wrap, order=self._order)

    def __radd__(self, other: typing.Union["GreyscaleColour", int]) -> "FullDepthColour":
        if not isinstance(other, (GreyscaleColour, int)):
            return NotImplemented
        return self + other

    def __sub__(self, other: typing.Union["FullDepthColour", "GreyscaleColour", int]) -> "FullDepthColour":
        if not isinstance(other, (FullDepthColour, GreyscaleColour, int)):
            return NotImplemented
        if isinstance(other, int):
            other = GreyscaleColour(other)
        return FullDepthColour(**{k: self[k] - other[k] for k in self._colours}, wrapping=self._wrap, order=self._order)

    def __rsub__(self, other: typing.Union["GreyscaleColour", int]) -> "FullDepthColour":
        if not isinstance(other, (GreyscaleColour, int)):
            return NotImplemented
        if isinstance(other, int):
            other = GreyscaleColour(other)
        return FullDepthColour(**{k: other[k] - self[k] for k in self._colours}, wrapping=self._wrap, order=self._order)

    def __mul__(self, other: int) -> "FullDepthColour":
        if not isinstance(other, int):
            return NotImplemented
        return FullDepthColour(**{k: v * other for k, v in self._colours.items()}, wrapping=self._wrap,
                               order=self._order)

    def __truediv__(self, other: int) -> "FullDepthColour":
        if not isinstance(other, int):
            return NotImplemented
        return FullDepthColour(**{k: self[k] // other for k in self._colours}, wrapping=self._wrap, order=self._order)

    def __eq__(self, other: typing.Union[Colour, KnownColour, _tuple[int, int, int, RGBOrder]]) -> bool:
        if isinstance(other, Colour):
            return self.items() == other.items(self._order)
        elif isinstance(other, KnownColour):
            return self == FullDepthColour.from_known(other)
        elif isinstance(other, tuple):
            if len(other) == 4:
                r, g, b, order = other
                if all(isinstance(c, int) for c in (r, g, b)) and isinstance(order, RGBOrder):
                    return self.items(order) == (r, g, b)
            raise TypeError(f"Expected to have a tuple of 3 integers and an order, got {other}")
        return NotImplemented

    def __gt__(self, other: KnownColour) -> bool:
        """
        Query if the known colour is the strongest channel(s) in the colour.

        Parameters
        ----------
        other: KnownColour
            The known colour to use.

        Returns
        -------
        bool
            If the known colour's channel(s) are the strongest in this colour.
        """
        if not isinstance(other, KnownColour):
            return NotImplemented
        largest_value = max(self._colours.values())
        r_comp = g_comp = b_comp = True
        if other & KnownColour.RED:
            r_comp = largest_value == self["r"]
        if other & KnownColour.GREEN:
            g_comp = largest_value == self["g"]
        if other & KnownColour.BLUE:
            b_comp = largest_value == self["b"]
        return r_comp and g_comp and b_comp

    def __contains__(self, item: KnownColour) -> bool:
        if not isinstance(item, KnownColour):
            return False
        r_comp = g_comp = b_comp = True
        if item & KnownColour.RED:
            r_comp = bool(self["r"])
        if item & KnownColour.GREEN:
            g_comp = bool(self["g"])
        if item & KnownColour.BLUE:
            b_comp = bool(self["b"])
        return r_comp and g_comp and b_comp

    def to_known(self) -> KnownColour:
        """
        Converts the colour to a known colour constant.

        Returns
        -------
        KnownColour
            The known colour created from the colour. If a channel is non-zero it appears in this constant.
        """
        constants = (k for k in (KnownColour.RED, KnownColour.GREEN, KnownColour.BLUE) if k in self)
        return functools.reduce(operator.or_, constants)

    @classmethod
    def from_known(cls, known: KnownColour, strength=1.0, brightness=0.0, *,
                   order=RGBOrder.RGB) -> "FullDepthColour":
        """
        Alternate constructor that converts a known colour constant to a proper colour.


        Parameters
        ----------
        known: KnownColour
            The known colour constant to construct.
        strength: float
            The percentage value of the channels in the known constant (should be 0-1).
        brightness: float
            The percentage value of the channels not in the known constant (should be 0-1).
        order: RGBOrder
            The order of the channels.

        Returns
        -------
        FullDepthColour
            The constructed colour.

        Raises
        ------
        ValueError
            If strength is not between zero and one (excluding zero).
            If brightness is not between zero and one (excluding one).
        """
        if not (0 < strength <= 1):
            raise ValueError(f"Expected strength to be between 0 and 1, not including 0 (got {strength})")
        if not (0 <= brightness < 1):
            raise ValueError(f"Expected brightness to be between 0 and 1, not including 1 (got {brightness})")
        strength = int(strength * 255)
        brightness = int(brightness * 255)
        r = g = b = brightness
        if known & KnownColour.RED:
            r = strength
        if known & KnownColour.GREEN:
            g = strength
        if known & KnownColour.BLUE:
            b = strength
        return FullDepthColour(r, g, b, order=order)

    @classmethod
    def from_order(cls, vals: _tuple[int, int, int], order: RGBOrder, *,
                   wrapping: WrapMode = None) -> "FullDepthColour":
        """
        Alternate constructor for creating an RGB colour from a tuple of channel values in a particular order.

        Parameters
        ----------
        vals: tuple[int, int, int]
            The channel values.
        order: RGBOrder
            The order that the tuple represents.
        wrapping: WrapMode
            The wrapping that the colour uses.

        Returns
        -------
        FullDepthColour
            The RGB colour created from the channel tuple.
        """
        colours = {}
        for i, channel in enumerate(order.items()):
            colours[channel] = vals[i]
        return cls(**colours, wrapping=wrapping, order=order)

    @classmethod
    def colour_space(cls, colour: KnownColour) -> typing.Iterator["FullDepthColour"]:
        """
        Iterate over all colours created from the known constant.

        This means that all colours that have a strength larger than their brightness (for all valid strength and
        brightness values) are yielded.

        Parameters
        ----------
        colour: KnownColour
            The colour constant to use for the channels for.

        Yields
        ------
        FullDepthColour
            The colours created from the known constant, for all valid strength and brightness values (where strength is
            larger than brightness)
        """
        for strength in range(255, 0, -1):
            for brightness in range(0, 255):
                if strength >= brightness:
                    yield cls.from_known(colour, strength / 255, brightness / 255)


class GreyscaleColour(Colour):
    """
    Concrete subclass representing an 8-bit Greyscale colour.

    Attributes
    ----------
    _grey: int
        The unique channel value.
    """

    def __init__(self, grey: int):
        self._grey = grey
        super().__init__(grey, grey, grey, RGBOrder.RGB)

    def __hash__(self) -> int:
        return hash(str(self))

    def __invert__(self) -> "GreyscaleColour":
        return GreyscaleColour(255 - self._grey)

    def __add__(self, other: typing.Union["GreyscaleColour", int]) -> "GreyscaleColour":
        if not isinstance(other, (GreyscaleColour, int)):
            return NotImplemented
        if isinstance(other, int):
            other = GreyscaleColour(other)
        return GreyscaleColour(self._grey + other["r"])

    def __sub__(self, other: typing.Union["GreyscaleColour", int]) -> "GreyscaleColour":
        if not isinstance(other, (GreyscaleColour, int)):
            return NotImplemented
        if isinstance(other, int):
            other = GreyscaleColour(other)
        return GreyscaleColour(self._grey - other["r"])

    def __rsub__(self, other: int) -> "GreyscaleColour":
        if not isinstance(other, int):
            return NotImplemented
        return GreyscaleColour(other - self._grey)

    def __mul__(self, other: int) -> "GreyscaleColour":
        if not isinstance(other, int):
            return NotImplemented
        return GreyscaleColour(self._grey * other)

    def __truediv__(self, other: int) -> "GreyscaleColour":
        if not isinstance(other, int):
            return NotImplemented
        return GreyscaleColour(self._grey // other)

    def __eq__(self, other: typing.Union[Colour, int]) -> bool:
        if isinstance(other, GreyscaleColour):
            return self._grey == other["r"]
        elif isinstance(other, FullDepthColour):
            return other["r"] == other["g"] == other["b"] == self._grey
        elif isinstance(other, int):
            return self._grey == other
        return NotImplemented

    def __contains__(self, item: KnownColour) -> bool:
        return isinstance(item, KnownColour)

    @classmethod
    def from_strength(cls, strength: float) -> "GreyscaleColour":
        """
        Creates a `GreyscaleColour` from a percentage strength value.

        Parameters
        ----------
        strength: float
            The percentage of 255 to use. This should be between zero and one (inclusive).

        Returns
        -------
        GreyscaleColour
            The greyscale colour created using the percentage strength value.

        Raises
        ------
        ValueError
            If the strength is not 0-1.
        """
        if not (0 <= strength <= 1):
            raise ValueError(f"Expected strength to be between 0 and 1, got {strength}")
        return cls(int(strength * 255))

    @classmethod
    def colour_space(cls) -> typing.Iterator["GreyscaleColour"]:
        """
        Iterate over all greyscale colours.

        Yields
        ------
        GreyscaleColour
            A greyscale colour for each number in the range 0-255.
        """
        yield from map(cls, range(256))
