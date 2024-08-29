import typing

from typing import Tuple as _tuple

import numpy as np

from ... import utils
from ..._base import images, microscope, ShortCorrectionPage
from .... import load_settings, validation
from ..._errors import *

default_settings = load_settings("assets/config.json",
                                 focus_scans=validation.examples.focus,
                                 focus_change=validation.examples.focus_change,
                                 change_decay=validation.examples.focus_decay,
                                 focus_tolerance=validation.examples.lens_value,
                                 focus_limit=validation.examples.focus_limit_hex,
                                 )


class AutoFocus(ShortCorrectionPage):
    """
    Correction page for an autofocus routine. This is an OLF lens correction.

    Note that the external counter for this correction is the number of high-resolution scans performed.

    Attributes
    ----------
    _scanner: Scanner
        The scanner to perform a scan.
    _scan: Callable[[ScanType, bool], GreyImage]
        The function capable of producing a scanned image.
    _region: FullScan
        The scan region to scan on - note that this is the full survey image.
    _focus_scans: Spinbox
        The number of scans performed prior to the correction being run.
    _scans: Counter
        The number of scans performed since the last correction.
    _decay: LabelledWidget[Spinbox]
        The rate of decay for the unit change to take in a run.
    _df: LabelledWidget[Spinbox]
        The unit change in the OLF lens.
    _tolerance: LabelledWidget[Spinbox]
        The lowest allowed value for the unit change to be before the focus correction is complete.
    _limit: LabelledWidget[Spinbox]
        The maximum number defocus to check for. This is the absolute defocus measured in nm.
    _plot: Canvas
        The current image being scanned.
    _focus_change: LabelledWidget[Spinbox]
        Alias for `_df` to maintain a clean global namespace for the DSL.
    _change_decay: LabelledWidget[Spinbox]
        Alias for `_decay` to maintain a clean global namespace for the DSL.
    _focus_tolerance: LabelledWidget[Spinbox]
        Alias for `_tolerance` to maintain a clean global namespace for the DSL.
    _focus_limit: LabelledWidget[Spinbox]
        Alias for `_limit` to maintain a clean global namespace for the DSL.
    """

    def __init__(self, failure_action: typing.Callable[[Exception], None], mic: microscope.Microscope,
                 scanner: microscope.Scanner, survey_size: _tuple[int, int],
                 scan_func: typing.Callable[[microscope.ScanType, bool], images.GreyImage]):
        super().__init__(mic)
        self._scanner = scanner
        self._scan = scan_func
        self._region = microscope.FullScan(survey_size)

        self._focus_scans = utils.Spinbox(default_settings["focus_scans"], 1, validation.examples.focus)
        self._scans = utils.Counter(self._focus_scans, "Number of scans since last routine", start=0)
        self._scans.needsReset.connect(self.conditionHit.emit)
        self._decay = utils.LabelledWidget("Decay", utils.PercentageBox(int(default_settings["change_decay"] * 100),
                                                                        validation.examples.focus_decay),
                                           utils.LabelOrder.SUFFIX)
        self._df = utils.LabelledWidget("Unit Change",
                                        utils.Spinbox(default_settings["focus_change"], 1,
                                                      validation.examples.focus_bits,
                                                      display=(lambda f: f"{f:04X}", lambda s: int(s, 16))),
                                        utils.LabelOrder.SUFFIX)
        focus_tolerance = validation.examples.any_int + validation.Pipeline(
            validation.Step(validation.RangeValidator(validation.LowerBoundValidator(1),
                                                      validation.DynamicUpperBoundValidator(
                                                          lambda: self._df.focus.get_data(),
                                                          inclusive=False))),
            in_type=int, out_type=int
        )
        self._tolerance = utils.LabelledWidget("Lowest Change",
                                               utils.Spinbox(default_settings["focus_tolerance"], 1, focus_tolerance,
                                                             display=(lambda f: f"{f:04X}", lambda s: int(s, 16))),
                                               utils.LabelOrder.SUFFIX)
        self._limit = utils.LabelledWidget("Defocus Limit",
                                           utils.Spinbox(default_settings["focus_limit"] * 0.76, 20,
                                                         validation.examples.focus_limit,
                                                         display=(lambda f: f"{int(f / 0.76):04X}",
                                                                  lambda s: float(int(s, 16) * 0.76))),
                                           utils.LabelOrder.SUFFIX)

        self._df.focus.dataPassed.connect(lambda v: self.settingChanged.emit("focus_change", v))
        self._df.focus.dataFailed.connect(failure_action)
        self._decay.focus.dataPassed.connect(lambda v: self.settingChanged.emit("change_decay", v))
        self._decay.focus.dataFailed.connect(failure_action)
        self._scans.limitChanged.connect(lambda v: self.settingChanged.emit("focus_scans", v))
        self._scans.limitFailure.connect(failure_action)
        self._tolerance.focus.dataPassed.connect(lambda v: self.settingChanged.emit("focus_tolerance", v))
        self._tolerance.focus.dataFailed.connect(failure_action)
        self._limit.focus.dataPassed.connect(lambda v: self.settingChanged.emit("focus_limit", v))
        self._limit.focus.dataFailed.connect(failure_action)
        self._regular.addWidget(self._scans)
        self._regular.addWidget(self._decay)
        self._regular.addWidget(self._df)
        self._regular.addWidget(self._tolerance)
        self._regular.addWidget(self._limit)

        self._plot = utils.Canvas(survey_size)

        self._focus_change = self._df
        self._change_decay = self._decay
        self._focus_tolerance = self._tolerance
        self._focus_limit = self._limit

        self.setLayout(self._layout)

    def scans_increased(self):
        """
        Method to increase the number of scans by 1.
        """
        self._scans.increase()

    def query(self):
        self._scans.check()

    def start(self):
        ShortCorrectionPage.start(self)
        self._display_popup(self._plot)

    def stop(self):
        ShortCorrectionPage.stop(self)
        self._plot.close()

    def run(self):
        if not self.isEnabled():
            return
        self.runStart.emit()
        if microscope.ONLINE:

            def _var() -> float:
                img = self._scan(self._region, True)
                self._plot.draw(img.norm().dynamic().promote())
                return self._get_variance(img)

            def _populate(*, backtrack: typing.Callable[[], None] = None):
                ds.append(link.value)
                if backtrack is not None:
                    backtrack()
                    ds.pop()
                else:
                    vs.append(_var())

            def _advance():
                link.value = ds[-1] + delta_d

            link = self._link.subsystems["Lenses"]
            delta_d = self._df.focus.get_data()
            tol = self._tolerance.focus.get_data()
            lim = self._limit.focus.get_data()
            decay = 1 - self._decay.focus.get_data()
            with link.switch_lens(microscope.Lens.OL_FINE):
                ds = []
                vs = []

                _populate()
                link.value = ds[0] + delta_d
                _populate()
                if vs[0] > vs[1]:
                    delta_d = -delta_d
                    _advance()  # back to zero
                    _populate(backtrack=_advance)  # advance again to get back on track
                i = 1
                minima, maxima = ds[0] - lim, ds[0] + lim

                while abs(delta_d) > tol and minima <= ds[-1] <= maxima:
                    i += 1
                    _populate()
                    if vs[-2] > vs[-1]:
                        delta_d = -int(delta_d * decay)
                    _advance()

                max_var = max(vs)
                ideal_delta = ds[vs.index(max_var)]
                link.value = ideal_delta

                if abs(delta_d) > tol:
                    raise GUIError(utils.ErrorSeverity.WARNING, "Too much defocus", "Defocus is beyond set limit")
        self.runEnd.emit()

    @staticmethod
    def _get_variance(image: images.GreyImage) -> float:
        array = image.convert(np.float64)
        return array.var() / (array.mean() ** 2)

    def all_settings(self) -> typing.Iterator[str]:
        yield from ("focus_change", "change_decay", "focus_scans", "focus_tolerance", "focus_limit")

    def help(self) -> str:
        s = f"""This correction is meant to combat the OLf value of the microscope no longer being optimal.
        As this is not a live correction (i.e. the value is not constantly being suboptimal);
        this is dependant on the number of scans being run.
        
        It is a blocking correction, and will halt the execution of other functions until it is finished.
        
        Settings
        --------
        Scan Amount:
            {validation.examples.focus}
            
            The number of scans to perform prior to this correction being run;
            this will cause the counter to reset when reached.
        Decay:
            {validation.examples.focus_decay}
            
            The rate of decay for the unit change. This means that the step gets exponentially lower each reversal.
            
            Autofocus acts like both a coarse sweep (flicking between over- and under-shooting the ideal point) and a;
            fine sweep (settling near the maxima) at the same time, dependant on how many times it's reversed. 
        Unit Change:
            {validation.examples.focus_bits}
            
            The value to change the OLf value by. It is a hexadecimal value.
        Lowest Change:
            {self._focus_tolerance.focus.validation_pipe()}
            
            The lowest value for the unit change to be before it is deemed that there is no point sweeping any more.
        Defocus Limit
            {validation.examples.focus_limit}
            
            The maximum amount of defocus (in nm) to check for."""
        return s
