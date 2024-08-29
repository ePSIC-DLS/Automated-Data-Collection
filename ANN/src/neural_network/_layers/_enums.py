from enum import Enum as _Base, auto as _member


class DropoutType(_Base):
    """
    Enumeration to represent the type of dropout in a dropout layer.

    Members
    -------
    NEURONS

    INPUTS

    """
    NEURONS = _member()
    INPUTS = _member()
