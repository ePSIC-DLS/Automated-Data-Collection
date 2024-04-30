import typing
from typing import Dict as _dict, Tuple as _tuple

from PyQt5 import QtCore as core, QtWidgets as widgets
from PyQt5.QtCore import Qt as enums

from ._containers import LabelledWidget
from ._validators import Spinbox, V, ValidatedWidget
from .._enums import *
from .... import validation

VW = typing.TypeVar("VW", bound=ValidatedWidget)

__all__ = ["XDControl", "SizeControl", "ScanPattern", "PALFunction", "ScanPatternGroup", "Counter"]


class XDControl(ValidatedWidget, typing.Generic[VW]):
    """
    A widget that can be validated and will display X-dimensional data.

    Generics
    --------
    VW: ValidatedWidget
        The generic validated widget type. All validation is forwarded to this type, and any signals from this type are
        forwarded to this widget.

    Signals
    -------
    dataFailed: Exception
        Proxy for the inner widget's `dataFailed` signal.
    dataPassed: object
        Proxy for the inner widget's ` `dataPassed` signal.

    Attributes
    ----------
    _widgets: tuple[VW, ...]
        The widgets in this controller.

    Parameters
    ----------
    n: int
        The number of widgets to create.
    ty: Type[VW]
        The type of validated widget to instantiate.
    **kwargs
        The keyword arguments to pass to the widget constructor.

    """
    dataFailed = ValidatedWidget.dataFailed
    dataPassed = ValidatedWidget.dataPassed

    def __init__(self, n: int, ty: typing.Type[VW], **kwargs):
        super().__init__(None, ...)
        self._widgets: _tuple[VW, ...] = tuple(ty(**kwargs) for _ in range(n))
        layout = widgets.QHBoxLayout()
        self.setLayout(layout)
        for i, wid in enumerate(self._widgets):
            if i == 0:
                layout.addWidget(LabelledWidget("{", wid, LabelOrder.PREFIX))
            elif i == n - 1:
                layout.addWidget(LabelledWidget("}", wid, LabelOrder.SUFFIX))
            else:
                layout.addWidget(wid)
            wid.dataFailed.connect(self.dataFailed.emit)
            wid.dataPassed.connect(lambda _: self.dataPassed.emit(self.get_data()))

    def validation_pipe(self) -> validation.Pipeline[typing.Any, V]:
        return self._widgets[0].validation_pipe()

    def change_data(self, data: tuple):
        """
        Changes all the data in the widget, one widget at a time.

        Parameters
        ----------
        data: tuple
            The data to send to the widgets
        """
        if (exp := len(self._widgets)) != len(data):
            raise ValueError(f"Number of data points does not match expected number (expected {exp})")
        for wid, elem in zip(self._widgets, data):
            wid.change_data(elem)

    def get_data(self) -> tuple:
        """
        Gets all the data in the widget, and wraps it in an immutable data structure.

        Returns
        -------
        tuple
            The data collected from the widgets
        """
        return tuple(map(lambda vw: vw.get_data(), self._widgets))

    def get_widget(self, i: int) -> VW:
        """
        Gets a singular widget from the collection by index.

        Parameters
        ----------
        i: int
            The index of the widget to get.

        Returns
        -------
        VW
            The widget at the specified index.
        """
        return self._widgets[i]

    def all_widgets(self) -> typing.Iterator[VW]:
        """
        Iterate over all the widgets in the collection.

        Yields
        ------
        VW
            All the widgets in the collection.
        """
        yield from self._widgets


