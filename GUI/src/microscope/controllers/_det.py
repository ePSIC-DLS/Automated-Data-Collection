from typing import Tuple as _tuple

from .._base import Base
from .._utils import *
from ... import validation

if ONLINE:
    from PyJEM.TEM3 import Detector3
import time

class Detector3Offline:
    """
    Placeholder class to represent an offline connection to the detectors.
    """

    def GetPosition(self, for_: int) -> int:
        """
        Get the position of a certain detector.

        Parameters
        ----------
        for_: int
            The detector id.

        Returns
        -------
        int
            The position of the detector.
        """
        return 1

    def SetPosition(self, for_: int, inserted: int):
        """
        Set the position of a certain detector.

        Parameters
        ----------
        for_: int
            The detector id.
        inserted: int
            Whether the detector is inserted.
        """
        pass

    def GetBrt(self, for_: int) -> int:
        """
        Get the brightness of a certain detector.

        Parameters
        ----------
        for_: int
            The detector id.

        Returns
        -------
        int
            The brightness of the detector.
        """
        return 0

    def SetBrt(self, for_: int, brightness: int):
        """
        Set the brightness of a certain detector.

        Parameters
        ----------
        for_: int
            The detector id.
        brightness: int
            The brightness of the detector.
        """
        pass

    def GetCont(self, for_: int) -> int:
        """
        Get the contrast of a certain detector.

        Parameters
        ----------
        for_: int
            The detector id.

        Returns
        -------
        int
            The contrast of the detector.
        """
        return 0

    def SetCont(self, for_: int, contrast: int):
        """
        Set the contrast of a certain detector.

        Parameters
        ----------
        for_: int
            The detector id.
        contrast: int
            The contrast of the detector
        """
        pass


detector = validation.Pipeline.enum(Detector)


class Controller(Base):
    """
    Concrete controller for the detectors in the microscope.

    Keys
    ----
    current: Detector (enum validation)
        The current detector being controlled.
    inserted: bool (boolean validation)
        The insertion status of the detector.
    brightness: int (int12 validation)
        The brightness of the detector.
    contrast: int (int12 validation)
        The contrast of the detector.
    """

    @Key
    def current(self) -> Detector:
        """
        Public access to the current detector.

        Returns
        -------
        Detector
            The current detector being controlled.
        """
        return self._current

    @current.setter
    def current(self, value: Detector):
        detector.validate(value)
        self._current = value
        self.inserted = True

    @Key
    def inserted(self) -> bool:
        """
        Public access to the detector state.

        Returns
        -------
        bool
            The insertion status of the detector.
        """
        return bool(self._controller.GetPosition(self.current.value))

    @inserted.setter
    def inserted(self, value: bool):
        validation.examples.any_bool.validate(value)
        self._controller.SetPosition(self.current.value, int(value))

    inserted.delay = 4.5 #ZN added to enforce ADF1 isnertion wait time

    @Key
    def brightness(self) -> int:
        """
        Public access to the detector's brightness.

        Returns
        -------
        int
            The brightness of the detector.
        """
        return self._controller.GetBrt(self.current.value)

    @brightness.setter
    def brightness(self, value: int):
        validation.examples.int12.validate(value)
        self._controller.SetBrt(self.current.value, value)

    @Key
    def contrast(self) -> int:
        """
        Public access to the detector's contrast.

        Returns
        -------
        int
            The contrast of the detector.
        """
        return self._controller.GetCont(self.current.value)

    @contrast.setter
    def contrast(self, value: int):
        validation.examples.int12.validate(value)
        self._controller.SetCont(self.current.value, value)

    def __init__(self, controlling: _tuple[Detector, bool]):
        super().__init__("Detectors")
        if ONLINE:
            self._controller = Detector3()
        else:
            self._controller = Detector3Offline()
        self.current = controlling[0]
        self.inserted = controlling[1]
        _ = self.brightness, self.contrast  # this will prime the keys with an instance

    switch_detector = current.switch
    switch_inserted = inserted.switch
    switch_brightness = brightness.switch
    switch_contrast = contrast.switch
