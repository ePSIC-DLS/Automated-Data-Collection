import typing

import numpy as np

from ._utilities import ActivationFunction, DualFunction, DualNumber, LossFunction

exp = DualFunction(np.exp, np.exp)
sum_ = DualFunction(np.sum, lambda _: 1)
abs_ = DualFunction(np.abs, lambda x: np.nan_to_num(np.abs(x) / x, nan=1, posinf=1, neginf=1))


@ActivationFunction
def linear(x: DualNumber) -> DualNumber:
    """
    Linear activation function.

    Parameters
    ----------
    x: DualNumber
        The input.

    Returns
    -------
    DualNumber
        The unchanged input.
    """
    return x


@ActivationFunction
def sigmoid(x: DualNumber) -> DualNumber:
    """
    S-curve activation function.

    Parameters
    ----------
    x: DualNumber
        The real-valued input.

    Returns
    -------
    DualNumber
        A mapping of the input into the space [0, 1].
    """
    return 1 / (1 + exp(-x))


@ActivationFunction
def tanh(x: DualNumber) -> DualNumber:
    """
    Sharp S-curve activation function.

    Parameters
    ----------
    x: DualNumber
        The real-valued input.

    Returns
    -------
    DualNumber
        A mapping of the input into the space [-1, 1]. This has a larger gradient than the `sigmoid`.
    """
    return 2 * sigmoid.original(2 * x) - 1


def make_relu(leak: float) -> ActivationFunction:
    """
    Factory function for making the Rectified Linear Unit activation function.

    Parameters
    ----------
    leak: float
        The leak factor. Must be positive.

    Returns
    -------
    ActivationFunction
        The Rectified Linear Unit activation function.
        Note the name of the function changes slightly to note the leak factor in angled brackets.

    Raises
    ------
    ValueError
        If the leak factor is negative.
    """
    if leak < 0:
        raise ValueError("leak must be positive")

    @ActivationFunction
    def leaky_relu(x: DualNumber) -> DualNumber:
        """
        Calculate the ReLU activation function.

        Parameters
        ----------
        x: DualNumber
            The real-valued input.

        Returns
        -------
        DualNumber
            The input array, such that any negative value is multiplied by the leak factor.
        """
        x[x < 0] *= leak
        return x

    leaky_relu.__name__ = f"leaky_relu<{leak}>"
    return leaky_relu


relu = make_relu(0)
relu.__name__ = "pure_relu"


@ActivationFunction
def softmax(x: DualNumber) -> DualNumber:
    """
    The softmax activation function.

    Parameters
    ----------
    x: DualNumber
        The real-valued input.

    Returns
    -------
    DualNumber
        The normalised output such that the sum of all values is 1.
    """
    y = exp(x)
    total = sum_(y)
    return y / total


def make_mean_error(power: int) -> LossFunction:
    """
    Factory function for making a Mean Error loss function.

    Parameters
    ----------
    power: int
        The power of the error. Must be a natural number.
        This power is used such that the absolute difference is raised to this power.

    Returns
    -------
    LossFunction
        The Mean Error loss function.
        Note the name of the function changes slightly to note the power in angled brackets.

    Raises
    ------
    ValueError
        If the power is non-natural.
    """
    if power <= 0:
        raise ValueError("power must be natural")

    @LossFunction
    def mean_error(a: DualNumber, p: DualNumber) -> DualNumber:
        """
        Calculate the Mean Error loss.

        Parameters
        ----------
        a: DualNumber
            The actual result.
        p: DualNumber
            The predicted result.

        Returns
        -------
        DualNumber
            The mean error loss, raised to the power of `power`.
        """
        diff = abs_(a - p) ** power
        total = sum_(diff)
        ans = total / len(diff)
        return ans

    mean_error.__name__ = f"mean_error<{power}>"
    return mean_error


mae = make_mean_error(1)
mae.__name__ = "mean_absolute_error"
mse = make_mean_error(2)
mse.__name__ = "mean_squared_error"


def make_huber(tolerance: float, tolerance_binds: typing.Literal["lt", "gt"]) -> LossFunction:
    """
    Factory function for making a Huber loss function.

    Parameters
    ----------
    tolerance: float
        The tolerance to use to find the small error. Must be a positive number.
    tolerance_binds: {"lt", "gt"}
        Where the tolerance binds on equality.

    Returns
    -------
    LossFunction
        The Huber loss function.
        Note the name of the function changes slightly to note the tolerance and bind in angled brackets.

    Raises
    ------
    ValueError
        If the power is non-natural.
    """
    if tolerance < 0:
        raise ValueError("Tolerance must be positive")
    elif tolerance_binds not in {"lt", "gt"}:
        raise TypeError(f"Cannot bind tolerance to comparison {tolerance_binds!r}")

    @LossFunction
    def huber(a: DualNumber, p: DualNumber) -> DualNumber:
        """
        Calculates the Huber loss.

        This divides the loss into a large error (`tolerance * (err - tolerance / 2)`) and a small error (`err ^ 2 / 2`)
        which are calculated based on the absolute difference between `a` and `p`. These errors are then mapped into the
        loss based on the relationship between the error and the tolerance.

        Parameters
        ----------
        a: DualNumber
            The actual result.
        p: DualNumber
            The predicted result.

        Returns
        -------
        DualNumber
            The Huber loss.
        """
        err = abs_(a - p)
        large = tolerance * (err - tolerance / 2)
        small = err ** 2 / 2
        if tolerance_binds == "lt":
            condition = err <= tolerance
        else:
            condition = err < tolerance
        new_x = np.where(condition, small.real, large.real)
        new_dx = np.where(condition, small.derivative, large.derivative)
        return DualNumber(np.sum(new_x), new_dx)

    huber.__name__ = f"Huber<{'<' if tolerance_binds == 'gt' else '<='} {tolerance}>"
    return huber
