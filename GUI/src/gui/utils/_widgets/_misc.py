import functools
import typing
from typing import Dict as _dict, Tuple as _tuple

import numpy as np
from PyQt5 import QtWidgets as widgets, QtCore as core, QtGui as gui

from ....images import RGBOrder, RGBImage, GreyImage, AABBCorner, RGB, Grey

__all__ = ["FileDialog", "FilePrompt", "Canvas", "Subplot"]


class FileDialog(widgets.QDialog):
    """
    A dialog that opens a file browser for loading files.

    Signals
    -------
    open: str
        Emitted when the open command is sent.
    save: str
        Emitted when the save command is sent.

    Attributes
    ----------
    BASE: str
        The base path for all file dialogs.
    _file_model: widgets.QFileSystemModel
        The file system model for viewing directories.
    _filepath: str
        The current filepath.

    Parameters
    ----------
    parent: widgets.QWidget
        The parent widget to spawn the dialog from.
    *filters: str
        The filters to apply to the dialog to restrict the file views.
    open_txt: str (default is "open")
        The text to display on the open button.
    save_txt: str (default is "save")
        The text to display on the save button.
    path: str (default is `BASE`)
        The path to use for the file dialogs.
    sections: dict[int, bool] (default is {})
        The section indices to display.
    section_sizes: dict[int, widgets.QHeaderView.ResizeMode] (default is {})
        The resize policies for the sections.

    Raises
    ------
    ValueError
        If a hidden section has a resize policy.
    """
    openFile = core.pyqtSignal(str)
    saveFile = core.pyqtSignal(str)

    BASE = r""

    def __init__(self, parent: widgets.QWidget, *filters: str, open_txt="open", save_txt="save", path=BASE,
                 sections: _dict[int, bool] = None, section_sizes: _dict[int, widgets.QHeaderView.ResizeMode] = None):
        if sections is None:
            sections = {}
        if section_sizes is None:
            section_sizes = {}
        super().__init__(parent)

        btns = widgets.QDialogButtonBox(widgets.QDialogButtonBox.Save | widgets.QDialogButtonBox.Open)
        open_btn = btns.button(widgets.QDialogButtonBox.Open)
        open_btn.clicked.connect(functools.partial(self._handle_file, self.openFile))
        save_btn = btns.button(widgets.QDialogButtonBox.Save)
        save_btn.clicked.connect(functools.partial(self._handle_file, self.saveFile))
        open_btn.setText(open_txt)
        save_btn.setText(save_txt)

        self._file_model = widgets.QFileSystemModel()
        self._file_model.setReadOnly(False)
        self._file_model.setNameFilters(filters)
        self._file_model.setNameFilterDisables(False)
        root = self._file_model.setRootPath(path)

        navigator = widgets.QTreeView()
        navigator.setModel(self._file_model)
        navigator.setRootIndex(root)
        navigator.clicked.connect(self._select_file)
        head = navigator.header()
        navigator.resizeColumnToContents(0)
        navigator.setMinimumHeight(300)
        for i in range(4):
            head.setSectionHidden(i, not sections.get(i, False))
        for i in section_sizes:
            if not sections.get(i, False):
                raise ValueError(f"Cannot set resize policy for section {i} if it's hidden")
            head.setSectionResizeMode(i, section_sizes[i])
        head.setStretchLastSection(False)
        head.resizeSection(0, 300)
        head.resizeSection(3, 200)

        self._filepath = ""
        layout = widgets.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(navigator)
        layout.addWidget(btns)

    def _select_file(self, i: core.QModelIndex):
        self.select_file(self._file_model.filePath(i))

    def _handle_file(self, sig: core.pyqtBoundSignal):
        if self._filepath != "":
            sig.emit(self._filepath)
            self.accept()

    def select_file(self, path: str):
        self._filepath = path


