import functools
import typing

import numpy as np
from sklearn.cluster import DBSCAN

from ._02_thresholding import ProcessingPipeline
from ... import utils
from ..._base import ClusterPage, SettingsPage, ProcessPage, widgets, images, core
from ..._errors import *
from .... import validation


class AlgorithmDict(utils.SettingsDict):
    algorithm: utils.ComboBox[str]
    square: widgets.QCheckBox
    power: utils.Spinbox
    size: utils.SizeControl
    size_match: utils.Enum[utils.Match]


class Algorithm(utils.SettingsPopup):

    def __init__(self, failure_action: typing.Callable[[Exception], None]):
        super().__init__()

        def _change(text: str):
            self._square.setEnabled(False)
            self._power.setEnabled(False)
            if text == "Euclidean":
                self._square.setEnabled(True)
            elif text == "Minkowski":
                self._power.setEnabled(True)

        self._algorithm = utils.ComboBox("Manhattan", "Euclidean", "Minkowski", start_i=1)
        self._algorithm.dataPassed.connect(_change)
        self._algorithm.dataPassed.connect(lambda v: self.settingChanged.emit("algorithm", v))

        self._square = utils.CheckBox("", False)
        self._square.dataPassed.connect(lambda v: self.settingChanged.emit("square", v))
        self._power = utils.Spinbox(3, 1, validation.examples.power)
        self._power.dataPassed.connect(lambda v: self.settingChanged.emit("power", v))
        self._match_mode = utils.Enum(utils.Match, utils.Match.NO_LOWER)
        self._match_mode.dataPassed.connect(lambda v: self.settingChanged.emit("match", v))
        self._size = utils.SizeControl(15, 1, validation.examples.size)
        self._size.dataPassed.connect(lambda v: self.settingChanged.emit("size", v))

        self._layout.addWidget(utils.DoubleLabelledWidget("Distance Algorithm", self._algorithm,
                                                          "The distance metric to use for clustering"))
        self._layout.addWidget(utils.DoubleLabelledWidget("Square Distance", self._square,
                                                          "Whether to square Euclidean distances prior to clustering"))
        self._layout.addWidget(utils.DoubleLabelledWidget("Minkowski Power", self._power,
                                                          "The power used in Minkowski distance"))
        self._layout.addWidget(utils.DoubleLabelledWidget("Cluster Size", self._size, "The size of each cluster"))
        self._layout.addWidget(utils.DoubleLabelledWidget("Size Match", self._match_mode,
                                                          "How to compare the cluster size to the 'Cluster Size'"))

        self._algorithm.dataPassed.connect(lambda v: self.settingChanged.emit("algorithm", v))
        self._algorithm.dataFailed.connect(failure_action)
        self._square.stateChanged.connect(lambda v: self.settingChanged.emit("square", v))
        self._square.dataFailed.connect(failure_action)
        self._power.dataPassed.connect(lambda v: self.settingChanged.emit("power", v))
        self._power.dataFailed.connect(failure_action)
        self._size.dataPassed.connect(lambda v: self.settingChanged.emit("size", v))
        self._size.dataFailed.connect(failure_action)
        self._match_mode.dataPassed.connect(lambda v: self.settingChanged.emit("size_match", v))
        self._match_mode.dataFailed.connect(failure_action)

        _change("Euclidean")

    def widgets(self) -> AlgorithmDict:
        return {"algorithm": self._algorithm, "square": self._square, "power": self._power, "size": self._size,
                "size_match": self._match_mode}


