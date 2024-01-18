"""
Module to facilitate EOS control
"""

import typing
import enum

from . import __online__

if __online__:
    from .PyJEM.TEM3 import EOS3
else:
    from .PyJEM.offline.TEM3 import EOS3
from ._controller import ControllerBase, validators
from ._enums import *


class Controller(ControllerBase):
    """
    Concrete subclass to control the EOS.

    Keys:
        * magnification (int): The magnification of the microscope
        * imaging_mode (ImagingMode): The mode currently imaging in
        * probe_mode (ProbeMode): The mode of the probe
        * spot_size (int): The size of the spot
        * function (TEMFunction for TEM mode, STEMFunction for STEM mode): The imaging function to perform
        * alpha (int): The alpha number
    """

    @staticmethod
    def validators() -> dict[str, validators.Pipeline]:
        enum_name = validators.Branch(validators.Step(validators.StrictTypeValidator(enum.Enum)),
                                      validators.Step.pure_translator(validators.PropertyTranslator("name")),
                                      validators.Step.pure_translator(validators.FStringTranslator("\'{}\'")),
                                      safety=validators.TypeTranslator(str))
        from_name = (
                validators.Pipeline.prefixed_str("\'") +
                validators.Pipeline(validators.Step.pure_translator(validators.UnionMixinTranslator(
                    validators.EnumTranslator(TEMFunction),
                    validators.EnumTranslator(STEMFunction))))
        )
        return dict(
            magnification=validators.xmpls.magnification,
            imaging_mode=validators.Pipeline.enum(ImagingMode),
            probe_mode=validators.Pipeline.enum(ProbeMode),
            spot_size=validators.Pipeline.bound_int(validators.RangeValidator(6, 13)),
            function=enum_name + from_name,
            alpha=validators.Pipeline.bound_int(validators.RangeValidator(0, 8))
        )

    def __init__(self, *, spot_size: int = None, magnification: int = None, mode: ImagingMode = None,
                 probe: ProbeMode = None):
        self._values = validators.xmpls.magnification.values
        self._controller = EOS3()
        super().__init__(
            "eos",
            magnification=(self._read_magnification, self._write_magnification),
            imaging_mode=(lambda: ImagingMode(self._controller.GetTemStemMode()),
                          self._write_imaging_mode),
            probe_mode=(lambda: ProbeMode(self._controller.GetProbeMode()),
                        lambda prb: self._controller.SelectProbMode(prb.value)),
            spot_size=(lambda: self._controller.GetSpotSize() + 6,
                       lambda spt: self._controller.SelectSpotSize(spt - 6)),
            function=(self._read_function, self._write_function),
            alpha=(self._controller.GetAlpha, self._controller.SetAlphaSelector),
        )
        if spot_size is not None:
            self["spot_size"] = spot_size
        if magnification is not None:
            self["magnification"] = magnification
        if mode is not None:
            self["imaging_mode"] = mode
        if probe is not None:
            self["probe_mode"] = probe

    def _write_imaging_mode(self, new: ImagingMode):
        self._controller.SelectTemStem(new.value)
        self._cache.pop("magnification", None)
        self._cache.pop("function", None)

    def _read_magnification(self) -> int:
        if self._controller.GetTemStemMode():
            getter = self._controller.GetStemCamValue
        else:
            getter = self._controller.GetMagValue
        return int(getter()[0])

    def _write_magnification(self, new: int):
        new = self._values.index(new)
        if self._controller.GetTemStemMode():
            setter = self._controller.SetStemCamSelector
        else:
            setter = self._controller.SetSelector
        setter(new)

    def _read_function(self) -> typing.Union[TEMFunction, STEMFunction]:
        if self._controller.GetTemStemMode():
            cls = STEMFunction
        else:
            cls = TEMFunction
        return cls(self._controller.GetFunctionMode()[0])

    def _write_function(self, new: typing.Union[TEMFunction, STEMFunction]):
        if self._controller.GetTemStemMode():
            expected_cls = STEMFunction
            mode = "STEM"
        else:
            expected_cls = TEMFunction
            mode = "TEM"
        if not isinstance(new, expected_cls):
            raise TypeError(f"{mode} mode expects a {expected_cls}")
        self._controller.SelectFunctionMode(new.value)

    def down_mag(self, by=1):
        """
        Decrease magnification by a number of stages.

        :param by: The number of stages to decrease by. Should be positive.
        """
        if self._controller.GetTemStemMode():
            down = self._controller.DownStemCamSelector
        else:
            down = self._controller.DownSelector
        for _ in range(by):
            down()

    def up_mag(self, by=1):
        """
        Increase magnification by a number of stages.

        :param by: The number of stages to increase by. Should be positive.
        """
        if self._controller.GetTemStemMode():
            up = self._controller.UpStemCamSelector
        else:
            up = self._controller.UpSelector
        for _ in range(by):
            up()

    def change_focus(self, mode: Focus, amount: int):
        """
        Change focus.

        :param mode: The type of focus to change.
        :param amount: The new focus.
        """
        if not (1 <= abs(amount) <= 50):
            raise ValueError("Invalid amount. Should have an absolute value between 1 and 50")
        if mode == Focus.OBJ:
            setter = self._controller.SetObjFocus
        else:
            setter = self._controller.SetDiffFocus
        setter(amount)
