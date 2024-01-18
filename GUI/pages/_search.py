"""
Module to represent a focussed search on individual grid squares.
"""
import functools
import time
import typing
import os
from PyQt5.QtCore import Qt as enums

from modular_qt import errors, microscope, validators
from . import base, extra_widgets, __pyjem__
from ._cluster import SegmentationPage
from ._scan import ScanPage
from .base import widgets, core, utils, sq


class MerlinSettings(utils.AdvancedSettingWindow):
    """
    Subclass to represent settings that the Merlin software controls.

    :cvar SIZES tuple[int, ...]: The possible sizes that a grid scan can be.
    :cvar EXPOSURE tuple[int, int]: The range of exposure times.
    :cvar DEPTH tuple[int, ...]: The possible bit depths.

    :var _size ComboSpin: The size control.
    :var _exposure FixedSpinBox: The exposure control.
    :var _depth ComboSpin: The bit depth control.
    """
    SIZES = validators.xmpls.scan_size.values
    EXPOSURE = (validators.xmpls.exposure.bounds[0], validators.xmpls.exposure.bounds[-1],
                validators.xmpls.exposure.mod)
    DEPTH = validators.xmpls.bit_depth.values

    def _change_depth(self, new: int):
        if new == 1:
            self._exposure.setMinimum(100)
        elif new == 6:
            self._exposure.setMinimum(600)
        elif new == 12:
            self._exposure.setMinimum(1000)

    def __init__(self, size: int):
        super().__init__()
        self._size = extra_widgets.ComboSpin(*(s for s in self.SIZES if s < size), start=-1)
        self._exposure = extra_widgets.FixedSpinBox(self.EXPOSURE, "usec", value=600)
        self._depth = extra_widgets.ComboSpin(*self.DEPTH, start=2)
        self._depth.valueChanged.connect(self._change_depth)
        self._path = widgets.QLineEdit("X:/data/2023/{session}/Merlin/{sample}")
        self._path.setMinimumWidth(150)
        self._survey = widgets.QCheckBox()
        self._survey.setCheckState(enums.Checked)
        self._threshold = widgets.QCheckBox()
        self._threshold.setCheckState(enums.Checked)
        self._segments = widgets.QCheckBox()
        self._segments.setCheckState(enums.Checked)
        self._grid = widgets.QCheckBox()
        self._grid.setCheckState(enums.Checked)
        self._layout.addWidget(widgets.QLabel("Scan Size"), 0, 0)
        self._layout.addWidget(self._size, 0, 1)
        self._layout.addWidget(widgets.QLabel("(The size of each scan)"), 0, 2)
        self._layout.addWidget(widgets.QLabel("Dwell Value"), 1, 0)
        self._layout.addWidget(self._exposure, 1, 1)
        self._layout.addWidget(widgets.QLabel("(The exposure time for each scan)"), 1, 2)
        self._layout.addWidget(widgets.QLabel("Bit Depth"), 2, 0)
        self._layout.addWidget(self._depth, 2, 1)
        self._layout.addWidget(widgets.QLabel("(The bit depth of each scan)"), 2, 2)
        self._layout.addWidget(widgets.QLabel("Save Path"), 3, 0)
        self._layout.addWidget(self._path, 3, 1)
        self._layout.addWidget(widgets.QLabel("(The path to save the data to)"), 3, 2)
        self._layout.addWidget(widgets.QLabel("Capture survey image?"), 4, 0)
        self._layout.addWidget(self._survey, 4, 1)
        self._layout.addWidget(widgets.QLabel("(Whether to record the survey image in each scanned file)"), 4, 2)
        self._layout.addWidget(widgets.QLabel("Capture binary image?"), 5, 0)
        self._layout.addWidget(self._threshold, 5, 1)
        self._layout.addWidget(widgets.QLabel("(Whether to record the thresholded in each scanned file)"), 5, 2)
        self._layout.addWidget(widgets.QLabel("Capture clusters?"), 6, 0)
        self._layout.addWidget(self._segments, 6, 1)
        self._layout.addWidget(widgets.QLabel("(Whether to record the segments in each scanned file)"), 6, 2)
        self._layout.addWidget(widgets.QLabel("Capture grid?"), 7, 0)
        self._layout.addWidget(self._grid, 7, 1)
        self._layout.addWidget(widgets.QLabel("(Whether to record the grid (with marker) in each scanned file)"), 7, 2)

    def widgets(self) -> dict[str, widgets.QWidget]:
        return dict(
            scan_size=self._size,
            exposure_time=self._exposure,
            bit_depth=self._depth,
            save_path=self._path,
            do_scan=self._survey,
            do_threshold=self._threshold,
            do_cluster=self._segments,
            do_search=self._grid
        )


