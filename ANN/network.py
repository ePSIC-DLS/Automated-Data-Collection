import numpy as np

from . import layers, utils


class SequentialNetwork:
    """
    Class to represent an ANN for 1D data.
    :var _layers list[SequentialLayer]: The layers in the network.
    :var _loss LossFunc: The cost (or loss) metric to use.
    """

    def __init__(self, *components: layers.SequentialLayer, loss: utils.LossFunc):
        if not components:
            raise ValueError("Must have at least one layer")
        self._layers = list(components)
        self._loss = loss

    def __call__(self, x: utils.Vector) -> utils.Vector:
        """
        Forward propagation of data.
        :param x: Original input data.
        :return: Probability forecast of each class.
        """
        output = x
        for layer in self._layers:
            output = layer(output)
        return output.reshape(-1)

    def train(self, input_space: np.ndarray, *output_space: float, learn_rate: float, epochs: int):
        """
        Trains the network by using backwards propagation over a series of iterations.
        :param input_space: All possible inputs.
        :param output_space: Correct outputs, aligned to inputs.
        :param learn_rate: The speed of learning (too quick will overshoot, too slow will take too long).
        :param epochs: The number of iterations to train on.
        """
        for _ in range(epochs):
            for input_array, result in zip(input_space, output_space):
                actual = np.array([result])
                prediction = self(input_array)
                self._back_prop(learn_rate, actual, prediction)

    def _back_prop(self, alpha: float, target: np.ndarray, found: np.ndarray):
        # Step 1: dc/dz = dc/dy * dy/dz
        # Step 2: dc/dw = dc/dz * dz/dw
        # Step 3: dc/db = dc/dz * dz/db
        # Step 4: dc/dx = dc/dz * dz/dx
        # dc/dy = cost'(actual, Y)
        # dy/dz = act'(z)
        # dz/dw = x
        # dz/db = 1
        # dz/dx = w
        dc_dy = self._loss[target, found]
        for layer in self._layers:
            layer.update(dc_dy, alpha)
