"""
Module to facilitate detector control.
"""

import numpy as np

from modular_qt.cv_oop import Image
from . import __online__

if __online__:
    from .PyJEM import detector
    from .PyJEM.TEM3 import Detector3
else:
    from .PyJEM.offline import detector
    from .PyJEM.offline.TEM3 import Detector3
from ._controller import ControllerBase, validators
from ._enums import *


class Controller(ControllerBase):
    """
    Concrete subclass to control the detector.

    Keys:
        * scan_mode (ScanMode): The imaging mode
        * scan_size (int): The size of the scan in pixels
        * dwell_time (int): The exposure time
        * frame_integration (int): The integration of successive frames
        * position (tuple[int, int]): The cartesian pixel co-ordinates of the next scan
        * detector (Detector): The currently selected detector
        * inserted (bool): Whether the detector is inserted
        * brightness (int): The brightness of the scan. It should be 0 – 4095
        * contrast (int): The contrast of the scan. It should be 0 – 4095
    """

    @property
    def detector_states(self) -> dict[Detector, bool]:
        """
        The insertion state of each detector.

        :return: A dictionary of detector to state.
        """
        return {det: bool(self._alt.GetPosition(det.value)) for det in Detector}

    @staticmethod
    def validators() -> dict[str, validators.Pipeline]:
        return dict(
            scan_mode=validators.Pipeline.enum(ScanMode),
            scan_size=validators.xmpls.any_int,
            dwell_time=validators.Pipeline.bound_int(validators.RangeValidator(0, 1000)),
            frame_integration=validators.xmpls.colour,
            position=validators.xmpls.two_elem_int,
            detector=validators.Pipeline.enum(Detector),
            inserted=validators.xmpls.any_bool,
            brightness=validators.xmpls.low_int,
            contrast=validators.xmpls.low_int
        )

    def __init__(self, det: Detector, *, scan_size: int = None, initial_mode: ScanMode = None,
                 initial_dwell_time: float = None, initial_integration: int = None, initial_pos: tuple[int, int] = None,
                 brightness: int = None, contrast: int = None):
        self._main = detector.Detector(det.name)
        self._alt = Detector3()
        self._detector = det
        super().__init__(
            "detector",
            scan_mode=(self._read_mode, self._change_scan),
            scan_size=(self._read_size, self._change_size),
            dwell_time=(self._read_dwell, self._main.set_exposuretime_value),
            frame_integration=(self._read_frames, self._main.set_frameintegration),
            position=(self._read_pos, self._move),
            detector=(lambda: self._detector, self._change_active),
            inserted=(lambda: bool(self._alt.GetPosition(self._detector.value)),
                      lambda state: self._alt.SetPosition(self._detector.value, state)),
            brightness=(lambda: self._alt.GetBrt(self._detector.value), self._write_brightness),
            contrast=(lambda: self._alt.GetCont(self._detector.value), self._write_contrast),
        )
        if initial_mode is not None:
            self["scan_mode"] = initial_mode
        if scan_size is not None:
            self["scan_size"] = scan_size
        if initial_dwell_time is not None:
            self["dwell_time"] = initial_dwell_time
        if initial_integration is not None:
            self["frame_integration"] = initial_integration
        if initial_pos is not None:
            self["position"] = initial_pos
        if brightness is not None:
            self["brightness"] = brightness
        if contrast is not None:
            self["contrast"] = contrast
        self["inserted"] = True

    def _read_mode(self) -> ScanMode:
        return ScanMode(self._main.get_detectorsetting()["scanMode"])

    def _read_size(self) -> tuple[int, int]:
        key = "ImagingArea"
        if self["scan_mode"] == ScanMode.AREA:
            key = f"AreaMode{key}"
        all_settings = self._main.get_detectorsetting()[key]
        return all_settings["Width"], all_settings["Height"]

    def _read_dwell(self) -> float:
        return self._main.get_detectorsetting()["ExposureTimeValue"]

    def _read_frames(self) -> int:
        return self._main.get_detectorsetting()["frameIntegration"]

    def _read_pos(self) -> tuple[int, int]:
        key = "ImagingArea"
        if self["scan_mode"] == ScanMode.AREA:
            key = f"AreaMode{key}"
        all_settings = self._main.get_detectorsetting()[key]
        return all_settings["X"], all_settings["Y"]

    def _change_scan(self, mode: ScanMode):
        if not isinstance(mode, ScanMode):
            raise TypeError("Expected a scan mode")
        self._main.set_scanmode(mode.value)

    def _change_size(self, size: int):
        if not isinstance(size, int):
            raise TypeError("Expected an integer")
        if self["scan_mode"] == ScanMode.FULL:
            setter = self._main.set_imaging_area
        elif self["scan_mode"] == ScanMode.AREA:
            setter = self._main.set_areamode_imagingarea
        else:
            raise TypeError("Unable to change size in 'spot' mode")
        setter(size, size)

    def _move(self, pos: tuple[int, int]):
        if not isinstance(pos, tuple) or len(pos) != 2:
            raise TypeError("Expected a 2-element tuple")
        if self["scan_mode"] == ScanMode.FULL:
            func = self._main.set_imaging_area
        elif self["scan_mode"] == ScanMode.AREA:
            func = self._main.set_areamode_imagingarea
        else:
            raise TypeError("Unable to move in 'spot' mode")
        func(self["scan_size"], self["scan_size"], *pos)

    def _change_active(self, det: Detector):
        if not isinstance(det, Detector):
            raise TypeError("Expected a detector")
        self._main = detector.Detector(det.name)
        self._detector = det
        self["inserted"] = True
        self._cache.pop("brightness", None)
        self._cache.pop("contrast", None)

    def _write_brightness(self, amount: int):
        if amount < 0 or amount > 4095:
            raise ValueError("Brightness should be between 0 and 4095")
        self._alt.SetBrt(self._detector.value, amount)

    def _write_contrast(self, amount: int):
        if amount < 0 or amount > 4095:
            raise ValueError("Contrast should be between 0 and 4095")
        self._alt.SetCont(self._detector.value, amount)

    def scan(self, *, normalise=True) -> Image:
        """
        Performs a scan from the detector.

        :param normalise: Whether to normalise the image to a range of 0 to 255 (traditional colour range.)
        :return: The image scanned from the microscope.
        """
        image = np.frombuffer(self._main.snapshot_rawdata(), np.uint16).reshape((self["size"], self["size"]))
        if normalise:
            image = ((image / np.max(image)) * 255).astype(np.uint8)
        return Image(image)
