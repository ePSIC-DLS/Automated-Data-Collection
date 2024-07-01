import abc
import enum
import functools
import typing
from typing import Tuple as _tuple

from PyQt5 import QtWidgets as widgets, QtCore as core
from PyQt5.QtCore import Qt as enums

from ._base import AbstractWidget, CHAR_SIZE, POINT_SIZE
from .._enums import *
from .... import validation

V = typing.TypeVar("V")
E = typing.TypeVar("E", bound=enum.Enum)
F = typing.TypeVar("F", bound=enum.Flag)

__all__ = ["ValidatedWidget", "Spinbox", "PercentageBox", "Enum", "Flag", "CheckBox", "ComboBox", "Entry"]


class ValidatedWidget(widgets.QWidget, abc.ABC, typing.Generic[V], metaclass=AbstractWidget):
    """
    An abstract widget for some data validation.

    Generics
    --------
    V: Any
        The data type of the widget's value.

    Signals
    -------
    dataFailed: Exception
        Emitted when the validation failed. Carries the exception instance.
    dataPassed: V
        Emitted when the validation passed. Carries the successful data.

    Attributes
    ----------
    _data: V
        The current data value.
    _pipeline: Pipeline[Any, V]
        The validation to be performed.
    """
    dataFailed = core.pyqtSignal(Exception)
    dataPassed = core.pyqtSignal(object)

    def __init__(self, initial: V, pipeline: validation.Pipeline[typing.Any, V]):
        super().__init__()
        self._data = initial
        self._pipeline = pipeline

    def validation_pipe(self) -> validation.Pipeline[typing.Any, V]:
        """
        Getter for the validation to undergo.

        Returns
        -------
        Pipeline[Any, V]
            The pipeline the data is validated against.
        """
        return self._pipeline

    def change_data(self, data: V):
        """
        Changes the stored data. Immediately sends data to validation if it is not the current value.

        Parameters
        ----------
        data: V
            The new data value.
        """
        if data != self._data:
            self._validate(data)

    def get_data(self) -> V:
        """
        Getter for the stored data.

        Returns
        -------
        V
            The data currently stored.
        """
        return self._data

    def _validate(self, data: typing.Any):
        """
        Validates the data against the pipeline and emits the relevant signals.

        Parameters
        ----------
        data: Any
            The new data value to test.
        """
        try:
            self._pipeline.validate(data)
        except validation.ValidationError as err:
            self.dataFailed.emit(err)
        else:
            self._data = self._pipeline.translate(data)
            self.dataPassed.emit(self._data)


