"""
Import enumerations for colours, images, and pyramids
"""

import enum as _enum


class Colours(_enum.Flag):
    """
    The most common colours, represented as binary flags

    :cvar RED:
    :cvar GREEN:
    :cvar BLUE:
    :cvar BLACK:
    :cvar YELLOW:
    :cvar PINK:
    :cvar CYAN:
    :cvar WHITE:
    """
    RED = 1
    GREEN = 2
    BLUE = 4

    BLACK = RED & GREEN & BLUE
    YELLOW = RED | GREEN
    PINK = RED | BLUE
    CYAN = GREEN | BLUE
    WHITE = RED | GREEN | BLUE


class RGBOrder(_enum.Enum):
    """
    The permutations of RGB

    :cvar RGB:
    :cvar RBG:
    :cvar BGR:
    :cvar BRG:
    :cvar GBR:
    :cvar GRB:
    """
    RGB = ("r", "g", "b")
    RBG = ("r", "b", "g")
    BGR = ("b", "g", "r")
    BRG = ("b", "r", "g")
    GBR = ("g", "b", "r")
    GRB = ("g", "r", "b")


class HSVOrder(_enum.Enum):
    """
    The permutations of HSV

    :cvar HSV:
    :cvar HVS:
    :cvar VSH:
    :cvar VHS:
    :cvar SVH:
    :cvar SHV:
    """
    HSV = (0, 1, 2)
    HVS = (0, 2, 1)
    VSH = (2, 1, 0)
    VHS = (2, 0, 1)
    SVH = (1, 2, 0)
    SHV = (1, 0, 2)


class Domain(_enum.Enum):
    """
    The domains for which a colour can be strengthened or brightened

    :cvar R: Only red channel
    :cvar G: Only green channel
    :cvar B: Only blue channel
    :cvar MAX: The highest channel
    :cvar MIN: The lowest channel
    :cvar ALL: All channels
    """
    R = 0
    G = 1
    B = 2
    MAX = 3
    MIN = 4
    ALL = 5


class Increase(_enum.Enum):
    """
    The types of increase that can be done to a value

    :BY: Add the amount on.
    :TO: The value turns into the amount.
    :FACTOR: Multiply by the value
    """
    BY = 0
    TO = 1
    FACTOR = 2


class Wrapping(_enum.Enum):
    """
    The various modes for wrapping colours such that values higher than 255 are handled

    :cvar RAISE: No handling
    :cvar TRUNC: Truncates the value to 255
    :cvar WRAP: Wrap the value to the next one (only for first out of bounds value)
    :cvar WRAP_SEQ: Wrap the value to the next one continuously
    """
    RAISE = 0
    TRUNC = 1
    WRAP = 2
    WRAP_SEQ = 3


class CMODE(_enum.Enum):
    """
    A colour mode to use

    :cvar BW:
    :cvar RGB:
    """
    BW = 0
    RGB = 1


class PMODE(_enum.Enum):
    """
    Pyramid modes

    :cvar GAUSSIAN:
    :cvar LAPLACIAN:
    """
    GAUSSIAN = 0
    LAPLACIAN = 1

