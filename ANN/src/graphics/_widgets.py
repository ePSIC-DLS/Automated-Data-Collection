import typing
from typing import Optional as _None, Set as _set, Tuple as _tuple, List as _list, Type as _type

import numpy as np
from PyQt5 import QtCore as core, QtGui as gui, QtWidgets as widgets

from ..image_processing import imgs, Settings
from ..corrections import Correction
from ..corrections.PyJEM.offline.TEM3 import Scan3

__all__ = ["Canvas", "Range", "History", "SettingsView", "Corrector"]


class Canvas(widgets.QWidget):

    @property
    def displaying(self) -> bool:
        return self._data is not None

    @property
    def image_size(self) -> _tuple[int, int]:
        """
        Public access to the expected size of the images.

        Returns
        -------
        tuple[int, int]
            The expected size of the images. This is also the size of the widget.
        """
        return self._size

    def __init__(self, size: _tuple[int, int]):
        self._pixels = gui.QPixmap(*size)
        self._size = size
        self._data: _None[np.ndarray] = None
        self._pmap: _None[np.ndarray] = None
        super().__init__()
        self.setFixedSize(*size)

    def paintEvent(self, a0: gui.QPaintEvent):
        """
        Paints the image onto the widget.

        Parameters
        ----------
        a0: gui.QPaintEvent
            The event that triggered this callback.
        """
        painter = gui.QPainter(self)
        painter.drawPixmap(self.rect(), self._pixels)

    def draw(self, image: imgs.RGBImage):
        self._data = image.norm().convert(np.uint32)
        self.update()

    def update(self):
        """
        Updates the widget's display. This is called internally whenever the image is changed.
        """
        if self._data is not None:
            h, w, *c = self._data.shape
            self._pmap = 255 << 24 | self._data
            # noinspection PyTypeChecker
            qt_image = gui.QImage(self._pmap, w, h, gui.QImage.Format_RGB32)
            self._pixels = gui.QPixmap.fromImage(qt_image)
        super().update()


class Range(widgets.QWidget):
    edited = core.pyqtSignal()

    # Steven.zeltmann@berkley.edu -> Microscope Graduates?

    @property
    def start(self) -> int:
        return self._start.value()

    @property
    def stop(self) -> int:
        return self._stop.value()

    @property
    def step(self) -> int:
        return self._step.value()

    def __init__(self, global_min: int, global_max: int):
        super().__init__()
        layout = widgets.QGridLayout()

        self._start = widgets.QSpinBox()
        self._start.setMinimum(global_min)
        self._start.valueChanged.connect(self._set_min)
        self._start.valueChanged.connect(lambda _: self.edited.emit())

        self._stop = widgets.QSpinBox()
        self._stop.setMaximum(global_max)
        self._stop.valueChanged.connect(self._set_max)
        self._stop.valueChanged.connect(lambda _: self.edited.emit())

        self._step = widgets.QSpinBox()
        self._step.setRange(1, global_max)
        self._step.valueChanged.connect(lambda _: self.edited.emit())

        self._exclusive = widgets.QListWidget()
        self._exclude = widgets.QSpinBox()
        self._exclude.setRange(global_min, global_max)
        self._pusher = widgets.QPushButton("Push")
        self._pusher.clicked.connect(self._push)
        self._exclusions: _set[int] = set()

        layout.addWidget(self._start, 0, 0)
        layout.addWidget(self._stop, 1, 0)
        layout.addWidget(self._step, 2, 0)
        layout.addWidget(self._exclusive, 0, 1, 2, 2)
        layout.addWidget(self._exclude, 2, 1)
        layout.addWidget(self._pusher, 2, 2)
        self.setLayout(layout)

        self._set_min(global_min)
        self._set_max(global_max)
        self._start.setValue(global_min)
        self._stop.setValue(global_max)

    def _set_min(self, value: int):
        self._stop.setMinimum(value)
        self._exclude.setMinimum(value)

    def _set_max(self, value: int):
        self._start.setMaximum(value)
        if value != 0:
            self._step.setMaximum(abs(value))
        self._exclude.setMaximum(value)

    def _push(self):
        if (i := self._exclude.value()) not in self._exclusions:
            self._exclusions.add(i)
            self._exclusive.addItem(str(i))
            self.edited.emit()

    def value(self) -> _tuple[int, ...]:
        return tuple(x for x in range(self.start, self.stop, self.step) if x not in self._exclusions)

    def singleton(self, value: int):
        self._start.setMaximum(value)
        self._start.setValue(value)
        self._stop.setValue(value + 1)
        self._step.setValue(1)


