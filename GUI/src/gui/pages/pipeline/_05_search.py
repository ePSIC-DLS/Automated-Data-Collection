import functools
import os
import typing
from datetime import datetime
from typing import Tuple as _tuple, Optional as _None

import h5py
import numpy as np
import time

from ._01_survey import SurveyImage
from ._02_thresholding import ProcessingPipeline
from ._03_clustering import Clusters
from ._04_manager import Management
from ... import utils
from ..._base import CanvasPage, core, images, ProcessPage, SettingsPage, widgets
from ..._errors import *
from .... import load_settings, microscope, validation
from ..corrections import _drift

import logging

Corners = images.AABBCorner


class GridDict(utils.SettingsDict):
    """
    Typed dictionary representing the advanced grid search settings.

    Keys
    ----
    scan_size: ComboBox[int]
        The real size of the grid scan.
    exposure_time: Spinbox
        The time in seconds to spend on each pixel in the scan.
    bit_depth: ComboBox[int]
        The bit depth of the grid scan (only available for merlin data).
    save_path: Entry
        The filepath for the images to be saved to. This supports python f-string formatting using '{}'.
    checkpoints: Flag[Stages]
        The additional images to be saved as metadata.
    """
    scan_size: utils.ComboBox[int]
    exposure_time: utils.Spinbox
    bit_depth: utils.ComboBox[int]
    save_path: utils.Entry
    checkpoints: utils.Flag[utils.Stages]


default_settings = load_settings("assets/config.json",
                                 scan_size=validation.examples.survey_size,
                                 exposure_time=validation.examples.dwell_time,
                                 bit_depth=validation.examples.bit_depth,
                                 save_path=validation.examples.any_str,
                                 checkpoints=validation.examples.flag_4,
                                 scan_mode=validation.examples.any_bool,
                                 session=validation.examples.save_path,
                                 sample=validation.examples.save_path,
                                 scan_resolution=validation.examples.resolution
                                 )


