"""
Base module for all segments.
All classes defined are ABCs to represent the possible types of operation that can be performed.
"""
import abc
import typing

from PyQt5 import Qt as events
from PyQt5 import QtCore as core, QtWidgets as widgets

from modular_qt import errors, cv_oop as sq
from . import page_utils as utils


class Page(abc.ABC, widgets.QWidget, metaclass=utils.AbstractWidgetWithDecorators, lock="_lock"):
    """
    Abstract class to represent a blank section of the program.

    :cvar triggered PyQt5.QTCore.pyqtSignal: The signal to emit when triggered (signal argument is the callback).
    :var _layout PyQt5.QtWidgets.QGridLayout: The layout this widget uses.
    :var _activated bool: Flag to represent the state of the object.
    """
    triggered = core.pyqtSignal(object)

    _layout: widgets.QGridLayout

    def __init__(self):
        try:
            hasattr(self, "_layout")
        except RuntimeError:
            super().__init__()
            self._layout = widgets.QGridLayout()
            self.setLayout(self._layout)
        self._activated = True

    @abc.abstractmethod
    def compile(self) -> str:
        """
        Compile this object into a PAL code snippet.

        :return: The string that represents a snippet to save into a .GUIAS file.
        """
        pass

    @abc.abstractmethod
    def run(self, btn_state: bool):
        """
        How this specific step is performed.

        :param btn_state: The state of the button that caused this run.
        """
        pass

    def start(self):
        """
        Initial set-up of the section.
        """
        self._activated = True

    def stop(self):
        """
        Shutdown of the section.
        """
        self._activated = False

    def pause(self):
        """
        Halt the section to a state where it can be resumed.
        """
        self._activated = False

    def _lock(self, fn: typing.Callable[..., None], *args, **kwargs) -> typing.Optional[bool]:
        """
        A way to lock the specified function, preventing it from triggering if not active.

        :param fn: The callable.
        :param args: The arguments to provide.
        :param kwargs: The keyword-only arguments to provide.
        :return: Whether the callable had an error.
        """
        handler = errors.ErrorHandler(fn, parent=self)
        if self._activated:
            return handler(self, *args, **kwargs)
        if handler.track:
            return True


class ProcessPage(Page, abc.ABC):
    """
    Abstract subclass to represent a page with a long-running process.

    :var _manager PyQt5.QtCore.QThreadPool: The thread manager.
    :var _tracked_index int: The number of iterations the long-running process has run without completing.
    :var _running bool: Whether the long-running process is currently running.
    """

    def __init__(self, threadpool: core.QThreadPool):
        Page.__init__(self)
        self._manager = threadpool
        self._tracked_index = 0
        self._running = False

    def stop(self):
        super().stop()
        self._tracked_index = 0
        self._running = False

    def pause(self):
        super().pause()
        self._running = False

    def _thread(self, f: typing.Callable, *args, **kwargs) -> utils.Thread:
        """
        Utility partial to create a thread with the given manager.

        :param f: The callable to thread.
        :param args: The arguments to pass to the thread.
        :param kwargs: The keyword arguments to pass to the thread.
        :return: The thread managed by this section's manager.
        """
        return utils.Thread(f, args, kwargs, pool=self._manager)

    def _lock(self, fn: typing.Callable[..., None], *args, **kwargs) -> typing.Optional[bool]:
        """
        Expands the Page-wide lock by disallowing multiple long-running processes.

        :param fn: The callable.
        :param args: The arguments to provide.
        :param kwargs: The keyword-only arguments to provide.
        :return: Whether the callable had an error.
        :raise ParallelError: If the long-running process is already running.
        """
        handler = errors.ErrorHandler(fn, parent=self)
        if self._running:
            raise errors.ParallelError()
        if self._activated:
            self._running = True
            return handler(self, *args, **kwargs)
        if handler.track:
            return True


