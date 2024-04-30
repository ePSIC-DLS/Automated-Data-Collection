import typing
from typing import Optional as _None

import numpy as np
from pyscanengine import ScanEngine
from pyscanengine.data.frame_monitor import FrameMonitor

from ._utils import *
from .. import validation
from ..images import GreyImage

valid_type = validation.Pipeline(
    validation.Step(validation.TypeValidator(ScanType)),
    in_type=ScanType, out_type=ScanType)


class Connection:

    def __init__(self, engine: ScanEngine, notifier: "Scanner", line_index: int, mode: TTLMode, source: TriggerSource,
                 *, active: float = None, delay: float = None, count: int = None):
        for var, needed, desc in zip((active,
                                      delay,
                                      count),
                                     ({TTLMode.SOURCE_TIMED, TTLMode.SOURCE_TIMED_DELAY},
                                      {TTLMode.SOURCE_TIMED_DELAY},
                                      {TTLMode.PULSE_TRAIN, TTLMode.SOURCE_TRAIN}),
                                     ("time to be active for",
                                      "delay to activate after",
                                      "number of pulses")
                                     ):
            if mode in needed:
                if var is None:
                    raise ValueError(f"{mode} requires a {desc}")
            else:
                if var is not None:
                    raise ValueError(f"{mode} does not require a {desc}")
        self._engine = engine
        self._i = line_index
        self._line = "".join(map(str, map(int, (i == 9 - line_index for i in range(10)))))
        self._mode = mode.value
        self._source = source.value()
        self._kwargs = {}
        if active is not None:
            self._kwargs["on_time"] = active
        if delay is not None:
            self._kwargs["delay"] = delay
        if count is not None:
            self._kwargs["nb_pulses"] = count
        self._notifier = notifier

    def __enter__(self):
        self.activate()

    def __exit__(self, exc_type: typing.Type[Exception], exc_val: Exception, exc_tb):
        self.deactivate()

    def activate(self):
        self._engine.enable_lines(int(self._line, 2))
        self._engine.set_output_line_a(self._i, self._mode, self._source, **self._kwargs)
        self._notifier.add_line(self._i)

    def deactivate(self):
        self._engine.disable_lines(int(self._line, 2))
        self._engine.set_output_line_a(self._i, 0, self._source, **self._kwargs)
        self._notifier.remove_line(self._i)


class Scanner:

    @Key
    def scan_area(self) -> ScanType:
        return self._region

    @scan_area.setter
    def scan_area(self, value: ScanType):
        valid_type.validate(value)
        self._region = value
        self._engine.set_image_area(*value.size, *value.rect())

    @Key
    def dwell_time(self) -> float:
        return self._engine.pixel_time

    @dwell_time.setter
    def dwell_time(self, dwell_time: float):
        validation.examples.dwell_time.validate(dwell_time)
        self._engine.pixel_time = dwell_time
        self.flyback = 10 * dwell_time

    @Key
    def flyback(self) -> float:
        return self._engine.get_flyback_time()

    @flyback.setter
    def flyback(self, flyback: float):
        self._engine.set_flyback_time(flyback)
        # self._inhibit.validate(flyback)
        # self._engine.set_inhibit_time(flyback)

    @Key
    def lines(self) -> str:
        return "".join(self._lines)

    def __init__(self, full_scan: FullScan, dwell_time: float = None, flyback: float = None):
        self._inhibit = validation.examples.any_float + validation.Pipeline(
            validation.Step(validation.DynamicUpperBoundValidator(lambda: self.dwell_time, inclusive=False)),
            in_type=float, out_type=float
        )
        self._engine = ScanEngine(1)
        self._engine.set_image_size(*full_scan.size)
        self.scan_area = full_scan
        if dwell_time is not None:
            self.dwell_time = dwell_time
        if flyback is not None:
            self.flyback = flyback
        self._lines = ["0"] * 10

        self._engine.set_enabled_inputs([3])  # add proper support for inputs

    def inhibit_validation(self) -> validation.Pipeline:
        return self._inhibit

    def set_pattern(self, arr: np.ndarray):
        pass  # add proper encoding support

    def scan(self, *, return_=True) -> _None[GreyImage]:
        x_size, y_size = self._region.size
        sx, ex, sy, ey = self._region.rect()
        monitor = FrameMonitor(x_size + 1, y_size + 1, inputs=[3], max_queue_size=1)
        monitor.register(self._engine)
        self._engine.start_imaging(0)
        self._engine.stop_imaging()
        monitor.wait_for_image()
        if return_:
            image = monitor.pop().get_input_data(3)[sy:ey, sx:ex]

            img_min = np.abs(np.min(image))
            p_img = image.astype(np.float32) + img_min
            p_img = ((p_img / np.max(p_img)) * 255).astype(np.uint8)

            return GreyImage(p_img)

    def using_connection(self, line_index: int, mode: TTLMode, source: TriggerSource, *,
                         active: float = None, delay: float = None, count: int = None) -> Connection:
        return Connection(self._engine, self, line_index, mode, source, active=active, delay=delay, count=count)

    def add_line(self, i: int):
        self._lines[i] = "1"

    def remove_line(self, i: int):
        self._lines[i] = "0"

    switch_scan_area = scan_area.switch
    switch_dwell_time = dwell_time.switch
    switch_flyback = flyback.switch
