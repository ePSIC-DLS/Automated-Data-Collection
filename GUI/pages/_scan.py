"""
Module to represent the initial survey image page.
"""
import operator

import cv2
from PyQt5 import Qt as events
from PyQt5.QtCore import Qt as enums

from modular_qt import utils as scans, errors, microscope
from . import base, extra_widgets, __pyjem__
from .base import utils, widgets, sq, core


class ScanPage(base.DrawingPage, base.SettingsPage):
    """
    Concrete subclass to represent the initial scan page (survey image).

    :var _regions dict[tuple[int, int], tuple[ScanSite, Marker]]: The regions clicked.
    :var _pos PyQt5.QtWidgets.QLabel: The position of the cursor.
    :var _markers list[Marker]: The list of markers.
    :var _square_colour Colour: The colour to draw the squares.
    """

    @property
    def regions(self) -> list[scans.ScanSite]:
        """
        Public access to the clicked regions.

        :return: All clicked regions, without the markers.
        """
        return list(map(operator.itemgetter(0), self._regions.values()))

    def __init__(self, size: int, *, colour: sq.Colour):
        super().__init__(size)
        super(base.DrawingPage, self).__init__(utils.Settings.REGULAR)
        super(base.SettingsPage, self).__init__()
        self._regions: dict[tuple[int, int], tuple[scans.ScanSite, extra_widgets.Marker]] = {}
        self._pos = widgets.QLabel(f"<00, 00>")
        self._markers: list[extra_widgets.Marker] = []
        self._reg_col.addWidget(self._pos)
        self._square_colour = colour
        self._link: microscope.Microscope = microscope.Microscope.get_instance()
        self._scan_size = -1

    def compile(self) -> str:
        return ""

    @base.DrawingPage.lock
    def run(self, btn_state: bool):
        """
        Performs a scan of the image on the microscope.

        :param btn_state: The state of the button that caused this run.
        """
        self.triggered.emit(self.run)
        if __pyjem__:
            self._link["detector.scan_mode"] = microscope.ScanMode.FULL
            self._link["detector.scan_size"] = self._canvas.figsize
            with self._link.blanked(False):
                with self._link.detector(insertion=True):
                    self._curr = self._link.detector_controller.scan()
        else:
            src = cv2.imread("../PytchoGUI/assets/img_3.bmp", cv2.IMREAD_GRAYSCALE)
            self._curr = sq.Image(src, colour=sq.CMode.GREY)
        self._original = self._curr.copy()
        self._canvas.image(self._curr.get_channeled_image() / 255)

    def _handle_click(self, event: events.QMouseEvent, drag: bool):
        button = event.button()
        pos = event.pos()
        self._pos.setText(f"<{pos.x():02}, {pos.y():02}>")
        if drag:
            btns = event.buttons()
            c1 = btns & enums.LeftButton
        else:
            c1 = button
        if c1 == enums.LeftButton:
            if self._curr is None:
                raise errors.StagingError("Add Additional Zones", "Scanning")
            self._add_square(pos.x(), pos.y())
        else:
            return
        self._canvas.image(self._curr.get_channeled_image(sq.RGBOrder.RGB) / 255)

    def _add_square(self, x: int, y: int):
        if (x, y) in self._regions:
            return
        size = self.pitch_size()
        colour = self._square_colour.all(sq.RGBOrder.BGR)
        img = self._curr.get_raw()
        region = scans.ScanSite.from_centre((x, y), size, size, self._canvas.figsize)
        left, top = region.extract_point(scans.HSide.LEFT | scans.VSide.TOP)
        right, bottom = region.extract_point(scans.HSide.RIGHT | scans.VSide.BOTTOM)
        if left < 0 or top < 0 or right >= self._canvas.figsize or bottom >= self._canvas.figsize:
            return
        img[top:bottom, (left, right)] = colour
        img[(top, bottom), left:right] = colour
        marker = extra_widgets.Marker(self, (x, y), self._rem_square)
        self._regions[x, y] = (region, marker)
        self._markers.append(marker)
        self._reg_col.addWidget(marker)

    def _rem_square(self, x: int, y: int):
        if (x, y) not in self._regions:
            return
        img = self._curr.get_raw()
        orig = self._original.get_raw()
        region, marker = self._regions.pop((x, y))
        left, top = region.extract_point(scans.HSide.LEFT | scans.VSide.TOP)
        right, bottom = region.extract_point(scans.HSide.RIGHT | scans.VSide.BOTTOM)
        img[top:bottom, (left, right)] = orig[top:bottom, (left, right)]
        img[(top, bottom), left:right] = orig[(top, bottom), left:right]
        self._markers.remove(marker)
        marker.hide()
        self._canvas.image(img[:, :, ::-1] / 255)

    @base.DrawingPage.lock
    def mouseMoveEvent(self, a0: events.QMouseEvent):
        super().mouseMoveEvent(a0)
        self._handle_click(a0, True)

    @base.DrawingPage.lock
    def mouseReleaseEvent(self, a0: events.QMouseEvent):
        """
        Process the mouse being clicked on the widget.
        :param a0: The event that caused this callback.
        """
        self._handle_click(a0, False)

    def pitch_size(self) -> int:
        """
        Find pitch size value based on image size and scan size.

        :return: The size of each square to mark on the board.
        """
        return self._scan_size // (4096 // self._canvas.figsize)

    @core.pyqtSlot(int)
    def update_pitch(self, new: int):
        """
        Update the scan size (therefore updating the pitch size)

        :param new: The new scan size value.
        """
        self._scan_size = new
