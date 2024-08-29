import functools
import abc
import typing

import numpy as np
import numpy.typing as npt
import typing_extensions
from ._enums import *


class MutateCopy(abc.ABC):
    """
    Abstract decorator for making a function a mutable attribute.

    A mutable attribute has two ways of handling the parent-child relationship - a reference, or a copy.
    In 'reference' mode, modifications of the child affect the parent and vice versa.
    In 'copy' mode, modifications to parent or child will only affect that instance.

    Abstract Methods
    ----------------
    reference
    copy

    Attributes
    ----------
    _mutate: Callable
        The default implementation that assumes 'reference' mode.
    _default: ReferBehaviour
        The default behaviour (what option does the decorator take when called).
    _instance: Any
        What the method is bound to.
    """

    def __init__(self, fn: typing.Callable, /, *, default: ReferBehavior):
        self._mutate = fn
        self._default = default
        self._instance = None
        functools.update_wrapper(self, fn)

    def __get__(self, instance, owner):
        self._instance = instance
        return self

    def __call__(self, *args, **kwargs):
        if self._default == ReferBehavior.REFER:
            return self.reference(*args, **kwargs)
        elif self._default == ReferBehavior.COPY:
            return self.copy(*args, **kwargs)

    @abc.abstractmethod
    def reference(self, *args, **kwargs):
        """
        Handle the reference behaviour.

        This assumes that cross-modification is possible and care should be taken when modifying parent or child.

        Parameters
        ----------
        *args: Any
            The positional arguments.
        **kwargs: Any
            The keyword arguments.

        Returns
        -------
        Any
            The return value.
        """
        pass

    @abc.abstractmethod
    def copy(self, *args, **kwargs):
        """
        Handle the copy behaviour.

        This assumes that cross-modification is not possible.

        Parameters
        ----------
        *args: Any
            The positional arguments.
        **kwargs: Any
            The keyword arguments.

        Returns
        -------
        Any
            The return value.
        """
        pass

    @classmethod
    def decorate(cls, *, default: ReferBehavior) -> typing.Callable[[typing.Callable], typing_extensions.Self]:
        """
        Alternative constructor for using the decorator on a function being defined.

        This only requires the default behaviour; the returned function accepts a function to construct the instance.

        Parameters
        ----------
        default: ReferBehaviour
            The default behaviour (what option does the decorator take when called).

        Returns
        -------
        Callable[[Callable], Self]
            The callable that will be used as a decorator.
        """

        def _wrapped(fn: typing.Callable) -> typing_extensions.Self:
            return cls(fn, default=default)

        return _wrapped


class OnImg(MutateCopy):
    """
    Concrete subclass decorator to turn a function in the Image class into a mutable attribute.
    """

    def reference(self, *args, **kwargs):
        if self._instance is not None:
            return self._mutate(self._instance, *args, **kwargs)
        return self._mutate(*args, **kwargs)

    def copy(self, *args, **kwargs):
        if self._instance is not None:
            return self._mutate(self._instance, *args, **kwargs).copy()
        return self._mutate(*args, **kwargs).copy()


class OnHasImg(MutateCopy):
    """
    Concrete subclass decorator to turn a method of a class with an Image attribute into a mutable attribute.
    """

    def reference(self, *args, **kwargs):
        if self._instance is not None:
            self._mutate(self._instance, *args, **kwargs)
        else:
            raise UnboundLocalError(f"Cannot reference an unbound {self.__name__}")

    def copy(self, *args, **kwargs):
        if self._instance is not None:
            orig = self._instance.instance
            self._instance.instance = orig.copy()
            self._mutate(self._instance, *args, **kwargs)
            modified = self._instance.instance
            self._instance.instance = orig
            return modified
        raise UnboundLocalError(f"Cannot copy an unbound {self.__name__}")


