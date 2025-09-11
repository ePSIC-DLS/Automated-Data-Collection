import typing
from typing import Optional as _None, Dict as _dict, List as _list

import cv2
import numpy as np
from pyscanengine import ScanEngine
from pyscanengine.data.frame_monitor import FrameMonitor

from ._utils import *
from .. import validation
from ..images import GreyImage

if ONLINE:
    from PyJEM.detector import Detector as JEOLEngine

valid_type = validation.Pipeline(
    validation.Step(validation.TypeValidator(ScanType)),
    in_type=ScanType, out_type=ScanType)


class Connection:
    """
    A TTL connection to an external service.

    This connection can be activated and deactivated at will, and can be used as a context manager.

    Attributes
    ----------
    _engine: ScanEngine
        The scanner engine designed to make a connection work.
    _i: int
        The connection index.
    _line: str
        The connection string - it is a binary string representing the line integer.
    _mode: int
        The TTL mode integer.
    _source: int
        The trigger source integer.
    _kwargs: dict[str, float]
        The keyword-arguments for the output-line.
    _notifier: Scanner
        A notifier of the TTL signals.

    Parameters
    ----------
    engine: ScanEngine
        The scanner engine.
    notifier: Scanner
        The notifier of the TTL signals.
    line_index: int
        The index of the line to connect to. This controls the connection index and the line integer.
    mode: TTLMode
        The TTL mode to use for the connection.
    source: TriggerSource
        The trigger source to use for the connection.
    active: float | None
        The time for which this connection is active.
    delay: float | None
        The delay to activate after.
    count: int | None
        The number of pulses to emit.

    Raises
    ------
    ValueError
        If the optional parameters (active, delay, count) are provided when not needed.
        If the optional parameters (active, delay, count) are not provided when needed.
    """

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
        """
        Activate the connection, by enabling the specific line integer as an output in the engine.

        Will also register the activation with the notifier.
        """
        self._engine.enable_lines(int(self._line, 2))
        self._engine.set_output_line_a(self._i, self._mode, self._source, **self._kwargs)
        self._notifier.add_line(self._i)

    def deactivate(self):
        """
        Deactivate the connection, by disabling the specific line integer as an output in the engine.

        Will also register the deactivation with the notifier.
        """
        self._engine.disable_lines(int(self._line, 2))
        self._engine.set_output_line_a(self._i, 0, self._source, **self._kwargs)
        self._notifier.remove_line(self._i)


