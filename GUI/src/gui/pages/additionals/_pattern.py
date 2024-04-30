import functools
import itertools
import typing
from typing import Dict as _dict, Set as _set, Tuple as _tuple

import numpy as np

from ... import utils
from ..._base import CanvasPage, images, SettingsPage, widgets
from .... import validation


class ScanType(CanvasPage, SettingsPage):
    settingChanged = SettingsPage.settingChanged
    SIZES = (256, 512, 1024, 2048, 4096, 8192, 16384)

    def __init__(self, size: int, pattern_colour: images.RGB, failure_action: typing.Callable[[Exception], None]):
        ScanType.SIZES = tuple(s for s in ScanType.SIZES if s > size)
        CanvasPage.__init__(self, size, movement_handler=lambda _: None)
        SettingsPage.__init__(self, utils.SettingsDepth.REGULAR)
        self._colour_option.hide()
        self._colour = pattern_colour
        divisions = 25
        self._scale = size // divisions
        self._chosen = ""
        self._offset = 5
        self._l = self._t = self._offset + 1
        self._b = self._r = size - self._offset - 1
        self._rng = np.random.default_rng()
        self._pattern: typing.Optional[np.ndarray] = None

        def _bounds(lower=True) -> validation.Step[int, int]:
            inclusive = "" if lower else ", and not including the lower bound"
            return validation.Step(
                validation.RangeValidator.known((0, divisions - 1), l_bound=lower, u_bound=False),
                desc=f"Ensure the input is between 0 and {divisions - 1}, not including the upper bound{inclusive}",
            )

        def _max_step() -> int:
            spiral = self._spiral.to_dict()
            growth_rate = spiral["growth_factor"].get_data()
            return min(10, divisions - (growth_rate * 4))

        def _low_max() -> int:
            random = self._random.to_dict()
            return random["high"].get_data()

        def _high_min() -> int:
            random = self._random.to_dict()
            return random["low"].get_data()

        def _gen_coverage() -> utils.XDControl[utils.PercentageBox]:
            return utils.XDControl(2, utils.PercentageBox, initial=100, pipeline=validation.examples.coverage, step=5)

        def _change_rand_type(new: utils.RandomTypes):
            for k, widget in random_dict.items():
                if k not in {"seed", "n", "type", "coverage", "under_handler", "over_handler"}:
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

        def _on_update():
            self._rng = np.random.default_rng()
            self._update()

        def _auto_switch(pattern: utils.ScanPattern):
            self._chosen = pattern.name()
            pattern.button().setChecked(True)
            self._update()

        spiral_step = validation.RangeValidator(validation.LowerBoundValidator(1),
                                                validation.DynamicUpperBoundValidator(_max_step, inclusive=False))
        skip_pipe = validation.Pipeline(_bounds(), in_type=int, out_type=int)
        check_pipe = validation.Pipeline(_bounds(False), in_type=int, out_type=int)
        spiral_pipe = validation.Pipeline(validation.Step(spiral_step,
                                                          desc="ensure the integer is between 1 and the "
                                                               "maximum step (based on parameters)"),
                                          in_type=int, out_type=int)
        uniform_l_step = validation.RangeValidator(validation.LowerBoundValidator(self._l),
                                                   validation.DynamicUpperBoundValidator(_low_max, inclusive=False))

        uniform_h_step = validation.RangeValidator(validation.DynamicLowerBoundValidator(_high_min, inclusive=False),
                                                   validation.UpperBoundValidator(self._r // self._scale))
        uniform_l_pipe = validation.Pipeline(validation.Step(uniform_l_step,
                                                             desc=f"ensure the integer is between {self._l} and the "
                                                                  "`high` setting"), in_type=int,
                                             out_type=int)
        uniform_h_pipe = validation.Pipeline(validation.Step(uniform_h_step,
                                                             desc=f"ensure the integer is between "
                                                                  f"{self._r // self._scale} and the `low` setting"),
                                             in_type=int, out_type=int)
        self._raster = utils.ScanPattern("Raster",
                                         start=utils.Enum(images.AABBCorner, images.AABBCorner.TOP_LEFT),
                                         coverage=_gen_coverage(),
                                         line_skip=utils.Spinbox(0, 1, skip_pipe),
                                         stroke_orientation=utils.ComboBox("along x", "along y")
                                         )
        self._snake = utils.ScanPattern("Snake", "N",
                                        start=utils.Enum(images.AABBCorner, images.AABBCorner.TOP_LEFT),
                                        coverage=_gen_coverage(),
                                        line_skip=utils.Spinbox(0, 1, skip_pipe),
                                        stroke_orientation=utils.ComboBox("along x", "along y")
                                        )
        self._spiral = utils.ScanPattern("Square Spiral", "Q",
                                         starting_length=utils.Spinbox(1, 1, spiral_pipe),
                                         x_order=utils.ComboBox("right -> left", "left -> right"),
                                         y_order=utils.ComboBox("up -> down", "down -> up"),
                                         growth_factor=utils.Spinbox(1, 1, spiral_pipe),
                                         coverage=_gen_coverage()
                                         )
        self._checkerboard = utils.ScanPattern("Sparse Grid", "G",
                                               gap=utils.XDControl(2, utils.Spinbox, initial=1, step=1,
                                                                   pipeline=check_pipe),
                                               coverage=_gen_coverage(),
                                               shift=utils.XDControl(2, utils.Spinbox, initial=0, step=1,
                                                                     pipeline=skip_pipe)
                                               )
        self._stairs = utils.ScanPattern("Stairway", "T",
                                         length=utils.XDControl(2, utils.Spinbox, initial=1, step=1,
                                                                pipeline=check_pipe),
                                         from_corner=utils.Enum(images.AABBCorner, images.AABBCorner.TOP_LEFT),
                                         shift=utils.XDControl(2, utils.Spinbox, initial=0, step=1,
                                                               pipeline=skip_pipe),
                                         coverage=_gen_coverage()
                                         )
        self._random = utils.ScanPattern("Random", "O", True,
                                         n=utils.Spinbox(10, 1, validation.examples.natural_int),
                                         under_handler=utils.Enum(utils.UnderflowHandler, utils.UnderflowHandler.DROP),
                                         over_handler=utils.Enum(utils.OverflowHandler, utils.OverflowHandler.DROP),
                                         coverage=_gen_coverage(),
                                         type=utils.Enum(utils.RandomTypes, utils.RandomTypes.UNIFORM),
                                         scale=utils.Spinbox(1, 0.01, validation.examples.positive_float),
                                         loc=utils.Spinbox(0, 0.01, validation.examples.any_float),
                                         lam=utils.Spinbox(0, 10, validation.examples.positive_float),
                                         low=utils.Spinbox(0, 1, validation.examples.any_int + uniform_l_pipe),
                                         high=utils.Spinbox(self._r // self._scale, 1,
                                                            validation.examples.any_int + uniform_h_pipe),
                                         )
        random_dict = self._random.to_dict()
        random_dict["type"].dataPassed.connect(_change_rand_type)
        _change_rand_type(utils.RandomTypes.UNIFORM)
        self._random.on_update(_on_update)
        # self._custom = utils.ScanPattern("Custom", "U",
        #                                  filepath=utils.Entry("", validation.examples.file_path, "%"),
        #                                  click_required=utils.CheckBox("", True)
        #                                  )

        self._scan_resolution = utils.LabelledWidget("Upscaled Resolution", utils.ComboBox(*ScanType.SIZES, start_i=-1),
                                                     utils.LabelOrder.SUFFIX)
        self._scan_resolution.focus.dataPassed.connect(lambda v_: self.settingChanged.emit("scan_resolution", v_))
        self._scan_resolution.focus.dataFailed.connect(failure_action)

        self._regular.addWidget(self._scan_resolution)

        self._selected = utils.ScanPatternGroup("raster", raster=self._raster, snake=self._snake,
                                                square_spiral=self._spiral, sparse_grid=self._checkerboard,
                                                stairway=self._stairs, random=self._random)
        self._selected.patternFailed.connect(failure_action)
        self._selected.newPattern.connect(_auto_switch)

        self._btns = widgets.QButtonGroup()
        patterns = (self._raster, self._snake, self._spiral, self._checkerboard, self._stairs, self._random)
        for i, ptn in enumerate(patterns, 1):
            self._btns.addButton(ptn.button(), i)
            self._regular.addWidget(ptn)
            for v in ptn.to_dict().values():
                v.dataPassed.connect(lambda _: self._update())
                v.dataFailed.connect(failure_action)
        self._btns.idToggled.connect(functools.partial(self._draw, dict(enumerate(patterns, 1))))
        self._raster.button().setChecked(True)

        self.setLayout(self._layout)

    def raster(self, _, start: images.AABBCorner, coverage: _tuple[float, float], line_skip: int,
               stroke_orientation: str) -> utils.ScanPattern:
        return self._set_selected(self._raster, start=start, coverage=coverage, line_skip=line_skip,
                                  stroke_orientation=stroke_orientation)

    def snake(self, _, start: images.AABBCorner, coverage: _tuple[float, float], line_skip: int,
              stroke_orientation: str) -> utils.ScanPattern:
        return self._set_selected(self._snake, start=start, coverage=coverage, line_skip=line_skip,
                                  stroke_orientation=stroke_orientation)

    def spiral(self, _, starting_length: int, x_order: str, y_order: str, growth_factor: float,
               coverage: _tuple[float, float]) -> utils.ScanPattern:
        return self._set_selected(self._spiral, starting_length=starting_length, x_order=x_order, y_order=y_order,
                                  growth_factor=growth_factor, coverage=coverage)

    def checkerboard(self, _, gap: _tuple[int, int], coverage: _tuple[float, float],
                     shift: _tuple[int, int]) -> utils.ScanPattern:
        return self._set_selected(self._checkerboard, gap=gap, coverage=coverage, shift=shift)

    def stairs(self, _, length: _tuple[int, int], from_corner: images.AABBCorner, shift: _tuple[int, int],
               coverage: _tuple[float, float]) -> utils.ScanPattern:
        return self._set_selected(self._stairs, length=length, from_corner=from_corner, coverage=coverage,
                                  shift=shift)

    def random(self, _, n: int, under_handler: utils.UnderflowHandler, over_handler: utils.OverflowHandler,
               coverage: _tuple[float, float], type_: utils.RandomTypes, scale: float, loc: float, lam: float, low: int,
               high: int) -> utils.ScanPattern:
        return self._set_selected(self._stairs, n=n, under_handler=under_handler, over_handler=over_handler,
                                  coverage=coverage, type=type_, scale=scale, loc=loc, lam=lam, low=low, high=high)

    @staticmethod
    def _set_selected(pattern: utils.ScanPattern, **kwargs):
        pattern_dict = pattern.to_dict()
        for k, v in kwargs.items():
            SettingsPage.setter(pattern_dict[k], v)
        return pattern

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

    def get_pattern(self) -> np.ndarray:
        return self._pattern  # convert to encoded version

    def _draw(self, patterns: _dict[int, utils.ScanPattern], index: int, state: bool):
        if not state:
            return
        self._chosen = patterns[index].name()
        self._selected.select(patterns[index])

    def _update(self):
        img = images.RGBImage.blank(self._canvas.image_size)
        # if self._chosen == "Custom":
        #     grid = ~self._colour
        #     for x in range(self._l, self._r + 1, self._scale):
        #         img.drawing.line((x, self._t), (x, self._b), grid)
        #     for y in range(self._t, self._b + 1, self._scale):
        #         img.drawing.line((self._l, y), (self._r, y), grid)
        #     self._custom_pattern(img)
        if self._chosen == "Raster":
            self._raster_pattern(img)
        elif self._chosen == "Snake":
            self._snake_pattern(img)
        elif self._chosen == "Square Spiral":
            self._spiral_pattern(img)
        elif self._chosen == "Sparse Grid":
            self._grid_pattern(img)
        elif self._chosen == "Stairway":
            self._stair_pattern(img)
        elif self._chosen == "Random":
            self._random_pattern(img)
        self._canvas.draw(img)

    def _raster_pattern(self, img: images.RGBImage):
        co_ord_pattern: _set[_tuple[int, int]] = set()
        raster = self._raster.to_dict()
        skip: int = raster["line_skip"].get_data()
        start: images.AABBCorner = raster["start"].get_data()
        orientation: str = raster["stroke_orientation"].get_data()
        x_cov, y_cov = raster["coverage"].get_data()
        jump = int(self._scale + (skip * self._scale))
        if start.x() == "left":
            s_x = self._l
            e_x = int(self._r * x_cov)
            x_mov = 1
            h_arr = "right"
        else:
            s_x = self._r
            e_x = int(self._r * (1 - x_cov)) + self._l
            x_mov = -1
            h_arr = "left"

        if start.y() == "top":
            s_y = self._t
            e_y = int(self._b * y_cov)
            y_mov = 1
            v_arr = "down"
        else:
            s_y = self._b
            e_y = int(self._b * (1 - y_cov)) + self._t
            y_mov = -1
            v_arr = "up"

        if orientation == "along x":
            centre = min(s_x, e_x) + max(e_x, s_x) // 2
            position = [s_y, y_mov]

            def _stroke(y: int):
                img.drawing.line((s_x, y), (e_x, y), self._colour, co_ords=co_ord_pattern)
                self._arrow(img, (centre, y), h_arr)

            def _flyback(y: int):
                if _active(y + jump * y_mov):
                    img.drawing.line((e_x, y), (s_x, y + jump * y_mov), self._colour)
                    self._arrow(img, (centre, y + (jump * y_mov) // 2), v_arr)

            def _active(y: int = None) -> bool:
                if y is None:
                    y = position[0]
                return min(s_y, e_y) <= y <= max(e_y, s_y)
        else:
            centre = min(s_x, e_x) + max(e_x, s_x) // 2
            position = [s_x, x_mov]

            def _stroke(x: int):
                img.drawing.line((x, s_y), (x, e_y), self._colour, co_ords=co_ord_pattern)
                self._arrow(img, (x, centre), v_arr)

            def _flyback(x: int):
                if _active(x + jump * x_mov):
                    img.drawing.line((x, e_y), (x + jump * x_mov, s_y), self._colour)
                    self._arrow(img, (x + (jump * x_mov) // 2, centre), h_arr)

            def _active(x: int = None) -> bool:
                if x is None:
                    x = position[0]
                return min(s_x, e_x) <= x <= max(e_x, s_x)

        while _active():
            _stroke(position[0])
            _flyback(position[0])
            position[0] += jump * position[1]
        self._pattern = np.array(list(co_ord_pattern))

    def _snake_pattern(self, img: images.RGBImage):
        co_ord_pattern: _set[_tuple[int, int]] = set()
        snake = self._snake.to_dict()
        skip: int = snake["line_skip"].get_data()
        start: images.AABBCorner = snake["start"].get_data()
        orientation: str = snake["stroke_orientation"].get_data()
        x_cov, y_cov = snake["coverage"].get_data()
        jump = int(self._scale + (skip * self._scale))
        if start.x() == "left":
            s_x = self._l
            e_x = int(self._r * x_cov)
            x_mov = 1
            h_arrs = itertools.cycle(("right", "left"))
        else:
            s_x = self._r
            e_x = int(self._r * (1 - x_cov)) + self._l
            x_mov = -1
            h_arrs = itertools.cycle(("left", "right"))

        if start.y() == "top":
            s_y = self._t
            e_y = int(self._b * y_cov)
            y_mov = 1
            v_arrs = itertools.cycle(("down", "up"))
        else:
            s_y = self._b
            e_y = int(self._b * (1 - y_cov)) + self._t
            y_mov = -1
            v_arrs = itertools.cycle(("up", "down"))

        h_points = itertools.cycle((e_x, s_x))
        v_points = itertools.cycle((e_y, s_y))
        if orientation == "along x":
            centre = min(s_x, e_x) + max(e_x, s_x) // 2
            position = [s_y, y_mov]
            v_arrs = itertools.cycle((next(v_arrs),))

            def _stroke(y: int):
                img.drawing.line((s_x, y), (e_x, y), self._colour)
                x_range = range(s_x, e_x, x_mov) if (h_dir := next(h_arrs)) == "right" else range(e_x, s_x, -x_mov)
                co_ord_pattern.update((_x, y) for _x in x_range)
                self._arrow(img, (centre, y), h_dir)

            def _flyback(y: int):
                if _active(y + jump * y_mov):
                    x = next(h_points)
                    img.drawing.line((x, y), (x, y + jump * y_mov), self._colour)
                    co_ord_pattern.update((x, _y) for _y in range(y, y + jump * y_mov, y_mov))
                    self._arrow(img, (x, y + (jump * y_mov) // 2), next(v_arrs))

            def _active(y: int = None) -> bool:
                if y is None:
                    y = position[0]
                return min(s_y, e_y) <= y <= max(e_y, s_y)
        else:
            centre = min(s_y, e_y) + max(e_y, s_y) // 2
            position = [s_x, x_mov]
            h_arrs = itertools.cycle((next(h_arrs),))

            def _stroke(x: int):
                img.drawing.line((x, s_y), (x, e_y), self._colour)
                y_range = range(s_y, e_y, y_mov) if (v_dir := next(v_arrs)) == "down" else range(e_y, s_y, -y_mov)
                co_ord_pattern.update((x, _y) for _y in y_range)
                self._arrow(img, (x, centre), v_dir)

            def _flyback(x: int):
                if _active(x + jump * x_mov):
                    y = next(v_points)
                    img.drawing.line((x, y), (x + jump * x_mov, y), self._colour)
                    co_ord_pattern.update((_x, y) for _x in range(x, x + jump * x_mov, x_mov))
                    self._arrow(img, (x + (jump * x_mov) // 2, y), next(h_arrs))

            def _active(x: int = None) -> bool:
                if x is None:
                    x = position[0]
                return min(s_x, e_x) <= x <= max(e_x, s_x)

        while _active():
            _stroke(position[0])
            _flyback(position[0])
            position[0] += jump * position[1]
        self._pattern = np.array(list(co_ord_pattern))

    def _spiral_pattern(self, img: images.RGBImage):
        co_ord_pattern: _set[_tuple[int, int]] = set()
        spiral = self._spiral.to_dict()
        length = int(spiral["starting_length"].get_data() * self._scale)
        growth = int(spiral["growth_factor"].get_data() * self._scale)
        x_order = spiral["x_order"].get_data().split(" -> ")
        y_order = spiral["y_order"].get_data().split(" -> ")
        x_cov, y_cov = spiral["coverage"].get_data()
        if x_cov == y_cov == 1:
            img.drawing.spiral((self._l + self._r // 2, self._t + self._b // 2), length, self._colour,
                               growth=growth, x_order=x_order, y_order=y_order, co_ords=co_ord_pattern)
        else:
            new_w, new_h = int(x_cov * self._r), int(y_cov * self._b)
            new_img = img.region((self._l, self._t), (self._l + new_w - 1, self._t + new_h - 1))
            data = img.image()
            img_w, img_h = new_img.size
            new_img.drawing.spiral((img_w // 2 - 1, img_h // 2 - 1), length, self._colour,
                                   growth=growth, x_order=x_order, y_order=y_order, co_ords=co_ord_pattern)
            data[self._t:new_h + self._t, self._l:new_w + self._r] = new_img.image()
        self._pattern = np.array(list(co_ord_pattern))

    def _grid_pattern(self, img: images.RGBImage):
        data = img.image.reference()
        board = self._checkerboard.to_dict()
        x_gap, y_gap = map(lambda d: int(d * self._scale), board["gap"].get_data())
        x_cov, y_cov = board["coverage"].get_data()
        x_shift, y_shift = map(lambda d: int(d * self._scale), board["shift"].get_data())
        only_ys, only_xs = np.meshgrid(np.arange(self._t + y_shift, int(self._b * y_cov) + y_shift + 1, y_gap),
                                       np.arange(self._l + x_shift, int(self._r * x_cov) + x_shift + 1, x_gap)
                                       )
        valid_ys = only_ys <= self._b
        only_ys = only_ys[valid_ys]
        only_xs = only_xs[valid_ys]
        valid_xs = only_xs <= self._r
        only_ys = only_ys[valid_xs]
        only_xs = only_xs[valid_xs]
        for i in range(self._offset + 1):
            data[only_ys - i, only_xs + i] = self._colour.items(images.RGBOrder.BGR)
            data[only_ys - i, only_xs - i] = self._colour.items(images.RGBOrder.BGR)
            data[only_ys + i, only_xs + i] = self._colour.items(images.RGBOrder.BGR)
            data[only_ys + i, only_xs - i] = self._colour.items(images.RGBOrder.BGR)
        self._pattern = np.array(list({(x, y) for y, x in zip(only_ys, only_xs)}))

    def _stair_pattern(self, img: images.RGBImage):
        co_ord_pattern: _set[_tuple[int, int]] = set()
        stair = self._stairs.to_dict()
        x_length, y_length = map(lambda d: int(d * self._scale), stair["length"].get_data())
        corner = stair["from_corner"].get_data()
        x_cov, y_cov = stair["coverage"].get_data()
        x_shift, y_shift = map(lambda d: int(d * self._scale), stair["shift"].get_data())
        if corner.x() == "left":
            s_x = self._l + x_shift
            e_x = int(self._r * x_cov) + x_shift
            h_arr = "right"
        else:
            s_x = self._r - x_shift
            e_x = int(self._r * (1 - x_cov)) + self._l - x_shift
            x_length *= -1
            h_arr = "left"

        if corner.y() == "top":
            s_y = self._t + y_shift
            e_y = int(self._b * y_cov) + y_shift
            v_arr = "down"
        else:
            s_y = self._b - y_shift
            e_y = int(self._b * (1 - y_cov)) + self._t - y_shift
            y_length *= -1
            v_arr = "up"

        c_x, c_y = s_x, s_y
        while min(s_x, e_x) <= c_x <= max(e_x, s_x) and min(s_y, e_y) <= c_y <= max(e_y, s_y):
            if c_x + x_length > self._r or c_y + x_length > self._b:
                break
            img.drawing.line((c_x, c_y), (c_x + x_length, c_y), self._colour, co_ords=co_ord_pattern)
            c_x += x_length
            self._arrow(img, (c_x - x_length // 2, c_y), h_arr)
            img.drawing.line((c_x, c_y), (c_x, c_y + y_length), self._colour, co_ords=co_ord_pattern)
            c_y += y_length
            self._arrow(img, (c_x, c_y - y_length // 2), v_arr)
        self._pattern = np.array(list(co_ord_pattern))

    def _random_pattern(self, img: images.RGBImage):
        random = self._random.to_dict()
        r_type = random["type"].get_data()
        pairs = random["n"].get_data()
        under = random["under_handler"].get_data()
        over = random["over_handler"].get_data()
        x_cov, y_cov = random["coverage"].get_data()
        max_x, max_y = int(self._r * x_cov), int(self._b * y_cov)
        generator = self._rng
        if r_type == utils.RandomTypes.EXP:
            scale = random["scale"].get_data()
            points = generator.exponential(scale, pairs * 2)
        elif r_type in {utils.RandomTypes.LAPLACE, utils.RandomTypes.LOGISTIC, utils.RandomTypes.NORMAL}:
            scale = random["scale"].get_data()
            loc = random["loc"].get_data()
            if r_type == utils.RandomTypes.LAPLACE:
                dist = generator.laplace
            elif r_type == utils.RandomTypes.LOGISTIC:
                dist = generator.logistic
            elif r_type == utils.RandomTypes.NORMAL:
                dist = generator.normal
            else:
                raise RuntimeError(f"Unhandled case {r_type}")
            points = dist(loc, scale, pairs * 2)
        elif r_type == utils.RandomTypes.POISSON:
            lam = random["lam"].get_data()
            points = generator.poisson(lam, pairs * 2)
        else:
            low = random["low"].get_data()
            high = random["high"].get_data()
            points = generator.uniform(low, high, pairs * 2).astype(np.int_)
        if points.dtype == np.float64:
            powers = np.log10(np.abs(points)).astype(np.int_)
            max_dec = np.abs(np.min(powers))
            points = (points * 10 ** max_dec).astype(np.int_)

        points = (points.reshape(-1, 2) + self._l) * self._scale
        if under == utils.UnderflowHandler.DROP:
            y_mask = np.where(points[:, 0] >= self._t, 1, 0)
            x_mask = np.where(points[:, 1] >= self._l, 1, 0)
            mask = y_mask & x_mask
            points = points[np.nonzero(mask)]
        elif under == utils.UnderflowHandler.TRUNCATE:
            y_mask = np.where(points[:, 0] < self._t, 1, 0)
            points[np.nonzero(y_mask)] = self._t
            x_mask = np.where(points[:, 1] < self._l, 1, 0)
            points[np.nonzero(x_mask)] = self._l
        elif under == utils.UnderflowHandler.ABS:
            points = np.abs(points)
        if over == utils.OverflowHandler.DROP:
            y_mask = np.where(points[:, 0] <= max_y, 1, 0)
            x_mask = np.where(points[:, 1] <= max_x, 1, 0)
            mask = y_mask & x_mask
            points = points[np.nonzero(mask)]
        elif over == utils.OverflowHandler.TRUNCATE:
            y_mask = np.where(points[:, 0] > max_y, 1, 0)
            points[np.nonzero(y_mask)] = max_y
            x_mask = np.where(points[:, 1] > max_x, 1, 0)
            points[np.nonzero(x_mask)] = max_x
        elif over == utils.OverflowHandler.MODULO:
            y_mask = np.nonzero(np.where(points[:, 0] > max_y, 1, 0))
            points[y_mask] %= max_y
            points[y_mask] += self._t
            x_mask = np.nonzero(np.where(points[:, 0] > max_x, 1, 0))
            points[x_mask] %= max_x
            points[x_mask] += self._l

        only_ys = points[:, 0]
        only_xs = points[:, 1]
        data = img.image.reference()
        for i in range(self._offset + 1):
            data[only_ys + i, only_xs + i] = self._colour.items(images.RGBOrder.BGR)
            data[only_ys + i, only_xs - i] = self._colour.items(images.RGBOrder.BGR)
            data[only_ys - i, only_xs + i] = self._colour.items(images.RGBOrder.BGR)
            data[only_ys - i, only_xs - i] = self._colour.items(images.RGBOrder.BGR)
        self._pattern = np.array(list({(x, y) for y, x in zip(only_ys, only_xs)}))

    def _arrow(self, img: images.RGBImage, position: _tuple[int, int], pointing: str):
        x, y = position
        if pointing == "right":
            img.drawing.line(position, (x - self._offset, y - self._offset), self._colour)
            img.drawing.line(position, (x - self._offset, y + self._offset), self._colour)
        elif pointing == "left":
            img.drawing.line(position, (x + self._offset, y - self._offset), self._colour)
            img.drawing.line(position, (x + self._offset, y + self._offset), self._colour)
        elif pointing == "up":
            img.drawing.line(position, (x - self._offset, y + self._offset), self._colour)
            img.drawing.line(position, (x + self._offset, y + self._offset), self._colour)
        elif pointing == "down":
            img.drawing.line(position, (x - self._offset, y - self._offset), self._colour)
            img.drawing.line(position, (x + self._offset, y - self._offset), self._colour)

    def all_settings(self) -> typing.Iterator[str]:
        yield from ("scan_resolution", "selected")

    def help(self) -> str:
        s = f"""This page allows for changing the way that each grid square is scanned.

        A scan pattern can be chosen and customised, allowing for beam damage to be lessened;
        while still obtaining useful data.

        The available patterns are:
            Raster - move across and then back to origin.
            Snake - move across, then invert direction.
            Square Spiral - move in a square, increasing line length every corner.
            Sparse Grid - discrete points, spaced evenly.
            Stairway - travel from one corner to the opposite by alternating x/y lines.
            Random - discrete points, distributed based on a particular probability distribution.
        
        Some are 'line' patterns (Raster, Snake, Spiral, Stairs) which move the probe in a continuous fashion;
        some are 'point' patterns (Grid, Random) which move the probe to discrete co-ordinates.
        
        All point patterns must take flyback into consideration more heavily than line patterns.
        
        Settings
        --------
        Upscaled Resolution:
            {self._scan_resolution.focus.validation_pipe()}
            
            The new resolution to acquire the data in. 

        For configuring the patterns, see the help page."""
        return s

    def advanced_help(self) -> str:
        raster = {k: v.validation_pipe() for k, v in self._raster.to_dict().items()}
        snake = {k: v.validation_pipe() for k, v in self._snake.to_dict().items()}
        spiral = {k: v.validation_pipe() for k, v in self._spiral.to_dict().items()}
        grid = {k: v.validation_pipe() for k, v in self._checkerboard.to_dict().items()}
        stair = {k: v.validation_pipe() for k, v in self._stairs.to_dict().items()}
        random = {k: v.validation_pipe() for k, v in self._random.to_dict().items()}
        s = f"""Raster:
                The raster pattern will move the probe continuously along its stroke direction;
                then move against this direction while moving back the way it came (returning to origin).
                
                This has the effect of scanning a new line, from the same point, every time.
                The probe does not scan while moving to origin.
                
                Settings
                --------
                Start:
                    {raster['start']}
                    
                    The corner from which to start the scan from. This controls the x and y directions.
                Coverage:
                    {raster['coverage']}
                    
                    The percentage of each grid square covered.
                Line Skip:
                    {raster['line_skip']}
                    
                    The amount of extra deviation to have when moving back to origin.
                Stroke Orientation:
                    {raster['stroke_orientation']}
                    
                    The direction of the "long" movement. This is the direction to move in while scanning.
                    
        Snake:
            The snake pattern will move the probe continuously along its stroke direction;
            then move against this direction. This requires it to reverse the direction it came for the next line. 
            
            This has the effect of scanning a new line, from alternating points, every time.
            The probe does not scan while moving against the stroke direction.
            
            Settings
            --------
            Start:
                {snake['start']}
                
                The corner from which to start the scan from. This controls the x and y directions.
            Coverage:
                {snake['coverage']}
                
                The percentage of each grid square covered.
            Line Skip:
                {snake['line_skip']}
                
                The amount of extra deviation to have when moving against the stroke.
            Stroke Orientation:
                {snake['stroke_orientation']}
                
                The direction of the "long" movement. This is the direction to move in while scanning.
                
        Square Spiral:
            The spiral pattern will move the probe in the first x direction;
            then internally increase the length of the line by 1.
            Then, it will do the same thing for the first y direction.
            The next two steps are repeating this using the last x and y directions.
            
            This means that one full turn will end up further in the last x-direction and the last y-direction;
            before it's ready to begin the cycle again. The algorithm is constrained such that;
            if a full turn cannot be made, it is not *drawn*.
            
            Settings
            --------
            Starting Length:
                {spiral['starting_length']}
                
                The initial line length.
            X Order:
                {spiral['x_order']}
                
                The horizontal order of probe movement. This will be steps 1 and 3 per turn.
            Y Order:
                {spiral['y_order']}
                
                The vertical order of probe movement. This will be steps 2 and 4 per turn.
            Growth Factor:
                {spiral['growth_factor']}
                
                The rate of growth for the line. This is how much the line increases its length by.
            Coverage:
                {snake['coverage']}
                
                The percentage of each grid square covered.
                
        Sparse Grid:
            The pattern places evenly distributed discrete points and will move the probe to each one.
            Scanning only takes place during the static probe moments.
            
            Settings
            --------
            Gap:
                {grid['gap']}
                
                The spacing between each discrete point.
            Coverage:
                {grid['coverage']}
                
                The percentage of each grid square covered.
            Shift:
                {grid['shift']}
                
                The deviation from the origin the starting point is on.
        Stairway:
            The pattern will alternate between an x-line and a y-line in order to traverse from one corner to the other.
            
            Settings
            --------
            Length
                {stair['length']}
                
                The length of the lines to draw.
            
            From Corner
                {stair['from_corner']}
                
                The starting corner. This will control the x and y directions.
            Shift:
                {stair['shift']}
                
                The deviation from the corner to start from.
            Coverage:
                {stair['coverage']}
                
                The percentage of each grid square covered.
        
        Random:
            This pattern will place discrete points at random co-ordinates, decided by a particular distribution.
            
            Settings
            --------
            N
                {random['n']}
                
                The maximum number of grid points to place. This number is only violated from "DROP" handlers.
            Under Handler
                {random['under_handler']}
                
                How to handle points that are randomly selected below the minimum bounds of the square.
                DROP implies to remove then from the list of points;
                TRUNCATE implies to make them the minimum value;
                ABS implies to turn them to their absolute value (and let the overflow handler handle it if required).
            Over Handler
                {random['over_handler']}
                
                How to handle points that are randomly selected below the minimum bounds of the square.
                DROP implies to remove then from the list of points;
                TRUNCATE implies to make them the maximum value;
                MODULO implies to wrap it around the maximum using a modulo operation.            
            Coverage:
                {random['coverage']}
                
                The percentage of each grid square covered.
            Type:
                {random['type']}
                
                The distribution to use. Switching distributions will change which settings are available.
                
                EXP is a continuous version of geometric distribution.
                LAPLACE uses a Gaussian (NORMAL) distribution but with a sharper peak and fatter tails.
                LOGISTIC uses a mixture of Gumbel distributions and is commonly used in extreme value problems.
                NORMAL is a Gaussian distribution (a bell curve) and will most likely return samples near the mean.
                POISSON is the limit of binomial distribution.
                UNIFORM means that any value is equally likely to be drawn and does not include the end value.
            Scale:
                {random['scale']}
                
                A multi-distribution variable.
                
                In EXP mode, it is the inverse of the rate, where the rate describes the speed of events occurring.
                In LAPLACE mode, it is the exponential decay parameter.
                In LOGISTIC mode, it is the scale.
                In NORMAL mode, it is the standard deviation.
            Loc:
                {random['loc']}
                
                A multi-distibution variable.
                
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
