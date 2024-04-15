import typing

import h5py

from . import controllers
from ._base import Base
from ._utils import *

if ONLINE:
    from PyJEM.TEM3 import HT3
else:
    from .PyJEM.offline.TEM3 import HT3


class SubSystems(typing.TypedDict):
    Stage: controllers.Stage
    Lenses: controllers.Lens
    Gun: controllers.Gun
    FEG: controllers.Feg
    EOS: controllers.Eos
    Detectors: controllers.Detector
    Deflectors: controllers.Deflector
    Apertures: controllers.Aperture


class Controller(Base):

    @Key
    def merlin_camera_length(self) -> float:
        ht = self._ht.GetHtValue()
        cam = self._systems["EOS"].magnification
        if ht == 80:
            factor = 1.58
        elif ht == 300:
            factor = 1.64
        else:
            factor = 1
        return factor * cam

    @Key
    def field_of_view(self) -> float:
        inv_mag = 20_000 / self._systems["EOS"].magnification
        return 10e-6 * inv_mag

    @Key
    def defocus_per_bit(self) -> float:
        ht = self._ht.GetHtValue()
        # <editor-fold desc="HT decider block">
        if ht == 300_000:
            return 0.7622
        elif ht == 200_000:
            return 0.8206
        elif ht == 80_000:
            return 0.75
        elif ht == 60_000:
            return 0.84
        elif ht == 30_000:
            return 0.8
        elif ht == 0:
            return 0.7
        else:
            return 0.75
        # </editor-fold>

    @Key
    def defocus(self) -> float:
        lenses = self._systems["Lenses"]
        with lenses.switch_lens(Lens.OL_FINE):
            return self.defocus_per_bit * (lenses.value - self._zdf)

    @Key
    def convergence(self) -> float:
        ht = self._ht.GetHtValue()
        apt = self._systems["Apertures"]
        ty = apt.current.value
        size = apt.size
        mapping_300k = {
            (1, 1): 0.0447,
            (1, 2): 0.0341,
            (1, 3): 0.0267,
            (1, 4): 0.0167,
        }
        mapping_200k = {
            (1, 1): 0.0377,
            (1, 2): 0.0288,
            (1, 3): 0.0224,
            (1, 3): 0.014,
            (0, 4): 0.0064,
        }
        mapping_80k = {
            (1, 1): 0.04165,
            (1, 2): 0.03174,
            (1, 3): 0.0248,
            (1, 4): 0.01544,
        }
        mapping_60k = {
            (1, 1): 0.0515,
            (1, 2): 0.0391,
            (1, 3): 0.0306,
            (1, 4): 0.019,
            (0, 4): 0.0087,
        }
        mapping_30k = {
            (1, 1): 0.061,
            (1, 2): 0.0481,
            (1, 3): 0.0379,
            (1, 4): 0.0242,
        }
        mapping_15k = {
            (0, 2): 0.02332
        }
        mapping_def = {
            (1, 1): 0.061,
            (1, 2): 0.0481,
            (1, 3): 0.0379,
            (1, 4): 0.0242,
        }
        mapping = {
            300_000: mapping_300k,
            200_000: mapping_200k,
            80_000: mapping_80k,
            60_000: mapping_60k,
            30_000: mapping_30k,
            15_000: mapping_15k
        }
        return mapping.get(ht, mapping_def).get((ty, size), 0.0)

    @property
    def subsystems(self) -> SubSystems:
        return self._systems.copy()

    def __init__(self, detector: Detector, inserted: bool, mode: ImagingMode, lens: Lens, axis: Axis, /, zdf=38942, *,
                 aperture: AptKind = None, beam: bool = None, magnification: int = None, valve: bool = None,
                 driver: Driver = None):
        super().__init__("All")
        self._systems: SubSystems = {
            "Stage": controllers.Stage(axis, driver),
            "Lenses": controllers.Lens(lens),
            "Gun": controllers.Gun(),
            "FEG": controllers.Feg(valve),
            "EOS": controllers.Eos(mode, magnification),
            "Detectors": controllers.Detector((detector, inserted)),
            "Deflectors": controllers.Deflector(beam),
            "Apertures": controllers.Aperture(aperture),
        }
        self._zdf = zdf
        self._ht = HT3()

    def export(self, file: str, **merlin):
        with h5py.File(file, "a") as out:
            if not ONLINE:
                return
