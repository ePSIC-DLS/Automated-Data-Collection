from .._base import Base
from .._utils import *
from ... import validation

if ONLINE:
    from PyJEM.TEM3 import Lens3


class Lens3Offline:
    """
    Placeholder class to represent an offline connection to the lenses.
    """

    def _lens(self) -> int:
        return 0xFFFF

    GetCL1 = _lens
    GetCL2 = _lens
    GetCL3 = _lens
    GetCM = _lens
    GetOLc = _lens
    GetOLf = _lens
    GetOM = _lens
    GetOM2 = _lens
    GetIL1 = _lens
    GetIL2 = _lens
    GetIL3 = _lens
    GetIL4 = _lens
    GetPL1 = _lens
    GetPL2 = _lens
    GetPL3 = _lens
    GetFLc = _lens
    GetFLf = _lens

    def SetCL3(self, value: int):
        """
        Set the value of the CL3 lens.

        Parameters
        ----------
        value: int
            The lens value.
        """
        pass

    def SetOLc(self, value: int):
        """
        Set the value of the OL coarse lens.

        Parameters
        ----------
        value: int
            The lens value.
        """
        pass

    def SetOLf(self, value: int):
        """
        Set the value of the OL fine lens.

        Parameters
        ----------
        value: int
            The lens value.
        """
        pass

    def SetOM(self, value: int):
        """
        Set the value of the OM lens.

        Parameters
        ----------
        value: int
            The lens value.
        """
        pass

    def SetFLc(self, value: int):
        """
        Set the value of the FL coarse lens.

        Parameters
        ----------
        value: int
            The lens value.
        """
        pass

    def SetFLf(self, value: int):
        """
        Set the value of the FL fine lens.

        Parameters
        ----------
        value: int
            The lens value.
        """
        pass


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
        if self._current == Lens.CL1:
            return self._controller.GetCL1()
        elif self._current == Lens.CL2:
            return self._controller.GetCL2()
        elif self._current == Lens.CL3:
            return self._controller.GetCL3()
        elif self._current == Lens.CM:
            return self._controller.GetCM()
        elif self._current == Lens.OL_COARSE:
            return self._controller.GetOLc()
        elif self._current == Lens.OL_FINE:
            return self._controller.GetOLf()
        elif self._current == Lens.OM1:
            return self._controller.GetOM()
        elif self._current == Lens.OM2:
            return self._controller.GetOM2()
        elif self._current == Lens.IL1:
            return self._controller.GetIL1()
        elif self._current == Lens.IL2:
            return self._controller.GetIL2()
        elif self._current == Lens.IL3:
            return self._controller.GetIL3()
        elif self._current == Lens.IL4:
            return self._controller.GetIL4()
        elif self._current == Lens.PL1:
            return self._controller.GetPL1()
        elif self._current == Lens.PL2:
            return self._controller.GetPL2()
        elif self._current == Lens.PL3:
            return self._controller.GetPL3()
        elif self._current == Lens.FL_COARSE:
            return self._controller.GetFLc()
        elif self._current == Lens.FL_FINE:
            return self._controller.GetFLf()

    @value.setter
    def value(self, value: int):
        if self._current == Lens.CL1:
            raise ValueError("Cannot set CL1 lens")
        elif self._current == Lens.CL2:
            raise ValueError("Cannot set CL2 lens")
        elif self._current == Lens.CL3:
            self._controller.SetCL3(value)
        elif self._current == Lens.CM:
            raise ValueError("Cannot set CM lens")
        elif self._current == Lens.OL_COARSE:
            self._controller.SetOLc(value)
        elif self._current == Lens.OL_FINE:
            self._controller.SetOLf(value)
        elif self._current == Lens.OM1:
            self._controller.SetOM(value)
        elif self._current == Lens.OM2:
            raise ValueError("Cannot set OM2 lens")
        elif self._current == Lens.IL1:
            raise ValueError("Cannot set IL1 lens")
        elif self._current == Lens.IL2:
            raise ValueError("Cannot set IL2 lens")
        elif self._current == Lens.IL3:
            raise ValueError("Cannot set IL3 lens")
        elif self._current == Lens.IL4:
            raise ValueError("Cannot set IL4 lens")
        elif self._current == Lens.PL1:
            raise ValueError("Cannot set PL1 lens")
        elif self._current == Lens.PL2:
            raise ValueError("Cannot set PL2 lens")
        elif self._current == Lens.PL3:
            raise ValueError("Cannot set PL3 lens")
        elif self._current == Lens.FL_COARSE:
            self._controller.SetFLc(value)
        elif self._current == Lens.FL_FINE:
            self._controller.SetFLf(value)

    def __init__(self, current: Lens):
        super().__init__("Lenses")
        if ONLINE:
            self._controller = Lens3()
        else:
            self._controller = Lens3Offline()
        self.current = current
        _ = self.value  # this will prime the keys with an instance

    switch_lens = current.switch
