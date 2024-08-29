import abc
import typing
from typing import List as _list, Tuple as _tuple

import numpy as np
import typing_extensions
from PyQt5 import QtCore as core, QtGui as gui, QtWidgets as widgets

from . import utils
from ._errors import *
from .. import images, microscope

P = typing.TypeVar("P", bound=utils.SettingsPopup)
Spec = typing_extensions.ParamSpec("Spec")


class Page(widgets.QWidget, abc.ABC, metaclass=utils.AbstractWidget):
    """
    Abstract Base Class representing an interactable page in the GUI. It is accessed through a notebook tab.

    Signals
    -------
    runStart:
        Emitted when the page starts running - carries no data.
    runEnd:
        Emitted when the page stops running - carries no data.

    Abstract Methods
    ----------------
    compile
    run
    clear
    help

    Attributes
    ----------
    _layout: QGridLayout
        The main layout for the page.
    _state: StoppableStatus
        The current state of the page.
        Much like a tracked decorator, each page can be paused or killed.
    _safe: tuple[BaseDecorator, ...]
        A list of decorators that are also tracked. Note that the tracking does not have to be the outermost decorator
        - as long as somewhere in the nesting chain there is a `Tracked` decorator.
    """
    _layout: widgets.QGridLayout

    runStart = core.pyqtSignal()
    runEnd = core.pyqtSignal()

    def __init__(self):
        widgets.QWidget.__init__(self)
        if not hasattr(self, "_layout"):
            self._layout = widgets.QGridLayout()
        self._state = utils.StoppableStatus.ACTIVE
        self._safe = tuple(fn for fn in type(self).__dict__.values() if
                           isinstance(fn, utils.BaseDecorator) and fn.is_(utils.Tracked))
        for fn in self._safe:
            fn = fn.find(utils.Tracked)
            try:
                fn.callFailed.disconnect(self._err)
            except TypeError:
                pass
            fn.callFailed.connect(self._err)

    def start(self):
        """
        Start the page and perform all necessary setup.
        """
        self._state = utils.StoppableStatus.ACTIVE

    def stop(self):
        """
        Stop the page and perform all necessary shutdown tasks.
        """
        self._state = utils.StoppableStatus.DEAD

    def pause(self):
        """
        Stop the page, but don't perform any shutdown tasks.
        """
        self._state = utils.StoppableStatus.PAUSED

    @abc.abstractmethod
    def compile(self) -> str:
        """
        Compile the page into a series of statements compatible with the attached DSL.

        Returns
        -------
        str
            A source code string containing the compiled code.
        """
        pass

    @abc.abstractmethod
    def run(self):
        """
        Perform this page's main action. This is nominally linked to a button on the GUI.
        """
        pass

    @abc.abstractmethod
    def clear(self):
        """
        Completely wipe the page's data. Useful for specific sequencing.
        """
        pass

    # @abc.abstractmethod
    def help(self) -> str:
        """
        Return a user-friendly description of the page. This includes all settings.

        Returns
        -------
        str
            The user-friendly description of the page.
        """
        return ""

    def advanced_help(self) -> str:
        """
        Return a user-friendly description of any extra information about the page - this is usually advanced settings.

        Returns
        -------
        str
            The user-friendly extra information.
        """
        return ""

    def _err(self, exc: Exception):
        if isinstance(exc, GUIError):
            popup_error(exc, self)
        else:
            raise exc


