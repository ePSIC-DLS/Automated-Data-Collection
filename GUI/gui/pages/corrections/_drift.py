import typing
from typing import Tuple as _tuple

import numpy as np
import scipy.ndimage as images
from scipy.signal import convolve

from ... import utils
from ..._base import ShortCorrectionPage, core, widgets, microscope
from .... import validation


class TranslateRegion(ShortCorrectionPage):
    drift = core.pyqtSignal(int, int)

    def __init__(self, failure_action: typing.Callable[[Exception], None], mic: microscope.Microscope,
                 scanner: microscope.Scanner, survey_size: _tuple[int, int]):
        super().__init__(mic)
        self._scanner = scanner
        self._area = microscope.FullScan(survey_size)
        self._reference: typing.Optional[np.ndarray] = None

        self._drift_scans = utils.Spinbox(1, 1, validation.examples.drift)
        self._amount = utils.Counter(self._drift_scans, "Number of scans since last routine", start=0)
        self._amount.limitChanged.connect(lambda v: self.settingChanged.emit("drift_scans", v))
        self._amount.limitFailure.connect(failure_action)
        # self._amount.needsReset.connect(self.conditionHit.emit)
        self._windowing = utils.LabelledWidget("Windowing types", utils.Flag(utils.Windowing, utils.Windowing(0)),
                                               utils.LabelOrder.SUFFIX)
        self._windowing.focus.dataPassed.connect(lambda v: self.settingChanged.emit("windowing", v))
        self._windowing.focus.dataFailed.connect(failure_action)
        self._order = utils.LabelledWidget("Windowing Order",
                                           utils.OrderedGroup(widgets.QLabel("Hanning"), widgets.QLabel("Sobel"),
                                                              widgets.QLabel("Median")),
                                           utils.LabelOrder.SUFFIX)
        self._order.focus.orderChanged.connect(lambda o, n:
                                               self.settingChanged.emit(
                                                   "window_order",
                                                   tuple(lab.text() for lab in self._order.focus.get_members())
                                               ))

        self._window_order = self._order

        self._regular.addWidget(self._amount)
        self._regular.addWidget(self._windowing)
        self._regular.addWidget(self._order)
        self.setLayout(self._layout)

    def scans_increased(self):
        self._amount.increase()

    def set_reference(self, new: np.ndarray):
        self._reference = new
        self._amount.set_current(0)

    def query(self):
        self._amount.check()

    def run(self):
        self.runStart.emit()
        if microscope.ONLINE:
            with self._scanner.switch_scan_area(self._area):
                new = self._scanner.scan().image()
                windowed_reference = self._window(self._reference)
                windowed_scan = self._window(new)
                drift = convolve(windowed_reference, windowed_scan[::-1, ::-1], mode="same")
                r, c = self._reference.shape
                drift_vec = np.array(np.unravel_index(np.argmax(drift), drift.shape)) - np.array((r // 2, c // 2))
                self.drift.emit(drift_vec[1], drift_vec[0])
        self.runEnd.emit()

    def _window(self, image: np.ndarray) -> np.ndarray:
        def _hanning(img: np.ndarray) -> np.ndarray:
            m, n = img.shape
            return img * np.outer(np.hanning(m), np.hanning(n))

        def _sobel(img: np.ndarray) -> np.ndarray:
            sx = images.sobel(img, axis=0, mode="constant")
            sy = images.sobel(img, axis=1, mode="constant")
            return np.hypot(sx, sy)

        def _median(img: np.ndarray) -> np.ndarray:
            return images.median_filter(img, size=3)

        window_map = {}
        window_value = self._windowing.focus.get_data()
        if window_value & utils.Windowing.HANNING:
            window_map["Hanning"] = _hanning
        if window_value & utils.Windowing.SOBEL:
            window_map["Sobel"] = _sobel
        if window_value & utils.Windowing.MEDIAN:
            window_map["Median"] = _median

        for window_type in map(lambda t: t.text(), self._order.focus.get_members()):
            image = window_map.get(window_type, lambda i: i)(image)
        return image - image.mean()

    def all_settings(self) -> typing.Iterator[str]:
        yield from ("drift_scans", "windowing", "window_order")

    def help(self) -> str:
        s = f"""This correction is meant to combat the movement of internal positions of the microscope.
        This will help keep the Field Of View (FOV) constant.

        Settings
        --------
        Scan Amount
            {validation.examples.drift}

            The number of scans to perform prior to this correction being run;
            this will cause the counter to reset when reached.
        Windowing types:
            {self._windowing.focus.validation_pipe()}

            Which windowing techniques to use:
                HANNING windowing implies using a 2D bell curve to smoothly transition on rising and falling edges;
                meaning the 0 - 1 transitions and the 1 - 0 transitions are smoother.
                SOBEL windowing implies using a Sobel derivative in the x-axis and then in the y-axis;
                each component is squared, summed and square rooted.
                MEDIAN windowing implies using a Median filter with a kernel size of 3.
        Windowing Order:
            No validation

            The order of the windowing types.
        """
        return s
