import functools
import typing
from typing import Dict as _dict, Tuple as _tuple, List as _list

from ._01_survey import SurveyImage
from ._03_clustering import Clusters
from ... import utils
from ..._base import ClusterPage, CanvasPage, SettingsPage, ProcessPage, widgets, gui
from PyQt5.QtCore import Qt as enums
from ..._errors import *
from .... import validation


class FilterDict(utils.SettingsDict):
    match: utils.PercentageBox
    order: utils.OrderedGroup[widgets.QLabel]
    padding: utils.SizeControl
    dir: utils.XDControl[utils.Enum[utils.Extreme]]


class Filter(utils.SettingsPopup):

    def __init__(self, failure_action: typing.Callable[[Exception], None]):
        super().__init__()
        self._match = utils.PercentageBox(60, validation.examples.match)
        self._match.dataPassed.connect(lambda v: self.settingChanged.emit("match", v))
        self._match.dataFailed.connect(failure_action)
        self._order = utils.OrderedGroup[widgets.QLabel]()
        self._pad_value = utils.SizeControl(-1, 1, validation.examples.pad, mode=utils.RoundingMode.TRUNCATE,
                                            display=(lambda f: "auto" if f == -1 else str(f),
                                                     lambda s: -1 if s == "auto" else int(s))
                                            )
        self._pad_value.dataPassed.connect(lambda v: self.settingChanged.emit("padding", v))
        self._pad_value.dataFailed.connect(failure_action)
        self._pad_type = utils.XDControl(2, utils.Enum, members=utils.Extreme, start=utils.Extreme.MAXIMA)
        self._pad_type.dataPassed.connect(lambda v: self.settingChanged.emit("dir", v))
        self._pad_type.dataFailed.connect(failure_action)
        self._layout.addWidget(utils.DoubleLabelledWidget("Match Percentage", self._match,
                                                          "The percentage of a region within the cluster for validity"))
        self._layout.addWidget(utils.DoubleLabelledWidget("Padding Value", self._pad_value,
                                                          "The amount of padding around each cluster"))
        self._layout.addWidget(utils.DoubleLabelledWidget("Padding Direction", self._pad_type,
                                                          "The direction of padding around each cluster"))
        self._layout.addWidget(utils.DoubleLabelledWidget("Cluster Order", self._order,
                                                          "The order of exported clusters"))

    def widgets(self) -> FilterDict:
        return {"match": self._match, "order": self._order, "padding": self._pad_value, "dir": self._pad_type}


