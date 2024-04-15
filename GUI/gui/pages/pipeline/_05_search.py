import functools
from datetime import datetime

import time
import typing
from typing import Tuple as _tuple

from ._01_survey import SurveyImage
from ._04_manager import Management
from ... import utils
from ..._base import CanvasPage, SettingsPage, ProcessPage, widgets, core, images
from ..._errors import *
from .... import validation, microscope


class GridDict(utils.SettingsDict):
    scan_size: utils.ComboBox[int]
    exposure_time: utils.Spinbox
    bit_depth: utils.ComboBox[int]
    save_path: utils.Entry
    checkpoints: utils.Flag[utils.Stages]


class GridSettings(utils.SettingsPopup):

    def __init__(self, failure_action: typing.Callable[[Exception], None]):
        super().__init__()

        def _exposure(new: int):
            exposure_branches.branch = self._depth.currentIndex()
            v = self._exposure.get_data()
            if new == 1 and v < 100:
                self._exposure.change_data(100)
            elif new == 6 and v < 600:
                self._exposure.change_data(600)
            elif new == 12 and v < 1000:
                self._exposure.change_data(1000)

        self._size = utils.ComboBox(*DeepSearch.SIZES, start_i=-1)
        self._size.dataPassed.connect(lambda v: self.settingChanged.emit("scan_size", v))
        self._size.dataFailed.connect(failure_action)
        exposure_branches = validation.VBranchedMixin(
            validation.RangeValidator.known((100, 5000)),
            validation.RangeValidator.known((600, 5000)),
            validation.RangeValidator.known((1000, 5000)),
            branch=1)
        exposure = validation.examples.any_int + validation.Pipeline(validation.Step(exposure_branches,
                                                                                     desc="ensure the exposure time is "
                                                                                          "between (100 for bit depth 1"
                                                                                          ", 600 for bit depth 6, or "
                                                                                          "1000 for bit depth 12) and "
                                                                                          "5000",
                                                                                     ), in_type=int, out_type=int)
        self._exposure = utils.Spinbox(5000, 100, exposure)
        self._exposure.dataPassed.connect(lambda v: self.settingChanged.emit("exposure_time", v))
        self._exposure.dataFailed.connect(failure_action)
        self._depth = utils.ComboBox(1, 6, 12, start_i=1)
        self._depth.dataPassed.connect(lambda v: self.settingChanged.emit("bit_depth", v))
        self._depth.dataPassed.connect(_exposure)
        self._depth.dataFailed.connect(failure_action)
        self._path = utils.Entry("X:/data/2023/{session}/Merlin/{sample}", validation.examples.file_path, "\"")
        self._path.dataPassed.connect(lambda v: self.settingChanged.emit("save_path", v))
        self._path.dataFailed.connect(failure_action)
        self._extras = utils.Flag(utils.Stages, utils.Stages(15))
        self._extras.dataPassed.connect(lambda v: self.settingChanged.emit("checkpoints", v))
        self._extras.dataFailed.connect(failure_action)

        self._layout.addWidget(utils.DoubleLabelledWidget("Scan Size", self._size,
                                                          "The size (in pixels) of each grid square"))
        self._layout.addWidget(utils.DoubleLabelledWidget("Dwell Value", self._exposure,
                                                          "The exposure time (in microseconds) of each scan"))
        self._layout.addWidget(utils.DoubleLabelledWidget("Bit Depth", self._depth,
                                                          "The bit depth for each scan"))
        self._layout.addWidget(utils.DoubleLabelledWidget("Save Path", self._path,
                                                          "The path to save the data to"))
        self._layout.addWidget(utils.DoubleLabelledWidget("Additional Files", self._extras,
                                                          "The extra stages to save into the dataset file"))

    def widgets(self) -> GridDict:
        return {"scan_size": self._size, "exposure_time": self._exposure, "bit_depth": self._depth,
                "save_path": self._path, "checkpoints": self._extras}