if QD:
    class OfflineEngine:
        """
        Placeholder class for the offline QD scanner engine.

        Attributes
        ----------
        pixel_time: float
            The pixel time in seconds.
        """

        def __init__(self):
            self.pixel_time = 0.0

        def set_enabled_inputs(self, inputs: _list[int]):
            """
            Set the enabled detectors.

            Parameters
            ----------
            inputs: list[int]
                The detector IDs.
            """
            pass

        def set_image_area(self, width: int, height: int, sx: int, ex: int, sy: int, ey: int):
            """
            Set the area for the scan.

            Parameters
            ----------
            width: int
                The rectangular width of the scan.
            height: int
                The rectangular height of the scan.
            sx: int
                The starting x coordinate of the scan.
            ex: int
                The ending x coordinate of the scan.
            sy: int
                The starting y coordinate of the scan.
            ey: int
                The ending y coordinate of the scan.
            """
            pass

        def get_flyback_time(self) -> float:
            """
            Get the flyback time. The flyback time is transition time per row of pixels.

            Returns
            -------
            float
                The flyback time.
            """
            return 0.0

        def set_flyback_time(self, flyback: float):
            """
            Set the flyback time.

            Parameters
            ----------
            flyback: float
                The transition time per row of pixels.
            """
            pass

        def disable_lines(self, lines: int):
            """
            Disable the connected lines.

            Parameters
            ----------
            lines: int
                The lines to disconnect.
            """
            pass

        def set_output_line_a(self, index: int, mode: int):
            """
            Configure output lines based on a specific index and mode.

            Parameters
            ----------
            index: int
                The lines to configure.
            mode: int
                The mode to enable.
            """
            pass


    class Scanner:
        """
        A scan engine that can encapsulates the Quantum Detectors scan engine.

        Keys
        ----
        scan_area: ScanType (type validation)
            The scan area covered by the engine.
        dwell_time: float (dwell_time validation)
            The dwell time in seconds.
        flyback: float (inhibit validation)
            The time spent in flyback (not scanning, but moving between pixels).
        lines: str (read-only)
            A binary string representing which connections are enabled.

        Attributes
        ----------
        _engine: ScanEngine
            The underlying engine.
        _lines: list[str]
            The list of binary markers to determine which connections are active.
        """

        @Key
        def scan_area(self) -> ScanType:
            """
            Public access to the area being used for the scan.

            Returns
            -------
            ScanType
                The scan area covered by the engine.
            """
            return self._region

        @scan_area.setter
        def scan_area(self, value: ScanType):
            valid_type.validate(value)
            self._region = value
            self._engine.set_image_area(*value.size, *value.rect())

        @Key
        def dwell_time(self) -> float:
            """
            Public access to the time spent scanning per pixel.

            Returns
            -------
            float
                The dwell time in seconds.
            """
            return self._engine.pixel_time

        @dwell_time.setter
        def dwell_time(self, dwell_time: float):
            validation.examples.dwell_time.validate(dwell_time)
            self._engine.pixel_time = dwell_time
            self.flyback = 10 * dwell_time

        @Key
        def flyback(self) -> float:
            """
            Public access to the time spent in flyback.

            Returns
            -------
            float
                The time spent in flyback (not scanning, but moving between pixels).
            """
            return self._engine.get_flyback_time()

        @flyback.setter
        def flyback(self, flyback: float):
            self._engine.set_flyback_time(flyback)
            # self._inhibit.validate(flyback)
            # self._engine.set_inhibit_time(flyback)

        @Key
        def lines(self) -> str:
            """
            Public access to the representation of connected lines.

            Returns
            -------
            str
                A binary string representing which connections are enabled.
            """
            return "".join(self._lines)

        def __init__(self, full_scan: FullScan, dwell_time: float = None, flyback: float = None):
            self._inhibit = validation.examples.any_float + validation.Pipeline(
                validation.Step(validation.DynamicUpperBoundValidator(lambda: self.dwell_time, inclusive=False)),
                in_type=float, out_type=float
            )
            if ONLINE:
                self._engine = ScanEngine(1)
                self._engine.set_image_size(*full_scan.size)
            else:
                self._engine = OfflineEngine()
            self.scan_area = full_scan
            if dwell_time is not None:
                self.dwell_time = dwell_time
            if flyback is not None:
                self.flyback = flyback
            self._lines = ["0"] * 10

            self._engine.set_enabled_inputs([3])  # add proper support for inputs
            self._engine.disable_lines(0b1111111111)
            for i in range(10):
                self._engine.set_output_line_a(i, 0)  # make sure no connections at start

        def inhibit_validation(self) -> validation.Pipeline:
            """
            The pipeline for inhibition validation.

            Returns
            -------
            Pipeline
                The pipeline for inhibition validation.
                This will be a floating point number that must be lower than the dwell time.
            """
            return self._inhibit

        def set_pattern(self, arr: np.ndarray):
            """
            Sets the scanning pattern.

            Note that this is not currently implemented.

            Parameters
            ----------
            arr: ndarray[int [y, 2]]
                The co-ordinate array for the pattern.
            """
            pass  # add proper encoding support

        def scan(self, *, return_=True) -> _None[GreyImage]:
            """
            Perform a scan on the registered area.

            Parameters
            ----------
            return_: bool
                Whether the scanned image should be returned (defaults to True).

            Returns
            -------
            GreyImage | None
                The scanned image (None if the `return_` parameter is False).
            """
            x_size, y_size = self._region.size
            sx, ex, sy, ey = self._region.rect()
            if ONLINE:
                monitor = FrameMonitor(x_size + 1, y_size + 1, inputs=[3], max_queue_size=1)
                monitor.register(self._engine)
                self._engine.start_imaging(0)
                self._engine.stop_imaging()
                monitor.wait_for_image()
                if return_:
                    img = monitor.pop().get_input_data(3)[sy:ey, sx:ex]
                    return GreyImage(img.astype(np.int_))
            elif return_:
                return GreyImage.from_file("./assets/img_3.bmp", do_static=True)

        def using_connection(self, line_index: int, mode: TTLMode, source: TriggerSource, *,
                             active: float = None, delay: float = None, count: int = None) -> Connection:
            """
            Create and establish a TTL connection.

            Parameters
            ----------
            line_index: int
                The index of the line to connect to.
            mode: TTLMode
                The mode for the connection.
            source: TriggerSource
                The source for the trigger.
            active: float | None
                The time in seconds that the connection is active.
            delay: float | None
                The delay (in seconds) before the connection is active.
            count: int | None
                The number of pulses to send.

            Returns
            -------
            Connection
                A TTL connection object.
            """
            if not ONLINE:
                raise TypeError(f"Offline engine cannot be used in a TTL connection.")
            return Connection(self._engine, self, line_index, mode, source, active=active, delay=delay, count=count)

        def add_line(self, i: int):
            """
            Registers a connection line as active.

            Parameters
            ----------
            i: int
                The line index.
            """
            self._lines[i] = "1"

        def remove_line(self, i: int):
            """
            Registers a connection line as inactive.

            Parameters
            ----------
            i: int
                The line index.
            """
            self._lines[i] = "0"

        switch_scan_area = scan_area.switch
        switch_dwell_time = dwell_time.switch
        switch_flyback = flyback.switch
