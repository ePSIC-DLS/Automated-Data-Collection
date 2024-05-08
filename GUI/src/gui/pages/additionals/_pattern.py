import functools
import itertools
import typing
from typing import Dict as _dict, Set as _set, Tuple as _tuple, List as _list, Optional as _None

import numpy as np

from ... import utils
from ..._base import CanvasPage, images, SettingsPage, widgets
from .... import validation
from ....language.utils import vals, objs


class ScanType(CanvasPage, SettingsPage):
    settingChanged = SettingsPage.settingChanged
    SIZES = (256, 512, 1024, 2048, 4096, 8192, 16384)

    def __init__(self, size: int, pattern_colour: images.RGB, failure_action: typing.Callable[[Exception], None]):
        ScanType.SIZES = tuple(s for s in ScanType.SIZES if s > size)
        CanvasPage.__init__(self, size)
        SettingsPage.__init__(self, utils.SettingsDepth.REGULAR)
        self._colour_option.hide()
        self._colour = pattern_colour
        self._sq_size = 256
        self._pattern: _None[utils.Design] = None
        self._selected: _None[utils.ScanPattern] = None

        def _gen_coverage() -> utils.XDControl:
            return utils.XDControl(2, utils.PercentageBox, initial=100, pipeline=validation.examples.coverage, step=5)

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

        self._raster = utils.ScanPattern(utils.Raster,
                                         skip=utils.Spinbox(0, 1, _gen_skip()),
                                         start=utils.Enum(images.AABBCorner, images.AABBCorner.TOP_LEFT),
                                         orientation=utils.ComboBox("along x", "along y"),
                                         coverage=_gen_coverage()
                                         )
        self._snake = utils.ScanPattern(utils.Snake, shortcut="N",
                                        skip=utils.Spinbox(0, 1, _gen_skip()),
                                        start=utils.Enum(images.AABBCorner, images.AABBCorner.TOP_LEFT),
                                        orientation=utils.ComboBox("along x", "along y"),
                                        coverage=_gen_coverage()
                                        )
        self._spiral = utils.ScanPattern(utils.Spiral, "Square Spiral", "Q",
                                         skip=utils.Spinbox(0, 1, _gen_skip()),
                                         start=utils.Enum(images.AABBCorner, images.AABBCorner.TOP_LEFT),
                                         orientation=utils.ComboBox("outside-in", "inside-out"),
                                         coverage=_gen_coverage()
                                         )
        self._checkerboard = utils.ScanPattern(utils.Grid, "Sparse Grid", "G",
                                               gap=utils.SizeControl(1, 1, _gen_skip(False)),
                                               shift=utils.SizeControl(0, 1, _gen_skip()),
                                               order=utils.ComboBox("row-major (++)", "row-major (-+)",
                                                                    "row-major (+-)", "row-major (--)",
                                                                    "column-major (++)", "column-major (-+)",
                                                                    "column-major (+-)", "column-major (--)"),
                                               coverage=_gen_coverage()
                                               )
        self._random = utils.ScanPattern(utils.Random, shortcut="O",
                                         r_type=utils.Enum(utils.RandomTypes, utils.RandomTypes.UNIFORM),
                                         n=utils.Spinbox(20, 5, n),
                                         coverage=_gen_coverage(),
                                         scale=utils.Spinbox(1, 0.01, validation.examples.positive_float),
                                         loc=utils.Spinbox(0, 0.01, validation.examples.any_float),
                                         lam=utils.Spinbox(0, 10, validation.examples.positive_float),
                                         low=utils.Spinbox(0, 1, low),
                                         high=utils.Spinbox(self._sq_size, 1, high),
                                         )
        random_dict = self._random.to_dict()
        random_dict["r_type"].dataPassed.connect(_change_rand_type)
        _change_rand_type(utils.RandomTypes.UNIFORM)

        self._scan_resolution = utils.LabelledWidget("Upscaled Resolution", utils.ComboBox(*ScanType.SIZES, start_i=-1),
                                                     utils.LabelOrder.SUFFIX)
        self._scan_resolution.focus.dataPassed.connect(lambda v_: self.settingChanged.emit("scan_resolution", v_))
        self._scan_resolution.focus.dataFailed.connect(failure_action)

        self._regular.addWidget(self._scan_resolution)

        self._btns = widgets.QButtonGroup()
        patterns = (self._raster, self._snake, self._spiral, self._checkerboard, self._random)
        for i, ptn in enumerate(patterns, 1):
            self._btns.addButton(ptn.button(), i)
            self._regular.addWidget(ptn)
            for v in ptn.to_dict().values():
                v.dataPassed.connect(lambda _: self._update())
                v.dataFailed.connect(failure_action)
        self._btns.idToggled.connect(functools.partial(self._draw, dict(enumerate(patterns, 1))))
        self._raster.button().setChecked(True)

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
        self._sq_size = new
        self._update()

    def generate_pattern(self) -> np.ndarray:
        return np.vstack([p.decode() for p in self._pattern.encode()])  # change to encoded version

    def raster(self, argc: vals.Number, argv: _list[vals.Value]) -> objs.NativeClass:
        kwargs = ("skip", "start", "orientation", "coverage")
        if argc != (arge := len(kwargs)):
            raise TypeError(f"Expected {arge} arguments, got {argc}")
        args = dict(zip(kwargs, map(lambda x: x.raw, argv)))
        args["coverage"] = list(map(lambda x: x.raw, args["coverage"]))
        return objs.NativeClass(utils.Raster((self._sq_size, self._sq_size), **args))

    def snake(self, argc: vals.Number, argv: _list[vals.Value]) -> objs.NativeClass:
        kwargs = ("skip", "start", "orientation", "coverage")
        if argc != (arge := len(kwargs)):
            raise TypeError(f"Expected {arge} arguments, got {argc}")
        args = dict(zip(kwargs, map(lambda x: x.raw, argv)))
        args["coverage"] = list(map(lambda x: x.raw, args["coverage"]))
        return objs.NativeClass(utils.Snake((self._sq_size, self._sq_size), **args))

    def spiral(self, argc: vals.Number, argv: _list[vals.Value]) -> objs.NativeClass:
        kwargs = ("skip", "start", "orientation", "coverage")
        if argc != (arge := len(kwargs)):
            raise TypeError(f"Expected {arge} arguments, got {argc}")
        args = dict(zip(kwargs, map(lambda x: x.raw, argv)))
        args["coverage"] = list(map(lambda x: x.raw, args["coverage"]))
        return objs.NativeClass(utils.Spiral((self._sq_size, self._sq_size), **args))

    def grid(self, argc: vals.Number, argv: _list[vals.Value]) -> objs.NativeClass:
        kwargs = ("gap", "shift", "order", "coverage")
        if argc != (arge := len(kwargs)):
            raise TypeError(f"Expected {arge} arguments, got {argc}")
        args = dict(zip(kwargs, map(lambda x: x.raw, argv)))
        args["gap"] = list(map(lambda x: x.raw, args["gap"]))
        args["shift"] = list(map(lambda x: x.raw, args["shift"]))
        args["coverage"] = list(map(lambda x: x.raw, args["coverage"]))
        return objs.NativeClass(utils.Grid((self._sq_size, self._sq_size), **args))

    def random(self, argc: vals.Number, argv: _list[vals.Value]) -> objs.NativeClass:
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
        image = images.GreyImage(img).promote()
        try:
            image.replace(images.Grey(255), self._colour)
        except ValueError:
            pass
        self._canvas.draw(image)

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
                    (self._raster, self._snake, self._spiral, self._checkerboard, self._random)
            ):
                pattern: utils.ScanPattern = pattern
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
        grid = {k: v.validation_pipe() for k, v in self._checkerboard.to_dict().items()}
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
