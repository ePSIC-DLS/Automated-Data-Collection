"""
Module for custom widgets used throughout the pages.
"""
import abc
import functools
import typing

from PyQt5 import Qt as events
from PyQt5 import QtWidgets as widgets, QtGui as colours
from PyQt5.QtCore import Qt as enums

from modular_qt import utils as scans, errors
from . import base
from .base import utils, core, sq


class ValidatedSpinBox(widgets.QSpinBox, abc.ABC, metaclass=utils.AbstractWidget):
    """
    Custom spinbox that disallows going out of range (both with button presses and by disabling the internal entry).

    :var _values list[int]: The values this box can take.
    """

    @abc.abstractmethod
    def __init__(self, values: typing.Iterable[int], value: int = None):
        super().__init__()
        values = list(values)
        self._values = values
        self.setRange(min(values), max(values))
        self.lineEdit().setReadOnly(True)
        if value is None:
            value = values[0]
        self.setValue(value)

    def setValue(self, val: int):
        """
        Overload of setting the value. Will only set the value if it is an allowed value.

        :param val: The new value.
        """
        if val in self._values:
            super().setValue(val)
        else:
            raise ValueError(f"Value {val} not in {self._values}")


class ValidatedDoubleSpinBox(widgets.QDoubleSpinBox, abc.ABC, metaclass=utils.AbstractWidget):
    """
    Custom spinbox that disallows going out of range (both with button presses and by disabling the internal entry)

    :var _values Container[float]: The values this box can take.
    """

    @abc.abstractmethod
    def __init__(self, values: typing.Union[typing.Iterable[float], scans.FloatTarget], value: float = None):
        super().__init__()
        if isinstance(values, scans.FloatTarget):
            self.setRange(values.min, values.max)
            if value is None:
                value = values.min
        else:
            values = list(values)
            self.setRange(min(values), max(values))
            if value is None:
                value = values[0]
        self._values = values
        self.lineEdit().setReadOnly(True)
        self.setValue(value)

    def setValue(self, val: float):
        """
        Overload of setting the value. Will only set the value if it is an allowed value.

        :param val: The new value.
        """
        if val in self._values:
            super().setValue(val)
        else:
            raise ValueError(f"Value {val} not in {self._values}")


class FixedSpinBox(ValidatedSpinBox):
    """
    Special subclass to represent a spinbox with a specified step
    """

    def __init__(self, limits: tuple[int, int, int], context: str = None, *, value: int = None):
        super().__init__(range(limits[0], limits[1] + limits[2], limits[2]), value)
        self.setSingleStep(limits[2])
        if context:
            self.setSuffix(f" {context}")
        self.setAccelerated(True)

    def setMinimum(self, low: int):
        """
        Public method to change the lowest value this spinbox can take.

        :param low: The new lowest.
        """
        super().setMinimum(low)
        if self._values:
            self._values = list(range(low, self._values[-1] + self.singleStep()))

    def setMaximum(self, high: int):
        """
        Public method to change the highest value this spinbox can take.

        :param high: The new highest.
        """
        super().setMaximum(high)
        if self._values:
            self._values = list(range(self._values[0], high + self.singleStep()))

    @classmethod
    def from_range(cls, limits: tuple[int, int], step: int, context: str = None, *, value: int = None) -> typing.Self:
        """
        Alternative constructor to construct the object from limits and a step.

        :param limits: The minimum and maximum values that the spinbox can take.
        :param step: The step between valid values.
        :param context: Any suffix to have.
        :param value: Starting value.
        :return: Constructed SpinBox
        """
        return cls((limits[0], limits[1], step), context, value=value)


