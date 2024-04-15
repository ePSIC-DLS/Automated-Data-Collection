import re
import typing
from typing import Tuple as _tuple, Optional as _None

from PyQt5 import QtWidgets as widgets

from . import pages, bases, utils
from .. import images, microscope
from ..language.grammar import KeywordType

app = widgets.QApplication([])


def _help(text: str) -> str:
    text = re.sub(r"#\n", "", text)  # code too long marker
    text = re.sub(r" {16}", " " * 14, text)  # slightly offset to not double catch the 8 spaces
    text = re.sub(r" {8}", "", text)  # perform 8 spaces replacement
    text = re.sub(r";\n", f";9", text)  # replace trailing semicolons, as these are line too long markers
    text = re.sub(r"; ", f";\n{' ' * 4}", text)  # expand semicolons with trailing space
    text = re.sub(r";9( *)", f"; ", text)  # truncate replaced semicolons, squishing into one line
    text = re.sub(r" {6}", " " * 8, text)  # re-adjust for the 8 spaces offset
    return text


class CombinedPage(widgets.QWidget):

    def __init__(self, **containing: bases.Page):
        super().__init__()
        layout = widgets.QVBoxLayout()
        self._master = widgets.QTabWidget()
        self._master.setTabShape(self._master.Triangular)
        layout.addWidget(self._master)
        for i, (name, page) in enumerate(containing.items()):
            self._master.addTab(page, name.title())
            self._master.setTabToolTip(i, _help(page.help()))
        self.setLayout(layout)

    def switch_view(self, i: int):
        self._master.setCurrentIndex(i)


