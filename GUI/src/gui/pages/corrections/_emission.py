import time
import typing

from ... import utils
from ..._base import LongCorrectionPage, microscope
from .... import validation


class Flash(LongCorrectionPage):

    def __init__(self, failure_action: typing.Callable[[Exception], None], mic: microscope.Microscope):
        self._min_emission = utils.Spinbox(3.5, 0.01, validation.examples.emission)
        self._live = utils.Counter(self._min_emission, "Current Gun Emission", 1e-4, utils.Match.NO_LOWER, 4)
        self._live.limitChanged.connect(lambda v: self.settingChanged.emit("min_emission", v))
        self._live.limitFailure.connect(failure_action)
        super().__init__(mic)
        self._live.needsReset.connect(self.conditionHit.emit)
        self._regular.addWidget(self._live)
        self.setLayout(self._layout)

    @utils.Thread.decorate(manager=LongCorrectionPage.MANAGER)
    def background(self):
        if microscope.ONLINE:
            return
        while True:
            if self._state != utils.StoppableStatus.ACTIVE:
                return
            if microscope.ONLINE:
                self._live.set_current(self._link.subsystems["Gun"].emission)
            else:
                self._live.decrease()
            time.sleep(self.DELAY)

    def run(self):
        if not self.isEnabled():
            return
        self.runStart.emit()
        # if microscope.ONLINE:
        #     self._link.subsystems["FEG"].auto_flash_control(True)
        self.runEnd.emit()

    def all_settings(self) -> typing.Iterator[str]:
        yield from ("min_emission",)

    def help(self) -> str:
        s = f"""This correction is meant to combat the emission of the microscope slowly decreasing.
        As this is a live correction, it is running in a separate thread and is more time-dependant.

        Settings
        --------
        Emission Value
            {validation.examples.emission}

            The lowest value the emission can reach before requiring a beam flash."""
        return s
