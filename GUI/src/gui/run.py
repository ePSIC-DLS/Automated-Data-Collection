import enum
import functools
import re
import typing
from typing import List as _list, Optional as _None, Tuple as _tuple

from PyQt5 import QtWidgets as widgets

from . import bases, pages, utils
from .. import images, load_settings, microscope
from ..language import objs, OpCodes, vals
from ..validation import examples as pipelines

app = widgets.QApplication([])

sizes = load_settings("assets/config.json", size=pipelines.survey_size, scan_size=pipelines.survey_size,
                      scan_resolution=pipelines.resolution)


def _help(text: str) -> str:
    text = re.sub(r"#\n", "", text)  # code too long marker
    text = re.sub(r" {16}", " " * 14, text)  # slightly offset to not double catch the 8 spaces
    text = re.sub(r" {8}", "", text)  # perform 8 spaces replacement
    text = re.sub(r";\n", ";9", text)  # replace trailing semicolons, as these are line too long markers
    text = re.sub(r"; ", f";\n{' ' * 4}", text)  # expand semicolons with trailing space
    text = re.sub(r";9( *)", "; ", text)  # truncate replaced semicolons, squishing into one line
    text = re.sub(r" {6}", " " * 8, text)  # re-adjust for the 8 spaces offset
    return text


class CombinedPage(widgets.QWidget):

    def __init__(self, starting_index=0, /, **containing: bases.Page):
        super().__init__()
        layout = widgets.QVBoxLayout()
        self._master = widgets.QTabWidget()
        self._master.setTabShape(self._master.Triangular)
        layout.addWidget(self._master)
        for i, (name, page) in enumerate(containing.items()):
            self._master.addTab(page, name.title())
            self._master.setTabToolTip(i, _help(page.help()))
        self.setLayout(layout)
        self.switch_view(starting_index)

    def switch_view(self, i: int):
        self._master.setCurrentIndex(i)


