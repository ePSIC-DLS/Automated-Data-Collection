"""
Defines the aliases used within images.

These are mainly aliases for literal choices.

Attributes
----------
Channel: {"r", "g", "b"}
    Colour channel being queried.
ThresholdBehaviourType: {"src", "ext", "pin"}
    Used in describing how a threshold behaviour handles its input.
EqDefaults: {"gt", "lt"}
    What sign equality is a proxy for in threshold behaviours.
XAxis: {"left", "right"}
    The x-axis extremes that a corner can reside on.
YAxis: {"top", "bottom"}
    The y-axis extremes that a corner can reside on.
YDir: {"up", "down"}
    The y-axis directions that a spiral can be drawn in.
XDir: {"left", "right"}
    The x-axis directions that a spiral can be drawn in. This is a reference to the `XAxis` alias.
"""
from typing_extensions import TypeAlias as _Alias
from typing import Literal as _L

Channel: _Alias = _L["r", "g", "b"]
ThresholdBehaviourType: _Alias = _L["src", "ext", "pin"]
EqDefaults: _Alias = _L["gt", "lt"]
XAxis: _Alias = _L["left", "right"]
YAxis: _Alias = _L["top", "bottom"]
YDir: _Alias = _L["up", "down"]
XDir: _Alias = XAxis
