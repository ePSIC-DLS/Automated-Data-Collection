"""
Module to provide the various preprocessing of the image.
"""
import typing

import cv2
from PyQt5 import QtWidgets as widgets, Qt as core

from modular_qt import errors, utils as scans
from . import base
from . import extra_widgets
from .base import utils, sq
from ._scan import ScanPage


class Order(utils.AdvancedSettingWindow):
    """
    Subclass to represent the order of preprocessing steps and their specific arguments.

    :var _buttons list[OrderedButton]: The controls for the order.
    :var _names list[str]: The names of each operation.
    :var _boxes list[list[PyQt5.QWidgets.Widget]]: The controls for the arguments of the operations.
    """

    @property
    def processes(self) -> list[extra_widgets.OrderedButton]:
        """
        Public access to the order of processes.

        :return: The controls for the order.
        """
        return self._buttons.copy()

    def __init__(self, *commands: tuple[str, typing.Callable[[bool], None], list[widgets.QWidget]]):
        super().__init__()
        group = extra_widgets.OrderedButtonGroup(len(commands))
        self._buttons = [extra_widgets.OrderedButton(name, command, group) for name, command, _ in commands]
        self._names, _, self._boxes = zip(*commands)
        longest = max(map(len, self._names))
        for btn in self._buttons:
            btn.pad_name(longest)
        for i, (order, widget_list) in enumerate(zip(self._buttons, self._boxes)):
            self._layout.addWidget(order, i, 0)
            for j, w in enumerate(widget_list, 1):
                self._layout.addWidget(w, i, j)
        self._buttons[self._names.index("gss_blur")].force(1)
        self._buttons[self._names.index("threshold")].force(2)

    def widgets(self) -> dict[str, widgets.QWidget]:
        names = {}
        for name, wid_list in zip(self._names, self._boxes):
            for i, wid in enumerate(wid_list):
                names[f"{name}_{i}"] = wid
        return names


