import functools
import typing
from typing import Dict as _dict, Tuple as _tuple, List as _list

from ._01_survey import SurveyImage
from ._03_clustering import Clusters
from ... import utils
from ..._base import ClusterPage, CanvasPage, SettingsPage, ProcessPage, widgets, gui
from PyQt5.QtCore import Qt as enums
from ..._errors import *
from .... import load_settings, validation


class FilterDict(utils.SettingsDict):
    """
    Typed dictionary representing the advanced cluster management settings.

    Keys
    ----
    match: PercentageBox
        The match factor to apply to the scan regions.
    order: OrderedGroup[QLabel]
        The ordering of the clusters.
    """
    match: utils.PercentageBox
    order: utils.OrderedGroup[widgets.QLabel]


default_settings = load_settings("assets/config.json",
                                 match=validation.examples.match,
                                 overlap=validation.examples.overlap,
                                 overlap_directions=validation.examples.flag_3
                                 )


class Filter(utils.SettingsPopup):
    """
    Concrete popup representing the advanced clustering settings.

    Attributes
    ----------
    _match: PercentageBox
        The widget controlling the match factor.
    _order: OrderedGroup[widgets.QLabel]
        The widget controlling the order.
    """

    def __init__(self, failure_action: typing.Callable[[Exception], None]):
        super().__init__()
        self._match = utils.PercentageBox(int(default_settings["match"] * 100), validation.examples.match)
        self._match.dataPassed.connect(lambda v: self.settingChanged.emit("match", v))
        self._match.dataFailed.connect(failure_action)
        self._order = utils.OrderedGroup[widgets.QLabel]()
        self._layout.addWidget(utils.DoubleLabelledWidget("Match Percentage", self._match,
                                                          "The percentage of a region within the cluster for validity"))
        self._layout.addWidget(utils.DoubleLabelledWidget("Cluster Order", self._order,
                                                          "The order of exported clusters"))

    def widgets(self) -> FilterDict:
        return {"match": self._match, "order": self._order}


