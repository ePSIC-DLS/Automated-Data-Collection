import numpy as np

from ._base import Correction


class Skew(Correction[float]):

    def valid(self, value: float) -> bool:
        return 90 - self._tolerance <= value < 90 + self._tolerance

    def _apply_correction(self, value: float):
        self._values["rotation"] += int(90 - value)

    def to_matrix(self) -> np.ndarray:
        cos = np.cos(np.deg2rad(self._values["rotation"]))
        sin = np.sin(np.deg2rad(self._values["rotation"]))
        arr = np.eye(3) * cos
        arr[0, 1] = -sin
        arr[1, 0] = sin
        arr[2, 2] = 1
        return arr