class Spinbox(widgets.QAbstractSpinBox, ValidatedWidget[float]):
    """
    Spinbox widget that allows data validation.

    Bound Generics
    --------------
    V: float

    Attributes
    ----------
    _step: float
        The step size of the widget's arrows.
    _valid_txt: str
        The last entry value that was valid.
    _round: tuple[RoundingMode, int]
        How to handle rounding of the spinbox's written value (not internal value).
    _transform: tuple[typing.Callable[[float], str], typing.Callable[[str], float]] | None
        How to transform the data to a string and back again (used for parsing to and from the QLineEdit)
    """
    dataFailed = ValidatedWidget.dataFailed
    dataPassed = ValidatedWidget.dataPassed

    def __init__(self, initial: float, step: float, pipeline: validation.Pipeline[float, float], *,
                 display: _tuple[typing.Callable[[float], str], typing.Callable[[str], float]] = None,
                 mode=RoundingMode.SIG_FIG, precision=3):
        widgets.QAbstractSpinBox.__init__(self)
        ValidatedWidget.__init__(self, initial, pipeline)
        self._step = step
        self._valid_txt = ""
        self._round = (mode, precision)
        self.setButtonSymbols(self.PlusMinus)
        self.setKeyboardTracking(False)
        self.setWrapping(False)
        self._transform = display
        self.editingFinished.connect(self._txt)
        self.dataPassed.connect(self._write)
        self.dataFailed.connect(lambda err: self._write(self._from_text(self._valid_txt)))
        self._write(initial)

    def change_step(self, new: float):
        """
        Change the step the arrows cause.

        Parameters
        ----------
        new: float
            The new step.
        """
        self._step = new

    def change_rounding(self, new_mode: RoundingMode = None, new_precision: int = None):
        """
        Change the rounding the display uses.

        Parameters
        ----------
        new_mode: RoundingMode
            The new mode. Defaults to the current mode.
        new_precision: int
            The new precision. Defaults to the current precision.
        """
        if new_mode is None:
            new_mode = self._round[0]
        if new_precision is None:
            new_precision = self._round[1]
        self._round = (new_mode, new_precision)

    def stepEnabled(self) -> "Spinbox.StepEnabled":
        """
        Checks which buttons are enabled.

        Returns
        -------
        StepEnabled
            Bitwise flag for both buttons being enabled.
        """
        return self.StepUpEnabled | self.StepDownEnabled

    def stepBy(self, steps: int):
        """
        Changes the data by x steps of the button in a given direction.

        Parameters
        ----------
        steps: int
            The number of steps to increment by. It can be negative for decrement.
        """
        self._validate(self._data + steps * self._step)

    def _to_text(self, value: float) -> str:
        if self._transform is not None:
            return self._transform[0](value)
        elif self._round[0] == RoundingMode.SIG_FIG:
            rounded_value = float(f"{value:.{self._round[1]}g}")
            return f"{rounded_value:{self._round[1]}g}"
        elif self._round[0] == RoundingMode.DECIMAL:
            return f"{value:.{self._round[1]}f}"
        return str(int(value))

    def _from_text(self, text: str) -> float:
        if self._transform is not None:
            return self._transform[1](text)
        return float(text)

    def _txt(self):
        text = self.lineEdit().text()
        try:
            self._validate(self._from_text(text))
        except TypeError as err:
            self.dataFailed.emit(err)

    def _write(self, success: float):
        text = self._to_text(success)
        self._valid_txt = text
        self.lineEdit().setText(text)
        chars = len(text) + 1
        point = False
        if "." in text:
            point = True
            chars -= 1
        self.setFixedSize(CHAR_SIZE * chars + POINT_SIZE * int(point), CHAR_SIZE)


class PercentageBox(Spinbox):
    """
    Specialist spinbox for percentages.

    Automatically displays the data as an integer, but represents it as a float.

    Raises
    ------
    ValueError
        If the step is not between 1 and 99.
    """

    def __init__(self, initial: int, pipeline: validation.Pipeline[float, float], *, step=1):
        if not 1 <= step < 100:
            raise ValueError("Stride should be 1 - 100 (excluding 100)")
        super().__init__(initial / 100, step * 0.01, pipeline,
                         display=(lambda f: str(int(f * 100)), lambda s: float(s) / 100))


class Enum(widgets.QComboBox, ValidatedWidget[E], typing.Generic[E]):
    """
    Special combobox designed to handle Enumerations.

    Bound Generics
    --------------
    V: E

    Generics
    --------
    E: enum.Enum
        The enum type for the validation.

    Attributes
    ----------
    _items: tuple[str,...]
        The member names.
    """
    dataFailed = ValidatedWidget.dataFailed
    dataPassed = ValidatedWidget.dataPassed

    def __init__(self, members: typing.Type[E], start: E):
        widgets.QComboBox.__init__(self)
        ValidatedWidget.__init__(self, start, validation.Pipeline.enum(members))
        self._items = tuple(member.name for member in members)
        self.currentIndexChanged.connect(lambda i: self._validate(members[self._items[i]]))
        self.addItems(self._items)
        self.dataPassed.connect(self._modify)
        self._cls = members
        self._modify(start)

    def change_data(self, data: V):
        if isinstance(data, int) or (isinstance(data, float) and int(data) == data):
            data = self._cls(data)
        super().change_data(data)

    def setCurrentText(self, text: str):
        """
        Externally change the text of the widget.


        Parameters
        ----------
        text: str
            The new text of the widget.
        """
        if not isinstance(text, str):
            text = str(text)
        self._validate(text)

    def _modify(self, text: E):
        txt = text.name
        super().setCurrentText(txt)
        self.setCurrentIndex(self._items.index(txt))


