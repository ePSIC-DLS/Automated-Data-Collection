import functools
import operator
import time
import typing
from typing import List as _list, Tuple as _tuple, Optional as _None

import numpy as np
from PyQt5 import QtCore as core, QtWidgets as widgets

from ._widgets import *
from ..image_processing import Axis, Grid, imgs, Settings, sweep, ValidityMeasure
from ..corrections import *

enums = core.Qt

__all__ = ["Sweeper", "Setup", "Manual", "Tester"]


class Sweeper(widgets.QWidget):
    current_updated = core.pyqtSignal(Grid)
    _pass = core.pyqtSignal(imgs.RGBImage)
    _complete = core.pyqtSignal()
    _error = core.pyqtSignal(str, str)
    start = core.pyqtSignal()
    MANAGER = core.QThreadPool()

    @property
    def sweeping(self) -> bool:
        return self._sweeping

    def __init__(self, img_size: int):
        super().__init__()
        layout = widgets.QVBoxLayout()
        self._size = img_size
        self._settings: _list[Settings] = []
        self._sweeping = False

        self._cnv = History((img_size, img_size))
        self._cnv.new_index.connect(self._update)
        self._progress = widgets.QProgressBar()
        self._progress.setFormat("Image: %v (%p%)")
        self._progress.setValue(0)
        self._progress.setRange(0, 0)
        self._image = SettingsView()
        self._view = Viewer()
        self._view.jump_requested.connect(self._on_jump)

        self._pass.connect(self._on_pass)
        self._complete.connect(self._on_complete)
        self._error.connect(self._on_error)

        layout.addWidget(self._image)
        layout.addWidget(self._cnv)
        layout.addWidget(self._progress)

        self.setLayout(layout)

    def _on_jump(self, to: int):
        self._cnv.jump(to)
        settings = self._settings[to]
        self.current_updated.emit(
            Grid(self._size, settings["angle"], settings["pitch"], settings["offset"], ValidityMeasure.LT)
        )

    def _on_error(self, message: str, err_type: typing.Literal["critical", "error", "information"]):
        if err_type == "critical":
            func = widgets.QMessageBox.critical
        elif err_type == "error":
            func = widgets.QMessageBox.warning
        else:
            func = widgets.QMessageBox.information
        func(self, "Invalid sweep", message, widgets.QMessageBox.Ok, widgets.QMessageBox.Ok)

    def _on_complete(self):
        self._cnv.end_batch()
        self._sweeping = False
        self._progress.setRange(0, 0)
        try:
            self._view.display(*self._settings)
        except ValueError as err:
            self._error.emit(str(err), "information")
        else:
            if self._view.isVisible():
                self._view.raise_()
            else:
                self._view.show()

    def _on_pass(self, img: imgs.RGBImage):
        self._progress.setValue(self._progress.value() + 1)
        self._cnv.draw(img)
        self._update(self._cnv.current_index())

    def _update(self, i: int):
        try:
            self._image.populate(self._settings[i])
        except IndexError:
            print(f"Error, detecting {i}>={len(self._settings)}")

    def sweep(self, file: str, x_size: _tuple[int, ...], y_size: _tuple[int, ...], x_angles: _tuple[int, ...],
              y_angles: _tuple[int, ...], x_offsets: _tuple[int, ...], y_offsets: _tuple[int, ...],
              measure: ValidityMeasure):
        self.start.emit()
        master = imgs.GreyImage.from_file(file)

        def _inner():
            time.sleep(0.2)
            try:
                for settings in sweep(master, x_size, y_size, x_angles, y_angles, x_offsets,
                                      y_offsets, full=False, using=measure):
                    square = Grid(self._size, settings["angle"], settings["pitch"], settings["offset"], measure)
                    child = imgs.RGBImage.from_file(file, do_static=True)
                    child.data()[square.mask()] = child.make_blue()
                    self._settings.append(settings)
                    self._pass.emit(child)
                self._complete.emit()
            except Exception as err:
                self._error.emit(str(err), "error")

        self._settings.clear()
        self._sweeping = True
        self._cnv.start_batch()
        length = functools.reduce(operator.mul, map(len, (x_size, y_size, x_angles, y_angles, x_offsets, y_offsets)))
        try:
            self._progress.setMaximum(length)
        except OverflowError:
            self._error.emit("Too many images to sweep over", "critical")
        self._progress.setValue(0)

        self.MANAGER.start(_inner)


