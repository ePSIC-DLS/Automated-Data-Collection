from .._base import Base
from .._utils import *
from ... import validation

from typing import Tuple as _tuple

if ONLINE:
    from PyJEM.TEM3 import Def3


class Def3Offline:
    """
    Placeholder class to represent an offline connection to the deflectors.
    """

    def GetPLA(self) -> _tuple[int, int]:
        """
        Get the value of the PLA deflector.

        Returns
        -------
        tuple[int, int]
            The PLA value.
        """
        return 0, 0

    def SetPLA(self, x: int, y: int):
        """
        Set the value of the PLA deflector.

        Parameters
        ----------
        x: int
            The PLA x-value.
        y: int
            The PLA y-value.
        """
        pass

    def GetBeamBlank(self) -> int:
        """
        Get whether the beam is blanked.

        Returns
        -------
        bool
            The blanked flag.
        """
        return 1

    def SetBeamBlank(self, new: int):
        """
        Set the value of the beam blank.

        Parameters
        ----------
        new: int
            The blanked flag.
        """
        pass

    def SetTemA1CoarseRel(self, x: int, y: int):
        """
        Set the value of the TEM A1. This is a relative, coarse adjustment.

        Parameters
        ----------
        x: int
            The TEM A1 x-value.
        y: int
            The TEM A2 y-value.
        """
        pass

    def SetStemA1CoarseRel(self, x: int, y: int):
        """
        Set the value of the STEM A1. This is a relative, coarse adjustment.

        Parameters
        ----------
        x: int
            The STEM A1 x-value.
        y: int
            The STEM A2 y-value.
        """
        pass

    def SetStemStigA1Rel(self, x: int, y: int):
        """
        Set the value of the STEM A1. This is a relative, stig adjustment.

        Parameters
        ----------
        x: int
            The STEM A1 x-value.
        y: int
            The STEM A2 y-value.
        """
        pass

    def SetTemStigA1Rel(self, x: int, y: int):
        """
        Set the value of the TEM A1. This is a relative, stig adjustment.

        Parameters
        ----------
        x: int
            The TEM A1 x-value.
        y: int
            The TEM A2 y-value.
        """
        pass


class Controller(Base):
    """
    Concrete controller for the microscope deflector.

    Keys
    ----
    value: tuple[int, int] (int16 validation on each element)
        The PLA deflector value.
    blanked: bool (boolean validation)
        Whether the beam is blanked.
    """

    @Key
    def value(self) -> _tuple[int, int]:
        """
        Public access to the deflector value.

        Returns
        -------
        tuple[int, int]
            The PLA deflector value.
        """
        v = self._controller.GetPLA()
        return v[0], v[1]

    @value.setter
    def value(self, value: _tuple[int, int]):
        for v in value:
            validation.examples.int16.validate(v)
        self._controller.SetPLA(*value)

    @Key
    def blanked(self) -> bool:
        """
        Public access to the blanking status.

        Returns
        -------
        bool
            Whether the beam is blanked.
        """
        return bool(self._controller.GetBeamBlank())

    @blanked.setter
    def blanked(self, value: bool):
        validation.examples.any_bool.validate(value)
        self._controller.SetBeamBlank(int(value))

    blanked.delay = 1.5 

    def __init__(self, beam_status: bool = None):
        super().__init__("Deflectors")
        if ONLINE:
            self._controller = Def3()
        else:
            self._controller = Def3Offline()
        if beam_status is not None:
            self.blanked = not beam_status
        _ = self.value, self.blanked  # this will prime the keys with an instance

    def toggle_beam(self):
        """
        Toggle the beam status.
        """
        self.blanked = not self.blanked

    def coarse_align(self, pos: _tuple[int, int], mode: ImagingMode):
        """
        Set the relative coarse alignment of the beam.

        Parameters
        ----------
        pos: tuple[int, int]
            The relative position of the beam. Undergoes int16 validation on each element.
        mode: ImagingMode
            The scan mode.
        """
        for v in pos:
            validation.examples.int16.validate(v)
        if mode == ImagingMode.TEM:
            self._controller.SetTemA1CoarseRel(*pos)
        else:
            self._controller.SetStemA1CoarseRel(*pos)

    def stig_align(self, pos: _tuple[int, int], mode: ImagingMode):
        """
        Set the relative stig alignment of the beam.

        Parameters
        ----------
        pos: tuple[int, int]
            The relative position of the beam. Undergoes int16 validation on each element.
        mode: ImagingMode
            The scan mode.
        """
        for v in pos:
            validation.examples.int16.validate(v)
        if mode == ImagingMode.STEM:
            self._controller.SetStemStigA1Rel(*pos)
        else:
            self._controller.SetTemStigA1Rel(*pos)

    switch_value = value.switch
    switch_blanked = blanked.switch