class Clusters(ClusterPage, SettingsPage[Algorithm], ProcessPage):
    clusterFound = ClusterPage.clusterFound
    settingChanged = SettingsPage.settingChanged
    _newMax = core.pyqtSignal(int)
    _newVal = core.pyqtSignal(int)

    def __init__(self, size: int, cluster_colour: images.RGB, initial_size: int, pipeline: ProcessingPipeline,
                 failure_action: typing.Callable[[Exception], None]):
        ClusterPage.__init__(self, size, cluster_colour, initial_size)
        SettingsPage.__init__(self, utils.SettingsDepth.REGULAR | utils.SettingsDepth.ADVANCED,
                              functools.partial(Algorithm, failure_action))
        ProcessPage.__init__(self)
        self._prev = pipeline
        self._DBSCAN_clusters: typing.Optional[np.ndarray] = None
        self._DBSCAN_regions: typing.Optional[np.ndarray] = None

        self._epsilon = utils.LabelledWidget("Epsilon",
                                             utils.Spinbox(4.2, 0.01, validation.examples.epsilon,
                                                           mode=utils.RoundingMode.DECIMAL),
                                             utils.LabelOrder.SUFFIX)
        self._samples = utils.LabelledWidget("Minimum Samples",
                                             utils.Spinbox(50, 1, validation.examples.minimum_samples),
                                             utils.LabelOrder.SUFFIX)
        self._progress = widgets.QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setValue(0)

        self.clusterFound.connect(self._progress.setValue)
        self._newVal.connect(self._progress.setValue)
        self._newMax.connect(self._progress.setMaximum)

        self._epsilon.focus.dataPassed.connect(lambda v: self.settingChanged.emit("epsilon", v))
        self._epsilon.focus.dataFailed.connect(failure_action)
        self._samples.focus.dataPassed.connect(lambda v: self.settingChanged.emit("minimum_samples", v))
        self._samples.focus.dataFailed.connect(failure_action)

        self._regular.addWidget(self._epsilon)
        self._regular.addWidget(self._samples)
        self._regular.addWidget(self._progress)

        self._minimum_samples = self._samples  # alias for get_control

        self.setLayout(self._layout)
        self._automate = False

    def clear(self):
        ClusterPage.clear(self)
        ProcessPage.clear(self)
        self._progress.setValue(0)
        self._progress.setRange(0, 0)

    def start(self):
        ClusterPage.start(self)
        SettingsPage.start(self)
        ProcessPage.start(self)

    def stop(self):
        ClusterPage.stop(self)
        SettingsPage.stop(self)
        ProcessPage.stop(self)

    def compile(self) -> str:
        return "cluster\nmark"

    # @utils.Tracked
    def chosen_cluster(self, radius: int) -> utils.Cluster:
        x_lim, y_lim = self._canvas.image_size
        for cluster in self._clusters:
            sx, sy = cluster[images.AABBCorner.TOP_LEFT]
            ex, ey = cluster[images.AABBCorner.BOTTOM_RIGHT]
            left_most = max(sx - radius, 0)
            right_most = min(ex + radius, x_lim)
            top_most = max(sy - radius, 0)
            bottom_most = min(ey + radius, y_lim)
            left_edge = sx - 1
            right_edge = ex + 1
            top_edge = sy - 1
            bottom_edge = ey + 1
            if left_edge < 0 or top_edge < 0 or right_edge > x_lim or bottom_edge > y_lim:
                continue
            left_radius = self._modified_image.region((left_most, top_most), (left_edge, bottom_most))
            right_radius = self._modified_image.region((right_edge, top_most), (right_most, bottom_most))
            top_radius = self._modified_image.region((left_most, top_most), (right_most, top_edge))
            bottom_radius = self._modified_image.region((left_most, bottom_edge), (right_most, bottom_most))
            if not left_radius and not right_radius and not top_radius and not bottom_radius:
                chosen = cluster
                break
        else:
            raise GUIError(utils.ErrorSeverity.WARNING, "No valid cluster",
                           f"There is no cluster with {radius} pixels of padding around itself")
        return chosen

    @utils.Tracked
    def run(self):
        if self._state != utils.StoppableStatus.ACTIVE:
            return
        self.runStart.emit()
        if (img := self._prev.modified) is None:
            raise StagingError("segmentation", "pre-processing")
        try:
            img.downchannel(images.Grey(0), images.Grey(255))
        except TypeError:
            raise GUIError(utils.ErrorSeverity.WARNING, "Incomplete processing",
                           "Pre-processing must end with a binary image. Try adding a 'threshold' or an 'edge' process")
        self._canvas.draw(images.RGBImage.blank(self._canvas.image_size))
        if not self._automate:
            self._run()
        else:
            self._run.py_func()

    @utils.Thread.decorate(manager=ProcessPage.MANAGER)
    @utils.Tracked
    def _run(self):
        img = self._prev.modified
        data = img.channel.copy("r")

        indices = np.nonzero(data == 255)
        white_mask = np.asarray(indices).T
        regions = np.zeros_like(data)
        metric_params = {}
        metric = self.get_setting("algorithm").lower()
        if metric == "minkowski":
            metric_params["p"] = self.get_setting("power")
        elif metric == "euclidean" and self.get_setting("square"):
            metric = "sqeuclidean"
        scan = DBSCAN(self._epsilon.focus.get_data(), min_samples=self._samples.focus.get_data(), metric=metric,
                      metric_params=metric_params)
        clusters = scan.fit_predict(white_mask) + 1
        regions[indices] = clusters

        if (largest := np.max(clusters)) > 765:
            raise GUIError(utils.ErrorSeverity.INFO, "Too many clusters",
                           f"Found {largest} clusters, which overflows the colour space (expected 765 or less)")
        elif largest == 0:
            self._newMax.emit(1)
            self._newVal.emit(1)
            return
        self._newMax.emit(largest)
        self._newVal.emit(0)
        self._DBSCAN_clusters = clusters
        self._DBSCAN_regions = regions
        if not self._automate:
            self._identify()
        else:
            self._identify.py_func(None)

    @utils.Stoppable.decorate(manager=ProcessPage.MANAGER)
    def _identify(self, progress: typing.Optional[int]):
        size, mode = self.get_setting("size"), self.get_setting("size_match")

        def _size(site: utils.Cluster) -> bool:
            x_size, y_size = site.size(utils.Axis.X), site.size(utils.Axis.Y)
            if mode == utils.Match.NO_LOWER:
                return x_size >= size[0] and y_size >= size[1]
            elif mode == utils.Match.EXACT:
                return x_size == size[0] and y_size == size[1]
            return x_size <= size[0] and y_size <= size[1]

        cw, ch = self._canvas.image_size
        clusters_img = np.zeros((ch, cw, 3), dtype=np.uint8)
        by, bx = np.nonzero(self._DBSCAN_regions <= 255)
        gy, gx = np.nonzero((self._DBSCAN_regions > 255) & (self._DBSCAN_regions <= 510))
        ry, rx = np.nonzero(self._DBSCAN_regions > 510)
        clusters_img[by, bx, 2] = self._DBSCAN_regions[by, bx]
        clusters_img[gy, gx, 1] = self._DBSCAN_regions[gy, gx] - 255
        clusters_img[ry, rx, 0] = self._DBSCAN_regions[ry, rx] - 510

        all_clusters = images.RGBImage(clusters_img, data_order=images.RGBOrder.RGB)
        self._cluster_image = all_clusters.copy()

        i = 0
        if progress is None:
            progress = -1
        for blue in np.unique(self._DBSCAN_clusters):
            if self._state == utils.StoppableStatus.PAUSED:
                self._identify.pause.emit(i)
                return
            elif self._state == utils.StoppableStatus.DEAD:
                return
            if i < progress:
                i += 1
                continue
            if blue == 0:
                continue
            blue_colour = images.RGB(0, 0, blue, wrapping=images.WrapMode.SPILL, order=images.RGBOrder.BGR)
            if not _size(cluster := utils.Cluster(all_clusters.downchannel(images.Grey(0), blue_colour,
                                                                           invalid_handler=images.BimodalBehaviour.BG),
                                                  blue)
                         ):
                self._cluster_image.replace(blue_colour, images.Grey(0))
                self._progress.setMaximum(self._progress.maximum() - 1)
                continue
            i += 1
            self._clusters.append(cluster)
            self.clusterFound.emit(i)

        self._modified_image = self._cluster_image.downchannel(images.Grey(0), self._cluster_colour,
                                                               invalid_handler=images.BimodalBehaviour.FG).upchannel()
        self._canvas.draw(self._modified_image)
        self.runEnd.emit()

    def automate(self):
        self._automate = True
        try:
            self.run.py_func()
        finally:
            self._automate = False

    def all_settings(self) -> typing.Iterator[str]:
        yield from ("epsilon", "minimum_samples", "algorithm", "square", "power", "size", "size_match")

    def help(self) -> str:
        s = f"""This page allows for segmenting the preprocessed image. It is expected to be a binary image.

        Settings
        --------
        Epsilon:
            {validation.examples.epsilon}

            The epsilon value to use for DBSCAN. 
            Epsilon controls the distance between core points required to classify a point as a core point.
        Minimum Samples:
            {validation.examples.minimum_samples}

            The minimum samples to use in DBSCAN.
            Minimum samples controls the number of core points required to form a cluster.    
        For advanced settings, see the help page."""
        return s

    def advanced_help(self) -> str:
        s = f"""Distance Algorithm:
            {self.get_control('algorithm').validation_pipe()}

            The algorithm to use for calculating distances. 
            Minkowski is the generic form `(x ** p + y ** p) ** (1 / p)`;
            Manhattan locks this `p` value at 1;
            Euclidean locks this `p` value at 2.
        Square Distance:
            {validation.examples.any_bool}
            
            Whether to use the squared Euclidean distance.
            This only has an affect on the "Euclidean" algorithm.
        Minkowski Power:
            {validation.examples.power}
            
            What `p` value to use.
            This only has an affect on the "Minkowski" algorithm.
        Cluster Size
            {validation.examples.size}
            
            The pixel size of each cluster. This is combined with the `Size Match` to determine if a cluster passes.
        Size Match
            {self.get_control('size_match').validation_pipe()}
            
            How size filtering works.
            NO_LOWER implies that the size is the minimum size;
            EXACT implies that the size is the only size;
            NO_HIGHER implies that the size is the maximum size. """
        return s