class ThresholdBehaviour(abc.ABC):
    """
    Abstract representation of the value thresholding returns.

    Abstract Methods
    ----------------
    handle

    Attributes
    ----------
    _pin: int
        The value for which this behaviour is defined.
    """

    @property
    def pin(self) -> int:
        """
        Public access to the pin value.

        Returns
        -------
        int
            The value for which this behaviour is defined.
        """
        return self._pin

    def __init__(self, pin: int):
        if not 0 <= pin <= 255:
            raise ValueError("Pin must be between 0 and 255")
        self._pin = pin

    def __eq__(self, other: "ThresholdBehaviour") -> bool:
        if not isinstance(other, ThresholdBehaviour):
            return NotImplemented
        return self._pin == other.pin

    @abc.abstractmethod
    def handle(self, src: npt.NDArray[np.int_]) -> npt.ArrayLike:
        """
        How this behaviour handles masked input data.

        Parameters
        ----------
        src: ndarray[int, []]
            The masked input array.

        Returns
        -------
        ArrayLike
            The output value to be assigned to the array.
        """
        pass


class Source(ThresholdBehaviour):
    """
    Concrete behaviour that returns its input.
    """

    def handle(self, src: npt.NDArray[np.int_]) -> npt.ArrayLike:
        return src


class Pinned(ThresholdBehaviour):
    """
    Concrete behaviour that returns its threshold value.
    """

    def handle(self, src: npt.NDArray[np.int_]) -> npt.ArrayLike:
        return self._pin


class External(ThresholdBehaviour):
    """
    Concrete behaviour that returns a known value.

    Attributes
    ----------
    _value: int
        The value to return.
    """

    def __init__(self, pin: int, external: int):
        super().__init__(pin)
        self._value = external

    def handle(self, src: npt.NDArray[np.int_]) -> npt.ArrayLike:
        return self._value


class ThresholdType:
    """
    A complex system of thresholding, with multiple behaviours.

    The behaviours are defined for less than the threshold, equal to the threshold, and greater than the threshold.

    Attributes
    ----------
    _lt: ThresholdBehaviour
        The "less than" behaviour.
    _gt: ThresholdBehaviour
        The "greater than" behaviour.
    _eq: ThresholdBehaviour
        The "equal to" behaviour.
    _threshold: int
        The known threshold value.

    Parameters
    ----------
    lt: ThresholdBehaviour
        The "less than" behaviour.
    gt: ThresholdBehaviour
        The "greater than" behaviour.
    equal: ThresholdBehaviour | Equality
        The "equal to" behaviour. Note that by using an `Equality` it is possible to have it refer to a previously
        defined behaviour.

    Raises
    ------
    ValueError
        If the behaviours have differing threshold values.
    """

    @property
    def threshold(self) -> int:
        """
        Public access to the thresholding value.

        Returns
        -------
        int
            The known thresholding value of all behaviours.
        """
        return self._threshold

    @property
    def less(self) -> ThresholdBehaviour:
        """
        Public access to the "less than" behaviour.

        Returns
        -------
        ThresholdBehaviour
            The "less than" behaviour.
        """
        return self._lt

    @property
    def greater(self) -> ThresholdBehaviour:
        """
        Public access to the "greater than" behaviour.

        Returns
        -------
        ThresholdBehaviour
            The "greater than" behaviour.
        """
        return self._gt

    @property
    def equal(self) -> ThresholdBehaviour:
        """
        Public access to the "equal to" behaviour.

        Returns
        -------
        ThresholdBehaviour
            The "equal to" behaviour.
        """
        return self._eq

    def __init__(self, lt: ThresholdBehaviour, gt: ThresholdBehaviour,
                 equal: typing.Union[ThresholdBehaviour, Equality] = Equality.LT):
        self._lt, self._gt = lt, gt
        if equal == Equality.LT:
            self._eq = lt
        elif equal == Equality.GT:
            self._eq = self._gt
        else:
            self._eq = equal
        if lt.pin != self._eq.pin != gt.pin:
            raise ValueError("Cannot have conflicting thresholding information")
        self._threshold = self._eq.pin
