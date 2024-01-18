"""
Module to encapsulate all microscope data into a single class with a lot of attributes
"""
from PyJEM import TEM3
import h5py
import datetime as dt


class MicroscopeParameters:
    """
    The parameters of the microscope, encapsulated into a class
    """
    
    @property 
    def time_stamp(self):
        return str(dt.datetime.now().strftime('%Y%m%d_%H%M%S'))

    def __init__(self, zdf=38942, scan_size=256):
        self.convergence = 0.0
        self.guna1 = None
        self.guna2 = None
        self.ils = None
        self.is1 = None
        self.is2 = None
        self.magadjust = None
        self.ols = None
        self.offset = None
        self.pla = None
        self.rotation = None
        self.scan1 = None
        self.scan2 = None
        self.shifbal = None
        self.spota = None
        self.stemis = None
        self.tiltbal = None
        self.angbal = None
        self.stage_pos = None
        self.piezo_pos = None
        self.correction = None
        self.cls = None
        self.cla2 = None
        self.cla1 = None
        self.pl1 = None
        self.om = None
        self.olf = None
        self.olc = None
        self.olsf = None
        self.il3 = None
        self.il2 = None
        self.il1 = None
        self.cm = None
        self.cl3 = None
        self.cl2 = None
        self.cl1 = None
        self.defocus = None
        self.defocus_per_bit = None
        self.objective_lens_value = None
        self.a2 = None
        self.a1 = None
        self.FOV = None
        self.apt_type = None
        self.apt_size = None
        self.spot_size = None
        self.merlin_camera_length = None
        self.camera_length = None
        self.ht_value = None
        self.scan_rotation = None
        self.magnification = None
        self.stage = TEM3.Stage3()
        self.eos = TEM3.EOS3()
        self.scan = TEM3.Scan3()
        self.ht = TEM3.HT3()
        self.apt = TEM3.Apt3()
        self.lens = TEM3.Lens3()
        self.gun = TEM3.GUN3()
        self.defl = TEM3.Def3()

        self.zdf = zdf
        self.scan_size = scan_size

    def get_state(self):
        """
        Get the state of the microscope and store it in the instance variables
        """
        self.magnification = self.eos.GetMagValue()[0]
        self.scan_rotation = self.scan.GetRotationAngle()
        self.ht_value = self.ht.GetHtValue()
        self.camera_length = self.eos.GetStemCamValue()

        if int(self.ht_value) == 80:
            self.merlin_camera_length = 1.58 * self.camera_length[0] * 1e-3
        elif int(self.ht_value) == 300:
            self.merlin_camera_length = 1.64 * self.camera_length[0] * 1e-3
        else:
            self.merlin_camera_length = self.camera_length[0] * 1e-3

        self.spot_size = self.eos.GetSpotSize() + 6

        self.apt_size = self.apt.GetExpSize(1)
        if self.apt_size == 0:
            self.apt_type = 0
            self.apt_size = self.apt.GetExpSize(0)
        else:
            self.apt_type = 1

        self.FOV = 10e-6 * (20000 / self.magnification)

        self.a1 = self.gun.GetAnode1CurrentValue()
        self.a2 = self.gun.GetAnode2CurrentValue()

        self.objective_lens_value = self.lens.GetOLf()

        ht_list = [200000, 300000, 80000, 60000, 30000, 15000]

        if int(self.ht_value) in ht_list:
            self.defocus = self.get_defocus_per_bit() * (self.objective_lens_value - self.zdf)
            self.get_convergence()

        if int(self.ht_value) == 0:
            self.defocus_per_bit = 0.7
            self.defocus = 0.7 * (self.objective_lens_value - self.zdf)

        self.cl1 = self.lens.GetCL1()
        self.cl2 = self.lens.GetCL2()
        self.cl3 = self.lens.GetCL3()
        self.cm = self.lens.GetCM()
        self.il1 = self.lens.GetIL1()
        self.il2 = self.lens.GetIL2()
        self.il3 = self.lens.GetIL3()
        self.olsf = self.lens.GetOLSuperFineValue()
        self.olc = self.lens.GetOLc()
        self.olf = self.lens.GetOLf()
        self.om = self.lens.GetOM()
        self.pl1 = self.lens.GetPL1()

        self.cla1 = self.defl.GetCLA1()
        self.cla2 = self.defl.GetCLA2()
        self.cls = self.defl.GetCLs()
        self.correction = self.defl.GetCorrection()
        self.guna1 = self.defl.GetGunA1()
        self.guna2 = self.defl.GetGunA2()
        self.ils = self.defl.GetILs()
        self.is1 = self.defl.GetIS1()
        self.is2 = self.defl.GetIS2()
        self.magadjust = self.defl.GetMagAdjust()
        self.ols = self.defl.GetOLs()
        self.offset = self.defl.GetOffset()
        self.pla = self.defl.GetPLA()
        self.rotation = self.defl.GetRotation()
        self.scan1 = self.defl.GetScan1()
        self.scan2 = self.defl.GetScan2()
        self.shifbal = self.defl.GetShifBal()
        self.spota = self.defl.GetSpotA()
        self.stemis = self.defl.GetStemIS()
        self.tiltbal = self.defl.GetTiltBal()
        self.angbal = self.defl.GetAngBal()

        self.stage_pos = self.stage.GetPos()
        self.piezo_pos = self.stage.GetPiezoPosi()

    def get_defocus_per_bit(self):
        """
        Save de-focus per bit into an instance variable and return it
        :return: The de-focus per bit
        """

        if int(self.ht_value) == 300000:
            self.defocus_per_bit = 0.7622
        if int(self.ht_value) == 200000:
            self.defocus_per_bit = 0.8206
        if int(self.ht_value) == 80000:
            self.defocus_per_bit = 0.75
        if int(self.ht_value) == 60000:
            self.defocus_per_bit = 0.84
        if int(self.ht_value) == 30000:
            self.defocus_per_bit = 0.8  # This is not calibrated
        else:
            self.defocus_per_bit = 0.75  # this is not calibrated
        return self.defocus_per_bit

    def get_convergence(self):
        """
        Get the convergence and return it
        :return: The convergence
        """

        if int(self.ht_value) == 300000:
            if self.apt_type == 1:
                if self.apt_size == 1:
                    self.convergence = 0.0447
                elif self.apt_size == 2:
                    self.convergence = 0.0341
                elif self.apt_size == 3:
                    self.convergence = 0.0267
                elif self.apt_size == 4:
                    self.convergence = 0.0167
        elif int(self.ht_value) == 200000:
            if self.apt_type == 1:
                if self.apt_size == 1:
                    self.convergence = 0.0377
                elif self.apt_size == 2:
                    self.convergence = 0.0288
                elif self.apt_size == 3:
                    self.convergence = 0.0224
                elif self.apt_size == 4:
                    self.convergence = 0.014
            elif self.apt_type == 0:
                if self.apt_size == 4:
                    self.convergence = 0.0064
        elif int(self.ht_value) == 80000:
            if self.apt_type == 1:
                if self.apt_size == 1:
                    self.convergence = 0.04165
                elif self.apt_size == 2:
                    self.convergence = 0.03174
                elif self.apt_size == 3:
                    self.convergence = 0.0248
                elif self.apt_size == 4:
                    self.convergence = 0.01544
        elif int(self.ht_value) == 60000:
            if self.apt_type == 1:
                if self.apt_size == 1:
                    self.convergence = 0.0515
                elif self.apt_size == 2:
                    self.convergence = 0.0391
                elif self.apt_size == 3:
                    self.convergence = 0.0306
                elif self.apt_size == 4:
                    self.convergence = 0.019
            elif self.apt_type == 0:
                if self.apt_size == 4:
                    self.convergence = 0.0087
        elif int(self.ht_value) == 30000:
            if self.apt_type == 1:
                if self.apt_size == 1:
                    self.convergence = 0.061
                elif self.apt_size == 2:
                    self.convergence = 0.0481
                elif self.apt_size == 3:
                    self.convergence = 0.0379
                elif self.apt_size == 4:
                    self.convergence = 0.0242

        elif int(self.ht_value) == 15000:
            if self.apt_type == 0:
                if self.apt_size == 1:
                    self.convergence = 0.000
                elif self.apt_size == 2:
                    self.convergence = 0.02332
                elif self.apt_size == 3:
                    self.convergence = 0.000
                elif self.apt_size == 4:
                    self.convergence = 0.000

        else:
            if self.apt_type == 1:
                if self.apt_size == 1:
                    self.convergence = 0.061
                elif self.apt_size == 2:
                    self.convergence = 0.0481
                elif self.apt_size == 3:
                    self.convergence = 0.0379
                elif self.apt_size == 4:
                    self.convergence = 0.0242

        return self.convergence

    def write_to(self, file: str, **merlin):
        """
        Get the state of the instance variables and store them in a file
        :param file: The path to the .hdf5 file
        """
        with h5py.File(file, "a") as f:
            metadata_group = f.create_group('metadata')
            metadata_group['magnification'] = self.magnification
            metadata_group['nominal_scan_rotation'] = self.scan_rotation
            metadata_group['ht_value(V)'] = self.ht_value
            metadata_group['nominal_camera_length(m)'] = self.camera_length[0] * 1e-3
            metadata_group['merlin_camera_length(m)'] = self.merlin_camera_length
            metadata_group['spot_size'] = self.spot_size
            metadata_group['aperture_size'] = self.apt_size
            metadata_group['field_of_view(m)'] = self.FOV
            metadata_group['step_size(m)'] = self.FOV / self.scan_size
            metadata_group['zero_OLfine'] = self.zdf
            metadata_group['current_OLfine'] = self.objective_lens_value

            metadata_group['A1_value_(kV)'] = self.a1
            metadata_group['A2_value_(kV)'] = self.a2

            metadata_group['x_pos(m)'] = self.stage_pos[0] * 1e-9
            metadata_group['y_pos(m)'] = self.stage_pos[1] * 1e-9
            metadata_group['z_pos(m)'] = self.stage_pos[2] * 1e-9
            metadata_group['x_tilt(deg)'] = self.stage_pos[3]
            metadata_group['y_tilt(deg)'] = self.stage_pos[4]

            lens_group = metadata_group.create_group('lens_values')
            lens_group['CL1'] = self.cl1
            lens_group['CL2'] = self.cl2
            lens_group['CL3'] = self.cl3
            lens_group['CM'] = self.cm
            lens_group['IL1'] = self.il1
            lens_group['IL2'] = self.il2
            lens_group['IL3'] = self.il3
            lens_group['OLSF'] = self.olsf
            lens_group['OLC'] = self.olc
            lens_group['OLF'] = self.olf
            lens_group['OM'] = self.om
            lens_group['PL1'] = self.pl1

            defl_group = metadata_group.create_group('deflector_values')
            defl_group['CLA1'] = self.cla1
            defl_group['CLA2'] = self.cla2
            defl_group['CLS'] = self.cls
            defl_group['Correction'] = self.correction
            defl_group['GUNA1'] = self.guna1
            defl_group['GUNA2'] = self.guna2
            defl_group['ILS'] = self.ils
            defl_group['IS1'] = self.is1
            defl_group['IS2'] = self.is2
            defl_group['MAGADJUST'] = self.magadjust
            defl_group['OLS'] = self.ols
            defl_group['OFFSET'] = self.offset
            defl_group['PLA'] = self.pla
            defl_group['ROTATION'] = self.rotation
            defl_group['SCAN1'] = self.scan1
            defl_group['SCAN2'] = self.scan2
            defl_group['SHIFBAL'] = self.shifbal
            defl_group['SPOTA'] = self.spota
            defl_group['STEMIS'] = self.stemis
            defl_group['TILTBAL'] = self.tiltbal
            defl_group['ANGBAL'] = self.angbal

            if int(self.ht_value) in {200_000, 300_000, 30_000, 60_000, 80_000}:
                metadata_group['defocus(nm)'] = self.defocus
                metadata_group['defocus_per_bit(nm)'] = self.defocus_per_bit
                metadata_group['convergence_semi-angle(rad)'] = self.convergence

            merlin_group = metadata_group.create_group("merlin_parameters")
            for k, v in merlin.items():
                merlin_group[k] = v

    def write_from(self, file: str):
        """
        Get the state of the file and store them in instance variables
        :param file: The path to the .hdf5 file
        """
        with h5py.File(file, "r") as f:
            print(f.keys())
            metadata_group = f["metadata"]
            self.magnification =  metadata_group['magnification'] #follow.
            # metadata_group['nominal_scan_rotation'] = self.scan_rotation
            # metadata_group['ht_value(V)'] = self.ht_value
            # metadata_group['nominal_camera_length(m)'] = self.camera_length[0] * 1e-3
            # metadata_group['merlin_camera_length(m)'] = self.merlin_camera_length
            # metadata_group['spot_size'] = self.spot_size
            # metadata_group['aperture_size'] = self.apt_size
            # metadata_group['field_of_view(m)'] = self.FOV
            # metadata_group['step_size(m)'] = self.FOV / self.scan_size
            # metadata_group['zero_OLfine'] = self.zdf
            # metadata_group['current_OLfine'] = self.objective_lens_value
            
            # metadata_group['A1_value_(kV)'] = self.a1
            # metadata_group['A2_value_(kV)'] = self.a2
            
            # metadata_group['x_pos(m)'] = self.stage_pos[0] * 1e-9
            # metadata_group['y_pos(m)'] = self.stage_pos[1] * 1e-9
            # metadata_group['z_pos(m)'] = self.stage_pos[2] * 1e-9
            # metadata_group['x_tilt(deg)'] = self.stage_pos[3]
            # metadata_group['y_tilt(deg)'] = self.stage_pos[4]

            lens_group = metadata_group["lens_values"]
            # lens_group['CL1'] = self.cl1
            # lens_group['CL2'] = self.cl2
            # lens_group['CL3'] = self.cl3
            # lens_group['CM'] = self.cm
            # lens_group['IL1'] = self.il1
            # lens_group['IL2'] = self.il2
            # lens_group['IL3'] = self.il3
            # lens_group['OLSF'] = self.olsf
            # lens_group['OLC'] = self.olc
            # lens_group['OLF'] = self.olf
            # lens_group['OM'] = self.om
            # lens_group['PL1'] = self.pl1

            defl_group = metadata_group["deflector_values"]
            # defl_group['CLA1'] = self.cla1
            # defl_group['CLA2'] = self.cla2
            # defl_group['CLS'] = self.cls
            # defl_group['Correction'] = self.correction
            # defl_group['GUNA1'] = self.guna1
            # defl_group['GUNA2'] = self.guna2
            # defl_group['ILS'] = self.ils
            # defl_group['IS1'] = self.is1
            # defl_group['IS2'] = self.is2
            # defl_group['MAGADJUST'] = self.magadjust
            # defl_group['OLS'] = self.ols
            # defl_group['OFFSET'] = self.offset
            # defl_group['PLA'] = self.pla
            # defl_group['ROTATION'] = self.rotation
            # defl_group['SCAN1'] = self.scan1
            # defl_group['SCAN2'] = self.scan2
            # defl_group['SHIFBAL'] = self.shifbal
            # defl_group['SPOTA'] = self.spota
            # defl_group['STEMIS'] = self.stemis
            # defl_group['TILTBAL'] = self.tiltbal
            # defl_group['ANGBAL'] = self.angbal

            # if int(self.ht_value) in {200_000, 300_000, 30_000, 60_000, 80_000}:
            #     metadata_group['defocus(nm)'] = self.defocus
            #     metadata_group['defocus_per_bit(nm)'] = self.defocus_per_bit
            #     metadata_group['convergence_semi-angle(rad)'] = self.convergence
