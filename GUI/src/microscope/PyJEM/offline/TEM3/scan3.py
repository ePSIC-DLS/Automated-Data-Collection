# -*- coding: utf-8 -*-



class Scan3:
    def __init__(self):
        self.__rotationangle_range = [0, 359]
        self.__scanmode = 0
        self.__noisecanceller_value = 0
        self.__rotationangle  = 0
        self.__scandatamode = 0
        self.__dataabs = 0
    
    def GetExtScanMode(self):
        '''
        Summary:
            Get whether External scan is going on.
        
        Return: int
            0=OFF, 1=ON
        '''
        return self.__scanmode 
        
    def GetNoiseCancellerVal(self):
        '''
        Summary:
            Get Noise Canceller value. 
                * This works for ARM200F and ARM300F.
        
        Return: int
        '''
        return self.__noisecanceller_value
        
    def GetRotationAngle(self):
        '''
        Summary:
            Get Scan Rotation angle(degree).
        
        Return: int
            0-359 (degree)
        '''
        return self.__rotationangle 
        
    def SetExtScanMode(self, sw):
        '''
        Summary:
            Allow External scan.
        
        Args:
            sw: 
                0=OFF, 1=ON
        '''
        if (type(sw) is int):
            if(sw == 0 or sw == 1):
                self.__scanmode = sw
        return 
        
    def SetRotationAngle(self, value):
        '''
        Summary:
            Set Scan Rotation angle.(degree)
        
        Args:
            value: 
                0-359 (degree)
        '''
        if (type(value) is int):
            if(self.__rotationangle_range[0] <= value and value <= self.__rotationangle_range[1]):
                self.__rotationangle  = value
        
    def SetScanDataAbs(self, mode, value):
        '''
        Summary:
            Set Scan Data Value. 
        
        Args:
            mode: 
                0=Mag Adjust H 1=Mag Adjust V, 2=Rotation H, 3=Rotation V, 
                4=Correction H, 5=Correction V, 6=Offset H, 7=Offset V 
            value: 
                absolute value. 0-65535
        '''
        if(type(mode) is int and type(value) is int):
            self.__dataabs = value
            self.__scandatamode = mode
        return