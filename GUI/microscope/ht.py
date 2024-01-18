"""
Module to facilitate HT control
"""

from . import __online__

if __online__:
    from .PyJEM.TEM3 import HT3
else:
    from .PyJEM.offline.TEM3 import HT3
from ._controller import ControllerBase, validators


class Controller(ControllerBase):
    """
    Concrete subclass to control the HT.

    Keys:
        * value (float): The value of the acceleration voltage
    """

    @staticmethod
    def validators() -> dict[str, validators.Pipeline]:
        inst = HT3()

        def _l() -> float:
            return inst.GetHtRange()[1]

        def _h() -> float:
            return inst.GetHtRange()[0]

        return dict(
            value=validators.Pipeline(validators.Step.type(float, validators.DynamicRangeValidator(_l, _h)))
        )

    def __init__(self):
        self._controller = HT3()
        super().__init__(
            "ht",
            value=(self._controller.GetHtValue, self._controller.SetHtValue)
        )

    def valid_range(self) -> tuple[float, float]:
        """
        Retrieve the valid range of values that the key 'value' can take.

        :return: The lowest and highest valid value.
        """
        v_range = self._controller.GetHtRange()
        return v_range[1], v_range[0]
