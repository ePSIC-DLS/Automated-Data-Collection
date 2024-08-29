# -*- coding: utf-8 -*-



class Filter3:
    def __init__(self):
        self.__energyshift_value = 0.0
        self.__energyshift_range = [3000.0, 0.2]  # [max,min]
        self.__energyshift_sw = 0
        self.__slitposition = 0
        self.__slitwidth_value = 0.0
        self.__slitwidth_range = [48.0, 0.2]
        # Omage Auto Tune
        self.__omega_status = 0
        self.__omega_method = 0 
        self.__omega_cam = 0
        self.__omega_time = 0
        self.__omega_crs = 1
        self.__omega_fine = 1
    
    def GetEnergyShift(self):
        '''
        Summary:
            Get energy shift voltage(V). Variable range and unit can be obtained with GetEnergyShiftRange()

        Return: int
            energy shift.
        '''
        return self.__energyshift_value 
        
    def GetEnergyShiftRange(self):
        '''
        Summary:
            Get maximum and minimum valve.

        Return: int
            energy shift range.
        '''
        return self.__energyshift_range
        
    def GetEnergyShiftSw(self):
        '''
        Summary:
            Get energy shift status(ON or OFF)

        Return: int
            0=OFF, 1=ON
        '''
        return self.__energyshift_sw
        
    def GetSlitPosition(self):
        '''
        Summary:
            Get slit status(IN or OUT)

        Return: int
            0=OUT, 1=IN
        '''
        return self.__slitposition 
        
    def GetSlitWidth(self):
        '''
        Summary:
            Get slit width(eV). 
            Variable range and unit can be obtained with GetSlitWidthRange()

        Return: int
            slit width
        '''
        return self.__slitwidth_value
        
    def GetSlitWidthRange(self):
        '''
        Summary:
            Get maximum and minimum value(eV).

        Return: int
            slit width range
        '''
        return self.__slitwidth_range
        
    def SetEnergyShift(self, value):
        '''
        Summary:
            Set energy shift voltage(V). 
            Variable range and unit can be obtained with GetEnergyShiftRange()

        Args:
            value: int
                energy shift value.
        '''
        if (type(value) is int):
            value = float(value)
        if(type(value) is float):
            if(self.__energyshift_range[0] <= value and value <= self.__energyshift_range[1]):
                self.__energyshift_value = value
        return 

    def SetEnergyShiftSw(self, sw):
        '''
        Summary:
            ON/OFF energy shift.

        Args:
            sw: int
                0=OFF, 1=ON
        '''
        if (type(sw) is int):
            if(sw == 0 or sw == 1):
                self.__energyshift_sw = sw
        return 

    def SetSlitPosition(self, sw):
        '''
        Summary:
            IN/OUT slit.

        Args:
            sw: int
                0=OUT, 1=IN
        '''
        if (type(sw) is int):
            if(sw == 0 or sw == 1):
                self.__slitposition = sw
        return 

    def SetSlitWidth(self, value):
        '''
        Summary:
            Set slit width(eV). 
            Variable range and unit can be obtained with GetSlitWidthRange()

        Args:
            value: int
                slit width
        '''
        if (type(value) is int):
            value = float(value)
        if(type(value) is float):
            if(self.__slitwidth_range[0] <= value and value <= self.__slitwidth_range[1]):
                self.__slitwidth_value = value
        return 
                
    def SetOmegaAutoTune(self, method, cam, time, crs, fine):
        """
        Summary:        
            Omega Autotune setting change
        Args: (int)method, (int)cam, (int)time, (int)crs, (int)fine
            * method-> 0=Crs+Fine, 1=Fine, 2=Crs, 3=SuperFine
            * cam-> camera kind. (detector id)
            * time-> exposure time.
            * crs-> Threshold coefficient for coarse processing.
            * fine-> Threshold coefficient for fine processing 
        Return: 
            None
        """
        self.__omega_method = method
        self.__omega_cam = cam
        self.__omega_time = time
        self.__omega_crs = crs
        self.__omega_fine = fine
        return 
    
    def GetOmegaAutoTune(self):
        """
        Summary:        
            Get Omega Autotune setting.
        Args: 
            no argument.
        Return: list((int)sw, (int)method, (int)cam, (int)crs, (int)fine)
            * sw-> 0=off, 1=on
            * method-> 0=Crs+Fine, 1=Fine, 2=Crs, 3=SuperFine
            * cam-> camera kind. (detector id)
            * time-> exposure time.
            * crs-> Threshold coefficient for coarse processing.
            * fine-> Threshold coefficient for fine processing 
        """
        res = []
        res.append(self.__omega_status) # 動作状態
        res.append(self.__omega_method) # 手法
        res.append(self.__omega_cam) # カメラ種類変更
        res.append(self.__omega_time) # カメラ露光時間
        res.append(self.__omega_crs) # Crs処理用 閾値 係数
        res.append(self.__omega_fine) # Fine処理用 閾値 係数
        return res

    def OmegaAutoTuneExec(self, sw):
        """
        Summary:        
            Execute Omega Autotune.
        Args: (int)sw
            * sw-> 0=off, 1=on
        Return: NoneType
            None
        """
        self.__omega_status = sw
        return 






