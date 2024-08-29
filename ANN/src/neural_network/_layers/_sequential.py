import functools
import typing

import numpy as np

from ._bases import SequentialLayer
from .._aliases import *
from .._utilities import *
from ._enums import *


class Linear(SequentialLayer):
    """
    A concrete sequential layer that does nothing special with its input prior to propagation.
    """

    def __call__(self, x: Number) -> Number:
        if len(np.asarray(x).shape) < 2:
            x = np.reshape(x, (-1, 1))
        self._in = x
        self._out = self._z(x)
        return self.y

    @classmethod
    def lock(cls, *, bias: np.ndarray = None, activation: ActivationFunction) \
            -> typing.Callable[[np.ndarray], "Linear"]:
        return functools.partial(cls, bias=bias, activation=activation)


class Dropout(SequentialLayer):
    """
    A concrete sequential layer that randomly drops certain characteristics of its input prior to propagation.

    Attributes
    ----------
    _shape: tuple[int, int]
        The shape of the weights matrix.
    _rng: Generator
        The random number generator.
    _drop: DropoutType
        The characteristic to drop.
    _amount: tuple[int, int]
        The maximum amount of points to drop in the chosen characteristic.
    """

    def __init__(self, weights: np.ndarray, rate: float, bias: np.ndarray = None, *, seed: int = None,
                 activation: ActivationFunction, dropout=DropoutType.NEURONS):
        super().__init__(weights, bias, activation=activation)
        self._shape = weights.shape
        if not (0 < rate < 1):
            raise ValueError("Rate must be in percentage range, excluding the ends")
        self._rng = np.random.default_rng(seed)
        self._drop = dropout
        self._amount = tuple(map(lambda y: int(rate * y), self._shape))

    def __call__(self, x: Number) -> Number:
        if self._drop == DropoutType.NEURONS:
            idx = (self._rng.integers(0, self._shape[0], self._amount[0]), slice(None, None))
        else:
            idx = (slice(None, None), self._rng.integers(0, self._shape[1], self._amount[1]))
        w = self._w[idx].copy()
        self._w[idx] = 0
        if len(np.asarray(x).shape) < 2:
            x = np.reshape(x, (-1, 1))
        self._in = x
        self._out = self._z(x)
        self._w[idx] = w
        return self.y

    @classmethod
    def lock(cls, *, rate: float, bias: np.ndarray = None, seed: int = None, activation: ActivationFunction,
             dropout=DropoutType.NEURONS) -> typing.Callable[[np.ndarray], "Dropout"]:
        return functools.partial(cls, rate=rate, bias=bias, seed=seed, activation=activation, dropout=dropout)
