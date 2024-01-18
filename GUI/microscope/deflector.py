"""
Module to facilitate deflector control
"""

from . import __online__

if __online__:
    from .PyJEM.TEM3 import Def3
else:
    from .PyJEM.offline.TEM3 import Def3
from ._controller import ControllerBase, MappedSetter, MappedGetter, validators
from ._enums import *


class Controller(ControllerBase):
    """
    Concrete subclass to control the deflectors.

    Keys:
        * deflector (Deflector): The currently selected deflector
        * value (tuple[int, int]): The deflector value for currently selected deflector
        * info (list[int], read-only): The information of the currently selected deflector
        * shift_balance (tuple[int, int]): The value for shift balance. It should be 0-65535
        * tilt_balance (tuple[int, int]): The value for tilt balance. It should be 0-65535
        * angle_balance (tuple[int, int]): The value for angle balance. It should be 0-65535
        * alignment (tuple[int, int]): The value for the alignment of the deflector. It should be 0-65535
        * blanked (bool): Whether the beam is blanked
    """

    @staticmethod
    def validators() -> dict[str, validators.Pipeline]:
        return dict(
            deflector=validators.Pipeline.enum(Deflector),
            value=validators.xmpls.high_tuple,
            shift_balance=validators.xmpls.high_tuple,
            tilt_balance=validators.xmpls.high_tuple,
            angle_balance=validators.xmpls.high_tuple,
            alignment=validators.xmpls.high_tuple,
            blanked=validators.xmpls.any_bool
        )

    @property
    def map(self) -> dict[Deflector, str]:
        """
        A map of deflector to their key in the hardware.

        :return: A dictionary mapping deflectors to their corresponding hardware control key
        """
        return {
            Deflector.GUN1: "GunA1",
            Deflector.GUN2: "GunA2",
            Deflector.SPA: "SpotA",
            Deflector.ISC1: "IS1",
            Deflector.ISC2: "IS2",
            Deflector.CLS: "CLs",
            Deflector.ILS: "ILs",
            Deflector.OLS: "OLs",
            Deflector.FLS1: "FLs1",
            Deflector.FLS2: "FLs2",
            Deflector.SCAN1: "Scan1",
            Deflector.SCAN2: "Scan2",
            Deflector.IS_ASID: "StemIS",
            Deflector.CORRECTION: "Correction",
            Deflector.MAG_ADJUST: "MagAdjust",
            Deflector.OFFSET: "Offset",
            Deflector.ROTATION: "Rotation",
        }

    def __init__(self, aligner: Deflector, *, blank=False):
        self._controller = Def3()
        self._blank_status = blank
        self._def = aligner
        super().__init__(
            "deflector",
            deflector=(lambda: self._def, self._write_deflector),
            value=(self._read_info, self._write_info),
            info=(lambda: self._controller.GetDefInfo(self._def.value), None),
            shift_balance=self._read_write("ShifBal"),
            tilt_balance=self._read_write("TiltBal"),
            angle_balance=self._read_write("AngBal"),
            alignment=(self._read_alignment,
                       lambda pos: self._controller.SetDetAlign(self._def.value, *pos)),
            blanked=(lambda: self._blank_status, self._control_blank)
        )
        self["blanked"] = blank

    def toggle_beam(self):
        """
        Toggle the blanked state of the beam.
        """
        self["blanked"] = not self._blank_status

    def change_NTRL(self, for_: Deflector = None):
        """
        Change the NTRL for the given deflector.

        :param for_: The deflector to change information about. Defaults to the currently selected deflector.
        """
        if for_ is None:
            for_ = self._def
        self._controller.SetNtrl(for_.value)

    def STEM_beam_tilt(self, pos: tuple[int, int]):
        """
        Set the beam tilt for STEM mode.

        :param pos: The cartesian tilt.
        """
        self._controller.SetStemBeamTiltRel(*pos)

    def STEM_stig_b2(self, pos: tuple[int, int]):
        """
        Set the b2 stig for STEM mode.

        :param pos: The cartesian stig b2.
        """
        self._controller.SetStemStigB2Rel(*pos)

    def STEM_user_bshift(self, pos: tuple[int, int]):
        """
        Set the user b-shift for STEM mode.

        :param pos: The cartesian user b-shift.
        """
        self._controller.SetStemUserBShiftRel(*pos)

    def TEM_d_stig(self, pos: tuple[int, int]):
        """
        Set the d-stig for TEM mode.

        :param pos: The cartesian d-stig.
        """
        self._controller.SetTemDiStigRel(*pos)

    def TEM_d_shift(self, pos: tuple[int, int]):
        """
        Set the d-shift for TEM mode.

        :param pos: The cartesian d-shift.
        """
        self._controller.SetTemDShiftRel(*pos)

    def coarse_align1(self, pos: tuple[int, int], mode: ImagingMode):
        """
        Set the coarse alignment for either TEM or STEM mode.

        :param pos: The cartesian coarse alignment.
        :param mode: The mode to adjust.
        """
        if mode == ImagingMode.TEM:
            self._controller.SetTemA1CoarseRel(*pos)
        else:
            self._controller.SetStemA1CoarseRel(*pos)

    def stig_align1(self, pos: tuple[int, int], mode: ImagingMode):
        """
        Set the stig alignment for either TEM or STEM mode.

        :param pos: The cartesian stig alignment.
        :param mode: The mode to adjust.
        """
        if mode == ImagingMode.STEM:
            self._controller.SetStemStigA1Rel(*pos)
        else:
            self._controller.SetTemStigA1Rel(*pos)

    def _write_deflector(self, new: Deflector):
        if not isinstance(new, Deflector):
            raise TypeError("Expected deflector")
        self._cache.pop("alignment", None)
        self._def = new

    def _read_info(self) -> tuple[int, int]:
        if self._def in {Deflector.CMT_A, Deflector.CMP_S, Deflector.CMP_T}:
            raise TypeError(f"Cannot read information for {self._def}")
        name = self.map.get(self._def, self._def.name)
        reader = getattr(self._controller, f"Get{name}")
        ans = reader()
        return ans[0], ans[1]

    def _write_info(self, xy: tuple[int, int]):
        if self._def in {Deflector.CORRECTION, Deflector.MAG_ADJUST, Deflector.OFFSET, Deflector.ROTATION,
                         Deflector.CMT_A, Deflector.CMP_S, Deflector.CMP_T}:
            raise TypeError(f"Cannot change information for {self._def}")
        if any(value < 0 or value > 65535 for value in xy):
            raise ValueError("Co-ordinates must be between 0 and 65535")
        elif len(xy) != 2:
            raise ValueError("Expected a 2-element tuple")
        name = self.map.get(self._def, self._def.name)
        writer = getattr(self._controller, f"Set{name}")
        writer(*xy)

    def _control_blank(self, new: bool):
        self._blank_status = new
        self._controller.SetBeamBlank(int(new))

    def _read_write(self, name: str) -> tuple[MappedGetter, MappedSetter]:
        reader = getattr(self._controller, f"Get{name}")
        writer = getattr(self._controller, f"Set{name}")

        def _read() -> tuple[int, int]:
            ans = reader()
            return ans[0], ans[1]

        def _write(xy: tuple[int, int]):
            if any(value < 0 or value > 65535 for value in xy):
                raise ValueError("Co-ordinates must be between 0 and 65535")
            elif len(xy) != 2:
                raise ValueError("Expected a 2-element tuple")
            writer(*xy)

        return _read, _write

    def _read(self, name: str) -> tuple[MappedGetter, None]:
        reader = getattr(self._controller, f"Get{name}")

        def _read() -> tuple[int, int]:
            ans = reader()
            return ans[0], ans[1]

        return _read, None

    def _read_alignment(self) -> tuple[int, int]:
        ans = self._controller.GetDetAlign(self._def.value)
        return ans[0], ans[1]
