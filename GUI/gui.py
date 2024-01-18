"""
Module to create the GUI to ease Pytchography.

GUI can scan an image from the microscope, threshold it at certain values, perform clustering, and automatically set up
scan regions from clusters, or additional regions from the scanned image (and then scan these regions)

Has settings to change epsilon (in clustering), min samples (in clustering), and threshold values (in thresholding)
"""

from __future__ import annotations

import collections
import functools
import tkinter as tk
import typing
from tkinter import messagebox as mtk
from tkinter import ttk

import cv2
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle as RectPatch
import h5py
# from skimage.transform import AffineTransform, warp
from PyJEM import detector
from sklearn.cluster import DBSCAN

import custom_tk as ctk
import squares as sq
import utils
from microscope_params import MicroscopeParameters
from squares.transforms import Morphs

import time

import os
start_dir = os.getcwd()
md=r'C:\Users\Merlin\Desktop\microscope_control_private\merlin-tcp-connection-master_python3'#'C:/code/merlin-tcp-connection-master_python3'
os.chdir(md)
from connection.MERLIN_connection import *
# md='C:/code/merlin-tcp-connection-master_python3'
os.chdir(start_dir)

from PyJEM import TEM3


"""
TODO:
    
    Change scan button to sample
    Calibration per save (DONE)
    Save all images on grid scan
    Subfolder per scan (and image)
    Select all clusters
    Autofocus routine every X scans
    Drift correction on X scans
    Automate settings recall
    Add stage movement (+ automation)
    Fix emission
    Send co-ordinates of each scan to file (one file per cluster)
    Migrate to QT
"""


