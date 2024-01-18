"""
Module to group pockets of similar particles into one cluster.
"""
import collections
import typing

import numpy as np
from PyQt5 import QtWidgets as widgets
from sklearn.cluster import DBSCAN

from modular_qt import utils as scans, errors, validators
from . import base, extra_widgets
from .base import core, sq, utils, events
from ._preprocess import PreprocessPage
from ._scan import ScanPage
from PyQt5.QtCore import Qt as enums


class GridSetup(utils.AdvancedSettingWindow):
    """
    Subclass to represent the settings controlling both grid squares (excluding pitch size) and segmentation metrics.

    :cvar ALGORITHMS tuple[str, ...]: The algorithms that clustering can use.
    :cvar POWER tuple[int, int]: The power to use in Minkowski algorithms.
    :cvar OVERLAP tuple[int, int]: The percentage of overlap to use for setting up grid squares.
    :cvar PADDING tuple[int, int]: The minimum padding to add to each cluster bounding box.
    :cvar MATCH tuple[int, int]: The minimum percentage of each grid square to be filled for tightening.

    :var _algorithm PyQt5.QWidgets.QComboBox: The algorithm control.
    :var _square PyQt5.QWidgets.QCheckBox: Whether to square the Euclidean distances.
    :var _power FixedSpinBox: The power control.
    :var _overlap_percentage FixedSpinBox: The overlap control.
    :var _padding FixedSpinBox: The padding control.
    :var _match_percentage FixedSpinBox: The match control.
    :var _pitch PyQt5.QWidgets.QSpinBox: The pitch size control (available from another advanced setting window).
    """
    ALGORITHMS = validators.xmpls.algorithm.values
    POWER = validators.xmpls.power.bounds
    OVERLAP = (int(validators.xmpls.overlap.bounds[0] * 100), int(validators.xmpls.overlap.bounds[1] * 100))
    PADDING = validators.xmpls.padding.bounds
    MATCH = (int(validators.xmpls.match.bounds[0] * 100), int(validators.xmpls.match.bounds[1] * 100))
    SIZE = validators.xmpls.size.bounds

    def __init__(self):
        super().__init__()
        self._algorithm = widgets.QComboBox()
        self._algorithm.addItems(self.ALGORITHMS)
        self._algorithm.currentTextChanged.connect(self._select)
        self._square = widgets.QCheckBox()
        self._power = extra_widgets.FixedSpinBox.from_range(self.POWER, 1, value=3)
        self._overlap_percentage = extra_widgets.FixedSpinBox.from_range(self.OVERLAP, 1, "%", value=10)
        self._padding = extra_widgets.FixedSpinBox.from_range(self.PADDING, 1, value=3)
        self._match_percentage = extra_widgets.FixedSpinBox.from_range(self.MATCH, 1, "%", value=35)
        self._width = extra_widgets.FixedSpinBox.from_range(self.SIZE, 1, value=10)
        self._height = extra_widgets.FixedSpinBox.from_range(self.SIZE, 1, value=10)
        self._layout.addWidget(widgets.QLabel("Algorithm"), 0, 0)
        self._layout.addWidget(self._algorithm, 0, 1)
        self._layout.addWidget(widgets.QLabel("(Metric to pass into DBScan)"), 0, 2)
        self._layout.addWidget(widgets.QLabel("Square?"), 1, 0)
        self._layout.addWidget(self._square, 1, 1)
        self._layout.addWidget(widgets.QLabel("(Whether to square the euclidean distances)"), 1, 2)
        self._layout.addWidget(widgets.QLabel("Power"), 2, 0)
        self._layout.addWidget(self._power, 2, 1)
        self._layout.addWidget(widgets.QLabel("(Exponential to use in Minkowski algorithm)"), 2, 2)
        self._layout.addWidget(widgets.QLabel("Overlap"), 3, 0)
        self._layout.addWidget(self._overlap_percentage, 3, 1)
        self._layout.addWidget(widgets.QLabel("(Percentage of pitch size to use for overlap)"), 3, 2)
        self._layout.addWidget(widgets.QLabel("Padding"), 4, 0)
        self._layout.addWidget(self._padding, 4, 1)
        self._layout.addWidget(widgets.QLabel("(Minimum amount of padding to apply)"), 4, 2)
        self._layout.addWidget(widgets.QLabel("Match"), 5, 0)
        self._layout.addWidget(self._match_percentage, 5, 1)
        self._layout.addWidget(widgets.QLabel("(Amount of sample to have in grid square to constitute valid square)"),
                               5, 2)
        self._layout.addWidget(widgets.QLabel("Min Width"), 6, 0)
        self._layout.addWidget(self._width, 6, 1)
        self._layout.addWidget(widgets.QLabel("(Minimum width of clusters to be bounded)"), 6, 2)
        self._layout.addWidget(widgets.QLabel("Min Height"), 7, 0)
        self._layout.addWidget(self._height, 7, 1)
        self._layout.addWidget(widgets.QLabel("(Minimum height of clusters to be bounded)"), 7, 2)
        self._algorithm.setCurrentText("Euclidean")

    def widgets(self) -> dict[str, widgets.QWidget]:
        return dict(
            algorithm=self._algorithm,
            square=self._square,
            power=self._power,
            overlap=self._overlap_percentage,
            padding=self._padding,
            match=self._match_percentage,
            min_cluster_width=self._width,
            min_cluster_height=self._height
        )

    def _select(self, txt: str):
        """
        Select which options to enable based on the algorithm.

        :param txt: The algorithm.
        """
        self._power.setEnabled(False)
        self._square.setEnabled(False)
        if txt == "Euclidean":
            self._square.setEnabled(True)
        elif txt == "Minkowski":
            self._power.setEnabled(True)