class CanvasPage(Page, abc.ABC):
    """
    An abstract page with an attached canvas for visually displaying image data.

    The image data can optionally have a tooltip. By default, this outputs the co-ordinates and the colour of the pixel
    under the cursor.

    Abstract Methods
    ----------------
    compile
    run
    clear
    help

    Attributes
    ----------
    _display_type: ColourDisplay
        The way that colour information is formatted.
    _original_image: RGBImage | None
        The original image taken when the run is started.
    _modified_image: RGBImage | None
        The current working image. While in most cases it is different to the original image, it may just be a copy.
    _canvas: Canvas
        The canvas that displays the image data.
    _colour_option: Enum
        The widget for the user to control the way that colour information is formatted.

    Parameters
    ----------
    size: tuple[int, int]
        The size of the canvas (and expected image size).
    canvas_tracks: bool
        Whether the canvas live-tracks the mouse, or whether the cursor position is only tracked while click-dragging.
    movement_handler: Callable[[QMouseEvent], None] | None
        How to handle a mouse-movement event. If left blank, will default to the tooltip instruction.
    """

    @property
    def original(self) -> typing.Optional[images.RGBImage]:
        """
        Public access to the original image.

        Returns
        -------
        RGBImage | None
            The original image taken when the run is started.
            Note this is not a copy, and is the actual, mutable instance, so no changes are expected.
        """
        return self._original_image

    @property
    def modified(self) -> typing.Optional[images.RGBImage]:
        """
        Public access to the current image.

        Returns
        -------
        RGBImage | None
            The current working image.
            Note this is not a copy, and is the actual, mutable instance, so no changes are expected.
        """
        return self._modified_image

    def __init__(self, size: int, canvas_tracks=True,
                 movement_handler: typing.Callable[[gui.QMouseEvent], None] = None):
        if movement_handler is None:
            movement_handler = self._tooltip
        Page.__init__(self)
        self._display_type = utils.ColourDisplay.RGB
        self._original_image: typing.Optional[images.RGBImage] = None
        self._modified_image: typing.Optional[images.RGBImage] = None

        self._canvas = utils.Canvas((size, size), live_mouse=canvas_tracks)
        self._canvas.mouseMoved.connect(movement_handler)

        self._colour_option = utils.Enum(utils.ColourDisplay, self._display_type)
        self._colour_option.currentIndexChanged.connect(
            lambda d: setattr(self, "_display_type", utils.ColourDisplay(d + 1))
        )

        self._layout.addWidget(self._canvas, 0, 0)
        self._layout.addWidget(self._colour_option, 1, 0)

    def clear(self):
        self._canvas.clear()
        self._original_image = self._modified_image = None

    def _tooltip(self, event: gui.QMouseEvent):
        rel_pos = event.pos()
        x, y = rel_pos.x(), rel_pos.y()
        if not self._canvas.displaying:
            return
        widgets.QToolTip.showText(event.globalPos(), "\n".join(self._process_tooltip(x, y)))

    def _process_tooltip(self, x: int, y: int) -> typing.Iterator[str]:
        yield f"<{x}, {y}>"
        # <editor-fold desc="Colour Handling">
        with self._canvas as img:
            colour = img.normalise(img[x, y])  # should be in range 0 → (2 ** 24 - 1)
        hexa = f"{colour:06x}"
        if self._display_type == utils.ColourDisplay.HEX:
            clr = hexa
        else:
            clr = str((int(hexa[0:2], 16), int(hexa[2:4], 16), int(hexa[4:6], 16)))
        # </editor-fold>
        yield clr


class ClusterPage(CanvasPage, abc.ABC):
    """
    Abstract canvas page for pages that deal with clusters.

    Signals
    -------
    clusterFound: int
        Emitted when a cluster has been found. Carries the unique integer identifier of the cluster.#

    Abstract Methods
    ----------------
    compile
    run
    clear
    help

    Attributes
    ----------
    _clusters: list[Cluster]
        The found clusters.
    _cluster_image: RGBImage | None
        The specific image for the found clusters.
    _cluster_colour: int_
        The colour of the found clusters. This ensures all clusters are represented uniformly.
    _pitch_size: int
        The expected size of the grid squares to divide each cluster into.
    """
    clusterFound = core.pyqtSignal(int)

    @property
    def cluster(self) -> typing.Optional[images.RGBImage]:
        """
        Public access to the cluster image.

        Returns
        -------
        RGBImage | None
            The specific image for the found clusters.
        """
        return self._cluster_image

    def __init__(self, size: int, cluster_colour: np.int_, initial_size: int, canvas_tracks=True,
                 movement_handler: typing.Callable[[gui.QMouseEvent], None] = None):
        super().__init__(size, canvas_tracks, movement_handler)
        self._clusters: _list[utils.Cluster] = []
        self._cluster_image: typing.Optional[images.RGBImage] = None
        self._cluster_colour = cluster_colour
        self._pitch_size = initial_size

    def colour(self) -> np.int_:
        """
        Finds the cluster colour.

        Returns
        -------
        int_
            The colour of the found clusters.
        """
        return self._cluster_colour

    def set_colour(self, colour: np.int_):
        """
        Sets the cluster colour.

        Parameters
        ----------
        colour: int_
            The new colour of the found clusters.
        """
        self._cluster_colour = colour

    def pitch_size(self) -> int:
        """
        Finds the `ScanRegion` size.

        Returns
        -------
        int
            The expected size of the grid squares to divide each cluster into.
        """
        return self._pitch_size

    def set_pitch_size(self, new: int):
        """
        Sets the `ScanRegion` size.

        Parameters
        ----------
        new: int
            The new size of the grid squares to divide each cluster into.
        """
        self._pitch_size = new

    def clear(self):
        super().clear()
        self._clusters.clear()
        self._cluster_image = None

    def get_clusters(self) -> _tuple[utils.Cluster, ...]:
        """
        Gets the found clusters.

        Returns
        -------
        tuple[Cluster, ...]
            The found clusters, wrapped into an immutable data structure.

        Raises
        ------
        StagingError
            If no clusters are found.
        """
        if not self._clusters:
            raise StagingError("Extracting Clusters", "Finding Clusters")
        return tuple(self._clusters)