class SizeControl(XDControl[Spinbox]):
    """
    Specialist subclass of a 2-Dimensional control for size.
    """

    def __init__(self, initial: float, step: float, pipeline: validation.Pipeline[float, float], *, precision=3,
                 mode=RoundingMode.SIG_FIG,
                 display: _tuple[typing.Callable[[float], str], typing.Callable[[str], float]] = None):
        super().__init__(2, Spinbox, initial=initial, step=step, pipeline=pipeline, precision=precision, mode=mode,
                         display=display)

    def change_data(self, data: _tuple[float, float]):
        for i in range(2):
            self._widgets[i].change_data(data[i])

    def get_data(self) -> _tuple[float, float]:
        return self._widgets[0].get_data(), self._widgets[1].get_data()


class ScanPattern(widgets.QWidget):
    """
    Class to represent a specific pattern or shape that can be used to scan.

    Attributes
    ----------
    _enabled: LabelledWidget[widgets.QRadioButton]
        The enabled flag. This is an exclusive choice, so this button must be added to an external group.
    _options: tuple[ValidatedWidget, ...]
        The settings that control the pattern.
    _op_map: dict[str, ValidatedWidget]
        The mapping between option name and actual widget.
    _update: widgets.QPushButton
        The button to use to refresh the pattern.
    """
    MAX_WIDTH = 2

    def __init__(self, name: str, shortcut: str = None, live=False, **options: ValidatedWidget):
        if shortcut and len(shortcut) != 1 and shortcut.isalpha():
            raise ValueError("Expected a shortcut character that is in the alphabet")
        super().__init__()
        layout = widgets.QHBoxLayout()
        self.setLayout(layout)
        self._enabled = LabelledWidget(name, widgets.QRadioButton(f"&{(shortcut or name[0]).upper()}"),
                                       LabelOrder.PREFIX)
        self._options = {(k := " ".join(n.split("_"))): LabelledWidget(k, options[n], LabelOrder.PREFIX)
                         for n in options}
        self._op_map = options
        layout.addWidget(self._enabled)
        blank = widgets.QWidget()
        popup = widgets.QGridLayout()
        blank.setLayout(popup)
        r = 0
        for i, option in enumerate(self._options.values()):
            c = (i % self.MAX_WIDTH) + 1
            if c == 1 and i != 0:
                r += 1
            popup.addWidget(option, r, c)
        trigger = widgets.QPushButton("Settings")
        trigger.clicked.connect(lambda: blank.raise_() if blank.isVisible() else blank.show())
        layout.addWidget(trigger)
        self._update = widgets.QPushButton("Update")
        if live:
            layout.addWidget(self._update)

    def hide_option(self, option: str):
        self._options[option].hide()

    def show_option(self, option: str):
        self._options[option].show()

    def button(self) -> widgets.QRadioButton:
        """
        Getter for the enabled flag button.

        Returns
        -------
        widgets.QRadioButton
            The button representing whether this widget is enabled.
        """
        return self._enabled.focus

    def name(self) -> str:
        """
        Getter for the pattern name.

        Returns
        -------
        str
            The text attached to the enabled flag, which is the pattern name.
        """
        return self._enabled.label.text()

    def on_update(self, action: typing.Callable[[], None]):
        self._update.clicked.connect(action)

    def to_dict(self) -> _dict[str, ValidatedWidget]:
        """
        Converts the Scan Pattern's options to a dictionary

        Returns
        -------
        dict[str, widgets.QWidget]
            A mapping from widget name and parameter name to widget instance.
        """
        return self._op_map.copy()


