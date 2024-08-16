import typing
from typing import List as _list, Tuple as _tuple

import h5py
import numpy as np

from ._enums import *
from ... import images

__all__ = ["ScanRegion", "Grid", "Cluster"]


class ScanRegion:
    """
    Represents a single square to scan.

    Attributes
    ----------
    _disabled: bool
        Whether the region is disabled.
    _left: int
        The minimum x-coordinate of the square.
    _top: int
        The minimum y-coordinate of the square.
    _right: int
        The maximum x-coordinate of the square.
    _bottom: int
        The maximum y-coordinate of the square.
    _scan_res: int
        The resolution of the scan.
    _delta: int
        The difference between the minima and maxima of the square.
    """

    @property
    def disabled(self) -> bool:
        """
        Public access to the status of the region.

        Returns
        -------
        bool
            Whether the region is disabled.
        """
        return self._disabled

    @disabled.setter
    def disabled(self, value: bool):
        self._disabled = value

    @property
    def size(self) -> int:
        """
        Public access to the region's width and height.

        Returns
        -------
        int
            The difference between the minima and maxima of the square.
        """
        return self._delta

    def __init__(self, top_left: _tuple[int, int], size: int, scan_resolution: int):
        self._disabled = False
        self._left, self._top = top_left
        self._right = self._left + size
        self._bottom = self._top + size
        self._scan_res = scan_resolution
        self._delta = size

    def __str__(self) -> str:
        return f"Region {self._left, self._top} -> {self._right, self._bottom} @ {self._scan_res}x{self._scan_res}"

    def __hash__(self) -> int:
        return hash((self._left, self._top, self._right, self._bottom, self._scan_res))

    def __getitem__(self, item: images.AABBCorner) -> _tuple[int, int]:
        """
        Grab a corner of the square.

        Parameters
        ----------
        item: AABBCorner
            The corner to extract.

        Returns
        -------
        tuple[int, int]
            The cartesian coordinates of the corner.

        Raises
        ------
        TypeError
            If the item is not a corner.
        """
        if not isinstance(item, images.AABBCorner):
            raise TypeError(f"Expected a valid corner, got {item}")
        if item.x() == images.XAxis.LEFT:
            x = self._left
        else:
            x = self._right
        if item.y() == images.YAxis.TOP:
            y = self._top
        else:
            y = self._bottom
        return x, y

    def __matmul__(self, other: int) -> "ScanRegion":
        """
        Scales the region to a new resolution. This will multiply the square by the ratio of the new to old resolution.

        Parameters
        ----------
        other: int
            The new resolution to go to.

        Returns
        -------
        ScanRegion
            The new region with a scaled top-left corner and size.
        """
        if not isinstance(other, int):
            return NotImplemented
        ratio = other / self._scan_res
        return ScanRegion((int(self._left * ratio), int(self._top * ratio)), int(self._delta * ratio), other)

    __rmatmul__ = __matmul__

    def __and__(self, other: "Cluster") -> int:
        """
        Calculates the overlap between this region and a cluster. This is just the number of valid pixels.

        Parameters
        ----------
        other: Cluster
            The cluster to check the amount of overlap. This will count the number of pixels inside the cluster.

        Returns
        -------
        int
            The number of valid pixels inside the cluster.
        """
        if not isinstance(other, Cluster):
            return NotImplemented
        area = other.cluster.region(self[images.AABBCorner.TOP_LEFT], self[images.AABBCorner.BOTTOM_RIGHT]).data()
        count = np.count_nonzero(area)
        return count

    __rand__ = __and__

    def save(self, filepath: str, bg: images.GreyImage):
        """
        Save the region to hdf5 file.

        This will save the scanned image in a dataset, then create a group for the cartesian co-ordinates of the scan.

        Parameters
        ----------
        filepath: str
            The hdf5 file to save to.
        bg: GreyImage
            The greyscale scan image.
        """
        if self._disabled:
            return
        with h5py.File(filepath, "a") as file:
            file.create_dataset("Captured Square", data=bg.data())
            dset = file.create_group("Co-ordinates (cartesian)")
            dset.attrs["top left"] = self[images.AABBCorner.TOP_LEFT]
            dset.attrs["bottom right"] = self[images.AABBCorner.BOTTOM_RIGHT]

    def draw(self, onto: images.RGBImage, outline: np.int_, *, filled=False):
        """
        Draw the region onto an image.

        Parameters
        ----------
        onto: RGBImage
            The background image to draw the square onto.
        outline: int_
            The outline colour to use.
        filled: bool
            Whether the square should be filled. (Default is False)
        """
        if self._disabled:
            return
        onto.drawings.square.size((self._left, self._top), self._delta, outline, safe=True,
                                  fill=None if not filled else outline)

    def move(self, by: _tuple[int, int]):
        """
        Shift the co-ordinates of the region.

        Parameters
        ----------
        by: tuple[int, int]
            The x and y shift.
        """
        self._left += by[0]
        self._right += by[0]
        self._top += by[1]
        self._bottom += by[1]


