from .._base import Base
from .._utils import *

if ONLINE:
    from PyJEM.TEM3 import GUN3


class GUN3Offline:
    """
    Placeholder class to represent an offline connection to the gun.
    """

    def GetFilamentCurrentValue(self) -> float:
        """
        Get the value of the filament.

        Returns
        -------
        float
            Filament value.
        """
        return 0.0

    def GetEmissionCurrentValue(self):
        """
        Get the value of the emission current.

        Returns
        -------
        float
            Current in microamps.
        """
        return 0.0


class Controller(Base):
    """
    Concrete controller for the electron gun.

    Keys
    ----
    filament: float (read-only)
        The value of the filament.
    emission: float (read-only)
        The value of the emission.
    """

    @Key
    def filament(self) -> float:
        """
        Public access to the filament.

        Returns
        -------
        float
            The value of the filament.
        """
        return self._controller.GetFilamentCurrentValue()

    @Key
    def emission(self) -> float:
        """
        Public access to the emission.

        Returns
        -------
        float
            The value of the emission.
        """
        return self._controller.GetEmissionCurrentValue()

    def __init__(self):
        super().__init__("Gun")
        if ONLINE:
            self._controller = GUN3()
        else:
            self._controller = GUN3Offline()
        _ = self.filament, self.emission  # this will prime the keys with an instance
