"""
Module to facilitate scan control
"""

from . import __online__

if __online__:
    from .PyJEM.TEM3 import Scan3
else:
    from .PyJEM.offline.TEM3 import Scan3
from ._controller import ControllerBase, MappedSetter, MappedGetter, validators


class Controller(ControllerBase):
    """
    Concrete subclass to control the scan.

    Keys:
        * external (bool): Whether the scan is external
        * mag_adjust_h (int): The horizontal magnification adjustment should be between 0 and 65535
        * mag_adjust_v (int): The vertical magnification adjustment should be between 0 and 65535
        * rot_adjust_h (int): The horizontal rotation adjustment should be between 0 and 65535
        * rot_adjust_v (int): The vertical rotation adjustment should be between 0 and 65535
        * cor_adjust_h (int): The horizontal correction adjustment should be between 0 and 65535
        * cor_adjust_v (int): The vertical correction adjustment should be between 0 and 65535
        * off_adjust_h (int): The horizontal offset adjustment should be between 0 and 65535
        * off_adjust_v (int): The vertical offset adjustment should be between 0 and 65535
        * solid_rotation (int): The solid rotation angle. It should be 0-359
        * mag_adjust (tuple[int, int]): Shortcut for adjusting horizontal and vertical magnification
        * rot_adjust (tuple[int, int]): Shortcut for adjusting horizontal and vertical rotation
        * cor_adjust (tuple[int, int]): Shortcut for adjusting horizontal and vertical correction
        * off_adjust (tuple[int, int]): Shortcut for adjusting horizontal and vertical offset
    """

    @staticmethod
    def validators() -> dict[str, validators.Pipeline]:
        return dict(
            external=validators.xmpls.any_bool,
            mag_adjust_h=validators.xmpls.high_int,
            mag_adjust_v=validators.xmpls.high_int,
            rot_adjust_h=validators.xmpls.high_int,
            rot_adjust_v=validators.xmpls.high_int,
            cor_adjust_h=validators.xmpls.high_int,
            cor_adjust_v=validators.xmpls.high_int,
            off_adjust_h=validators.xmpls.high_int,
            off_adjust_v=validators.xmpls.high_int,
            solid_rotation=validators.xmpls.angle,
            mag_adjust=validators.xmpls.high_tuple,
            rot_adjust=validators.xmpls.high_tuple,
            cor_adjust=validators.xmpls.high_tuple,
            off_adjust=validators.xmpls.high_tuple,
        )

    def __init__(self, *, mag_adjust: tuple[int, int] = None, rotation_adjust: tuple[int, int] = None,
                 correction_adjust: tuple[int, int] = None, offset_adjust: tuple[int, int] = None):
        self._controller = Scan3()
        self._mag = list(mag_adjust or (-1, -1))
        self._rotation = list(rotation_adjust or (-1, -1))
        self._correction = list(correction_adjust or (-1, -1))
        self._offset = list(offset_adjust or (-1, - 1))
        super().__init__(
            "scan",
            external=(lambda: bool(self._controller.GetExtScanMode()), self._controller.SetExtScanMode),
            mag_adjust_h=self._read_write(self._mag, 0),
            mag_adjust_v=self._read_write(self._mag, 1),
            rot_adjust_h=self._read_write(self._rotation, 2),
            rot_adjust_v=self._read_write(self._rotation, 3),
            cor_adjust_h=self._read_write(self._correction, 4),
            cor_adjust_v=self._read_write(self._correction, 5),
            off_adjust_h=self._read_write(self._offset, 6),
            off_adjust_v=self._read_write(self._offset, 7),
            solid_rotation=(self._controller.GetRotationAngle, self._controller.SetRotationAngle),
            mag_adjust=self._2d("mag"),
            rot_adjust=self._2d("rot"),
            cor_adjust=self._2d("cor"),
            off_adjust=self._2d("off"),
        )
        if mag_adjust is not None:
            self["mag_adjust"] = mag_adjust
        if rotation_adjust is not None:
            self["rot_adjust"] = rotation_adjust
        if correction_adjust is not None:
            self["cor_adjust"] = correction_adjust
        if offset_adjust is not None:
            self["off_adjust"] = offset_adjust

    def _read_write(self, li: list[int], mode: int) -> tuple[MappedGetter, MappedSetter]:
        i = mode % 2

        def _read():
            if (ans := li[i]) == -1:
                raise ValueError("No data available for specified adjustment")
            return ans

        def _write(val: int):
            if not (0 <= val <= 65535):
                raise ValueError(f"Value {val!r} out of range")
            elif not isinstance(val, int):
                raise TypeError("Expected an integer")
            self._controller.SetScanDataAbs(mode, val)
            li[i] = val

        return _read, _write

    def _2d(self, name: str) -> tuple[MappedGetter, MappedSetter]:
        h = f"{name}_adjust_h"
        v = f"{name}_adjust_v"

        def _read() -> tuple[int, int]:
            return self[h], self[v]

        def _write(hv: tuple[int, int]):
            self[h], self[v] = hv

        return _read, _write
