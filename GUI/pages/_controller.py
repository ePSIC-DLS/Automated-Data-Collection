"""
Module to interface with the microscope from within a GUI page.
"""
import typing

from . import base, extra_widgets, corrections
from .base import widgets, core
from modular_qt import microscope


class MicroscopePage(base.Page):
    """
    Concrete subclass to perform some microscope configuration (recalling and saving from .hdf5 files).

    Can also perform some adjustments for built-in corrections.

    :var _link Microscope: The link to the microscope hardware.
    :var _panel FilePrompt: The front end panel for choosing a file.
    :var _file_path PyQt5.QWidgets.QLineEdit: The editor for filepaths.
    :var _chooser PyQt5.QWidgets.QPushButton: A button to display the directory chooser.
    :var _corrections list[BaseCorrection]: A list of all corrections to implement.
    :var _correction_manager PyQt5.QWidgets.QTabWidget: A widget to display correction settings one at a time.
    """

    def __init__(self, threads: core.QThreadPool, pause_func: typing.Callable[[], None]):
        super().__init__()
        self._link = microscope.Microscope.get_instance()
        self._panel = extra_widgets.FilePrompt("hdf5", open_="recall")
        self._panel.dialog().open.connect(self._link.read)
        self._panel.dialog().save.connect(self._link.write)
        self._corrections: list[corrections.BaseCorrection] = [corrections.Beam(threads),
                                                               corrections.Emission(threads),
                                                               corrections.Focus()]
        self._corrections[1].begin.connect(pause_func)
        self._corrections[1].end.connect(pause_func)
        self._corrections[2].begin.connect(pause_func)
        self._corrections[2].end.connect(pause_func)
        self._correction_manager = widgets.QTabWidget()
        self._correction_manager.setTabPosition(widgets.QTabWidget.South)
        self._layout.addWidget(self._panel, 0, 0)
        for method in self._corrections:
            self._correction_manager.addTab(method, f"{type(method).__name__} Correction")
        self._layout.addWidget(self._correction_manager, 0, 1)

    def compile(self) -> str:
        return ""

    @core.pyqtSlot(int)
    def corrections_update(self, scans: int):
        """
        Slot to update all corrections every scan.

        :param scans: The number of scans.
        """
        for method in self._corrections:
            method.update_on_scan(scans)

    def run(self, btn_state: bool):
        pass

    def start(self):
        super().start()
        self.setEnabled(True)
        for method in self._corrections:
            method.start()

    def stop(self):
        super().stop()
        self.setEnabled(False)
        for method in self._corrections:
            method.stop()