class GridSettings(utils.SettingsPopup):
    """
    Concrete popup representing the advanced clustering settings.

    Attributes
    ----------
    _merlin: bool
        Whether the merlin scan is enabled by default.
    _size: ComboBox[int]
        The widget controlling the scan size.
    _exposure_branches: VBranchedMixin[float, float, float, float]
        The various possible exposure time values. These are dependent on whether merlin is activated and the bit depth.
    _exposure: Spinbox
        The widget controlling the exposure time.
    _depth: ComboBox[int]
        The widget controlling the bit depth.
    _path: Entry
        The widget controlling the filepath.
    _extras: Flag[Stages]
        The widget controlling the metadata images.
    """

    def __init__(self, failure_action: typing.Callable[[Exception], None]):
        super().__init__()

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

        self._merlin = default_settings["scan_mode"]
        size = DeepSearch.SIZES.index(default_settings["scan_size"])
        self._size = utils.ComboBox(*DeepSearch.SIZES, start_i=size)
        self._size.dataPassed.connect(lambda v: self.settingChanged.emit("scan_size", v))
        self._size.dataFailed.connect(failure_action)
        self._exposure_branches = validation.VBranchedMixin[float, float, float, float](
            validation.RangeValidator.known((40e-9, 70)),
            validation.RangeValidator.known((100e-6, 5e-3)),
            validation.RangeValidator.known((600e-6, 5e-3)),
            validation.RangeValidator.known((1e-3, 5e-3)),
            branch=0)
        exposure = validation.examples.any_float + validation.Pipeline(validation.Step(self._exposure_branches,
                                                                                       desc="ensure the exposure time "
                                                                                            "is valid."),
                                                                       in_type=float, out_type=int)
        self._exposure = utils.Spinbox(default_settings["exposure_time"], 100e-6, exposure,
                                       display=(_add_unit, _sub_unit))
        self._exposure.dataPassed.connect(lambda v: self.settingChanged.emit("exposure_time", v))
        self._exposure.dataFailed.connect(failure_action)
        bit_depth = (1, 6, 12).index(default_settings["bit_depth"])
        self._depth = utils.ComboBox(1, 6, 12, start_i=bit_depth)
        self._depth.dataPassed.connect(lambda v: self.settingChanged.emit("bit_depth", v))
        self._depth.dataPassed.connect(self._edit_exposure)
        self._edit_exposure(bit_depth)
        self._depth.dataFailed.connect(failure_action)
        self._path = utils.Entry(default_settings["save_path"], validation.examples.file_path, "\"")
        self._path.dataPassed.connect(lambda v: self.settingChanged.emit("save_path", v))
        self._path.dataFailed.connect(failure_action)
        flags = map(lambda f, p: int(f) * 2 ** p, default_settings["checkpoints"], range(3, -1, -1))
        self._extras = utils.Flag(utils.Stages, utils.Stages(sum(flags)))
        self._extras.dataPassed.connect(lambda v: self.settingChanged.emit("checkpoints", v))
        self._extras.dataFailed.connect(failure_action)

        self._layout.addWidget(utils.DoubleLabelledWidget("Scan Size", self._size,
                                                          "The size (in pixels) of each grid square"))
        self._layout.addWidget(utils.DoubleLabelledWidget("Dwell Value", self._exposure,
                                                          "The exposure time of each scan"))
        self._layout.addWidget(utils.DoubleLabelledWidget("Bit Depth", self._depth,
                                                          "The bit depth for each scan"))
        self._layout.addWidget(utils.DoubleLabelledWidget("Save Path", self._path,
                                                          "The path to save the data to"))
        self._layout.addWidget(utils.DoubleLabelledWidget("Additional Files", self._extras,
                                                          "The extra stages to save into the dataset file"))

    def widgets(self) -> GridDict:
        return {"scan_size": self._size, "exposure_time": self._exposure, "bit_depth": self._depth,
                "save_path": self._path, "checkpoints": self._extras}

    def new_merlin_state(self, new: bool):
        """
        Change the merlin state.

        Parameters
        ----------
        new: bool
            The new state of the merlin scanner.
        """
        self._merlin = new
        if not new:
            self._exposure_branches.branch = 0
        self._depth.setEnabled(new)
        self._edit_exposure(self._depth.currentIndex())

    def _edit_exposure(self, new: int):
        if not self._merlin:
            return
        self._exposure_branches.branch = new
        if new == 0:
            return
        v = self._exposure.get_data()
        if new == 1 and v < 100e-6:
            self._exposure.change_data(100e-6)
        elif new == 6 and v < 600e-6:
            self._exposure.change_data(600e-6)
        elif new == 12 and v < 1e-3:
            self._exposure.change_data(1e-3)
        elif v > 5e-3:
            self._exposure.change_data(5e-3)


