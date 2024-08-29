import abc
import functools
import typing
from typing import Dict as _dict
from ._enums import *

import typing_extensions
from PyQt5 import QtCore as core

__all__ = ["make_meta", "BaseOptions", "BaseDecorator", "SimpleDecorator", "Thread", "Stoppable", "Tracked"]


def make_meta(src1: type, src2: type) -> type:
    """
    Make a metaclass from the two input types.

    Utility function, returns a class that inherits from the types of the inputs.

    Parameters
    ----------
    src1: type
        The first input class.
    src2: type
        The second input class.

    Returns
    -------
    type
        A metaclass that inherits from both inputs' types.
    """
    return type(f"{src1.__name__}And{src2.__name__}Meta", (type(src1), type(src2)), {})


P = typing_extensions.ParamSpec("P")
R = typing.TypeVar("R")
D = typing.TypeVar("D", bound="BaseDecorator")


class BaseOptions(typing_extensions.TypedDict):
    """
    Typed Dictionary for basic options. Designed only to be subclassed for other decorators with options.
    """
    pass


Options = typing.TypeVar("Options", bound=BaseOptions)


class BaseDecorator(typing.Generic[P, R, Options], abc.ABC):
    """
    A base decorator, representing a stateful decorator that can be applied to methods or regular functions.

    This decorator can have options, and constructing one using the '@' syntax requires using the `decorate` function.
    Any of these options become protected instance variables, with some name mangling from reserved words. This means
    the option 'manager' becomes the instance variable '_manager', but the option 'def_' becomes the instance variable
    '_def' (as 'def' is a reserved word, and such cannot create an option using it, but an extra underscore is
    superfluous).

    Generics
    --------
    **P: Any
        The parameter specification generic. Binds to the decorated function.
    R: Any
        The return type of the decorated function.
    Options: BaseOptions
        The option dictionary type to use when using `decorate`.

    Attributes
    ----------
    _wrapped: Callable[P, R]
        The current wrapped function, which can change depending on __get__.
    _original: Callable[P, R]
        The function to wrap.
    _instances: dict[type | None: Callable[P, R]]
        The mapping from instance type to wrapped function to call.
    """

    @property
    def wrapped(self) -> typing.Callable[P, R]:
        """
        The current wrapped function, which can change depending on __get__.

        Returns
        -------
        Callable[P, R]
            The function that will be called by this decorator when called.
        """
        return self._wrapped

    @property
    def py_func(self) -> typing.Callable[P, R]:
        """
        Public access to the underlying python function wrapped by the decorator.

        This differs from `wrapped` in that it chains for *all* applied decorators.

        Returns
        -------
        Callable[P, R]
            The underlying python function under all decorators.
        """
        obj = self
        while isinstance(obj, BaseDecorator):
            obj = obj.wrapped
        return obj

    def __init__(self, fn: typing.Callable[P, R], **kwargs: typing_extensions.Unpack[Options]):
        self._wrapped = self._original = fn
        self._options = kwargs
        self._instances: _dict[typing.Optional[type], typing.Callable[P, R]] = {None: fn}
        self.__name__ = f"{type(self).__name__}_{fn.__name__}"
        self.__doc__ = fn.__doc__

    def __get__(self, instance, owner: type) -> typing_extensions.Self:
        if instance not in self._instances:
            if isinstance(self._original, BaseDecorator):
                _new = self._original.__get__(instance, owner)
            else:
                old = self._original

                @functools.wraps(self._wrapped)
                def _new(*args: P.args, **kwargs: P.kwargs) -> R:
                    return old(instance, *args, **kwargs)
            self._instances[instance] = _new
        self._wrapped = self._instances[instance]
        return self

    def __getattr__(self, item: str):
        if item.startswith("_"):
            item = item[1:]
            if item in self._options:
                return self._options[item]
            elif f"{item}_" in self._options:
                return self._options[f"{item}_"]
            raise AttributeError(f"No such option '{item}' for {type(self)}")
        raise AttributeError(f"{type(self)} has no public attributes")

    @abc.abstractmethod
    def __str__(self) -> str:
        pass

    @abc.abstractmethod
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        pass

    def is_(self, sub: typing.Type["BaseDecorator"]) -> bool:
        """
        Checks if this object is wrapping (or is itself) a specific decorator.

        Useful for checking nesting arbitrarily nested decorators for a specific type.

        Parameters
        ----------
        sub: Type[BaseDecorator]
            The decorator type to check for.

        Returns
        -------
        bool
            Whether this decorator is (or is wrapping) the specfied type.
        """
        if not issubclass(sub, BaseDecorator) or sub == SimpleDecorator:
            raise TypeError(f"Invalid subclass type {sub}")
        obj = self
        while True:
            if isinstance(obj, sub):
                return True
            elif not isinstance(obj, BaseDecorator):
                return False
            obj = obj.wrapped

    def find(self, sub: typing.Type[D]) -> D:
        """
        Find a particular decorator subclass applied to the underlying python function.

        This will search under arbitrarily nested decorators.

        Generics
        --------
        D: BaseDecorator
            The decorator type to search for.

        Parameters
        ----------
        sub: type[D]
            The decorator type to search for.

        Returns
        -------
        D
            The found decorator subclass.

        Raises
        ------
        TypeError
            If the wrapped function is not wrapped by the specified subclass.
        """
        if not self.is_(sub):
            raise TypeError(f"{self} is not a {sub}")
        obj = self
        while True:
            if isinstance(obj, sub):
                return obj
            obj = obj.wrapped

    @classmethod
    def decorate(cls, **kwargs: typing_extensions.Unpack[Options]) \
            -> typing.Callable[[typing.Callable[P, R]], typing_extensions.Self]:
        """
        Static method for decorating a function. Use this when you want to provide extra options.

        Parameters
        ----------
        **kwargs: Options
            The options to provide.

        Returns
        -------
        Callable[[Callable[P, R], Self]
            A callable with only one argument that returns an instance of this decorator with the options provided from
            calling this function.
        """
        return functools.partial(cls, **kwargs)


