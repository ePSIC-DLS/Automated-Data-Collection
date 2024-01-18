import time
import typing
from contextlib import contextmanager
from datetime import datetime

import h5py

from . import Apt, Def, Det, Eos, Feg, Gun, Ht, Len, Scan, Stage
from . import _controller as base
from ._enums import *
from .. import validators


class Microscope(base.ControllerBase):
    """
    Special subclass that acts like a global microscope controller, allowing for control of all hardware.

    Keys:
        * camera_length (int): The length of the camera
        * merlin_camera_length (float, read-only): The length of the merlin camera
        * FOV (float, read-only): The Field-Of-View for the microscope
        * defocus_per_bit (float, read-only): The defocus measured per bit
        * defocus (float, read-only): Overall defocus of the microscope
        * convergence (float, read-only): Convergence semi-angle of the microscope
        * zdf (int): The Zero-DeFocus value of the microscope
    """

    def keys(self) -> typing.Iterator[str]:
        yield from self._mapping
        for cnt_name, cnt in self._controllers.items():
            yield from map(lambda s: f"{cnt_name}.{s}", cnt.keys())

    @staticmethod
    def validators() -> dict[str, validators.Pipeline]:
        return dict(
            camera_length=validators.xmpls.magnification,
            zdf=validators.xmpls.any_int
        )

    @property
    def time_stamp(self) -> str:
        """
        Retrieve the current year, month, day, hour, minute and second.

        :return: A string representing the current time.
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    @property
    def apt_controller(self) -> Apt:
        """
        Public access to the apt controller. This allows for accessing apt methods.

        **Attribute access by key shouldn't be done on this controller as they're incompatible with global cache
        Always use self[apt.key] instead.**
        :return: The apt controller.
        """
        return self._apt

    @property
    def deflector_controller(self) -> Def:
        """
        Public access to the deflector controller. This allows for accessing deflector methods.

        **Attribute access by key shouldn't be done on this controller as they're incompatible with global cache
        Always use self[deflector.key] instead.**
        :return: The deflector controller.
        """
        return self._def

    @property
    def detector_controller(self) -> Det:
        """
        Public access to the detector controller. This allows for accessing detector methods.

        **Attribute access by key shouldn't be done on this controller as they're incompatible with global cache
        Always use self[detector.key] instead.**
        :return: The detector controller.
        """
        return self._det

    @property
    def eos_controller(self) -> Eos:
        """
        Public access to the eos controller. This allows for accessing eos methods.

        **Attribute access by key shouldn't be done on this controller as they're incompatible with global cache
        Always use self[eos.key] instead.**
        :return: The eos controller.
        """
        return self._eos

    @property
    def feg_controller(self) -> Feg:
        """
        Public access to the feg controller. This allows for accessing feg methods.

        **Attribute access by key shouldn't be done on this controller as they're incompatible with global cache
        Always use self[feg.key] instead.**
        :return: The feg controller.
        """
        return self._feg

    @property
    def gun_controller(self) -> Gun:
        """
        Public access to the gun controller. This allows for accessing gun methods.

        **Attribute access by key shouldn't be done on this controller as they're incompatible with global cache
        Always use self[gun.key] instead.**
        :return: The gun controller.
        """
        return self._gun

    @property
    def ht_controller(self) -> Ht:
        """
        Public access to the ht controller. This allows for accessing ht methods.

        **Attribute access by key shouldn't be done on this controller as they're incompatible with global cache
        Always use self[ht.key] instead.**
        :return: The ht controller.
        """
        return self._ht

    @property
    def lens_controller(self) -> Len:
        """
        Public access to the lens controller. This allows for accessing lens methods.

        **Attribute access by key shouldn't be done on this controller as they're incompatible with global cache
        Always use self[lens.key] instead.**
        :return: The lens controller.
        """
        return self._lens

    @property
    def scan_controller(self) -> Scan:
        """
        Public access to the scan controller. This allows for accessing scan methods.

        **Attribute access by key shouldn't be done on this controller as they're incompatible with global cache
        Always use self[scan.key] instead.**
        :return: The scan controller.
        """
        return self._scan

    @property
    def stage_controller(self) -> Stage:
        """
        Public access to the stage controller. This allows for accessing stage methods.

        **Attribute access by key shouldn't be done on this controller as they're incompatible with global cache
        Always use self[stage.key] instead.**
        :return: The stage controller.
        """
        return self._stage

    def __init__(self, deflector: Deflector, detector: Detector, wobbler: Wobbler, lens: Lens, stage_driver: Driver,
                 zdf=38942, /, *, beam_blanked=False, scan_size: int = None, scan_mode: ScanMode = None,
                 exposure_time: float = None, frames: int = None, position: tuple[int, int] = None,
                 brightness: int = None, contrast: int = None, spot_size: int = None, magnification: int = None,
                 imaging: ImagingMode = None, probe: ProbeMode = None, xy_mag: tuple[int, int] = None,
                 xy_rot: tuple[int, int] = None, xy_cor: tuple[int, int] = None, xy_off: tuple[int, int] = None,
                 stage_offset: tuple[int, int] = None):
        self._apt = Apt()
        self._def = Def(deflector, blank=beam_blanked)
        self._det = Det(detector, scan_size=scan_size, brightness=brightness, contrast=contrast, initial_mode=scan_mode,
                        initial_dwell_time=exposure_time, initial_integration=frames, initial_pos=position)
        self._eos = Eos(magnification=magnification, mode=imaging, probe=probe, spot_size=spot_size)
        self._feg = Feg()
        self._gun = Gun(wobbler)
        self._ht = Ht()
        self._lens = Len(lens)
        self._scan = Scan(mag_adjust=xy_mag, rotation_adjust=xy_rot, correction_adjust=xy_cor, offset_adjust=xy_off)
        self._stage = Stage(stage_driver, offset=stage_offset)
        self._zdf = zdf
        self._controllers: dict[str, base.ControllerBase] = {
            cnt.controller: cnt for cnt in
            (self._apt, self._def, self._det, self._eos, self._feg, self._gun, self._ht, self._lens, self._scan,
             self._stage)
        }
        super().__init__(
            "global",
            camera_length=(self._camera, self._camera_write),
            merlin_camera_length=(self._merlin, None),
            FOV=(lambda: 10e-6 * (20_000 / self["eos.magnification"]), None),
            defocus_per_bit=(self._defocus_per_bit, None),
            defocus=(self._defocus, None),
            convergence=(self._convergence, None),
            zdf=(lambda: self._zdf, self._write_zdf)
        )
        self._pops = {
            "ht.value": ["merlin_camera_length", "defocus_per_bit", "convergence"],
            "eos.magnification": ["merlin_camera_length", "FOV"],
            "defocus_per_pit": ["defocus"],
            "apt.apt": ["convergence"],
            "apt.size": ["convergence"]
        }

    def __getitem__(self, item: str) -> typing.Any:
        try:
            return super().__getitem__(item)
        except KeyError:
            for module, cnt in self._controllers.items():
                search = item.find(f"{module}.")
                if search != -1:
                    return cnt[item[len(module) + 1:]]
            raise

    def __setitem__(self, item: str, value: typing.Any):
        try:
            super().__setitem__(item, value)
            return
        except KeyError:
            for module, cnt in self._controllers.items():
                search = item.find(f"{module}.")
                if search != -1:
                    new = item[len(module) + 1:]
                    cnt[new] = value
                    for key in self._pops.get(item, []):
                        self._cache.pop(key, None)
                    return
            raise

    def read(self, file: str):
        """
        Read the file and then change all relevant attributes to be the values specified by the file.

        :param file: The filepath to open.
        """
        with h5py.File(file) as read:
            self.wipe()
            for cnt in self._controllers.values():
                cnt.wipe()
            values: dict[str, typing.Callable[[typing.Any], typing.Any]] = {
                "zdf": lambda group: group["zero_OLfine"],
                "eos.magnification": lambda group: group["magnification"],
                "ht.value": lambda group: group["ht_value(V)"],
                "camera_length": lambda group: group["nominal_camera_length(m)"] / 1e3,
                "merlin_camera_length": lambda group: group["merlin_camera_length(m)"],
                "eos.spot_size": lambda group: group["spot_size"],
                "apt.apt_size": lambda group: group["aperture_size"],
                "FOV": lambda group: group["field_of_view(m)"],
                "detector.scan_size": lambda group: self["FOV"] / group["step_size(m)"],
                "gun.a1": lambda group: group["A1_value_(kV)"],
                "gun.a2": lambda group: group["A2_value_(kV)"],
                "stage.motor_pos": lambda group: tuple(map(lambda s: group[f"{s}_pos(m)"] / 1e-9, ("x", "y", "z"))),
                "stage.tilt": lambda group: (group["x_tilt(deg)"], group["y_tilt(deg)"]),
            }
            metadata = read["metadata"]
            lenses = metadata["lens_values"]
            deflectors = metadata["deflector_values"]
            with self.lens(Lens.OL_FINE):
                self["lens.info"] = metadata["current_OLfine"]
            for self_key, meta_key in values.items():
                try:
                    self[self_key] = meta_key(metadata)
                except AttributeError:
                    continue
            for lens in Lens:
                if lens == Lens.OL_FINE:
                    continue
                with self.lens(lens):
                    self["lens.info"] = lenses[lens.name]
            for defl in Deflector:
                with self.deflector(defl):
                    try:
                        self["deflector.value"] = deflectors[defl.name]
                    except TypeError:
                        continue
            for defl in ("shift_balance", "tilt_balance", "angle_balance", "alignment"):
                self[f"deflector.{defl}"] = deflectors[defl]

    def write(self, file: str, **merlin):
        """
        Write all relevant attributes to the file, such that it can be read by the "read" method.

        :param file: The filepath to open.
        """
        with h5py.File(file, "a") as write:
            values: dict[str, typing.Callable[[typing.Any], typing.Any]] = {
                "zero_OLfine": self["zdf"],
                "magnification": self["eos.magnification"],
                "ht_value(V)": self["ht.value"],
                "nominal_camera_length(m)": self["camera_length"] * 1e3,
                "merlin_camera_length(m)": self["merlin_camera_length"],
                "spot_size": self["eos.spot_size"],
                "aperture_size": self["apt.apt_size"],
                "field_of_view(m)": self["FOV"],
                "step_size(m)": self["FOV"] / self["detector.scan_size"],
                "A1_value_(kV)": self["gun.a1"],
                "A2_value_(kV)": self["gun.a2"],
                "x_pos(m)": self["stage.motor_pos"][0] * 1e-9,
                "y_pos(m)": self["stage.motor_pos"][1] * 1e-9,
                "z_pos(m)": self["stage.motor_pos"][2] * 1e-9,
                "x_tilt(deg)": self["stage.tilt"][0],
                "y_tilt(deg)": self["stage.tilt"][1],
            }
            metadata = write.create_group("metadata")
            lenses = metadata.create_group("lens_values")
            deflectors = metadata.create_group("deflector_values")
            merlin_group = metadata.create_group("merlin_params")
            with self.lens(Lens.OL_FINE):
                metadata["current_OLfine"] = self["lens.info"]
            for meta_key, self_value in values.items():
                metadata[meta_key] = self_value
            for lens in Lens:
                if lens == Lens.OL_FINE:
                    continue
                with self.lens(lens):
                    lenses[lens.name] = self["lens.info"]
            for defl in Deflector:
                with self.deflector(defl):
                    if defl in {Deflector.CMT_A, Deflector.CMP_S, Deflector.CMP_T}:
                        continue
                    deflectors[defl.name] = self["deflector.value"]
            for defl in ("shift_balance", "tilt_balance", "angle_balance", "alignment"):
                deflectors[defl] = self[f"deflector.{defl}"]
            for k, v in merlin.items():
                merlin_group[k] = v

    @contextmanager
    def apt_kind(self, new: ApertureKind):
        """
        Context manager to temporarily switch the aperture kind.

        This allows for block-specific aperture type changes.
        Note that this context manager **doesn't** return anything – using an 'as' statement binds to None.
        :param new: The new aperture kind to switch to
        """
        yield from self._context_switch("apt", "apt_kind", new)

    @contextmanager
    def apt(self, new: Aperture):
        """
        Context manager to temporarily switch the aperture.

        This allows for block-specific aperture changes.
        Note that this context manager **doesn't** return anything – using an 'as' statement binds to None.
        :param new: The new aperture to switch to
        """
        yield from self._context_switch("apt", "apt", new)

    @contextmanager
    def deflector(self, new: Deflector):
        """
        Context manager to temporarily switch the deflector.

        This allows for block-specific deflector changes.
        Note that this context manager **doesn't** return anything – using an 'as' statement binds to None.
        :param new: The new deflector to switch to
        """
        yield from self._context_switch("deflector", "deflector", new)

    @contextmanager
    def blanked(self, new: bool):
        """
        Context manager to temporarily switch the beam status.

        This allows for block-specific beam blanking.
        Note that this context manager **doesn't** return anything – using an 'as' statement binds to None.
        :param new: The new blanked state to switch to
        """
        yield from self._context_switch("deflector", "blanked", new, sleep=1)

    @contextmanager
    def detector(self, new: Detector = None, *, insertion: bool = None):
        """
        Context manager to temporarily switch the detector or its insertion status.

        This allows for block-specific detector or insertion changes.
        Note that this context manager **doesn't** return anything – using an 'as' statement binds to None.
        :param new: The new detector to switch to (None if switching insertion status)
        :param insertion: The new insertion status (None if switching detectors)
        :raises ValueError: If trying to change detector and insertion status (or neither)
        """
        do_det = new is not None
        do_insert = insertion is not None
        if do_det ^ do_insert:
            if do_det:
                yield from self._context_switch("detector", "detector", new)
            elif do_insert:
                yield from self._context_switch("detector", "inserted", insertion)
        else:
            raise ValueError("Must switch either detector or insertion state")

    @contextmanager
    def scan_mode(self, new: ScanMode):
        """
        Context manager to temporarily switch the detector's scan mode.

        This allows for block-specific scanning mode changes.
        Note that this context manager **doesn't** return anything – using an 'as' statement binds to None.
        :param new: The new scan mode to switch to
        """
        yield from self._context_switch("detector", "scan_mode", new)

    @contextmanager
    def magnification(self, new: int):
        """
        Context manager to temporarily switch the magnification.

        This allows for block-specific magnification changes.
        Note that this context manager **doesn't** return anything – using an 'as' statement binds to None.
        :param new: The new magnification to switch to
        """
        yield from self._context_switch("eos", "magnification", new)

    @contextmanager
    def lens(self, new: Lens):
        """
        Context manager to temporarily switch the lens.

        This allows for block-specific lens changes.
        Note that this context manager **doesn't** return anything – using an 'as' statement binds to None.
        :param new: The new lens to switch to
        """
        yield from self._context_switch("lens", "lens", new)

    @contextmanager
    def imaging_mode(self, new: ImagingMode):
        """
        Context manager to temporarily switch the imaging mode.

        This allows for block-specific imaging changes.
        Note that this context manager **doesn't** return anything – using an 'as' statement binds to None.
        :param new: The new imaging mode to switch to
        """
        yield from self._context_switch("eos", "imaging_mode", new)

    def _camera(self) -> int:
        with self.imaging_mode(ImagingMode.STEM):
            return self["eos.magnification"]

    def _camera_write(self, new: int):
        with self.imaging_mode(ImagingMode.STEM):
            self["eos.magnification"] = new

    def _merlin(self) -> float:
        ht = self["ht.value"]
        cam = self["eos.magnification"]
        if ht == 80:
            factor = 1.58
        elif ht == 300:
            factor = 1.64
        else:
            factor = 1
        return factor * cam

    def _defocus_per_bit(self) -> float:
        ht = int(self["ht.value"])
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

    def _defocus(self) -> float:
        with self.lens(Lens.OL_FINE):
            return self["defocus_per_bit"] * (self["lens.info"] - self._zdf)

    def _convergence(self) -> float:
        ht = int(self["ht.value"])
        ty = self["apt.apt"].value
        size = self["apt.size"]
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

    def _context_switch(self, controller_name: str, key: str, new, *, sleep=0.0):
        if sleep < 0:
            raise ValueError("Sleep time should be positive")
        old = self[f"{controller_name}.{key}"]
        try:
            self[f"{controller_name}.{key}"] = new
            if sleep:
                time.sleep(sleep)
            yield
        except Exception as err:
            raise err
        finally:
            self[f"{controller_name}.{key}"] = old
            if sleep:
                time.sleep(sleep)

    def _write_zdf(self, new: int):
        self._zdf = new
        self._cache.pop("defocus", None)
