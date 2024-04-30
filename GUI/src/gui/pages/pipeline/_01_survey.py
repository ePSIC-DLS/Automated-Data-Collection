import typing
from typing import List as _list, Tuple as _tuple

from PyQt5.QtCore import Qt as enums

from ... import utils
from ..._base import ClusterPage, SettingsPage, widgets, gui, images
from ..._errors import *

from ....microscope import Scanner, Microscope, ONLINE, FullScan


class SurveyImage(ClusterPage, SettingsPage):
    settingChanged = SettingsPage.settingChanged
    SIZES = (128, 256, 512, 1024)

    def __init__(self, size: int, cluster_colour: images.RGB, initial_size: int, link: Microscope, scanner: Scanner):
        def _reset(new: enums.CheckState):
            if new == enums.Unchecked and self._original_image is not None:
                self._polygon.clear()
                self._clusters.clear()
                self._modified_image = self._original_image.copy()
                self._canvas.draw(self._modified_image)
                self._original_image = self._modified_image.copy()
                self._cluster_image = self._modified_image.copy()

        ClusterPage.__init__(self, size, cluster_colour, initial_size, movement_handler=self._draw)
        SettingsPage.__init__(self, utils.SettingsDepth.REGULAR)

        self._polygon: _list[_tuple[int, int]] = []
        self._polygon_mode = utils.LabelledWidget("ROI Drawing Mode", widgets.QCheckBox("&R"), utils.LabelOrder.SUFFIX)
        self._polygon_mode.focus.stateChanged.connect(_reset)
        self._regular.addWidget(self._polygon_mode)

        self._canvas.mousePressed.connect(self._click)

        self.setLayout(self._layout)

        self._mic = link
        self._scanner = scanner

    def compile(self) -> str:
        return ""

    def run(self):
        if self._state != utils.StoppableStatus.ACTIVE:
            return
        self.runStart.emit()
        if ONLINE:
            self._scanner.scan_area = FullScan(self._canvas.image_size)
            self._scanner.dwell_time = 15e-6
            with self._mic.subsystems["Deflectors"].switch_blanked(False):
                with self._mic.subsystems["Detectors"].switch_inserted(True):
                    self._modified_image = self._scanner.scan().promote()
        else:
            self._modified_image = images.RGBImage.from_file(
                r"C:\Users\fmz84311\OneDrive - Diamond Light Source Ltd\Documents\Project\Collection\assets\img_3.bmp"
            )
        self._original_image = self._modified_image.copy()
        self._canvas.draw(self._modified_image)
        self.runEnd.emit()

    def clear(self):
        ClusterPage.clear(self)
        self._polygon.clear()

    def start(self):
        SettingsPage.start(self)
        ClusterPage.start(self)

    def stop(self):
        SettingsPage.stop(self)
        ClusterPage.stop(self)

    def _draw(self, event: gui.QMouseEvent):
        if self._state != utils.StoppableStatus.ACTIVE:
            return
        if self._polygon_mode.focus.isChecked() and self._modified_image is not None and self._polygon:
            self._cluster_image = self._modified_image.copy()
            pos = event.pos()
            x, y = pos.x(), pos.y()
            self._cluster_image.drawing.line(self._polygon[-1], (x, y), self._cluster_colour)
            self._canvas.draw(self._cluster_image)
        else:
            self._tooltip(event)

    @utils.Tracked
    def _click(self, event: gui.QMouseEvent):
        if self._state != utils.StoppableStatus.ACTIVE:
            return
        elif not self._polygon_mode.focus.isChecked():
            return
        elif self._modified_image is None:
            raise StagingError("cluster drawing", "image scanning")
        btn = event.button()
        pos = event.pos()
        if btn == enums.LeftButton:
            self._polygon.append((pos.x(), pos.y()))
        else:
            try:
                cl_label = len(self._clusters) + 1
                cluster = utils.Cluster.from_vertices(*self._polygon, label=cl_label,
                                                      im_size=self._canvas.image_size)
            except TypeError:
                raise GUIError(utils.ErrorSeverity.INFO, "Polygon Formation Error",
                               "Need at least 3 vertices to form a polygon")
            self._cluster_image = self._modified_image.copy()
            if self._polygon[-1] != self._polygon[0]:
                self._cluster_image.drawing.line(self._polygon[-1], self._polygon[0], self._cluster_colour)
            self._clusters.append(cluster)
            self._polygon.clear()
            self._canvas.draw(self._cluster_image)
            self.clusterFound.emit(cl_label)
        if self._cluster_image is not None:
            self._modified_image = self._cluster_image.copy()

    def all_settings(self) -> typing.Iterator[str]:
        yield from ()

    def help(self) -> str:
        s = """This is the survey image - it represents an initial image to threshold and segment.
        On the survey image, arbitrary polygons can be made and managed in the cluster manager
        
        Settings
        --------
        ROI Drawing Mode
            No validation.
            
            Enables the Region Of Interest Drawing Mode, where left-clicking the canvas will create a vertex, and
            right-clicking will complete the ROI polygon."""
        return s
