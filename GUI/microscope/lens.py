"""
Module to facilitate lens control
"""

from . import __online__

if __online__:
    from .PyJEM.TEM3 import Lens3
else:
    from .PyJEM.offline.TEM3 import Lens3
from ._controller import ControllerBase, validators
from ._enums import *


class Controller(ControllerBase):
    """
    Concrete subclass to control the lenses.

    Keys:
        * lens (Lens): The currently selected lens
        * info (int): The absolute value of the current lens
        * free_lens_control (bool): Whether free lens control is enabled
        * super_fine_control (bool): Whether super fine lens control is enabled
        * super_fine_value (int): The super fine lens value
    """

    @staticmethod
    def validators() -> dict[str, validators.Pipeline]:
        return dict(
            lens=validators.Pipeline.enum(Lens),
            info=validators.xmpls.high_int,
            free_lens_control=validators.xmpls.any_bool,
            super_lens_control=validators.xmpls.any_bool,
            super_lens_value=validators.xmpls.high_int,
        )

    def __init__(self, initial_lens: Lens):
        self._controller = Lens3()
        self._lens = initial_lens
        super().__init__(
            "lens",
            lens=(lambda: self._lens, self._change_active),
            info=(lambda: self._controller.GetLensInfo(self._lens.value), self._write_info),
            free_lens_control=(lambda: bool(self._controller.GetFLCInfo(self._lens.value)),
                               lambda s: self._controller.SetFLCSw(self._lens.value, int(s))),
            super_fine_control=(lambda: bool(self._controller.GetOLSuperFineSw()),
                                lambda s: self._controller.SetOLSuperFineSw(int(s))),
            super_fine_value=(self._controller.GetOLSuperFineValue, self._controller.SetOLSuperFineValue)
        )

    def _change_active(self, new: Lens):
        if not isinstance(new, Lens):
            raise TypeError("Expected a lens")
        self._cache.pop("info", None)
        self._cache.pop("free_lens_control", None)
        self._lens = new

    def _write_info(self, value: int):
        if value < 0 or value > 65535:
            raise ValueError("Lens value must be between 0 and 65535")
        elif self._lens == Lens.FL_RATIO:
            raise TypeError("Cannot change FL ratio")
        name = self._lens.name.replace("_COARSE", "c").replace("_FINE", "f")
        setter = getattr(self._controller, f"Set{name}")
        setter(value)
