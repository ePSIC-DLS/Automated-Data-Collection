"""
Module to correct for beam blanking (also allows the beam to blank on command)
"""
from PyQt5 import Qt as core

from modular_qt import utils, microscope
from . import base
from .. import extra_widgets, __pyjem__


class Beam(base.LiveCorrection):
    """
    Concrete subclass to correct the beam's 'blanked' state.

    When microscope status differs from internal state, it will update internal state on the next update.
    When ready (emitted after an update), or when the internal state changes, it will update microscope status.
    """
    RANGE = (0, 1)

    def __init__(self, threads: core.QThreadPool):
        super().__init__(threads, {"seconds": 1e-3, "when": utils.Delayer.Delay.POST}, "Beam Status",
                         extra_widgets.ComboSpin, *self.RANGE, wrap=True)
        self._link: microscope.Microscope = microscope.Microscope.get_instance()
        self._control.valueChanged.connect(self.run)

    def update_on_scan(self, new: int):
        """
        Update the blanker by syncing status with microscope.

        :param new: The new number of scans.
        """
        if __pyjem__:
            blanked = self._link["deflector.blanked"]
            if blanked != self._control.value():
                self._control.setValue(int(blanked))
        self._control.setSuffix(" (unblanked)" if not self._control.value() else " (blanked)")
        self.ready.emit()

    def run(self, btn_state: bool):
        """
        Will tell the microscope to blank the beam (or unblank) depending on status.

        :param btn_state: The state of the button that caused the callback.
        """
        if __pyjem__:
            self._link["deflector.blanked"] = bool(self._control.value())
