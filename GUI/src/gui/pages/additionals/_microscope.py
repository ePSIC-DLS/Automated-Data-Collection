import functools
import typing
from typing import Dict as _dict, Tuple as _tuple

from ... import utils
from ..._base import SettingsPage, widgets, core
from .... import microscope, validation, images
from ..._errors import *


def _add_unit(value: float) -> str:
    sci = f"{value:.3e}"
    dig, exp = map(float, sci.split("e"))
    exp = int(exp)
    if exp == -8:
        return f"{dig * 10:g}ns"
    elif exp == -7:
        return f"{dig * 100:g}ns"
    elif exp == -6:
        return f"{dig:g}us"
    elif exp == -5:
        return f"{dig * 10:g}us"
    elif exp == -4:
        return f"{dig * 100:g}us"
    elif exp == -3:
        return f"{dig:g}ms"
    elif exp == -2:
        return f"{dig * 10:g}ms"
    elif exp == -1:
        return f"{dig * 100:g}ms"
    elif exp == 0:
        return f"{dig:g} s"
    elif exp == 1:
        return f"{dig * 10:g} s"


def _sub_unit(value: str) -> float:
    dig = float(value[:-2])
    exp = value[-2]
    if exp == "n":
        return dig * 1e-9
    elif exp == "u":
        return dig * 1e-6
    elif exp == "m":
        return dig * 1e-3
    elif exp == " ":
        return dig


class Sources(widgets.QWidget):
    """
    Widget representing the TTL communication source for a particular connection.

    Attributes
    ----------
    _choices: tuple[QRadioButton, ...]
        The available sources.
    _input: ComboBox[int]
        The TTL input trigger values.
    _output: ComboBox[int]
        The TTL output trigger values.
    _clock: Enum[EdgeType]
        The type of pixel clock trigger.
    """

    def __init__(self):
        super().__init__()
        layout = widgets.QGridLayout()
        self._choices = tuple(widgets.QRadioButton(name) for name in ("TTL&Input", "TTL&Output", "Pi&xelClock"))
        self._input = utils.ComboBox(*range(5))
        self._output = utils.ComboBox(*range(8))
        self._clock = utils.Enum(microscope.EdgeType, microscope.EdgeType.RISING)
        for i, (choice, param) in enumerate(zip(self._choices, (self._input, self._output, self._clock))):
            layout.addWidget(choice, i, 0)
            layout.addWidget(param, i, 1)
            param.setEnabled(False)
            choice.toggled.connect(self._param(i))
        self.setLayout(layout)

    def get_data(self) -> microscope.TriggerSource:
        """
        Get a trigger source based on the widget's state.

        Returns
        -------
        TriggerSource
            The source of a trigger.
        """
        if self._choices[0].isChecked():
            return microscope.TTLInput(self._input.get_data())
        elif self._choices[1].isChecked():
            return microscope.TTLOutput(self._output.get_data())
        elif self._choices[2].isChecked():
            return microscope.PixelClock(self._clock.get_data())

    def _param(self, i: int) -> typing.Callable[[], None]:
        def _inner():
            self._input.setEnabled(False)
            self._output.setEnabled(False)
            self._clock.setEnabled(False)
            if i == 0:
                self._input.setEnabled(True)
            elif i == 1:
                self._output.setEnabled(True)
            elif i == 2:
                self._clock.setEnabled(True)

        return _inner