class FixedDoubleSpinBox(ValidatedDoubleSpinBox):
    """
    Special subclass to represent a spinbox with a specified step
    """

    def __init__(self, limits: tuple[float, float, float], context: str = None, *, value: float = None):
        super().__init__(scans.FloatTarget(limits[0], limits[1], limits[2]), value)
        self.setSingleStep(limits[2])
        if context:
            self.setSuffix(f" {context}")
        self.setAccelerated(True)

    def setMinimum(self, low: int):
        """
        Public method to change the lowest value this spinbox can take.

        :param low: The new lowest.
        """
        super().setMinimum(low)
        self._values = scans.FloatTarget(low, self._values.max, self._values.stride, self._values.accuracy)

    def setMaximum(self, high: int):
        """
        Public method to change the highest value this spinbox can take.

        :param high: The new highest.
        """
        super().setMaximum(high)
        self._values = scans.FloatTarget(self._values.min, high, self._values.stride, self._values.accuracy)

    @classmethod
    def from_range(cls, limits: tuple[float, float], step: float, context: str = None, *,
                   value: float = None) -> typing.Self:
        """
        Alternative constructor to construct the object from limits and a step.

        :param limits: The minimum and maximum values that the spinbox can take.
        :param step: The step between valid values.
        :param context: Any suffix to have.
        :param value: Starting value.
        :return: Constructed SpinBox
        """
        return cls((limits[0], limits[1], step), context, value=value)


class ComboSpin(ValidatedSpinBox):
    """
    Special subclass to combine a combobox and a spinbox.

    :var _wrapping bool: Whether to wrap around.
    :var _index int: The index of the current value.
    :var _maximum int: The largest value the index can take.
    """

    def __init__(self, *values: int, start=0, wrap=False):
        super().__init__(values)
        self.setRange(self.minimum() - wrap, self.maximum() + wrap)
        self._wrapping = wrap
        self._index = start
        self._maximum = len(values) - 1
        if self._index < 0:
            self._index += (self._maximum + 1)
        self.setValue(self._values[self._index])

    def stepBy(self, steps: int):
        """
        Custom implementation of clicking the buttons

        :param steps: The number of clicks
        """
        self._index += steps
        if self._wrapping:
            if self._index > self._maximum:
                self._index = 0
            elif self._index < 0:
                self._index = self._maximum
        self.setValue(self._values[self._index])


class DoubleComboSpin(ValidatedDoubleSpinBox):
    """
    Special subclass to combine a combobox and a spinbox.

    :var _wrapping bool: Whether to wrap around.
    :var _index int: The index of the current value.
    :var _maximum int: The largest value the index can take.
    """

    def __init__(self, *values: float, start=0, wrap=False):
        super().__init__(values)
        self.setRange(self.minimum() - wrap, self.maximum() + wrap)
        self._wrapping = wrap
        self._index = start
        self._maximum = len(values) - 1
        if self._index < 0:
            self._index += (self._maximum + 1)
        self.setValue(self._values[self._index])

    def stepBy(self, steps: int):
        """
        Custom implementation of clicking the buttons.

        :param steps: The number of clicks
        """
        self._index += steps
        if self._wrapping:
            if self._index > self._maximum:
                self._index = 0
            elif self._index < 0:
                self._index = self._maximum
        self.setValue(self._values[self._index])


class Marker(widgets.QLabel):
    """
    Special label that marks a location and can be removed by left-clicking.

    :var _controller DrawingPage: The parent of the marker.
    :var _x int: Horizontal co-ordinate.
    :var y int: Vertical co-ordinate.
    :var _rem_square Callable[[int, int], None]: The function to remove the marker.
    """

    def __init__(self, master: base.DrawingPage, at: tuple[int, int], removal: typing.Callable[[int, int], None]):
        super().__init__(f"<{at[0]:02}, {at[1]:02}>")
        self._controller = master
        self._x, self._y = at
        self._rem_square = functools.partial(removal, self._x, self._y)
        self.setFixedSize(100, 50)

    def mouseReleaseEvent(self, a0: events.QMouseEvent):
        """
        Handle clicking on the marker.

        :param a0: The event that caused the callback.
        :raise StagingError: If called before the controller is run.
        """
        if a0.button() == enums.LeftButton:
            if self._controller.get_mutated() is None:
                raise errors.StagingError("Remove Additional Zones", "Scanning")
            self._rem_square()
            return a0.accept()
        a0.ignore()


