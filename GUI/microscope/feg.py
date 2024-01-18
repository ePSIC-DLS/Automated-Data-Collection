"""
Module to facilitate FEG control
"""

from . import __online__

if __online__:
    from .PyJEM.TEM3 import FEG3
else:
    from .PyJEM.offline.TEM3 import FEG3
from ._controller import ControllerBase, validators
from ._enums import *


class Controller(ControllerBase):
    """
    Concrete subclass to control the FEG.

    Keys:
        * open_valve (bool): Whether the beam valve is closed
        * ready (bool, read-only): Whether the V1 is ready
        * flash_status (ProcessStatus, read-only): Status of the auto-flash routine
        * emission_status (tuple[bool, ProcessStatus], read-only): State (on or off) and status of the emission
    """

    @staticmethod
    def validators() -> dict[str, validators.Pipeline]:
        return dict(
            open_valve=validators.xmpls.any_bool
        )

    def __init__(self):
        self._controller = FEG3()
        super().__init__(
            "feg",
            open_valve=(lambda: bool(self._controller.GetBeamValve()), lambda b: self._controller.SetBeamValve(int(b))),
            ready=(lambda: bool(self._controller.GetV1Ready()), None),
            flash_status=(lambda: ProcessStatus(self._controller.GetAutoFlashingStatus()), None),
            emission_status=(self._emission, None),
        )

    def auto_flash(self) -> ProcessStatus:
        """
        Automatically flash the FEG tip.

        :return: The status of the operation.
        """
        return ProcessStatus(self._controller.ExecAutoFlashing(1))

    def control_emission(self, on: bool) -> ProcessStatus:
        """
        Control whether emission is on or off.

        :param on: The state of the emission.
        :return: The status of the operation.
        """
        return ProcessStatus(self._controller.ExecEmissionOn(int(on)))

    def kill_emission(self):
        """
        Alternative method to turn emission off.

        Uses FEGEmissionOff.
        """
        self._controller.SetFEGEmissionOff(0)

    def _emission(self) -> tuple[bool, ProcessStatus]:
        phase, status = self._controller.GetEmissionOnStatus()
        return status, ProcessStatus(phase)
