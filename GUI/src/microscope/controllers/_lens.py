from .._base import Base
from .._utils import *
from ... import validation

if ONLINE:
    from PyJEM.TEM3 import Lens3
else:
    from ..PyJEM.offline.TEM3 import Lens3

lens = validation.Pipeline.enum(Lens)


class Controller(Base):
    """
    Concrete controller for the lenses.

    Keys
    ----
    current: Lens (enum validation)
        The current lens being controlled.
    value: int (read-only)
        The value of the lens being controlled.
    """

    @Key
    def current(self) -> Lens:
        """
        Public access to the controlling lens.

        Returns
        -------
        Lens
            The current lens being controlled.
        """
        return self._current

    @current.setter
    def current(self, value: Lens):
        lens.validate(value)
        self._current = value

    @Key
    def value(self) -> int:
        """
        Public access to the lens data.

        Returns
        -------
        int
            the value of the lens being controlled.
        """
        return self._controller.GetLensInfo(self._current.value)

    def __init__(self, current: Lens):
        super().__init__("Lenses")
        self._controller = Lens3()
        self.current = current
        _ = self.value  # this will prime the keys with an instance

    switch_lens = current.switch
