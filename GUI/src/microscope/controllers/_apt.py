from .._base import Base
from .._utils import *
from ... import validation

from typing import Tuple as _tuple

if ONLINE:
    from PyJEM.TEM3 import Apt3
else:
    from ..PyJEM.offline.TEM3 import Apt3

apt_kind = validation.Pipeline.enum(AptKind)


class Controller(Base):
    """
    Concrete controller for the apertures.

    Keys
    ----
    current: AptKind (enum validation)
        The current aperture kind.
    position: tuple[int, int] (int12 validation on each element)
        The position of the aperture.
    size: int (apt_size validation)
        The size of the aperture.
    """

    @Key
    def current(self) -> AptKind:
        """
        Public access to the aperture being controlled.

        Returns
        -------
        AptKind
            The current aperture kind.
        """
        return AptKind(self._controller.GetExpKind())

    @current.setter
    def current(self, kind: AptKind):
        apt_kind.validate(kind)
        self._controller.SelectExpKind(kind.value)

    @Key
    def position(self) -> _tuple[int, int]:
        """
        Public access to the aperture's position.

        Returns
        -------
        tuple[int, int]
            The position of the aperture.
        """
        v = self._controller.GetPosition()
        return v[0], v[1]

    @position.setter
    def position(self, position: _tuple[int, int]):
        for v in position:
            validation.examples.int12.validate(v)
        self._controller.SetPosition(*position)

    @Key
    def size(self) -> int:
        """
        Public access to the aperture's size.

        Returns
        -------
        int
            The size of the aperture.
        """
        return self._controller.GetExpSize(self.current.value)

    @size.setter
    def size(self, value: int):
        validation.examples.apt_size.validate(value)
        self._controller.SetExpSize(self.current.value, value)

    def __init__(self, starting: AptKind = None):
        super().__init__("Apertures")
        self._controller = Apt3()
        if starting is not None:
            self.current = starting
        _ = self.current, self.position, self.size  # this will prime the keys with an instance

    switch_current = current.switch
    switch_position = position.switch
    switch_size = size.switch