class ConnectionManager(widgets.QWidget):
    """
    Widget managing a singular TTL connection.

    Signals
    -------
    exported: dict[str, Any]
        The exported connection parameters.

    Attributes
    ----------
    _mode: LabelledWidget[Enum[TTLMode]]
        The connection mode.
    _source: LabelledWidget[Source]
        The connection source.
    _active: LabelledWidget[Spinbox]
        The active time.
    _delay: LabelledWidget[Spinbox]
        The delay prior to activation.
    _count: LabelledWidget[Spinbox]
        The number of pulses to send.
    _export: QPushButton
        The button to export and save the connection.
    _enabled: QPushButton
        The button to enable/disable the connection.
    """
    exported = core.pyqtSignal(dict)

    def __init__(self, index: int):
        super().__init__()

        def _edit(new: microscope.TTLMode):
            self._active.setEnabled(False)
            self._delay.setEnabled(False)
            self._count.setEnabled(False)
            if new in {microscope.TTLMode.SOURCE_TIMED, microscope.TTLMode.SOURCE_TIMED_DELAY}:
                self._active.setEnabled(True)
            if new in {microscope.TTLMode.SOURCE_TIMED_DELAY}:
                self._delay.setEnabled(True)
            if new in {microscope.TTLMode.PULSE_TRAIN, microscope.TTLMode.SOURCE_TRAIN}:
                self._count.setEnabled(True)

        def _export():
            settings = dict(
                line_index=index,
                mode=self._mode.focus.get_data(),
                source=self._source.focus.get_data(),
                active=None,
                delay=None,
                count=None,
                enabled=self._enabled.isChecked()
            )
            if self._active.isEnabled():
                settings["active"] = self._active.focus.get_data()
            if self._delay.isEnabled():
                settings["delay"] = self._delay.focus.get_data()
            if self._count.isEnabled():
                settings["count"] = self._count.focus.get_data()
            self.exported.emit(settings)

        layout = widgets.QGridLayout()
        self._mode = utils.LabelledWidget("Activation Mode", utils.Enum(microscope.TTLMode, microscope.TTLMode.ON),
                                          utils.LabelOrder.PREFIX)
        self._source = utils.LabelledWidget("Communication Source", Sources(), utils.LabelOrder.PREFIX)
        self._active = utils.LabelledWidget("On Time", utils.Spinbox(1e-3, 1e-3, validation.examples.natural_float,
                                                                     display=(_add_unit, _sub_unit)),
                                            utils.LabelOrder.PREFIX)
        self._delay = utils.LabelledWidget("Delay Time",
                                           utils.Spinbox(1e-3, 1e-3, validation.examples.natural_float,
                                                         display=(_add_unit, _sub_unit)),
                                           utils.LabelOrder.PREFIX)
        self._count = utils.LabelledWidget("Pulse Count", utils.Spinbox(1, 1, validation.examples.natural_int),
                                           utils.LabelOrder.PREFIX)
        self._export = widgets.QPushButton("E&xport")
        self._enabled = widgets.QCheckBox("E&nabled")

        self._mode.focus.dataPassed.connect(_edit)
        self._export.clicked.connect(_export)
        _edit(microscope.TTLMode.ON)

        layout.addWidget(widgets.QLabel(f"Index: {index}"), 0, 0)
        layout.addWidget(self._enabled, 0, 1)
        layout.addWidget(self._export, 0, 2)
        layout.addWidget(self._mode, 1, 0)
        layout.addWidget(self._source, 2, 0)
        layout.addWidget(self._active, 2, 1)
        layout.addWidget(self._delay, 2, 2)
        layout.addWidget(self._count, 2, 3)
        self.setLayout(layout)