class PreprocessPage(base.DrawingPage, base.SettingsPage):
    """
    Concrete subclass to represent the page for all preprocessing steps.

    :cvar KERNEL tuple[int, int]: The range of size values for all operations.
    :cvar SD tuple[int, int]: The range of sigma values for 'Gaussian' blurring.
    :cvar MORPH tuple[int, int]: The range of values for binary processing (scale and epochs).
    :cvar SHAPES tuple[str, str, str]: The different kernel shapes for binary processing.

    :var _scanner ScanPage: The previous step in the pipeline.
    :var _min FixedSpinBox: The minimum thresholding value.
    :var _max FixedSpinBox: The maximum thresholding value.
    :var _invert PyQt5.QWidgets.QCheckBox: Whether to invert the result.
    """
    KERNEL = (1, 15)
    SD = (-10, 10)
    MORPH = (1, 10)
    SHAPES = ("Rect", "Cross", "Ellipse")

    @property
    def min(self) -> int:
        """
        Public access to the minima.

        :return: The minimum thresholding value.
        """
        return self._min.value()

    @min.setter
    def min(self, value: int):
        """
        Public access to modifying the minima.

        :param value: The new minimum thresholding.
        """
        self._min.setValue(value)

    @property
    def max(self) -> int:
        """
        Public access to the maxima.

        :return: The maximum thresholding value.
        """
        return self._max.value()

    @max.setter
    def max(self, value: int):
        """
        Public access to modifying the maxima.

        :param value: The new maximum thresholding.
        """
        self._max.setValue(value)

    def __init__(self, size: int, prev: ScanPage):
        # noinspection PyTypeChecker
        def _produce_order() -> Order:
            def _choices() -> widgets.QComboBox:
                choices = widgets.QComboBox()
                choices.addItems(self.SHAPES)
                return choices

            return Order(
                ("blur", self.blur, [extra_widgets.FixedSpinBox.from_range(self.KERNEL, 2, value=5),
                                     extra_widgets.FixedSpinBox.from_range(self.KERNEL, 2, value=5)]),
                ("gss_blur", self.gss_blur, [extra_widgets.FixedSpinBox.from_range(self.KERNEL, 2, value=5),
                                             extra_widgets.FixedSpinBox.from_range(self.KERNEL, 2, value=5),
                                             extra_widgets.FixedSpinBox.from_range(self.SD, 1, value=0),
                                             extra_widgets.FixedSpinBox.from_range(self.SD, 1, value=0)]),
                ("sharpen", self.sharpen, [extra_widgets.FixedSpinBox.from_range(self.KERNEL, 2, value=5),
                                           extra_widgets.FixedSpinBox.from_range(self.SD, 1, value=1),
                                           extra_widgets.FixedSpinBox.from_range(self.SD, 1, value=0)]),
                ("median", self.median, [extra_widgets.FixedSpinBox.from_range(self.KERNEL, 2, value=5)]),
                ("edge", self.edge, [extra_widgets.FixedSpinBox.from_range(self.KERNEL, 2, value=5)]),
                ("threshold", self.threshold, []),
                ("open", self.open, [extra_widgets.FixedSpinBox.from_range(self.KERNEL, 2, value=5),
                                     extra_widgets.FixedSpinBox.from_range(self.KERNEL, 2, value=5),
                                     extra_widgets.FixedSpinBox.from_range(self.MORPH, 1),
                                     extra_widgets.FixedSpinBox.from_range(self.MORPH, 1),
                                     _choices()]),
                ("close", self.close, [extra_widgets.FixedSpinBox.from_range(self.KERNEL, 2, value=5),
                                       extra_widgets.FixedSpinBox.from_range(self.KERNEL, 2, value=5),
                                       extra_widgets.FixedSpinBox.from_range(self.MORPH, 1),
                                       extra_widgets.FixedSpinBox.from_range(self.MORPH, 1),
                                       _choices()]),
                ("gradient", self.gradient, [extra_widgets.FixedSpinBox.from_range(self.KERNEL, 2, value=5),
                                             extra_widgets.FixedSpinBox.from_range(self.KERNEL, 2, value=5),
                                             extra_widgets.FixedSpinBox.from_range(self.MORPH, 1),
                                             extra_widgets.FixedSpinBox.from_range(self.MORPH, 1),
                                             _choices()]),
                ("i_gradient", self.i_gradient, [extra_widgets.FixedSpinBox.from_range(self.KERNEL, 2, value=5),
                                                 extra_widgets.FixedSpinBox.from_range(self.KERNEL, 2, value=5),
                                                 extra_widgets.FixedSpinBox.from_range(self.MORPH, 1),
                                                 extra_widgets.FixedSpinBox.from_range(self.MORPH, 1),
                                                 _choices()]),
                ("e_gradient", self.e_gradient, [extra_widgets.FixedSpinBox.from_range(self.KERNEL, 2, value=5),
                                                 extra_widgets.FixedSpinBox.from_range(self.KERNEL, 2, value=5),
                                                 extra_widgets.FixedSpinBox.from_range(self.MORPH, 1),
                                                 extra_widgets.FixedSpinBox.from_range(self.MORPH, 1),
                                                 _choices()]),
            )

        super().__init__(size)
        super(base.DrawingPage, self).__init__(utils.Settings.REGULAR | utils.Settings.ADVANCED, _produce_order)
        self._scanner = prev
        self._min = extra_widgets.FixedSpinBox((0, 255, 1), "Minima")
        self._max = extra_widgets.FixedSpinBox((0, 255, 1), "Maxima", value=255)
        self._min.valueChanged.connect(lambda v: self._max.setMinimum(v + 1))
        self._max.valueChanged.connect(lambda v: self._min.setMaximum(v - 1))
        self._invert = widgets.QCheckBox("Invert?")
        self._reg_col.addWidget(self._min)
        self._reg_col.addWidget(self._max)
        self._reg_col.addWidget(self._invert)

    def compile(self) -> str:
        items = []
        for process in sorted(self._window.processes, key=extra_widgets.OrderedButton.get_num):
            if process.get_num() == 0:
                continue
            command_name = process.command()
            if command_name == "threshold":
                items.append("threshold")
                continue
            elif command_name == "edge":
                items.append(f"edge @ {self.get_setting('edge_0')}")
                continue
            elif command_name == "median":
                items.append(f"median({self.get_setting('median_0')})")
                continue
            args = (self.get_setting(f'{command_name}_0'), self.get_setting(f'{command_name}_1'))
            if command_name == "blur":
                items.append(f"{command_name}{args}")
            elif command_name == "gss_blur":
                gss_args = (self.get_setting("gss_blur_2"), self.get_setting("gss_blur_3"))
                items.append(f"gss_blur{args + gss_args}")
            elif command_name == "sharpen":
                delta = (self.get_setting('sharpen_2'),)
                items.append(f"sharpen{args + delta}")
            elif command_name in ("open", "close", "gradient", "i_gradient", "e_gradient"):
                bin_args = list(self.get_setting(f"{command_name}_{i}") for i in range(2, 5))
                bin_args[-1] = bin_args[-1].lower()
                items.append(f"{command_name}({', '.join(map(str, args))}, {', '.join(map(str, bin_args))})")
            else:
                print(f"{command_name!r} unhandled")
        return "\n".join(items)

    def trace(self, minima: widgets.QLineEdit, maxima: widgets.QLineEdit):
        """
        Allow the modification of the controls to affect an external entry.

        :param minima: The entry linked to the minima threshold value.
        :param maxima: The entry linked to the maxima threshold value.
        """

        def _formatter(w: widgets.QLineEdit, spec: str) -> typing.Callable[[int], None]:
            def _inner(new: int):
                w.setText(f"{spec}: {new}")

            return _inner

        self._min.valueChanged.connect(_formatter(minima, "Minima"))
        self._max.valueChanged.connect(_formatter(maxima, "Maxima"))

    def _get_image(self):
        self._curr = self._scanner.get_original().copy()
        if self._curr is None:
            raise errors.StagingError("Preprocessing", "Scan")
        self._original = self._curr.copy()

    @base.DrawingPage.lock
    def run(self, btn_state: bool):
        """
        Performs preprocessing by invoking the separate stages in the order required.

        To change the order, change the advanced settings.
        :param btn_state: The state of the button that caused this callback
        """
        self._curr = None
        for process in sorted(self._window.processes, key=extra_widgets.OrderedButton.get_num):
            if process.get_num() == 0:
                continue
            process.invoke(btn_state)

    @base.DrawingPage.lock
    def threshold(self, btn_state: bool):
        """
        Performs binary thresholding with a minima and a maxima.

        Inside the boundary can be white or black, depending on inversion state.
        :param btn_state: The state of the button that caused this callback.
        """
        self.triggered.emit(self.threshold)
        self._get_image()
        in_bound = (sq.ThresholdMode.GT_0_LTE_MAX
                    if self._invert.checkState() == core.Qt.Unchecked else
                    sq.ThresholdMode.GT_MAX_LTE_0)
        self._curr.transform.region_threshold((self._min.value(), self._max.value()), in_bound, maximum=255)
        self._canvas.image(self._curr.get_channeled_image(sq.RGBOrder.RGB) / 255)

    @base.DrawingPage.lock
    def edge(self, btn_state: bool):
        """
        Performs Canny edge detection on the image.

        :param btn_state: The state of the button that caused this callback.
        """
        self.triggered.emit(self.edge)
        self._get_image()
        low, high = self._min.value(), self._max.value()
        size = int(scans.map_to_range(self.get_setting("edge_0"), self.KERNEL, self.KERNEL))
        self._curr = self._curr.edge_detection(low, high, size)
        if self._invert.checkState() == core.Qt.Unchecked:
            self._curr = ~self._curr
        self._canvas.image(self._curr.get_channeled_image(sq.RGBOrder.RGB) / 255)

    @base.DrawingPage.lock
    def blur(self, btn_state: bool):
        """
        Method to perform standard blurring on the image.

        It is recommended to do this before thresholding or edge detection.
        """
        self.triggered.emit(self.blur)
        self._get_image()
        s1 = scans.map_to_range(self.get_setting("blur_0"), self.KERNEL, self.KERNEL)
        s2 = scans.map_to_range(self.get_setting("blur_1"), self.KERNEL, self.KERNEL)
        self._curr.blur((int(s1), int(s2)))
        self._canvas.image(self._curr.get_channeled_image(sq.RGBOrder.RGB) / 255)

    @base.DrawingPage.lock
    def gss_blur(self, btn_state: bool):
        """
        Method to perform Gaussian blurring on the image.

        It is recommended to do this before thresholding or edge detection.
        """
        self.triggered.emit(self.gss_blur)
        self._get_image()
        s1 = scans.map_to_range(self.get_setting("gss_blur_0"), self.KERNEL, self.KERNEL)
        s2 = scans.map_to_range(self.get_setting("gss_blur_1"), self.KERNEL, self.KERNEL)
        sd1 = scans.map_to_range(self.get_setting("gss_blur_2"), self.SD, self.SD)
        sd2 = scans.map_to_range(self.get_setting("gss_blur_3"), self.SD, self.SD)
        self._curr.gaussian_blur((int(s1), int(s2)), (int(sd1), int(sd2)))
        self._canvas.image(self._curr.get_channeled_image(sq.RGBOrder.RGB) / 255)

    @base.DrawingPage.lock
    def sharpen(self, btn_state: bool):
        """
        Method to perform sharpening on the image.

        It is recommended to do this before thresholding or edge detection.
        """
        self.triggered.emit(self.sharpen)
        self._get_image()
        size = scans.map_to_range(self.get_setting("sharpen_0"), self.KERNEL, self.KERNEL)
        factor = scans.map_to_range(self.get_setting("sharpen_1"), self.SD, self.SD)
        term = scans.map_to_range(self.get_setting("sharpen_2"), self.SD, self.SD)
        self._curr.sharpen(int(size), int(factor), int(term))
        self._canvas.image(self._curr.get_channeled_image(sq.RGBOrder.RGB) / 255)

    @base.DrawingPage.lock
    def median(self, btn_state: bool):
        """
        Method to perform median blurring on the image.

        It is recommended to do this before thresholding or edge detection.
        """
        self.triggered.emit(self.median)
        self._get_image()
        size = scans.map_to_range(self.get_setting("median_0"), self.KERNEL, self.KERNEL)
        self._curr.median_blur(int(size))
        self._canvas.image(self._curr.get_channeled_image(sq.RGBOrder.RGB) / 255)

    @base.DrawingPage.lock
    def open(self, btn_state: bool):
        """
        Method to perform the binary preprocessing 'open' on the image.

        It is recommended to do this after thresholding or edge detection.
        """
        self.triggered.emit(self.open)
        self._get_image()
        self._handle_morph(sq.Transform.OPEN, "open")

    @base.DrawingPage.lock
    def close(self, btn_state: bool):
        """
        Method to perform the binary preprocessing 'close' on the image.

        It is recommended to do this after thresholding or edge detection.
        """
        self.triggered.emit(self.close)
        self._get_image()
        self._handle_morph(sq.Transform.CLOSE, "close")

    @base.DrawingPage.lock
    def gradient(self, btn_state: bool):
        """
        Method to perform the binary preprocessing 'gradient' on the image.

        It is recommended to do this after thresholding or edge detection.
        """
        self.triggered.emit(self.gradient)
        self._get_image()
        self._handle_morph(sq.Transform.GRADIENT, "gradient")

    @base.DrawingPage.lock
    def i_gradient(self, btn_state: bool):
        """
        Method to perform the binary preprocessing 'internal gradient' on the image.

        It is recommended to do this after thresholding or edge detection.
        """
        self.triggered.emit(self.i_gradient)
        self._get_image()
        self._handle_morph(sq.Transform.WHITEHAT, "i_gradient")

    @base.DrawingPage.lock
    def e_gradient(self, btn_state: bool):
        """
        Method to perform the binary preprocessing 'external gradient' on the image.

        It is recommended to do this after thresholding or edge detection.
        """
        self.triggered.emit(self.e_gradient)
        self._get_image()
        self._handle_morph(sq.Transform.BLACKHAT, "e_gradient")

    def _handle_morph(self, mode: sq.Transform, src: str):
        num_iterations = scans.map_to_range(self.get_setting(f"{src}_2"), self.MORPH, self.MORPH)
        scale = scans.map_to_range(self.get_setting(f"{src}_3"), self.MORPH, self.MORPH)
        shape = self.get_setting(f"{src}_4")
        s1 = scans.map_to_range(self.get_setting(f"{src}_0"), self.KERNEL, self.KERNEL)
        s2 = scans.map_to_range(self.get_setting(f"{src}_1"), self.KERNEL, self.KERNEL)
        if shape == "Rect":
            i_shape = cv2.MORPH_RECT
        elif shape == "Cross":
            i_shape = cv2.MORPH_CROSS
        else:
            i_shape = cv2.MORPH_ELLIPSE
        self._curr.transform.morphological_transform(mode, (int(s1), int(s2)), i_shape, k_scale=int(scale),
                                                     iterations=int(num_iterations))
        self._canvas.image(self._curr.get_channeled_image(sq.RGBOrder.RGB) / 255)
