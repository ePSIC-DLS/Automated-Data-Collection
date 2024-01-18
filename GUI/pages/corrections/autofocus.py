"""
Module to run an autofocus routine every few scans.
"""
from . import base
from .. import extra_widgets
from PyQt5 import Qt as core


class Focus(base.BlockingCorrection):
    """
    Concrete subclass to represent a focus correction that runs every few scans. The number of scans is configurable.
    """
    RANGE = (2, 20)
    begin = core.pyqtSignal()
    end = core.pyqtSignal()

    def __init__(self):
        super().__init__("0", extra_widgets.FixedSpinBox.from_range, self.RANGE, 1, "scans", value=15)
        self._control.setPrefix("/ ")

    def update_on_scan(self, new: int):
        self._value.setText(str(new))
        if new % self._control.value() == 0:
            self.ready.emit()

    # @base.BlockingCorrection.block
    def run(self, btn_state: bool):
        print("Running Auto Focus Routine")