SignalsDecorator = make_meta(BaseDecorator, core.QObject)


class SimpleDecorator(BaseDecorator[P, R, BaseOptions], typing.Generic[P, R], abc.ABC):
    """
    Special decorator that provided no options.

    Usage of `decorate` is discouraged (but does the same thing as the class constructor).

    Bound Generics
    --------------
    Options: BaseOptions
    """

    def __init__(self, fn: typing.Callable[P, R]):
        super().__init__(fn)

    @classmethod
    def decorate(cls) -> typing.Callable[[typing.Callable[P, R]], typing_extensions.Self]:
        """
        Static method for decorating a function. Not recommended for use.

        Returns
        -------
        Callable[[Callable[P, R], Self]
            A callable with only one argument that returns an instance of this decorator.
            This is the class constructor, hence why this function is not recommended for use - it returns the same
            thing as if it was not used.
        """
        return cls


class ThreadOptions(BaseOptions):
    """
    Typed Dictionary for thread options.

    Keys
    ----
    manager: widgets.QThreadPool
        The threadpool used to manage threaded functions.
    """
    manager: core.QThreadPool


class Thread(BaseDecorator[P, None, ThreadOptions], typing.Generic[P]):
    """
    Thread decorator for running functions concurrently.

    This means each function call happens on a new thread (managed by the specified threadpool).

    Bound Generics
    --------------
    R: None
    Options: ThreadOptions
    """

    def __init__(self, fn: typing.Callable[P, None], *, manager: core.QThreadPool):
        super().__init__(fn, manager=manager)

    def __str__(self) -> str:
        return f"<Threaded {self._wrapped}>"

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None:
        """
        Run the function on a new thread.

        Parameters
        ----------
        *args: Any
            The arguments to pass to the decorated function. Matches the positional arguments bound in P.
        **kwargs: Any
            The keyword arguments to pass to the decorated function. Matches the keyword arguments bound in P.
        """
        self._manager.start(lambda: self._wrapped(*args, **kwargs))


