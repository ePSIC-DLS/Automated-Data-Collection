# -*- coding: utf-8 -*-


import time

class Camera3:
    def __init__(self):
#        self.__filmload_mode_list = ["Manual", "Auto1", "Auto2"]
#        self.__shutterspeed_mode_list = ["Manual", "Automatic", "BULB"]
#        self.__photomode_list = ["Normal", "Bulb", "Multi Exposure", "TF", "AMS", "MDS"]
#        self.__shutterposition_list = ["Open", "Close", "Expose"]
#        self.__status_list = ["Rest", "Imaging"]
        self.__expshutter_range = [0.1, 180.0]
        self.__exptime = 0.0
        self.__electric_density = 0.0
        self.__filmload_mode = 0
        self.__shutterspeed_mode = 0
        self.__photomode = 0
        self.__shutterposition = 0
        self.__status = 0
        self.__unused = 50
    
    def ExposeShutter(self, value):
        '''
        Summary:
            Open shutter and close it after wait. (sec)
            
        Args:
            value: int
                0.1-180.0 (sec)
        '''
        if(type(value) is int):
            if(self.__expshutter_range[0] <= value and value <= self.__expshutter_range[1]):
                time.sleep(2)
        return 
        
    def GetCurrentDensity(self):
        '''
        Summary:
            Get electric current density. Converted value to film plane.(pA/cm2)
        
        Return: int
            currently density.
        '''
        return self.__electric_density
        
    def GetExpTime(self):
        '''
        Summary:
            Get exposure time(sec).

        Return: int
            0-180.0 (sec)
        '''
        return self.__exptime
      
    def GetFilmLoadingMode(self):
        '''
        Summary:
            Get film loading mode.

        Return: int
            0=Manual, 1=Auto(Load film to imaging position before photography), 2=Auto(Load film to imaging position after photography)
        '''
        return self.__filmload_mode 
        
    def GetMode(self):
        '''
        Summary:
            Get the way to set shutter speed.

        Return: int
            0=Manual exposure, 1=Automatic exposure, 2=BULB
        '''
        return self.__shutterspeed_mode
        
    def GetPhotoMode(self):
        '''
        Summary:
            Get photo mode.

        Return: int
            0=Normal, 1=Bulb, 2=Multi Exposure, 3=TF, 4=AMS, 5=MDS
        '''
        return self.__photomode
        
    def GetShutterPosition(self):
        """
        Summary:
            Get shutter status.

        Return: int
            0=Open, 1=Close, 2=Expose
        """
        return self.__shutterposition
        
    def GetStatus(self):
        """
        Summary:
            Get photography status.
            
        Return: int
            0=Rest, 1=Imaging
        """
        return self.__status
        
    def GetUnused(self):
        return self.__unused
        
    def SelectFilmLoadingMode(self, mode):
        '''
        Summary:
            Select film loading mode.
            
        Args: 
            mode: int
                0=Manual, 1=Auto(Load film to imaging position before photography), 2=Auto(Load film to imaging position after photography)
        '''
        if (type(mode) is int):
            #raise TypeError()
#            if (0 <= kind and kind <= len(self.kindlist)):
            self.__filmload_mode = mode
        return 
        
    def SelectMode(self, mode):
        '''
        Summary:
            Select the way to set Shutter Speed.

        Args: 
            mode: int
                0=Manual exposure, 1=Automatic exposure, 2=BULB   
        '''
        if (type(mode) is int):
#            if (0 <= kind and kind <= len(self.kindlist)):
            self.__shutterspeed_mode = mode
        return 
        
    def SetExpTime(self, exp_time):
        '''
        Summary:
            Set exposure time(sec). 

        Args: 
            exp_time: int
                0-180.0 (sec) 
        '''
        if(type(exp_time) is int):
            exp_time = float(exp_time)
        if(type(exp_time) is float):
            if(self.__expshutter_range[0] <= exp_time and exp_time <= self.__expshutter_range[1]):
                self.__exptime = exp_time
        return
        
    def SetShutterPosition(self, sw):
        '''
        Summary:
            Open/Close shutter. This does not work while imaging. Time out error occurs after 1 minute closing.

        Args: 
            sw: int
                0=Open, 1=Close
        '''
        if(type(sw) is int):
            if(sw == 0 or sw == 1):
                self.__shutterposition = sw
        return