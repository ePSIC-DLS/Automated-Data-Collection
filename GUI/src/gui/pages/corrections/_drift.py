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
    radiusUpdate = core.pyqtSignal(int)

    def __init__(self, failure_action: typing.Callable[[Exception], None], mic: microscope.Microscope,
                 scanner: microscope.Scanner, survey_size: _tuple[int, int]):
        super().__init__(mic)
        self._scanner = scanner
        self._size = survey_size

        self._ref: _None[images.GreyImage] = None
        self._chosen: _None[utils.Cluster] = None

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

        self._window_order = self._order

        self._radius = utils.LabelledWidget("Cluster Radius",
                                            utils.Spinbox(5, 2, validation.examples.drift_radius),
                                            utils.LabelOrder.SUFFIX)
        self._radius.focus.dataPassed.connect(lambda v: self.radiusUpdate.emit(int(v)))
        self._radius.focus.dataPassed.connect(lambda v: self.settingChanged.emit("radius", v))
        self._radius.focus.dataFailed.connect(failure_action)

        self._drift_scans = self._limit
        self._window_order = self._order

        self._regular.addWidget(self._amount)
        self._regular.addWidget(self._radius)
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

    def set_ref(self, image: images.GreyImage):
        self._ref = image
        self._amount.set_current(0)

    def set_cluster(self, chosen: utils.Cluster):
        self._chosen = chosen
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

    @utils.Tracked
    def run(self):
        if self._chosen is None:
            raise StagingError("drift correction", "clustering")
        elif self._ref is None:
            raise StagingError("drift correction", "collecting a survey image")
        self.runStart.emit()
        radius = self._radius.focus.get_data()
        x_size = self._chosen.size(utils.Axis.X) + radius
        y_size = self._chosen.size(utils.Axis.Y) + radius
        x_lim, y_lim = self._size
        x_shift, y_shift = map(int, self._shift.get_data())

        def _pad(start: int, end: int, size: int, limit: int) -> _tuple[int, int]:
            while end - start != size:
                if end < limit:
                    end += 1
                    if end - start == size:
                        break
                if start > 0:
                    start -= 1
                if end > limit and start < 0:
                    raise ValueError("Chosen cluster invalid, cannot be padded such that it fits within the image size")
            return start, end

        sx, ex = _pad(self._chosen.extreme(utils.Axis.X, utils.Extreme.MINIMA),
                      self._chosen.extreme(utils.Axis.X, utils.Extreme.MAXIMA), x_size, x_lim)
        sy, ey = _pad(self._chosen.extreme(utils.Axis.Y, utils.Extreme.MINIMA),
                      self._chosen.extreme(utils.Axis.Y, utils.Extreme.MAXIMA), y_size, y_lim)
        reference = self._ref.region((sx, sy), (ex, ey))

        if microscope.ONLINE:
            with self._scanner.switch_scan_area(microscope.AreaScan(self._size, (x_size, y_size), (sx, sy))):
                with self._scanner.switch_dwell_time(15e-6):
                    with self._link.subsystems["Deflectors"].switch_blanked(False):
                        with self._link.subsystems["Detectors"].switch_inserted(True):
                            new = self._scanner.scan()
        else:
            new = images.GreyImage.from_file(
                r"C:\Users\fmz84311\OneDrive - Diamond Light Source Ltd\Documents\Project\Collection\assets\img_3.bmp"
            ).region((sx + x_shift, sy + y_shift), (ex + x_shift, ey + y_shift))

        ref_mask = self._window(reference.image().astype(np.float64))
        new_mask = self._window(new.image().astype(np.float64))
        correlation = convolve(ref_mask, new_mask[::-1, ::-1], mode="same")

        for cnv, img in zip(self._outputs, (ref_mask, new_mask, correlation)):
            img_pos = np.abs(np.min(img)) + img
            img_norm = (img_pos / np.max(img_pos)) * 255
            img_dis = images.GreyImage(img_norm.astype(np.uint32))
            cnv.resize_canvas(img_dis.size)
            cnv.draw(img_dis)

        # View cross correlation gives me for too large shifts - error when not valid
        peak = np.array(np.unravel_index(np.argmax(correlation), correlation.shape))
        correction = np.ceil([y_size / 2, x_size / 2]).astype(np.int_) - peak

        self._outputs.title(f"{peak = }", " @ ")
        self.open_all()

        self.drift.emit(correction[1], correction[0])

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
        yield from ("radius", "drift_scans", "windowing", "window_order")

    def help(self) -> str:
        s = f"""This correction is meant to combat the movement of internal positions of the microscope.
        This will help keep the Field Of View (FOV) constant.
        
        It will use the survey image as a reference, and a known cluster position in order to minimise false positives.

        Settings
        --------
        Scan Amount
            {validation.examples.drift}

            The number of scans to perform prior to this correction being run;
            this will cause the counter to reset when reached.
        Cluster Radius
            {validation.examples.drift_radius}
            
            The radius around the chosen cluster, in pixels.
            This will project a square with `radius` pixels between the edge and the cluster's bounding box;
            using this to decide whether the cluster is too close to other clusters for it to be valid.
            
            Ideally a high radius is preferred to ensure that the cluster is isolated;
            but frequent drift correction also prevents close clusters from drifting into the FOV of the chosen cluster.
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

            The order of the windowing types."""
        return s