class OrderedButton(widgets.QCheckBox):
    """
    Custom checkbox that remembers the order of clicks.

    :var _name str: The name of the box.
    :var _command Callable[[bool], None]: The command associated with the button.
    :var _container OrderedButtonGroup: The group this button belongs to.
    :var _largest int: The length of the largest number in the group.
    :var _num int: The current order.
    :var _longest int: The length of the largest name in the group.
    """

    @property
    def group(self) -> "OrderedButtonGroup":
        """
        Public access to the group.

        :return: The group this button belongs to.
        """
        return self._container

    def __init__(self, name: str, command: typing.Callable[[bool], None], group: "OrderedButtonGroup"):
        super().__init__()
        self.setText(name)
        self._name = name
        self._command = command
        self._container = group
        self._largest = len(str(self._container.max))
        self._num = 0
        self._longest = 1

    def pad_name(self, longest: int):
        """
        Pad the name with spaces to ensure the widget doesn't resize when clicked.

        :param longest: The longest length.
        """
        self._longest = longest
        self.setText(f"{self._name:^{longest + self._largest + 2}}")  # +2 for colon and space
        self.setFixedWidth(len(self.text()) + 100)

    def mouseReleaseEvent(self, a0: events.QMouseEvent):
        """
        Handles clicking on the widget.

        :param a0: The event that caused the callback.
        """
        btn = a0.button()
        if btn not in (enums.LeftButton, enums.RightButton):
            return a0.ignore()
        if btn == enums.RightButton:
            if self._num == 0:
                return a0.ignore()
            self._container.remove(self._num)
            self._num = 0
            self.setText(f"{self._name}")
        else:
            if self._num != 0:
                return a0.ignore()
            self._num = self._container.get_next()
            self._container.insert(self._num)
            self.setText(f"{self._num:{self._largest}}: {self._name:^{self._longest}}")
        self.setCheckState(enums.Unchecked if self._num == 0 else enums.PartiallyChecked)

    def command(self) -> str:
        """
        Gets the name of the command to invoke.

        :return: The function name (not qualname) associated with the button.
        """
        return self._command.__name__

    def get_num(self) -> int:
        """
        Public access to the number this button currently holds.

        :return: The current number of the button.
        """
        return self._num

    def invoke(self, state: bool):
        """
        Invoke the command associated.

        :param state: The button state to pass into the callback
        """
        self._command(state)

    def force(self, num: int):
        """
        Forces the button to be the specified number.

        :param num: The number to be.
        """
        self._num = num
        if self._num == 0:
            self._container.remove(num)
            self.setText(f"{self._name}")
        else:
            self._container.insert(num)
            self.setText(f"{self._num:{self._largest}}: {self._name:^{self._longest}}")
        self.setCheckState(enums.Unchecked if self._num == 0 else enums.PartiallyChecked)


class OrderedButtonGroup:
    """
    Container for ordered buttons.

    :var _record dict[int, bool]: A mapping of number to filled status.
    :var _amount int: The maximum number of records.
    """

    @property
    def max(self) -> int:
        """
        Public access to the number of records.

        :return: The maximum number of records.
        """
        return self._amount

    def __init__(self, limit: int):
        self._record: dict[int, bool] = {i: False for i in range(1, limit + 1)}
        self._amount = limit

    def insert(self, at: int):
        """
        Mark the specified position as filled.

        :param at: The position to mark.
        :raise ValueError: If value isn't between one and the maximum number of records.
        """
        self._record[at] = True
        if len(self._record) != self._amount:
            del self._record[at]
            raise ValueError("Invalid position!")

    def remove(self, at: int):
        """
        Mark the specified position as unfilled.

        :param at: The position to mark.
        :raise ValueError: If value isn't between one and the maximum number of records.
        """
        self._record[at] = False
        if len(self._record) != self._amount:
            del self._record[at]
            raise ValueError("Invalid position!")

    def get_next(self) -> int:
        """
        Find the last mark filled, and increment it by 1.

        :return: The next available position after marking.
        """
        mark = 1
        for i, filled in self._record.items():
            if filled:
                mark = i + 1
        return mark


