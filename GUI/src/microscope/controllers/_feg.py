from .._base import Base
from .._utils import *
from ... import validation
from typing import Tuple as _tuple

if ONLINE:
    from PyJEM.TEM3 import FEG3


class FEG3Offline:
    """
    Placeholder class to represent an offline connection to the FEG system.
    """

    def GetV1Ready(self) -> int:
        """
        Get whether the v1 system is ready.

        Returns
        -------
        int
            Whether the v1 system is ready.
        """
        return 1

    def GetEmissionOnStatus(self) -> _tuple[int, int]:
        """
        Get whether the emission is on.

        Returns
        -------
        tuple[int, int]
            A tuple depicting the phase and status of the emission.
        """
        return 1, 1

    def ExecEmissionOn(self, begin: int):
        """
        Execute the emission on procedure.

        Parameters
        ----------
        begin: int
            Whether the process should be started or stopped.
        """
        pass

    def SetFEGEmissionOff(self, begin: int):
        """
        Execute the emission off procedure.

        Parameters
        ----------
        begin: int
            Whether the process should be started or stopped.
        """
        pass

    def GetBeamValve(self) -> int:
        """
        Get the status of the beam valve.

        Returns
        -------
        int
            Whether the valve is open.
        """
        return 1

    def SetBeamValve(self, new: int):
        """
        Change the beam valve status.

        Parameters
        ----------
        new: int
            Whether the valve is open.
        """
        pass

    def ExecAutoFlashing(self, begin: int):
        """
        Execute the low flash procedure.

        Parameters
        ----------
        begin: int
            Whether the process should be started or stopped.
        """
        pass


class Controller(Base):
    """
    Concrete controller for the FEG system.

    Keys
    ----
    ready: bool (read-only)
        Whether the v1 is ready.
    emission: bool
        Whether the emission is enabled.
    valve: bool
        Whether the valve is open.
    """

    @Key
    def ready(self) -> bool:
        """
        Public access to the state of the v1 subsystem.

        Returns
        -------
        bool
            Whether the v1 is ready.
        """
        return bool(self._controller.GetV1Ready())

    @Key
    def emission(self) -> bool:
        """
        Public access to the state of the emission subsystem.

        Returns
        -------
        bool
            Whether the emission is enabled.

        Raises
        ------
        ValueError
            If the process errors.
        """
        phase, status = self._controller.GetEmissionOnStatus() if not ONLINE else FEG3Offline.GetEmissionOnStatus(...)
        if phase == -1:
            raise ValueError("Process has errored")
        status = bool(status)
        return status if not phase else not status

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
        """
        Public access to the state of the valve subsystem.

        Returns
        -------
        bool
            Whether the valve is open.
        """
        return bool(self._controller.GetBeamValve())

    @valve.setter
    def valve(self, value: bool):
        validation.examples.any_bool.validate(value)
        if not self.ready:
            raise ValueError("Cannot open or close beam valve while not ready")
        self._controller.SetBeamValve(int(value))

    def __init__(self, valve: bool = None):
        super().__init__("FEG")
        if ONLINE:
            self._controller = FEG3()
        else:
            self._controller = FEG3Offline()
        if valve is not None:
            self.valve = valve
        _ = self.ready, self.emission, self.valve  # this will prime the keys with an instance

    def auto_flash_control(self, on: bool):  # possibly change signature - is flashing timed?
        """
        Automatically flashes the beam tip.

        Parameters
        ----------
        on: bool
            Whether the flash should be started or stopped.

        Raises
        ------
        ValueError
            If the FEG is not ready.
        """
        validation.examples.any_bool.validate(on)
        if not self.ready:
            raise ValueError("Cannot flash tip without being ready")
        self._controller.ExecAutoFlashing(on)

    switch_emission = emission.switch
    switch_valve = valve.switch
