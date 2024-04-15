from enum import Enum as _Base, auto as _value


class UnionType(_Base):
    """
    Enumeration to describe how the union of multiple conditions is defined.

    Members
    -------
    OR

    AND

    XOR

    """
    OR = _value()
    AND = _value()
    XOR = _value()
