"""
Module to facilitate aperture control
"""
from . import __online__

if __online__:
    from .PyJEM.TEM3 import Apt3
else:
    from .PyJEM.offline.TEM3 import Apt3
from ._controller import ControllerBase, validators
from ._enums import *


class Controller(ControllerBase):
    """
    Concrete subclass to control the apertures.

    Keys:
        * pos (tuple[int, int]): The position of the current aperture. It should be between 0 and 4095
        * apt_kind (ApertureKind): The kind of aperture being controlled
        * apt (Aperture): The specific aperture being controlled
        * kind_size (int): The size of the aperture kind being controlled. 0-4, with 0 meaning "open"
        * size (int): The size of the specific aperture being controlled. 0-4, with 0 meaning "open"
    """

    @staticmethod
    def validators() -> dict[str, validators.Pipeline]:
        return dict(
            pos=validators.xmpls.low_tuple,
            apt_kind=validators.Pipeline.enum(ApertureKind),
            apt=validators.Pipeline.enum(Aperture),
            kind_size=validators.xmpls.apt_size,
            size=validators.xmpls.apt_size
        )

    def __init__(self):
        self._controller = Apt3()
        super().__init__(
            "apt",
            pos=(self._read_position, self._write_position),
            apt_kind=(lambda: ApertureKind(self._controller.GetKind()),
                      lambda k: self._controller.SelectKind(k.value)),
            apt=(lambda: Aperture(self._controller.GetExpKind()),
                 lambda a: self._controller.SelectExpKind(a.value)),
            kind_size=(lambda: self._controller.GetSize(self["apt_kind"].value), self._controller.SetSize),
            size=(lambda: self._controller.GetExpSize(self["apt"].value),
                  lambda v: self._controller.SetExpSize(self["apt"].value, v)),
        )

    def _write_kind(self, k: ApertureKind):
        if not isinstance(k, ApertureKind):
            raise TypeError("Expected an aperture kind")
        self._cache.pop("kind_size", None)
        self._controller.SelectKind(k.value)

    def _write_apt(self, a: Aperture):
        if not isinstance(a, Aperture):
            raise TypeError("Expected an aperture")
        self._cache.pop("size", None)
        self._controller.SelectExpKind(a.value)

    def _read_position(self) -> tuple[int, int]:
        pos = self._controller.GetPosition()
        return pos[0], pos[1]

    def _write_position(self, pos: tuple[int, int]):
        if any(i > 4095 or i < 0 for i in pos):
            raise ValueError("Position should be between 0 and 4095")
        elif len(pos) != 2:
            raise ValueError("Position should be a 2-element tuple")
        self._controller.SetPosition(*pos)