class FilePrompt(widgets.QWidget):
    """
    Special widget for creating a file dialog.

    Attributes
    ----------
    _file_path: widgets.QLineEdit
        The current path controller.
    _directory: FileDialog
        The file dialog to produce.
    _chooser: widgets.QPushButton
        The button to use to produce the file dialog.

    Parameters
    ----------
    *valid_extensions: str
        The valid file extensions to view.
    open_txt: str (default is "open")
        Open button text to send to the file dialog.
    save_txt: str (default is "save")
        Save button text to send to the file dialog.
    path: str (default is `FileDialog.BASE`)
        File path to send to the file dialog.
    context: str (default is "Choose File")
        The text of the dialog opening button.
    sections: dict[int, bool] (default is {0: True, 3: True})
        Section visibility to send to the file dialog.
    section_sizes: dict[int, widgets.QHeaderView.ResizeMode] (default is {0: ResizeToContents, 3: Fixed})
        Section sizes to send to the file dialog.
    """

    def __init__(self, *valid_extensions: str, open_txt="open", save_txt="save", path=FileDialog.BASE,
                 context="Choose File", sections: _dict[int, bool] = None,
                 section_sizes: _dict[int, widgets.QHeaderView.ResizeMode] = None, block=True):
        def _action(sig: core.pyqtBoundSignal) -> typing.Callable[[], None]:
            def _emit():
                txt = self._file_path.text()
                if any(txt.endswith(f".{ext}") for ext in valid_extensions):
                    self._directory.select_file(txt)
                    sig.emit(txt)

            return _emit

        super().__init__()
        layout = widgets.QHBoxLayout()
        self._directory = FileDialog(
            self, *map(lambda s: f"*.{s}", valid_extensions), open_txt=open_txt,
            save_txt=save_txt, path=path, sections=sections or {0: True, 3: True},
            section_sizes=section_sizes or {0: widgets.QHeaderView.ResizeToContents, 3: widgets.QHeaderView.Fixed}
        )
        dialog_function = self._directory.exec if block else self._directory.open
        bslsh = "\\"
        self._file_path = widgets.QLineEdit(f"{path.replace(bslsh, '/')}/")
        self._chooser = widgets.QPushButton(context)
        self._chooser.clicked.connect(lambda: dialog_function())
        o_action = widgets.QPushButton(f"Run ({open_txt})")
        s_action = widgets.QPushButton(f"Run ({save_txt})")
        o_action.clicked.connect(_action(self._directory.openFile))
        s_action.clicked.connect(_action(self._directory.saveFile))
        layout.addWidget(self._file_path)
        layout.addWidget(self._chooser)
        layout.addWidget(o_action)
        layout.addWidget(s_action)
        self.setLayout(layout)

    def dialog(self) -> FileDialog:
        """
        Getter for the file dialog to open.

        Returns
        -------
        FileDialog
            The file dialog that will be opened.
        """
        return self._directory

    def file_path(self) -> widgets.QLineEdit:
        """
        Getter for the file path entry.

        Returns
        -------
        widgets.QLineEdit
            The entry for the file path.
        """
        return self._file_path