class Management(CanvasPage, SettingsPage[Filter], ProcessPage):
    settingChanged = SettingsPage.settingChanged

    def __init__(self, size: int, made_clusters: SurveyImage, found_clusters: Clusters,
                 failure_action: typing.Callable[[Exception], None]):
        CanvasPage.__init__(self, size)
        SettingsPage.__init__(self, utils.SettingsDepth.REGULAR | utils.SettingsDepth.ADVANCED,
                              functools.partial(Filter, failure_action))
        ProcessPage.__init__(self)
        self._order: _dict[utils.Cluster, int] = {}
        self._clusters: _dict[utils.Cluster, _tuple[utils.Grid, ...]] = {}
        self._selected: typing.Optional[ClusterPage] = None
        self._hardcoded: _list[utils.ScanRegion] = []

        self._made = utils.LabelledWidget("Survey Clusters", widgets.QRadioButton("&U"), utils.LabelOrder.SUFFIX)
        self._found = utils.LabelledWidget("Segmentation Clusters", widgets.QRadioButton("&E"), utils.LabelOrder.SUFFIX)
        self._buttons = widgets.QButtonGroup()
        self._buttons.addButton(self._made.focus, 1)
        self._buttons.addButton(self._found.focus, 2)
        self._buttons.idToggled.connect(functools.partial(self._choose_page, {1: made_clusters, 2: found_clusters}))
        self._choose_segmented = functools.partial(self._choose_page.py_func,
                                                   {1: made_clusters, 2: found_clusters}, 2, True)
        self._overlap = utils.LabelledWidget("Overlap percentage",
                                             utils.PercentageBox(10, validation.examples.overlap, step=5),
                                             utils.LabelOrder.SUFFIX)
        self._overlap_directions = utils.LabelledWidget("Overlap Directions",
                                                        utils.XDControl(3, utils.CheckBox, text="X", initial=True),
                                                        utils.LabelOrder.SUFFIX)
        self._overlap.focus.dataPassed.connect(lambda v: self.settingChanged.emit("overlap", v))
        self._overlap.focus.dataFailed.connect(failure_action)
        self._overlap_directions.focus.dataPassed.connect(lambda v: self.settingChanged.emit("overlap_directions", v))
        self._overlap_directions.focus.dataFailed.connect(failure_action)
        self._overlap_directions.focus.get_widget(1).setText("Y")
        self._overlap_directions.focus.get_widget(2).setText("XY")
        self._overlap_directions.focus.get_widget(2).change_data(False)
        self._pitch = widgets.QLabel("Grid Size:")
        self._tighten = widgets.QPushButton("&Tighten")
        self._tighten.clicked.connect(lambda: self._tighten_grids())
        self._export = widgets.QPushButton("E&xport")
        # noinspection PyCallingNonCallable
        self._export.clicked.connect(lambda: self._export_grids())

        self._regular.addWidget(self._made)
        self._regular.addWidget(self._found)
        self._regular.addWidget(self._overlap)
        self._regular.addWidget(self._overlap_directions)
        self._regular.addWidget(self._pitch)
        self._regular.addWidget(self._tighten)
        self._regular.addWidget(self._export)

        self.setLayout(self._layout)
        self._popup.widgets()["order"].orderChanged.connect(self._change_order)
        self._canvas.mousePressed.connect(self._click)

    def compile(self) -> str:
        return "tighten"

    def run(self):
        pass

    def clear(self):
        CanvasPage.clear(self)
        ProcessPage.clear(self)
        self._hardcoded.clear()
        self._made.focus.setChecked(False)
        self._found.focus.setChecked(False)
        self._pitch.setText("Grid Size:")

    def start(self):
        SettingsPage.start(self)
        CanvasPage.start(self)
        ProcessPage.start(self)

    def stop(self):
        SettingsPage.stop(self)
        CanvasPage.stop(self)
        ProcessPage.stop(self)

    def get_tight(self) -> _tuple[utils.ScanRegion, ...]:
        return tuple(self._hardcoded)

    def update_label(self):
        if self._selected is None:
            return
        pitch = self._selected.pitch_size()
        self._pitch.setText(f"Grid Size: {pitch}")
        pitch, overlap, pad, overlaps = self._settings()
        for cluster in self._order:
            if not cluster.locked:
                continue
            try:
                self._clusters[cluster] = tuple(
                    cluster.divide(pitch, overlap, off_dir, self._canvas.image_size[0], pad[0], pad[1])
                    for off_dir in overlaps
                )
            except ValueError as err:
                raise GUIError(utils.ErrorSeverity.WARNING, "Division Error", f"For {cluster}, {err}")
        self._draw()

    @utils.Tracked
    def _choose_page(self, mapping: _dict[int, ClusterPage], index: int, state: bool) -> None:
        selected = mapping[index]
        clusters = selected.get_clusters()
        if not self._made.focus.isChecked() and not self._found.focus.isChecked():
            self.runStart.emit()
        order = self._popup.widgets()["order"]
        order.clear_members()
        self._clusters.clear()
        for cluster in self._order:
            cluster.locked = False
        self._order.clear()
        if not state:
            return
        self._pitch.setText(f"Grid Size: {selected.pitch_size()}")
        for i, cluster in enumerate(clusters, 1):
            order.add_member(widgets.QLabel(str(cluster)))
            self._order[cluster] = i
        self._selected = selected
        self._draw()

    def _draw(self):
        self._modified_image = self._selected.modified.copy()
        colour = ~self._selected.colour()
        for grid_set in self._clusters.values():
            for grid in grid_set:
                grid.draw(self._modified_image, colour)
        self._canvas.draw(self._modified_image)

    def _change_order(self, old: int, new: int):
        order = {v: k for k, v in self._order.items()}
        order[old + 1], order[new + 1] = order[new + 1], order[old + 1]
        self._order = {v: k for k, v in order.items()}
        self._draw()

    @utils.Stoppable.decorate(manager=ProcessPage.MANAGER)
    @utils.Tracked
    def _tighten_grids(self, progress: typing.Optional[int]):
        match = self.get_setting("match")
        if progress is None:
            progress = -1
        clusters = filter(lambda cl: cl.locked, self._clusters)
        try:
            for i, cluster in enumerate(clusters):
                if i < progress:
                    continue
                elif self._state == utils.StoppableStatus.PAUSED:
                    self._tighten_grids.pause.emit(i)
                    return
                elif self._state == utils.StoppableStatus.DEAD:
                    return
                for grid in self._clusters[cluster]:
                    grid.tighten(match)
                if not sum(map(lambda x: list(x), self._clusters[cluster]), []):
                    raise GUIError(utils.ErrorSeverity.WARNING, "No grids remaining",
                                   f"{cluster} has no grids remaining after tightening. "
                                   f"Try using a match percentage lower than {match:.0%}")
        finally:
            self._draw()

    @utils.Tracked
    def _export_grids(self):
        hardcoded = []
        for grids in self._clusters.values():
            for grid in grids:
                if not grid.tight:
                    raise GUIError(utils.ErrorSeverity.WARNING, "Loose Grid",
                                   "Must tighten all grids prior to exporting")
                hardcoded.extend(grid)
        self._hardcoded.extend(hardcoded)
        self._clusters.clear()
        self._draw()
        self.runEnd.emit()

    def _process_tooltip(self, x: int, y: int) -> typing.Iterator[str]:
        yield from super()._process_tooltip(x, y)
        for cluster, position in self._order.items():
            if (x, y) in cluster:
                yield f"#{position}: {cluster}"
                break

    @utils.Tracked
    def _click(self, event: gui.QMouseEvent):
        if self._state != utils.StoppableStatus.ACTIVE:
            return
        elif self._modified_image is None:
            raise StagingError("marking clusters", "choosing cluster source")
        pos = event.pos()
        x, y = pos.x(), pos.y()
        btn = event.button()
        if btn == enums.LeftButton:
            # noinspection PyCallingNonCallable
            self._mark(x, y)
        elif btn == enums.RightButton:
            # noinspection PyCallingNonCallable
            self._update_cluster(x, y)

    @utils.Tracked
    def _mark(self, x: int, y: int):
        pitch, overlap, pad, overlaps = self._settings()
        for cluster in self._order:
            if (x, y) not in cluster:
                continue
            if cluster.locked:
                raise GUIError(utils.ErrorSeverity.INFO, "Cluster Marked",
                               f"Cannot mark cluster at {(x, y)} multiple times")
            try:
                self._clusters[cluster] = tuple(
                    cluster.divide(pitch, overlap, off_dir, self._canvas.image_size[0], pad[0], pad[1])
                    for off_dir in overlaps
                )
            except ValueError as err:
                raise GUIError(utils.ErrorSeverity.WARNING, "Division Error", f"For {cluster}, {err}")
            cluster.locked = True
            break
        else:
            raise GUIError(utils.ErrorSeverity.ERROR, "Missing Cluster", f"No cluster recorded at {x, y}")
        self._draw()

    @utils.Tracked
    def _update_cluster(self, x: int, y: int):
        pitch, overlap, pad, overlaps = self._settings()
        for cluster in self._order:
            if (x, y) not in cluster:
                continue
            if not cluster.locked:
                raise GUIError(utils.ErrorSeverity.INFO, "Cluster Not Marked",
                               f"Cannot update unmarked cluster at {(x, y)}")
            try:
                self._clusters[cluster] = tuple(
                    cluster.divide(pitch, overlap, off_dir, self._canvas.image_size[0], pad[0], pad[1])
                    for off_dir in overlaps
                )
            except ValueError as err:
                raise GUIError(utils.ErrorSeverity.WARNING, "Division Error", f"For {cluster}, {err}")
            break
        else:
            raise GUIError(utils.ErrorSeverity.ERROR, "Missing Cluster", f"No cluster recorded at {x, y}")
        self._draw()

    def _settings(self) \
            -> _tuple[int, int, _tuple[_tuple[int, int], _tuple[utils.Extreme, utils.Extreme]], _list[utils.Overlap]]:
        pitch = self._selected.pitch_size()
        overlap = int((1 - self._overlap.focus.get_data()) * pitch)
        pad = self.get_setting("padding"), self.get_setting("dir")
        overlaps = [utils.Overlap(0)]
        for i, flag in enumerate(self._overlap_directions.focus.get_data()):
            if not flag:
                continue
            if i == 0:
                overlaps.append(utils.Overlap.X)
            elif i == 2:
                overlaps.append(utils.Overlap.Y)
            else:
                overlaps.append(utils.Overlap.X | utils.Overlap.Y)
        return pitch, overlap, pad, overlaps

    def automate_click(self):
        self._choose_segmented()
        for cluster in self._order:
            self._mark.py_func(*cluster.position())

    def automate_tighten(self):
        if self._modified_image is None:
            raise StagingError("tightening grids", "forming grids")
        self._tighten_grids.py_func(None)
        self._export_grids.py_func()

    def all_settings(self) -> typing.Iterator[str]:
        yield from ("overlap", "overlap_directions", "match", "padding", "dir")

    def help(self) -> str:
        s = f"""This page allows for manging any clusters - either made by the user or found by DBSCAN.

        Marking a cluster happens by click, and is when a grid is placed around the bounding box of a cluster.
        This is regarded as a "loose" grid, as it doesn't conform to the edges of the cluster.
        
        The different directions of overlap can be modified, as well as the percentage of the grid covered by overlap.
        The grid size is a function of: 
            the size of the survey image;
            the resolution to upscale to;
            the size of each small image.
        
        Tightening of a grid involves identifying which individual squares have enough cluster in to be valid.
        This will make the grid conform to the edges of the cluster better than a loose grid.
        
        The final stage is to export the tightened grids, as this ensures they are saved (and their order maintained);
        when switching between sources.

        Settings
        --------
        Overlap Percentage: 
            {validation.examples.overlap}
            
            The percentage of overlap to have per grid. 
            Note that this is an offset from the first square;
            so a 10% overlap means that 10% of the first square overlaps with the first square in the next grid.
        Overlap Directions:
            {validation.examples.any_bool}
            
            The enabled directions for overlap. This creates at most 4 grids on each cluster (minimum 1).
            
            An x-overlap creates another grid on top of the existing grids. This grid has a horizontal offset *only*.
            A y-overlap creates another grid on top of the existing grids. This grid has a vertical offset *only*.
            An xy-overlap creates another grid on top of the existing grids. This grid has offset in *both* directions.
        For advanced settings, see the help page."""
        return s

    def advanced_help(self) -> str:
        s = f"""Match Percentage:
            {validation.examples.match}
    
            The percentage of pixels required to mark a loose grid as tight. 
            Higher values will miss more of the cluster, but will eliminate more dead space.
        Padding Value:
            {validation.examples.pad}
    
            The amount of pixels extra padding to apply in the specified `Padding Direction` to each cluster;
            prior to creating the grids. 
            When set to "-1", automatic padding is applied which will continue to pad;
            until it reaches an even multiple of the pitch size.
        Padding Direction:
            {self.get_control('dir').validation_pipe()}
    
            The direction in which to apply padding.
            MINIMA means it increases size where co-ordinates tend to 0 (left or top);
            MAXIMA means it increases size where co-ordinates tend to {self._canvas.image_size[0]} (right or bottom)."""
        return s
