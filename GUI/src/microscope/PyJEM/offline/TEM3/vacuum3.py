# -*- coding: utf-8 -*-



class VACUUM3:
    def __init__(self):
        self.__camera_air = 0     #valve_status以外0/1
        self.__camera_ready = 0
        self.__column_air = 0
        self.__column_ready = 0
        self.__specimen_air = 0
        self.__spec_evacstart = 0
        self.__specimen_ready = 0
        self.__valve_status = [17,3072,0] #取り合えず居室で出た値
        self.__pig_sw = 0
        self.__peg_sw = 0
        self.__peg_max = 9
        self.__pig_max = 9
        self.__peg_info = [(i, 0) for i in range(self.__peg_max)]
        self.__pig_info = [(i, 0) for i in range(self.__pig_max)]
    
    def GetCameraAir(self):
        '''
        Summary:
            Get Camera Air status. 
                * This works for ARM200F and ARM300F
        
        Return:
            0=Not Air, 1=Air
        '''
        return self.__camera_air 
        
    def GetCameraReady(self):
        '''
        Summary:
            Get Camera Ready status.
                * This works for ARM200F and ARM300F
        
        Return:
            0=Not Air, 1=Air
        '''
        return self.__camera_ready
        
    def GetColumnAir(self):
        '''
        Summary:
            Get Column Air status.
                * This works for ARM200F and ARM300F
        
        Return:
            0=Not Air, 1=Air
        '''
        return self.__column_air
        
    def GetColumnReady(self):
        '''
        Summary:
            Get Column Ready status.
                * This works for ARM200F and ARM300F
        
        Return:
            0=Not Air, 1=Air
        '''
        return self.__column_ready 
        
    def GetSpecimenAir(self):
        '''
        Summary:
            Get Specimen Air status.
                * This works for ARM200F and ARM300F
        
        Return:
            0=Not Air, 1=Air
        '''
        return self.__specimen_air
        
    def GetSpecimenPreEvacStart(self):
        '''
        Summary:
            Get Specimen previous evacuation Start status.
                * This works for ARM200F and ARM300F
        
        Return:
            0=Not Start, 1=Start
        '''
        return self.__spec_evacstart
  
    def GetSpecimenReady(self):
        '''
        Summary:
            Get Specimen Ready status.
                * This works for ARM200F and ARM300F
        
        Return:
            0=Not Air, 1=Air
        '''
        return self.__specimen_ready
  
    def GetValveStatus(self):
        '''
        Summary:
            Get valve status.
        
        Return: list
            * [0]= int: The number of the effective valves.
            * [1]= int: Bit the information represented in the OPEN/CLOSE of each valve.
            * [2]= int: Bit the information represented in the OPEN/CLOSE of each valve.

        '''
        return self.__valve_status
        
    def SetPegMonitorSw(self, sw):
        '''
        Summary:
            Set the penning gauge monitor (ON/OFF).
        Args: 
            no arguments.
        Return: int
            0=Off, 1=On
        '''
        if sw == 0 or sw == 1:
            self.__pig_sw = sw
        return 
        
    def SetPigMonitorSw(self, sw):
        '''
        Summary:
            Set the pirani  gauge monitor (ON/OFF).
        Args: 
            no arguments.
        Return: int
            0=Off, 1=On
        '''
        if sw == 0 or sw == 1:
            self.__peg_sw = sw
        return 

    def GetPegInfo(self, val):
        '''
        Summary:
            Get the penning gauge setting.
        Args: (int)val
            val-> select penning gauge. (0-9)
        Return: list((int)val, (int)sts)
            * val-> ACD value. (0-4095)
            * sts-> 0=Off, 1=High, 2=Low, 3=Ready
        '''
        if 0 <= val-1 and val-1 < self.__peg_max:
            return self.__peg_info[val-1]

    def GetPigInfo(self, val):
        '''
        Summary:
            Get the pirani gauge setting.
        Args: (int)val
            val-> select pirani gauge. (0-9)
        Return: list((int)val, (int)sts)
            * val-> ACD value. (0-4095)
            * sts-> 0=Off, 1=High, 2=Low, 3=Ready
        '''
        if 0 <= val-1 and val-1 < self.__pig_max:
            return self.__pig_info[val-1]
        
        
