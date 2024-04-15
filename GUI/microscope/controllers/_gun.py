from .._base import Base
from .._utils import *

if ONLINE:
    from PyJEM.TEM3 import GUN3
else:
    from ..PyJEM.offline.TEM3 import GUN3


class Controller(Base):

    @Key
    def filament(self) -> float:
        return self._controller.GetFilamentCurrentValue()

    @Key
    def emission(self) -> float:
        return self._controller.GetEmissionCurrentValue()

    def __init__(self):
        super().__init__("Gun")
        self._controller = GUN3()