class Grid:
    """
    Represents a grid of scan regions overlaid with a cluster, such that the cluster's bounding box is captured.

    It has an optional amount of padding to ensure the bounds of the cluster is captured (as it will try to divide the
    cluster to even sizes, there may be a portion not captured. Padding is done to prevent this).

    Each grid can be tightened, where it will eliminate any grid squares that it considers invalid.
    Validity is determined by the number of pixels inside the cluster itself, as opposed to in its bounding box. This
    can be tweaked to be looser or tighter, depending on the cluster's shape (a more axis-aligned rectangle cluster can
    afford to have a higher tightness, as the squares would more closely align with the cluster).

    Attributes
    ----------
    _owner: Cluster
        The cluster to overlay this grid on.
    _tight: list[ScanRegion]
        The tightened squares.
    _is_tight: bool
        Flag for tightness.
    _pitch_size: int
        The size of each scan region.
    _resolution: int
        The resolution of each scan region.
    _start: tuple[int, int]
        The pixel offset this grid has from the top left corner of the cluster.
    _all: list[ScanRegion]
        All available scan regions within the cluster's bounding box (including padding).
    """

    @property
    def tight(self) -> bool:
        """
        Public access to the tightness flag.

        Returns
        -------
        bool
            Whether the grid has been tightened.
        """
        return self._is_tight

    @property
    def pitch_size(self) -> int:
        """
        Public access to the size of the grid's squares.

        Returns
        -------
        int
            The size of each scan region.
        """
        return self._pitch_size

    @property
    def cluster(self) -> "Cluster":
        """
        Public access to the cluster.

        Returns
        -------
        Cluster
            The cluster to overlay this grid on.
        """
        return self._owner

    def __init__(self, sq_size: int, offset: _tuple[int, int], resolution: int, marking: "Cluster"):
        self._owner = marking
        self._tight: _list[ScanRegion] = []
        self._is_tight = False
        self._pitch_size = sq_size
        self._start = offset
        self._resolution = resolution
        self._all = list(self._regions())

    def __iter__(self) -> typing.Iterator[ScanRegion]:
        """
        Iterate over the most suitable grid squares.

        These are the tight squares if this grid has been tightened otherwise it's all the squares.

        Yields
        ------
        ScanRegion
            Each square in the grid.
        """
        if self._is_tight:
            yield from self._tight
        else:
            yield from self._all

    def draw(self, onto: images.RGBImage, colour: np.int_ = None):
        """
        Draw the entire grid onto an image.

        Parameters
        ----------
        onto: RGBImage
            The image to draw onto.
        colour: int_
            The colour to draw each region. Defaults to the cluster's colour.
        """
        if colour is None:
            colour = self._owner.id
        for region in self:
            region.draw(onto, colour)

    def tighten(self, min_rel: float):
        """
        Tighten the grid.

        Parameters
        ----------
        min_rel: float
            The relative minimum number of pixels allowed.

        Raises
        ------
        TypeError
            If min_rel is not a valid percentage range.
        """
        if min_rel < 0 or min_rel > 1:
            raise TypeError(f"Expected a percentage, got {min_rel}")

        min_abs = int(min_rel * self._pitch_size ** 2)

        def _valid(region: ScanRegion) -> bool:
            try:
                count = (region & self._owner)
                return count >= min_abs
            except ValueError:
                return False

        self._tight = list(filter(_valid, self._all))
        self._is_tight = True

    def _regions(self) -> typing.Iterator[ScanRegion]:
        def _pad(minima: int, maxima: int) -> _tuple[int, int]:
            do_min = do_max = True
            while (maxima - minima) % self._pitch_size:
                if not do_max and not do_min:
                    raise ValueError("Cluster too large!")
                if do_min:
                    minima -= 1
                if (maxima - minima) % self._pitch_size == 0 and minima > 0 and maxima < self._resolution:
                    break
                if do_max:
                    maxima += 1
                if minima < 0:
                    minima = 0
                    do_min = False
                elif maxima >= self._resolution:
                    maxima = self._resolution - 1
                    do_max = False
            return minima, maxima

        left, right = self._owner.extreme(Axis.X, Extreme.MINIMA), self._owner.extreme(Axis.X, Extreme.MAXIMA)
        top, bottom = self._owner.extreme(Axis.Y, Extreme.MINIMA), self._owner.extreme(Axis.Y, Extreme.MAXIMA)
        self._left, self._right = _pad(left, right)
        self._top, self._bottom = _pad(top, bottom)
        curr_y = self._top + self._start[1]
        while curr_y + self._pitch_size <= self._bottom:
            curr_x = self._left + self._start[0]
            while curr_x + self._pitch_size <= self._right:
                yield ScanRegion((curr_x, curr_y), self._pitch_size, self._resolution)
                curr_x += self._pitch_size
            curr_y += self._pitch_size


