# -*- coding: utf-8 -*-
import time


class FEG3:
    _ins = None
    def __init__(self):
#        self.__sizelist = ["Open", "1", "2", "3", "4"]
#        self.kindlist = ["Nothing", "CLA", "OLA", "HCA", "SAA", "ENTA", "EDS"]
        self.__beamvalve = 0  # 0:Open, 1:Close
        self.__v1ready = 1
        self.__size = 0
        self.__emissionoff = 0    #　なぜSetで引数が必要なのか分からないがあるので変数作成
        self.__autoflashing_status = 0
        self.__emissionon_status = [0,0]
        
    def __new__(cls):
        if cls._ins == None:
            cls._ins = super().__new__(cls)
        return cls._ins
        
    def GetBeamValve(self):
        '''
        Summary:
            Get FEGUN valve status. This works for FEG and 3100EF.

        Return: int
            0=Close, 1=Open
        '''
        return self.__beamvalve 
        
    def GetV1Ready(self):
        '''
        Summary:
            Get V1 Ready status. This works for ARM200F

        Return: int
            0=Not Ready, 1=Ready
        '''
        return self.__v1ready
        
    def SetBeamValve(self, mode):
        '''
        Summary:
            Open/Close FEGUN valve. This works for FEG and 3100EF.

        Args:
            mode: int
                0=Close, 1=Open
        '''
        if (type(mode) is int):
            if (mode == 0 or mode == 1):
                self.__beamvalve = mode
        return 
        
    def SetFEGEmissionOff(self, value):
        '''
        Summary:
            Set FEG Emission OFF. This works for ARM200F
        Args:        
            value: int
                0=Close, 1=Open
        '''
        if(type(value) is int):
#            if (0 <= size and size <= len(self.__size)):
            self.__emissionoff = value
        return
    
    
#### Ver.1.2
    
    def ExecAutoFlashing(self, val):
        """
        Summary:
            This command is used to start or stop the 'AutoFlashing' method.
        Args:
            val:
                0: Stop
                1: Start
        Return:
            -1: Not ready
            0: Stop
            1: Start
        """
        if self.__autoflashing_status == 1:
            return -1
        
        self.__autoflashing_status = 1
        
        time.sleep(5)
        
        self.__autoflashing_status = 0
        return self.__autoflashing_status
    
    def ExecEmissionOn(self, val):
        """
        Summary:
            This command is used to start or stop the 'EmissionON' method.
        Args:
            val: start/stop
                0: Stop
                1: Start
        Return :
            -1: Not ready
            0: Stop
            1: Start                
        """
        if self.__autoflashing_status == 1:
            return -1
        self.__autoflashing_status = 1
        
        time.sleep(10)
        
        self.__autoflashing_status = 0
        return self.__autoflashing_status
    
    def GetAutoFlashingStatus(self):
        """
        Summary:
            This command is used to get the AutoFlashing status.
        Return:
            -1:Error
            0:Idle
            1:Running
        """
        return self.__autoflashing_status
    
    def GetEmissionOnStatus(self):
        """
        Summary:
            This command is used to get the ExecEmissionON() method's phase.
        Return:
            list:
                [0]: Execution Phase: 
                    -1: Error
                    0: Idle
                    1: Running
                [1]: Emission Status
                    0: OFF
                    1: ON
        """
        return self.__emissionon_status
    
    
    
    
    
    