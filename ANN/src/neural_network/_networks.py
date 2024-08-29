import itertools
import typing

import numpy as np

from . import funcs
from ._aliases import *
from ._layers import sequential as seq_layers, SequentialLayer
from ._utilities import *

Layer = typing.Callable[[np.ndarray], SequentialLayer]


class SequentialNetwork:
    """
    Represents a generic ANN that can be trained.

    Note that this class assumes a layer is a function that takes a numpy array and returns a `SequentialLayer`.

    Attributes
    ----------
    _i: int
        The number of input nodes.
    _layers: tuple[SequentialLayer, ...]
        The layers to pass the input data through.
    _cost: LossFunction
        The cost function used to train the neural network.

    Parameters
    ----------
    n_inputs: int
        The number of input nodes.
    *n_neurons: int
        The number of neurons per layer.
    classes: Iterable[Layer] | Layer
        The layer classes to use. Note that each layer will be initialised with a random weight.
        If it is an iterable it must have at least as many elements as there are layers.
        If it is a singular layer, it is assumed to be an infinite iterator of that layer.
    seed: int
        The seed used to initialise the random weights. Specify this value if you wish to reproduce results.
    loss: LossFunction
        The cost function used to train the neural network.
    """

    def __init__(self, n_inputs: int, *n_neurons: int, classes: typing.Union[typing.Iterable[Layer], Layer],
                 seed: int = None, loss: LossFunction):
        self._i = n_inputs
        if not isinstance(classes, typing.Iterable):
            classes = itertools.repeat(classes)
        if not classes:
            raise ValueError("Requires at least one layer class")
        elif len(n_neurons) < 1:
            raise ValueError("Requires at least one layer size")
        rng = np.random.default_rng(seed)
        rows = []
        n_neurons = (n_inputs,) + n_neurons
        if len(n_neurons) > 2:
            rows.extend(
                cls(rng.uniform(-1, 1, (count, n_neurons[i - 1])))
                for i, (cls, count) in enumerate(zip(classes, n_neurons[1:-1]), 1)
            )
        rows.append(seq_layers.Linear(rng.random((n_neurons[-1], n_neurons[-2])), activation=funcs.softmax))
        self._layers = tuple(rows)
        self._cost = loss

    def __call__(self, x: Vector) -> Number:
        """
        Propagate the input through the neural network, layer by layer.

        Parameters
        ----------
        x: Vector
            The input to predict.

        Returns
        -------
        Number
            The predicted output.
        """
        output = x
        for i, layer in enumerate(self._layers):
            output = layer(output)
        return np.argmax(output.reshape(-1))

    def train(self, i_space: np.ndarray, o_space: np.ndarray, *, learn_rate: float, epochs: int):
        """
        Train the neural network.

        Parameters
        ----------
        i_space: ndarray[float, (t, n)]
            The inputs to use in training. Note that it has `t` rows in the matrix (where `t` is the training data size)
            and `n` columns in the matrix (where `n` is the number of input neurons).
        o_space: ndarray[float, (t, 1)]
            The actual outputs, organised with respect to the inputs (such that the ith input (from `i_space`) produces
            the ith output (from `o_space`)). Note that it has `t` rows in the matrix (where `t` is the training data
            size).
        learn_rate: float
            The learning rate. A higher learning rate will converge quicker, but sacrifices accuracy.
        epochs: int
            The number of iterations to perform. A higher number of iterations will lead to better accuracy - provided
            the algorithm does not converge onto a *local* minima (as this will cause subsequent iterations to remain at
            this minimum).
        """
        for epoch in range(epochs):
            for x, y in zip(i_space, o_space):
                y_hat = self(x)
                self._back(learn_rate, y, y_hat)
            print(f"{epoch}/{epochs} complete")

    def _back(self, alpha: float, p: Vector, a: Number):
        # Step 1: dc/dz = dc/dy * dy/dz
        # Step 2: dc/dw = dc/dz * dz/dw
        # Step 3: dc/db = dc/dz * dz/db
        # Step 4: dc/dx = dc/dz * dz/dx
        # dc/dy = cost'(actual, Y)
        # dy/dz = act'(z)
        # dz/dw = x
        # dz/db = 1
        # dz/dx = w
        dc_dy = self._cost[a, p]
        for layer in self._layers[::-1]:
            layer.update(dc_dy, alpha)
