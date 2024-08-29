from .._base import Base
from .._utils import *
from ... import validation

from typing import Tuple as _tuple

if ONLINE:
    from PyJEM.TEM3 import Apt3


class Apt3Offline:
    """
    Placeholder class to represent an offline connection to the apertures.
    """

    def GetExpKind(self) -> int:
        """
        Get the expected kind of the aperture.

        Returns
        -------
        int
            The code for the aperture.
        """
        return 0

    def SelectExpKind(self, value: int):
        """
        Set the expected kind of the aperture.

        Parameters
        ----------
        value: int
            The code for the aperture.
        """
        pass

    def GetPosition(self) -> _tuple[int, int]:
        """
        Get the position of the aperture.

        Returns
        -------
        tuple[int, int]
            The position for the aperture.
        """
        return 0, 0

    def SetPosition(self, x: int, y: int):
        """
        Set the position of the aperture.

        Parameters
        ----------
        x: int
            The horizontal aperture position.
        y: int
            The vertical aperture position.
        """
        pass

    def GetExpSize(self, for_: int) -> int:
        """
        Get the expected size of the aperture.

        Parameters
        ----------
        for_: int
            The code for the aperture.

        Returns
        -------
        int
            The aperture's size.
        """
        return 0

    def SetExpSize(self, for_: int, size: int):
        """
        Set the expected size of the aperture.

        Parameters
        ----------
        for_: int
            The code for the aperture.
        size: int
            The aperture's size.
        """
        pass


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
        code = self._controller.GetExpKind()
        return AptKind(code)

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
        self._controller = Apt3Offline()
        if starting is not None:
            self.current = starting
        _ = self.current, self.position, self.size  # this will prime the keys with an instance

    switch_current = current.switch
    switch_position = position.switch
    switch_size = size.switch
