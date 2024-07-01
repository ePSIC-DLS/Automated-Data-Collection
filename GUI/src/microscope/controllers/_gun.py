from .._base import Base
from .._utils import *

if ONLINE:
    from PyJEM.TEM3 import GUN3
else:
    from ..PyJEM.offline.TEM3 import GUN3


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
        self._controller = GUN3()
        _ = self.filament, self.emission  # this will prime the keys with an instance