class Stoppable(BaseDecorator[typing.Optional[R], None, ThreadOptions], typing.Generic[R], core.QObject,
                metaclass=SignalsDecorator):
    """
    Stoppable decorator for allowing stopping a function at an arbitrary time.

    This means each function call happens on a new thread (managed by the specified threadpool), and it has signals for
    controlling execution.

    A full setup must consist of some external state - there is no way for a decorator to stop executing a function,
    so each function must have some external state that tells it to stop executing.
    The `stop` signal should be connected such that it changes the external state, so that when the signal is emitted,
    the function returns *because of the external state value*.
    The `pause` signal should only be emitted internally, as the state is most likely stored in local variables that
    external sources cannot read.

    Bound Generics
    --------------
    P: R | None
    R: None
    Options: ThreadOptions

    Generics
    --------
    R: Any
        This is the state of the function and is its only argument. Note that this is *not* the return value of the
        function (despite using the same name); this is None (as seen in `Bound Generics`).

    Signals
    -------
    callStarted: bool
        Emitted when the function has been started or resumed. Contains data for whether the function was resumed.
    callPaused:
        Emitted when the function has been paused. Contains no data.
    callStopped:
        Emitted when the function has been stopped. Contains no data.
    play:
        Emitted when the user wants to resume / start the function. Contains no data.
    pause: R
        Emitted when the user wants to pause the function. Contains data for the current state.
    stop:
        Emitted when the user wants to stop the function. Contains no data.

    Attributes
    ----------
    _state: R | None
        The current state of the function. None is assumed to be a blank state.
    _status: StoppableStatus
        The current status for the function's execution.
    """
    callStarted = core.pyqtSignal(bool)
    callPaused = core.pyqtSignal()
    callStopped = core.pyqtSignal()
    _callFinished = core.pyqtSignal()

    play = core.pyqtSignal()
    pause = core.pyqtSignal(object)
    stop = core.pyqtSignal()

    @property
    def state(self) -> StoppableStatus:
        """
        Public access to the function's status.

        Returns
        -------
        StoppableStatus
            The current status for the function's execution.
        """
        return self._status

    def __init__(self, fn: typing.Callable[P, R], *, manager: core.QThreadPool):
        BaseDecorator.__init__(self, fn, manager=manager)
        core.QObject.__init__(self)
        self._state: typing.Optional[R] = None
        self._status = StoppableStatus.FINISHED
        self.play.connect(self._play)
        self.pause.connect(self._pause)
        self.stop.connect(self._stop)
        self._callFinished.connect(self._end)

    def __str__(self) -> str:
        return f"<Stoppable {self._wrapped}>"

    def __call__(self) -> None:
        """
        Emit the play signal to start the function.
        """
        self.play.emit()

    def _play(self):
        if self._status == StoppableStatus.ACTIVE:
            return
        self.callStarted.emit(self._status != StoppableStatus.PAUSED)
        self._status = StoppableStatus.ACTIVE
        self._manager.start(self._start)

    def _pause(self, state: R):
        if self._status != StoppableStatus.ACTIVE:
            return
        self._status = StoppableStatus.PAUSED
        self._state = state
        self.callPaused.emit()

    def _stop(self):
        if self._status in {StoppableStatus.DEAD, StoppableStatus.FINISHED}:
            return
        self._status = StoppableStatus.DEAD
        self._state = None
        self.callStopped.emit()

    def _start(self):
        self._wrapped(self._state)
        self._callFinished.emit()

    def _end(self):
        if self._status == StoppableStatus.ACTIVE:
            self._status = StoppableStatus.FINISHED
            self._state = None


class Tracked(SimpleDecorator[P, R], typing.Generic[P, R], core.QObject, metaclass=SignalsDecorator):
    """
    Tracking decorator without options for knowing certain checkpoints have been hit with the function.

    Signals
    -------
    callStarted:
        Emitted when the decorator is called. Carries no data.
    callFinished: bool
        Emitted when the decorator finished calling. Carries the error status (if the function raised an error).
    callFailed: Exception
        Emitted when the decorator errors. Carries the exception instance that caused the failure.
    callSucceeded: R
        Emitted when the decorator doesn't error. Carries the return value of the function.
    """
    callStarted = core.pyqtSignal()
    callFinished = core.pyqtSignal(bool)
    callFailed = core.pyqtSignal(Exception)
    callSucceeded = core.pyqtSignal(object)

    def __init__(self, fn: typing.Callable[P, R]):
        SimpleDecorator.__init__(self, fn)
        core.QObject.__init__(self)

    def __str__(self) -> str:
        return f"<StatusTracked {self._wrapped}>"

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None:
        """
        Call the function and release the relevant status signals.

        First emits `callStarted`, then tries to execute the function. If there's any error, the `callFailed` signal is
        emitted. Otherwise, the `callSucceeded` signal is emitted. Finally, emits `callFinished` signal.

        Parameters
        ----------
        *args: Any
            The arguments to pass to the decorated function. Matches the positional arguments bound in P.
        **kwargs: Any
            The keyword arguments to pass to the decorated function. Matches the keyword arguments bound in P.
        """
        self.callStarted.emit()
        success = True
        try:
            value = self._wrapped(*args, **kwargs)
        except Exception as err:
            success = False
            self.callFailed.emit(err)
        else:
            self.callSucceeded.emit(value)
        finally:
            self.callFinished.emit(success)
