from typing import Tuple as _tuple

import numpy as np

from ._base import Correction, Scan3


class Size(Correction[_tuple[int, int]]):

    def __init__(self, scanner: Scan3, expected: int, *, tolerance=0):
        super().__init__(scanner, tolerance=int(tolerance))
        self._size = expected

    def _apply_correction(self, value: _tuple[int, int]):
        dist = (self._size - value[0], self._size - value[1])
        self._values["mag_h"] += dist[0]
        self._values["mag_v"] += dist[1]

    def valid(self, value: _tuple[int, int]) -> bool:
        return value[0] == value[1] and self._size - self._tolerance <= value[0] <= self._size + self._tolerance

    def to_matrix(self) -> np.ndarray:
        arr = np.eye(3)
        arr[0, 1] = self._values["mag_h"]
        arr[1, 0] = self._values["mag_v"]
        return arr
