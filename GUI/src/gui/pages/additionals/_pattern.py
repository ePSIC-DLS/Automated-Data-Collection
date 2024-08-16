import functools
import typing
from typing import Dict as _dict, List as _list, Optional as _None

import numpy as np

from ... import utils
from ..._base import CanvasPage, images, SettingsPage, widgets
from .... import load_settings, validation
from ....language.utils import objs, vals

default_settings = load_settings("assets/config.json",
                                 scan_size=validation.examples.survey_size,
                                 scan_resolution=validation.examples.resolution,
                                 selected=validation.examples.pattern,
                                 raster=validation.examples.raster_pattern,
                                 snake=validation.examples.snake_pattern,
                                 spiral=validation.examples.spiral_pattern,
                                 grid=validation.examples.grid_pattern,
                                 random=validation.examples.random_pattern,
                                 )


class ScanType(CanvasPage, SettingsPage):
    """
    Concrete page with a canvas and settings to determine how the scan is performed.

    This uses the arbitrary pattern generation of the QD scan engine.

    Note that while this *page* is fully implemented, it does not yet export the pattern.

    Attributes
    ----------
    SIZES: tuple[int, ...]
        The possible scan resolutions.
    _colour: int_
        The colour representing a pattern.
    _sq_size: int
        The size of the square (this affects the co-ordinates).
    _pattern: Design | None
        The currently selected pattern.
    _selected: ScanPattern | None
        The currently selected widget.
    _raster: ScanPattern
        The widget representing the parameter space for the raster pattern.
    _snake: ScanPattern
        The widget representing the parameter space for the snake pattern.
    _spiral: ScanPattern
        The widget representing the parameter space for the spiral pattern.
    _grid: ScanPattern
        The widget representing the parameter space for the grid pattern.
    _random: ScanPattern
        The widget representing the parameter space for the random pattern.
    _scan_resolution: LabelledWidget[ComboBox[int]]
        The widget representing the current resolution of grid search scans.
    _btns: QButtonGroup
        The grouping of all choices - used to make sure each ScanPattern is mutually exclusive.
    """
    settingChanged = SettingsPage.settingChanged
    SIZES = (256, 512, 1024, 2048, 4096, 8192, 16384)

    def __init__(self, size: int, pattern_colour: np.int_, failure_action: typing.Callable[[Exception], None]):
        ScanType.SIZES = tuple(s for s in ScanType.SIZES if s > size)
        CanvasPage.__init__(self, size)
        SettingsPage.__init__(self, utils.SettingsDepth.REGULAR)
        self._colour_option.hide()
        self._colour = pattern_colour
        self._sq_size = default_settings["scan_size"]
        self._pattern: _None[utils.Design] = None
        self._selected: _None[utils.ScanPattern] = None

        def _gen_coverage(init: int) -> utils.XDControl:
            return utils.XDControl(2, utils.PercentageBox, initial=int(init * 100),
                                   pipeline=validation.examples.coverage, step=5)

        def _gen_skip(inclusive=True) -> validation.Pipeline:
            return validation.examples.any_int + validation.Pipeline(
                validation.Step(validation.RangeValidator(
                    validation.LowerBoundValidator(0, inclusive=inclusive),
                    validation.DynamicUpperBoundValidator(lambda: self._sq_size, inclusive=False)
                ), desc="ensure the integer is between 0 and the grid size"),
                in_type=int, out_type=int)

        def _low_max() -> int:
            random = self._random.to_dict()
            return random["high"].get_data()

        def _high_min() -> int:
            random = self._random.to_dict()
            return random["low"].get_data()

        def _change_rand_type(new: utils.RandomTypes):
            for k, widget in random_dict.items():
                if k not in {"n", "r_type", "coverage"}:
                    self._random.hide_option(k)
            if new == utils.RandomTypes.EXP:
                keys = ("scale",)
            elif new in {utils.RandomTypes.LAPLACE, utils.RandomTypes.LOGISTIC, utils.RandomTypes.NORMAL}:
                keys = ("scale", "loc")
            elif new == utils.RandomTypes.POISSON:
                keys = ("lam",)
            else:
                keys = ("low", "high")
            for k in keys:
                self._random.show_option(k)
            self._update()

        n = validation.examples.any_int + validation.Pipeline(
            validation.Step(validation.RangeValidator(
                validation.LowerBoundValidator(0),
                validation.DynamicUpperBoundValidator(lambda: self._sq_size ** 2, inclusive=False)
            ), desc="Ensure the integer is between 0 and the total number of pixels"),
            in_type=int, out_type=int)
        low = validation.examples.any_int + validation.Pipeline(
            validation.Step(validation.RangeValidator(
                validation.LowerBoundValidator(0),
                validation.DynamicUpperBoundValidator(_low_max, inclusive=False)
            ), desc="Ensure the integer is between 0 and the 'high' value"),
            in_type=int, out_type=int)
        high = validation.examples.any_int + validation.Pipeline(
            validation.Step(validation.RangeValidator(
                validation.DynamicLowerBoundValidator(_high_min, inclusive=False),
                validation.DynamicUpperBoundValidator(lambda: self._sq_size)
            ), desc="Ensure the integer is between the 'low' value and the grid size"),
            in_type=int, out_type=int)

        raster_o = ("along x", "along y").index(default_settings["raster"]["orientation"])
        snake_o = ("along x", "along y").index(default_settings["snake"]["orientation"])
        spiral_o = ("outside-in", "inside-out").index(default_settings["spiral"]["orientation"])
        grid_o = (
            "row-major (++)", "row-major (-+)", "row-major (+-)", "row-major (--)", "column-major (++)",
            "column-major (-+)", "column-major (+-)", "column-major (--)"
        ).index(default_settings["grid"]["order"])
        self._raster = utils.ScanPattern(utils.Raster,
                                         skip=utils.Spinbox(default_settings["raster"]["skip"], 1, _gen_skip()),
                                         start=utils.Enum(images.AABBCorner,
                                                          images.AABBCorner[default_settings["raster"]["start"]]),
                                         orientation=utils.ComboBox("along x", "along y", start_i=raster_o),
                                         coverage=_gen_coverage(default_settings["raster"]["coverage"])
                                         )
        self._snake = utils.ScanPattern(utils.Snake, shortcut="N",
                                        skip=utils.Spinbox(default_settings["snake"]["skip"], 1, _gen_skip()),
                                        start=utils.Enum(images.AABBCorner,
                                                         images.AABBCorner[default_settings["snake"]["start"]]),
                                        orientation=utils.ComboBox("along x", "along y", start_i=snake_o),
                                        coverage=_gen_coverage(default_settings["snake"]["coverage"])
                                        )
        self._spiral = utils.ScanPattern(utils.Spiral, "Square Spiral", "Q",
                                         skip=utils.Spinbox(default_settings["spiral"]["skip"], 1, _gen_skip()),
                                         start=utils.Enum(images.AABBCorner,
                                                          images.AABBCorner[default_settings["spiral"]["start"]]),
                                         orientation=utils.ComboBox("outside-in", "inside-out", start_i=spiral_o),
                                         coverage=_gen_coverage(default_settings["spiral"]["coverage"])
                                         )
        self._grid = utils.ScanPattern(utils.Grid, "Sparse Grid", "G",
                                       gap=utils.SizeControl(default_settings["grid"]["gap"], 1,
                                                             _gen_skip(False)),
                                       shift=utils.SizeControl(default_settings["grid"]["shift"], 1,
                                                               _gen_skip()),
                                       order=utils.ComboBox("row-major (++)", "row-major (-+)", "row-major (+-)",
                                                            "row-major (--)", "column-major (++)", "column-major (-+)",
                                                            "column-major (+-)", "column-major (--)", start_i=grid_o),
                                       coverage=_gen_coverage(default_settings["grid"]["coverage"])
                                       )
        self._random = utils.ScanPattern(utils.Random, shortcut="O",
                                         r_type=utils.Enum(utils.RandomTypes,
                                                           utils.RandomTypes[default_settings["random"]["r_type"]]),
                                         n=utils.Spinbox(default_settings["random"]["n"], 5, n),
                                         coverage=_gen_coverage(default_settings["random"]["coverage"]),
                                         scale=utils.Spinbox(default_settings["random"]["scale"], 0.01,
                                                             validation.examples.positive_float),
                                         loc=utils.Spinbox(default_settings["random"]["loc"], 0.01,
                                                           validation.examples.any_float),
                                         lam=utils.Spinbox(default_settings["random"]["lam"], 10,
                                                           validation.examples.positive_float),
                                         low=utils.Spinbox(default_settings["random"]["low"], 1, low),
                                         high=utils.Spinbox(default_settings["random"]["high"], 1, high),
                                         )
        random_dict = self._random.to_dict()
        random_dict["r_type"].dataPassed.connect(_change_rand_type)
        _change_rand_type(random_dict["r_type"].get_data())

        start_res = ScanType.SIZES.index(default_settings["scan_resolution"])
        self._scan_resolution = utils.LabelledWidget("Upscaled Resolution",
                                                     utils.ComboBox(*ScanType.SIZES, start_i=start_res),
                                                     utils.LabelOrder.SUFFIX)
        self._scan_resolution.focus.dataPassed.connect(lambda v_: self.settingChanged.emit("scan_resolution", v_))
        self._scan_resolution.focus.dataFailed.connect(failure_action)

        self._regular.addWidget(self._scan_resolution)

        self._btns = widgets.QButtonGroup()
        patterns = (self._raster, self._snake, self._spiral, self._grid, self._random)
        for i, ptn in enumerate(patterns, 1):
            self._btns.addButton(ptn.button(), i)
            self._regular.addWidget(ptn)
            for v in ptn.to_dict().values():
                v.dataPassed.connect(lambda _: self._update())
                v.dataFailed.connect(failure_action)
        self._btns.idToggled.connect(functools.partial(self._draw, dict(enumerate(patterns, 1))))
        getattr(self, f"_{default_settings['selected']}").button().setChecked(True)

        self.setLayout(self._layout)

    def compile(self) -> str:
        return ""

    def run(self):
        pass

    def start(self):
        SettingsPage.start(self)
        CanvasPage.start(self)

    def stop(self):
        SettingsPage.stop(self)
        CanvasPage.stop(self)

    def clear(self):
        CanvasPage.clear(self)
        self._update()

    def change_size(self, new: int):
        """
        Change the square size, which updates all the co-ordinates of the selected pattern.

        Parameters
        ----------
        new: int
            The new size of the square. Note that the canvas size stays the same, therefore using smaller squares acts
            like an optical zoom.
        """
        self._sq_size = new
        self._update()

    def generate_pattern(self) -> np.ndarray:
        """
        Turns the scan pattern into a proper set of co-ordinates.

        Note that this function does not *yet* present the co-ordinates in a QD-friendly manner.

        Returns
        -------
        ndarray[int_, (n, 2)]
            An array of co-ordinates. Each co-ordinate is in the form (x, y).
        """
        return np.vstack([p.decode() for p in self._pattern.encode()])  # change to the encoded version

    def raster(self, argc: vals.Number, argv: _list[vals.Value]) -> objs.NativeClass:
        """
        Native function to represent the raster pattern.

        Parameters
        ----------
        argc: Number
            The number of arguments to provide. Is expected to match the number of parameters for the raster pattern.
        argv: list[Value]
            The value of the parameters. The order is maintained based on the raster pattern.

        Returns
        -------
        NativeClass
            A native instance of a particular pattern.
        """
        kwargs = ("skip", "start", "orientation", "coverage")
        if argc != (arge := len(kwargs)):
            raise TypeError(f"Expected {arge} arguments, got {argc}")
        args = dict(zip(kwargs, map(lambda x: x.raw, argv)))
        args["coverage"] = list(map(lambda x: x.raw, args["coverage"]))
        return objs.NativeClass(utils.Raster((self._sq_size, self._sq_size), **args))

    def snake(self, argc: vals.Number, argv: _list[vals.Value]) -> objs.NativeClass:
        """
        Native function to represent the snake pattern.

        Parameters
        ----------
        argc: Number
            The number of arguments to provide. Is expected to match the number of parameters for the snake pattern.
        argv: list[Value]
            The value of the parameters. The order is maintained based on the snake pattern.

        Returns
        -------
        NativeClass
            A native instance of a particular pattern.
        """
        kwargs = ("skip", "start", "orientation", "coverage")
        if argc != (arge := len(kwargs)):
            raise TypeError(f"Expected {arge} arguments, got {argc}")
        args = dict(zip(kwargs, map(lambda x: x.raw, argv)))
        args["coverage"] = list(map(lambda x: x.raw, args["coverage"]))
        return objs.NativeClass(utils.Snake((self._sq_size, self._sq_size), **args))

    def spiral(self, argc: vals.Number, argv: _list[vals.Value]) -> objs.NativeClass:
        """
        Native function to represent the spiral pattern.

        Parameters
        ----------
        argc: Number
            The number of arguments to provide. Is expected to match the number of parameters for the spiral pattern.
        argv: list[Value]
            The value of the parameters. The order is maintained based on the spiral pattern.

        Returns
        -------
        NativeClass
            A native instance of a particular pattern.
        """
        kwargs = ("skip", "start", "orientation", "coverage")
        if argc != (arge := len(kwargs)):
            raise TypeError(f"Expected {arge} arguments, got {argc}")
        args = dict(zip(kwargs, map(lambda x: x.raw, argv)))
        args["coverage"] = list(map(lambda x: x.raw, args["coverage"]))
        return objs.NativeClass(utils.Spiral((self._sq_size, self._sq_size), **args))

    def grid(self, argc: vals.Number, argv: _list[vals.Value]) -> objs.NativeClass:
        """
        Native function to represent the grid pattern.

        Parameters
        ----------
        argc: Number
            The number of arguments to provide. Is expected to match the number of parameters for the grid pattern.
        argv: list[Value]
            The value of the parameters. The order is maintained based on the grid pattern.

        Returns
        -------
        NativeClass
            A native instance of a particular pattern.
        """
        kwargs = ("gap", "shift", "order", "coverage")
        if argc != (arge := len(kwargs)):
            raise TypeError(f"Expected {arge} arguments, got {argc}")
        args = dict(zip(kwargs, map(lambda x: x.raw, argv)))
        args["gap"] = list(map(lambda x: x.raw, args["gap"]))
        args["shift"] = list(map(lambda x: x.raw, args["shift"]))
        args["coverage"] = list(map(lambda x: x.raw, args["coverage"]))
        return objs.NativeClass(utils.Grid((self._sq_size, self._sq_size), **args))

    def random(self, argc: vals.Number, argv: _list[vals.Value]) -> objs.NativeClass:
        """
        Native function to represent the random pattern.

        Parameters
        ----------
        argc: Number
            The number of arguments to provide. Is expected to match the number of parameters for the random pattern.
        argv: list[Value]
            The value of the parameters. The order is maintained based on the random pattern.

        Returns
        -------
        NativeClass
            A native instance of a particular pattern.
        """
        kwargs = ("r_type", "n", "coverage", "scale", "loc", "lam", "low", "high")
        if argc != (arge := len(kwargs)):
            raise TypeError(f"Expected {arge} arguments, got {argc}")
        args = dict(zip(kwargs, map(lambda x: x.raw, argv)))
        args["coverage"] = list(map(lambda x: x.raw, args["coverage"]))
        return objs.NativeClass(utils.Random((self._sq_size, self._sq_size), **args))

    def _draw(self, patterns: _dict[int, utils.ScanPattern], index: int, state: bool):
        if not state:
            return
        self._selected = patterns[index]
        self._update()

    def _update(self):
        if self._selected is None:
            return
        params = {k: v.get_data() for k, v in self._selected.to_dict().items()}
        self._pattern = self._selected.pattern()((self._sq_size, self._sq_size), **params)
        img = self._pattern.draw()
        o_h, o_w = img.shape
        n_w, n_h = self._canvas.image_size
        img = np.repeat(img, n_h // o_h, axis=0)
        img = np.repeat(img, n_w // o_w, axis=1)
        image = images.RGBImage(img.astype(np.int_)).downchannel(0, self._colour, invalid=images.ColourConvert.TO_FG)
        self._canvas.draw(image.upchannel())

    def all_settings(self) -> typing.Iterator[str]:
        yield from ("scan_resolution", "selected")

    def get_setting(self, name: str):
        if name == "selected":
            return self._pattern
        return super().get_setting(name)

    def set_setting(self, name: str, value):
        if name == "selected":
            for cls, pattern in zip(
                    (utils.Raster, utils.Snake, utils.Spiral, utils.Grid, utils.Random),
                    (self._raster, self._snake, self._spiral, self._grid, self._random)
            ):
                if isinstance(value, cls):
                    self._selected = pattern
                    p_dict = pattern.to_dict()
                    for prop, wid in p_dict.items():
                        self.setter(wid, value[prop])
                    break
        else:
            super().set_setting(name, value)

    def _process_tooltip(self, x: int, y: int) -> typing.Iterator[str]:
        if self._pattern is None:
            return
        yield f"<{x}, {y}>"
        scaled_x, scaled_y = map(int, np.interp([x, y], [0, self._canvas.image_size[0]], [0, self._sq_size]))
        if any((scaled_x, scaled_y) in (match := p) for i, p in enumerate(self._pattern.encode()) if (j := i) + 1):
            yield f"{j}:{match.index((scaled_x, scaled_y))}"

    def help(self) -> str:
        s = f"""This page allows for customising the scan pattern that is applied to each grid square.
        Various patterns are used to minimise beam damage while maximising data collected.
        
        Each pattern is divided into two categories: Continuous and Discrete.
        Continuous patterns will have a series of lines to scan (so that the probe positions are always adjacent);
        Discrete patterns will have a series of points to scan (so that the probe positions may not be adjacent)
        
        Most patterns have a flyback region where no data is collected; 
        but this allows the probe to do a discontinuous jump between pixels.
        
        Continuous Patterns:
        Raster - move the probe in parallel lines, with a flyback joining two lines at opposing corners.
        Snake - move the probe in alternating, parallel lines, with a flyback joining two lines at the same corner.
        Square Spiral - move the probe in perpendicular lines, decreasing the line length with each successful square.
        
        Discrete Patterns:
        Sparse Grid - a series of discrete points spaced evenly on a grid.
        Random - a series of discrete points distributed randomly, based on differing probability distributions.
        
        The two types of pattern have different requirements for flyback time: 
        Continuous patterns must decide a value that is large enough to cover the flyback time; 
        but not too large that non-flyback pixels are affected.
        Discrete patterns must decide a high enough value to consider each pixel as a flyback pixel.
        
        Settings
        --------
        Upscaled Resolution:
            {self._scan_resolution.focus.validation_pipe()}
            
            The new resolution to acquire the data in. Affects grid size (and therefore pattern size).
        
        For pattern parameters, see the help page"""
        return s

    def advanced_help(self) -> str:
        raster = {k: v.validation_pipe() for k, v in self._raster.to_dict().items()}
        snake = {k: v.validation_pipe() for k, v in self._snake.to_dict().items()}
        spiral = {k: v.validation_pipe() for k, v in self._spiral.to_dict().items()}
        grid = {k: v.validation_pipe() for k, v in self._grid.to_dict().items()}
        random = {k: v.validation_pipe() for k, v in self._random.to_dict().items()}
        s = f"""Raster:
            The raster pattern moves the probe in parallel lines, all going in one uniform direction.
            As flyback goes from line end to line start, this creates diagonal flyback lines.
            
            Settings
            --------
            Skip:
                {raster['skip']}
                
                The amount of lines to skip per flyback, meaning each line is `skip` + 1 pixels apart.
            Start:
                {raster['start']}
                
                The corner to start the scan from. This controls the direction of the scan in both x and y.
            orientation:
                {raster['orientation']}
                
                The direction of the scan - this controls whether it's a row or column scan.
            coverage:
                {raster['coverage']}
                
                The percentage of each grid square covered.
                    
        Snake:
            The snake pattern moves the probe in parallel lines, alternating directions each time.
            As flyback goes from line end to line start, this creates perpendicular flyback lines.
            
            Settings
            --------
            Skip:
                {snake['skip']}
                
                The amount of lines to skip per flyback, meaning each line is `skip` + 1 pixels apart.
            Start:
                {snake['start']}
                
                The corner to start the scan from. This controls the direction of the scan in both x and y.
            orientation:
                {snake['orientation']}
                
                The direction of the scan - this controls whether it's a row or column scan.
            coverage:
                {snake['coverage']}
                
                The percentage of each grid square covered.
        
        Square Spiral:
            The spiral pattern moves the probe in perpendicular lines, with alternating parallel lines.
            As the end of one line is the start of another, there is no flyback. 
            It will adjust the line size with each movement to avoid re-scanning areas. This creates a spiral pattern.
            
            Settings
            --------
            Skip:
                {spiral['skip']}
                
                The extra adjustment to line size. This creates more gap between each spiral coil.
            Start:
                {spiral['start']}
                
                The corner to start the scan from. This controls the direction of the scan in both x and y.
            orientation:
                {spiral['orientation']}
                
                The direction of the scan, controlling the origin of the spiral. 
                This differs from the `start` in that it controls the direction of each line independently; 
                also reversing their order of occurrence.
            coverage:
                {spiral['coverage']}
                
                The percentage of each grid square covered.
            
        Sparse Grid:
            The grid pattern places evenly distributed points over the square.
            Each pixel causes flyback pixels to the next one.
            
            Settings
            --------
            Gap:
                {grid['gap']}
                
                The spacing between each point.
            shift:
                {grid['shift']}
                
                The offset from the origin to begin the scan grid from.
            order:
                {grid['order']}
                
                The direction of the scan - this controls whether it's a row or column scan, and where it starts from.
                
                A row-major order states that the pixels are scanned horizontally.
                A column-major order states that the pixels are scanned vertically.
                
                A ++ order states that the row and column increase as x and y increase.
                A -+ order states that the row increases as y decreases, but column increases as x increases.
                A +- order states that the row increases as y increases, but column increases as x decreases.
                A -- order states that row and column increase and x and y decrease.
            coverage:
                {grid['coverage']}
                
                The percentage of each grid square covered. This can be combined with the shift to translate the grid.
        
        Random:
            The random pattern creates discrete points distributed randomly based on a particular distribution.
            
            Settings
            --------
            R type:
                {random['r_type']}
                
                The type of distribution used to generate points.
                
                EXP is a continuous version of geometric distribution.
                LAPLACE uses a Gaussian (NORMAL) distribution but with a sharper peak and fatter tails.
                LOGISTIC uses a mixture of Gumbel distributions and is commonly used in extreme value problems.
                NORMAL is a Gaussian distribution (a bell curve) and will most likely return samples near the mean.
                POISSON is the limit of binomial distribution.
                UNIFORM means that any value is equally likely to be drawn and does not include the end value.
            N:
                {random['n']}
                
                The maximum amount of points to generate. This can be violated if the points fall out of bounds.
            coverage:
                {random['coverage']}
                
                The percentage of each grid square covered.
                
            Scale:
                {random['scale']}
                
                In EXP mode, it is the inverse of the rate, where the rate describes the speed of events occurring.
                In LAPLACE mode, it is the exponential decay parameter.
                In LOGISTIC mode, it is the scale.
                In NORMAL mode, it is the standard deviation.
            
             Loc:
                {random['loc']}
                
                In LAPLACE mode, it is the location of the distribution's peak.
                In LOGISTIC mode, it is the mean.
                In NORMAL mode, it is the mean (or centre).
            Lam:
                {random['lam']}
                
                The lambda value in Poisson distribution. It is the expected number of events in a fixed-time interval.
            Low:
                {random['low']}
                
                The smallest value in the uniform distribution. It is included.
            High:
                {random['high']}
                
                The highest value in the uniform distribution. It is not included."""
        return s
