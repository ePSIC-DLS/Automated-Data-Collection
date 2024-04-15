import abc
import typing
from typing import Tuple as _tuple, Dict as _dict

import typing_extensions
from PyQt5 import QtGui as gui, QtWidgets as widgets, QtCore as core

from .._decorators import make_meta

__all__ = ["AbstractWidget", "Forwarder", "SettingsDict", "SettingsPopup", "CHAR_SIZE", "POINT_SIZE"]

AbstractWidget = make_meta(abc.ABC, widgets.QWidget)

CHAR_SIZE = 20
POINT_SIZE = 5


class Forwarder(AbstractWidget):
    """
    Special kind of abstract widget that forwards all events to other widgets.
    """

    def __new__(cls, name: str, bases: _tuple[type, ...], attrs: _dict[str, typing.Any]):
        all_attrs = {}
        for base in bases[::-1]:
            all_attrs.update(base.__dict__)
        all_attrs.update(attrs)
        for handler in (
                "changeEvent", "hideEvent", "showEvent", "dropEvent", "dragLeaveEvent", "dragMoveEvent",
                "dragEnterEvent", "actionEvent", "tabletEvent", "contextMenuEvent", "closeEvent", "resizeEvent",
                "moveEvent", "paintEvent", "leaveEvent", "enterEvent", "focusOutEvent", "focusInEvent",
                "keyReleaseEvent", "keyPressEvent", "wheelEvent", "mouseMoveEvent", "mouseDoubleClickEvent",
                "mouseReleaseEvent", "mousePressEvent"
        ):
            if handler not in all_attrs:
                attrs[handler] = lambda self, a0: a0.ignore()
        return super().__new__(cls, name, bases, attrs)


class SettingsDict(typing_extensions.TypedDict):
    """
    Typed Dictionary for basic settings. Designed only to be subclassed for other settings windows.
    """
    pass


class SettingsPopup(widgets.QWidget, abc.ABC, metaclass=AbstractWidget):
    """
    Special popup widget for changing advanced settings.

    Signals
    -------
    settingChanged: str, object
        The name of the setting and the new value.

    Attributes
    ----------
    _layout : QVBoxLayout
        The layout of the popup.
    """

    settingChanged = core.pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self._layout = widgets.QVBoxLayout()
        self.setLayout(self._layout)

    def closeEvent(self, a0: gui.QCloseEvent):
        """
        Close the popup. Will hide the widget then ignore the event.

        Parameters
        ----------
        a0: gui.QCloseEvent
            The event that caused the callback.
        """
        self.hide()
        a0.ignore()

    @abc.abstractmethod
    def widgets(self) -> SettingsDict:
        """
        Get all the widgets by name.

        Returns
        -------
        SettingsDict
            The dictionary of all settings.
        """
        pass