class DeepSearch(CanvasPage, SettingsPage, ProcessPage):
    settingChanged = SettingsPage.settingChanged
    clusterScanned = core.pyqtSignal(int)
    scanPerformed = core.pyqtSignal()
    _newVal = core.pyqtSignal(int)
    SIZES = (64, 128, 256, 512)

    def __init__(self, size: int, grids: Management, image: SurveyImage, marker: images.RGB,
                 failure_action: typing.Callable[[Exception], None], mic: microscope.Microscope,
                 scanner: microscope.Scanner):
        DeepSearch.SIZES = tuple(s for s in DeepSearch.SIZES if s < size)
        CanvasPage.__init__(self, size)
        SettingsPage.__init__(self, utils.SettingsDepth.REGULAR | utils.SettingsDepth.ADVANCED,
                              functools.partial(GridSettings, failure_action))
        ProcessPage.__init__(self)
        self._colour_option.hide()
        self._regions: _tuple[utils.ScanRegion, ...] = ()
        self._grids = grids
        self._image = image
        self._marker = marker
        self._automate = False

        self._scan_mode = utils.LabelledWidget("Merlin Scan Mode", utils.CheckBox("&M", True), utils.LabelOrder.SUFFIX)
        self._scan_mode.focus.dataPassed.connect(lambda v: self.settingChanged.emit("scan_mode", v))
        self._scan_mode.focus.dataFailed.connect(failure_action)
        self._session = utils.LabelledWidget("Session",
                                             utils.Entry("cm33902-5", validation.examples.save_path),
                                             utils.LabelOrder.SUFFIX)
        self._session.focus.dataPassed.connect(lambda v: self.settingChanged.emit("session", v))
        self._session.focus.dataFailed.connect(failure_action)
        self._sample = utils.LabelledWidget("Sample",
                                            utils.Entry("test_xgrating", validation.examples.save_path),
                                            utils.LabelOrder.SUFFIX)
        self._sample.focus.dataPassed.connect(lambda v: self.settingChanged.emit("sample", v))
        self._sample.focus.dataFailed.connect(failure_action)
        self._progress = widgets.QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setValue(0)
        self._progress.setFormat("%v/%m steps complete (%p%)")
        self.clusterScanned.connect(self._progress.setValue)
        self._newVal.connect(self._progress.setValue)

        self._regular.addWidget(self._scan_mode)
        self._regular.addWidget(self._session)
        self._regular.addWidget(self._sample)
        self._regular.addWidget(self._progress)

        self.setLayout(self._layout)
        self._mic = mic
        self._scanner = scanner

    def clear(self):
        CanvasPage.clear(self)
        ProcessPage.clear(self)
        self._progress.setRange(0, 0)
        self._regions = ()

    def start(self):
        SettingsPage.start(self)
        CanvasPage.start(self)
        ProcessPage.start(self)

    def stop(self):
        SettingsPage.stop(self)
        CanvasPage.stop(self)
        ProcessPage.stop(self)

    def compile(self) -> str:
        return "search"

    @utils.Tracked
    def run(self):
        if self._state != utils.StoppableStatus.ACTIVE:
            return
        self._regions = self._grids.get_tight()
        if not self._regions:
            raise StagingError("grid search", "exporting tightened grids")
        self.runStart.emit()
        self._progress.setMaximum(len(self._regions))
        self._modified_image = self._image.original.copy()
        for grid in self._regions:
            grid.draw(self._modified_image, ~self._marker)
        self._canvas.draw(self._modified_image)
        self._original_image = self._modified_image.copy()
        if self._automate or microscope.ONLINE:
            self._run.py_func(None)
        else:
            self._run()

    @utils.Stoppable.decorate(manager=ProcessPage.MANAGER)
    @utils.Tracked
    def _run(self, current: typing.Optional[int]):
        if current is None:
            current = -1
            self._newVal.emit(0)
        if microscope.ONLINE:
            self._mic.subsystems["Deflectors"].blanked = True
        resolution = 4096
        original = self._original_image.image.copy()
        do_merlin = self._scan_mode.focus.isChecked()
        save_path = self.get_setting("save_path").format(session=self._session.focus.text()[1:-1],
                                                         sample=self._sample.focus.text()[1:-1])
        try:
            validation.examples.save_path.validate(f"\'{save_path}\'")
        except validation.ValidationError as err:
            raise GUIError(utils.ErrorSeverity.ERROR, "Cannot validate save path", str(err))
        if microscope.ONLINE:
            self._scanner.scan_area = microscope.FullScan((resolution, resolution))  # add in pattern size
        for i, region in enumerate(self._regions):
            if i < current:
                continue
            elif self._state == utils.StoppableStatus.PAUSED:
                self._run.pause.emit(i)
                return
            elif self._state == utils.StoppableStatus.DEAD:
                with self._canvas as draw:
                    draw.image.reference()[:, :, :] = original.copy()
                return
            with self._canvas as draw:
                draw.image.reference()[:, :, :] = original.copy()
                region.draw(draw, self._marker, filled=True)
                if not microscope.ONLINE:
                    time.sleep(1)
            if microscope.ONLINE:
                region_4k = region @ resolution
                top_left = region[images.AABBCorner.TOP_LEFT]
                bottom_right = region[images.AABBCorner.BOTTOM_RIGHT]
                self._scanner.scan_area = microscope.AreaScan.from_corners((resolution, resolution), top_left,
                                                                           bottom_right)
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                params = f"{save_path}/{stamp}.hdf5"
                if not do_merlin:
                    with self._mic.subsystems["Deflectors"].switch_blanked(False):
                        with self._mic.subsystems["Detectors"].switch_inserted(True):
                            img = self._scanner.scan()
                            region_4k.save(f"{save_path}/image_{i}.hdf5", img)
            if self._progress.isEnabled():
                self.scanPerformed.emit()
                self.clusterScanned.emit(i + 1)
        self.runEnd.emit()

    def automate(self):
        self._automate = True
        try:
            self.run.py_func()
        finally:
            self._automate = False

    def _process_tooltip(self, x: int, y: int) -> typing.Iterator[str]:
        yield f"<{x}, {y}>"

    def all_settings(self) -> typing.Iterator[str]:
        yield from ("scan_mode", "session", "sample", "scan_size", "exposure_time", "bit_depth", "save_path",
                    "checkpoints")

    def help(self) -> str:
        s = f"""This page allows for scanning each grid square managed by the cluster manager.
        
        Each grid square will be scanned by using the proposed scan pattern;
        and will be in a higher resolution to allow for better data.

        Settings
        --------
        Merlin Scan Mode:
            {validation.examples.any_bool}
            
            Whether to activate the Merlin software to perform 4D data collection. While this collects more data;
            (and different kinds of data) it is a much slower scan and can increase beam damage of the sample.
        Session:
            {validation.examples.save_path}
            
            The session to be substituted into the save path.
        Sample:
            {validation.examples.save_path}
            
            The sample to be substituted into the save path.
        For advanced settings, see the help page."""
        return s

    def advanced_help(self) -> str:
        s = f"""Scan Size:
                {self.get_control('scan_size').validation_pipe()}
                
                The square size of the scan (in pixels). This will affect the grid size of each cluster.
        Dwell Value:
            {self.get_control('exposure_time').validation_pipe()}
            
            The exposure time in microseconds. Dependant on the bit depth.
        Bit Depth:
            {self.get_control('bit_depth').validation_pipe()}
            
            The bit depth to use when communicating with Merlin.
        Save Path:
            {validation.examples.file_path}
            
            The save path to use for the output files.
            Using python f-string style substitution ({{session}}) will substitute the relevant variable.
            Note that "session" and "sample" are the only supported variables.
        Additional Files:
            {self.get_control('checkpoints').validation_pipe()}
            
            The extra files to save into the HDF5 file. Each image will have its own dataset."""
        return s