class Viewer(widgets.QWidget):
    MAX = 20
    jump_requested = core.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        layout = widgets.QGridLayout()
        self._none = widgets.QRadioButton("&Average")
        self._none.setChecked(True)
        self._none.clicked.connect(self._update)
        self._x = widgets.QRadioButton("&X")
        self._x.clicked.connect(self._update)
        self._y = widgets.QRadioButton("&Y")
        self._y.clicked.connect(self._update)
        self._clip = widgets.QSpinBox()
        self._clip.setRange(0, self.MAX)
        self._clip.setValue(10)
        self._clip.valueChanged.connect(lambda _: self._update())
        self._leaderboard = tuple(SettingsView() for _ in range(self.MAX))
        self._cache: _tuple[Settings, ...] = ()
        for i, view in enumerate(self._leaderboard):
            layout.addWidget(view, i // 2, i % 2)
            view.clicked.connect(self.jump_requested)
        layout.addWidget(self._clip, self.MAX, 0)
        layout.addWidget(self._none, self.MAX, 1)
        layout.addWidget(self._x, self.MAX + 1, 0)
        layout.addWidget(self._y, self.MAX + 1, 1)
        self.setLayout(layout)

    def wipe(self):
        for view in self._leaderboard:
            view.clear()

    def _update(self):
        if not self._cache:
            return
        self.wipe()
        if self._none.isChecked():
            def _combine(validity: _tuple[float, float]) -> float:
                return np.mean(validity)
        elif self._x.isChecked():
            def _combine(validity: _tuple[float, float]) -> float:
                return validity[0]
        else:
            def _combine(validity: _tuple[float, float]) -> float:
                return validity[1]
        indices = np.argsort([_combine(settings["validity"]) for settings in self._cache])
        lowest = -len(self._cache)
        for i, s_i in enumerate(range(-1, -(self._clip.value() + 1), -1)):
            if s_i < lowest:
                return
            viewer = self._leaderboard[i]
            idx = indices[s_i]
            viewer.populate(self._cache[idx])
            viewer.set_data_index(idx)

    def display(self, *settings: Settings):
        if not settings:
            raise ValueError("No settings to display")
        self._cache = settings
        self._update()


class Setup(widgets.QWidget):
    PITCH = (20, 200)
    OFFSET = (-50, 50)
    ANGLE = (-80, 80)

    def __init__(self, controlling: Sweeper):

        def _passes() -> int:
            return functools.reduce(operator.mul, map(lambda x: len(x.value()), params))

        widgets.QWidget.__init__(self)
        layout = widgets.QGridLayout()
        self._mask = controlling

        self._x_pitch = Range(*self.PITCH)
        self._y_pitch = Range(*self.PITCH)
        self._x_offset = Range(*self.OFFSET)
        self._y_offset = Range(*self.OFFSET)
        self._x_angle = Range(*self.ANGLE)
        self._y_angle = Range(*self.ANGLE)
        self._method = widgets.QComboBox()
        self._method.addItems(map(lambda x: x.name, ValidityMeasure))
        self._method.setCurrentText("ONE_MINUS_LE")
        params = (self._x_pitch, self._y_pitch, self._x_offset, self._y_offset, self._x_angle, self._y_angle)
        self._file = widgets.QLineEdit()
        self._run = widgets.QPushButton("Run Sweep")
        self._num = widgets.QLabel(f"Num passes: {_passes():.3E}")

        for param in params:
            param.edited.connect(lambda: self._num.setText(f"Num Passes: {_passes():.3E}"))
        self._run.clicked.connect(self._sweep)
        for i, (name, rng) in enumerate(zip(
                ("horizontal pitch size", "vertical pitch size", "horizontal offset", "vertical offset",
                 "angle from x-axis", "angle from y-axis", "filepath", "validity measure"),
                (*params, self._file, self._method)
        )):
            layout.addWidget(widgets.QLabel(name), i, 0)
            layout.addWidget(rng, i, 1)
        last = len(params) + 2
        layout.addWidget(self._run, last, 0)
        layout.addWidget(self._num, last, 1)
        self.setLayout(layout)

    def set_pitch(self, pitch: int, axis: Axis):
        self._set(self._x_pitch, self._y_pitch, pitch, axis)

    def set_offset(self, offset: int, axis: Axis):
        self._set(self._x_offset, self._y_offset, offset, axis)

    def set_angle(self, angle: int, axis: Axis):
        self._set(self._x_angle, self._y_angle, angle, axis)

    @staticmethod
    def _set(x_wid: Range, y_wid: Range, value: int, axis: Axis):
        if axis == Axis.X:
            wid = x_wid
        else:
            wid = y_wid
        wid.singleton(value)

    def _sweep(self):
        if self._mask.sweeping:
            widgets.QMessageBox.information(self, "Already sweeping", "Cannot run concurrent sweeps",
                                            widgets.QMessageBox.Ok, widgets.QMessageBox.Ok)
            return

        self._mask.sweep(
            self._file.text(),
            self._x_pitch.value(),
            self._y_pitch.value(),
            self._x_angle.value(),
            self._y_angle.value(),
            self._x_offset.value(),
            self._y_offset.value(),
            ValidityMeasure[self._method.currentText()]
        )


class Manual(widgets.QWidget):

    def __init__(self, img_size: int, space: Setup):
        super().__init__()
        layout = widgets.QGridLayout()
        self._size = img_size
        self._cnv = Canvas((img_size, img_size))
        self._info = SettingsView()
        self._file = widgets.QLineEdit()
        self._pitch = (widgets.QSlider(enums.Horizontal), widgets.QSlider(enums.Horizontal))
        self._offset = (widgets.QSlider(enums.Horizontal), widgets.QSlider(enums.Horizontal))
        self._angle = (widgets.QDial(), widgets.QDial())
        for i, wid in enumerate(self._pitch):
            wid.setRange(*Setup.PITCH)
            wid.setValue(wid.minimum())
            wid.valueChanged.connect(functools.partial(self._update, i, space.set_pitch, "pitch"))
            wid.setTickPosition(widgets.QSlider.TicksBelow)
            wid.setTickInterval(10)
        for i, wid in enumerate(self._offset):
            wid.setRange(*Setup.OFFSET)
            wid.setValue(wid.minimum())
            wid.valueChanged.connect(functools.partial(self._update, i, space.set_offset, "offset"))
            wid.setTickPosition(widgets.QSlider.TicksBelow)
            wid.setTickInterval(10)
        for i, wid in enumerate(self._angle):
            wid.setRange(*Setup.ANGLE)
            wid.setValue(wid.minimum())
            wid.valueChanged.connect(functools.partial(self._update, i, space.set_angle, "angle"))
            wid.setNotchesVisible(True)
        file_changed = widgets.QPushButton("File Changed")
        file_changed.clicked.connect(self._file_changed)
        layout.addWidget(self._info, 0, 0)
        layout.addWidget(self._cnv, 1, 0, 2, 1)
        layout.addWidget(widgets.QLabel("Filepath"), 3, 0)
        layout.addWidget(self._file, 3, 1, 1, 2)
        layout.addWidget(file_changed, 3, 3)
        layout.addWidget(widgets.QLabel("Pitch control"), 0, 1)
        layout.addWidget(self._pitch[0], 1, 1)
        layout.addWidget(self._pitch[1], 2, 1)
        layout.addWidget(widgets.QLabel("Offset control"), 0, 2)
        layout.addWidget(self._offset[0], 1, 2)
        layout.addWidget(self._offset[1], 2, 2)
        layout.addWidget(widgets.QLabel("Angle control"), 0, 3)
        layout.addWidget(self._angle[0], 1, 3)
        layout.addWidget(self._angle[1], 2, 3)
        self.setLayout(layout)

    def _get(self) -> Settings:
        return {"pitch": (self._pitch[0].value(), self._pitch[1].value()),
                "angle": (self._angle[0].value(), self._angle[1].value()),
                "offset": (self._offset[0].value(), self._offset[1].value()),
                "validity": (-1, -1)}

    def _file_changed(self):
        self._draw(self._get())

    def _update(self, idx: int, setter: typing.Callable[[int, Axis], None],
                key: typing.Literal["pitch", "angle", "offset"], value: int):
        axis = Axis.X if idx == 0 else Axis.Y
        setter(value, axis)
        settings = self._get()
        control = list(settings[key])
        control[idx] = value
        settings[key] = tuple(control)
        self._draw(settings)

    def _draw(self, settings: Settings):
        self._info.populate(settings)
        square = Grid(self._size, settings["angle"], settings["pitch"], settings["offset"], ValidityMeasure.LT)
        try:
            child = imgs.RGBImage.from_file(self._file.text(), do_static=True)
        except FileNotFoundError as e:
            widgets.QMessageBox.warning(self, "Invalid file", str(e), widgets.QMessageBox.Ok, widgets.QMessageBox.Ok)
            return
        child.data()[square.mask()] = child.make_blue()
        self._cnv.draw(child)


class Tester(widgets.QWidget):

    @property
    def _result_text(self) -> str:
        size = "passes" if self._validity[0] else "fails"
        angle = "passes" if self._validity[1] else "fails"
        return f"Size {self._results[0]} {size}, Angle {self._results[1]} {angle}"

    def __init__(self):
        super().__init__()
        layout = widgets.QVBoxLayout()
        pitch_exp = widgets.QSpinBox()
        pitch_exp.setRange(*Setup.PITCH)
        self._pitch = Corrector(Size, expected=pitch_exp)
        self._angle = Corrector(Skew)
        self._validity = [False, False]
        self._results = [(-1, -1), -1]
        self._result = widgets.QLabel(self._result_text)
        layout.addWidget(self._pitch)
        layout.addWidget(self._angle)
        layout.addWidget(self._result)
        self._pitch.instantiated.connect(self._apply)
        self._angle.instantiated.connect(self._apply)
        self._grid: _None[Grid] = None
        self.setLayout(layout)

    def add_grid(self, grid: Grid):
        self._grid = grid

    def _apply(self, correction: Correction):
        if self._grid is None:
            widgets.QMessageBox.warning(self, "No grid", "Must perform sweep prior to testing corrections",
                                        widgets.QMessageBox.Ok, widgets.QMessageBox.Ok)
            return
        if isinstance(correction, Size):
            prop = self._grid.length()
            idx = 0
        else:
            prop = round(self._grid.angle())
            idx = 1
        self._results[idx] = prop
        self._validity[idx] = correction.valid(prop)
        self._result.setText(self._result_text)
        if ONLINE:
            correction.correct(prop)
