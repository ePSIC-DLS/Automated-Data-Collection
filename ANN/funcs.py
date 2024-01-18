import numpy as np

from src.utils import Expression, Vector, ActFunc, LossFunc, DualNumber

exp = Expression.register_function(np.exp, np.exp)
sum_ = Expression.register_function(lambda x: np.array([np.sum(x)]), lambda x: np.array([1]))
abs_ = Expression.register_function(np.abs, lambda x: x / np.abs(x))

__all__ = ["linear_act", "sigmoid", "tanh", "leaky_relu", "softmax", "relu", "mean_error", "huber", "mae", "mse"]


@ActFunc
def linear_act(x: Vector) -> Vector:
    """
    Linear activation function to not change output.
    :param x: The input vector.
    :return: The input vector.
    """
    return x


@ActFunc
def sigmoid(x: Vector) -> Vector:
    """
    Activation function to represent the 's-curve'. Will map any real input into the range [0, 1].
    :param x: The input vector.
    :return: A new vector where each value is between 0 and 1.
    """
    return 1 / (1 + exp(-x))


@ActFunc
def tanh(x: Vector) -> Vector:
    """
    Activation function to represent the 'hyperbolic tan' function.
    Similar to sigmoid, any real input is mapped to a finite range - [-1, 1] in this case.
    :param x: The input vector.
    :return: A new vector where each value is between -1 and 1.
    """
    return 2 * sigmoid(2 * x) - 1


def leaky_relu(leak: float) -> ActFunc:
    """
    Factory function for creating the ReLU activation function with some leak.
    :param leak: The leak to use, expected to be a small value.
    :return: The ReLU activation function, where the negative slope is the leak specified.
    """

    @ActFunc
    def relu_with_leak(x: Vector) -> Vector:
        """
        Activation function for restricting the range of the input.
        Tries to avoid the "dying ReLU" problem by having some leak.
        :param x: The input vector.
        :return: A modified output vector, where negative input is scaled by the leak, and positive input is unchanged.
        """
        y = x.copy()
        y[y < 0] *= leak
        return y

    return relu_with_leak


@ActFunc
def softmax(x: Vector) -> Vector:
    """
    Activation function for making the cumulative sum of the input one, while mapping each to the range [0, 1].
    :param x: The input vector.
    :return: A new vector where each element is [0, 1] and the sum is 1.
    """
    expon = exp(x)
    avg = sum_(expon).x[0]  # due to chain rule sum_ needs to return an array
    return expon / avg


relu = leaky_relu(0)
relu.__name__ = "relu"
relu.__doc__ = ("Baseline ReLU activation function.\nIs an alias for leaky_relu(0)\n"
                ":param x: The input vector.\n"
                ":return: A new vector where each negative value is replaced with 0.")


def mean_error(power: float) -> LossFunc:
    """
    Factory function to produce loss functions that follow the MAE and MSE convention – mean(|a – p| ** x).
    :param power: The power to raise the linear loss to.
    :return: A loss function for mean(|a – p| ** power)
    """

    @LossFunc
    def mean_error_pow(a: Vector, p: Vector) -> DualNumber:
        """
        Loss function to compute the linear loss of a and p, then find the absolute value of that.
        Will raise this result to the power specified and then compute the average.
        :param a: The actual results.
        :param p: The predicted results.
        :return: The loss.
        """
        differences = abs_(a - p) ** power
        # noinspection PyTypeChecker
        total = DualNumber.from_number(sum_(differences).x[0])
        length = len(differences.x)
        return total / length

    return mean_error_pow


def huber(tol: float) -> LossFunc:
    """
    Factory function to return the loss function for the Huber loss.
    :param tol: The tolerance to use in the calculation.
    :return: The Huber loss function.
    """

    @LossFunc
    def huber_loss(a: Vector, p: Vector) -> DualNumber:
        """
        Loss function to calculate the Huber loss, which combines MAE and MSE.
        Where the linear loss is larger than some tolerance, calculate the mean of (tolerance * (linear – tol / 2)).
        :param a: The actual results.
        :param p: The predicted results.
        :return: The Huber loss.
        """
        err = abs_(a - p)
        out = mse(a, p)
        if np.any(err > tol):
            new_out = tol * (err - tol / 2)
            # noinspection PyTypeChecker
            total = DualNumber.from_number(sum_(new_out).x[0])
            length = len(err.x)
            out = total / length
        return out

    return huber_loss


mae = mean_error(1)
mae.__name__ = "mae"
mae.__doc__ = ("Loss function to calculate the mean absolute error.\nIs an alias for mean_error(1)\n"
               ":param x: The input vector.\n"
               ":return: mean(|a - p|)")
mse = mean_error(2)
mse.__name__ = "mse"
mse.__doc__ = ("Loss function to calculate the mean squared error.\n Is an alias for mean_error(2)\n"
               ":param x: The input vector.\n"
               ":return: mean(|a - p| ** 2)")
