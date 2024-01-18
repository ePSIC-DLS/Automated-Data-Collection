import abc
import enum
import random
import typing

import numpy as np

from src import utils
from funcs import *


class Layer(abc.ABC):
    """
    ABC to represent a layer in an Artificial Neural Network (ANN).
    Each ANN layer has an activation function, stores its last input and output, and can be called.

    :var _act ActFunc: The activation function used.
    :var _in numpy.ndarray | None: The last recorded input.
    :var _out numpy.ndarray | None: The last recorded output.
    """

    @property
    def act_func(self) -> utils.ActFunc:
        """
        Public access to the activation function.
        :return: The activation function used.
        """
        return self._act

    @property
    def cached_input(self) -> np.ndarray:
        """
        Public access to the input.
        :return: The last recorded input.
        :raise ValueError: If layer isn't yet called.
        """
        if self._in is None:
            raise ValueError("No input recorded")
        return self._in

    @property
    def cached_output(self) -> np.ndarray:
        """
        Public access to the output.
        :return: The last recorded output.
        :raise ValueError: If layer isn't yet called.
        """
        if self._out is None:
            raise ValueError("No output recorded")
        return self._out

    z = property(cached_output.fget, doc="Alias for cached_output, for derivatives.\n:return: The cached output.")

    @property
    def y(self) -> np.ndarray:
        """
        Public access to the activated output.
        :return: The result of the activation function on the last recorded output.
        """
        return self._act(self._out)

    @abc.abstractmethod
    def __init__(self, activation: utils.ActFunc):
        self._act = activation
        self._in: np.ndarray | None = None
        self._out: np.ndarray | None = None

    @abc.abstractmethod
    def __call__(self, x: utils.Vector) -> utils.Vector:
        pass


class SequentialLayer(Layer, abc.ABC):
    """
    Abstract subclass to represent a layer dealing with 1D data.
    Each layer has a system of weights (magnitudes of inputs) and bias (initial conditions).

    :var _w numpy.ndarray: The weights (or magnitudes) of each input for each neuron.
    :var _b numpy.ndarray: The initial offset for each neuron.
    """

    @property
    def weights(self) -> np.ndarray:
        """
        Public access to the weights.
        :return: The magnitude of each input for each neuron.
        """
        return self._w.copy()

    @property
    def bias(self) -> utils.Vector:
        """
        Public access to the bias.
        :return: The initial offset for each neuron.
        """
        return self._b.copy()

    def __init__(self, weights: np.ndarray, bias: np.ndarray = None, *, activation: utils.ActFunc):
        super().__init__(activation)
        self._w = weights
        self._b = bias if bias is not None else np.zeros((weights.shape[1], 1), dtype=np.float64)

    def update(self, loss: float, learn_rate: float):
        # Step 1: dc/dz = dc/dy * dy/dz
        # Step 2: dc/dw = dc/dz * dz/dw
        # Step 3: dc/db = dc/dz * dz/db
        # Step 4: dc/dx = dc/dz * dz/dx
        dc_dz = loss * self._act[self._out]  # out has shape (n, 1)
        dc_dw = self._in @ dc_dz.T  # in has shape (p, 1)
        dc_db = dc_dz
        dc_dx = dc_dz.T @ self._w.T  # weight has shape (p, n)
        self._w -= dc_dw * learn_rate
        self._b -= dc_db * learn_rate
        self._in = None
        self._out = None

    def _find_z(self, arr: utils.Vector) -> utils.Vector:
        """
        Internal method for calculating common output (weights * input + bias)
        :param arr: The input array.
        :return: A vector for the matrix multiplication of the weights and input, add the bias.
        """
        return self._w.T @ arr + self._b


class LinearLayer(SequentialLayer):
    """
    Concrete subclass to represent a linear layer – has no extra effects on the internal matrix calculation.
    """

    def __call__(self, x: utils.Vector) -> utils.Vector:
        self._in = x
        self._out = self._find_z(x)
        return self.y


class DropoutLayer(SequentialLayer):
    """
    Concrete subclass to represent a layer that drops random weights (always a fixed amount). Will perform the same
    matrix calculation as a LinearLayer.

    :var _length int: The highest index to drop (excluded).
    :var _rng numpy.Generator: The random number generator.
    :var _amount int: The number of weights to drop.
    :var _drop DropType: The determiner for the shape of the dropped weights.
    """

    class DropType(enum.Enum):
        """
        Enumeration to determine the shape of dropped weights.

        :cvar NEURONS: Will drop in the shape (<indices>, :) where <indices> is a vector.
        :cvar INPUTS: Will drop in the shape (:, <indices>) where <indices> is a vector.
        :cvar RANDOM: Will randomise shape each call.
        :cvar MIXED: Will drop in the shape (<partition 1>, <partition 2>).
        """
        NEURONS = 0
        INPUTS = 1
        RANDOM = 2
        MIXED = 3

    def __init__(self, weights: typing.Optional[np.ndarray], rate: float, *, seed: int = None, activation=linear_act,
                 shape: tuple[int, int] = None, round_schema: typing.Callable[[float], int] = np.floor,
                 drop_schema=DropType.NEURONS):
        if not (0 <= rate <= 1):
            raise ValueError("Invalid percentage")
        if weights is None and shape is not None:
            weights = np.ones(shape)
        elif shape is None and weights is not None:
            shape = weights.shape
        else:
            raise ValueError("Must specify weights or shape, but not both")
        super().__init__(weights, activation=activation)
        self._length = shape[0]
        self._rng = np.random.default_rng(seed)
        self._amount = round_schema(rate * self._length)
        self._drop = drop_schema

    def __call__(self, x: utils.Vector) -> utils.Vector:
        self._in = x
        nums = self._rng.integers(0, self._length, self._amount)
        portion = self._slice(nums)
        w = self._w[portion].copy()
        self._w[portion] = 0
        self._out = self._find_z(x)
        self._w[portion] = w
        return self.y

    def _slice(self, nums: np.ndarray) -> tuple[typing.Union[int, slice, typing.Iterable[int]], ...]:
        """
        Internal method to handle the shape for dropped weights. Will rely on the drop type.
        :param nums: The indices to use (or partition).
        :return: A tuple pattern for the dropped weights.
        """
        if self._drop == self.DropType.NEURONS:
            return nums, slice(None, None)
        elif self._drop == self.DropType.INPUTS:
            return slice(None, None), nums
        elif self._drop == self.DropType.MIXED:
            neurons, inputs = np.array_split(nums, 2)
            return neurons, inputs
        else:
            self._drop = random.choice((self.DropType.INPUTS, self.DropType.NEURONS, self.DropType.MIXED))
            portion = self._slice(nums)
            self._drop = self.DropType.RANDOM
            return portion