class GUI(widgets.QMainWindow):

    def __init__(self, size: int, cluster_colour: int, marker_colour: int, histogram_outline: int, pattern_colour: int,
                 init_dwell: float, finished_colour: int):
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
                stage_p.change_size(value)
            elif name == "scan_resolution":
                pitch = stage_5.get_setting("scan_size") // (value // size)
                stage_1.set_pitch_size(pitch)
                stage_3.set_pitch_size(pitch)
                stage_4.update_label()
                stage_5.update_resolution(value)

        def _auto_variable(name: str, value: vals.Value):
            if name in {"Corner", "Underflow", "Overflow", "Random", "KernelShape", "NumberMatch", "Axis", "Staging"}:
                _data_failed(NameError(f"Cannot set native variable {name!r}"))
                return
            print(f"{name = }, raw_{value = !s}", end=" ")
            if isinstance(value, vals.Array):
                value = tuple(map(lambda x: x.raw, value.raw))
            else:
                value = value.raw
            print(f"{value = }")
            for stage, settings in stage_settings.items():
                if name in settings:
                    stages[stage].set_setting(name, value)
                    return
            if name == "dwell_time":
                self._scanner.dwell_time = value
                stage_m.read()
            elif name == "flyback":
                self._scanner.flyback = value
                stage_m.read()

        def _auto_keyword(code: int):
            if code == OpCodes.SCAN.value:
                self._jump(stage_h.run, 1, None)()
            elif code == OpCodes.CLUSTER.value:
                self._jump(stage_3.automate, 3, None)()
            elif code == OpCodes.MARK.value:
                self._jump(stage_4.automate_click, 4, None)()
            elif code == OpCodes.TIGHTEN.value:
                stage_4.automate_tighten()
            else:
                self._jump(stage_5.automate, 5, (5, 1))

        def _data_failed(exc: Exception):
            stage_a.interpreter().error(str(exc))

        def _compile() -> str:
            return "\n".join(compiled for s_ in self._pages if (compiled := s_.compile()))

        def _value(name: str, obj) -> vals.Value:
            if isinstance(obj, bool):
                return vals.Bool(obj)
            elif isinstance(obj, (int, float)):
                return vals.Number(obj)
            elif isinstance(obj, str):
                if name == "algorithm":
                    return vals.Algorithm(obj)
                elif name in {"session", "sample"}:
                    return vals.Path(obj)
                else:
                    return vals.String(obj)
            elif isinstance(obj, enum.Enum):
                return vals.Number(obj.value)
            elif isinstance(obj, utils.Design):
                return objs.NativeClass(obj)
            elif obj is None:
                return vals.Nil()
            try:
                return vals.Array(*map(functools.partial(_value, ""), obj))
            except TypeError:
                pass
            raise RuntimeError(f"Case {type(obj)} handled ({name=})")

        def _stage_move(argc: int, argv: _list[vals.Value]) -> vals.Value:
            if argc != 2:
                raise TypeError(f"Expected 2 arguments, got {argc}")
            elif any(not isinstance(arg, vals.Array) for arg in argv):
                raise TypeError("Expected 2 tuples")
            step_, size_, *rest = map(tuple, map(lambda x: list(map(lambda y: y.raw, x.raw)), argv))
            if rest:
                raise TypeError("Expected 2 tuples")
            if not all((len(x) == 2 and all(int(y) == y for y in x)) for x in (step_, size_)):
                raise ValueError("Expected numeric tuples of 2 values each")

            def _inner() -> typing.Iterator[vals.Nil]:
                for _ in self._microscope.subsystems["Stage"].flat_snake(step_, size_):
                    yield vals.Nil()

            return objs.NativeIterator(_inner())

        initial_pitch = sizes["scan_size"] // (sizes["scan_resolution"] // sizes["size"])

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

        self._microscope = microscope.Microscope(microscope.Detector.ADF1, True, microscope.Lens.CL1, microscope.Axis.X,
                                                 beam=False, valve=True)
        self._scanner = microscope.Scanner(microscope.FullScan((size, size)), dwell_time=init_dwell)

        self._master.setUsesScrollButtons(False)
        stage_m = pages.additionals.Scanner(self._microscope, self._scanner)
        stage_1 = pages.pipeline.SurveyImage(size, cluster_colour, initial_pitch, self._scanner, stage_m.scan)
        stage_2 = pages.pipeline.ProcessingPipeline(size, stage_1, _data_failed)
        stage_3 = pages.pipeline.Clusters(size, cluster_colour, initial_pitch, stage_2, _data_failed)
        stage_4 = pages.pipeline.Management(size, stage_1, stage_3, _data_failed)
        stage_5 = pages.pipeline.DeepSearch(size, stage_4, stage_1, marker_colour, finished_colour, _data_failed,
                                            self._microscope, self._scanner, stage_3, stage_2)

        stage_h = pages.additionals.Histogram(size, stage_1, histogram_outline, _data_failed)
        stage_p = pages.additionals.ScanType(size, pattern_colour, _data_failed)
        stage_c = pages.additionals.Manager(_data_failed, self._microscope, self._scanner, (size, size), stage_m.scan)
        stage_f = pages.additionals.DiffractionFilter(stage_3)
        corrections = stage_c.corrections()
        focus = corrections["focus"]
        emission = corrections["emission"]
        drift = corrections["drift"]

        stage_a = pages.additionals.Scripts(
            _compile,
            _auto_variable,
            _auto_keyword,
            **{
                **{k: _value(k, stage_1.get_setting(k)) for k in stage_1.all_settings()},
                **{k: _value(k, stage_h.get_setting(k)) for k in stage_h.all_settings()},
                **{k: _value(k, stage_2.get_setting(k)) for k in stage_2.all_settings()},
                **{k: _value(k, stage_3.get_setting(k)) for k in stage_3.all_settings()},
                **{k: _value(k, stage_f.get_setting(k)) for k in stage_f.all_settings()},
                **{k: _value(k, stage_4.get_setting(k)) for k in stage_4.all_settings()},
                **{k: _value(k, stage_p.get_setting(k)) for k in stage_p.all_settings()},
                **{k: _value(k, stage_5.get_setting(k)) for k in stage_5.all_settings()},
                **{k: _value(k, focus.get_setting(k)) for k in focus.all_settings()},
                **{k: _value(k, emission.get_setting(k)) for k in emission.all_settings()},
                **{k: _value(k, drift.get_setting(k)) for k in drift.all_settings()},
            },
            Corner=objs.NativeEnum(images.AABBCorner),
            Randoms=objs.NativeEnum(utils.RandomTypes),
            KernelShape=objs.NativeEnum(images.MorphologicalShape),
            NumberMatch=objs.NativeEnum(utils.Match),
            Axis=objs.NativeEnum(utils.Extreme),
            Staging=objs.NativeEnum(utils.Stages),
            dwell_time=_value("", self._scanner.dwell_time),
            flyback=_value("", self._scanner.flyback),
            blur=objs.NativeFunc(stage_2.single_stage("blur")),
            gss_blur=objs.NativeFunc(stage_2.single_stage("gss_blur")),
            sharpen=objs.NativeFunc(stage_2.single_stage("sharpen")),
            median=objs.NativeFunc(stage_2.single_stage("median")),
            edge=objs.NativeFunc(stage_2.single_stage("edge")),
            threshold=objs.NativeFunc(stage_2.single_stage("threshold")),
            open=objs.NativeFunc(stage_2.single_stage("open")),
            close=objs.NativeFunc(stage_2.single_stage("close")),
            gradient=objs.NativeFunc(stage_2.single_stage("gradient")),
            i_gradient=objs.NativeFunc(stage_2.single_stage("i_gradient")),
            e_gradient=objs.NativeFunc(stage_2.single_stage("e_gradient")),
            Raster=objs.NativeFunc(stage_p.raster),
            Snake=objs.NativeFunc(stage_p.snake),
            Spiral=objs.NativeFunc(stage_p.spiral),
            Grid=objs.NativeFunc(stage_p.grid),
            Random=objs.NativeFunc(stage_p.random),
            correct_for=objs.NativeFunc(stage_c.run_now),
            stage_snake=objs.NativeFunc(_stage_move)
        )

        self._floating = pages.additionals.WhatsThis(
            Preprocessing_Options=_help(stage_2.advanced_help()),
            Segmentation_Settings=_help(stage_3.advanced_help()),
            Manager_Settings=_help(stage_4.advanced_help()),
            Scan_Patterns=_help(stage_p.advanced_help()),
            Grid_Search_Settings=_help(stage_5.advanced_help()),
            **{f"{stage_a.L_NAME}_Grammar": _help(stage_a.advanced_help()),
               f"{stage_a.L_NAME}_Standard_Library": _help(stage_a.standard_library())},
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

        self._pages: _tuple[bases.Page, ...] = (stage_1, stage_h,
                                                stage_2,
                                                stage_3, stage_f,
                                                stage_4,
                                                stage_p, stage_5,
                                                stage_c, stage_m,
                                                stage_a)

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

        stage_1.driftRegion.connect(drift.set_ref)
        drift.drift.connect(stage_5.update_grids)
        stage_5.scanPerformed.connect(focus.scans_increased)
        stage_5.scanPerformed.connect(drift.scans_increased)

        focus.runStart.connect(lambda: self._pause(-1))
        drift.runStart.connect(lambda: self._pause(-1))
        focus.runEnd.connect(lambda: self._resume(-1))
        drift.runEnd.connect(lambda: self._resume(-1))
        print("0 - DRIFT CORR RUNNING")
        stage_5.runStart.connect(drift.run)

        stage_1.clusterFound.connect(lambda _: stage_4.clear())

        self._master.addTab(CombinedPage(image=stage_1, histogram=stage_h), "Survey (&1)")
        self._master.setTabToolTip(0, "A page showcasing the survey image and its histogram")
        self._master.addTab(stage_2, "Processed Image (&2)")
        self._master.setTabToolTip(1, _help(stage_2.help()))
        self._master.addTab(CombinedPage(image=stage_3, analysis=stage_f), "Segmented (&3)")
        self._master.setTabToolTip(2, "A page showcasing the clusters and the diffraction filters")
        self._master.addTab(stage_4, "Cluster Manager (&4)")
        self._master.setTabToolTip(3, _help(stage_4.help()))
        self._master.addTab(CombinedPage(1, pattern=stage_p, scan=stage_5), "Grid Search (&5)")
        self._master.setTabToolTip(4, "A page showcasing the pattern (per square) and scans each square")
        self._master.addTab(CombinedPage(1, corrections=stage_c, interface=stage_m), "Hardware (&6)")
        self._master.setTabToolTip(5, "A page allowing for interaction with the microscope hardware")
        self._master.addTab(stage_a, "Automation Scripts (&7)")
        self._master.setTabToolTip(6, _help(stage_a.help()))
        stage_c.add_tooltip(0, _help(focus.help()))
        stage_c.add_tooltip(1, _help(emission.help()))
        stage_c.add_tooltip(2, _help(drift.help()))

        scan = widgets.QPushButton("Scan (&A)")
        process = widgets.QPushButton("Threshold (&B)")
        cluster = widgets.QPushButton("Cluster (&C)")
        search = widgets.QPushButton("Search (&D)")
        show_help = widgets.QPushButton("Help (&0)")

        pause = widgets.QCheckBox("Paused (&P)")
        stop = widgets.QCheckBox("Stopped (&S)")

        scan.clicked.connect(self._jump(stage_h.run, 1, (0, 0)))
        process.clicked.connect(self._jump(stage_2.run, 2, (1, None)))
        cluster.clicked.connect(self._jump(stage_3.run, 3, (2, 0)))
        search.clicked.connect(self._jump(stage_5.run, 7, (4, 1)))
        pause.stateChanged.connect(lambda: self._pause() if pause.isChecked() else self._resume())
        stop.stateChanged.connect(lambda: self._stop() if stop.isChecked() else self._resume())
        show_help.clicked.connect(
            lambda: self._floating.raise_() if self._floating.isVisible() else self._floating.show()
        )

        self._btns = (scan, process, cluster, search, pause, stop, show_help)
        for btn in self._btns:
            actions.addWidget(btn)
        for page in self._pages:
            page.clear()
            page.start()

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
        for page in self._pages:
            page.close()
        bases.ProcessPage.MANAGER.waitForDone()
        super().closeEvent(a0)


def main():
    configuration = load_settings("assets/config.json", init_dwell=pipelines.dwell_time,
                                  cluster_colour=pipelines.colour, marker_colour=pipelines.colour,
                                  histogram_outline=pipelines.colour, pattern_colour=pipelines.colour,
                                  finished_colour=pipelines.colour)
    window = GUI(sizes["size"], **configuration)
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