class DeepSearch(CanvasPage, SettingsPage[GridSettings], ProcessPage):
    """
    Concrete page representing the scanning of each exported region. This performs the scan at a much higher resolution.

    Signals
    -------
    scanPerformed:
        Emitted whenever a scan is performed. Contains no data.

    Attributes
    ----------
    SIZES: tuple[int, ...]
        The available sizes for the grid squares.
    _regions: tuple[ScanRegion, ...]
        The regions that are going to be scanned.
    _grids: Management
        The cluster manager spawning the grids.
    _image: SurveyImage
        The survey image controller.
    _marker: int_
        The colour of the scanned squares.
    _clusters: Callable[[], ndarray[uint8, (r, c, 3)]
        The function that will grab the cluster image and convert it into a matplotlib compatible 3D array as scan
        metadata.
    _pipeline: Callable[[], ndarray[uint8, (r, c, 3)]
        The function that will grab the pre-processed image and convert it into a matplotlib compatible 3D array as scan
        metadata.
    _survey: Callable[[], ndarray[uint8, (r, c, 3)]
        The function that will grab the survey image and convert it into a matplotlib compatible 3D array as scan
        metadata.
    _automate: bool
        Whether the run is fully automated (single-threaded).
    _logger: Logger | None
        The logger used to document drift.
    _scan_mode: LabelledWidget[CheckBox]
        The widget controlling whether merlin scan is enabled.
    _session: LabelledWidget[Entry]
        The widget controlling the session id. The string in the entry must be a valid save path.
    _sample: LabelledWidget[Entry]
        The widget controlling the sample. The string in the entry must be a valid save path.
    _progress: QProgressBar
        The widget indicating current progress.
    _mic: Microscope
        The link to the microscope system to read metadata.
    _scanner: Scanner
        The link to the scan-engine used to perform the scan.
    _resolution: int
        The current high-resolution being used.
    _i: int
        The index of the next square to scan.
    """
    settingChanged = SettingsPage.settingChanged
    scanPerformed = core.pyqtSignal()
    _clusterScanned = core.pyqtSignal(int)
    _newVal = core.pyqtSignal(int)
    SIZES = (64, 128, 256, 512)

    def __init__(self, size: int, grids: Management, image: SurveyImage, marker: np.int_, done: np.int_,
                 failure_action: typing.Callable[[Exception], None], mic: microscope.Microscope,
                 scanner: microscope.Scanner, clusters: Clusters, pipeline: ProcessingPipeline):
        DeepSearch.SIZES = tuple(s for s in DeepSearch.SIZES if s < size)
        CanvasPage.__init__(self, size)
        SettingsPage.__init__(self, utils.SettingsDepth.REGULAR | utils.SettingsDepth.ADVANCED,
                              functools.partial(GridSettings, failure_action))
        ProcessPage.__init__(self)

        def _cluster_image() -> np.ndarray:
            err = "Cannot add clustered image to save file when clustering has not been performed"
            if clusters.modified is None:
                raise GUIError(utils.ErrorSeverity.WARNING, "Specified Null Step", err)
            return self._img(clusters.modified)

        def _pipeline_image() -> np.ndarray:
            err = "Cannot add processed image to save file when clustering has not been performed"
            if pipeline.modified is None:
                raise GUIError(utils.ErrorSeverity.WARNING, "Specified Null Step", err)
            return self._img(pipeline.modified)

        def _survey_image() -> np.ndarray:
            return self._img(image.modified)

        self._colour_option.hide()
        self._regions: _tuple[utils.ScanRegion, ...] = ()
        self._grids = grids
        self._image = image
        self._marker = marker
        self._done = done
        self._clusters = _cluster_image
        self._pipeline = _pipeline_image
        self._survey = _survey_image
        self._automate = False
        self._i = 0
        self._logger: _None[logging.Logger] = None

        self._scan_mode = utils.LabelledWidget("Merlin Scan Mode", utils.CheckBox("&M", default_settings["scan_mode"]),
                                               utils.LabelOrder.SUFFIX)
        self._scan_mode.focus.dataPassed.connect(lambda v: self.settingChanged.emit("scan_mode", v))
        self._scan_mode.focus.dataPassed.connect(self._popup.new_merlin_state)
        self._scan_mode.focus.dataFailed.connect(failure_action)
        self._session = utils.LabelledWidget("Session",
                                             utils.Entry(default_settings["session"], validation.examples.save_path),
                                             utils.LabelOrder.SUFFIX)
        self._session.focus.dataPassed.connect(lambda v: self.settingChanged.emit("session", v))
        self._session.focus.dataFailed.connect(failure_action)
        self._sample = utils.LabelledWidget("Sample",
                                            utils.Entry(default_settings["sample"], validation.examples.save_path),
                                            utils.LabelOrder.SUFFIX)
        self._sample.focus.dataPassed.connect(lambda v: self.settingChanged.emit("sample", v))
        self._sample.focus.dataFailed.connect(failure_action)
        self._progress = widgets.QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setValue(0)
        self._progress.setFormat("%v/%m steps complete (%p%)")
        self._clusterScanned.connect(self._progress.setValue)
        self._newVal.connect(self._progress.setValue)

        self._regular.addWidget(self._scan_mode)
        self._regular.addWidget(self._session)
        self._regular.addWidget(self._sample)
        self._regular.addWidget(self._progress)

        self.setLayout(self._layout)
        self._mic = mic
        self._scanner = scanner

        self._resolution = default_settings["scan_resolution"]
        
        #### Adding code for drift correction- MD #####
       
        self.drift_correction = _drift.TranslateRegion(failure_action,
                                                       mic=self._mic, 
                                                       scanner=self._scanner, 
                                                       scan_func=lambda scan_type, bool_: self._scan(scan_type, bool_),  # Corrected scan_func, 
                                                       survey_size=(512,512))  # Correct survey_size)
                                                       # image.original.size())
        self._drift_ref = self.drift_correction.set_ref( tl=(5,5), br=(20,20))
        self.drift_correction.conditionHit.connect(self.perform_drift_correction)
        self.x_shift = 0
        self.y_shift = 0
    
    def _scan(self, scan_type, bool_) :
        return self._scanner.scan()
    
    def perform_drift_correction(self):
        print("********DRIFT CORR TRIGGERED******")
        # PAUSE before correction
        self._state = utils.StoppableStatus.PAUSED
        # self._run.pause.emit()
        self._run_drift_correction()
        self.update_grids(self.x_shift, self.y_shift)
        self._image.run()
        self._draw_images()
        #RESUME after correction
        self._state = utils.StoppableStatus.ACTIVE
    
    def _run_drift_correction(self):
    #  set reference image here
        # tl = (0, 0)  #  Top-left corner of the region
        # br = self._image.original.size # Bottom-right corner of the region
        # self.drift_correction.set_ref(tl, br)
        print("*****Line_364****")
        self.drift_correction.run()
        self.drift_correction.drift.connect(self.update_drift_values)
        # self.drift_correction.run()
        # self.drift_correction.drift.connect(self.update_drift_values)

    def update_drift_values(self, x, y):
        self.x_shift, self.y_shift = x, y        
        
        #### Adding code for drift correction- MD - end
        
        

    def _img(self, img: images.RGBImage) -> np.ndarray:
        w, h = self._canvas.image_size
        arr = np.zeros((h, w, 3))
        normalised = img.norm().data()
        r_mask = np.nonzero((normalised >= 0) & (normalised < 2 ** 8))
        g_mask = np.nonzero((normalised >= 2 ** 8) & (normalised < 2 ** 16))
        b_mask = np.nonzero((normalised >= 2 ** 16) & (normalised < 2 ** 24))
        arr[(*r_mask, 0)] = normalised[r_mask]
        arr[(*g_mask, 1)] = normalised[g_mask]
        arr[(*b_mask, 2)] = normalised[b_mask]
        return arr

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

    def update_resolution(self, new: int):
        """
        Update the resolution of the scan.

        Parameters
        ----------
        new: int
            The new scan resolution.
        """
        self._resolution = new

    def update_grids(self, x_shift: int, y_shift: int):
        """
        Move all the scan regions, linked to drift correction.

        Parameters
        ----------
        x_shift: int
            The number of pixels to horizontally shift the scan regions.
        y_shift: int
            The number of pixels to vertically shift the scan regions.
        """
        msg = f"Shifting all squares by {x_shift, y_shift}"
        if self._logger is None:
            print(msg)
        else:
            self._logger.debug(msg)
        lim = self._canvas.image_size[0]
        for grid in self._regions:
            grid.move((x_shift, y_shift))
            grid.disabled = (any(c < 0 for c in grid[Corners.TOP_LEFT]) or
                             any(c > lim for c in grid[Corners.BOTTOM_RIGHT]))
        self._image.run()
        self._draw_images()

    def _draw_images(self):
        self._modified_image = self._image.original.copy()
        for grid in self._regions[:self._i]:
            grid.draw(self._modified_image, self._done)
        for grid in self._regions[self._i:]:
            grid.draw(self._modified_image, 2 ** 24 - 1 - self._marker)
        self._canvas.draw(self._modified_image)
        self._original_image = self._modified_image.copy()

    @utils.Tracked
    def run(self):
        if self._state != utils.StoppableStatus.ACTIVE:
            return
        self._regions = self._grids.get_tight()
        if not self._regions:
            raise StagingError("grid search", "exporting tightened grids")
        self._progress.setMaximum(len(self._regions))
        self.runStart.emit()
        self._draw_images()
        if self._automate:
            self._run.py_func(None)
        elif microscope.ONLINE:
            self._run.wrapped(None)
        else:
            self._run()

    @utils.Stoppable.decorate(manager=ProcessPage.MANAGER)
    @utils.Tracked
    def _run(self, current: typing.Optional[int]):

        def _reg_scan():
            with self._mic.subsystems["Deflectors"].switch_blanked(False):
                with self._mic.subsystems["Detectors"].switch_inserted(True):
                    img = self._scanner.scan()
                    print(i)  # testing for making sure nonlocal variable is read properly
                    region_4k.save(f"{save_path}\\image_{i}.hdf5", img)

        def _file_write():
            with h5py.File(params, "w") as clear:
                clear.clear()
            with h5py.File(params, "a") as f:
                if images_saved & utils.Stages.MARKER:
                    f.create_dataset("Grid Marker", data=self._img(self._modified_image))
                if images_saved & utils.Stages.CLUSTERS:
                    f.create_dataset("Clusters Found", data=self._clusters())
                if images_saved & utils.Stages.PROCESSED:
                    f.create_dataset("Thresholded Image", data=self._pipeline())
                if images_saved & utils.Stages.SURVEY:
                    f.create_dataset("Survey Scan", data=self._survey())

        def _merlin_scan():
            time.sleep(1)
            try:
                print("******First Try******")
                # merlin_cmd.getVariable('DETECTORSTATUS', PRINT='ON')
                merlin_cmd.setValue('FILENAME', f"{stamp}_data")
            except IndexError:
                print("*****TRY AGAIN!**")
                merlin_cmd.setValue('FILENAME', f"{stamp}_data")
            merlin_cmd.setValue('TRIGGERSTART', 1)
            time.sleep(1)
            merlin_cmd.setValue('TRIGGERSTOP', 1)
            time.sleep(1)
            with self._mic.subsystems["Deflectors"].switch_blanked(False):
                merlin_cmd.MPX_CMD(type_cmd='CMD', cmd='SCANSTARTRECORD')
                time.sleep(1)
                print('6')
                self._scanner.scan(return_=False)
                time.sleep(1)
                print("********SET TRIGGER TO 0*******")
                merlin_cmd.setValue('TRIGGERSTART', 0) # changed from 0 - MD 
                merlin_cmd.setValue('TRIGGERSTOP', 0) #  changed from 0 - MD 
                time.sleep(1)

        if current is None:
            current = -1
            self._newVal.emit(0)
        if microscope.ONLINE:
            self._mic.subsystems["Deflectors"].blanked = True
        px_val = self.get_setting("scan_size")
        pixels = px_val ** 2
        exposure = self.get_setting("exposure_time")
        bit_depth = self.get_setting("bit_depth")
        images_saved = self.get_setting("checkpoints")
        do_merlin = self._scan_mode.focus.isChecked()
        save_path = self.get_setting("save_path").format(session=self._session.focus.text()[1:-1],
                                                         sample=self._sample.focus.text()[1:-1]).replace("/", "\\")
        try:
            validation.examples.save_path.validate(f"\'{save_path}\'")
        except validation.ValidationError as err:
            raise GUIError(utils.ErrorSeverity.ERROR, "Cannot validate save path", str(err))
        if microscope.ONLINE:
            self._scanner.scan_area = microscope.FullScan((self._resolution, self._resolution))
            self._scanner.dwell_time = exposure  # add pattern
            hostname = "10.182.0.5"
            merlin_cmd = microscope.merlin_connection.MERLIN_connection(hostname)
            print('Setup')
            # <editor-fold desc="Merlin config">
            print("******Detector STATUS******")
            merlin_cmd.getVariable('DETECTORSTATUS', PRINT='ON')
            
            merlin_cmd.setValue('NUMFRAMESTOACQUIRE', pixels)
            merlin_cmd.setValue('COUNTERDEPTH', bit_depth)
            merlin_cmd.setValue('CONTINUOUSRW', 1)
            merlin_cmd.setValue('ACQUISITIONTIME', (exposure / 2e3))
            merlin_cmd.setValue('FILEDIRECTORY', save_path)
            merlin_cmd.setValue('FILEENABLE', 1)
            # trigger set up and filesaving
            merlin_cmd.setValue('SAVEALLTOFILE', 1)
            merlin_cmd.setValue('USETIMESTAMPING', 0)
            # setting up VDF with STEM mode
            merlin_cmd.setValue('SCANX', px_val)
            merlin_cmd.setValue('SCANY', px_val)
            #        # set to pixel trigger
            merlin_cmd.setValue('SCANTRIGGERMODE', 0)
            merlin_cmd.setValue('SCANDETECTOR1ENABLE', 1)
            # Standard ADF det
            merlin_cmd.setValue('SCANDETECTOR1TYPE', 0)
            merlin_cmd.setValue('SCANDETECTOR1CENTREX', 128)
            merlin_cmd.setValue('SCANDETECTOR1CENTREY', 128)
            merlin_cmd.setValue('SCANDETECTOR1INNERRADIUS', 50)
            merlin_cmd.setValue('SCANDETECTOR1OUTERRADIUS', 150)
            # </editor-fold>

        original = self._original_image.data()
        print(f"*********regions num {len(self._regions)}************")
        for i, region in enumerate(self._regions):
            print(f"*********region {i}************")
            original = self._original_image.data()
            self._i = i + 1
            if i < current:
                print("#######L518######")
                continue
            elif self._state == utils.StoppableStatus.PAUSED:
                print("#######L521######")
                self._run.pause.emit(i)
                return
            elif self._state == utils.StoppableStatus.DEAD:
                print("#######L525######")
                with self._canvas as draw:
                    draw.data.reference()[:, :] = original.copy()
                return
            elif region.disabled:
                continue

            with self._canvas as draw:
                draw.data.reference()[:, :] = original.copy()
                region.draw(draw, self._marker)
                region.draw(self._original_image, self._done)
                if not microscope.ONLINE:
                    time.sleep(0.5)

            if microscope.ONLINE:
                with self._mic.subsystems["Detectors"].switch_inserted(False):
                    region_4k = region @ self._resolution
                    top_left, top_left_4k = region[Corners.TOP_LEFT], region_4k[Corners.TOP_LEFT]
                    bottom_right = region[Corners.BOTTOM_RIGHT]
                    scan_area = microscope.AreaScan((self._resolution, self._resolution),
                                                    (px_val, px_val), top_left_4k)
                    with self._scanner.switch_scan_area(scan_area):
                        print(f"******scan area: {scan_area.rect}******")
                        if not os.path.exists(save_path):
                            os.makedirs(save_path)
                            print(f"Made dir: {save_path}")
                        self._logger = logging.Logger("drift", level=logging.DEBUG)
                        logging.basicConfig(level=logging.DEBUG,
                                            filename=f"{save_path}\\drift.log", filemode="a", force=True)
                        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        params = f"{save_path}\\{stamp}.hdf5"
                        if not do_merlin:
                            print("************4********")
                            _reg_scan()
                        else:
                            print(params)
                            print("************3********")
                        _file_write()
                        if do_merlin:
                            with h5py.File(params, "a") as co_ords:
                                dset = co_ords.create_group("Co-ordinates (cartesian, non-scaled)")
                                dset.attrs["top left"] = top_left
                                dset.attrs["bottom right"] = bottom_right
                            merlin_params = {'set_dwell_time(usec)': exposure, 'set_scan_px': px_val,
                                             'set_bit_depth': bit_depth}
                            self._mic.export(params, px_val, **merlin_params)
                            with self._scanner.using_connection(6, microscope.TTLMode.SOURCE_TIMED,
                                                                microscope.PixelClock(microscope.EdgeType.RISING),
                                                                active=1e-5):
                                print("************2********")
                                _merlin_scan()
                            self.drift_correction.scans_increased()
                            print("******SCAN INCREASED*****")
                            # Here we need to check if the criteria for drift corr is met
                            # Do we need to pause?
                            self.drift_correction.query()
                            print(self.drift_correction.query())
                            
            if self._progress.isEnabled():
                print("************1********")
                self.scanPerformed.emit()
                self._clusterScanned.emit(i + 1)

        with self._canvas as draw:
            draw.data.reference()[:, :] = original.copy()
        self.runEnd.emit()
        self.clear()

    def automate(self):
        """
        Perform an automated, single-threaded run.
        """
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

            The exposure time in seconds. Dependant on the bit depth and whether a Merlin scan is being performed.

            If doing a merlin scan, then it should be between 40ns and 70s (which is formatted as '70 s').
            Otherwise, it has an upper limit of 5ms and a variable lower limit (dependant on bit depth).
        Bit Depth:
            {self.get_control('bit_depth').validation_pipe()}

            The bit depth to use when communicating with Merlin.

            When using 12-bit depth, the lower limit of the `Dwell Value` is 1ms;
            When using 6-bit depth, the lower limit of the `Dwell Value` is 600us;
            When using 1-bit depth, the lower limit of the `Dwell Value` is 100us.
        Save Path:
            {validation.examples.file_path}

            The save path to use for the output files.
            Using python f-string style substitution ({{session}}) will substitute the relevant variable.
            Note that "session" and "sample" are the only supported variables.
        Additional Files:
            {self.get_control('checkpoints').validation_pipe()}

            The extra files to save into the HDF5 file. Each image will have its own dataset."""
        return s
