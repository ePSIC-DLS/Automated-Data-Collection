"""
Utility module for section-specific objects.
"""
import abc
import enum
import functools
import typing

import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import Qt as events
from PyQt5 import QtCore as core, QtWidgets as widgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from modular_qt.utils import WithDecorators


class Signals(core.QObject):
    """
    Class to represent some useful signals to have

    :cvar FIN PyQt5.QTCore.pyqtSignal: The signal to emit when finished (signal argument is whether an error occurred).
    :cvar ERR PyQt5.QTCore.pyqtSignal: The signal to emit when errors occur (signal argument is the type and message).
    """
    FIN = core.pyqtSignal(bool)
    ERR = core.pyqtSignal(tuple)


class SignalUser(type(core.QObject)):
    """
    Metaclass to automatically add a protected Signals attribute and public getters for the corresponding signals.
    """

    def __new__(cls, name: str, bases: tuple, attrs: dict[str]):
        def __init__(self, *args, **kwargs):
            self._signals = Signals()
            attrs.get("__init__", lambda: None)(self, *args, **kwargs)

        return super().__new__(cls, name, bases, attrs | dict(finished=property(lambda self: self._signals.FIN),
                                                              error=property(lambda self: self._signals.ERR),
                                                              __init__=__init__))


class Thread(core.QRunnable, metaclass=SignalUser):
    """
    Class to represent a callable object that can be threaded.

    :var _func Callable: The process to thread.
    :var _args tuple: The stored arguments.
    :var _kwargs dict[str]: The stored keyword arguments.
    :var _executor PyQt5.QtCore.QThreadPool: The thread manager.
    """

    def __init__(self, fn: typing.Callable, stored_args: tuple = None, stored_kwargs: dict[str, typing.Any] = None, *,
                 pool: core.QThreadPool):
        super().__init__()
        self._func = fn
        self._args = stored_args or ()
        self._kwargs = stored_kwargs or {}
        self._executor = pool
        functools.update_wrapper(self, self._func)

    def __call__(self):
        """
        Thread the process
        """
        self._executor.start(self)

    @core.pyqtSlot()
    def run(self):
        """
        Call the function without any threading, and release status signals to track progress.
        """
        error = False
        try:
            self._func(*self._args, **self._kwargs)
        except Exception as err:
            error = True
            self.error.emit((type(err), err.args[0]))
        finally:
            self.finished.emit(error)


class Settings(enum.Flag):
    """
    Type of settings to have. Can be combined.

    :cvar REGULAR:
    :cvar ADVANCED:
    """
    REGULAR = 1
    ADVANCED = 2


class Orient(enum.Enum):
    """
    Directions of axis-aligned lines.

    :cvar VERTICAL:
    :cvar HORIZONTAL:
    """
    VERTICAL = 1
    HORIZONTAL = 2


class Capture(enum.Enum):
    """
    Enumeration to describe how to combine filter conditions.

    :cvar ALL:
    :cvar ANY:
    :cvar ONE:
    """
    ALL = 1
    ANY = 2
    ONE = 3


class ForwarderWidget(widgets.QWidget):
    """
    Special widget that forwards all events to its parent.
    """

    def mouseReleaseEvent(self, a0: events.QMouseEvent):
        """
        Callback for handling the mouse clicking the widget.

        :param a0: The event that caused the callback.
        """
        a0.ignore()

    def mouseMoveEvent(self, a0: events.QMouseEvent):
        """
        Callback for handling the mouse moving over the widget.

        :param a0: The event that caused the callback.
        """
        a0.ignore()

    def leaveEvent(self, a0: events.QEvent):
        """
        Callback for handling the mouse leaving the widget.

        :param a0: The event that caused the callback.
        """
        a0.ignore()


