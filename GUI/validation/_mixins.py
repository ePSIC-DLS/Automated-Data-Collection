"""
Defines aliases for the various base and mixin classes used across validation and translation.

This is because they have non-unique names.

Attributes
----------
Validator
    The base validator class.
Translator
    The base translator class.
VBlank
    The validator that passes every test.
TBlank
    The translator that returns its input.
VMixin
    The base mixin validator class. A mixin mutates the test of an input validator in some way.
TMixin
    The base mixin translator class. A mixin mutates the test of an input translator in some way.
VUnionMixin
    The mixin that requires at least one validator to pass.
VCombinationMixin
    The mixin that has a customisable number of validators to pass.
VBranchedMixin
    The mixin that has different validators stored, where the current (active) validator can change.
VIterableMixin
    The mixin that expects all elements of the iterable to pass the validation.
TIterableMixin
    The mixin that translates all elements of the iterable.
VInverseMixin
    The mixin that inverts the validation condition.
"""
from . import _guards as _g, _morphs as _t

Validator = _g.Base
Translator = _t.Base

VBlank = _g.Pass
TBlank = _t.Pass

VMixin = _g.Mixin
TMixin = _t.Mixin

VUnionMixin = _g.UnionMixin

VCombinationMixin = _g.CombinationMixin

VBranchedMixin = _g.BranchedMixin

VIterableMixin = _g.IterableMixin
TIterableMixin = _t.IterableMixin

VInverseMixin = _g.InverseMixin
