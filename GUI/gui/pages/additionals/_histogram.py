import typing

from PyQt5.QtCore import Qt as enums

from ..pipeline import SurveyImage
from ... import utils
from ..._base import CanvasPage, SettingsPage, images, widgets, gui
from .... import validation


class Histogram(CanvasPage, SettingsPage):
    settingChanged = SettingsPage.settingChanged

    def __init__(self, size: int, prev: SurveyImage, outline: images.Colour,
                 failure_action: typing.Callable[[Exception], None]):
        CanvasPage.__init__(self, size, False, self._drag)
        SettingsPage.__init__(self, utils.SettingsDepth.REGULAR)
        self._colour_option.hide()
        self._minima = widgets.QLabel("Minima: 30")
        self._maxima = widgets.QLabel("Maxima: 60")
        self._min_val, self._max_val = 30, 60
        self._num_groups = utils.LabelledWidget("Colour Groups", utils.Spinbox(17, 1, validation.examples.colours),
                                                utils.LabelOrder.SUFFIX)
        self._num_groups.focus.dataPassed.connect(lambda v: self.settingChanged.emit("num_groups", v))
        self._num_groups.focus.dataPassed.connect(lambda _: self._hist())
        self._num_groups.focus.dataFailed.connect(failure_action)
        self._regular.addWidget(self._minima)
        self._regular.addWidget(self._maxima)
        self._regular.addWidget(self._num_groups)
        self._src = prev
        self._colour = outline

        self._canvas.mousePressed.connect(self._drag)
        self.setLayout(self._layout)

    def start(self):
        SettingsPage.start(self)
        CanvasPage.start(self)

    def stop(self):
        SettingsPage.stop(self)
        CanvasPage.stop(self)

    def compile(self) -> str:
        return "scan"

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
        self._canvas.histogram(self._original_image.demote("r"), int(self._num_groups.focus.get_data()), self._colour)
        with self._canvas as img:
            self._modified_image = img.copy()
        self._min_line()
        self._max_line()

    def update_min(self, line: int):
        self._min_val = line
        if self._modified_image is None:
            return
        self._canvas.draw(self._modified_image.copy())
        self._min_line(False)
        self._max_line(False)

    def update_max(self, line: int):
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
            img.drawing.line((x_pos, 0), (x_pos, self._canvas.image_size[1] - 1), images.RGB(255, 0, 0))
        self._minima.setText(f"Minima: {self._min_val}")

    def _max_line(self, emit=True):
        self._max_val = min(255, max(self._max_val, self._min_val + 1))
        if emit:
            self.settingChanged.emit("maxima", self._max_val)
        x_pos = int((self._max_val / 255) * (self._canvas.image_size[0] - 1))
        with self._canvas as img:
            img.drawing.line((x_pos, 0), (x_pos, self._canvas.image_size[1] - 1), images.RGB(0, 0, 255))
        self._maxima.setText(f"Maxima: {self._max_val}")

    def _drag(self, event: gui.QMouseEvent):
        self._canvas.draw(self._modified_image.copy())
        x_pos = event.pos().x()
        colour = int((x_pos / self._canvas.image_size[0]) * 255)
        btns = int(event.buttons())
        if btns == enums.LeftButton:
            self._min_val = colour
        elif btns == enums.RightButton:
            self._max_val = colour
        elif btns == enums.MiddleButton:
            o_l, o_h = self._min_val, self._max_val
            line_gap = self._max_val - self._min_val
            self._min_val = colour - line_gap // 2
            self._max_val = colour + line_gap // 2
            if self._min_val < 0 or self._max_val > 255:
                self._min_val = o_l
                self._max_val = o_h
        for _ in range(2):
            # do twice as drawing is little overhead, but the emitting twice will successfully update threshold values
            self._min_line()
            self._max_line()

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