class SettingsPage(Page, abc.ABC, typing.Generic[P]):
    """
    Abstract page subclass representing pages with parameters (settings) that can change.

    Abstract Methods
    ----------------
    compile
    run
    clear
    help
    all_settings

    Generics
    --------
    P: SettingsPopup
        The advanced settings popup type.

    Signals
    -------
    settingChanged: str, object
        Emitted when a setting has been changed. Contains data for the setting name and the new value.

    Attributes
    ----------
    _regular: QGridLayout
        The layout for critical settings.
    _popup: P | None
        The non-critical settings popup.
        It's None if there are no non-critical settings.
    """
    settingChanged = core.pyqtSignal(str, object)

    def __init__(self, level: utils.SettingsDepth, advanced: typing.Callable[[], P] = None):
        super().__init__()
        self._regular = widgets.QGridLayout()
        popup = widgets.QPushButton("Ad&vanced Settings")
        self._popup: typing.Optional[P] = None
        if level & utils.SettingsDepth.REGULAR:
            w = widgets.QWidget()
            w.setLayout(self._regular)
            self._layout.addWidget(w, 0, 1)
        if level & utils.SettingsDepth.ADVANCED:
            self._popup = advanced()
            self._popup.settingChanged.connect(lambda s, o: self.settingChanged.emit(s, o))
            popup.clicked.connect(lambda: self._display_popup(self._popup))
            self._layout.addWidget(popup, 1, 1)

    def start(self):
        Page.start(self)
        self.setEnabled(True)

    def stop(self):
        Page.stop(self)
        self.setEnabled(False)

    @abc.abstractmethod
    def all_settings(self) -> typing.Iterator[str]:
        """
        Get the names of all the available settings, critical or not.

        Yields
        ------
        str
            The name of an available setting.
        """
        pass

    def get_setting(self, name: str):
        """
        Get a specific named setting.

        Parameters
        ----------
        name: str
            The setting name.

        Returns
        -------
        Any
            The setting's value.
        """
        return self.getter(self.get_control(name))

    def set_setting(self, name: str, value):
        """
        Set a specific named setting.

        Parameters
        ----------
        name: str
            The setting name.
        value: Any
            The new value for the setting.
        """
        self.setter(self.get_control(name), value)

    def get_control(self, name: str) -> widgets.QWidget:
        """
        Get a widget that holds a specific setting.

        Parameters
        ----------
        name: str
            The setting name to find the widget for.

        Returns
        -------
        QWidget
            The widget that controls the specified setting.

        Raises
        ------
        AttributeError
            If the setting is not found.
        """
        if self._popup is None:
            widget = None
        else:
            widget = self._popup.widgets().get(name)
        if widget is None:
            if not name.startswith("_"):
                name = f"_{name}"
            widget = getattr(self, name, None)
            if widget is None or not isinstance(widget, widgets.QWidget):
                raise AttributeError(f"Cannot find {name!r} in settings for {self.__class__}")
        if isinstance(widget, utils.LabelledWidget):
            widget = widget.focus
        return widget

    @staticmethod
    def getter(widget: widgets.QWidget):
        """
        Get the main data for a particular widget.

        Parameters
        ----------
        widget: QWidget
            The widget to get the data for.

        Returns
        -------
        Any
            The main data for a particular widget.

        Raises
        ------
        NotImplementedError
            If the type of widget is not supported.
        """
        if isinstance(widget, utils.LabelledWidget):
            return SettingsPage.getter(widget.focus)
        if isinstance(widget, (utils.ValidatedWidget, utils.XDControl)):
            return widget.get_data()
        elif isinstance(widget, widgets.QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, utils.OrderedGroup):
            return tuple(map(SettingsPage.getter, widget.get_members()))
        elif isinstance(widget, widgets.QLabel):
            return widget.text()
        raise NotImplementedError(f"{type(widget)} unhandled")

    @staticmethod
    def setter(widget: widgets.QWidget, value):
        """
        Set the main data for a particular widget.

        Parameters
        ----------
        widget: QWidget
            The widget to get the data for.
        value: Any
            The new data.

        Raises
        ------
        NotImplementedError
            If the type of widget is not supported.
        """
        if isinstance(widget, utils.Flag):
            raise NotImplementedError(f"{value=} FLAGS unhandled")
        elif isinstance(widget, (utils.ValidatedWidget, utils.XDControl)):
            widget.change_data(value)
        elif isinstance(widget, widgets.QCheckBox):
            widget.setCheckState(value)
        elif isinstance(widget, utils.OrderedGroup):
            widget.configure_members(SettingsPage.getter, SettingsPage.setter, *value)
        elif isinstance(widget, widgets.QLabel):
            widget.setText(value)
        else:
            raise NotImplementedError(f"{type(widget)} unhandled")

    @staticmethod
    def _display_popup(wid: widgets.QWidget):
        if not wid.isVisible():
            wid.show()
        else:
            wid.raise_()


