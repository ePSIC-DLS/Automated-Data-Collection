from typing import Tuple as _tuple

from .._base import Base
from .._utils import *
from ... import validation

if ONLINE:
    from PyJEM.TEM3 import Detector3
else:
    from ..PyJEM.offline.TEM3 import Detector3

detector = validation.Pipeline.enum(Detector)


class Controller(Base):

    @Key
    def current(self) -> Detector:
        return self._current

    @current.setter
    def current(self, value: Detector):
        detector.validate(value)
        self._current = value
        self.inserted = True

    @Key
    def inserted(self) -> bool:
        return bool(self._controller.GetPosition(self.current.value))

    @inserted.setter
    def inserted(self, value: bool):
        validation.examples.any_bool.validate(value)
        self._controller.SetPosition(self.current.value, int(value))

    @Key
    def brightness(self) -> int:
        return self._controller.GetBrt(self.current.value)

    @brightness.setter
    def brightness(self, value: int):
        validation.examples.int12.validate(value)
        self._controller.SetBrt(self.current.value, value)

    @Key
    def contrast(self) -> int:
        return self._controller.GetCont(self.current.value)

    @contrast.setter
    def contrast(self, value: int):
        validation.examples.int12.validate(value)
        self._controller.SetCont(self.current.value, value)

    def __init__(self, controlling: _tuple[Detector, bool]):
        super().__init__("Detectors")
        self._controller = Detector3()
        self.current = controlling[0]
        self.inserted = controlling[1]

    switch_detector = current.switch
    switch_inserted = inserted.switch
    switch_brightness = brightness.switch
    switch_contrast = contrast.switch