class Cluster:
    """
    Class to represent a cluster. This cluster has an AABB, along with an actual representation.

    Attributes
    ----------
    _label: int_
        The colour label of the cluster.
    _binary: GreyBiModal
        The binary image of the cluster. Note that this will be an image of the same size as the GUI's survey image,
        with only the cluster itself being white (255).
    _min: tuple[int, int]
        The top-left corner of the cluster's AABB.
    _max: tuple[int, int]
        The bottom-right corner of the cluster's AABB.
    _marked: bool
        Whether the cluster has been turned into a series of grids.

    Raises
    ------
    TypeError
        If the image provided does not have the correct colours.
    """

    @property
    def locked(self) -> bool:
        """
        Public access to the grid status.

        Returns
        -------
        bool
            Whether the cluster has been marked by a grid.
        """
        return self._marked

    @locked.setter
    def locked(self, value: bool):
        self._marked = value

    @property
    def cluster(self) -> images.GreyBiModal:
        """
        Public access to the underlying image.

        Returns
        -------
        GreyBimodal
            The binary image representing the polygon.
        """
        return self._binary

    @property
    def id(self) -> np.int_:
        """
        Public access to the colour of this cluster.

        Returns
        -------
        RGB
            The label colour.
        """
        return self._label

    def __init__(self, image: images.RGBBiModal, label: int):
        self._label = np.int_(label)
        if image.get_colours() != {np.int_(0), self._label}:
            raise TypeError(f"Expected image colours to be 0 and {label}, got {image.get_colours()}")
        promoted_image = image.upchannel().find_replace(self._label, 255)
        demoted_image = promoted_image.demote()
        self._binary = demoted_image.downchannel(0, 255)
        img = self._binary.data()
        rows_f, = np.nonzero(np.sum(img, axis=0))
        cols_f, = np.nonzero(np.sum(img, axis=1))
        self._min = (rows_f[0], cols_f[0])
        self._max = (rows_f[-1], cols_f[-1])
        self._marked = False

    def __contains__(self, point: _tuple[int, int]) -> bool:
        """
        Fast collision detection by using the underlying image.

        Parameters
        ----------
        point: tuple[int, int]
            The cartesian co-ordinates to check.

        Returns
        -------
        bool
            Whether the specified co-ordinate is in the cluster.
        """
        return bool(self._binary[point])

    def __str__(self) -> str:
        return f"Cluster {self.id}"

    def __hash__(self) -> int:
        return hash(self._label)

    def __getitem__(self, item: images.AABBCorner) -> _tuple[int, int]:
        """
        Grab a corner of the bounding box.

        Parameters
        ----------
        item: AABBCorner
            The corner to extract.

        Returns
        -------
        tuple[int, int]
            The cartesian coordinates of the corner.

        Raises
        ------
        TypeError
            If the item is not a corner.
        """
        if not isinstance(item, images.AABBCorner):
            raise TypeError(f"Expected a valid corner, got {item}")
        if item.x() == images.XAxis.LEFT:
            x = Extreme.MINIMA
        else:
            x = Extreme.MAXIMA
        if item.y() == images.YAxis.TOP:
            y = Extreme.MINIMA
        else:
            y = Extreme.MAXIMA
        return self.extreme(Axis.X, x), self.extreme(Axis.Y, y)

    def position(self) -> _tuple[int, int]:
        """
        Get the top-left corner of the cluster (based on the bounding box).

        Returns
        -------
        tuple[int, int]
            The top-left corner of the cluster's bounding box.
        """
        return self[images.AABBCorner.TOP_LEFT]

    def extreme(self, axis: Axis, extreme: Extreme) -> int:
        """
        Extract one extreme of the bounding box. This can be minima or maxima in any axis.

        Parameters
        ----------
        axis: Axis
            The axis to extract in.
        extreme: Extreme
            The extremity to extract.

        Returns
        -------
        int
            The bounding box extremity.
        """
        corner = self._min if extreme == Extreme.MINIMA else self._max
        index = 0 if axis == Axis.X else 1
        return corner[index]

    def size(self, axis: Axis) -> int:
        """
        Get the size of the bounding box in a particular axis.

        Parameters
        ----------
        axis: Axis
            The axis to measure in.

        Returns
        -------
        int
            The difference between the maxima and minima location in the particular axis.
        """
        return self.extreme(axis, Extreme.MAXIMA) - self.extreme(axis, Extreme.MINIMA)

    def divide(self, square: int, off_val: int, off_dir: Overlap, resolution: int) -> Grid:
        """
        Divide the bounding box into a singular grid.

        Parameters
        ----------
        square: int
            The square size to use in the grid.
        off_val: int
            The offset value to use for the grid.
        off_dir: Overlap
            The direction of the overlap.
        resolution: int
            The scan resolution to use in the grid.

        Returns
        -------
        Grid
            The grid overlaid over this cluster, created according to the specification of the parameters.
        """
        return Grid(square, (off_val if Overlap.X & off_dir else 0, off_val if Overlap.Y & off_dir else 0), resolution,
                    self)

    @classmethod
    def from_vertices(cls, v1: _tuple[int, int], v2: _tuple[int, int], v3: _tuple[int, int], *v_e: _tuple[int, int],
                      label: int, im_size: _tuple[int, int]) -> "Cluster":
        """
        Alternate constructor to construct a polygon from known vertices, rather than image.

        This will construct the image and draw the polygon onto it, using the specified vertices.

        Parameters
        ----------
        v1: tuple[int, int]
            The first vertex.
        v2: tuple[int, int]
            The second vertex.
        v3: tuple[int, int]
            The third vertex.
        *v_e: tuple[int, int]
            The remaining vertices.
        label: int
            The label of the polygon. This will determine the colour.
        im_size: tuple[int, int]
            The size of the image.

        Returns
        -------
        Cluster
            The cluster created from a known polygon.
        """
        bg = images.RGBImage.blank(im_size)
        bg.drawings.polygon.vertices(label, v1, v2, v3, *v_e)
        return cls(bg.downchannel(0, label), label)