class Management(CanvasPage, SettingsPage[Filter], ProcessPage):
    """
    Concrete page representing the division of identified clusters from any source.

    Attributes
    ----------
    _order: dict[Cluster, int]
        The mapping from cluster to order of scanning.
    _clusters: dict[Cluster, tuple[Grid, ...]]
        The mapping from cluster to scan grid.
    _selected: ClusterPage | None
        The selected cluster source.
    _hardcoded: list[ScanRegion]
        The scan regions to search.
    _made: LabelledWidget[QRadioButton]
        A widget detailing one choice for cluster source - the ones user made.
    _found: LabelledWidget[QRadioButton]
        A widget detailing one choice for cluster source - the ones programmatically found.
    _buttons: QButtonGroup
        The button group to group the source choices.
    _choose_segmented: Callable[[], None]
        A shortcut function to choose the segmented source.
    _overlap: LabelledWidget[PercentageBox]
        The widget controlling the percentage of overlap.
    _overlap_directions: LabelledWidget[XDControl[CheckBox]]
        The widget controlling what directions of overlap are enabled.
    _pitch: QLabel
        The widget showcasing the size of each grid square (in relation to the survey image size).
    _tighten: QPushButton
        The button to tighten the grids around each cluster.
    _export: QPushButton
        The button to export the selected, tightened grids.
    _click_all: QPushButton
        The button to mark all available clusters with grids.
    """
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
        self._buttons.idClicked.connect(functools.partial(self._choose_page, {1: made_clusters, 2: found_clusters}))
        self._choose_segmented = functools.partial(self._choose_page.py_func,
                                                   {1: made_clusters, 2: found_clusters}, 2, True)
        self._overlap = utils.LabelledWidget("Overlap percentage",
                                             utils.PercentageBox(int(default_settings["overlap"] * 100),
                                                                 validation.examples.overlap, step=5),
                                             utils.LabelOrder.SUFFIX)
        self._overlap_directions = utils.LabelledWidget("Overlap Directions",
                                                        utils.XDControl(3, utils.CheckBox, text="X", initial=True),
                                                        utils.LabelOrder.SUFFIX)
        self._overlap.focus.dataPassed.connect(lambda v: self.settingChanged.emit("overlap", v))
        self._overlap.focus.dataFailed.connect(failure_action)
        direc = self._overlap_directions.focus
        direc.dataPassed.connect(lambda v: self.settingChanged.emit("overlap_directions", v))
        direc.dataFailed.connect(failure_action)
        direc.get_widget(1).setText("Y")
        direc.get_widget(2).setText("XY")

        directions = default_settings["overlap_directions"]
        for i in range(3):
            direc.get_widget(i).change_data(directions[i])

        self._pitch = widgets.QLabel("Grid Size:")
        self._tighten = widgets.QPushButton("&Tighten")
        self._tighten.clicked.connect(lambda: self._tighten_grids())
        self._export = widgets.QPushButton("E&xport")
        # noinspection PyCallingNonCallable
        self._export.clicked.connect(lambda: self._export_grids())

        self._click_all = widgets.QPushButton("Mark all clusters")
        self._click_all.clicked.connect(self.automate_click)

        self._regular.addWidget(self._made)
        self._regular.addWidget(self._found)
        self._regular.addWidget(self._overlap)
        self._regular.addWidget(self._overlap_directions)
        self._regular.addWidget(self._pitch)
        self._regular.addWidget(self._tighten)
        self._regular.addWidget(self._export)
        self._regular.addWidget(self._click_all)

        self.setLayout(self._layout)
        self._popup.widgets()["order"].orderChanged.connect(self._change_order)
        self._canvas.mousePressed.connect(self._click)

    def compile(self) -> str:
        return "Mark\nTighten"

    def run(self):
        pass

    def clear(self):
        CanvasPage.clear(self)
        ProcessPage.clear(self)
        self._hardcoded.clear()
        self._found.focus.setChecked(False)
        self._buttons.idToggled.emit(1, False)
        self._buttons.idToggled.emit(2, False)
        self._made.focus.setChecked(False)
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
        """
        Access the tightened grids.

        Returns
        -------
        tuple[ScanRegion, ...]
            The scan regions ready to export, as an immutable data structure.
        """
        return tuple(self._hardcoded)

    def update_label(self):
        """
        Update the pitch size label.

        This will also re-grid each cluster - however, each grid will need to be tightened again.

        Raises
        ------
        GUIError
            If a ValueError occurs during the division.
        """
        if self._selected is None:
            return
        pitch = self._selected.pitch_size()
        self._pitch.setText(f"Grid Size: {pitch}")
        pitch, overlap, overlaps = self._settings()
        for cluster in self._order:
            if not cluster.locked:
                continue
            try:
                self._clusters[cluster] = tuple(
                    cluster.divide(pitch, overlap, off_dir, self._canvas.image_size[0])
                    for off_dir in overlaps
                )
            except ValueError as err:
                raise GUIError(utils.ErrorSeverity.WARNING, "Division Error", f"For {cluster}, {err}")
        self._draw()

    @utils.Tracked
    def _choose_page(self, mapping: _dict[int, ClusterPage], index: int) -> None:
        selected = mapping[index]
        if self._buttons.checkedId() == -1:
            self.runStart.emit()
        order = self._popup.widgets()["order"]
        order.clear_members()
        self._clusters.clear()
        for cluster in self._order:
            cluster.locked = False
        self._order.clear()
        clusters = selected.get_clusters()
        self._pitch.setText(f"Grid Size: {selected.pitch_size()}")
        for i, cluster in enumerate(clusters, 1):
            order.add_member(widgets.QLabel(str(cluster)))
            self._order[cluster] = i
        self._selected = selected
        self._draw()

    def _draw(self):
        self._modified_image = self._selected.modified.copy()
        colour = 2 ** 24 - 1 - self._selected.colour()
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
                self._draw()
        finally:
            self._draw()

    @utils.Tracked
    def _export_grids(self):
        hardcoded = []
        keys = sorted(self._clusters, key=lambda cl: self._order[cl])
        for grids in map(self._clusters.get, keys):
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

    @utils.Thread.decorate(manager=ProcessPage.MANAGER)
    @utils.Tracked
    def _mark(self, x: int, y: int):
        pitch, overlap, overlaps = self._settings()
        for cluster in self._order:
            if (x, y) not in cluster:
                continue
            if cluster.locked:
                raise GUIError(utils.ErrorSeverity.INFO, "Cluster Marked",
                               f"Cannot mark cluster at {(x, y)} multiple times")
            try:
                self._clusters[cluster] = tuple(
                    cluster.divide(pitch, overlap, off_dir, self._canvas.image_size[0])
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
        pitch, overlap, overlaps = self._settings()
        for cluster in self._order:
            if (x, y) not in cluster:
                continue
            if not cluster.locked:
                raise GUIError(utils.ErrorSeverity.INFO, "Cluster Not Marked",
                               f"Cannot update unmarked cluster at {(x, y)}")
            try:
                self._clusters[cluster] = tuple(
                    cluster.divide(pitch, overlap, off_dir, self._canvas.image_size[0])
                    for off_dir in overlaps
                )
            except ValueError as err:
                raise GUIError(utils.ErrorSeverity.WARNING, "Division Error", f"For {cluster}, {err}")
            break
        else:
            raise GUIError(utils.ErrorSeverity.ERROR, "Missing Cluster", f"No cluster recorded at {x, y}")
        self._draw()

    def _settings(self) -> _tuple[int, int, _list[utils.Overlap]]:
        pitch = self._selected.pitch_size()
        overlap = int((1 - self._overlap.focus.get_data()) * pitch)
        overlaps = [utils.Overlap(0)]
        for i, flag in enumerate(self._overlap_directions.focus.get_data()):
            if not flag:
                continue
            if i == 0:
                overlaps.append(utils.Overlap.X)
            elif i == 1:
                overlaps.append(utils.Overlap.Y)
            else:
                overlaps.append(utils.Overlap.X | utils.Overlap.Y)
        return pitch, overlap, overlaps

    def automate_click(self):
        """
        Perform a single-threaded click of all clusters.
        """
        pitch, overlap, overlaps = self._settings()
        for cluster in self._order:
            try:
                self._clusters[cluster] = tuple(
                    cluster.divide(pitch, overlap, off_dir, self._canvas.image_size[0])
                    for off_dir in overlaps
                )
                cluster.locked = True
            except ValueError:
                continue
        self._draw()

    def automate_tighten(self):
        """
        Perform a single-threaded tighten and export of all marked clusters.

        Raises
        ------
        StagingError
            If there are no grids to tighten.
        """
        if self._modified_image is None:
            raise StagingError("tightening grids", "forming grids")
        self._tighten_grids.py_func(None)
        self._export_grids.py_func()

    def all_settings(self) -> typing.Iterator[str]:
        yield from ("overlap", "overlap_directions", "match")

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
            Higher values will miss more of the cluster, but will eliminate more dead space."""
        return s