class ColourWheel(widgets.QWidget):
    """
    Widget to represent a wheel that can be used to edit colours.

    :cvar colourChanged PyQt5.QtCore.pyqtSignal: The signal to emit when the colour is changed, with a string code.
    :cvar valuesChanged PyQt5.QtCore.pyqtSignal: The signal to emit when the colour is changed, with the colour object.

    :var _value list[int]: The RGB values.
    :var _mode int: The current index.
    :var _wheel PyQt5.QWidgets.QDial: The colour-controlling wheel.
    :var _colour PyQt5.QWidgets.QLabel: A label showing the colour code.
    :var _r PyQt5.QWidgets.QRadioButton: A control to switch to the red channel.
    :var _g PyQt5.QWidgets.QRadioButton: A control to switch to the green channel.
    :var _b PyQt5.QWidgets.QRadioButton: A control to switch to the blue channel.
    :var _layout PyQt5.QWidgets.QGridLayout: A manager for all the child widgets.
    """
    colourChanged = core.pyqtSignal(str)
    valuesChanged = core.pyqtSignal(sq.Colour)

    def __init__(self, starting: tuple[int, int, int]):
        super().__init__()
        self._value = list(starting)
        self._mode = 0
        self._wheel = widgets.QDial()
        self._wheel.setRange(0, 255)
        self._wheel.setNotchesVisible(True)
        self._colour = widgets.QLabel("")
        self._colour.setAlignment(enums.AlignCenter)
        self._colour.setAutoFillBackground(True)
        self._set_colour()
        self._r = widgets.QRadioButton("Red")
        self._g = widgets.QRadioButton("Green")
        self._b = widgets.QRadioButton("Blue")
        self._r.setChecked(True)
        self._r.clicked.connect(self._button(0))
        self._g.clicked.connect(self._button(1))
        self._b.clicked.connect(self._button(2))
        self._layout = widgets.QGridLayout()
        self.setLayout(self._layout)
        self._layout.addWidget(self._wheel, 0, 0)
        self._layout.addWidget(self._colour, 1, 0)
        self._layout.addWidget(self._r, 2, 1)
        self._layout.addWidget(self._g, 2, 2)
        self._layout.addWidget(self._b, 2, 3)
        self._wheel.valueChanged.connect(self._wheel_spun)

    def _button(self, i: int) -> typing.Callable[[bool], None]:
        def _inner(state: bool):
            if state:
                self._mode = i
                self._wheel.setValue(0)

        return _inner

    def _wheel_spun(self, value: int):
        self._value[self._mode] = value
        self._set_colour()
        self.colourChanged.emit(self.value())
        self.valuesChanged.emit(sq.Colour(*self._value))

    def _set_colour(self):
        colour = self._colour.palette()
        colour.setColor(colours.QPalette.Window, colours.QColor(*self._value))
        self.setPalette(colour)
        self._colour.setText(self.value())

    def value(self) -> str:
        """
        Find the hex code of the current colour.

        :return: A string hex code representing the current colour
        """
        return f"#{self._value[0]:02x}{self._value[1]:02x}{self._value[2]:02x}"


