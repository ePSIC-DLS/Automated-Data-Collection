import typing
from typing import Tuple as _tuple, List as _list

from .. import corrections
from ..._base import Page, widgets, microscope, utils
from ....language import vals
from ....images import GreyImage


class Corrections(typing.TypedDict):
    focus: corrections.AutoFocus
    emission: corrections.Flash
    drift: corrections.TranslateRegion


class Manager(Page):

    def __init__(self, failure_action: typing.Callable[[Exception], None], mic: microscope.Microscope,
                 scanner: microscope.Scanner, survey_size: _tuple[int, int],
                 scanning: typing.Callable[[microscope.ScanType, bool], GreyImage]):
        super().__init__()
        self._master = widgets.QTabWidget()
        self._master.setUsesScrollButtons(False)
        self._master.setTabShape(self._master.Triangular)
        c1 = corrections.AutoFocus(failure_action, mic, scanner)
        c2 = corrections.Flash(failure_action, mic)
        c3 = corrections.TranslateRegion(failure_action, mic, scanner, scanning, survey_size)
        self._corrections: Corrections = {"focus": c1, "emission": c2, "drift": c3}
        self._master.addTab(c1, "&Focus")
        self._master.addTab(c2, "&Emission")
        self._master.addTab(c3, "Dr&ift")
        self._layout.addWidget(self._master, 0, 0)
        self._enabled = utils.Flag(utils.Corrections, utils.Corrections(7))
        self._enabled.dataPassed.connect(self._child_visibility)
        self._layout.addWidget(self._enabled, 0, 1)
        self.setLayout(self._layout)

    def _child_visibility(self, value: utils.Corrections):
        for i, c in enumerate(self._corrections.values()):
            c.setEnabled(False)
            self._master.setTabEnabled(i, False)
        if value & utils.Corrections.DRIFT:
            self._corrections["drift"].setEnabled(True)
            self._master.setTabEnabled(2, True)
        if value & utils.Corrections.EMISSION:
            self._corrections["emission"].setEnabled(True)
            self._master.setTabEnabled(1, True)
        if value & utils.Corrections.FOCUS:
            self._corrections["focus"].setEnabled(True)
            self._master.setTabEnabled(0, True)
        self._master.setCurrentIndex(0)

    def add_tooltip(self, i: int, tooltip: str):
        self._master.setTabToolTip(i, tooltip)

    def run_now(self, argc: vals.Number, argv: _list[vals.Value]):
        if argc != 1:
            raise TypeError(f"Expected 1 argument, got {argc}")
        correction = argv[0].raw
        if correction not in self._corrections:
            raise ValueError(f"{correction!r} not recognised as a valid correction")
        correction = typing.cast(typing.Literal["focus", "emission", "drift"], correction)
        self._corrections[correction].run()

    def compile(self) -> str:
        return ""

    def run(self):
        pass

    def clear(self):
        pass

    def close(self):
        for correction in self._corrections.values():
            correction.close()
        super().close()

    def start(self):
        super().start()
        self._child_visibility(utils.Corrections(15))
        self.setEnabled(True)
        for correction in self._corrections.values():
            correction.start()

    def stop(self):
        super().stop()
        self.setEnabled(False)
        for correction in self._corrections.values():
            correction.stop()

    def pause(self):
        super().pause()
        for correction in self._corrections.values():
            correction.pause()

    def corrections(self) -> Corrections:
        return self._corrections.copy()

    def help(self) -> str:
        s = f"""This page allows for configuring certain 'corrections' due to hardware irregularities.
        The following corrections are available:
            Focus - perform an auto-focus routine to adjust the lens objective focus value.
            Emission - perform a beam-flashing routine to refresh emission when it gets too low.
            Drift - perform a co-ordinate transform to ensure the co-ordinates are still valid;
            especially useful for high-magnification work where small drift amounts can largely affect the scene."""
        return s
