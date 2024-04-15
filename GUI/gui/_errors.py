from . import utils as _utils
from PyQt5 import QtWidgets as _widgets


class GUIError(Exception):

    @property
    def severity(self) -> _utils.ErrorSeverity:
        return self._level

    @property
    def title(self) -> str:
        return self._title

    @property
    def message(self) -> str:
        return self._message

    def __init__(self, severity: _utils.ErrorSeverity, title: str, message: str):
        self._level = severity
        self._title = title
        self._message = message
        super().__init__(f"{title} {severity.name.lower()}: {message}")

    def __str__(self) -> str:
        return f"{self._level.name.title()} - {self._title!r} due to '{self._message}'"


class StagingError(GUIError):

    def __init__(self, process: str, correct: str):
        super().__init__(_utils.ErrorSeverity.ERROR, "Operations Out Of Order",
                         f"Cannot perform {process!r} prior to {correct!r}")


class ConcurrentError(GUIError):

    def __init__(self):
        super().__init__(_utils.ErrorSeverity.WARNING, "Parallel Processes Running",
                         "Cannot have multiple conflicting processes running")


def popup_error(err: GUIError, parent: _widgets.QWidget):
    if err.severity == _utils.ErrorSeverity.INFO:
        popup = _widgets.QMessageBox.information
    elif err.severity == _utils.ErrorSeverity.WARNING:
        popup = _widgets.QMessageBox.warning
    else:
        popup = _widgets.QMessageBox.critical
    popup(parent, err.title, err.message, _widgets.QMessageBox.Ok, _widgets.QMessageBox.Ok)
