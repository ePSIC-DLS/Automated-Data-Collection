from .._base import Base
from .._utils import *
from ... import validation
from typing import Tuple as _tuple

if ONLINE:
    from PyJEM.TEM3 import EOS3


class EOS3Offline:
    """
    Placeholder class to represent an offline connection to the EOS system.
    """

    def GetMagValue(self) -> _tuple[str, str, str]:
        """
        Get the magnification value.

        Returns
        -------
        tuple[str, str, str]
            A tuple of strings representing the magnification value, an 'X' and a combination of the first two elements.
        """
        return "20000", "X", "X20000"

    def SetSelector(self, new: int):
        """
        Set the magnification value.

        Parameters
        ----------
        new: int
            The index of the magnification value.
        """
        pass

    def GetStemCamValue(self) -> _tuple[str, str, str]:
        """
        Get the camera length.

        Returns
        -------
        tuple[str, str, str]
            A tuple of strings representing the camera length, an 'X' and a combination of the first two elements.
        """
        return "20000", "X", "X20000"

    def SetStemCamSelector(self, new: int):
        """
        Set the camera length.

        Parameters
        ----------
        new: int
            The index of the camera length.
        """
        pass

    def SetObjFocus(self, new: int):
        """
        Set the objective focusing value.

        Parameters
        ----------
        new: int
            The new focus value.
        """
        pass


mag_vals = validation.ContainerValidator(
    int(20e3), int(25e3), int(30e3), int(40e3), int(50e3), int(60e3), int(80e3), int(100e3), int(120e3), int(150e3),
    int(200e3), int(250e3), int(300e3), int(400e3), int(500e3), int(600e3), int(800e3), int(1e6), int(1.2e6),
    int(1.5e6), int(2e6), int(2.5e6), int(3e6), int(4e6), int(5e6), int(6e6), int(8e6), int(10e6), int(12e6), int(15e6),
    int(20e6), int(25e6), int(30e6), int(40e6), int(50e6), int(60e6), int(80e6), int(100e6), int(120e6), int(150e6)
)

magnification = validation.examples.any_int + validation.Pipeline(
    validation.Step(mag_vals),
    in_type=int, out_type=int
)


class Controller(Base):
    """
    Concrete controller to control the EOS.

    Keys
    ----
    magnification: int (magnification validation)
        The current magnification value.
    camera_length: int (magnification validation)
        The current camera length.
    """

    @Key
    def magnification(self) -> int:
        """
        Public access to the magnification of the microscope.

        Returns
        -------
        int
            The current magnification value. Note that when offline, it returns twenty thousand as a default value.
        """
        return int(self._controller.GetMagValue()[0])

    @magnification.setter
    def magnification(self, value: int):
        magnification.validate(value)
        new = self._vals.index(value)
        self._controller.SetSelector(new)

    @Key
    def camera_length(self) -> int:
        """
        Public access to the camera length of the microscope.

        Returns
        -------
        int
            The current camera length. Note that when offline, it returns twenty thousand as a default value.
        """
        return int(self._controller.GetStemCamValue()[0])

    @camera_length.setter
    def camera_length(self, value: int):
        magnification.validate(value)
        new = self._vals.index(value)
        self._controller.SetStemCamSelector(new)

    def __init__(self, curr_mag: int = None, curr_length: int = None):
        super().__init__("EOS")
        if ONLINE:
            self._controller = EOS3()
        else:
            self._controller = EOS3Offline()
        self._vals = mag_vals.values
        if curr_mag is not None:
            self.magnification = curr_mag
        if curr_length is not None:
            self.camera_length = curr_length
        _ = self.magnification, self.camera_length  # this will prime the keys with an instance

    def adjust_focus(self, new: int):
        """
        Adjust the objective focus. Note that this undergoes obj_focus validation.

        Parameters
        ----------
        new: int
            The new objective focus value.
        """
        validation.examples.obj_focus.validate(new)
        self._controller.SetObjFocus(new)

    switch_magnification = magnification.switch
    switch_camera_length = camera_length.switch