else:
    class OfflineEngine:
        """
        Placeholder class for the offline JEOL scanner engine.
        """

        def set_areamode_imagingarea(self, width: int, height: int, x: int, y: int):
            """
            Set the imaging area for any area mode scans.

            Parameters
            ----------
            width: int
                The horizontal size of the area.
            height: int
                The vertical size of the area.
            x: int
                The horizontal position of the area.
            y: int
                The vertical position of the area.
            """
            pass

        def get_detectorsetting(self) -> _dict[str, int]:
            """
            Get the detector settings.

            Returns
            -------
            dict[str, int]
                The mapping from setting name to value.
            """
            return {"ExposureTimeValue": 0}

        def set_exposuretime_value(self, dwell_time: float):
            """
            Set the exposure time value.

            Parameters
            ----------
            dwell_time: float
                The exposure time value in microseconds.
            """
            pass

        def snapshot_rawdata(self) -> bytes:
            """
            Begin scanning the area into a raw data buffer.

            Returns
            -------
            bytes
                The raw data buffer of detector intensities.
            """
            img = cv2.imread("./assets/img_3.bmp", cv2.IMREAD_GRAYSCALE).astype(np.int16)
            print(img.shape)
            return img.tobytes()


    class Scanner:
        """
        A scan engine that encapsulates the JEOL scan engine.

        Attributes
        ----------
        _engine: Detector
            The detector controller that will be used for scanning - this is the scan engine for JEOL.
        _area: ScanType
            The scan area that will be used for scanning.
        """

        @Key
        def scan_area(self) -> ScanType:
            """
            Public access to the type of scan being performed.

            Returns
            -------
            ScanType
                The scan area that will be used for scanning.
            """
            return self._area

        @scan_area.setter
        def scan_area(self, value: ScanType):
            valid_type.validate(value)
            self._area = value
            sx, ex, sy, ey = self._area.rect()
            self._engine.set_areamode_imagingarea(ex - sx, ey - sy, sx, sy)

        @Key
        def dwell_time(self) -> float:
            """
            Public access to the time spent scanning per pixel.

            Returns
            -------
            float
                The dwell time in seconds.
            """
            return self._engine.get_detectorsetting()["ExposureTimeValue"]

        @dwell_time.setter
        def dwell_time(self, dwell_time: float):
            validation.examples.dwell_time.validate(dwell_time)
            self._engine.set_exposuretime_value(dwell_time)

        @Key
        def flyback(self) -> float:
            """
            Public access to the time spent in flyback.

            For the JEOL engine, this is not defined.

            Returns
            -------
            float
                The time spent in flyback (not scanning, but moving between pixels).
            """
            return -1

        @flyback.setter
        def flyback(self, flyback: float):
            pass

        @Key
        def lines(self) -> str:
            """
            Public access to the scan lines.

            Note the JEOL engine has no scan line connections available, so this will always return a constant string.

            Returns
            -------
            str
                The bit-string for whether scan lines are connected.
            """
            return "0000000000"

        def __init__(self, full_scan: FullScan, dwell_time: float = None, flyback: float = None):
            if ONLINE:
                self._engine = JEOLEngine("ADF1")
                self._engine.set_frameintegration(1)
                self._engine.set_scanmode(3)  # area mode
            else:
                self._engine = OfflineEngine()
            self.scan_area = full_scan
            if dwell_time is not None:
                self.dwell_time = dwell_time

        def inhibit_validation(self) -> validation.Pipeline:
            """
            The validation pipeline for flyback.

            Returns
            -------
            Pipeline
                The pipeline for flyback. Note that as the JEOL engine does not have a flyback, this is a null instance.
            """
            return validation.Pipeline(in_type=typing.Any, out_type=typing.Any)

        def set_pattern(self, arr: np.ndarray):
            """
            Sets the scanning pattern.

            Note that this is not currently implemented.

            Parameters
            ----------
            arr: ndarray[int [y, 2]]
                The co-ordinate array for the pattern.
            """
            pass  # add proper encoding support

        def scan(self, *, return_=True) -> _None[GreyImage]:
            """
            Perform a scan on the registered area.

            Parameters
            ----------
            return_: bool
                Whether the scanned image should be returned (defaults to True).

            Returns
            -------
            GreyImage | None
                The scanned image (None if the `return_` parameter is False).
            """
            buffer = self._engine.snapshot_rawdata()
            if return_:
                array = np.frombuffer(buffer, np.int16)
                w, h = self._area.size
                array = array.reshape((h, w)).astype(np.int_)
                return GreyImage(array)

        def using_connection(self, line_index: int, mode: TTLMode, source: TriggerSource, *,
                             active: float = None, delay: float = None, count: int = None) -> Connection:
            """
            Create and establish a TTL connection.

            Parameters
            ----------
            line_index: int
                The index of the line to connect to.
            mode: TTLMode
                The mode for the connection.
            source: TriggerSource
                The source for the trigger.
            active: float | None
                The time in seconds that the connection is active.
            delay: float | None
                The delay (in seconds) before the connection is active.
            count: int | None
                The number of pulses to send.

            Returns
            -------
            Connection
                A TTL connection object.

            Raises
            ------
            TypeError
                When called, as JEOL engines have no TTL connections.
            """
            raise TypeError("JEOL engine has no TTL connections")

        def add_line(self, i: int):
            """
            Registers a connection line as active.

            Parameters
            ----------
            i: int
                The line index.

            Raises
            ------
            TypeError
                When called, as JEOL engines have no TTL connections.
            """
            raise TypeError(f"JEOL engine has no TTL connections")

        def remove_line(self, i: int):
            """
            Registers a connection line as inactive.

            Parameters
            ----------
            i: int
                The line index.

            Raises
            ------
            TypeError
                When called, as JEOL engines have no TTL connections.
            """
            raise TypeError(f"JEOL engine has no TTL connections")

        switch_scan_area = scan_area.switch
        switch_dwell_time = dwell_time.switch
        switch_flyback = flyback.switch
