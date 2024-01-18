"""
Module to represent the histogram view of the scanned image.
"""
from PyQt5.QtCore import Qt as enums

from . import base, extra_widgets
from ._preprocess import PreprocessPage
from ._scan import ScanPage
from .base import widgets, events, utils


class Colours(utils.AdvancedSettingWindow):
    """
    Subclass to change the colours of the histogram lines.

    :var _min ColourWheel: The minima line colour control.
    :var _max ColourWheel: The maxima line colour control.
    """

    def __init__(self):
        super().__init__()
        self._min = extra_widgets.ColourWheel((255, 0, 0))
        self._max = extra_widgets.ColourWheel((0, 0, 255))
        self._layout.addWidget(widgets.QLabel("Minima"), 0, 0)
        self._layout.addWidget(self._min, 0, 1)
        self._layout.addWidget(widgets.QLabel("(The colour of the minima line)"), 0, 2)
        self._layout.addWidget(widgets.QLabel("Maxima"), 1, 0)
        self._layout.addWidget(self._max, 1, 1)
        self._layout.addWidget(widgets.QLabel("(The colour of the maxima line)"), 1, 2)

    def widgets(self) -> dict[str, widgets.QWidget]:
        return dict(minima=self._min, maxima=self._max)


class HistPage(base.DrawingPage, base.SettingsPage):
    """
    Concrete subclass to represent the histogram of the scanned image.

    :var _scanner ScanPage: The original image page.
    :var _processor PreprocessPage: The preprocessing page.
    :var _min PyQt5.QWidgets.QLineEdit: Readonly entry to represent the minima line colour.
    :var _max PyQt5.QWidgets.QLineEdit: Readonly entry to represent the maxima line colour.
    :var _minima_colour str: The colour of the minima line.
    :var _maxima_colour str: The colour of the maxima line.
    """

    def __init__(self, size: int, prev: ScanPage, ahead: PreprocessPage):
        super().__init__(size)
        super(base.DrawingPage, self).__init__(utils.Settings.REGULAR | utils.Settings.ADVANCED, Colours)
        self._colour.hide()
        self._scanner = prev
        self._processor = ahead
        self._min = widgets.QLineEdit(f"Minima: {ahead.min}")
        self._max = widgets.QLineEdit(f"Minima: {ahead.max}")
        self._min.setReadOnly(True)
        self._max.setReadOnly(True)
        self._reg_col.addWidget(self._min)
        self._reg_col.addWidget(self._max)
        ahead.trace(self._min, self._max)
        self.setMouseTracking(False)
        self._minima_colour = self.get_setting("minima")
        self._maxima_colour = self.get_setting("maxima")
        self.get_control("minima").colourChanged.connect(self._new_colour)
        self.get_control("maxima").colourChanged.connect(self._new_colour)

    def compile(self) -> str:
        return "scan"

    def _new_colour(self):
        for line in self._canvas.filter_lines(utils.Capture.ANY, color=self._minima_colour):
            line.remove()
            self._canvas.remove(line)
        for line in self._canvas.filter_lines(utils.Capture.ANY, color=self._maxima_colour):
            line.remove()
            self._canvas.remove(line)
        self._minima_colour = self.get_setting("minima")
        self._maxima_colour = self.get_setting("maxima")
        if self._curr is None:
            return
        self._canvas.line(int(self._min.text()[8:]), utils.Orient.VERTICAL, self._minima_colour)
        self._canvas.line(int(self._max.text()[8:]), utils.Orient.VERTICAL, self._maxima_colour)

    @base.DrawingPage.lock
    def run(self, btn_state: bool):
        """
        Will run the scanner then create a histogram of the image.

        Will then draw lines at the minimum and maximum threshold values.
        :param btn_state: The state of the button that caused this callback.
        """
        self.triggered.emit(self.run)
        self._scanner.run(btn_state)
        self._curr = self._scanner.get_mutated()
        self._original = self._scanner.get_original()
        self._canvas.histogram(self._curr.get_raw())
        self._canvas.line(int(self._min.text()[8:]), utils.Orient.VERTICAL, self.get_setting("minima"))
        self._canvas.line(int(self._max.text()[8:]), utils.Orient.VERTICAL, self.get_setting("maxima"))

    @base.DrawingPage.lock
    def mouseMoveEvent(self, a0: events.QMouseEvent):
        if self._curr is None:
            return

        def _find_other(other_colour: str, direction: int) -> tuple[int, float]:
            line = next(self._canvas.filter_lines(utils.Capture.ANY, color=other_colour))
            other = self._canvas.raw(line) + direction
            ratio = 255 / self._canvas.figsize
            return other, ratio

        def _remove_self(self_colour: str):
            for line in self._canvas.filter_lines(utils.Capture.ANY, color=self_colour):
                line.remove()
                self._canvas.remove(line)

        minima_colour = self.get_setting("minima")
        maxima_colour = self.get_setting("maxima")

        button = a0.buttons()
        x, y = a0.pos().x(), a0.pos().y()
        if button & enums.LeftButton:
            max_x, x_ratio = _find_other(maxima_colour, -1)
            constricted = min(max_x, max(0, int(x_ratio * x)))
            self._react_min(constricted)
            _remove_self(minima_colour)
            self._canvas.line(constricted, utils.Orient.VERTICAL, minima_colour)
        elif button & enums.RightButton:
            min_x, x_ratio = _find_other(minima_colour, 1)
            constricted = max(min_x, min(255, int(x_ratio * x)))
            self._react_max(constricted)
            _remove_self(maxima_colour)
            self._canvas.line(constricted, utils.Orient.VERTICAL, maxima_colour)

    def _react_min(self, new: int):
        self._processor.min = new

    def _react_max(self, new: int):
        self._processor.max = new