class Flag(ValidatedWidget[F], typing.Generic[F]):
    dataFailed = ValidatedWidget.dataFailed
    dataPassed = ValidatedWidget.dataPassed

    def __init__(self, members: typing.Type[F], start: F):
        super().__init__(start, validation.Pipeline.enum(members))
        self._cls = members
        layout = widgets.QHBoxLayout()
        for member in members:
            check = widgets.QCheckBox(member.name)
            check.stateChanged.connect(functools.partial(self._update, member))
            if member in start:
                check.setChecked(True)
            layout.addWidget(check)
        self.setLayout(layout)
        self._cls = members

    def change_data(self, data: V):
        if isinstance(data, int) or (isinstance(data, float) and int(data) == data):
            data = self._cls(data)
        super().change_data(data)

    def _update(self, value: F, new: enums.CheckState):
        if new == enums.Checked:
            self._data |= value
        else:
            self._data &= ~value
        self.dataPassed.emit(self._data)


class CheckBox(widgets.QCheckBox, ValidatedWidget[bool]):
    dataFailed = ValidatedWidget.dataFailed
    dataPassed = ValidatedWidget.dataPassed

    def __init__(self, text: str, initial: bool):
        ValidatedWidget.__init__(self, initial, validation.examples.any_bool)
        widgets.QCheckBox.__init__(self, text)
        self.stateChanged.connect(lambda v: self._validate("True" if v else "False"))
        self.change_data(initial)

    def change_data(self, data: V):
        super().change_data(data)
        self.setCheckState(enums.Checked if data else enums.Unchecked)


class ComboBox(widgets.QComboBox, ValidatedWidget[V], typing.Generic[V]):
    """
    Validated combobox for various options, all of a specific type.

    Attributes
    ----------
    _items: tuple[str,...]
        The string versions of the members.

    Raises
    ------
    ValueError
        If the items and the raw list are provided.
        If the raw list is not provided and the items are not provided.
    """
    dataFailed = ValidatedWidget.dataFailed
    dataPassed = ValidatedWidget.dataPassed

    def __init__(self, *items: V, start_i=0, raw: typing.Iterable[V] = None):
        if raw is not None:
            if items:
                raise ValueError("Cannot specify items and raw")
            items = raw
        elif not items:
            raise ValueError("Need raw or items")
        val_step = validation.Step(validation.ContainerValidator(*items), desc=f"ensure the input is in {items}")
        widgets.QComboBox.__init__(self)
        ValidatedWidget.__init__(self, items[start_i],
                                 validation.Pipeline(val_step, in_type=typing.Any, out_type=type(items[start_i]))
                                 )
        self._items = tuple(map(str, items))
        self.currentIndexChanged.connect(lambda i: self._validate(items[i]))
        self.addItems(self._items)
        self.dataPassed.connect(self._modify)
        self._modify(items[start_i])

    def setCurrentText(self, text: typing.Any):
        """
        Set the text of the combobox by validating.

        Parameters
        ----------
        text: Any
            The text to validate.
        """
        self._validate(text)

    def _modify(self, text: V):
        txt = str(text)
        super().setCurrentText(txt)
        self.setCurrentIndex(self._items.index(txt))


class Entry(widgets.QLineEdit, ValidatedWidget[str]):
    """
    A special text-entry point that is validated.
    """
    dataFailed = ValidatedWidget.dataFailed
    dataPassed = ValidatedWidget.dataPassed

    def __init__(self, initial: str, pipeline: validation.Pipeline[str, str], surround="\'"):
        super().__init__(initial, pipeline)
        self._surround = surround
        self._prev = f"{self._surround}{initial}{self._surround}"
        self.dataPassed.connect(self._write)
        self.dataFailed.connect(lambda _: self._write(self._prev))
        self.editingFinished.connect(self._modify)
        self._write(self._prev)

    def change_data(self, data: str):
        if self._surround == "\"":
            if not data.startswith(self._surround):
                data = f"{self._surround}{data}"
            if not data.endswith(self._surround):
                data = f"{data}{self._surround}"
        super().change_data(data)

    def setText(self, text: str):
        """
        Set the text of the widget. This will immediately validate it.

        Parameters
        ----------
        text: str
            The new text.
        """
        self._validate(str(text))

    def _write(self, text: str):
        if not text.startswith(self._surround):
            text = f"{self._surround}{text}"
        if not text.endswith(self._surround):
            text = f"{text}{self._surround}"
        self._prev = text
        super().setText(text)

    def _modify(self):
        text = self.text()
        if not text:
            return
        if text[0] == text[-1] == self._surround:
            self._validate(text)
        else:
            self._validate(f"{self._surround}{text}{self._surround}")
