import typing
from typing import Optional as _None, Tuple as _tuple

import numpy as np
import scipy.ndimage as imgs
from scipy.signal import convolve

from ... import utils
from ..._base import core, microscope, ShortCorrectionPage, widgets
from .... import images, validation
from ..._errors import *


class TranslateRegion(ShortCorrectionPage):
    drift = core.pyqtSignal(int, int)
    SIZES = (256, 512, 1024, 2048, 4096, 8192, 16384)

    def __init__(self, failure_action: typing.Callable[[Exception], None], mic: microscope.Microscope,
                 scanner: microscope.Scanner, scan_func: typing.Callable[[microscope.ScanType, bool], images.GreyImage],
                 survey_size: _tuple[int, int]):
        super().__init__(mic)
        TranslateRegion.SIZES = tuple(s for s in TranslateRegion.SIZES if s > survey_size[0])
        self._scanner = scanner
        self._scan = scan_func
        self._size = survey_size[0]

        self._ref: _None[images.GreyImage] = None
        self._region: _None[utils.ScanRegion] = None

        self._limit = utils.Spinbox(5, 1, validation.examples.drift)
        self._amount = utils.Counter(self._limit, "Number of scans since last routine", start=0)
        self._amount.limitChanged.connect(lambda v: self.settingChanged.emit("drift_scans", v))
        self._amount.limitFailure.connect(failure_action)
        self._amount.needsReset.connect(self.conditionHit.emit)
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

        self._drift_resolution = utils.LabelledWidget("Reference Resolution",
                                                      utils.ComboBox(*TranslateRegion.SIZES, start_i=-1),
                                                      utils.LabelOrder.SUFFIX)
        self._drift_resolution.focus.dataPassed.connect(lambda v: self.settingChanged.emit("drift_resolution", v))
        self._drift_resolution.focus.dataFailed.connect(failure_action)

        self._window_order = self._order

        self._drift_scans = self._limit
        self._window_order = self._order

        self._regular.addWidget(self._amount)
        self._regular.addWidget(self._drift_resolution)
        self._regular.addWidget(self._windowing)
        self._regular.addWidget(self._order)

        self._shift = utils.SizeControl(0, 1, validation.examples.any_int)
        if not microscope.ONLINE:
            self._layout.addWidget(self._shift, 0, 2)
        self._outputs = utils.Subplot(1, 3, survey_size, survey_size, survey_size, title="ref | new | correlation")
        self._o_size = survey_size
        self.setLayout(self._layout)

    def scans_increased(self):
        self._amount.increase()

    def set_ref(self, tl: _tuple[int, int], br: _tuple[int, int]):
        print(f"set_ref({tl}, {br})")
        self._region = utils.ScanRegion(tl, br[0] - tl[0], self._size)
        self._ref = self._do_scan(0, 0)
        self._amount.set_current(0)

    def query(self):
        self._amount.check()

    def close(self):
        self._outputs.close()
        super().close()

    def open_all(self):
        if self._outputs.isVisible():
            self._outputs.raise_()
        else:
            self._outputs.show()

    def _do_scan(self, x_shift: int, y_shift: int) -> images.GreyImage:
        if microscope.ONLINE:
            res = self._drift_resolution.focus.get_data()
            new_reg = self._region @ res
            print(f"{self._region = !s}, {new_reg = !s}")
            top_left = new_reg[images.AABBCorner.TOP_LEFT]
            return self._scan(microscope.AreaScan((res, res), (new_reg.size, new_reg.size), top_left), True)
        else:
            x_min, y_min = self._region[images.AABBCorner.TOP_LEFT]
            x_max, y_max = self._region[images.AABBCorner.BOTTOM_RIGHT]
            return images.GreyImage.from_file("./assets/img_3.bmp").region((x_min + x_shift, y_min + y_shift),
                                                                           (x_max + x_shift, y_max + y_shift))

    @utils.Tracked
    def run(self):
        if not self.isEnabled():
            return
        if self._ref is None:
            raise StagingError("drift correction", "exporting drift region")
        self.runStart.emit()
        x_shift, y_shift = map(int, self._shift.get_data())
        size = self._region.size
        new = self._do_scan(x_shift, y_shift)

        ref_mask = self._window(self._ref.image().astype(np.float64))
        new_mask = self._window(new.image().astype(np.float64))
        correlation = convolve(ref_mask, new_mask[::-1, ::-1], mode="same")

        for cnv, arr in zip(self._outputs, (ref_mask, new_mask, correlation)):
            arr_dis = arr + np.abs(np.min(arr))
            img = images.GreyImage(((arr_dis / np.max(arr_dis)) * 255).astype(np.uint8))
            cnv.resize_canvas(img.size)
            cnv.draw(img)
        # shift exceeds FOV - bail
        peak = np.array(np.unravel_index(np.argmax(correlation), correlation.shape))
        correction = np.ceil([size / 2] * 2).astype(np.int_) - peak
        self.drift.emit(correction[1], correction[0])
        self.open_all()
        if microscope.ONLINE:
            self._ref = new
        self.runEnd.emit()

    def _window(self, image: np.ndarray) -> np.ndarray:
        def _hanning(img: np.ndarray) -> np.ndarray:
            m, n = img.shape
            return img * np.outer(np.hanning(m), np.hanning(n))

        def _sobel(img: np.ndarray) -> np.ndarray:
            sx = imgs.sobel(img, axis=0, mode="constant")
            sy = imgs.sobel(img, axis=1, mode="constant")
            return np.hypot(sx, sy)

        def _median(img: np.ndarray) -> np.ndarray:
            return imgs.median_filter(img, size=3)

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
        yield from ("drift_scans", "windowing", "window_order", "drift_resolution")