class GUI(widgets.QMainWindow):

    def __init__(self, size: int):
        def _update_thresh(name: str, value):
            if name == "minima":
                stage_2.set_setting("_minima", value)
            elif name == "maxima":
                stage_2.set_setting("_maxima", value)

        def _update_hist(name: str, value):
            if name == "minima":
                stage_h.update_min(value)
            elif name == "maxima":
                stage_h.update_max(value)

        def _update_pitches(name: str, value):
            if name == "scan_size":
                pitch = value // (stage_p.get_setting("scan_resolution") // size)
                stage_1.set_pitch_size(pitch)
                stage_3.set_pitch_size(pitch)
                stage_4.update_label()
            elif name == "scan_resolution":
                pitch = stage_5.get_setting("scan_size") // (value // size)
                stage_1.set_pitch_size(pitch)
                stage_3.set_pitch_size(pitch)
                stage_4.update_label()

        def _auto_variable(name: str, value):
            for stage, settings in stage_settings.items():
                if name in settings:
                    stages[stage].set_setting(name, value)

        def _data_failed(exc: Exception):
            stage_a.interpreter().fail(exc)

        super().__init__()
        layout = widgets.QVBoxLayout()
        actions = widgets.QHBoxLayout()

        row = widgets.QWidget()
        row.setLayout(actions)

        self._master = widgets.QTabWidget()
        layout.addWidget(self._master)
        layout.addWidget(row)

        central = widgets.QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

        self._microscope = microscope.Microscope(microscope.Detector.ADF1, True, microscope.ImagingMode.STEM,
                                                 microscope.Lens.CL1, microscope.Axis.X, beam=False, valve=True)
        self._scanner = microscope.Scanner(microscope.FullScan((size, size)), dwell_time=15e-6)

        self._master.setUsesScrollButtons(False)
        stage_1 = pages.pipeline.SurveyImage(size, images.RGB(255, 0, 0), 8, self._microscope, self._scanner)
        stage_2 = pages.pipeline.ProcessingPipeline(size, stage_1, _data_failed)
        stage_3 = pages.pipeline.Clusters(size, images.RGB(255, 0, 0), 8, stage_2, _data_failed)
        stage_4 = pages.pipeline.Management(size, stage_1, stage_3, _data_failed)
        stage_5 = pages.pipeline.DeepSearch(size, stage_4, stage_1, images.RGB(0, 255, 0), _data_failed,
                                            self._microscope, self._scanner)

        stage_h = pages.additionals.Histogram(size, stage_1, images.Grey(255), _data_failed)
        stage_p = pages.additionals.ScanType(size, images.RGB(255, 0, 0), _data_failed)
        stage_c = pages.additionals.Manager(_data_failed, self._microscope, self._scanner, (size, size))
        stage_f = pages.additionals.DiffractionFilter(stage_3)
        corrections = stage_c.corrections()
        focus = corrections["focus"]
        emission = corrections["emission"]
        drift = corrections["drift"]

        script_handlers = {
            KeywordType.SURVEY: self._jump(stage_h.run, 1, None),
            KeywordType.SEGMENT: self._jump(stage_3.automate, 3, None),
            KeywordType.FILTER: stage_f.automate,
            KeywordType.INTERACT: self._jump(stage_4.automate_click, 4, None),
            KeywordType.MANAGE: stage_4.automate_tighten,
            KeywordType.SCAN: self._jump(stage_5.automate, 5, (5, 1))
        }
        stage_a = pages.additionals.Scripts(
            _auto_variable,
            {
                **{k: stage_1.get_setting(k) for k in stage_1.all_settings()},
                **{k: stage_h.get_setting(k) for k in stage_h.all_settings()},
                **{k: stage_2.get_setting(k) for k in stage_2.all_settings()},
                **{k: stage_3.get_setting(k) for k in stage_3.all_settings()},
                **{k: stage_f.get_setting(k) for k in stage_f.all_settings()},
                **{k: stage_4.get_setting(k) for k in stage_4.all_settings()},
                **{k: stage_p.get_setting(k) for k in stage_p.all_settings()},
                **{k: stage_5.get_setting(k) for k in stage_5.all_settings()},
                **{k: focus.get_setting(k) for k in focus.all_settings()},
                **{k: emission.get_setting(k) for k in emission.all_settings()},
                **{k: drift.get_setting(k) for k in drift.all_settings()},
                "corner": images.AABBCorner,
                "underflow": utils.UnderflowHandler,
                "overflow": utils.OverflowHandler,
                "random": utils.RandomTypes,
                "kernel_shape": images.MorphologicalShape,
                "number_match": utils.Match,
                "axis": utils.Extreme,
                "staging": utils.Stages,
                "windows": utils.Windowing,
                "window_order": list(lab.text() for lab in drift.get_setting("window_order"))
            },
            script_handlers,
            blur=stage_2.single_stage("blur"),
            gss_blur=stage_2.single_stage("gss_blur"),
            sharpen=stage_2.single_stage("sharpen"),
            median=stage_2.single_stage("median"),
            edge=stage_2.single_stage("edge"),
            threshold=stage_2.single_stage("threshold"),
            open=stage_2.single_stage("open"),
            close=stage_2.single_stage("close"),
            gradient=stage_2.single_stage("gradient"),
            i_gradient=stage_2.single_stage("i_gradient"),
            e_gradient=stage_2.single_stage("e_gradient"),
            Raster=stage_p.raster,
            Snake=stage_p.snake,
            Spiral=stage_p.spiral,
            Grid=stage_p.checkerboard,
            Random=stage_p.random,
            correct_for=stage_c.run_now
        )

        stage_gh = pages.additionals.WhatsThis(
            Preprocessing_Options=_help(stage_2.advanced_help()),
            Segmentation_Settings=_help(stage_3.advanced_help()),
            Manager_Settings=_help(stage_4.advanced_help()),
            Scan_Patterns=_help(stage_p.advanced_help()),
            Grid_Search_Settings=_help(stage_5.advanced_help()),
            **{f"{stage_a.L_NAME}_Grammar": _help(stage_a.advanced_help()),
               f"{stage_a.L_NAME}_Standard_Library": _help(stage_a.standard_library())}
        )

        self._floating = pages.additionals.WhatsThis(
            **stage_gh.items(),
            Survey_Image=_help(stage_1.help()),
            Survey_Histogram=_help(stage_h.help()),
            Processed_Image=_help(stage_2.help()),
            Segmented_Image=_help(stage_3.help()),
            Segmented_Analysis=_help(stage_f.help()),
            Cluster_Manager=_help(stage_4.help()),
            Grid_Search_Pattern=_help(stage_p.help()),
            Grid_Search_Scan=_help(stage_5.help()),
            Focus_Correction=_help(focus.help()),
            Emission_Correction=_help(emission.help()),
            Drift_Correction=_help(drift.help()),
        )

        self._floating.show()

        self._pages: _tuple[bases.Page, ...] = (stage_1, stage_2, stage_3, stage_4, stage_5,
                                                stage_h, stage_p, stage_c, stage_f, stage_gh, stage_a)

        stages = locals()
        stage_settings = {f"stage_{x}": set(stages[f"stage_{x}"].all_settings())
                          for x in ("1", "h", "2", "3", "f", "4", "p", "5")}
        stage_settings["focus"] = set(focus.all_settings())
        stage_settings["emission"] = set(emission.all_settings())
        stage_settings["drift"] = set(drift.all_settings())

        stage_h.settingChanged.connect(_update_thresh)
        stage_2.settingChanged.connect(_update_hist)
        stage_5.settingChanged.connect(_update_pitches)
        stage_p.settingChanged.connect(_update_pitches)
        stage_1.runEnd.connect(lambda: drift.set_reference(stage_1.original.demote("r").image()))
        stage_5.scanPerformed.connect(focus.scans_increased)
        stage_5.scanPerformed.connect(drift.scans_increased)
        focus.runStart.connect(lambda: self._pause(-1))
        drift.runStart.connect(lambda: self._pause(-1))
        focus.runEnd.connect(lambda: self._resume(-1))
        drift.runEnd.connect(lambda: self._resume(-1))

        self._master.addTab(stage_gh, "GUI Help (&0)")
        self._master.addTab(CombinedPage(image=stage_1, histogram=stage_h), "Survey (&1)")
        self._master.setTabToolTip(1, "A page showcasing the survey image and its histogram")
        self._master.addTab(stage_2, "Processed Image (&2)")
        self._master.setTabToolTip(2, _help(stage_2.help()))
        self._master.addTab(CombinedPage(image=stage_3, analysis=stage_f), "Segmented (&3)")
        self._master.setTabToolTip(3, "A page showcasing the clusters and the diffraction filters")
        self._master.addTab(stage_4, "Cluster Manager (&4)")
        self._master.setTabToolTip(4, _help(stage_4.help()))
        self._master.addTab(CombinedPage(pattern=stage_p, scan=stage_5), "Grid Search (&5)")
        self._master.setTabToolTip(5, "A page showcasing the pattern (per square) and scans each square")
        self._master.addTab(stage_c, "Corrections (&6)")
        self._master.setTabToolTip(6, _help(stage_c.help()))
        self._master.addTab(stage_a, "Automation Scripts (&7)")
        self._master.setTabToolTip(7, _help(stage_a.help()))
        stage_c.add_tooltip(0, _help(focus.help()))
        stage_c.add_tooltip(1, _help(emission.help()))
        stage_c.add_tooltip(2, _help(drift.help()))

        scan = widgets.QPushButton("Scan (&A)")
        process = widgets.QPushButton("Threshold (&B)")
        cluster = widgets.QPushButton("Cluster (&C)")
        search = widgets.QPushButton("Search (&D)")

        pause = widgets.QCheckBox("Paused (&P)")
        stop = widgets.QCheckBox("Stopped (&S)")

        scan.clicked.connect(self._jump(stage_h.run, 1, (1, 0)))
        process.clicked.connect(self._jump(stage_2.run, 2, (2, None)))
        cluster.clicked.connect(self._jump(stage_3.run, 3, (3, 0)))
        search.clicked.connect(self._jump(stage_5.run, 5, (5, 1)))
        pause.stateChanged.connect(lambda: self._pause() if pause.isChecked() else self._resume())
        stop.stateChanged.connect(lambda: self._stop() if stop.isChecked() else self._resume())

        self._btns = (scan, process, cluster, search, pause, stop)
        for btn in self._btns:
            actions.addWidget(btn)

    def _jump(self, wrapped: typing.Callable[[], None], clear_from: int, jump_to: _None[_tuple[int, _None[int]]]) \
            -> typing.Callable[[], None]:
        def _wrapper():
            for page in self._pages[clear_from:]:
                page.clear()
            if jump_to is None:
                wrapped()
                return
            pri, sec = jump_to
            self._master.setCurrentIndex(pri)
            wid = self._master.currentWidget()
            if isinstance(wid, CombinedPage):
                wid.switch_view(sec)
            wrapped()

        return _wrapper

    def _pause(self, upto: int = None):
        for page in self._pages[:upto]:
            page.pause()

    def _resume(self, upto: int = None):
        for page in self._pages[:upto]:
            page.start()

    def _stop(self, upto: int = None):
        for page in self._pages[:upto]:
            page.stop()

    def closeEvent(self, a0):
        self._stop()
        self._floating.close()
        bases.ProcessPage.MANAGER.waitForDone()
        super().closeEvent(a0)


def main():
    window = GUI(512)
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
