import typing

import h5py

from . import controllers
from ._base import Base
from ._utils import *

if ONLINE:
    from PyJEM.TEM3 import HT3, Scan3, EOS3, GUN3, Def3
else:
    from .PyJEM.offline.TEM3 import HT3, Scan3, EOS3, GUN3, Def3


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

    def __init__(self, detector: Detector, inserted: bool, lens: Lens, axis: Axis, /, zdf=38942, *,
                 aperture: AptKind = None, beam: bool = None, magnification: int = None, camera_length: int = None,
                 valve: bool = None, driver: Driver = None):
        super().__init__("All")
        self._systems: SubSystems = {
            "Stage": controllers.Stage(axis, driver),
            "Lenses": controllers.Lens(lens),
            "Gun": controllers.Gun(),
            "FEG": controllers.Feg(valve),
            "EOS": controllers.Eos(magnification, camera_length),
            "Detectors": controllers.Detector((detector, inserted)),
            "Deflectors": controllers.Deflector(beam),
            "Apertures": controllers.Aperture(aperture),
        }
        self._zdf = zdf
        self._ht = HT3()
        self._scan = Scan3()
        self._eos = EOS3()
        self._gun = GUN3()
        self._def = Def3()

    def export(self, file: str, scan_size: int, **merlin):
        with h5py.File(file, "a") as f:
            if not ONLINE:
                return
            metadata_group = f.create_group('metadata')

            for key, value in merlin.items():
                metadata_group[key] = value

            local_mag = int(self._eos.GetMagValue()[0])
            local_fov = 10e-6 * (20000 / local_mag)
            local_ht = self._ht.GetHtValue()

            metadata_group['magnification'] = local_mag
            metadata_group['nominal_scan_rotation'] = self._scan.GetRotationAngle()
            metadata_group['ht_value(V)'] = local_ht
            metadata_group['nominal_camera_length(m)'] = self._systems["EOS"].magnification * 1e-3
            metadata_group['merlin_camera_length(m)'] = self.merlin_camera_length
            metadata_group['spot_size'] = self._eos.GetSpotSize()
            metadata_group['aperture_size'] = self._systems["Apertures"].size
            metadata_group['field_of_view(m)'] = local_fov
            metadata_group['step_size(m)'] = local_fov / scan_size
            metadata_group['zero_OLfine'] = self._zdf

            with self._systems["Lenses"].switch_lens(Lens.OL_FINE):
                metadata_group['current_OLfine'] = self._systems["Lenses"].value

            metadata_group['A1_value_(kV)'] = self._gun.GetAnode1CurrentValue()
            metadata_group['A2_value_(kV)'] = self._gun.GetAnode2CurrentValue()

            with self._systems["Stage"].switch_axis(Axis.X):
                metadata_group['x_pos(m)'] = self._systems["Stage"].pos * 1e-9
                metadata_group['x_tilt(deg)'] = self._systems["Stage"].tilt
            with self._systems["Stage"].switch_axis(Axis.Y):
                metadata_group['y_pos(m)'] = self._systems["Stage"].pos * 1e-9
                metadata_group['y_tilt(deg)'] = self._systems["Stage"].tilt
            with self._systems["Stage"].switch_axis(Axis.Z):
                metadata_group['z_pos(m)'] = self._systems["Stage"].pos * 1e-9

            lens_group = metadata_group.create_group('lens_values')
            for lens_type in Lens:
                with self._systems["Lenses"].switch_lens(lens_type):
                    lens_group[lens_type.name] = self._systems["Lenses"].value

            defl_group = metadata_group.create_group('deflector_values')
            defl_group['CLA1'] = self._def.GetCLA1()
            defl_group['CLA2'] = self._def.GetCLA2()
            defl_group['CLS'] = self._def.GetCLs()
            defl_group['Correction'] = self._def.GetCorrection()
            defl_group['GUNA1'] = self._def.GetGunA1()
            defl_group['GUNA2'] = self._def.GetGunA2()
            defl_group['ILS'] = self._def.GetILs()
            defl_group['IS1'] = self._def.GetIS1()
            defl_group['IS2'] = self._def.GetIS2()
            defl_group['MAGADJUST'] = self._def.GetMagAdjust()
            defl_group['OLS'] = self._def.GetOLs()
            defl_group['OFFSET'] = self._def.GetOffset()
            defl_group['PLA'] = self._def.GetPLA()
            defl_group['ROTATION'] = self._def.GetRotation()
            defl_group['SCAN1'] = self._def.GetScan1()
            defl_group['SCAN2'] = self._def.GetScan2()
            defl_group['SHIFBAL'] = self._def.GetShifBal()
            defl_group['SPOTA'] = self._def.GetSpotA()
            defl_group['STEMIS'] = self._def.GetStemIS()
            defl_group['TILTBAL'] = self._def.GetTiltBal()
            defl_group['ANGBAL'] = self._def.GetAngBal()

            if int(local_ht) in {200000, 300000, 60000, 80000}:
                metadata_group['defocus(nm)'] = self.defocus
                metadata_group['defocus_per_bit(nm)'] = self.defocus_per_bit
                metadata_group['convergence_semi-angle(rad)'] = self.convergence