class FocusScanPage(base.DrawingPage, base.ProcessPage, base.SettingsPage):
    """
    Concrete subclass to represent the grid searching page.

    :cvar SIZES tuple[int, ...]: The possible sizes a regular scan can take.
    :cvar _index_sig PyQt5.QtCore.pyqtSignal: The signal to emit internally to update progress bar.
    :var _just_image PyQt5.QWidgets.QCheckBox: Whether to collect 4D STEM data.
    :var _clusters SegmentationPage: The previous stage in the pipeline.
    :var _extra_regions ScanPage: The first stage in the pipeline.
    :var _event_colour Colour: The colour to fill the currently scanning square.
    """
    SIZES = MerlinSettings.SIZES[1:] + (MerlinSettings.SIZES[-1] * 2,)
    scan = core.pyqtSignal(int)
    _index_sig = core.pyqtSignal(int)

    @property
    def scans(self) -> int:
        """
        Public access to the number of scans performed.

        :return: The number of scans.
        """
        return self._scans

    @scans.setter
    def scans(self, value: int):
        """
        Public access to modify the number of scans. Will emit the scan signal with the new value.

        :param value: The value to modify the number of scans to.
        """
        self._scans = value
        self.scan.emit(value)

    def __init__(self, size: int, manager: core.QThreadPool, prev: SegmentationPage, start: ScanPage, *,
                 colour: sq.Colour, survey: typing.Callable[[], sq.Image], binary: typing.Callable[[], sq.Image],
                 colours: typing.Callable[[], sq.Image]):
        super().__init__(size)
        super(base.DrawingPage, self).__init__(manager)
        super(base.ProcessPage, self).__init__(utils.Settings.REGULAR | utils.Settings.ADVANCED,
                                               functools.partial(MerlinSettings, size))
        super(base.SettingsPage, self).__init__()
        self._colour.hide()
        self._just_image = widgets.QCheckBox("4D Scan?")
        self._just_image.setCheckState(enums.Checked)
        self._session = widgets.QLineEdit("Session: cm33902-5")
        self._sample = widgets.QLineEdit("Sample: test_xgrating")
        self._session.setValidator(extra_widgets.PrefixedValidator("Session:"))
        self._sample.setValidator(extra_widgets.PrefixedValidator("Sample:"))
        self._progress = widgets.QProgressBar()
        self._index_sig.connect(lambda i: self._progress.setValue(i))
        self._progress.setRange(0, 0)
        self._progress.setValue(0)
        self._progress.setFormat("%v/%m steps complete (%p%)")
        self._reg_col.addWidget(self._just_image)
        self._reg_col.addWidget(self._session)
        self._reg_col.addWidget(self._sample)
        self._reg_col.addWidget(self._progress)
        self._clusters = prev
        self._extra_regions = start
        self._event_colour = colour
        self._scans = 0
        self._find_functions = {
            "scan": survey,
            "threshold": binary,
            "cluster": colours,
            "search": self.get_original
        }
        self._link: microscope.Microscope = microscope.Microscope.get_instance()
        self.get_control("scan_size").valueChanged.connect(start.update_pitch)
        start.update_pitch(self.get_setting("scan_size"))

    @staticmethod
    def _get_entry(widget: widgets.QLineEdit) -> str:
        text = widget.text()
        pre = widget.validator().prefix
        ind = text.find(pre)
        if ind == -1:
            return text
        return text[ind + len(pre):].strip()

    def compile(self) -> str:
        return "search"

    def stop(self):
        base.DrawingPage.stop(self)
        base.ProcessPage.stop(self)
        base.SettingsPage.stop(self)

    start = base.SettingsPage.start

    @base.SettingsPage.lock
    def run(self, btn_state: bool):
        """
        Scans all tightened grid squares and additional regions created by the original scan.

        :param btn_state: The state of the button that caused the callback.
        :raise StagingError: If called before any grid squares are tightened.
        """
        self.triggered.emit(self.run)
        regions = self._clusters.squares + self._extra_regions.regions
        if not regions:
            raise errors.StagingError("Searching Grid Squares", "Tightening Grid Squares")
        self._curr = self._clusters.get_original()
        self._original = self._curr.copy()
        do_4d = self._just_image.checkState() == enums.Checked
        save_path = self.get_setting("save_path").format(session=self._get_entry(self._session),
                                                         sample=self._get_entry(self._sample))
        try:
            validators.file_path.validate(save_path)
        except validators.ValidationError as err:
            raise errors.DialogError(errors.Level.ERROR, "Cannot validate save path", str(err))
        px_val = self.get_setting("scan_size")
        pixels = px_val ** 2
        dwell_val = self.get_setting("exposure_time")
        bit_depth = self.get_setting("bit_depth")
        images = {k: v for k, v in self._find_functions.items() if self.get_setting(f"do_{k}") == enums.Checked}
        hostname = "10.182.0.5"
        raw = self._curr.get_raw()
        original = self._clusters.get_mutated().get_channeled_image()
        colour = self._event_colour.all(sq.RGBOrder.BGR)
        self._progress.setMaximum(len(regions))

        def _search():
            from modular_qt import utils as scans
            raw[:, :, :] = original
            for i, region in enumerate(regions):
                if not self._activated:
                    self._canvas.image(raw[:, :, ::-1])
                    return
                if self._tracked_index > i:
                    continue
                self._tracked_index = i
                self._index_sig.emit(i + 1)
                left, top = region.extract_point(scans.HSide.LEFT | scans.VSide.TOP)
                right, bottom = region.extract_point(scans.HSide.RIGHT | scans.VSide.BOTTOM)
                raw[top:bottom, left:right] = colour
                self._canvas.image(raw[:, :, ::-1])
                self.scans += 1
                if __pyjem__:
                    with self._link.scan_mode(microscope.ScanMode.AREA):
                        region_4k = region.conv_to(4096)
                        top_left = region_4k.extract_point(scans.HSide.LEFT | scans.VSide.TOP)
                        bottom_right = region_4k.extract_point(scans.HSide.RIGHT | scans.VSide.BOTTOM)
                        self._link["detector.position"] = top_left
                        if not do_4d:
                            self._link["detector.dwell_time"] = 15
                            with self._link.blanked(False):
                                with self._link.detector(insertion=True):
                                    img = self._link.detector_controller.scan()
                                    scans.save_arr_to_file(img.extract_channel("r"), f"saved_files/image_{i}.hdf5",
                                                           top_left, bottom_right)
                        else:
                            stamp = self._link.time_stamp
                            params = f"{save_path}\\{stamp}.hdf5"
                            print(params)
                            if not os.path.exists(save_path):
                                os.makedirs(save_path)
                                print(f"Made dir: {save_path}")
                            merlin_params = {'set_dwell_time(usec)': dwell_val, 'set_scan_px': px_val,
                                             'set_bit_depth': bit_depth}
                            self._link.write(params, **merlin_params)
                            self._link["detector.dwell_time"] = dwell_val
                            with self._link.blanked(True):
                                with self._link.detector(insertion=False):
                                    with self._link.scan_mode(microscope.ScanMode.SPOT):
                                        merlin_cmd = microscope.Merlin(hostname, channel="cmd")
                                        print('*****3*****')
                                        # <editor-fold desc="Merlin config">
                                        merlin_cmd.setValue('NUMFRAMESTOACQUIRE', pixels)
                                        merlin_cmd.setValue('COUNTERDEPTH', bit_depth)
                                        merlin_cmd.setValue('CONTINUOUSRW', 1)
                                        merlin_cmd.setValue('ACQUISITIONTIME', dwell_val * 1e-6)
                                        merlin_cmd.setValue('FILEDIRECTORY', save_path)
                                        merlin_cmd.setValue('FILENAME', f"{stamp}_data")
                                        merlin_cmd.setValue('FILEENABLE', 1)
                                        # trigger set up and filesaving
                                        merlin_cmd.setValue('TRIGGERSTART', 1)
                                        merlin_cmd.setValue('TRIGGERSTOP', 1)
                                        merlin_cmd.setValue('SAVEALLTOFILE', 1)
                                        merlin_cmd.setValue('USETIMESTAMPING', 1)
                                        # setting up VDF with STEM mode
                                        merlin_cmd.setValue('SCANX', px_val)
                                        merlin_cmd.setValue('SCANY', px_val)
                                        #        # set to pixel trigger
                                        merlin_cmd.setValue('SCANTRIGGERMODE', 0)
                                        merlin_cmd.setValue('SCANDETECTOR1ENABLE', 1)
                                        # Standard ADF det
                                        merlin_cmd.setValue('SCANDETECTOR1TYPE', 0)
                                        merlin_cmd.setValue('SCANDETECTOR1CENTREX', 255)
                                        merlin_cmd.setValue('SCANDETECTOR1CENTREY', 255)
                                        merlin_cmd.setValue('SCANDETECTOR1INNERRADIUS', 50)
                                        merlin_cmd.setValue('SCANDETECTOR1OUTERRADIUS', 150)
                                        # </editor-fold>
                                        print('**5**')
                                        merlin_cmd.MPX_CMD(type_cmd='CMD', cmd='SCANSTARTRECORD')
                                        print('6')
                                        if px_val == 64:
                                            flyback = 2 * dwell_val * pixels
                                        else:
                                            # flyback = 1.7 * (dwell_val/1e6) * pixels
                                            flyback = 75
                                        total_frametime = int(dwell_val / 1000 * pixels + (flyback * px_val))
                                        print(total_frametime)
                            time.sleep(total_frametime / 1000)
                            del merlin_cmd
                            time.sleep(0.001)
                raw[:, :, :] = original
            raw[:, :, :] = original
            self._canvas.image(raw[:, :, ::-1])

        if __pyjem__:
            self._link["detector.scan_mode"] = microscope.ScanMode.FULL
            self._link["detector.scan_size"] = 4096
            time.sleep(1)
        self._thread(_search)()
