"""
Module to represent the abstract base correction class.
"""
import abc
import typing

from modular_qt import utils as scans
from .. import base, page_utils as utils
from ..base import widgets, core


class BaseCorrection(base.SettingsPage):
    """
    Base correction abstract class.

    :cvar RANGE tuple[float, float]: The range of values the control can take.
    :cvar ready PyQt5.QtCore.pyqtSignal: The signal to emit when ready to fire.

    :var _value PyQt5.QtWidgets.QLabel: The current value for the correction.
    :var _control PyQt5.QtWidgets.QWidget: The control for the correction.
    :var _force PyQt5.QtWidgets.QPushButton: A button to force a correction to run.
    """
    RANGE = (0.0, 1.0)
    ready = core.pyqtSignal()

    def __init__(self, name: str, control: typing.Callable[..., widgets.QWidget], *control_args, **control_kwargs):
        base.SettingsPage.__init__(self, utils.Settings.REGULAR)
        self._value = widgets.QLabel(name)
        self._control = control(*control_args, **control_kwargs)
        self._force = widgets.QPushButton("Run Now")
        self._force.clicked.connect(self.run)
        self._layout.addWidget(self._value, 0, 0)
        self._layout.addWidget(self._control, 0, 1)
        self._layout.addWidget(self._force, 1, 0)
        self.ready.connect(lambda: self.run(False))

    def compile(self) -> str:
        return ""

    @abc.abstractmethod
    def update_on_scan(self, new: int):
        """
        How the correction updates internal state after a single scan has been performed.

        :param new: The number of scans performed
        """
        pass


class BlockingCorrection(BaseCorrection, abc.ABC, block="_block"):
    """
    Abstract subclass to represent a correction that blocks all other processes while the correction is running.

    :cvar start PyQt5.QtCore.pyqtSignal: The signal to mark that correction execution has started.
    :cvar end PyQt5.QtCore.pyqtSignal: The signal to mark that correction execution has ended.
    """
    begin = core.pyqtSignal()
    end = core.pyqtSignal()

    def _block(self, fn: typing.Callable[..., None], *args, **kwargs):
        """
        A way to block the specified function, canceling all running threads until finished.

        :param fn: The callable.
        :param args: The arguments to provide.
        :param kwargs: The keyword-only arguments to provide.
        """
        self.begin.emit()
        fn(self, *args, **kwargs)
        self.end.emit()


class LiveCorrection(BaseCorrection, base.ProcessPage, abc.ABC):
    """
    Abstract subclass to represent a correction that constantly needs to update its value.

    The updating uses the "update_on_scan" method on a separate thread to sync state between this object and an external
    source.
    """

    def __init__(self, threads: core.QThreadPool, delay: dict[str, typing.Any], name: str,
                 control: typing.Callable[..., widgets.QWidget], *control_args, **control_kwargs):
        BaseCorrection.__init__(self, name, control, *control_args, **control_kwargs)
        base.ProcessPage.__init__(self, threads)
        repeating_scan = scans.Repeater(scans.Delayer(self.update_on_scan, **delay), condition=lambda: self._activated)
        self._thread(repeating_scan, 0)()

    def stop(self):
        BaseCorrection.stop(self)
        base.ProcessPage.stop(self)
