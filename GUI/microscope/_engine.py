import numpy as np
from pyscanengine import ScanEngine
from pyscanengine.data.frame_monitor import FrameMonitor

from ._utils import *
from .. import validation
from ..images import GreyImage

valid_type = validation.Pipeline(
    validation.Step(validation.TypeValidator(ScanType)),
    in_type=ScanType, out_type=ScanType)


class Scanner:
    ABSOLUTE = -1

    @Key
    def scan_area(self) -> ScanType:
        return self._region

    @scan_area.setter
    def scan_area(self, value: ScanType):
        valid_type.validate(value)
        self._region = value
        self._engine.set_image_size(*value.size)
        self._engine.set_image_area(*value.size, *value.rect())

    @Key
    def dwell_time(self) -> float:
        return self._engine.pixel_time

    @dwell_time.setter
    def dwell_time(self, dwell_time: float):
        validation.examples.dwell_time.validate(dwell_time)
        self._engine.pixel_time = dwell_time

    @Key
    def flyback(self) -> float:
        return self._engine.get_inhibit_time()

    @flyback.setter
    def flyback(self, flyback: float):
        self._inhibit.validate(flyback)
        self._engine.set_inhibit_time(flyback)

    def __init__(self, scan_area: ScanType, negative_value=0, dwell_time: float = None,
                 flyback: float = None):
        self._inhibit = validation.examples.any_float + validation.Pipeline(
            validation.Step(validation.DynamicUpperBoundValidator(lambda: self.dwell_time, inclusive=False)),
            in_type=float, out_type=float
        )
        self._engine = ScanEngine(1)
        self.scan_area = scan_area
        if dwell_time is not None:
            self.dwell_time = dwell_time
        if flyback is not None:
            self.flyback = flyback
        self._handle_neg = negative_value
        if negative_value < 0 and negative_value != self.ABSOLUTE:
            raise ValueError("Cannot have negative handler that's negative")

        self._engine.set_enabled_inputs([2, 3])  # add proper support for inputs

    def set_pattern(self, arr: np.ndarray):
        pass  # add proper encoding support

    def scan(self) -> GreyImage:
        monitor = FrameMonitor(*self._region.size, inputs=[2, 3], max_queue_size=1)
        monitor.register(self._engine)
        self._engine.start_imaging(0)
        self._engine.stop_imaging()
        monitor.wait_for_image()
        image = monitor.pop().get_input_data(3)

        p_img = np.where(image < 0, self._handle_neg if self._handle_neg != self.ABSOLUTE else np.abs(image), image)
        p_img = p_img.astype(np.float32)

        p_img = ((p_img / np.max(p_img)) * 255).astype(np.uint8)

        return GreyImage(p_img)

    switch_scan_area = scan_area.switch
    switch_dwell_time = dwell_time.switch
    switch_flyback = flyback.switch