class PALFunction(widgets.QWidget):
    """
    PAL Function widget, allowing for changing arguments.

    These functions have an optional specification enclosed within brackets.

    Signals
    -------
    toggled: bool
        Emitted whenever the enabled flag is toggled. Carries the new data.

    Attributes
    ----------
    _enabled: widgets.QCheckBox
        Whether the function should be called.
    _name: widgets.QLabel
        The name widget of the function.
    _params: tuple[LabelledWidget, ...]
        The parameters of the function.
    """
    toggled = core.pyqtSignal(bool)
    parameterChanged = core.pyqtSignal(str, object)

    def __init__(self, name: str, enabled=False, **params: ValidatedWidget):
        open_ = widgets.QLabel("(")
        close = widgets.QLabel(")")
        super().__init__()
        layout = widgets.QHBoxLayout()
        self.setLayout(layout)
        self._enabled = widgets.QCheckBox()
        self._enabled.toggled.connect(lambda _: self.toggled.emit(self._enabled.isChecked()))
        if enabled:
            self._enabled.setCheckState(enums.Checked)
        self._name = widgets.QLabel(name)
        self._params = tuple(LabelledWidget(f"{n} =", params[n], LabelOrder.PREFIX) for n in params)
        for widget in (self._enabled, self._name, open_, *self._params, close):
            layout.addWidget(widget)
        for name, wid in params.items():
            wid.dataPassed.connect(lambda v: self.parameterChanged.emit(name, v))

    def get_enabled(self) -> bool:
        """
        Getter for the enabled state of the PAL widget.

        Returns
        -------
        bool
            Whether the item is enabled - will automatically parse the state of the checkbox.
        """
        return self._enabled.isChecked()

    def name(self) -> str:
        """
        Getter for the name of the PAL widget.

        Returns
        -------
        str
            The name on the label of the item.
        """
        return self._name.text()

    def to_dict(self) -> _dict[str, widgets.QWidget]:
        """
        Converts the PAL widget and its parameters to a dictionary.

        Returns
        -------
        dict[str, widgets.QWidget]
            A mapping from widget name and parameter name to widget instance.
        """
        return {f"{self._name.text()}_{label.label.text()[:-2]}": label.focus for label in self._params}


class ScanPatternGroup(widgets.QWidget):
    newPattern = core.pyqtSignal(ScanPattern)
    patternFailed = core.pyqtSignal(Exception)

    def __init__(self, current: str, **patterns: ScanPattern):
        super().__init__()
        try:
            self._current = patterns[current]
        except KeyError:
            raise ValueError(f"Expected current to be in patterns, got {current!r}")
        self._patterns = {" ".join(k.split("_")).title(): v for k, v in patterns.items()}

    def select(self, new: ScanPattern):
        try:
            if not isinstance(new, ScanPattern):
                raise TypeError(f"Expected a ScanPattern, got {type(new)}")
            if (name := new.name()) not in self._patterns:
                raise ValueError(f"Expected name to be in patterns, got {name!r}")
            self._current = new
            self.newPattern.emit(new)
        except Exception as err:
            self.patternFailed.emit(err)

    def chosen(self) -> ScanPattern:
        return self._current


class Counter(widgets.QWidget):
    needsReset = core.pyqtSignal()
    limitChanged = core.pyqtSignal(float)
    limitFailure = core.pyqtSignal(Exception)

    def __init__(self, limit: Spinbox, context: str, step=1.0, mode=Match.NO_HIGHER, start=0.0):
        super().__init__()
        self._mode = mode
        self._curr = start
        self._step = step
        self._start = start
        self._current = widgets.QLabel(str(start))
        self._limit = limit
        layout = widgets.QHBoxLayout()
        layout.addWidget(LabelledWidget(context, self._current, LabelOrder.PREFIX))
        layout.addWidget(LabelledWidget(self._mode.sign(), self._limit, LabelOrder.PREFIX))
        limit.dataPassed.connect(self._check_from)
        limit.dataPassed.connect(self.limitChanged.emit)
        limit.dataFailed.connect(self.limitFailure.emit)
        self.setLayout(layout)

    def increase(self):
        self.set_current(self._curr + self._step)

    def decrease(self):
        self.set_current(self._curr - self._step)

    def set_current(self, new: float):
        self._curr = new
        self._current.setText(f"{self._curr:.3g}")
        self.check()

    def check(self):
        self._check_from(self._limit.get_data())

    def _check_from(self, i: int):
        if not self._mode(self._curr, i):
            self.needsReset.emit()
            self._curr = self._start
            self._current.setText("0")