class Canvas(widgets.QWidget):
    """
    Widget for displaying Images onto itself.

    A canvas can be used in a context manager to make several changes to the image (by mutation) and then automatically
    update the display. This is the only way to directly access and mutate the image stored.

    Signals
    -------
    mouseMoved: gui.QMouseEvent
        Emitted when the mouse is moved to allow for alternative handlers. Contains the event itself.
    mousePressed: gui.QMouseEvent
        Emitted when the mouse is clicked to allow for alternative handlers. Contains the event itself.
    mouseReleased: gui.QMouseEvent
        Emitted when the mouse is released to allow for alternative handlers. Contains the event itself.

    Attributes
    ----------
    _pixels: gui.QPixmap
        The pixel map to display.
    _size: tuple[int, int]
        The size of the widget, and the expected size of all images.
    _image: RGBImage | None
        The image currently being displayed.
    _data: np.ndarray | None
        The data array in a special QT acceptable format.
    """

    mouseMoved = core.pyqtSignal(gui.QMouseEvent)
    mousePressed = core.pyqtSignal(gui.QMouseEvent)
    mouseReleased = core.pyqtSignal(gui.QMouseEvent)

    @property
    def displaying(self) -> bool:
        """
        Public access to the display status.

        Returns
        -------
        bool
            Whether the widget has an image.
        """
        return self._image is not None

    @property
    def image_size(self) -> _tuple[int, int]:
        """
        Public access to the expected size of the images.

        Returns
        -------
        tuple[int, int]
            The expected size of the images. This is also the size of the widget.
        """
        return self._size

    def __init__(self, size: _tuple[int, int], *, live_mouse=True):
        self._pixels = gui.QPixmap(*size)
        self._size = size
        self._image: typing.Optional[RGBImage] = None
        self._data: typing.Optional[np.ndarray] = None
        super().__init__()
        self.setFixedSize(*size)
        self.setMouseTracking(live_mouse)

    def __enter__(self) -> RGBImage:
        if self._image is None:
            raise ValueError("Canvas has no current image")
        return self._image

    def __exit__(self, exc_type: typing.Optional[typing.Type[Exception]], exc_val: typing.Optional[Exception],
                 exc_tb) -> bool:
        if exc_type is None:
            self.update()
        return False

    def resize_canvas(self, new: _tuple[int, int]):
        """
        Resize the canvas to a new size. This will clear it.

        Parameters
        ----------
        new: tuple[int, int]
            The new canvas size.
        """
        self._size = new
        self.setFixedSize(*new)
        self.clear()

    def mouseMoveEvent(self, a0: gui.QMouseEvent):
        """
        Allows for alternative handlers to handle movement of the mouse.

        Parameters
        ----------
        a0: gui.QPaintEvent
            The event that triggered this callback.
        """
        self.mouseMoved.emit(a0)

    def mousePressEvent(self, a0):
        """
        Allows for alternative handlers to handle mouse clicks.

        Parameters
        ----------
        a0: gui.QPaintEvent
            The event that triggered this callback.
        """
        self.mousePressed.emit(a0)

    def mouseReleaseEvent(self, a0):
        """
        Allows for alternative handlers to handle releasing mouse clicks.

        Parameters
        ----------
        a0: gui.QPaintEvent
            The event that triggered this callback.
        """
        self.mouseReleased.emit(a0)

    def paintEvent(self, a0: gui.QPaintEvent):
        """
        Paints the image onto the widget.

        Parameters
        ----------
        a0: gui.QPaintEvent
            The event that triggered this callback.
        """
        painter = gui.QPainter(self)
        painter.drawPixmap(self.rect(), self._pixels)

    def draw(self, image: RGBImage):
        """
        Draws a new image onto the widget.

        Parameters
        ----------
        image: RGBImage
            The image to be drawn.
        """
        if image.size != self._size:
            raise ValueError(f"Expected image size and widget size to match! (got {image.size} and {self._size})")
        self._image = image
        self.update()

    def update(self):
        """
        Updates the widget's display. This is called internally whenever the image is changed.
        """
        if self._image is not None:
            data = self._image.get_channels(RGBOrder.RGB).astype(np.uint32)
            w, h = self._image.size
            self._data = (255 << 24 | data[:, :, 0] << 16 | data[:, :, 1] << 8 | data[:, :, 2]).flatten()
            # noinspection PyTypeChecker
            qt_image = gui.QImage(self._data, w, h, gui.QImage.Format_RGB32)
            self._pixels = gui.QPixmap.fromImage(qt_image)
        super().update()

    def histogram(self, image: GreyImage, groups=15, colour=RGB(0, 0, 255)) -> _tuple[np.ndarray, np.ndarray]:
        """
        Calculates the histogram of the specified image.

        This histogram will always plot on a log scale.

        Parameters
        ----------
        image: GreyImage
            The greyscale image to calculate the histogram of. Note that full-depth histograms are not supported.
        groups: int
            The number of bins to use in the histogram (default is 15).
        colour: RGB
            The colour to draw the histogram outline in. The fill is always the first colour in the group.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            The bottom left x position of each rectangle, and the greyscale colours used.
        """
        step = 255 // groups
        data = image.image()
        w, h = image.size
        blank = RGBImage.blank(image.size)
        greys = np.arange(0, 256, step, dtype=np.uint8)
        counts, _ = np.histogram(data, bins=greys)
        counts[np.nonzero(counts)] = np.log(counts[np.nonzero(counts)])
        largest = np.max(counts)
        heights = ((counts / largest) * (h - 1)).astype(np.int_)
        adj_step = w // counts.size
        rect_width = max(adj_step - 2, 2)
        for grey, x, height in zip(greys, (xs := np.arange(0, w - rect_width, rect_width)), heights):
            if height == 0:
                continue
            blank.drawing.rect.from_size((x, w - 1, AABBCorner.BOTTOM_LEFT), (rect_width, height), colour,
                                         fill=Grey(grey))
        blank.drawing.line((0, h - 1), (w - 1, h - 1), colour)
        self.draw(blank)
        return xs, greys

    def clear(self):
        """
        Wipe the image from the canvas.
        """
        self._image = self._data = None
        self._pixels = gui.QPixmap(*self._size)
        self.update()


class Subplot(widgets.QWidget):

    def __init__(self, rows: int, cols: int, *sizes: _tuple[int, int], title: str = None):
        super().__init__()
        if rows == cols == 1:
            raise ValueError("Cannot have a subplot with 1 canvas")
        elif rows < 1 or cols < 1:
            raise ValueError("Must have a natural number of rows and columns")
        layout = widgets.QGridLayout()
        self._m = cols
        if len(sizes) != rows * cols:
            raise ValueError(f"Must supply exactly {rows * cols} canvas sizes")
        self._plots = tuple(Canvas(s) for s in sizes)
        self._label = widgets.QLabel(title or "Subplot")
        layout.addWidget(self._label, 0, 0)
        for i, cnv in enumerate(self._plots):
            r, c = np.unravel_index(i, (rows, cols))
            layout.addWidget(cnv, r + 1, c + 1)
        self.setLayout(layout)

    def __getitem__(self, item: _tuple[int, int]) -> Canvas:
        r, c = item
        i = self._m * r + c
        return self._plots[i]

    def __iter__(self) -> typing.Iterator[Canvas]:
        yield from self._plots

    def title(self, add: str, sep=" "):
        self._label.setText(f"{self._label.text()}{sep}{add}")