class History(widgets.QWidget):
    new_index = core.pyqtSignal(int)
    new_image = core.pyqtSignal(imgs.RGBImage)

    def __init__(self, size: _tuple[int, int]):
        super().__init__()
        self._batch = False
        layout = widgets.QHBoxLayout()
        self._cnv = Canvas(size)
        self._history = widgets.QSlider()
        self._history.setEnabled(False)
        self._history.setRange(-1, -1)
        self._history.setTickPosition(widgets.QSlider.TicksBelow)
        self._imgs: _list[imgs.RGBImage] = []
        self._history.valueChanged.connect(self._select)
        layout.addWidget(self._cnv)
        layout.addWidget(self._history)
        self.setLayout(layout)

    def current_image(self) -> imgs.RGBImage:
        return self._imgs[self._history.value()]

    def current_index(self) -> int:
        return self._history.value()

    def jump(self, to: int):
        self._history.setValue(to)

    def start_batch(self):
        self._batch = True
        self._history.setRange(-1, -1)
        self._imgs.clear()
        self._history.setEnabled(False)

    def end_batch(self):
        self._batch = False
        self._history.setEnabled(True)

    def _select(self, i: int):
        self._cnv.draw(drawing := self._imgs[i])
        self.new_index.emit(i)
        self.new_image.emit(drawing)

    def draw(self, image: imgs.RGBImage):
        self._imgs.append(image)
        self._cnv.draw(image)
        if self._history.maximum() == -1:
            self._history.setEnabled(not self._batch)
            self._history.setRange(0, 0)
            self._history.setValue(0)
        else:
            self._history.setMaximum(self._history.maximum() + 1)
            self._history.setValue(self._history.maximum())


class SettingsView(widgets.QWidget):
    clicked = core.pyqtSignal(int)

    def __init__(self, dis: Settings = None):
        super().__init__()
        self._data_index = -1
        layout = widgets.QGridLayout()
        if dis is None:
            headers = ("pitch", "angle", "offset", "validity")
        else:
            headers = dis.keys()
        self._r_headers = tuple(widgets.QLabel(header) for header in headers)
        self._c_headers = (widgets.QLabel("X"), widgets.QLabel("Y"))
        self._data = tuple((widgets.QLabel(""), widgets.QLabel("")) for _ in headers)
        for i, header in enumerate(self._r_headers, 1):
            layout.addWidget(header, 0, i)
        for i, header in enumerate(self._c_headers, 1):
            layout.addWidget(header, i, 0)
        for i, (x_cell, y_cell) in enumerate(self._data, 1):
            layout.addWidget(x_cell, 1, i)
            layout.addWidget(y_cell, 2, i)
        self.setLayout(layout)
        if dis is not None:
            self.populate(dis)

    def mousePressEvent(self, a0):
        if self._data_index == -1:
            widgets.QMessageBox.critical(self, "Invalid Data", "Widget has no data index set", widgets.QMessageBox.Ok,
                                         widgets.QMessageBox.Ok)
            return
        self.clicked.emit(self._data_index)

    def populate(self, dis: Settings):
        for (x_label, y_label), (x_elem, y_elem) in zip(self._data, dis.values()):
            def _conv(elem: float) -> str:
                return str(elem) if float(elem).is_integer() else f"{elem:.3}"

            x_label.setText(_conv(x_elem))
            y_label.setText(_conv(y_elem))

    def set_data_index(self, i: int):
        self._data_index = i

    def clear(self):
        self._data_index = -1
        for x_label, y_label in self._data:
            x_label.setText("")
            y_label.setText("")


class Corrector(widgets.QWidget):
    instantiated = core.pyqtSignal(Correction)

    def __init__(self, ctype: _type[Correction], **kwargs: typing.Union[widgets.QSpinBox, widgets.QDoubleSpinBox]):
        super().__init__()
        scanner = Scan3()
        layout = widgets.QGridLayout()
        kwargs["tolerance"] = widgets.QDoubleSpinBox()
        kwargs["tolerance"].setRange(0, 10.0)
        kwargs["tolerance"].setValue(0.0)
        layout.addWidget(widgets.QLabel(f"{ctype.__name__} Correction: "), 0, 0, 1, 2)
        for i, (k, v) in enumerate(kwargs.items(), 1):
            layout.addWidget(widgets.QLabel(f"{k}="), i, 0)
            layout.addWidget(v, i, 1)
        self._spawn = widgets.QPushButton("Create")
        self._spawn.clicked.connect(
            lambda: self.instantiated.emit(ctype(scanner, **{k_: v_.value() for k_, v_ in kwargs.items()}))
        )
        layout.addWidget(self._spawn, len(kwargs) + 1, 0, 1, 2)
        self.setLayout(layout)
