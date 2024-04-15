from .._base import Base
from .._utils import *
from ... import validation

if ONLINE:
    from PyJEM.TEM3 import Lens3
else:
    from ..PyJEM.offline.TEM3 import Lens3

lens = validation.Pipeline.enum(Lens)


class Controller(Base):

    @Key
    def current(self) -> Lens:
        return self._current

    @current.setter
    def current(self, value: Lens):
        lens.validate(value)
        self._current = value

    @Key
    def value(self) -> int:
        return self._controller.GetLensInfo(self._current.value)

    def __init__(self, current: Lens):
        super().__init__("Lenses")
        self._controller = Lens3()
        self._current = current

    switch_lens = current.switch