class ProcessPage(Page, abc.ABC):
    """
    Abstract page subclass representing pages with long-running processes that needed to be threaded.

    Abstract Methods
    ----------------
    compile
    run
    clear
    help

    Attributes
    ----------
    MANAGER: QThreadPool
        A thread pool to manage all long-running processes.
        Note that this is a static attribute, implying that *all* processes share the same manager.
        This is crucial to ensure that QT centrally manages the scheduling.
    _threaded: tuple[Stoppable, ...]
        A tuple of threaded functions. Note that the stoppable *is* expected to be the final decorator, due to the way
        that `Stoppable` handles parameters.
    """
    MANAGER = core.QThreadPool()

    def __init__(self):
        Page.__init__(self)
        self._threaded = tuple(fn for fn in type(self).__dict__.values() if isinstance(fn, utils.Stoppable))

    def clear(self):
        for fn in self._threaded:
            fn.stop.emit()

    def start(self):
        Page.start(self)
        for fn in self._threaded:
            if fn.state == utils.StoppableStatus.PAUSED:
                fn.play.emit()

    def stop(self):
        Page.stop(self)
        for fn in self._threaded:
            fn.stop.emit()


class CorrectionPage(SettingsPage, abc.ABC):
    """
    Abstract settings page to represent a page to correct for a specific hardware issue.

    Signals
    -------
    conditionHit:
        Emitted when the correction is required to run (but has not yet started).

    Abstract Methods
    ----------------
    run
    help

    Attributes
    ----------
    _link: Microscope
        The microscope hardware to control.
    """
    conditionHit = core.pyqtSignal()

    def __init__(self, mic: microscope.Microscope):
        SettingsPage.__init__(self, utils.SettingsDepth.REGULAR)
        self.conditionHit.connect(self.run)
        run = widgets.QPushButton("&Run Now")
        run.clicked.connect(self.conditionHit.emit)
        self._regular.addWidget(run)
        self._link = mic

    def compile(self) -> str:
        return ""

    def clear(self):
        pass


class LongCorrectionPage(CorrectionPage, ProcessPage, abc.ABC):
    """
    Abstract correctional page that is a long-running process, periodically polling some resource.

    Abstract Methods
    ----------------
    run
    help
    background

    Attributes
    ----------
    DELAY: float
        The delay in seconds between polling some resource.
    """
    conditionHit = CorrectionPage.conditionHit
    settingChanged = CorrectionPage.settingChanged

    DELAY = 0.01

    def __init__(self, mic: microscope.Microscope):
        CorrectionPage.__init__(self, mic)
        ProcessPage.__init__(self)
        self.background()

    def start(self):
        CorrectionPage.start(self)
        ProcessPage.start(self)

    def stop(self):
        CorrectionPage.stop(self)
        ProcessPage.stop(self)

    @abc.abstractmethod
    def background(self):
        """
        Run the background polling sequence. This nominally checks some resource every `DELAY` seconds.
        """
        pass


class ShortCorrectionPage(CorrectionPage, abc.ABC):
    """
    Abstract correctional page that is not a long-running process, instead relying on an external counter.

    Abstract Methods
    ----------------
    run
    help
    query
    """
    conditionHit = CorrectionPage.conditionHit
    settingChanged = CorrectionPage.settingChanged

    @abc.abstractmethod
    def query(self):
        """
        Query whether the correction is required.
        """
        pass
