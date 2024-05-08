from enum import Enum as _Base, auto as _member, Flag as _Bitwise


class LabelOrder(_Base):
    """
    Enumeration to represent the different orderings a label can be in respect to a widget.

    Members
    -------
    PREFIX
    SUFFIX
    """
    PREFIX = _member()
    SUFFIX = _member()


class RoundingMode(_Base):
    """
    Enumeration to represent the different rounding methods to use in displaying decimal numbers.

    Members
    -------
    SIG_FIG
        Round to a fixed number of significant digits.
    DECIMAL
        Round to a fixed number of decimal places.
    TRUNCATE
        Remove the decimal component.
    """
    SIG_FIG = _member()
    DECIMAL = _member()
    TRUNCATE = _member()


class Axis(_Base):
    """
    Enumeration to represent the different axes that can be sampled

    Members
    -------
    X
    Y
    """
    X = _member()
    Y = _member()


class Extreme(_Base):
    """
    Enumeration to represent the different extremes of a given axis.

    Members
    -------
    MINIMA
    MAXIMA
    """
    MINIMA = _member()
    MAXIMA = _member()


class Overlap(_Bitwise):
    """
    Bitwise Enumeration to represent the different overlap directions possible.

    Members
    -------
    X
    Y
    """
    X = _member()
    Y = _member()


class StoppableStatus(_Base):
    """
    Enumeration to represent the different statuses a stoppable function can be in.

    Members
    -------
    ACTIVE
        Currently running the function.
    PAUSED
        Function state is remembered, but function is not running.
    DEAD
        Function state is forgotten and function is not remaining
    FINISHED
        Function is not running, state doesn't matter
    """
    ACTIVE = _member()
    PAUSED = _member()
    DEAD = _member()
    FINISHED = _member()


class ColourDisplay(_Base):
    """
    Enumeration to represent the different ways of displaying a colour.

    Members
    -------
    HEX
        Display the hexadecimal 32-bit integer for the colour.
    RGB
        Display the RGB values as integers in a tuple.
    NAME
        Display the name of the colour.
    """
    HEX = _member()
    RGB = _member()
    NAME = _member()


class ErrorSeverity(_Base):
    """
    Enumeration to represent the different severities of an error message.

    Members
    -------
    INFO
    WARNING
    ERROR
    """
    INFO = _member()
    WARNING = _member()
    ERROR = _member()


class SettingsDepth(_Bitwise):
    """
    Bitwise Enumeration to represent the different types of settings available.

    Members
    -------
    REGULAR
    ADVANCED
    """
    REGULAR = _member()
    ADVANCED = _member()


class Match(_Base):
    """
    Enumeration to represent the different numerical matching types.

    Members
    -------
    NO_LOWER
    EXACT
    NO_HIGHER
    """
    NO_LOWER = _member()
    EXACT = _member()
    NO_HIGHER = _member()

    def __call__(self, a: float, b: float) -> bool:
        if self == self.NO_LOWER:
            return a >= b
        elif self == self.EXACT:
            return a == b
        elif self == self.NO_HIGHER:
            return a <= b

    def sign(self) -> str:
        """
        Find the sign for the comparison.

        Returns
        -------
        str
            The mathematical operator that represents this numerical match.
        """
        if self == self.NO_LOWER:
            return ">="
        elif self == self.EXACT:
            return "=="
        elif self == self.NO_HIGHER:
            return "<="


class Stages(_Bitwise):
    """
    Bitwise Enumeration to represent the different save stages possible in the GUI

    Members
    -------
    SURVEY
    PROCESSED
    CLUSTERS
    MARKER
    """
    SURVEY = _member()
    PROCESSED = _member()
    CLUSTERS = _member()
    MARKER = _member()


class Windowing(_Bitwise):
    """
    Bitwise Enumeration to represent the different window types possible for drift correction.

    Members
    -------
    HANNING
        A 2D bell curve to smoothly transition on rising and falling edges (from 0-1 and 1-0).
    SOBEL
        A Sobel derivative in the x-axis and then in the y-axis. Each component is squared, summed and square rooted.
    MEDIAN
        A median filter with a kernel size of 3.
    """
    HANNING = _member()
    SOBEL = _member()
    MEDIAN = _member()


class RandomTypes(_Base):
    """
    Enumeration to represent the different random distributions used in scan patterns.

    Members
    -------
    EXP
    LAPLACE
    LOGISTIC
    NORMAL
    POISSON
    UNIFORM
    """
    EXP = _member()
    LAPLACE = _member()
    LOGISTIC = _member()
    NORMAL = _member()
    POISSON = _member()
    UNIFORM = _member()


class Corrections(_Bitwise):
    """
    Bitwise Enumeration to represent the different corrections possible.

    Members
    -------
    FOCUS
    EMISSION
    DRIFT
    """
    FOCUS = _member()
    EMISSION = _member()
    DRIFT = _member()
