from .._base import Base
from .._utils import *
from ... import validation

from typing import Tuple as _tuple

if ONLINE:
    from PyJEM.TEM3 import Def3
else:
    from ..PyJEM.offline.TEM3 import Def3


class Controller(Base):

    @Key
    def value(self) -> _tuple[int, int]:
        v = self._controller.GetPLA()
        return v[0], v[1]

    @value.setter
    def value(self, value: _tuple[int, int]):
        for v in value:
            validation.examples.int16.validate(v)
        self._controller.SetPLA(*value)

    @Key
    def blanked(self) -> bool:
        return bool(self._controller.GetBeamBlank())

    @blanked.setter
    def blanked(self, value: bool):
        validation.examples.any_bool.validate(value)
        self._controller.SetBeamBlank(int(value))

    blanked.delay = 1.5

    def __init__(self, beam_status: bool = None):
        super().__init__("Deflectors")
        self._controller = Def3()
        if beam_status is not None:
            self.blanked = not beam_status
        _ = self.value, self.blanked  # this will prime the keys with an instance

    def toggle_beam(self):
        self.blanked = not self.blanked

    def coarse_align(self, pos: _tuple[int, int], mode: ImagingMode):
        for v in pos:
            validation.examples.int16.validate(v)
        if mode == ImagingMode.TEM:
            self._controller.SetTemA1CoarseRel(*pos)
        else:
            self._controller.SetStemA1CoarseRel(*pos)

    def stig_align(self, pos: _tuple[int, int], mode: ImagingMode):
        for v in pos:
            validation.examples.int16.validate(v)
        if mode == ImagingMode.STEM:
            self._controller.SetStemStigA1Rel(*pos)
        else:
            self._controller.SetTemStigA1Rel(*pos)

    switch_value = value.switch
    switch_blanked = blanked.switch
