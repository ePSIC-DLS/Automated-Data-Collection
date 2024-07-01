import typing
from typing import List as _list, Tuple as _tuple

import numpy as np
from PyQt5.QtCore import Qt as enums

from ... import utils
from ..._base import ClusterPage, SettingsPage, widgets, gui, images, core
from ..._errors import *

from ....microscope import ScanType, ONLINE, FullScan, Scanner


class SurveyImage(ClusterPage, SettingsPage):
    settingChanged = SettingsPage.settingChanged
    driftRegion = core.pyqtSignal(tuple, tuple)

    def __init__(self, size: int, cluster_colour: np.int_, initial_size: int, scanner: Scanner,
                 scan_func: typing.Callable[[ScanType, bool], images.GreyImage]):
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

        self._drift_size = utils.LabelledWidget("Drift Region", utils.ComboBox(8, 16, 32, 64),
                                                utils.LabelOrder.SUFFIX)
        self._export = widgets.QPushButton("Export region")
        self._co_ords: _tuple[int, int, int, int] = (0, 0, 0, 0)
        self._export.clicked.connect(lambda: self._region_export())

        self._regular.addWidget(self._polygon_mode)
        self._regular.addWidget(self._drift_size)
        self._regular.addWidget(self._export)

        self._canvas.mousePressed.connect(self._click)

        self.setLayout(self._layout)

        self._scanner = scanner
        self._scan = scan_func

    @utils.Tracked
    def _region_export(self):
        if all(c == 0 for c in self._co_ords):
            raise StagingError("Exporting Region", "Creating Region")
        self.driftRegion.emit(self._co_ords[:2], self._co_ords[2:])

    def compile(self) -> str:
        return "Scan"

    def run(self):
        if self._state != utils.StoppableStatus.ACTIVE:
            return
        self.runStart.emit()
        if ONLINE:
            region = FullScan(self._canvas.image_size)
            self._scanner.scan_area = region
            self._modified_image = self._scan(region, True).promote()
        else:
            self._modified_image = images.RGBImage.from_file("./assets/img_3.bmp", do_static=True)
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
            self._cluster_image.drawings.line(self._polygon[-1], (x, y), self._cluster_colour)
            self._canvas.draw(self._cluster_image)
        else:
            self._tooltip(event)

    @utils.Tracked
    def _click(self, event: gui.QMouseEvent):
        if self._state != utils.StoppableStatus.ACTIVE:
            return
        elif self._modified_image is None:
            raise StagingError("drawing", "image scanning")
        btn = event.button()
        pos = event.pos()
        if not self._polygon_mode.focus.isChecked():
            self._modified_image = self._original_image.copy()
            x, y = pos.x(), pos.y()
            size = self._drift_size.focus.get_data()
            left, top = x - size // 2, y - size // 2
            right, bottom = x + size // 2, y + size // 2
            try:
                self._modified_image.drawings.rect.from_corners(
                    (left, top), (right, bottom), self._cluster_colour, fill=None)
            except IndexError as err:
                raise GUIError(utils.ErrorSeverity.WARNING, "Drift Region Error", str(err))
            self._canvas.draw(self._modified_image)
            self._co_ords = (left, top, right, bottom)
            return
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
                self._cluster_image.drawings.line(self._polygon[-1], self._polygon[0], self._cluster_colour)
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
