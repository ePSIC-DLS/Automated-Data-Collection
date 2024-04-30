import abc
import typing
from typing import List as _list, Tuple as _tuple

import typing_extensions
from PyQt5 import QtCore as core, QtGui as gui, QtWidgets as widgets

from . import utils
from ._errors import *
from .. import images, microscope

P = typing.TypeVar("P", bound=utils.SettingsPopup)
Spec = typing_extensions.ParamSpec("Spec")


class Page(widgets.QWidget, abc.ABC, metaclass=utils.AbstractWidget):
    _layout: widgets.QGridLayout

    runStart = core.pyqtSignal()
    runEnd = core.pyqtSignal()

    def __init__(self):
        widgets.QWidget.__init__(self)
        if not hasattr(self, "_layout"):
            self._layout = widgets.QGridLayout()
        self._state = utils.StoppableStatus.ACTIVE
        self._safe = [fn for fn in type(self).__dict__.values() if
                      isinstance(fn, utils.BaseDecorator) and fn.is_(utils.Tracked)]
        for fn in self._safe:
            fn = fn.find(utils.Tracked)
            try:
                fn.callFailed.disconnect(self._err)
            except TypeError:
                pass
            fn.callFailed.connect(self._err)

    def start(self):
        self._state = utils.StoppableStatus.ACTIVE

    def stop(self):
        self._state = utils.StoppableStatus.DEAD

    def pause(self):
        self._state = utils.StoppableStatus.PAUSED

    @abc.abstractmethod
    def compile(self) -> str:
        pass

    @abc.abstractmethod
    def run(self):
        pass

    @abc.abstractmethod
    def clear(self):
        pass

    # @abc.abstractmethod
    def help(self) -> str:
        return ""

    def advanced_help(self) -> str:
        return ""

    def _err(self, exc: Exception):
        if isinstance(exc, GUIError):
            popup_error(exc, self)
        else:
            raise exc


class CanvasPage(Page, abc.ABC):

    @property
    def original(self) -> typing.Optional[images.RGBImage]:
        return self._original_image

    @property
    def modified(self) -> typing.Optional[images.RGBImage]:
        return self._modified_image

    def __init__(self, size: int, canvas_tracks=True,
                 movement_handler: typing.Callable[[gui.QMouseEvent], None] = None):
        if movement_handler is None:
            movement_handler = self._tooltip
        Page.__init__(self)
        self._display_type = utils.ColourDisplay.HEX
        self._original_image: typing.Optional[images.RGBImage] = None
        self._modified_image: typing.Optional[images.RGBImage] = None

        self._canvas = utils.Canvas((size, size), live_mouse=canvas_tracks)
        self._canvas.mouseMoved.connect(movement_handler)

        self._colour_option = utils.Enum(utils.ColourDisplay, utils.ColourDisplay.HEX)
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
            colour = img[x, y]
        if self._display_type == utils.ColourDisplay.HEX:
            clr = str(colour)
        elif self._display_type == utils.ColourDisplay.RGB:
            clr = str(colour.items())
        else:
            colours = []
            if colour["r"]:
                colours.append("red")
            if colour["g"]:
                colours.append("green")
            if colour["b"]:
                colours.append("blue")
            if isinstance(colour, images.Grey):
                clr = "black" if colour["r"] == 0 else ("white" if colour["r"] == 255 else "grey")
                clr = f"A solid {clr}"
            elif len(colours) == 1:
                clr = f"A solid {colours[0]}"
            else:
                clr = f"A mixture of {' and '.join(colours)}"
        # </editor-fold>
        yield clr


class ClusterPage(CanvasPage, abc.ABC):
    clusterFound = core.pyqtSignal(int)

    @property
    def cluster(self) -> typing.Optional[images.RGBImage]:
        return self._cluster_image

    def __init__(self, size: int, cluster_colour: images.RGB, initial_size: int, canvas_tracks=True,
                 movement_handler: typing.Callable[[gui.QMouseEvent], None] = None):
        super().__init__(size, canvas_tracks, movement_handler)
        self._clusters: _list[utils.Cluster] = []
        self._cluster_image: typing.Optional[images.RGBImage] = None
        self._cluster_colour = cluster_colour
        self._pitch_size = initial_size

    def colour(self) -> images.RGB:
        return self._cluster_colour

    def set_colour(self, colour: images.RGB):
        self._cluster_colour = colour

    def pitch_size(self) -> int:
        return self._pitch_size

    def set_pitch_size(self, new: int):
        self._pitch_size = new

    def clear(self):
        super().clear()
        self._clusters.clear()
        self._cluster_image = None

    def get_clusters(self) -> _tuple[utils.Cluster, ...]:
        if not self._clusters:
            raise StagingError("Extracting Clusters", "Finding Clusters")
        return tuple(self._clusters)


class SettingsPage(Page, abc.ABC, typing.Generic[P]):
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
            popup.clicked.connect(lambda: self._popup.raise_() if self._popup.isVisible() else self._popup.show())
            self._layout.addWidget(popup, 1, 1)

    def start(self):
        Page.start(self)
        self.setEnabled(True)

    def stop(self):
        Page.stop(self)
        self.setEnabled(False)

    @abc.abstractmethod
    def all_settings(self) -> typing.Iterator[str]:
        pass

    def get_setting(self, name: str):
        return self.getter(self.get_control(name))

    def set_setting(self, name: str, value):
        self.setter(self.get_control(name), value)

    def get_control(self, name: str) -> widgets.QWidget:
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
        if isinstance(widget, (utils.ValidatedWidget, utils.XDControl)):
            return widget.get_data()
        elif isinstance(widget, widgets.QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, utils.OrderedGroup):
            return widget.get_members()
        elif isinstance(widget, utils.ScanPatternGroup):
            return widget.chosen()
        elif isinstance(widget, widgets.QLabel):
            return widget.text()
        raise NotImplementedError(f"{type(widget)} unhandled")

    @staticmethod
    def setter(widget: widgets.QWidget, value):
        if isinstance(widget, utils.Flag):
            raise NotImplementedError(f"{value=} FLAGS unhandled")
        elif isinstance(widget, (utils.ValidatedWidget, utils.XDControl)):
            widget.change_data(value)
        elif isinstance(widget, widgets.QCheckBox):
            widget.setCheckState(value)
        elif isinstance(widget, utils.ScanPatternGroup):
            widget.select(value)
        elif isinstance(widget, utils.OrderedGroup):
            widget.configure_members(SettingsPage.getter, SettingsPage.setter, *value)
        elif isinstance(widget, widgets.QLabel):
            widget.setText(value)
        else:
            raise NotImplementedError(f"{type(widget)} unhandled")


class ProcessPage(Page, abc.ABC):
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
        pass


class ShortCorrectionPage(CorrectionPage, abc.ABC):
    conditionHit = CorrectionPage.conditionHit
    settingChanged = CorrectionPage.settingChanged

    @abc.abstractmethod
    def query(self):
        pass
