from . import _aliases
from typing import Dict as _dict


class ColourOverflowError(Exception):
    """
    Special exception raised when colour channels overflow.
    """

    def __init__(self, msg: str):
        super().__init__(msg)

    @classmethod
    def from_channels(cls, channels: _dict[_aliases.Channel, int]) -> "ColourOverflowError":
        """
        Alternate constructor for creating a colour overflow with a view of the current channel values.

        Parameters
        ----------
        channels: dict[Channel, int]
            The channels that overflowed.

        Returns
        -------
        ColourOverflowError
            The error created.
        """
        return cls(f"Expected all channels to be between 0 and 255, got {channels}")


class DepthError(Exception):
    """
    Special exception raised when the depth of an array is wrong for images.
    """

    def __init__(self, expected: int, actual: int):
        super().__init__(f"Expected {expected} number of channels, got {actual}")


class ModalityError(Exception):
    """
    Special exception raised when a bimodal image has more than two colours.
    """

    def __init__(self, colours: int):
        super().__init__(f"Expected 2 colours, got {colours}")