class SegmentationPage(base.DrawingPage, base.SettingsPage, base.ProcessPage):
    """
    Concrete subclass to represent the page to segment or cluster the preprocessed stage.

    :cvar EPSILON_RANGE tuple[float, float]: The range of values 'Epsilon' can be.
    :cvar SAMPLE_RANGE tuple[int, int]: The range of values 'Minimum Samples' can be.

    :var _epsilon FixedDoubleSpinBox: The value of 'Epsilon'.
    :var _samples FixedSpinBox: The value of 'Minimum Samples'
    :var _tighten PyQt5.QWidgets.QPushButton: The command to tighten grid squares.
    :var _format PreprocessPage: The previous stage in the pipeline.
    :var _loose dict[tuple[int, int, int], tuple[ScanSite, int, int]]: The loose grid squares.
    :var _tight list[ScanSite]: The tightened grid squares.
    :var _region tuple[int, int, int] | None: The region the tightening algorithm stopped on.
    :var _offset tuple[int, int] | None: The offset the tightening algorithm stopped on.
    :var _square_colour Colour: The colour to draw the grid squares.
    :var _colours dict[int, int]: A mapping of DBSCAN labels to actual colours used.
    """
    EPSILON_RANGE = validators.xmpls.epsilon.bounds
    SAMPLE_RANGE = validators.xmpls.minimum_samples.bounds

    @property
    def squares(self) -> list[scans.ScanSite]:
        """
        Public access to the grid squares.

        :return: The tightened grid squares.
        """
        return self._tight.copy()

    def __init__(self, size: int, prev: PreprocessPage, manager: core.QThreadPool,
                 pitch_control: ScanPage, *, colour: sq.Colour):
        super().__init__(size)
        super(base.DrawingPage, self).__init__(utils.Settings.REGULAR | utils.Settings.ADVANCED, GridSetup)
        super(base.SettingsPage, self).__init__(manager)
        self._epsilon = extra_widgets.FixedDoubleSpinBox.from_range((self.EPSILON_RANGE[0], self.EPSILON_RANGE[1]), 0.1,
                                                                    "Epsilon", value=4.2)
        self._samples = extra_widgets.FixedSpinBox.from_range((self.SAMPLE_RANGE[0], self.SAMPLE_RANGE[1]), 1,
                                                              "Minimum Samples", value=50)
        self._tighten = widgets.QPushButton("Tighten")
        self._tighten.clicked.connect(self._tighten_squares)
        self._reg_col.addWidget(self._epsilon)
        self._reg_col.addWidget(self._samples)
        self._reg_col.addWidget(self._tighten)
        self._format = prev
        self._loose: dict[tuple[int, int, int], tuple[scans.ScanSite, int, int]] = {}
        self._tight: list[scans.ScanSite] = []
        self._region: typing.Optional[tuple[int, int, int]] = None
        self._offset: typing.Optional[tuple[int, int]] = None
        self._square_colour = colour
        self._colours: dict[int, int] = {}
        self._pitch_size = pitch_control.pitch_size

    def compile(self) -> str:
        return "cluster\nclick @ all\ntighten"

    def stop(self):
        base.SettingsPage.stop(self)
        base.ProcessPage.stop(self)
        base.DrawingPage.stop(self)
        self._region = None
        self._offset = None

    @base.SettingsPage.lock
    def run(self, btn_state: bool):
        """
        Will cluster the preprocessed image using DBSCAN with selected metrics.

        :param btn_state: The state of the button that triggered this callback.
        """
        self.triggered.emit(self.run)
        if self._format.get_mutated() is None:
            raise errors.StagingError("Clustering", "Thresholding")
        new_im = self._format.get_mutated().get_channeled_image()
        where_white = np.where(new_im == 255)
        white = np.asarray(where_white).T
        regions = np.zeros_like(new_im)
        kwargs = {}
        al = self.get_setting("algorithm")
        if al == "Euclidean" and self.get_setting("square") == enums.Checked:
            al = f"Sq{al}"
        elif al == "Minkowski":
            kwargs["p"] = self.get_setting("power")
        clusters = DBSCAN(self._epsilon.value(), min_samples=self._samples.value(), metric=al.lower(),
                          metric_params=kwargs).fit_predict(white) + 1
        step = (255 * 3) // len(np.unique(clusters))
        stepped = clusters * step
        regions[where_white] = stepped
        self._curr = sq.Image(regions[:, :, 0], auto_wrap=True)
        self._original = self._curr.copy()
        self._canvas.image(self._curr.get_channeled_image(sq.RGBOrder.RGB) / 255)
        self._colours = dict(zip(clusters, stepped))

    @base.SettingsPage.lock
    def mouseReleaseEvent(self, a0: events.QMouseEvent):
        """
        Handles clicking the canvas.

        :param a0: The event that caused the callback.
        :raise StagingError: If called before clustering.
        """
        if self._curr is None:
            raise errors.StagingError("Adding Grid Squares", "Clustering")
        self._tight.clear()
        button = a0.button()
        pos = a0.pos()
        # if pos.x() > self._canvas.figsize or pos.y() > self._canvas.figsize:
        #     return
        if button == enums.LeftButton:
            self.triggered.emit(lambda state: self._add_square(pos.x(), pos.y()))
            self._add_square(pos.x(), pos.y())
        elif button == enums.RightButton:
            self.triggered.emit(lambda state: self._rem_square(pos.x(), pos.y()))
            self._rem_square(pos.x(), pos.y())

    @base.SettingsPage.lock
    def _tighten_squares(self, btn_state: bool):
        """
        Method to perform the grid tightening algorithm.

        :param btn_state: The state of the button that caused this callback.
        :raise StagingError: If called before clicking on the canvas.
        """
        self.triggered.emit(self._tighten_squares)
        if self._original is None:
            raise errors.StagingError("Tightening Grid Squares", "Adding Grid Squares")
        image = self._original.get_channeled_image()
        img = self._original.copy().get_raw()
        fill = self.get_setting("match") / 100
        colour = self._square_colour.all(sq.RGBOrder.BGR)

        def _filter():
            for region, (cluster, size, overlap) in self._loose.items():
                if self._region is None:
                    self._region = region
                if self._region != region:
                    continue
                for offset in ((0, 0), (overlap, 0), (0, overlap), (overlap, overlap)):
                    if self._offset is None:
                        self._offset = offset
                    if self._offset != offset:
                        continue
                    for i, site in enumerate(cluster.split(size, offset)):
                        if self._tracked_index > i:
                            continue
                        self._tracked_index = i
                        item = self._find_bounds(site, img)
                        if item is None:
                            self._canvas.image(img[:, :, ::-1])
                            return
                        left, top, right, bottom = item
                        section = image[top:bottom, left:right]
                        area = sq.Image(section, auto_wrap=True).search(
                            sq.Colour.from_order(*region, order=sq.RGBOrder.BGR)).shape[0]
                        w, h = site.region_size
                        pass_ = int(fill * w * h)
                        if area >= pass_:
                            img[top:bottom, (left, right)] = colour
                            img[(top, bottom), left:right] = colour
                            self._tight.append(site)
                        self._tracked_index = 0
                    self._offset = None
                self._region = None
                self._canvas.image(img[:, :, ::-1])
            self._curr = sq.Image(img, auto_wrap=True)

        self._thread(_filter)()

    def _get_colour(self, colour: sq.Colour) -> tuple[int, int, int]:
        if colour == sq.Colours.BLACK:
            self._running = False
            raise errors.DialogError(errors.Level.WARNING, "Non featured area", "No cluster found at click")
        return colour.all(sq.RGBOrder.BGR)

    def _find_bounds(self, site: scans.ScanSite, cached: np.ndarray) -> typing.Optional[tuple[int, int, int, int]]:
        if not self._activated:
            self._canvas.image(cached[:, :, ::-1])
            return
        left, top = site.extract_point(scans.HSide.LEFT | scans.VSide.TOP)
        right, bottom = site.extract_point(scans.HSide.RIGHT | scans.VSide.BOTTOM)
        return left, top, right, bottom

    def _add_square(self, x: int, y: int, *, colour: sq.Colour = None):
        """
        Method to add grid squares to clusters.

        :param x: The horizontal deviation.
        :param y: The vertical deviation.
        :param colour: Optional colour to use if not called from an event.
        :raise DialogError: If colour doesn't exist.
        """
        if colour:
            click_colour = colour
        else:
            click_colour = self._curr[x, y]
        if colour and colour == sq.Colours.BLACK:
            self._running = False
            return
        tup_colour = self._get_colour(click_colour)

        region = self._curr.search(click_colour)
        if len(region.shape) == 1:
            raise errors.DialogError(errors.Level.INFO, "Cluster error", f"No points match {tup_colour[::-1]}")
        step = self._pitch_size()
        only_x = region[:, 1]
        only_y = region[:, 0]
        padding = self.get_setting("padding")

        def _minmax(data: np.ndarray, dim: typing.Literal["width", "height"]) \
                -> tuple[typing.Optional[int], typing.Optional[int]]:
            local_minima, local_maxima = np.min(data), np.max(data)
            if (local_maxima - local_minima) <= self.get_setting(f"min_cluster_{dim}"):
                return None, None
            minima, maxima = max(local_minima - padding, 0), min(local_maxima + padding, self._canvas.figsize - 1)
            while (maxima - minima) % step != 0 and minima != 0:
                minima -= 1
            while (maxima - minima) % step != 0 and maxima != self._canvas.figsize - 1:
                maxima += 1
            return minima, maxima

        min_x, max_x = _minmax(only_x, "width")
        min_y, max_y = _minmax(only_y, "height")
        if any(corner is None for corner in (min_x, max_x, min_y, max_y)):
            if colour:
                self._running = False
                return
            raise errors.DialogError(errors.Level.INFO, "Cluster error", "Cluster too small")
        line_step = step - int(self.get_setting("overlap") / 100 * step)

        cluster = scans.ScanSite((min_y, min_x), (max_y, max_x), self._canvas.figsize)

        self._loose[tup_colour] = (cluster, step, line_step)

        img = self._curr.get_raw()
        colour = self._square_colour.all(sq.RGBOrder.BGR)

        def _draw_offset():
            for offset in ((0, 0), (line_step, 0), (0, line_step), (line_step, line_step)):
                for site in cluster.split(step, offset):
                    item = self._find_bounds(site, img)
                    if item is None:
                        return
                    left, top, right, bottom = item
                    img[top:bottom, (left, right)] = colour
                    img[(top, bottom), left:right] = colour
                self._canvas.image(img[:, :, ::-1])

        self._thread(_draw_offset)()

    def _rem_square(self, x: int, y: int, *, colour: sq.Colour = None):
        """
        Method to remove grid squares from clusters.

        :param x: The horizontal deviation.
        :param y: The vertical deviation.
        :param colour: Optional colour to use if not called from an event.
        :raise DialogError: If colour doesn't have grid squares.
        """
        if colour:
            click_colour = colour
        else:
            click_colour = self._curr[x, y]
        tup_colour = self._get_colour(click_colour)
        if tup_colour not in self._loose:
            raise errors.DialogError(errors.Level.INFO, "Cluster Error",
                                     f"No grid squares for cluster {tup_colour[::-1]}")
        img = self._curr.get_raw()
        orig = self._original.get_raw()

        cluster, size, overlap = self._loose.pop(tup_colour)

        def _remove_offset():
            for offset in ((0, 0), (0, overlap), (overlap, 0)):
                for site in cluster.split(size, offset):
                    item = self._find_bounds(site, img)
                    if item is None:
                        return
                    left, top, right, bottom = item
                    img[top:bottom, (left, right)] = orig[top:bottom, (left, right)]
                    img[(top, bottom), left:right] = orig[(top, bottom), left:right]
                self._canvas.image(img[:, :, ::-1])

        self._thread(_remove_offset)()
