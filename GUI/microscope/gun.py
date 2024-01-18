"""
Module to facilitate gun-control.
"""
import functools

from . import __online__
from .. import validators

if __online__:
    from .PyJEM.TEM3 import GUN3
else:
    from .PyJEM.offline.TEM3 import GUN3
from ._enums import *
from ._controller import ControllerBase


class Controller(ControllerBase):
    """
    Concrete subclass to control the gun.

    Keys:
        * wobbler (Wobbler): The wobbler to control
        * status (ProcessStatus): The status of the current wobbler
        * a1 (float, read-only): The value of the first anode
        * a2 (float, read-only): The value of the second anode
        * emission (float, read-only): The value of the emission in micro-amps
        * filament (float, read-only): The value of the filament
    """

    @staticmethod
    def validators() -> dict[str, validators.Pipeline]:
        return dict(
            wobbler=validators.Pipeline.enum(Wobbler),
            status=validators.Pipeline.enum(ProcessStatus),
        )

    def __init__(self, wobbler: Wobbler):
        self._controller = GUN3()
        self._wobblers = {Wobbler.HT: ProcessStatus.IDLE, Wobbler.ANODE: ProcessStatus.IDLE}
        self._wobbler = wobbler
        super().__init__(
            "gun",
            wobbler=(lambda: self._wobbler, self._write_wobbler),
            status=(lambda: self._wobblers[self._wobbler], self._control_wobbler),
            a1=(self._controller.GetAnode1CurrentValue, None),
            a2=(self._controller.GetAnode2CurrentValue, None),
            emission=(self._controller.GetEmissionCurrentValue, None),
            filament=(self._controller.GetFilamentCurrentValue, None),
        )
        for off in self._wobblers:
            self["wobbler"] = off
        self["wobbler"] = wobbler

    def flash_tip(self):
        """
        Procedure to flash the tip of the gun and refresh emission.
        """
        raise NotImplementedError("No flashing yet")

    def shift_anode(self, by: int, *, mode=Shift.ABSOLUTE):
        """
        Shift the value of the a2 anode by a given amount. Can be relative or absolute shift.

        :param by: The amount to shift by.
        :param mode: Whether it is relative (shift by) or absolute (shift to).
        """
        if mode == Shift.ABSOLUTE:
            setter = self._controller.SetA2Abs
        else:
            setter = self._controller.SetA2Rel
        setter(by)

    def _control_wobbler(self, on: ProcessStatus):
        if on == ProcessStatus.ERR:
            raise ValueError("Cannot set wobbler to error")
        if self._wobbler == Wobbler.HT:
            wobble_control = self._controller.SetHtWobbler
        else:
            wobble_control = self._controller.SetA2Wobbler
        wobble_control(on.value)

    def _write_wobbler(self, wobbler: Wobbler):
        self._wobbler = wobbler
        self["status"] = ProcessStatus.IDLE
