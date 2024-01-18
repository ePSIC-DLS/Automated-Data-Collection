"""
Module to correct for emission dips.
"""
from . import base
from .. import extra_widgets, __pyjem__
from PyQt5 import Qt as core
from .base import scans as utils
from modular_qt import microscope


class Emission(base.LiveCorrection, base.BlockingCorrection):
    """
    Class to find live emission value from the microscope and test whether it is below a certain threshold.

    This is a threaded process running every second.
    """
    RANGE = (2.0, 4.0)
    begin = core.pyqtSignal()
    end = core.pyqtSignal()

    def __init__(self, threads: core.QThreadPool):
        super().__init__(threads, {"seconds": 1, "when": utils.Delayer.Delay.POST}, "3.5",
                         extra_widgets.FixedDoubleSpinBox.from_range, self.RANGE, 0.01, "uA", value=2)
        self._control.setPrefix(">= ")
        self._count = 3.5
        self._link: microscope.Microscope = microscope.Microscope.get_instance()

    def update_on_scan(self, new: int):
        """
        Refreshes emission value and checks if it is below the specified threshold.

        :param new: The new scan value
        """
        self._count -= 0.1
        if self._count < 3:
            self._count = 3.5
        if __pyjem__:
            emission = self._link["gun.emission"]
        else:
            emission = self._count
        self._value.setText(str(emission))
        if emission < self._control.value():
            self.ready.emit()

    # @base.BlockingCorrection.block
    def run(self, btn_state: bool):
        """
        Performs beam tip refresh.

        :param btn_state: The state of the calling button.
        """
        self._link.gun_controller.flash_tip()