class Scanner(SettingsPage):
    """
    Concrete page with settings to interface with the scan engine.

    _scanner: Scanner
        The actual scan engine.
    _mic: Microscope
        The link to the microscope.
    _stage: LabelledWidget[XDControl[Spinbox]]
        The controller for the stage position.
    _exposure: LabelledWidget[Spinbox]
        The dwell time of normal scans.
    _flyback: LabelledWidget[Spinbox]
        The flyback time for scans.
    _connections: tuple[QPushButton, ...]
        A series of buttons, each triggering a specific TTL connection to be configured.
    _connected: tuple[ConnectionManager, ...]
        A series of popups to control a TTL connection.
    """
    settingChanged = SettingsPage.settingChanged

    def __init__(self, mic: microscope.Microscope, scanner: microscope.Scanner):
        SettingsPage.__init__(self, utils.SettingsDepth.REGULAR)
        self._scanner = scanner
        self._mic = mic

        self._stage = utils.LabelledWidget("Stage Position",
                                           utils.XDControl(3, utils.Spinbox, initial=0, step=1,
                                                           pipeline=validation.examples.stage_pos),
                                           utils.LabelOrder.SUFFIX)
        self._stage.focus.dataPassed.connect(self._stage_moved)

        self._exposure = utils.LabelledWidget("Dwell Time",
                                              utils.Spinbox(self._scanner.dwell_time, 100e-6,
                                                            validation.examples.dwell_time,
                                                            display=(_add_unit, _sub_unit)),
                                              utils.LabelOrder.SUFFIX)
        self._flyback = utils.LabelledWidget("Flyback Time",
                                             utils.Spinbox(self._scanner.flyback, 100e-6,
                                                           self._scanner.inhibit_validation(),
                                                           display=(_add_unit, _sub_unit)),
                                             utils.LabelOrder.SUFFIX)
        self._connections = tuple(widgets.QPushButton("0") for _ in range(10))
        lay = widgets.QHBoxLayout()
        wid = widgets.QWidget()
        for cnc_i, cnctn in enumerate(self._connections):
            if cnc_i == 6:
                cnctn.setEnabled(False)
            cnctn.clicked.connect(functools.partial(lambda x: self._display_popup(self._connected[x]), cnc_i))
            lay.addWidget(cnctn)
        wid.setLayout(lay)
        self._exposure.focus.dataPassed.connect(lambda v: self._write("dwell_time", v))
        self._flyback.focus.dataPassed.connect(lambda v: self._write("flyback", v))
        self._regular.addWidget(self._exposure)
        self._regular.addWidget(self._flyback)
        self._regular.addWidget(utils.LabelledWidget("Peripheral Management", wid, utils.LabelOrder.SUFFIX))
        self._regular.addWidget(self._stage)
        self._connected = tuple(ConnectionManager(i) for i in range(10))
        for cnctn in self._connected:
            cnctn.exported.connect(self._add_connection)
        self.setLayout(self._layout)
        self.read()

    def read(self):
        """
        Re-read the actual settings from the scan engine, and import the data to the widgets.
        """
        self._exposure.focus.change_data(self._scanner.dwell_time)
        self._flyback.focus.change_data(self._scanner.flyback)
        for ln, cnctn in zip(self._scanner.lines, self._connections):
            cnctn.setText(ln)
        xyz = [0, 0, 0]
        stage = self._mic.subsystems["Stage"]
        with stage.switch_axis(microscope.Axis.X):
            with stage.switch_axis(microscope.Axis.Y):
                with stage.switch_axis(microscope.Axis.Z):
                    xyz[2] = stage.pos
                xyz[1] = stage.pos
            xyz[0] = stage.pos
        self._stage.focus.change_data(tuple(xyz))

    def stop(self):
        SettingsPage.stop(self)
        for cnc in self._connected:
            cnc.close()

    def compile(self) -> str:
        return ""

    def all_settings(self) -> typing.Iterator[str]:
        yield from ()

    def run(self):
        pass

    def clear(self):
        pass

    def scan(self, area: microscope.ScanType, detector_status: bool) -> images.GreyImage:
        """
        Perform a scan using the scan engine, configured to certain settings.

        This configuration of settings is the GUI's idea of an image scan.

        Parameters
        ----------
        area: ScanType
            The area to scan.
        detector_status: bool
            Whether the currently active detector is inserted.

        Returns
        -------
        GreyImage
            The scanned image.
        """
        with self._scanner.switch_scan_area(area):
            with self._scanner.switch_dwell_time(self._exposure.focus.get_data()):
                with self._mic.subsystems["Deflectors"].switch_blanked(False):
                    with self._mic.subsystems["Detectors"].switch_inserted(detector_status):
                        return self._scanner.scan()

    def _stage_moved(self, xyz: _tuple[int, int, int]):
        stage = self._mic.subsystems["Stage"]
        with stage.switch_axis(microscope.Axis.X):
            with stage.switch_axis(microscope.Axis.Y):
                with stage.switch_axis(microscope.Axis.Z):
                    stage.pos = xyz[2]
                stage.pos = xyz[1]
            stage.pos = xyz[0]
        self.read()

    @utils.Tracked
    def _add_connection(self, kwargs: _dict[str, object]):
        is_enabled = kwargs.pop("enabled")
        if kwargs["source"] is None:
            raise GUIError(utils.ErrorSeverity.ERROR, "Invalid Connection",
                           f"Connection {kwargs['line_index']} not successfully setup")
        connection = self._scanner.using_connection(**kwargs)
        if is_enabled:
            connection.activate()
        else:
            connection.deactivate()
        self.read()

    def _write(self, prop: str, value):
        setattr(self._scanner, prop, value)
        self.read()