class FileDialog(widgets.QDialog):
    """
    Class to represent a small popup window to choose a file.

    :cvar BASE str: The root directory.
    :cvar open PyQt5.QtCore.pyqtSignal: The signal to emit when opening a file.
    :cvar save PyQt5.QtCore.pyqtSignal: The signal to emit when saving a file.

    :var _filepath str: The current filename.
    :var _layout PyQt5.QWidgets.QVBoxLayout: The layout to use for the widget.
    :var _file_model PyQt5.QWidgets.QFileSystemModel: The updating file model to view.
    :var _navigator PyQt5.QWidgets.QTreeView: The viewer of the file model.
    """
    BASE = r"C:\Users\fmz84311\OneDrive - Diamond Light Source Ltd\Documents\Automator\modular_qt\scripts"

    open = core.pyqtSignal(str)
    save = core.pyqtSignal(str)

    def __init__(self, parent: widgets.QWidget, *filters: str, open_="open", save="save", date_important=True):
        super().__init__(parent)
        btns = widgets.QDialogButtonBox(widgets.QDialogButtonBox.Save | widgets.QDialogButtonBox.Open)
        open_btn = btns.button(widgets.QDialogButtonBox.Open)
        open_btn.clicked.connect(self._handle_file(self.open))
        save_btn = btns.button(widgets.QDialogButtonBox.Save)
        save_btn.clicked.connect(self._handle_file(self.save))
        open_btn.setText(open_)
        save_btn.setText(save)
        self._filepath = ""
        self._layout = widgets.QVBoxLayout()
        self.setLayout(self._layout)
        self._file_model = widgets.QFileSystemModel()
        self._file_model.setReadOnly(False)
        self._file_model.setNameFilters(filters)
        self._file_model.setNameFilterDisables(False)
        root = self._file_model.setRootPath(self.BASE)
        self._navigator = widgets.QTreeView()
        self._navigator.setModel(self._file_model)
        self._navigator.setRootIndex(root)
        self._navigator.clicked.connect(self._select_file)
        head = self._navigator.header()
        self._navigator.resizeColumnToContents(0)
        head.setSectionResizeMode(0, widgets.QHeaderView.ResizeToContents)
        head.setSectionHidden(1, True)
        head.setSectionHidden(2, True)
        head.setSectionHidden(3, not date_important)
        head.setSectionResizeMode(3, widgets.QHeaderView.Fixed)
        head.setStretchLastSection(False)
        head.resizeSection(0, 300)
        head.resizeSection(3, 200)
        self._navigator.setMinimumHeight(300)
        self._layout.addWidget(self._navigator)
        self._layout.addWidget(btns)

    def _select_file(self, i: core.QModelIndex):
        f_name = self._file_model.filePath(i)
        self._filepath = f_name

    def _handle_file(self, sig: core.pyqtBoundSignal) -> typing.Callable[[], None]:
        def _inner():
            if self._filepath != "":
                sig.emit(self._filepath)
                self.accept()

        return _inner


class FilePrompt(widgets.QWidget):
    """
    Class to have a front end representation of a file dialog widget.

    :var _directory FileDialog: The directory choosing widget.
    :var _file_path PyQt5.QWidgets.QLineEdit: The editor for filepaths.
    :var _chooser PyQt5.QWidgets.QPushButton: A button to display the directory chooser.
    """

    def __init__(self, *valid_extensions: str, date_important=True, open_="open", save="save", path=FileDialog.BASE):
        super().__init__()
        self._layout = widgets.QHBoxLayout()
        self._directory = FileDialog(self, *map(lambda s: f"*.{s}", valid_extensions), date_important=date_important,
                                     open_=open_, save=save)
        bslsh = "\\"
        self._file_path = widgets.QLineEdit(f"{path.replace(bslsh, '/')}/")
        self._chooser = widgets.QPushButton("Choose File")
        self._chooser.clicked.connect(lambda: self._directory.exec())
        self._layout.addWidget(self._file_path)
        self._layout.addWidget(self._chooser)
        self.setLayout(self._layout)

    def dialog(self) -> FileDialog:
        """
        Public access to the dialog.

        :return: The directory choosing widget.
        """
        return self._directory

    def file_path(self) -> widgets.QLineEdit:
        """
        Public access to the entry point.

        :return: The entry point of the dialog.
        """
        return self._file_path


class PrefixedValidator(colours.QValidator):
    """
    Special validator for prefixed LineEdits.

    Allows for keeping a portion of the line edit as a "prefix" such that it is impossible to remove.

    :var _prefix str: The prefix to keep constant.
    """

    @property
    def prefix(self) -> str:
        """
        Public access to the prefix.

        :return: The "prefix" portion of the line edit to keep constant.
        """
        return self._prefix

    def __init__(self, prefix: str):
        self._prefix = prefix
        super().__init__()

    def validate(self, a0: str, a1: int) -> tuple[int, str, int]:
        """
        Custom validation function for prefixed LineEdits.

        :param a0: The string to validate.
        :param a1: The position of validation.
        :return: Whether the string is valid or not (contains the prefix)
        """
        if self._prefix not in a0:
            return colours.QValidator.Invalid, a0, a1
        return colours.QValidator.Acceptable, a0, a1

    def fixup(self, a0: str) -> str:
        """
        Custom fixing function for prefixed LineEdits.

        :param a0: The string to fix.
        """
        return f"{self._prefix} {a0}"
