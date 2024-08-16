from . import utils as _utils
from PyQt5 import QtWidgets as _widgets


class GUIError(Exception):
    """
    Custom exception to represent GUI-specific errors that can be handled by creating a popup.

    Attributes
    ----------
    _level: ErrorSeverity
        The error severity level.
    _title: str
        The title of the error popup - this is a short description of the error.
    _message: str
        The error message. This goes into more detail than the title.
    """

    @property
    def severity(self) -> _utils.ErrorSeverity:
        """
        Public access to the severity of the level.

        Returns
        -------
        ErrorSeverity
            The error severity level.
        """
        return self._level

    @property
    def title(self) -> str:
        """
        Public access to a short description of the error.

        Returns
        -------
        str
            The title of the error popup.
        """
        return self._title

    @property
    def message(self) -> str:
        """
        Public access to a more detailed error message.

        Returns
        -------
        str
            The error message.
        """
        return self._message

    def __init__(self, severity: _utils.ErrorSeverity, title: str, message: str):
        self._level = severity
        self._title = title
        self._message = message
        super().__init__(f"{title} {severity.name.lower()}: {message}")

    def __str__(self) -> str:
        return f"{self._level.name.title()} - {self._title!r} due to '{self._message}'"


class StagingError(GUIError):
    """
    Special GUI error when operations were performed out of order.
    """

    def __init__(self, process: str, correct: str):
        super().__init__(_utils.ErrorSeverity.ERROR, "Operations Out Of Order",
                         f"Cannot perform {process!r} prior to {correct!r}")


class ConcurrentError(GUIError):
    """
    Special GUI error when multiple parallel processes are running concurrently.
    """

    def __init__(self):
        super().__init__(_utils.ErrorSeverity.WARNING, "Parallel Processes Running",
                         "Cannot have multiple conflicting processes running")


def popup_error(err: GUIError, parent: _widgets.QWidget):
    """
    Form a popup widget from a given GUI error.

    Parameters
    ----------
    err: GUIError
        The reason for failure.
    parent: QWidget
        The parent widget. The popup appears above this widget.
    """
    if err.severity == _utils.ErrorSeverity.INFO:
        popup = _widgets.QMessageBox.information
    elif err.severity == _utils.ErrorSeverity.WARNING:
        popup = _widgets.QMessageBox.warning
    else:
        popup = _widgets.QMessageBox.critical
    popup(parent, err.title, err.message, _widgets.QMessageBox.Ok, _widgets.QMessageBox.Ok)
