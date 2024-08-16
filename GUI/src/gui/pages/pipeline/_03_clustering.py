import functools
import typing

import numpy as np
from sklearn.cluster import DBSCAN

from ._02_thresholding import ProcessingPipeline
from ... import utils
from ..._base import ClusterPage, SettingsPage, ProcessPage, widgets, images, core
from ..._errors import *
from .... import load_settings, validation


class AlgorithmDict(utils.SettingsDict):
    """
    Typed dictionary representing the advanced clustering settings.

    Keys
    ----
    algorithm: ComboBox[str]
        The distance metric used.
    square: QCheckBox
        Whether to use a square distance metric (only available for Euclidean distance)
    power: Spinbox
        What p-factor to use (only available for Minkowski distance)
    size: SizeControl
        The size to check clusters against.
    size_match: Enum[Match]
        How to compare the clusters against the size.
    """
    algorithm: utils.ComboBox[str]
    square: widgets.QCheckBox
    power: utils.Spinbox
    size: utils.SizeControl
    size_match: utils.Enum[utils.Match]


default_settings = load_settings("assets/config.json",
                                 algorithm=validation.examples.distance_algorithm,
                                 square=validation.examples.any_bool,
                                 power=validation.examples.power,
                                 cluster_size=validation.examples.size,
                                 size_match=validation.examples.numerical_match,
                                 epsilon=validation.examples.epsilon,
                                 minimum_samples=validation.examples.minimum_samples,
                                 )


class Algorithm(utils.SettingsPopup):
    """
    Concrete popup representing the advanced clustering settings.

    Attributes
    ----------
    _algorithm: ComboBox[str]
        The widget controlling the distance metric.
    _square: QCheckBox
        The widget controlling the square distance metric.
    _power: Spinbox
        The widget controlling the p-factor.
    _match_mode: Enum[Match]
        The widget controlling the comparison mode.
    _size: SizeControl
        The widget controlling the size.
    """

    def __init__(self, failure_action: typing.Callable[[Exception], None]):
        super().__init__()

        def _change(text: str):
            self._square.setEnabled(False)
            self._power.setEnabled(False)
            if text == "Euclidean":
                self._square.setEnabled(True)
            elif text == "Minkowski":
                self._power.setEnabled(True)

        alg_choice = ("Manhattan", "Euclidean", "Minkowski").index(default_settings["algorithm"])
        self._algorithm = utils.ComboBox("Manhattan", "Euclidean", "Minkowski", start_i=alg_choice)
        self._algorithm.dataPassed.connect(_change)
        self._algorithm.dataPassed.connect(lambda v: self.settingChanged.emit("algorithm", v))

        self._square = utils.CheckBox("", default_settings["square"])
        self._square.dataPassed.connect(lambda v: self.settingChanged.emit("square", v))
        self._power = utils.Spinbox(default_settings["power"], 1, validation.examples.power)
        self._power.dataPassed.connect(lambda v: self.settingChanged.emit("power", v))
        self._match_mode = utils.Enum(utils.Match, utils.Match[default_settings["size_match"]])
        self._match_mode.dataPassed.connect(lambda v: self.settingChanged.emit("match", v))
        self._size = utils.SizeControl(default_settings["cluster_size"], 1, validation.examples.size)
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

        _change(default_settings["algorithm"])

    def widgets(self) -> AlgorithmDict:
        return {"algorithm": self._algorithm, "square": self._square, "power": self._power, "size": self._size,
                "size_match": self._match_mode}


class Clusters(ClusterPage, SettingsPage[Algorithm], ProcessPage):
    """
    Concrete page representing the identification of clusters from a binary image.

    Attributes
    ----------
    _prev: ProcessingPipeline
        The previous stage in the pipeline, used to check whether a processed image is binary.
    _DBSCAN_clusters: ndarray | None
        The identified clusters from a binary image.
    _DBSCAN_regions: ndarray
        An array-form of the image representing the identified clusters.
    _epsilon: LabelledWidget[Spinbox]
        The widget controlling the 'epsilon' parameter (defined in the help text).
    _samples: LabelledWidget[Spinbox]
        The widget controlling the 'min_samples' parameter (defined in the help text).
    _progress: QProgressBar
        The widget representing the ratio of formed clusters to identified clusters (as formation of clusters involves
        working with bimodal images, which can introduce an overhead).
    _minimum_samples: LabelledWidget[Spinbox]
        An alias for `_samples` so that the attached DSL's variable namepsace is clearer.
    _automate: bool
        Whether to run an automated cluster process, which is single-threaded.
    """
    clusterFound = ClusterPage.clusterFound
    settingChanged = SettingsPage.settingChanged
    _newMax = core.pyqtSignal(int)
    _newVal = core.pyqtSignal(int)

    def __init__(self, size: int, cluster_colour: np.int_, initial_size: int, pipeline: ProcessingPipeline,
                 failure_action: typing.Callable[[Exception], None]):
        ClusterPage.__init__(self, size, cluster_colour, initial_size)
        SettingsPage.__init__(self, utils.SettingsDepth.REGULAR | utils.SettingsDepth.ADVANCED,
                              functools.partial(Algorithm, failure_action))
        ProcessPage.__init__(self)
        self._prev = pipeline
        self._DBSCAN_clusters: typing.Optional[np.ndarray] = None
        self._DBSCAN_regions: typing.Optional[np.ndarray] = None

        self._epsilon = utils.LabelledWidget("Epsilon",
                                             utils.Spinbox(default_settings["epsilon"], 0.01,
                                                           validation.examples.epsilon,
                                                           mode=utils.RoundingMode.DECIMAL),
                                             utils.LabelOrder.SUFFIX)
        self._samples = utils.LabelledWidget("Minimum Samples",
                                             utils.Spinbox(default_settings["minimum_samples"], 1,
                                                           validation.examples.minimum_samples),
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
        return "Cluster"

    @utils.Tracked
    def run(self):
        if self._state != utils.StoppableStatus.ACTIVE:
            return
        self.runStart.emit()
        if (img := self._prev.modified) is None:
            raise StagingError("segmentation", "pre-processing")
        try:
            img.demote().norm().downchannel(0, 255)
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
        img = self._prev.modified.demote()
        data = img.norm().data()

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

        if (largest := np.max(clusters)) == 0:
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

        all_clusters = images.RGBImage(self._DBSCAN_regions)
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
            if not _size(cluster := utils.Cluster(all_clusters.downchannel(0, blue, invalid=images.ColourConvert.TO_BG),
                                                  blue)):
                self._cluster_image.replace(blue, 0)
                self._progress.setMaximum(self._progress.maximum() - 1)
                continue
            i += 1
            self._clusters.append(cluster)
            self.clusterFound.emit(i)

        self._modified_image = self._cluster_image.downchannel(0, self._cluster_colour,
                                                               invalid=images.ColourConvert.TO_FG).upchannel()
        self._canvas.draw(self._modified_image)
        self.runEnd.emit()

    def automate(self):
        """
        Perform an automated, single-threaded clustering process.
        """
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