class Program:
    """
    Wrapper class for all GUI work, to keep it stateful

    :var _window tkinter.Tk: The main window of the program.
    :var _size int: The size of each image taken.
    :var _grid_colour Colour: The colour of the lines within the image.
    :var _scanning_colour Colour: The colour of the region which is currently being scanned.
    :var _original_scan Image | None: The original scanned image.
    :var _c1_im Image | None: The image drawn on _c1.
    :var _c2_im Image | None: The image drawn on _c2.
    :var _c3_im Image | None: The image drawn on _c3.
    :var _scan_im Image | None: The image To scan.
    :var _clicked1 list[tuple[int, int]]: The co-ordinates clicked on _c1.
    :var _clicked2 list[tuple[int, int, int]]: The clusters clicked on _c2.
    :var _processed_images dict[tuple[int, int, int], Image]: The images drawn on _c4, mapped by colour.
    :var _areas dict[tuple[int, int, int], tuple[Image, numpy.ndarray, numpy.ndarray, int]]: The scan regions from _c4.
    :var _extras dict[tuple[int, int], tuple[Image, numpy.ndarray, numpy.ndarray]]: The scan regions from _c1.
    :var _elapsed float: The time elapsed since the last drift correction.

    :var _region_index tkinter.IntVar: The index of the current region being processed.
    :var _scan_index tkinter.IntVar: The index of the current region being scanned.
    :var _keep_going tkinter.IntVar: Flag to decide if the program is running.
    :var _searching tkinter.IntVar: Flag to decide if the program is running a grid scan.
    :var _gridding tkinter.IntVar: Flag to decide if the program is outlining a region.
    :var _thresh_low tkinter.IntVar: The minimum thresholding value.
    :var _thresh_high tkinter.IntVar: The maximum thresholding value.
    :var _clust1 tkinter.DoubleVar: The epsilon value.
    :var _clust2 tkinter.IntVar: The minimum number of samples.
    :var _threshold_mode tkinter.IntVar: Flag to decide if the thresholding needs to be inverted.
    :var _microscope_settings dict[str, tkinter.DoubleVar]: The settings from the microscope to load.

    :var _closed tkinter.IntVar: A flag for whether the advanced settings window has been closed.
    :var _gap tkinter.IntVar: The size of each square.
    :var _spacing tkinter.IntVar: The amount of overlap between each square.
    :var _cluster_power tkinter.IntVar: The power to use in Minkowski clustering.
    :var _cluster_algorithm tkinter.StringVar: The distance metric to use in clustering.
    :var _square_mode tkinter.IntVar: A flag for whether the Euclidean distances are squared.
    :var _preprocessing tkinter.StringVar: The type of preprocessing to perform.
    :var _kernel tkinter.IntVar: The size of the preprocessing kernel.
    :var _blur tkinter.IntVar: The width of the Gaussian or blurring kernel.
    :var _gaussian tuple[tkinter.IntVar, tkinter.IntVar]: The standard deviation to use in gaussian blurring.
    :var _scale tkinter.IntVar: The scale of the preprocessing kernel.
    :var _shape tkinter.StringVar: The shape of the preprocessing kernel.
    :var _epochs tkinter.IntVar: The number of epochs to perform.
    :var _min_points tkinter.IntVar: The minimum number of pixels a scan region needs to have to be valid.
    :var _emission_threshold tkinter.IntVar: The lowest emission value before tip refresh.
    :var _drift_time tkinter.IntVar: The time between each drift check.

    :var _canvas_frame tkinter.ttk.Notebook: The region to have the canvases to draw the image.
    :var _l1 tkinter.Label: The colour of the cursor for the first image.
    :var _l2 tkinter.Label: The colour of the cursor for the second image.
    :var _l3 tkinter.Label: The colour of the cursor for the third image.
    :var _l4 tkinter.Label: The colour of the cursor for the fourth image.
    :var _c1 matplotlib.backends.backend_tkagg.FigureCanvasTkAgg: The canvas to draw the first image.
    :var _c2 matplotlib.backends.backend_tkagg.FigureCanvasTkAgg: The canvas to draw the second image.
    :var _c3 matplotlib.backends.backend_tkagg.FigureCanvasTkAgg: The canvas to draw the third image.
    :var _c4 matplotlib.backends.backend_tkagg.FigureCanvasTkAgg: The canvas to draw the fourth image.
    :var _ch matplotlib.backends.backend_tkagg.FigureCanvasTkAgg: The canvas to draw the histogram.

    :var _thresh_low_control Spinbox: The controller for the minimum threshold value.
    :var _thresh_high_control Spinbox: The controller for the maximum threshold value.
    :var _clust1_control Spinbox: The controller for the epsilon value.
    :var _clust2_control Spinbox: The controller for the minimum number of samples.
    :var _invert_control tkinter.CheckButton: Whether to invert the thresholding.
    :var _get_s_control tkinter.Button: Load microscope position and camera length into variables (for scan store).
    :var _save_s_control tkinter.Button: Save microscope variables into external files (for scan store).
    :var _recall_s_control tkinter.Button: Set microscope position and camera length from variables (for scan store).
    :var _get_d_control tkinter.Button: Load microscope position and camera length into variables (for data store).
    :var _save_d_control tkinter.Button: Save microscope variables into external files (for data store).
    :var _recall_d_control tkinter.Button: Set microscope position and camera length from variables (for data store).

    :var _scan_button tkinter.Button: The button to scan an image from the microscope.
    :var _threshold_button tkinter.Button: The button to threshold the scanned image.
    :var _cluster_button tkinter.Button: The button to cluster the threshold image.
    :var _grid_button tkinter.Button: The button to perform a grid tightening on the regions highlighted.
    :var _search_button tkinter.Button: The button to perform a grid search on the regions highlighted.
    :var _remove_button tkinter.Button: The button to remove the most recent grid.
    :var _stop_button tkinter.Button: The button to stop current operation.
    :var _adv_button tkinter.Button: The button to view advanced settings.

    :var _current_det PyJem.detector.Detector: The link to the microscope

    :var _c1_event str: The event bound to c1
    :var _c2_event str: The event bound to c2
    :var _c3_event str: The event bound to c3
    :var _c4_event str: The event bound to c4
    :var _ch_event_l str: The event bound to dragging the minima of the histogram
    :var _ch_event_h str: The event bound to dragging the maxima of the histogram
    """

    @property
    def _c4_im(self) -> typing.Optional[sq.Image]:
        """
        The current image drawn on _c4 (getter)
        :return: The image stored from the final click
        """
        if len(self._clicked2) == 0:
            return
        return self._processed_images[self._clicked2[-1]]

    @_c4_im.setter
    def _c4_im(self, value: sq.Image):
        """
        The current image drawn on _c4 (setter)
        :param value: The image to set the final click to
        """
        self._processed_images[self._clicked2[-1]] = value

    @property
    def _coloured_im(self) -> typing.Optional[sq.Image]:
        """
        The first image drawn on _c4
        :return: Either the image corresponding to the first click, or a template image if there are no clicks stored
        """
        if len(self._clicked2) == 0:
            return self._c3_im.to_colour(sq.CMODE.RGB, sq.Domain.R)
        return self._processed_images[self._clicked2[0]]
    
    @property
    def _line_done(self) -> bool:
        return self._scan_position[0] == self._cols

    def __init__(self, img_size: int, grid_colour: sq.Colour, marked_colour: sq.Colour, *,
                 max_samples=60, max_epsilon=60, max_clusters=100):
        """
        Sets up instance variables and performs tkinter packing and binding.
        :param img_size: The size of each image.
        :param grid_colour: The colour of the grid squares.
        :param marked_colour: The colour of the scanning region.
        :param max_samples: The maximum value that "min samples" can reach.
        :param max_epsilon: The maximum value that epsilon can reach.
        :param max_clusters: The maximum value that the advanced setting "Minimum Match" can reach.
        """
        self._window = tk.Tk()
        self._window.config(bg="#000000")

        # <editor-fold desc="Set up non-tk related instance variables">
        self._size = img_size
        self._grid_colour = grid_colour
        self._scanning_colour = marked_colour
        self._original_scan: typing.Optional[sq.Image] = None
        self._c1_im: typing.Optional[sq.Image] = None
        self._c2_im: typing.Optional[sq.Image] = None
        self._c3_im: typing.Optional[sq.Image] = None
        self._scan_im: typing.Optional[sq.Image] = None
        self._clicked2: list[tuple[int, int, int]] = []
        self._processed_images: dict[tuple[int, int, int], sq.Image] = {}
        self._areas: dict[tuple[int, int, int], tuple[sq.Image, np.ndarray, np.ndarray, int]] = {}
        self._extras: dict[tuple[int, int], tuple[np.ndarray, np.ndarray]] = {}
        self._elapsed = 0.0
        self._valid_regions: list[utils.ScanSite] = []
        self._colours: dict[int, int] = {}
        self._number_of_scans = 0
        self._scan_position = [0, 0]
        self._cols = 4
        self._rows = 4
        # </editor-fold>

        # <editor-fold desc="Create regular setting tk Variables">
        self._region_index = tk.IntVar(self._window, value=0)
        self._scan_index = tk.IntVar(self._window, value=0)
        self._keep_going = tk.IntVar(self._window, value=1)
        self._searching = tk.IntVar(self._window, value=0)
        self._gridding = tk.IntVar(self._window, value=0)
        self._scanning = tk.IntVar(self._window, value=0)
        self._thresh_low = tk.IntVar(self._window, value=0)
        self._thresh_high = tk.IntVar(self._window, value=255)
        self._clust1 = tk.DoubleVar(self._window, value=4.2)
        self._clust2 = tk.IntVar(self._window, value=50)
        self._threshold_mode = tk.IntVar(self._window, value=1)
        self._microscope_settings = MicroscopeParameters()
        self._automation = tk.IntVar(self._window, value=1)
        self._auto_thresh = tk.StringVar(self._window, value="Both")
        self._timing = tk.DoubleVar(self._window, value=0.0)
        self._do_4d = tk.IntVar(self._window, value=0)
        # </editor-fold>

        # <editor-fold desc="Create advanced setting tk Variables">
        self._closed = tk.IntVar(self._window)
        self._gap = tk.IntVar(self._window, value=32)
        self._spacing = tk.IntVar(self._window, value=1)
        self._cluster_power = tk.IntVar(self._window, value=3)
        self._cluster_algorithm = tk.StringVar(self._window, value="Euclidean")
        self._square_mode = tk.IntVar(self._window, value=0)
        self._preprocessing = tk.StringVar(self._window, value="Gaussian Blurring")
        self._kernel = tk.IntVar(self._window, value=5)
        self._blur = tk.IntVar(self._window, value=-1)
        self._gaussian = (tk.IntVar(self._window, value=0), tk.IntVar(self._window, value=0))
        self._scale = tk.IntVar(self._window, value=1)
        self._shape = tk.StringVar(self._window, value="Rect")
        self._epochs = tk.IntVar(self._window, value=1)
        self._min_points = tk.IntVar(self._window, value=30)
        self._emission_threshold = tk.IntVar(self._window, value=30)
        self._drift_time = tk.IntVar(self._window, value=120)
        self._padding = tk.IntVar(self._window, value=4)
        # </editor-fold>

        # <editor-fold desc="Create frames">
        self._canvas_frame = ttk.Notebook(self._window)
        self._canvas_frame.enable_traversal()
        variable_frame = tk.Frame(self._window, bg="#00FF00")
        action_frame = tk.Frame(self._window, bg="#0000FF")
        c1_frame = tk.Frame(self._canvas_frame)
        c2_frame = tk.Frame(self._canvas_frame)
        c3_frame = tk.Frame(self._canvas_frame)
        c4_frame = tk.Frame(self._canvas_frame)
        h_frame = tk.Frame(self._canvas_frame, bg="#FF0000")
        # </editor-fold>

        # <editor-fold desc="Create colour labels">
        self._l1 = tk.Label(c1_frame, font=("Consolas", 10), bg=str(sq.Colour.from_colour(sq.Colours.YELLOW)),
                            text="(000,000,000)")
        self._l2 = tk.Label(c2_frame, font=("Consolas", 10), bg=str(sq.Colour.from_colour(sq.Colours.YELLOW)),
                            text="(000,000,000)")
        self._l3 = tk.Label(c3_frame, font=("Consolas", 10), bg=str(sq.Colour.from_colour(sq.Colours.YELLOW)),
                            text="(000,000,000)")
        self._l4 = tk.Label(c4_frame, font=("Consolas", 10), bg=str(sq.Colour.from_colour(sq.Colours.YELLOW)),
                            text="(000,000,000)")
        # </editor-fold>

        # <editor-fold desc="Create canvases">
        blank_figure = plt.figure(-1, (self._size, self._size), 1)
        self._c1 = FigureCanvasTkAgg(blank_figure, c1_frame)
        self._c2 = FigureCanvasTkAgg(blank_figure, c2_frame)
        self._c3 = FigureCanvasTkAgg(blank_figure, c3_frame)
        self._c4 = FigureCanvasTkAgg(blank_figure, c4_frame)
        self._ch = FigureCanvasTkAgg(blank_figure, h_frame)
        # </editor-fold>

        # <editor-fold desc="Create controls">
        thresh_low_label = tk.Label(variable_frame, text="Minimum Threshold", font=("Consolas", 9))
        self._thresh_low_control = ctk.Spinbox(variable_frame, increment=1, values=range(256),
                                               textvariable=self._thresh_low, dtype=int, fg="#FF0000")
        self._thresh_low_control["command"] = functools.partial(self._changed_thresh_low,
                                                                utils.EventProxy(focus=True))
        self._thresh_low_control.bind("<FocusIn>", self._changed_thresh_low)
        self._thresh_low_control.bind("<FocusOut>", self._changed_thresh_low)
        thresh_high_label = tk.Label(variable_frame, text="Maximum Threshold", font=("Consolas", 9))
        self._thresh_high_control = ctk.Spinbox(variable_frame, increment=1, values=range(256),
                                                textvariable=self._thresh_high, dtype=int, fg="#0000FF")
        self._thresh_high_control["command"] = functools.partial(self._changed_thresh_high,
                                                                 utils.EventProxy(focus=True))
        self._thresh_high_control.bind("<FocusIn>", self._changed_thresh_high)
        self._thresh_high_control.bind("<FocusOut>", self._changed_thresh_high)
        clust1_label = tk.Label(variable_frame, text="Epsilon", font=("Consolas", 9))
        self._clust1_control = ctk.Spinbox(variable_frame, increment=0.1,
                                           values=utils.LazyLinSpace(0, max_epsilon, begin=False),
                                           textvariable=self._clust1, dtype=float)
        clust2_label = tk.Label(variable_frame, text="Minimum Samples", font=("Consolas", 9))
        self._clust2_control = ctk.Spinbox(variable_frame, increment=1, values=range(1, max_samples),
                                           textvariable=self._clust2, dtype=int)
        invert_label = tk.Label(variable_frame, text="Threshold Inversion", font=("Consolas", 9))
        self._invert_control = tk.Checkbutton(variable_frame, variable=self._threshold_mode)
        image_label = tk.Label(variable_frame, text="Only image data", font=("Consolas", 9))
        self._image_control = tk.Checkbutton(variable_frame,variable=self._do_4d)
        # <editor-fold desc="Create microscope controls">
        scan_frame = tk.LabelFrame(variable_frame, text="Scan", font=("Consolas", 9))
        data_frame = tk.LabelFrame(variable_frame, text="Acquisition", font=("Consolas", 9))
        self._get_s_control = tk.Button(scan_frame, text="Get Values", font=("Consolas", 9), command=self._get_config)
        self._save_s_control = tk.Button(scan_frame, text="Set Values", font=("Consolas", 9),
                                         command=self._set_config("s"))
        self._recall_s_control = tk.Button(scan_frame, text="Recall", font=("Consolas", 9),
                                           command=self._load_config("s"))
        self._get_d_control = tk.Button(data_frame, text="Get Values", font=("Consolas", 9), command=self._get_config)
        self._save_d_control = tk.Button(data_frame, text="Set Values", font=("Consolas", 9),
                                         command=self._set_config("d"))
        self._recall_d_control = tk.Button(data_frame, text="Recall", font=("Consolas", 9),
                                           command=self._load_config("d"))
        # </editor-fold>
        # </editor-fold>

        # <editor-fold desc="Create buttons">
        # <editor-fold desc="Create Setting panels">
        gap_setting = (ctk.SingleControlSetting, {
            "widget": ctk.Spinbox,
            "textvariable": self._gap,
            "values": utils.LazyLinSpace(1, 64),
            "dtype": int,
            "increment": 1,
            "name": "Spacing",
            "description": "The pitch size of each square"
        })
        spacing_setting = (ctk.SingleControlSetting, {
            "widget": ctk.Spinbox,
            "textvariable": self._spacing,
            "values": utils.DynamicLazyLinSpace(tk.IntVar(value=1), self._gap, end=False),
            "dtype": int,
            "increment": 1,
            "name": "Overlap",
            "description": "The number of pixels of overlap",
        })
        match_setting = (ctk.SingleControlSetting, {
            "widget": ctk.Spinbox,
            "textvariable": self._min_points,
            "values": utils.LazyLinSpace(1, max_clusters),
            "dtype": int,
            "increment": 1,
            "name": "Minimum Match",
            "description": "The minimum number of matches found to constitute a valid square",
        })
        padding_setting = (ctk.SingleControlSetting, {
            "widget": ctk.Spinbox,
            "textvariable": self._padding,
            "values": utils.DynamicLazyLinSpace(tk.IntVar(value=0), self._gap),
            "dtype": int,
            "increment": 1,
            "name": "Padding",
            "description": "The padding to have around the bounding box of a cluster"
        })
        preprocess_settings = (ctk.DependantControlSetting, {
            "name": "Preprocessing",
            "names": ("Pre-processing Type", "Kernel Size", "2D blur size", "Standard Deviation X",
                      "Standard Deviation Y", "Shape", "Scale", "Iteration Count"),
            "descriptions": ("The type of morphological transform (or blur) to perform prior to clustering",
                             "The size of the pre-processing kernel (disabled if processing is None)",
                             "The width of the standard kernel (-1 to copy height, disabled if processing is not "
                             "Standard or Gaussian)",
                             "The first value for standard deviation used in Gaussian blurring (disabled if processing "
                             "is not Gaussian)",
                             "The second value for standard deviation used in Gaussian blurring (disabled if processing"
                             " is not Gaussian)",
                             "The shape of the kernel (disabled if processing is not Open and not Close)",
                             "The scale of the kernel (disabled if processing is not Open and not Close)",
                             "The number of iterations to perform (disabled if processing is not Open and not Close)"),
            "decider": {"justify": tk.CENTER, "textvariable": self._preprocessing,
                        "values": ("None", "Standard Blurring", "Gaussian Blurring", "Sharpen", "Open", "Close"),
                        "state": "readonly"},
            "widgets": ((ctk.Spinbox, {"increment": 2, "textvariable": self._kernel,
                                       "values": utils.LazyLinSpace(1, 15), "dtype": int}),
                        (ctk.Spinbox, {"increment": 2, "textvariable": self._blur,
                                       "values": utils.LazyLinSpace(-1, 15), "dtype": int}),
                        (ctk.Spinbox, {"increment": 1, "textvariable": self._gaussian[0],
                                       "values": utils.LazyLinSpace(0, 15), "dtype": int}),
                        (ctk.Spinbox, {"increment": 1, "textvariable": self._gaussian[1],
                                       "values": utils.LazyLinSpace(0, 15), "dtype": int}),
                        (ttk.Combobox, {"justify": tk.CENTER, "textvariable": self._shape,
                                        "values": ("Rectangle", "Cross", "Ellipse"), "state": "readonly"}),
                        (ctk.Spinbox, {"increment": 1, "textvariable": self._scale,
                                       "values": utils.LazyLinSpace(1, 10), "dtype": int}),
                        (ctk.Spinbox, {"increment": 1, "textvariable": self._epochs,
                                       "values": utils.LazyLinSpace(1, 10), "dtype": int})
                        ),
            "mapping": {"Standard Blurring": (0, 1), "Gaussian Blurring": (0, 1, 2, 3), "Sharpen": (0,),
                        "Open": (0, 4, 5, 6), "Close": (0, 4, 5, 6)},
        })
        clustering_settings = (ctk.DependantControlSetting, {
            "name": "Clustering",
            "names": ("Clustering Algorithm", "Square Euclidean", "Minkowski Power"),
            "descriptions": ("The metric used in DBSCAN when clustering",
                             "Whether to have squared distances (disabled if algorithm is not Euclidean)",
                             "The base of the root (and the power to raise values to) (disabled if algorithm is not "
                             "Minkowski)"),
            "decider": {"justify": tk.CENTER, "textvariable": self._cluster_algorithm,
                        "values": ("Manhattan", "Euclidean", "Minkowski"), "state": "readonly"},
            "widgets": ((tk.Checkbutton, {"variable": self._square_mode}),
                        (ctk.Spinbox, {"increment": 1, "textvariable": self._cluster_power,
                                       "values": utils.LazyLinSpace(3, 10), "dtype": int})
                        ),
            "mapping": {"Euclidean": (0,), "Minkowski": (1,)}
        })
        emission_settings = (ctk.SingleControlSetting, {
            "widget": ctk.Spinbox,
            "textvariable": self._emission_threshold,
            "values": utils.LazyLinSpace(80, 300),
            "dtype": int,
            "increment": 10,
            "name": "Emission",
            "mod": "Threshold",
            "description": "The lowest value the emission is allowed to reach before beam flashing"
        })
        drift_settings = (ctk.SingleControlSetting, {
            "widget": ctk.Spinbox,
            "textvariable": self._drift_time,
            "values": utils.LazyLinSpace(60, 180),
            "dtype": int,
            "increment": 1,
            "name": "Drift",
            "mod": "Period",
            "description": "The amount of minutes that pass before checking and correcting for drift"
        })
        # </editor-fold>
        self._scan_button = tk.Button(action_frame, text="Scan", font=("Consolas", 10), command=self._sample)
        self._threshold_button = tk.Button(action_frame, text="Threshold", font=("Consolas", 10),
                                           command=self._process_stage1)
        self._cluster_button = tk.Button(action_frame, text="Cluster", font=("Consolas", 10),
                                         command=self._process_stage2)
        self._grid_button = tk.Button(action_frame, text="Grid Tighten", font=("Consolas", 10), command=self._tighten)
        self._search_button = tk.Button(action_frame, text="Grid Search", font=("Consolas", 10), command=self._scan)
        self._remove_button = tk.Button(action_frame, text="Remove", font=("Consolas", 10), command=self._remove)
        self._stop_button = tk.Button(action_frame, text="STOP", bg="#FF0000", font=("Consolas", 10, "bold"),
                                      command=self._stop)
        self._adv_button = tk.Button(action_frame, text="Advanced Settings", font=("Consolas", 10, "underline"),
                                     command=lambda: ctk.Popup(self._window, self._closed,
                                                               (ctk.GroupedSetting, {
                                                                   "name": "Grid Settings",
                                                                   "settings": (gap_setting,
                                                                                spacing_setting,
                                                                                match_setting,
                                                                                padding_setting)
                                                               }),
                                                               (ctk.GroupedSetting, {
                                                                   "name": "Processing Settings",
                                                                   "settings": (preprocess_settings,
                                                                                clustering_settings)
                                                               }),
                                                               (ctk.GroupedSetting, {
                                                                   "name": "Microscope Settings",
                                                                   "settings": (emission_settings,
                                                                                drift_settings)
                                                               }),
                                                               forget=self._closed.get()))
        self._click_button = tk.Button(action_frame, text="Click cluster 0", font=("Consolas",10), command=self._auto_click)
        self._click_count = 0
        # <editor-fold desc="Create Automation">
        multi_frame = tk.LabelFrame(action_frame, text="Automation", font=("Consolas", 10))
        self._scan_flag = tk.Checkbutton(multi_frame, text="Sample", font=("Consolas", 10),
                                         command=self._change_automation(1))
        self._scan_flag.select()
        self._threshold_flag = tk.Checkbutton(multi_frame, text="Threshold", font=("Consolas", 10),
                                              command=self._change_automation(2, ("auto_threshold", "readonly")))
        self._auto_threshold = ttk.Combobox(multi_frame, font=("Consolas", 10), state=tk.DISABLED,
                                            values=("None", "Minima", "Maxima", "Both"), textvariable=self._auto_thresh)
        self._cluster_flag = tk.Checkbutton(multi_frame, text="Cluster", font=("Consolas", 10),
                                            command=self._change_automation(4, ("click_points", tk.NORMAL)))
        self._click_points = tk.Entry(multi_frame, font=("Consolas", 10), state=tk.DISABLED)
        self._tighten_flag = tk.Checkbutton(multi_frame, text="Tighten", font=("Consolas", 10),
                                            command=self._change_automation(8))
        self._search_flag = tk.Checkbutton(multi_frame, text="Search", font=("Consolas", 10),
                                           command=self._change_automation(16))
        self._go = tk.Button(multi_frame, text="Run", font=("Consolas", 10), command=self._automate)
        self._loop = ctk.Spinbox(multi_frame, font=("Consolas", 10), increment=1 / 60, textvariable=self._timing,
                                 dtype=float, values=utils.LazyLinSpace(0, 60))
        self._loop_description = tk.Label(multi_frame, text="Repeat (minutes)", font=("Consolas", 10))
        # </editor-fold>
        # </editor-fold>

        # <editor-fold desc="Set up PyJEM integration">
        self._current_det = detector.Detector("ADF1")
        self._current_det.set_scanmode(0)
        self._current_det.set_exposuretime_value(3)
        self._current_det.set_frameintegration(1)
        self._current_det.set_imaging_area(self._size, self._size)
        self._m_def = TEM3.Def3()
        self._stage = TEM3.Stage3()
        self._tem_detector = TEM3.Detector3()
        # </editor-fold>
        

        # <editor-fold desc="Tk commands (binding, packing, etc.)">
        self._c1_event = self._c1.get_tk_widget().bind("<Button-1>", self._click_canvas1_a)
        self._c1_event_r = self._c1.get_tk_widget().bind("<Button-3>", self._click_canvas1_r)
        self._c1_event_ad = self._c1.get_tk_widget().bind("<B1-Motion>", self._click_canvas1_a)
        self._c1_event_rd = self._c1.get_tk_widget().bind("<B3-Motion>", self._click_canvas1_r)
        self._c2_event = self._c2.get_tk_widget().bind("<Button-1>", self._click_canvas2)
        self._c3_event = self._c3.get_tk_widget().bind("<Button-1>", self._click_canvas2)
        self._c4_event = self._c4.get_tk_widget().bind("<Button-1>", self._click_canvas2)
        self._ch_event_l = self._ch.get_tk_widget().bind("<B1-Motion>", self._drag_hist_min)
        self._ch_event_h = self._ch.get_tk_widget().bind("<B3-Motion>", self._drag_hist_max)

        for i, e in enumerate(map(FigureCanvasTkAgg.get_tk_widget, (self._c1, self._c2, self._c3, self._c4)), 1):
            e.bind("<Motion>", self._get_colour(i))
            e.bind("<Leave>", self._reset_colour(i))

        action_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        variable_frame.pack(side=tk.LEFT, fill=tk.BOTH)
        self._canvas_frame.pack(side=tk.TOP, fill=tk.BOTH)
        for name, c, l, f in zip(("Scanned", "Thresholded", "Clustered", "Grid"),
                                 map(FigureCanvasTkAgg.get_tk_widget, (self._c1, self._c2, self._c3, self._c4)),
                                 (self._l1, self._l2, self._l3, self._l4),
                                 (c1_frame, c2_frame, c3_frame, c4_frame)):
            l.pack(fill=tk.X)
            c.pack()
            f.pack()
            self._canvas_frame.add(f, text=f"{name} Image", underline=0)
        h_frame.pack()
        self._ch.get_tk_widget().pack()
        self._canvas_frame.insert(1, h_frame, text="Histogram", underline=0)
        for i, control_set in enumerate(zip(
                (thresh_low_label, thresh_high_label, clust1_label, clust2_label, invert_label, image_label),
                (self._thresh_low_control, self._thresh_high_control, self._clust1_control, self._clust2_control,
                 self._invert_control, self._image_control)
        ), 2):
            control_set[0].grid(row=i, column=0, pady=5, sticky=tk.E + tk.W + tk.N + tk.S)
            control_set[1].grid(row=i, column=1, pady=5, sticky=tk.E + tk.W + tk.N + tk.S)
        scan_frame.grid(pady=5, sticky=tk.N + tk.S + tk.E + tk.W, columnspan=2)
        data_frame.grid(pady=5, sticky=tk.N + tk.S + tk.E + tk.W, columnspan=2)
        for (g, s, r) in ((self._get_s_control, self._save_s_control, self._recall_s_control),
                          (self._get_d_control, self._save_d_control, self._recall_d_control)):
            g.pack(fill=tk.Y, padx=5, side=tk.LEFT)
            s.pack(fill=tk.Y, padx=5, side=tk.LEFT)
            r.pack(fill=tk.Y, padx=5, side=tk.LEFT)
        for i, btn in enumerate((self._scan_button, self._threshold_button, self._cluster_button, self._grid_button,
                                 self._search_button, self._remove_button, self._adv_button, self._stop_button,
                                 self._click_button)):
            btn.pack(pady=5, fill=tk.BOTH)

        multi_frame.pack(fill=tk.BOTH)
        for flag in (self._scan_flag, self._threshold_flag, self._cluster_flag, self._tighten_flag, self._search_flag):
            flag.grid(sticky=tk.N + tk.W + tk.S)
        self._auto_threshold.grid(row=1, column=1, sticky=tk.N + tk.E + tk.W + tk.S)
        self._click_points.grid(row=2, column=1, sticky=tk.N + tk.E + tk.W + tk.S)
        self._go.grid(columnspan=2, sticky=tk.N + tk.E + tk.W + tk.S)
        self._loop_description.grid(sticky=tk.N + tk.E + tk.W + tk.S)
        self._loop.grid(row=6, column=1, sticky=tk.N + tk.E + tk.W + tk.S)

        # self._window.after(1, self._check_emission)
        # self._window.after(60_000, self._is_drift_ready)
        # </editor-fold>

    def _change_automation(self, by: int, config: tuple[str, str] = None) -> typing.Callable[[], None]:
        def inner():
            """
            Method to change the automation level by a certain power of two, and will update any external controls.
            Bitwise flag and external controls are gathered from nonlocal variables
            """
            auto_level = self._automation.get()
            if auto_level & by:
                self._automation.set(auto_level & ~by)
                if config is not None:
                    getattr(self, f"_{config[0]}").config(state=tk.DISABLED)
            else:
                self._automation.set(auto_level | by)
                if config is not None:
                    getattr(self, f"_{config[0]}").config(state=config[1])

        return inner

    def _auto_click(self):
        self._click_count += 1
        self._click_button.config(text=f"Click cluster {self._click_count}")
        area=self._colours.get(self._click_count)
        if area is not None:
            self._click_canvas2(utils.EventProxy(colour=sq.Colour(0, 0, self._colours[int(area)],
                                                              wrap=sq.Wrapping.WRAP_SEQ)))

    def _automate(self):
        timing = self._timing.get()
        auto_level = self._automation.get()
        print(auto_level, dict((level, bool(auto_level & level)) for level in (1, 2, 4, 8, 16)))
        if auto_level & 1:
            self._sample()
        if auto_level & 2:
            auto_thresh_mode = self._auto_thresh.get()
            if auto_thresh_mode != "None":
                axes = plt.figure("h").get_axes()
                if axes:
                    axis = axes[0]
                    h_bounds_map: dict[int, tuple[int, int]] = {}
                    for rect_patch in axis.get_children():
                        if not isinstance(rect_patch, RectPatch):
                            continue
                        points = rect_patch.get_bbox().get_points()
                        x0, x1 = int(points[0, 0]), int(points[1, 0])
                        h_bounds_map[int(rect_patch.get_height())] = x0, x1
                    heights = tuple(h_bounds_map.keys())
                    largest_index = max(range(len(h_bounds_map)), key=heights.__getitem__)
                    if auto_thresh_mode == "Minima" or auto_thresh_mode == "Both":
                        _, low = h_bounds_map[heights[largest_index + 1]]
                        self._changed_thresh_low(utils.EventProxy(set_from_callback=low))
                    if auto_thresh_mode == "Maxima" or auto_thresh_mode == "Both":
                        heights = heights[largest_index + 2:]
                        _, high = h_bounds_map[max(heights)]
                        self._changed_thresh_high(utils.EventProxy(set_from_callback=high))
            self._process_stage1()
        if auto_level & 4:
            self._process_stage2()
            points = self._click_points.get()
            if points=="all":
                for colour in self._colours.values():
                    self._click_canvas2(utils.EventProxy(colour=sq.Colour(0, 0, colour, wrap=sq.Wrapping.WRAP_SEQ)))
            elif points:
                areas = points.split(",")
                for area in areas:
                    try:
                        self._click_canvas2(utils.EventProxy(colour=sq.Colour(0, 0, self._colours[int(area)],
                                                                              wrap=sq.Wrapping.WRAP_SEQ)))
                    except ValueError:
                        mtk.showerror("Process Error", "Click points should be numbers seperated by commas")
                        return
                    except KeyError:
                        mtk.showerror("Not enough clusters", f"Cluster {area} does not exist")
                        return
        if auto_level & 8:
            print("Checking gridding")
            if self._gridding.get():
                print("Waiting for 0")
                self._window.wait_variable(self._gridding)
            self._tighten()
        if auto_level & 16:
            if self._gridding.get():
                self._window.wait_variable(self._gridding)
            if self._searching.get():
                self._window.wait_variable(self._searching)
            self._scan()
        if timing:
            self._loop.config(state=tk.DISABLED)
            if self._gridding.get():
                self._window.wait_variable(self._gridding)
            if self._searching.get():
                self._window.wait_variable(self._searching)
            if self._scanning.get():
                self._window.wait_variable(self._scanning)
            self._window.after(int(timing * 60 * 1000), self._automate)

    def _changed_thresh_low(self, event):
        if self._c1_im is None:
            return
        if getattr(event, "set_from_callback") is not None:
            self._thresh_low.set(event.set_from_callback)
        self._drag_hist_min(utils.EventProxy(x=self._thresh_low.get() * 2))
        if hasattr(event, "focus"):
            self._window.focus_set()

    def _changed_thresh_high(self, event):
        if self._c1_im is None:
            return
        if getattr(event, "set_from_callback") is not None:
            self._thresh_high.set(event.set_from_callback)
        self._drag_hist_max(utils.EventProxy(x=self._thresh_high.get() * 2))
        if hasattr(event, "focus"):
            self._window.focus_set()

    def _drag_hist_min(self, event):
        if self._c1_im is None:
            mtk.showwarning("No image set", "Cannot change histogram without scanning")
            return
        ax = plt.figure("h").gca()
        max_lines = [line for line in ax.lines if line.get_color() == "b"]
        max_limit = 255 if not max_lines else (max_lines[-1].get_xdata()[0] - 1)
        constricted = min(max(0, event.x // 2), max_limit)
        self._thresh_low.set(constricted)
        for line in ax.lines:
            if line.get_color() == "r":
                line.remove()
        ax.axvline(constricted, color="r", linewidth=self._size // 10)
        self._ch.draw()

    def _drag_hist_max(self, event):
        if self._c1_im is None:
            mtk.showwarning("No image set", "Cannot change histogram without scanning")
            return
        ax = plt.figure("h").gca()
        min_lines = [line for line in ax.lines if line.get_color() == "r"]
        min_limit = 0 if not min_lines else (min_lines[-1].get_xdata()[0] + 1)
        constricted = min(max(min_limit, event.x // 2), 255)
        self._thresh_high.set(constricted)
        for line in ax.lines:
            if line.get_color() == "b":
                line.remove()
        ax.axvline(constricted, color="b", linewidth=self._size // 10)
        self._ch.draw()

    def _check_emission(self):
        # beam =
        # if beam < self._emission_threshold.get():
        #     mtk.showinfo("Beam Emission Low", "Refreshing beam emission")
        #     self._stop(soft=False)
        #     # refresh beam
        #     self.go(soft=False)
        self._window.after(1, self._check_emission)

    def _is_drift_ready(self):
        # self._elapsed += 60_000
        # if self._elapsed / 1000 >= self._drift_time.get():
        #     page = self._canvas_frame.index(tk.CURRENT)
        #     mtk.showinfo("Drift time elapsed", "Performing drift correction")
        #     # <editor-fold desc="Remember old data and gather new data">
        #     self._elapsed = 0.0
        #     self._stop(soft=False)
        #     old_scan = self._original_scan
        #     if old_scan is None:
        #         self.go(soft=False)
        #         self._window.after(60_000, self._is_drift_ready)
        #         return
        #     old_threshold = self._c2_im
        #     if old_threshold is None:
        #         self._process_stage1(draw=False)
        #         old_threshold = self._c2_im
        #         self.switch_to_page(page)
        #     self._sample(draw=False, populate=False)
        #     self._process_stage1(draw=False)
        #     self.switch_to_page(page)
        #     new_scan = self._original_scan
        #     new_threshold = self._c2_im
        #     # </editor-fold>
        #     cmap = sq.Colour.from_colour(sq.Colours.BLACK if self._threshold_mode.get() else sq.Colours.WHITE)
        #     old_points = self._find_colour(old_threshold, cmap.all(sq.RGBOrder.BGR))
        #     new_points = self._find_colour(new_threshold, cmap.all(sq.RGBOrder.BGR))
        #     if np.all(old_points == new_points):
        #         self.go(soft=False)
        #         mtk.showinfo("No drift", "Microscope hasn't drifted")
        #         self._window.after(60_000, self._is_drift_ready)
        #         return
        #     # <editor-fold desc="Warp old image and clean up">
        #     old_new_map = AffineTransform()
        #     for i in range(5, 301):
        #         if old_new_map.estimate(old_points[:i], new_points[:i]):
        #             print("can estimate matrix at", i, "number of points")
        #             break
        #     to_warp = old_scan.get_channeled_image()
        #     warp_proof = new_scan.get_channeled_image()
        #     old_new_transform = warp(to_warp, old_new_map.inverse)  # if this works, instead warp co-ordinates stored
        #     print(np.all(old_new_tranform==warp_proof))
        #     self._draw("c1")
        #     self._draw("c2")
        #     self.go(soft=False)
        #     # </editor-fold>
        self._window.after(60_000, self._is_drift_ready)

    def _stop(self, soft=True):
        self._keep_going.set(0)
        self._searching.set(0)
        self._gridding.set(0)
        self._scanning.set(0)
        if not soft:
            for button in (self._scan_button, self._threshold_button, self._cluster_button, self._grid_button,
                           self._search_button, self._remove_button, self._adv_button, self._stop_button):
                button.config(state=tk.DISABLED)
            for auto in (self._scan_flag, self._threshold_flag, self._cluster_flag, self._go, self._loop):
                auto.config(state=tk.DISABLED)
                auto.invoke()
            for cid in range(1, 5):
                canvas = getattr(self, f"_c{cid}").get_tk_widget()
                event = getattr(self, f"_c{cid}_event")
                canvas.unbind("<Button-1>", event)
            self._c1.get_tk_widget().unbind("<Button-3>", self._c1_event_r)
            self._c1.get_tk_widget().bind("<B1-Motion>", self._c1_event_ad)
            self._c1.get_tk_widget().bind("<B3-Motion>", self._c1_event_rd)
            self._ch.get_tk_widget().unbind("<B1-Motion>", self._ch_event_l)
            self._ch.get_tk_widget().unbind("<B3-Motion>", self._ch_event_h)
            for ctrl in (self._thresh_low_control, self._thresh_high_control, self._clust1_control,
                         self._clust2_control, self._invert_control, self._image_control, self._get_s_control, self._get_d_control,
                         self._save_s_control, self._save_d_control, self._recall_s_control, self._recall_d_control):
                ctrl.config(state=tk.DISABLED)

    def _get_config(self):
        print("Loading microscope configurations into variables")
        self._microscope_settings.get_state()

    def _set_config(self, prefix: str) -> typing.Callable[[], None]:
        def inner():
            """
            A method to save the loaded configuration into a file.
            A nonlocal variable differentiates between scanning configurations and acquisition configurations
            """
            print("Saving microscope configurations into file")
            self._microscope_settings.write_to(f"assets/{prefix}_microscope.hdf5")

        return inner

    def _load_config(self, prefix: str) -> typing.Callable[[], None]:
        def inner():
            """
            A method to recall a saved configuration from a file.
            A nonlocal variable differentiates between scanning configurations and acquisition configurations
            """
            print("Restoring microscope configurations from file")
            self._microscope_settings.write_from(f"assets/{prefix}_microscope.hdf5")

        return inner

    def _get_colour(self, index: int) -> typing.Callable[[typing.Any], None]:
        def inner(event):
            """
            A method to get the colour of a particular canvas and display it on the corresponding label.
            Canvas and label are determined from nonlocal variable index.
            :param event: The event object obtained from the click.
            """
            label: tk.Label = getattr(self, f"_l{index}")
            image: sq.Image = getattr(self, f"_c{index}_im")
            if image is None or (event.x >= self._size or event.y >= self._size):
                return
            r, g, b = image[event.x, event.y].all(sq.RGBOrder.RGB)
            label.config(text=f"({r:03},{g:03},{b:03}) @ <{event.x}, {event.y}>")

        return inner

    def _reset_colour(self, index: int) -> typing.Callable[[typing.Any], None]:
        def inner(event):
            """
            A method to reset the colour of a particular label. Label is determined from nonlocal variable index.
            :param event: The event object obtained from the click.
            """
            getattr(self, f"_l{index}").config(text="(000,000,000)")

        return inner

    def _draw(self, c_name: str):
        """
        A method to draw the image of the specified canvas
        :param c_name: The name of the canvas to draw on, and to find the image of
        """
        c_name = f"_{c_name}"
        canvas: FigureCanvasTkAgg = getattr(self, c_name)
        image: sq.Image = getattr(self, f"{c_name}_im")
        fig = plt.figure(int(c_name[-1]), frameon=False, clear=True, tight_layout=True, figsize=(self._size, self._size), dpi=1)
        axis = fig.add_subplot(111)
        axis.set_xticks([])
        axis.set_yticks([])
        axis.imshow(image.get_channeled_image(sq.RGBOrder.RGB) / 255, extent=(0, self._size, 0, self._size))
        canvas.figure = fig
        canvas.draw()

    @utils.check_controls(0)
    def _sample(self, *, draw=True, populate=True):
        """
        Method to scan an image from the microscope
        """
        if self._searching.get():
            mtk.showwarning("Searching Grid", "Cannot change image while searching")
            return
        self._tem_detector.SetPosition(10, 1)
        self._current_det.set_scanmode(0)
        self._current_det.set_imaging_area(self._size, self._size)
        self._m_def.SetBeamBlank(0)
        time.sleep(1)
        byte_stream = self._current_det.snapshot_rawdata()
        image = np.frombuffer(byte_stream, np.uint16)
        image = image.reshape((self._size, self._size)) / np.max(image)
        image = (image * 255).astype(np.uint8)
        self._c1_im = sq.Image(image)
        self._m_def.SetBeamBlank(1)
        # self._c1_im = sq.Image.from_file("assets/img_3.bmp", cv2.IMREAD_GRAYSCALE)
        if not all(dim == self._size for dim in self._c1_im.shape):
            self._c1_im = None
            mtk.showerror("Value Error", f"Expected image to be {self._size}x{self._size} pixels")
            return
        self._clear(from_=1)
        self._original_scan = self._c1_im.copy()
        img = self._original_scan.get_raw()[:, :, 0]
        if populate:
            fig = plt.figure("h", frameon=False, clear=True, tight_layout=True, figsize=(self._size, self._size), dpi=1)
            axis = fig.add_subplot(111)
            axis.get_xaxis().set_visible(False)
            axis.get_yaxis().set_visible(False)
            axis.hist(img.flatten(), bins=255 // 15, log=True)
            axis.axvline(self._thresh_low.get(), color="r", linewidth=self._size // 10)
            axis.axvline(self._thresh_high.get(), color="b", linewidth=self._size // 10)
            self._ch.figure = fig
            self._ch.draw()
        if draw:
            self._draw("c1")

    @utils.check_controls(2)
    def _process_stage1(self, *, draw=True):
        """
        Method to perform thresholding of the scanned image
        """
        if self._searching.get():
            mtk.showwarning("Searching Grid", "Cannot change image while searching")
            return
        if self._c1_im is not None:
            im = self._original_scan.to_colour(sq.CMODE.BW, sq.Domain.R)
            process = self._preprocessing.get()
            size = self._kernel.get()
            # <editor-fold desc="Pre-processing">
            if process == "Standard Blurring":
                kern_2 = self._blur.get()
                im = im.blur((size, kern_2 if kern_2 != -1 else size))
            elif process == "Gaussian Blurring":
                kern_2 = self._blur.get()
                im = im.gaussian_blur((size, kern_2 if kern_2 != -1 else size),
                                      (self._gaussian[0].get(), self._gaussian[1].get()))
            elif process == "Sharpen":
                im = im.sharpen(size)
            # </editor-fold>
            in_bound = 255 if self._threshold_mode.get() else 0
            raw = im.get_raw()[:, :, 0]
            low_thresh = self._thresh_low.get()
            high_thresh = self._thresh_high.get()
            out = (raw < low_thresh) | (raw > high_thresh)
            raw[out] = 255 - in_bound
            raw[~out] = in_bound
            # <editor-fold desc="Post-processing">
            if process == "Open" or process == "Close":
                m_mode: Morphs = getattr(Morphs, process.upper())
                scale = self._scale.get()
                shape = self._shape.get()
                num_iterations = self._epochs.get()
                if shape == "Rectangle":
                    m_shape = cv2.MORPH_RECT
                elif shape == "Cross":
                    m_shape = cv2.MORPH_CROSS
                else:
                    m_shape = cv2.MORPH_ELLIPSE
                im = sq.transforms.Transform.morphological(im, m_mode, m_shape, (size, size),
                                                           kernel_scale=scale, iterations=num_iterations)
                raw = im.get_raw()
            # </editor-fold>
            self._c2_im = sq.Image(raw)
            self._clear(from_=2)
            if draw:
                self._draw("c2")
        else:
            mtk.showwarning("Un scanned Image", "The image has not been scanned yet")
            self._canvas_frame.select(0)

    @utils.check_controls(3)
    def _process_stage2(self, *, draw=True):
        """
        Method to perform clustering on the threshold image
        """
        if self._searching.get():
            mtk.showwarning("Searching Grid", "Cannot change image while searching")
            return
        if self._c2_im is not None:
            new_im = self._c2_im.image
            where_white = np.where(new_im == 255)
            white = np.asarray(where_white).T
            regions = np.zeros_like(new_im)
            metric_kwargs = None
            al = self._cluster_algorithm.get()
            if al == "Euclidian" and self._square_mode.get():
                al = f"Sq{al}"
            elif al == "Minkowski":
                metric_kwargs = {"p": int(self._cluster_power.get())}
            clusters = DBSCAN(float(self._clust1.get()), min_samples=int(self._clust2.get()), metric=al.lower(),
                              metric_params=metric_kwargs).fit_predict(white) + 1
            n = len(np.unique(clusters))
            step = (255 * 3) // n
            stepped = clusters * step
            regions[where_white] = stepped
            self._colours = dict(zip(clusters, stepped))
            print(step, np.any(clusters!=0), n, len(self._colours))
            self._c3_im = sq.Image(regions[:, :, 0], auto_wrap=True)
            self._clear(from_=3)
            if draw:
                self._draw("c3")
        else:
            mtk.showwarning("Un processed Image", "Must threshold prior to clustering")
            self._canvas_frame.select(2)

    @utils.check_controls(0)
    def _click_canvas1_a(self, event, *, draw=True):
        """
        Method to handle adding additional scan regions from _c1
        :param event: The event object obtained from the click
        """
        if self._searching.get():
            mtk.showwarning("Searching Grid", "Cannot change amount of searches while searching")
            return
        if self._c1_im is None:
            mtk.showwarning("No scanned image", "Image has not yet been scanned")
            return
        point = event.y, event.x
        if point in self._extras:
            return
        else:
            self._make_square(point, event, False)
        if draw:
            self._draw("c1")

    def _make_square(self, point: tuple[int, int], event, delete: bool):
        spacing = self._gap.get() // 2
        start = event.y - spacing, event.x - spacing
        end = event.y + spacing, event.x + spacing
        x_range = np.arange(start[0], end[0])
        y_range = np.arange(start[1], end[1])
        if not delete:
            self._extras[point] = (x_range, y_range)
            colour1 = colour2 = self._grid_colour.all(sq.RGBOrder.BGR)

            def _postprocess():
                pass
        else:
            del self._extras[point]
            colour1 = colour2 = None

            def _postprocess():
                nonlocal colour1, colour2
                colour1 = colour2 = None
        for y in x_range:
            if colour1 is None:
                colour1 = self._original_scan.get_raw()[y, y_range[0]]
            self._c1_im.get_raw()[y, y_range[0]] = colour1
            if colour2 is None:
                colour2 = self._original_scan.get_raw()[y, y_range[-1]]
            self._c1_im.get_raw()[y, y_range[-1]] = colour2
            _postprocess()
        for x in y_range:
            if colour1 is None:
                colour1 = self._original_scan.get_raw()[x_range[0], x]
            self._c1_im.get_raw()[x_range[0], x] = colour1
            if colour2 is None:
                colour2 = self._original_scan.get_raw()[x_range[-1], x]
            self._c1_im.get_raw()[x_range[-1], x] = colour2
            _postprocess()

    @utils.check_controls(0)
    def _click_canvas1_r(self, event, *, draw=True):
        if self._searching.get():
            mtk.showwarning("Searching Grid", "Cannot change amount of searches while searching")
            return
        if self._c1_im is None:
            mtk.showwarning("No scanned image", "Image has not yet been scanned")
            return
        point = event.y, event.x
        spacing = self._gap.get() // 2
        for p in range(-spacing, spacing):
            for new_point in ((point[0] + p, point[1]), (point[0], point[1] + p), (point[0] + p, point[1] + p)):
                if new_point not in self._extras:
                    continue
                self._make_square(new_point, utils.EventProxy(x=new_point[1], y=new_point[0]), True)
                break
            else:
                continue
            break
        if draw:
            self._draw("c1")

    @utils.check_controls(4)
    def _click_canvas2(self, event, *, draw=True):
        """
        Method to handle clicking on clusters from either _c2, _c3, or _c4
        :param event: The event object obtained from the click
        """
        print("Click 2 run")
        if self._searching.get():
            mtk.showwarning("Searching Grid", "Cannot change amount of searches while searching")
            return
        if self._c3_im is None:
            mtk.showwarning("Un processed image", "The scanned image has not been fully processed yet")
            self._canvas_frame.select(2)
            return
        if self._gridding.get():
            mtk.showwarning("Currently outlining", "Cannot perform outline process while running outline process")
            return
        self._gridding.set(1)

        # <editor-fold desc="Decide what cluster click belongs to and process if it has already been seen">
        if hasattr(event, "colour"):
            click_colour = event.colour
            print(f"Forced from {click_colour.all(sq.RGBOrder.RGB)}")
        else:
            click_colour = self._coloured_im[event.x, event.y]
        if click_colour.is_colour(sq.Colours.BLACK):
            if not hasattr(event, "colour"):
                mtk.showwarning("Non featured area", "Click was in area with no feature data")
                self._canvas_frame.select(2)
            self._gridding.set(0)
            return
        tup_colour = click_colour.all(sq.RGBOrder.BGR)
        if tup_colour in self._clicked2:
            self._remove(draw=False)
        else:
            target = self._c3_im if self._c4_im is None else self._c4_im
            self._processed_images[tup_colour] = target.copy()
        self._clicked2.append(tup_colour)
        self._region_index.set(0)
        # </editor-fold>

        # <editor-fold desc="Find cluster bounding box and create overlapping steps in x and y axes">
        correct_places = self._find_colour(self._c3_im, tup_colour)
        if len(correct_places.shape) == 1:
            mtk.showwarning("Cluster Error",
                            f"No points match cluster with colour {click_colour.all(sq.RGBOrder.RGB)}")
            self._gridding.set(0)
            return
        step = self._gap.get()
        only_x = correct_places[:, 0]
        only_y = correct_places[:, 1]
        min_x, max_x = max(np.min(only_x) - self._padding.get(), 0), min(np.max(only_x) + self._padding.get(),
                                                                         self._size - 1)
        min_y, max_y = max(np.min(only_y) - self._padding.get(), 0), min(np.max(only_y) + self._padding.get(),
                                                                         self._size - 1)
        if abs(max_x-min_x) <= 5:
            self._gridding.set(0)
            print(f"{click_colour} too narrow")
            return
        elif abs(max_y-min_y) <= 5:
            self._gridding.set(0)
            print(f"{click_colour} too short")
            return

        line_step = step - self._spacing.get()
        lines_x, lines_y = np.arange(min_x, max_x, line_step), np.arange(min_y, max_y, line_step)
        c4_im = sq.Image(self._c3_im.image[min_x:max_x + step, min_y:max_y + step])
        # </editor-fold>

        self._areas[tup_colour] = (c4_im, lines_x, lines_y, step)
        img = self._c4_im.get_raw()

        mesh_x, mesh_y = np.meshgrid(lines_x, lines_y)

        for i in range(step):
            new_mesh_x = mesh_x + i
            new_mesh_x[new_mesh_x >= self._size] = self._size - 1
            img[new_mesh_x, mesh_y] = self._grid_colour.all(sq.RGBOrder.BGR)
            new_mesh_y = mesh_y + i
            new_mesh_y[new_mesh_y >= self._size] = self._size - 1
            img[mesh_x, new_mesh_y] = self._grid_colour.all(sq.RGBOrder.BGR)
        self._gridding.set(0)
        if draw:
            self._draw("c4")

    @utils.check_controls(4)
    def _remove(self, *, draw=True):
        """
        Method to remove the grid from the most recently drawn cluster.
        :param draw: Whether to redraw the image post-removal
        """
        if self._searching.get():
            mtk.showwarning("Searching Grid", "Cannot change amount of searches while searching")
            return
        if self._scanning.get():
            mtk.showwarning("Searching Grid", "Cannot change amount of searches while scanning")
            return
        try:
            del self._processed_images[self._clicked2.pop()]
            if draw:
                if len(self._processed_images) == 0:
                    self._c4.figure.clear()
                    self._canvas_frame.select(3)
                else:
                    self._draw("c4")
            self._region_index.set(0)
            self._scan_index.set(0)
            self._valid_regions.clear()
        except IndexError:
            mtk.showerror("No processed images", "Processed images is empty")
            self._canvas_frame.select(3)

    @utils.check_controls(4)
    def _tighten(self, *, draw=True):
        """
        Method to run a grid search algorithm on every clicked region
        """
        if not self._clicked2 and not self._extras:
            mtk.showwarning("No grid", "No grid has been set up")
            self._canvas_frame.select(3)
            return
        if self._searching.get():
            mtk.showwarning("Already running search", "Cannot run parallel grid search operations")
            return
        self._searching.set(1)
        length = len(self._clicked2)
        self._c4_im = self._c3_im.copy()
        move_x = tk.IntVar(self._window)
        move_region = tk.IntVar(self._window)
        finished = tk.IntVar(self._window)

        def _do_scan():
            def _incr_x(i: int):
                if not self._keep_going.get() or i >= x_length:
                    move_region.set(move_region.get() + 1)
                    return
                # noinspection PyTypeChecker
                sq_s_x: int = square_x[i]
                sq_e_x = sq_s_x + square_size
                _incr_y(0, sq_s_x, sq_e_x)
                self._window.wait_variable(move_x)
                self._window.after(1, _incr_x, i + 1)

            def _incr_y(i: int, sq_s_x: int, sq_e_x: int):
                if not self._keep_going.get() or i >= y_length:
                    move_x.set(move_x.get() + 1)
                    return
                # noinspection PyTypeChecker
                sq_s_y: int = square_y[i]
                sq_e_y = sq_s_y + square_size
                section = img[sq_s_x:sq_e_x + 1, sq_s_y:sq_e_y + 1]
                co_ords = self._find_colour(sq.Image(section, auto_wrap=True), region)
                if len(co_ords) >= self._min_points.get():
                    self._c4_im = sq.Image(
                        cv2.rectangle(self._c4_im.image, (sq_s_y + low_y, sq_s_x + low_x),
                                      (sq_e_y + low_y, sq_e_x + low_x), self._grid_colour.all(sq.RGBOrder.BGR)),
                        auto_wrap=True)
                    self._valid_regions.append(utils.ScanSite((sq_s_y + low_y, sq_s_x + low_x),
                                                              (sq_e_y + low_y, sq_e_x + low_x),
                                                              self._size))
                    print(self._valid_regions[-1])
                self._window.after(1, _incr_y, i + 1, sq_s_x, sq_e_x)

            starting_region = self._region_index.get()
            if starting_region >= length:
                finished.set(1)
                return
            region = self._clicked2[starting_region]
            image, square_x_large, square_y_large, square_size = self._areas[region]
            img = image.image
            # noinspection PyTypeChecker
            low_x: int = square_x_large[0]
            # noinspection PyTypeChecker
            low_y: int = square_y_large[0]
            square_x = square_x_large - low_x
            square_y = square_y_large - low_y
            x_length = len(square_x)
            y_length = len(square_y)
            _incr_x(0)
            self._window.wait_variable(move_region)
            if not self._keep_going.get():
                finished.set(1)
                return
            self._region_index.set(self._region_index.get() + 1)
            self._window.after(1, _do_scan)

        _do_scan()
        self._window.wait_variable(finished)
        extras = list(self._extras.values())

        starting_extra_region = self._region_index.get()
        if starting_extra_region > length:
            extras = extras[starting_extra_region % length:]
        for _, square_x_region, square_y_region in extras:
            if not self._keep_going.get():
                break
            self._region_index.set(self._region_index.get() + 1)
            self._valid_regions.append(utils.ScanSite((np.min(square_y_region), np.min(square_x_region)),
                                                      (np.max(square_y_region), np.max(square_x_region)), self._size))
        self._searching.set(0)
        if draw:
            self._draw("c4")
        self._scan_im = self._c4_im.copy()

    @utils.check_controls(4)
    def _scan(self):
        if not self._valid_regions:
            mtk.showwarning("Loose regions", "Cannot perform grid searching before grid tightening")
            return
        elif self._searching.get():
            mtk.showwarning("Tightening", "Cannot scan while tightening")
            return
        active_colour = self._scanning_colour.all(sq.RGBOrder.BGR)
        original = self._scan_im.get_channeled_image()
        length = len(self._valid_regions)
        just_image = self._do_4d.get()
        lens = TEM3.Lens3()
        variances = []
        defocuses = []
        SIG_TOL = 0
        focus = lens.GetOLf()
        df = 5  # bit change
        y_shift = -100
        x_shift = 100

        def auto_focus(image_used: np.ndarray) -> float:
            var = image_used.var()
            mean = image_used.mean() ** 2
            return var / mean

        def scan():
            self._current_det.set_exposuretime_value(15)
            self._m_def.SetBeamBlank(0)
            byte_stream = self._current_det.snapshot_rawdata()
            image = np.frombuffer(byte_stream, np.uint16)
            image = image.reshape(256, 256) / np.max(image)
            return (image * 255).astype(np.uint8)

        def _scan(i: int):
            nonlocal df, focus
            if not self._keep_going.get():
                return
            elif i >= length:
                # self._c4_im = self._scan_im.copy()
                # self._draw("c4")
                # self._window.update()
                # if self._line_done:
                #     self._stage.SetYRel(y_shift)
                #     self._scan_position[1] += 1
                #     if self._scan_position[1] > self._rows:
                #         quit(0) # change this.    
                # else:
                #     self._stage.SetXRel(x_shift * (-1 if self._scan_position[1] % 2 else 1))
                #     self._scan_position[0] += 1
                # time.sleep(60)
                self._scanning.set(0)
                self._scan_index.set(0)
                self._m_def.SetBeamBlank(1)
                self._current_det.set_exposuretime_value(3)
                raw = self._c4_im.get_raw()
                raw[:, :, :] = original
                return
            region = self._valid_regions[i]
            self._scan_index.set(i)
            self._number_of_scans += 1
            # if self._number_of_scans % 10 == 0:
            #     self._current_det.set_scanmode(0)
            #     self._current_det.set_imaging_area(256, 256)
            #     self._tem_detector.SetPosition(10, 1)
            #     for j in range(20):
            #         image = scan()
            #         sigma = auto_focus(image)
            #         variances.append(sigma)
            #         defocuses.append(focus)
            #         if j > 1:
            #             dsigma = variances[-1] - variances[-2]
            #             if dsigma < 0:
            #                 if j > 2:
            #                     break
            #                 df *= -1
            #         lens.SetOLf(focus + df)
            #         focus += df
            #     chosen = max(range(len(variances)), key=variances.__getitem__)
            #     lens.SetOLf(defocuses[chosen])
            #     self._current_det.set_imaging_area(4096, 4096)
            #     self._current_det.set_scanmode(3)
            #     self._tem_detector.SetPosition(10, 0)
            raw = self._c4_im.get_raw()
            raw[:, :, :] = original
            top, left = region.corner(utils.BBox.TOP | utils.BBox.LEFT)
            bottom, right = region.corner(utils.BBox.BOTTOM | utils.BBox.RIGHT)
            raw[left:right, top:bottom] = active_colour
            converted = region.conv_to(4096)
            top_left = converted.corner(utils.BBox.TOP | utils.BBox.LEFT)
            bottom_right = converted.corner(utils.BBox.BOTTOM | utils.BBox.RIGHT)
            print(region, converted)
            self._current_det.set_areamode_imagingarea(256, 256, *top_left)
            self._draw("c4")
            self._window.update()
            if just_image:
                self._tem_detector.SetPosition(10, 1)
                image = scan()
                params_file_path = f"saved_files/image_{i}.hdf5"
                utils.save_arr_to_file(image, params_file_path, top_left, bottom_right)
                with h5py.File(params_file_path, "a") as out:
                    out.create_dataset("survey image",data=self._c1_im.get_channeled_image(sq.RGBOrder.RGB))
                    out.create_dataset("thresholded image",data=self._c2_im.get_channeled_image(sq.RGBOrder.RGB))
                    out.create_dataset("segmented image",data=self._c3_im.get_channeled_image(sq.RGBOrder.RGB))
                    out.create_dataset("grid squares",data=self._c4_im.get_channeled_image(sq.RGBOrder.RGB))
            else:
                self._tem_detector.SetPosition(10, 0)
                px_val = 256
                dwell_val = 1_000
                bit_val  = 12
                session = 'cm37231-1'
                sample = 'Pt_NP_SEND_Ptycho_Trial'
                datetime_base = self._microscope_settings.time_stamp
                save_path = f'X:\\data\\2024\\{session}\\Merlin\\{sample}'
                params_file_path = f'{save_path}\\{datetime_base}.hdf'
                print(params_file_path)
                if not os.path.exists(save_path):
                    os.makedirs(save_path)
                    print('made_dir : ', save_path)
                merlin_params = {}
                merlin_params['set_dwell_time(usec)'] = dwell_val
                merlin_params['set_scan_px'] = px_val
                merlin_params['set_bit_depth'] = bit_val
                self._microscope_settings.get_state()
                self._microscope_settings.write_to(params_file_path, **merlin_params)
                with h5py.File(params_file_path, "a") as out:
                    co_ords=out.create_group("Co-ordinates")
                    co_ords["top left"] = top_left
                    co_ords["bottom right"] = bottom_right
                    out.create_dataset("survey image",data=self._c1_im.get_channeled_image(sq.RGBOrder.RGB))
                    out.create_dataset("thresholded image",data=self._c2_im.get_channeled_image(sq.RGBOrder.RGB))
                    out.create_dataset("segmented image",data=self._c3_im.get_channeled_image(sq.RGBOrder.RGB))
                    out.create_dataset("grid squares",data=self._c4_im.get_channeled_image(sq.RGBOrder.RGB))
                self._current_det.set_exposuretime_value(dwell_val)
                self._current_det.set_scanmode(1)
                self._m_def.SetBeamBlank(1)
                hostname = '10.182.0.5'
                print('2') 
                
                merlin_cmd = MERLIN_connection(hostname, channel='cmd')
                # merlin_cmd = MERLIN_connection(hostname, channel=6341)
                print('*****3*****')   
                
                merlin_cmd.setValue('NUMFRAMESTOACQUIRE', px_val*px_val)
                merlin_cmd.setValue('COUNTERDEPTH', bit_val)
                merlin_cmd.setValue('CONTINUOUSRW', 1)
                merlin_cmd.setValue('ACQUISITIONTIME', dwell_val * 1e-6)
                merlin_cmd.setValue('FILEDIRECTORY', save_path)
                merlin_cmd.setValue('FILENAME', datetime_base+'_data')
                merlin_cmd.setValue('FILEENABLE',1)
        ###### trigger set up and filesaving
                merlin_cmd.setValue('TRIGGERSTART', 1)
                merlin_cmd.setValue('TRIGGERSTOP', 1)
                merlin_cmd.setValue('SAVEALLTOFILE', 1)
                merlin_cmd.setValue('USETIMESTAMPING', 1)
        ##### setting up VDF with STEM mode
                merlin_cmd.setValue('SCANX', px_val)
                merlin_cmd.setValue('SCANY', px_val)
        #        # set to pixel trigger
                merlin_cmd.setValue('SCANTRIGGERMODE', 0)
                merlin_cmd.setValue('SCANDETECTOR1ENABLE', 0)
                # Standard ADF det
                merlin_cmd.setValue('SCANDETECTOR1TYPE', 0)
                merlin_cmd.setValue('SCANDETECTOR1CENTREX', 255)
                merlin_cmd.setValue('SCANDETECTOR1CENTREY', 255)
                merlin_cmd.setValue('SCANDETECTOR1INNERRADIUS', 50)
                merlin_cmd.setValue('SCANDETECTOR1OUTERRADIUS', 150)
                
                print('**5**')
                merlin_cmd.MPX_CMD(type_cmd='CMD', cmd='SCANSTARTRECORD')
                print('6')
                #unblank beam
                self._m_def.SetBeamBlank(0)
                if px_val==64:
                    fly_back = 2 * (dwell_val) * (px_val * px_val)
                else:
                    #fly_back = 1.7 * (dwell_val/10**6) * px_val * px_val
                    fly_back = 75
                
                total_frametime = int(dwell_val/1000 * (px_val * px_val) + (fly_back * px_val)) #needs to be in milliseconds
                print(total_frametime)
                self._current_det.set_scanmode(3)
                time.sleep(total_frametime/1000)

                print('scanning done')   
                #merlin_cmd.__del__()
                
                time.sleep(0.001)

            print(top_left, bottom_right)
            self._window.after(1, _scan, i + 1)

        self._scanning.set(1)
        self._current_det.set_imaging_area(4096, 4096)
        self._current_det.set_scanmode(3)
        self._m_def.SetBeamBlank(0)
        _scan(self._scan_index.get())

    @staticmethod
    def _find_colour(img: sq.Image, colour: tuple[int, int, int]) -> np.ndarray:
        """
        Method to find all co-ordinates where the image is the corresponding colour
        :param img: The image to scan
        :param colour: The colour to check for
        :return: A list of every co-ordinate
        """
        channels = img.get_channeled_image()
        area = zip(*np.where(channels == colour))
        correct = collections.defaultdict(list)
        for co_ord in area:
            correct[co_ord[:2]].append(co_ord[2])
        return np.array(list(filter(lambda k: len(correct[k]) == 3, correct)))

    def _clear(self, from_: int):
        if from_ < 2:
            self._c2_im = None
            self._c2.figure.clear()
            self._extras.clear()
        if from_ < 3:
            self._c3_im = None
            self._c3.figure.clear()
        if from_ < 4:
            self._processed_images.clear()
            self._areas.clear()
            self._clicked2.clear()
            self._c4.figure.clear()
        if from_ > 3 or from_ < 1:
            raise ValueError("Invalid from value")

    def run(self):
        """
        Mainloop the window to actually see the program running and interact with it
        """
        self._window.mainloop()

    def get_controls(self) -> tuple[ctk.Spinbox, ctk.Spinbox, ctk.Spinbox, ctk.Spinbox]:
        """
        Method to get each of the variables controlling regular settings
        :return: The 4 controls
        """
        return self._thresh_low_control, self._thresh_high_control, self._clust1_control, self._clust2_control

    def switch_to_page(self, index: int):
        """
        Method to switch to a specific page of the notebook
        :param index: The index of the page to switch to
        """
        self._canvas_frame.select(index)

    def go(self, soft=True):
        """
        Will allow the microscope to re-scan again
        :param soft: Whether the re-scan is soft (normal) or hard (from beam emission)
        """
        self._keep_going.set(1)
        if not soft:
            for button in (self._scan_button, self._threshold_button, self._cluster_button, self._grid_button,
                           self._remove_button, self._adv_button, self._stop_button):
                button.config(state=tk.NORMAL)
            for auto in (self._scan_flag, self._threshold_flag, self._cluster_flag, self._go, self._loop):
                auto.config(state=tk.NORMAL)
                auto.invoke()
            self._c1_event = self._c1.get_tk_widget().bind("<Button-1>", self._click_canvas1_a)
            self._c1_event_r = self._c1.get_tk_widget().bind("<Button-3>", self._click_canvas1_r)
            self._c1_event_ad = self._c1.get_tk_widget().bind("<B1-Motion>", self._click_canvas1_a)
            self._c1_event_rd = self._c1.get_tk_widget().bind("<B3-Motion>", self._click_canvas1_r)
            self._c2_event = self._c2.get_tk_widget().bind("<Button-1>", self._click_canvas2)
            self._c3_event = self._c3.get_tk_widget().bind("<Button-1>", self._click_canvas2)
            self._c4_event = self._c4.get_tk_widget().bind("<Button-1>", self._click_canvas2)
            self._ch_event_l = self._ch.get_tk_widget().bind("<B1-Motion>", self._drag_hist_min)
            self._ch_event_h = self._ch.get_tk_widget().bind("<B3-Motion>", self._drag_hist_max)
            for ctrl in (self._thresh_low_control, self._thresh_high_control, self._clust1_control,
                         self._clust2_control, self._invert_control, self._image_control, self._get_s_control, self._get_d_control,
                         self._save_s_control, self._save_d_control, self._recall_s_control, self._recall_d_control):
                ctrl.config(state=tk.NORMAL)


if __name__ == '__main__':
    while True:
        try:
            Program(512, sq.Colour.from_colour(sq.Colours.RED), sq.Colour.from_colour(sq.Colours.GREEN)).run()
            plt.close("all")
            break
        except TEM3.TEM3Error:
            continue