class Canvas(ForwarderWidget, FigureCanvasQTAgg):
    """
    Represents a matplotlib figure in a QT widget.

    :var _size int: The size of the figure (in pixels)
    :var _inches int: The size of the figure (in inches)
    :var _axes matplotlib.Axes: The axes to draw with.
    :var _image matplotlib.AxesImage | None: The drawn image.
    :var _lines list[matplotlib.Line2D]: The lines drawn on the image.
    """

    @property
    def figsize(self) -> int:
        """
        Public access to the size of the figure.

        :return: The size of the figure (in pixels)
        """
        return self._size

    def __init__(self, size: int, *, dpi=100):
        self._size = size
        self._inches = size // dpi
        figure = plt.figure(figsize=(size // dpi, size // dpi), dpi=dpi)
        self._axes = figure.add_axes((0, 0, 1, 1))
        self._axes.set_axis_off()
        self._image: typing.Optional[plt.AxesImage] = None
        self._lines: list[plt.Line2D] = []
        ForwarderWidget.__init__(self)
        FigureCanvasQTAgg.__init__(self, figure)
        self.setFixedSize(core.QSize(self._size, self._size))

    def clear(self):
        """
        Clears the figure.
        """
        self._lines.clear()
        if self._image is not None:
            self._image.remove()
        self._image = None
        self.draw()

    def image(self, data: np.ndarray):
        """
        Function to draw an image onto the axes.

        :param data: The image to draw.
        """
        if self._image is None:
            self._image = self._axes.imshow(data, cmap="gray", aspect="auto")
        else:
            self._image.set_data(data)
        self.draw()

    def histogram(self, data: np.ndarray, colours=15):
        """
       Function to draw a histogram onto the axes.

       :param data: The data to sample.
       :param colours: The number of colour groups to use.
       """
        self._axes.clear()
        self._axes.hist(data.flatten(), bins=255 // colours, log=True)
        self.draw()

    def line(self, at: int, orient: Orient, colour: str):
        """
        Function to draw a line onto the axes.

        :param at: The x-position if vertical, or y-position if horizontal.
        :param orient: The orientation of the line.
        :param colour: The colour code of the line (hex string).
        """
        func = self._axes.axvline if orient == Orient.VERTICAL else self._axes.axhline
        self._lines.append(func(at, color=colour, linewidth=self._inches // min(self._inches, 10)))
        self.draw()

    def filter_lines(self, capture: Capture, **by) -> typing.Iterator[plt.Line2D]:
        """
        Method to filter lines by certain criteria.

        :param capture: The specification in which to combine criteria.
        :param by: The criteria for the line to pass.
        :return: Yield each line in turn.
        """
        if not by:
            yield from self._lines
        for line in self._lines:
            criteria = {k: getattr(line, f"get_{k}")() == v for k, v in by.items()}
            if capture == Capture.ALL and all(criteria.values()):
                yield line
            elif capture == Capture.ANY and any(criteria.values()):
                yield line
            elif capture == Capture.ONE and sum(criteria.values()) == 1:
                yield line

    # noinspection PyTypeChecker
    @staticmethod
    def raw(line: plt.Line2D) -> int:
        """
        Method to find the raw position of a given line.

        :param line: The line to measure.
        :return: The y position for a horizontal line, or the x position for a vertical line.
        """
        x_points = np.unique(line.get_xdata())
        y_points = np.unique(line.get_ydata())
        if len(x_points) == 1:
            return x_points[0]
        elif len(y_points) == 1:
            return y_points[0]
        raise ValueError("Line is not static")

    def ratio(self, line: plt.Line2D) -> float:
        """
        Return the percentage of the line's distance to the canvas size.

        :param line: The line to measure.
        :return: A float to represent how far along the canvas this line is as a percentage.
        """
        return self.raw(line) / self._size

    def remove(self, line: plt.Line2D):
        """
        Method to remove the line from the plot.

        :param line: The line to remove
        """
        self._lines.remove(line)


class AbstractWidget(type(abc.ABC), type(widgets.QWidget)):
    """
    Metaclass to represent an abstract widget (a widget that is both an ABC and a QWidget)
    """
    pass


class AbstractWidgetWithDecorators(AbstractWidget, WithDecorators):
    """
    Metaclass to combine an abstract widget with decorators.
    """
    pass


class AdvancedSettingWindow(widgets.QWidget, abc.ABC, metaclass=AbstractWidget):
    """
    Class to represent a popup for advanced settings.

    :var _layout PyQt5.QWidgets.QGridLayout: The layout to use.
    """

    def __init__(self):
        super().__init__()
        self._layout = widgets.QGridLayout()
        self.setLayout(self._layout)

    def closeEvent(self, a0):
        """
        How to handle the user closing the popup.

        :param a0: The event that caused the close.
        """
        self.hide()

    @abc.abstractmethod
    def widgets(self) -> dict[str, widgets.QWidget]:
        """
        Find all widgets by name.

        :return: The widgets organised into a dictionary of name -> widget.
        """
        pass
