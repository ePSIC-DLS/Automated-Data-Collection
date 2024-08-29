import typing
from typing import Optional as _None, Tuple as _tuple

import numpy as np
import scipy.ndimage as imgs
from skimage.registration import phase_cross_correlation as convolve

from ... import utils
from ..._base import core, microscope, ShortCorrectionPage, widgets
from .... import images, load_settings, validation
from ..._errors import *

default_settings = load_settings("assets/config.json",
                                 drift_scans=validation.examples.drift,
                                 windowing=validation.examples.flag_3,
                                 window_order=validation.examples.window_order,
                                 drift_resolution=validation.examples.resolution,
                                 )


class TranslateRegion(ShortCorrectionPage):
    """
    Correction page for a shift routine between a reference image and a fresh scan. This is a stage drift correction.

    Note that the external counter for this correction is the number of high-resolution scans performed.

    Signals
    -------
    drift: int, int
        The signal emitted when the drift vector has been found.

    Attributes
    ----------
    SIZES: tuple[int, ...]
        The possible resolutions for the reference image.
    _scanner: Scanner
        The scanner to perform a scan.
    _scan: Callable[[ScanType, bool], GreyImage]
        The scanned image.
    _size: int
        The original size of the reference image - used to determine the location when upscaled.
    _ref: GreyImage | None
        The stored reference image.
    _region: ScanRegion | None
        The region of the survey image that the reference image is located in.
    _limit: Spinbox
        The maximal number of scans before a drift correction is run.
    _amount: Counter
        The number of scans performed since the last correction.
    _windowing: LabelledWidget[Flag[Windowing]]
        The types of windowing enabled.
    _order: LabelledWidget[OrderedGroup[QLabel]]
        The order of enabled windows.
    _drift_resolution: LabelledWidget[ComboBox[int]]
        The upscaled resolution to perform each scan in.
    _window_order: LabelledWidget[OrderedGroup[QLabel]]
        Alias for `_order` to maintain a clean global namespace for the DSL.
    _drift_scans: Spinbox
        Alias for `_limit` to maintain a clean global namespace for the DSL.
    """
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

        self._limit = utils.Spinbox(default_settings["drift_scans"], 1, validation.examples.drift)
        self._amount = utils.Counter(self._limit, "Number of scans since last routine", start=0)
        self._amount.limitChanged.connect(lambda v: self.settingChanged.emit("drift_scans", v))
        self._amount.limitFailure.connect(failure_action)
        self._amount.needsReset.connect(self.conditionHit.emit)
        flags = map(lambda f, p: int(f) * 2 ** p, default_settings["windowing"], range(2, -1, -1))
        self._windowing = utils.LabelledWidget("Windowing types",
                                               utils.Flag(utils.Windowing, utils.Windowing(sum(flags))),
                                               utils.LabelOrder.SUFFIX)
        self._windowing.focus.dataPassed.connect(lambda v: self.settingChanged.emit("windowing", v))
        self._windowing.focus.dataFailed.connect(failure_action)
        self._order = utils.LabelledWidget("Windowing Order",
                                           utils.OrderedGroup(*map(widgets.QLabel, default_settings["window_order"])),
                                           utils.LabelOrder.SUFFIX)
        self._order.focus.orderChanged.connect(lambda o, n:
                                               self.settingChanged.emit(
                                                   "window_order",
                                                   tuple(lab.text() for lab in self._order.focus.get_members())
                                               ))

        resolution = TranslateRegion.SIZES.index(default_settings["drift_resolution"])
        self._drift_resolution = utils.LabelledWidget("Reference Resolution",
                                                      utils.ComboBox(*TranslateRegion.SIZES, start_i=resolution),
                                                      utils.LabelOrder.SUFFIX)
        self._drift_resolution.focus.dataPassed.connect(lambda v: self.settingChanged.emit("drift_resolution", v))
        self._drift_resolution.focus.dataFailed.connect(failure_action)

        self._window_order = self._order
        self._drift_scans = self._limit

        self._regular.addWidget(self._amount)
        self._regular.addWidget(self._drift_resolution)
        self._regular.addWidget(self._windowing)
        self._regular.addWidget(self._order)

        self._shift = utils.SizeControl(0, 1, validation.examples.any_int)
        if not microscope.ONLINE:
            self._layout.addWidget(self._shift, 0, 2)

        self._outputs = utils.Subplot(2, 2, *((512, 512),) * 4,
                                      title="Drift outputs: Reference Image | Scanned Image | Shifted Reference | Mask")
        for cnv in self._outputs:
            cnv.draw(images.RGBImage.blank(cnv.image_size))
        self._o_size = survey_size
        self.setLayout(self._layout)

    def scans_increased(self):
        """
        Method to increase the number of scans performed by 1.
        """
        self._amount.increase()

    def set_ref(self, tl: _tuple[int, int], br: _tuple[int, int]):
        """
        Method to set a reference image.

        This will store a region, an image, and reset the number of scans performed.

        Parameters
        ----------
        tl: tuple[int, int]
            The top-left co-ordinate of the region.
        br: tuple[int, int]
            The bottom-right co-ordinate of the region.
        """
        self._region = utils.ScanRegion(tl, br[0] - tl[0], self._size)
        self._ref = self._do_scan(0, 0)
        self._amount.set_current(0)
        self._outputs[0, 0].draw(self._ref, resize=True)
        self._display_popup(self._outputs)

    def query(self):
        self._amount.check()

    def _do_scan(self, x_shift: int, y_shift: int) -> images.RGBImage:
        if microscope.ONLINE:
            res = self._drift_resolution.focus.get_data()
            new_reg = self._region @ res
            top_left = new_reg[images.AABBCorner.TOP_LEFT]
            area = microscope.AreaScan((res, res), (new_reg.size, new_reg.size), top_left)
            return self._scan(area, True).norm().dynamic().promote()
        else:
            x_min, y_min = self._region[images.AABBCorner.TOP_LEFT]
            x_max, y_max = self._region[images.AABBCorner.BOTTOM_RIGHT]
            full = images.GreyImage.from_file("./assets/img_3.bmp")
            return full.region((x_min + x_shift, y_min + y_shift), (x_max + x_shift, y_max + y_shift)).promote()

    def start(self):
        ShortCorrectionPage.start(self)
        self._display_popup(self._outputs)

    def stop(self):
        ShortCorrectionPage.stop(self)
        self._outputs.close()

    @utils.Tracked
    def run(self):
        if not self.isEnabled():
            return
        if self._ref is None:
            raise StagingError("drift correction", "exporting drift region")
        self.runStart.emit()
        x_shift, y_shift = map(int, self._shift.get_data())
        new = self._do_scan(x_shift, y_shift)

        ref_mask = self._window(self._ref.convert(np.float64))
        new_mask = self._window(new.convert(np.float64))
        corr, error, _ = convolve(ref_mask, new_mask)
        shift = -corr
        self._outputs[0, 1].draw(new, resize=True)
        shifted_ref = np.real(np.fft.ifft(imgs.fourier_shift(np.fft.fftn(ref_mask), shift))).astype(np.int_)
        correction = shift.astype(np.int_)
        mask = images.RGBImage(np.where(shifted_ref == new_mask, 255, 0))
        self._outputs[1, 0].draw(images.RGBImage(shifted_ref).norm(), resize=True)
        self._outputs[1, 1].draw(mask.downchannel(0, mask.make_green(), invalid=images.ColourConvert.TO_FG).upchannel(),
                                 resize=True)
        self.drift.emit(correction[1], correction[0])
        if microscope.ONLINE:
            self._ref = new
            self._outputs[0, 0].draw(self._ref)
        self._display_popup(self._outputs)
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

    def help(self) -> str:
        s = f"""This correction is meant to combat the movement of internal positions of the microscope.
        This will help keep the Field Of View (FOV) constant.
        
        It will use an upscaled, known region of the survey image as a reference. The upscaling improves SNR.

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
        Reference Resolution:
            {self._drift_resolution.focus.validation_pipe()}
            
            The upscaled resolution to scan each image in."""
        return s
