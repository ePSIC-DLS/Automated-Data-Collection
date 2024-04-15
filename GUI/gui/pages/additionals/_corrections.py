import typing
from typing import Tuple as _tuple

from .. import corrections
from ..._base import Page, widgets, microscope


class Corrections(typing.TypedDict):
    focus: corrections.AutoFocus
    emission: corrections.Flash
    drift: corrections.TranslateRegion


class Manager(Page):

    def __init__(self, failure_action: typing.Callable[[Exception], None], mic: microscope.Microscope,
                 scanner: microscope.Scanner, survey_size: _tuple[int, int]):
        super().__init__()
        self._master = widgets.QTabWidget()
        self._master.setUsesScrollButtons(False)
        self._master.setTabShape(self._master.Triangular)
        c1 = corrections.AutoFocus(failure_action, mic, scanner)
        c2 = corrections.Flash(failure_action, mic)
        c3 = corrections.TranslateRegion(failure_action, mic, scanner, survey_size)
        self._corrections: Corrections = {"focus": c1, "emission": c2, "drift": c3}
        self._master.addTab(c1, "&Focus")
        self._master.addTab(c2, "&Emission")
        self._master.addTab(c3, "D&rift")
        self._layout.addWidget(self._master)
        self.setLayout(self._layout)

    def add_tooltip(self, i: int, tooltip: str):
        self._master.setTabToolTip(i, tooltip)

    def run_now(self, _, correction: typing.Literal["focus", "emission", "drift"]):
        if correction not in self._corrections:
            raise ValueError(f"{correction!r} not recognised as a valid correction")
        self._corrections[correction].run()

    def compile(self) -> str:
        return ""

    def run(self):
        pass

    def clear(self):
        pass

    def start(self):
        super().start()
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
