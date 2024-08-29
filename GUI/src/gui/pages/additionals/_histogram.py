import typing
from typing import Dict as _dict, Tuple as _tuple

import numpy as np
from PyQt5.QtCore import Qt as enums

from ..pipeline import SurveyImage
from ... import utils
from ..._base import CanvasPage, gui, SettingsPage, widgets
from .... import load_settings, validation

default_settings = load_settings("assets/config.json",
                                 minima=validation.examples.hist_colours,
                                 maxima=validation.examples.hist_colours,
                                 num_groups=validation.examples.colours
                                 )


class Histogram(CanvasPage, SettingsPage):
    """
    Concrete page representing a colour count of the survey image.

    There are two controls on the histogram, represented as two vertical lines. They are both draggable, with the
    leftmost one being the minima value, and the rightmost one being the maximum value.

    Attributes
    ----------
    _minima: QLabel
        Widget to display the minima value.
    _maxima: QLabel
        Widget to display the maxima value.
    _min_val: int
        The minima value.
    _max_val: int
        The maxima value.
    _num_groups: LabelledWidget[Spinbox]
        The widget controlling the number of histogram bins.
    _src: SurveyImage
        The creator of the survey image. Note that the histogram triggers this page when it is triggered.
    _colour: int_
        The outline colour of the histogram bins.
    _greys: dict[int, tuple[int, int]]
        The mapping of rightmost edge to start and end intensities.
    """
    settingChanged = SettingsPage.settingChanged

    def __init__(self, size: int, prev: SurveyImage, outline: np.int_,
                 failure_action: typing.Callable[[Exception], None]):
        CanvasPage.__init__(self, size, movement_handler=self._drag)
        SettingsPage.__init__(self, utils.SettingsDepth.REGULAR)
        self._min_val, self._max_val = default_settings["minima"], default_settings["maxima"]
        self._minima = widgets.QLabel(f"Minima: {self._min_val}")
        self._maxima = widgets.QLabel(f"Maxima: {self._max_val}")
        self._num_groups = utils.LabelledWidget("Colour Groups", utils.Spinbox(default_settings["num_groups"], 1,
                                                                               validation.examples.colours),
                                                utils.LabelOrder.SUFFIX)
        self._num_groups.focus.dataPassed.connect(lambda v: self.settingChanged.emit("num_groups", v))
        self._num_groups.focus.dataPassed.connect(lambda _: self._hist())
        self._num_groups.focus.dataFailed.connect(failure_action)
        self._regular.addWidget(self._minima)
        self._regular.addWidget(self._maxima)
        self._regular.addWidget(self._num_groups)
        self._src = prev
        self._colour = outline
        self._greys: _dict[int, _tuple[int, int]] = {}

        self._canvas.mousePressed.connect(self._drag)
        self.setLayout(self._layout)

    def start(self):
        SettingsPage.start(self)
        CanvasPage.start(self)

    def stop(self):
        SettingsPage.stop(self)
        CanvasPage.stop(self)

    def compile(self) -> str:
        return ""

    def run(self):
        if self._state != utils.StoppableStatus.ACTIVE:
            return
        self._src.run()
        self.runStart.emit()
        self._hist()
        self.runEnd.emit()

    def _hist(self):
        if self._src.original is None:
            return
        self._original_image = self._src.original.copy()
        x_points, greys = self._canvas.histogram(self._original_image.demote(),
                                                 int(self._num_groups.focus.get_data()), self._colour)
        x_points[:-1] = x_points[1:]
        x_points[-1] = self._canvas.image_size[0]
        exit_ = False
        for i, limit in enumerate(x_points):
            if i == greys.shape[0] - 1:
                end = 255
                exit_ = True
            else:
                end = greys[i + 1]
            self._greys[limit] = (greys[i], end)
            if exit_:
                break
        with self._canvas as img:
            self._modified_image = img.copy()
        self._min_line()
        self._max_line()

    def update_min(self, line: int):
        """
        Publicly edit the minima line.

        Parameters
        ----------
        line: int
            The new minima value.
        """
        self._min_val = line
        if self._modified_image is None:
            return
        self._canvas.draw(self._modified_image.copy())
        self._min_line(False)
        self._max_line(False)

    def update_max(self, line: int):
        """
        Publicly edit the maxima line.

        Parameters
        ----------
        line: int
            The new maxima value.
        """
        self._max_val = line
        if self._modified_image is None:
            return
        self._canvas.draw(self._modified_image.copy())
        self._min_line(False)
        self._max_line(False)

    def _min_line(self, emit=True):
        self._min_val = min(self._max_val - 1, max(self._min_val, 0))
        if emit:
            self.settingChanged.emit("minima", self._min_val)
        x_pos = int((self._min_val / 255) * (self._canvas.image_size[0] - 1))
        with self._canvas as img:
            img.drawings.line((x_pos, 0), (x_pos, self._canvas.image_size[1] - 1), 0xFF0000)
        self._minima.setText(f"Minima: {self._min_val}")

    def _max_line(self, emit=True):
        self._max_val = min(255, max(self._max_val, self._min_val + 1))
        if emit:
            self.settingChanged.emit("maxima", self._max_val)
        x_pos = int((self._max_val / 255) * (self._canvas.image_size[0] - 1))
        with self._canvas as img:
            img.drawings.line((x_pos, 0), (x_pos, self._canvas.image_size[1] - 1), 0x0000FF)
        self._maxima.setText(f"Maxima: {self._max_val}")

    def _drag(self, event: gui.QMouseEvent):
        if self._modified_image is None:
            return
        self._canvas.draw(self._modified_image.copy())
        x_pos = event.pos().x()
        colour = int((x_pos / self._canvas.image_size[0]) * 255)
        btns = int(event.buttons())
        if btns == enums.LeftButton:
            self._min_val = self._min_val = min(self._max_val - 1, max(colour, 0))
        elif btns == enums.RightButton:
            self._max_val = min(255, max(colour, self._min_val + 1))
        elif btns == enums.MiddleButton:
            o_l, o_h = self._min_val, self._max_val
            line_gap = self._max_val - self._min_val
            self._min_val = colour - line_gap // 2
            self._max_val = colour + line_gap // 2
            if self._min_val < 0 or self._max_val > 255:
                self._min_val = o_l
                self._max_val = o_h
        else:
            self._tooltip(event)
        for _ in range(2):
            self._min_line()
            self._max_line()

    def _process_tooltip(self, x: int, y: int) -> typing.Iterator[str]:
        def _handle(colour: int) -> str:
            hexa = f"{colour:06x}"
            if self._display_type == utils.ColourDisplay.HEX:
                clr = hexa
            else:
                clr = str((int(hexa[0:2], 16), int(hexa[2:4], 16), int(hexa[4:6], 16)))
            return clr

        for lim in self._greys:
            if x <= lim:
                start, end = map(_handle, self._greys[lim])
                break
        else:
            raise RuntimeError("Can't get here")
        yield f"{start} -> {end}"

    def all_settings(self) -> typing.Iterator[str]:
        yield from ("num_groups",)

    def help(self) -> str:
        s = f"""This is a histogram view of the survey image - it represents the colour counts within the image.
        The minima line can be manipulated with a left click and drag;
        the maxima line can be manipulated with a right click and drag;
        both can be manipulated with a middle click and drag.

        Settings
        --------
        Colour Groups: 
            {validation.examples.colours}
            
            The number of groups for colours. The amount of colours in each group is 255 // v"""
        return s
