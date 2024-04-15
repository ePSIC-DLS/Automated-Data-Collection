from .._base import Base
from .._utils import *
from ... import validation

if ONLINE:
    from PyJEM.TEM3 import FEG3
else:
    from ..PyJEM.offline.TEM3 import FEG3


class Controller(Base):

    @Key
    def ready(self) -> bool:
        return bool(self._controller.GetV1Ready())

    @Key
    def emission(self) -> bool:
        phase, status = self._controller.GetEmissionOnStatus()
        if phase == -1:
            raise ValueError("Process has errored")
        if not phase:
            return bool(status)
        return not status

    @emission.setter
    def emission(self, value: bool):
        validation.examples.any_bool.validate(value)
        if not self.ready:
            raise ValueError("Cannot change emission while not ready")
        if value:
            self._controller.ExecEmissionOn(1)
        else:
            self._controller.SetFEGEmissionOff(1)

    @Key
    def valve(self) -> bool:
        return bool(self._controller.GetBeamValve())

    @valve.setter
    def valve(self, value: bool):
        validation.examples.any_bool.validate(value)
        if not self.ready:
            raise ValueError("Cannot open or close beam valve while not ready")
        self._controller.SetBeamValve(int(value))

    def __init__(self, valve: bool = None):
        super().__init__("FEG")
        self._controller = FEG3()
        if valve is None:
            valve = self.valve
        self.valve = valve

    def auto_flash_control(self, on: bool):  # possibly change signature - is flashing timed?
        validation.examples.any_bool.validate(on)
        if not self.ready:
            raise ValueError("Cannot flash tip without being ready")
        self._controller.ExecAutoFlashing(on)
