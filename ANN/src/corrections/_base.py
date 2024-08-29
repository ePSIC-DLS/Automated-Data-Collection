import abc
import functools
import typing
from typing import Tuple as _tuple

import numpy as np

ONLINE = False

if not ONLINE:
    from .PyJEM.offline.TEM3 import Scan3
else:
    from PyJEM.TEM3 import Scan3

T = typing.TypeVar("T")


class ProxyDict:

    def __init__(self, **keys: _tuple[int, typing.Callable[[int], None], range]):
        self._keys = keys

    def __getitem__(self, item: str) -> int:
        if self._keys.get(item) is None:
            raise KeyError(f"Unknown scan parameter {item!r}")
        return self._keys[item][0]

    def __setitem__(self, key: str, value: int):
        if self._keys.get(key) is None:
            raise KeyError(f"Unknown scan parameter {key!r}")
        elif value not in (limit := self._keys[key][2]):
            raise ValueError(f"Value ({value}) out of range ({limit})")
        (fn := self._keys[key][1])(value)
        self._keys[key] = (value, fn, limit)


class Correction(abc.ABC, typing.Generic[T]):
    INIT_VALS = {
        0: 0XFFFF,
        1: 0XFFFF,
        2: 0XFFFF,
        3: 0XFFFF,
    }  # adjust as necessary

    def __init__(self, scanner: Scan3, *, tolerance=0.0):
        self._scan = scanner
        self._tolerance = tolerance
        self._values = ProxyDict(
            mag_h=(self.INIT_VALS[0], functools.partial(self._scan.SetScanDataAbs, 0), range(0XFFFF + 1)),
            mag_v=(self.INIT_VALS[1], functools.partial(self._scan.SetScanDataAbs, 1), range(0XFFFF + 1)),
            rot_h=(self.INIT_VALS[2], functools.partial(self._scan.SetScanDataAbs, 2), range(0XFFFF + 1)),
            rot_v=(self.INIT_VALS[3], functools.partial(self._scan.SetScanDataAbs, 3), range(0XFFFF + 1)),
            rotation=(self._scan.GetRotationAngle(), self._scan.SetRotationAngle, range(360))
        )

    def correct(self, value: T):
        if not self.valid(value):
            self._apply_correction(value)

    @abc.abstractmethod
    def to_matrix(self) -> np.ndarray:
        pass

    @abc.abstractmethod
    def valid(self, value: T) -> bool:
        pass

    @abc.abstractmethod
    def _apply_correction(self, value: T):
        pass
