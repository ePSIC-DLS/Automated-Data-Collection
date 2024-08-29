import abc
import typing
from typing import Optional as _None

import numpy as np

from .._aliases import *
from .._utilities import *


class Layer(abc.ABC):
    """
    Abstract base class for all layers.

    The `x` and `z` properties are aliases for the cached input and output respectively, used based on gradient descent
    notation.

    Attributes
    ----------
    _alpha: ActivationFunction
        The activation function of the layer.
    _in: Number | None
        The cached input.
    _out: Number | None
        The cached output.
    """

    @property
    def alpha(self) -> ActivationFunction:
        """
        Public access to the known activation function.

        Returns
        -------
        ActivationFunction
            The activation function of the layer.
        """
        return self._alpha

    @property
    def cached_input(self) -> Number:
        """
        Public access to the previous input.

        Returns
        -------
        Number
            The cached input.

        Raises
        ------
        ValueError
            If the cached input is empty.
        """
        if self._in is None:
            raise ValueError("No recorded input")
        return self._in

    @property
    def cached_output(self) -> Number:
        """
        Public access to the previous output.

        Returns
        -------
        Number
            The cached output.

        Raises
        ------
        ValueError
            If the cached output is empty.
        """
        if self._out is None:
            raise ValueError("No recorded output")
        return self._out

    x = cached_input
    z = cached_output

    @property
    def y(self) -> Number:
        """
        Public access to the activated output.

        Returns
        -------
        Number
            The cached output, sent through the activation function.
        """
        return self._alpha(self.z)

    def __init__(self, activation: ActivationFunction):
        self._alpha = activation
        self._in: _None[Number] = None
        self._out: _None[Number] = None

    @abc.abstractmethod
    def __call__(self, x: Number) -> Number:
        """
        Propagate the input through this layer.

        Parameters
        ----------
        x: Number
            The input to propagate.

        Returns
        -------
        Number
            The propagated output.
        """
        pass


class SequentialLayer(Layer, abc.ABC):
    """
    Abstract base class for all sequential layers.

    These layers have weights and biases to allow for linear algebra.

    Attributes
    ----------
    _w: ndarray[float_, (N, P)]
        The weights matrix for this layer. Note it has `N` rows (where N is the number of neurons for this layer) and
        `P` columns (where P is the number of neurons for the previous layer).
    _b: ndarray[float_, (N, 1)]
        The bias vector for this layer. Note it has `N` elements (where N is the number of neurons for this layer).
    """

    @property
    def weights(self) -> np.ndarray:
        """
        Public access to the weights values. This will always be a copy.

        Returns
        -------
        ndarray[float_, (N, P)]
            The weights matrix for this layer.
        """
        return self._w.copy()

    @property
    def bias(self) -> np.ndarray:
        """
        Public access to the bias values. This will always be a copy.

        Returns
        -------
        ndarray[float_, (N, 1)]
            The bias vector for this layer.
        """
        return self._b.copy()

    def __init__(self, weights: np.ndarray, bias: np.ndarray = None, *, activation: ActivationFunction):
        if bias is None:
            bias = np.ones((weights.shape[0], 1), np.float_)
        super().__init__(activation)
        self._w = weights
        self._b = bias

    def update(self, loss: Vector, learning_rate: float):
        """
        Update the weights and bias based on gradient descent.

        Parameters
        ----------
        loss: Vector
            The loss vector. This is the derivative of the overall network's cost function with respect to the output.
        learning_rate: float
            The scale in which to use for updating the weights and bias. A high scale leads to quicker convergence.
        """
        # dc_dw = dc_dy * dy_dz * dz_dw
        # dc_db = dc_dy * dy_dz * dz_db
        dc_dy = loss
        dy_dz = self._alpha[self._out]
        dz_dw = self._in
        dz_db = 1
        try:
            dc_dz = dc_dy @ dy_dz.T
        except ValueError:
            dc_dz = dc_dy * dy_dz
        try:
            dc_dw = dc_dz @ dz_dw.T
        except ValueError:
            dc_dw = dc_dz * dz_dw
        try:
            dc_db = dc_dz @ dz_db
        except ValueError:
            dc_db = dc_dz * dz_db
        self._w -= dc_dw * learning_rate
        self._b -= dc_db * learning_rate
        self._in = None
        self._out = None

    def _z(self, x: Number) -> Number:
        z = self._w @ x + self._b
        return z

    @classmethod
    @abc.abstractmethod
    def lock(cls, **kwargs) -> typing.Callable[[np.ndarray], "SequentialLayer"]:
        """
        Lock the parameters to a specific value.

        This will produce a callable such that only the weights can be specified to create the layer.

        Parameters
        ----------
        **kwargs
            The arguments to lock (passed by name).

        Returns
        -------
        Callable[[ndarray[float_, (N, P)], SequentialLayer]
            The function that creates the layer. Only the weights are customisable by this point.
        """
        pass