class SettingsPage(Page, abc.ABC):
    """
    Abstract subclass to represent a section with controllable settings.

    :var _reg_col PyQt5.QtWidgets.QVBoxLayout: The vertical stack of regular settings.
    :var _adv PyQt5.QtWidgets.QPushButton: The button to trigger the advanced settings popup.
    :var _window AdvancedSettingWindow | None: The advanced settings popup.
    """

    def __init__(self, spec: utils.Settings,
                 wind_type: typing.Callable[[], utils.AdvancedSettingWindow] = utils.AdvancedSettingWindow):
        Page.__init__(self)
        self._reg_col = widgets.QVBoxLayout()
        self._adv = widgets.QPushButton("Advanced settings")
        self._window: typing.Optional[utils.AdvancedSettingWindow] = None
        if spec & utils.Settings.REGULAR:
            w = utils.ForwarderWidget()
            w.setLayout(self._reg_col)
            self._layout.addWidget(w, 0, 1)
        if spec & utils.Settings.ADVANCED:
            self._window = wind_type()
            self._layout.addWidget(self._adv, 1, 1)
            self._adv.clicked.connect(lambda: self._window.show() if not self._window.isVisible() else None)

    def get_setting(self, name: str):
        """
        Get the value of the control with specified name.

        :param name: The name of the control.
        :return: The value of found control.
        :raise KeyError: If control doesn't exist.
        """
        wid = self._window.widgets()[name]
        if hasattr(wid, "value"):
            return wid.value()
        elif hasattr(wid, "checkState"):
            return wid.checkState()
        elif hasattr(wid, "currentText"):
            return wid.currentText()
        elif hasattr(wid, "text"):
            return wid.text()
        raise NotImplementedError(f"{type(wid)} unhandled {name=}")

    def get_control(self, name: str) -> widgets.QWidget:
        """
        Get the control with specified name.

        :param name: The name of the control.
        :return: The found control.
        :raise KeyError: If control doesn't exist.
        """
        try:
            return self._window.widgets()[name]
        except KeyError as err:
            wid = getattr(self, name, None)
            if wid is None:
                raise err
            return wid

    def set_setting(self, name: str) -> typing.Callable[[typing.Any], None]:
        """
        Find a callable that sets the value of the control with specified name.

        :param name: The name of the control to set.
        :return: A callable to set the value of the specified control.
        :raises KeyError: If control doesn't exist.
        """
        wid = self.get_control(name)

        def _inner(value):
            if hasattr(wid, "setValue"):
                return wid.setValue(value)
            elif hasattr(wid, "setCheckState"):
                return wid.setCheckState(value)
            elif hasattr(wid, "setCurrentText"):
                return wid.setCurrentText(value)
            elif hasattr(wid, "setText"):
                return wid.setText(value)
            raise NotImplementedError(f"{type(wid)} unhandled {name=}")

        return _inner

    def stop(self):
        super().stop()
        self.setEnabled(False)

    def start(self):
        super().start()
        self.setEnabled(True)


class DrawingPage(Page, abc.ABC):
    """
    Abstract subclass to represent a segment that requires a canvas to draw on.

    :var _canvas Canvas: The drawing region.
    :var _colour PyQt5.QtWidgets.QLabel: The colour under the cursor.
    :var _curr Image | None: The current image, with any modifications.
    :var _original Image | None: The initial image, with no modifications.
    """

    def __init__(self, size: int):
        Page.__init__(self)
        self._canvas = utils.Canvas(size)
        self._layout.addWidget(self._canvas, 0, 0)
        self._colour = widgets.QLabel(f"({0:03}, {0:03}, {0:03})")
        self._layout.addWidget(self._colour, 1, 0)
        self.setMouseTracking(True)
        self._curr: typing.Optional[sq.Image] = None
        self._original: typing.Optional[sq.Image] = None

    def clear(self):
        """
        Clear the canvas associated with the page. Will clear the images.
        """
        self._curr = None
        self._original = None
        self._canvas.clear()

    def get_mutated(self) -> typing.Optional[sq.Image]:
        """
        Grab the current image (the changed image).

        :return: The current image with any modifications.
        """
        return self._curr

    def get_original(self) -> typing.Optional[sq.Image]:
        """
        Grab the original image (the unchanged image).

        :return: The initial image with no modifications.
        """
        return self._original

    def mouseMoveEvent(self, a0: events.QMouseEvent):
        """
        Process the mouse moving across the widget.

        :param a0: The event that caused the callback.
        """
        if not self._activated:
            return a0.accept()
        if self._curr is None:
            return a0.accept()
        pos = a0.pos()
        x, y = pos.x(), pos.y()
        if (x < 0 or x >= self._canvas.figsize) or (y < 0 or y >= self._canvas.figsize):
            return a0.accept()
        r, g, b = self._curr[x, y].all()
        self._colour.setText(f"({r:03}, {g:03}, {b:03})")
        a0.accept()

    def leaveEvent(self, a0: core.QEvent):
        """
        Process the mouse leaving the widget.

        :param a0: The event that caused the callback.
        """
        if not self._activated:
            return
        self._colour.setText(f"({0:03}, {0:03}, {0:03})")
        a0.accept()
