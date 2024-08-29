import itertools
import typing
from typing import Tuple as _tuple

from . import _image as imgs
from ._enums import *
from ._img_mask import Grid


class Settings(typing.TypedDict):
    """
    Dictionary for settings of a grid.

    Attributes
    ----------
    pitch: tuple[int, int]
        The pitch size for a grid. This is in the format (x, y).
    angle: tuple[int, int]
        The angles for a grid. This is in the format (x, y).
    offset: tuple[int, int]
        The offset from the origin for a grid. This is in the format (x, y).
    validity: tuple[float, float]
        The validity in each dimension for a grid. This is in the format (x, y).
    """
    pitch: _tuple[int, int]
    angle: _tuple[int, int]
    offset: _tuple[int, int]
    validity: _tuple[float, float]


def sweep(img: imgs.GreyImage, x_size: _tuple[int, ...], y_size: _tuple[int, ...], x_angles: _tuple[int, ...],
          y_angles: _tuple[int, ...], x_offsets: _tuple[int, ...], y_offsets: _tuple[int, ...], *, full=True,
          using=ValidityMeasure.ONE_MINUS_LE) -> typing.Iterator[Settings]:
    """
    Perform a sweep for a series of grids on one image.

    This will aim to output the best-fitting grid.

    Parameters
    ----------
    img: GreyImage
        The image to fit to.
    x_size: tuple[int, ...]
        The gaps between adjacent x-lines.
    y_size: tuple[int, ...]
        The gaps between adjacent y-lines.
    x_angles: tuple[int, ...]
        The angles between the x-axis and the lines.
    y_angles: tuple[int, ...]
        The angles between the y-axis and the lines.
    x_offsets: tuple[int, ...]
        The offsets between the x-origin and the lines.
    y_offsets: tuple[int, ...]
        The offsets between the y-origin and the lines.
    full: bool
        Flag to determine whether to pause and return all grids, or just the best-fitting grid.
        Default is True, which will pause and return all grids.
    using: ValidityMeasure
        The validity measure to use for all grids.

    Yields
    ------
    Settings
        The settings for the current grid.
        Note that if `full` is False, then the only value yielded is the best-fitting grid.

    Raises
    ------
    TypeError
        If the image isn't square.
    """
    w, h = img.size
    if w != h:
        raise TypeError("Expected square image")

    best_settings: Settings = {"pitch": (0, 0), "angle": (0, 0), "offset": (0, 0), "validity": (0.0, 0.0)}
    max_validity = [-1.0, -1.0]

    def _pass(pitch: _tuple[int, int], angle: _tuple[int, int], offset: _tuple[int, int]) -> _tuple[float, float]:
        square = Grid(w, angle, pitch, offset, using)
        x_validity = square.validity(img, Axis.X)
        y_validity = square.validity(img, Axis.Y)
        if x_validity > max_validity[0]:
            max_validity[0] = x_validity
            best_settings["pitch"] = pitch
            best_settings["angle"] = angle
            best_settings["offset"] = offset
            best_settings["validity"] = (x_validity, max_validity[1])
        if y_validity > max_validity[1]:
            max_validity[1] = y_validity
            best_settings["pitch"] = pitch
            best_settings["angle"] = angle
            best_settings["offset"] = offset
            best_settings["validity"] = (max_validity[0], y_validity)
        return x_validity, y_validity

    for p_guess, a_guess, o_guess in itertools.product(
            itertools.product(x_size, y_size),
            itertools.product(x_angles, y_angles),
            itertools.product(x_offsets, y_offsets),
    ):
        validity = _pass(p_guess, a_guess, o_guess)
        if validity is None:
            continue
        if not full:
            yield {"pitch": p_guess, "angle": a_guess, "offset": o_guess, "validity": validity}
    yield best_settings
