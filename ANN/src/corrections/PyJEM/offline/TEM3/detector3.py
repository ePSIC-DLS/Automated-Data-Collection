# -*- coding: utf-8 -*-


class Detector3:
    def __init__(self):
#        self.sizelist = ["Open", "1", "2", "3", "4"]
#        self.kindlist = ["Nothing", "CLA", "OLA", "HCA", "SAA", "ENTA", "EDS"]
        self.__contbrt_range = [0,4095]
        self.__brt = {}
        self.__cont = {}
        self.__sw = {}
        self.__position = {}
        self.__screen = 0     #Getが無いのでいらないかも
    
    def GetBrt(self, detectID):
        '''
        Summary:
            Get Brightness of detector.

        Args:
            detectID: int
                DetectorID

        Return: int
            brightness value
        '''
        if(type(detectID) is int):
            if (detectID not in self.__brt):
                self.__brt.update({detectID:0})            
            return self.__brt[detectID]
        return #typeError
        
    def GetCont(self, detectID):
        '''
        Summary:
            Get Contrast of detector.

        Args:
            detectID: int
                DetectorID

        Return: int
            contrast value
        '''
        if(type(detectID) is int):
            if (detectID not in self.__cont):
                self.__cont.update({detectID:0})            
            return self.__cont[detectID]
        return #typeError
        
    def GetImageSw(self, detectID):
        '''
        Summary:
            Get input status from detector.

        Args:
            detectID: int
                DetectorID

        Return: int
            0=OUT, 1=IN
        '''
        if(type(detectID) is int):
            if (detectID not in self.__sw):
                self.__sw.update({detectID:0})            
            return self.__sw[detectID]
        return #typeError
        
    def GetPosition(self, detectID):
        '''
        Summary:
            Get Detector control.

        Args:
            detectID: int
                DetectorID

        Return: int
            0=OUT, 1=IN
        '''
        if(type(detectID) is int):
            if (detectID not in self.__position):
                self.__position.update({detectID:0})            
            return self.__position[detectID]
        return #typeError
        
    def SetBrt(self, detectID, value):
        '''
        Summary:
            Set Brightness of detector.

        Args:
            detectID: int
                target detector ID.
            value: int
                brightness value. range(0-4095)
        '''
        if((type(detectID) is int) and (type(value) is int)):
            if(self.__contbrt_range[0] <= value and value <= self.__contbrt_range[1]):
                if (detectID not in self.__brt):
                    self.__brt.update({detectID:value})  
                else:
                    self.__brt[detectID] = value               
        return 
        
    def SetCont(self, detectID, value):
        '''
        Summary:
            Set Contrast of detector.

        Args:
            detectID: int
                target detector ID.
            value: int
                contrast value. range(0-4095)
        '''
        if((type(detectID) is int) and (type(value) is int)):
            if (detectID not in self.__cont):
                self.__cont.update({detectID:value})  
            else:
                self.__cont[detectID] = value               
        return 
        
    def SetImageSw(self, detectID, value):
        '''
        Summary:
            ON/OFF input signal from detector.

        Args:
            detectID: int
                target detector ID
            value: int 
                0=OUT, 1=IN
        '''
        if((type(detectID) is int) and (type(value) is int)):
            if(self.__contbrt_range[0] <= value and value <= self.__contbrt_range[1]):
                if (detectID not in self.__sw):
                    self.__sw.update({detectID:value})  
                else:
                    self.__sw[detectID] = value               
        return 
        
    def SetPosition(self, detectID, sw):
        '''
        Summary:
            Detector control.

        Args:
            detectID: int
                target detector ID
            value: int 
                0=OUT, 1=IN
        '''
        if((type(detectID) is int) and (type(sw) is int)):
            if(sw == 0 or sw ==1):
                if (detectID not in self.__position):
                    self.__position.update({detectID:sw})  
                else:
                    self.__position[detectID] = sw               
        return 
        
    def SetScreen(self, value):
        '''
        Summary:
            Screen control.

        Args:
            value: int
                0=0(deg), 1=7(deg), 2=90(deg)
        '''
        if(type(value) is int):
            self.__screen = value
        return
        
#### Ver.1.0.3        
    def GetContBrtInfo(self, detectID):
        '''
        Summary:
            Get Contrast of detector.

        Args:
            detectID: int
                DetectorID

        Return: int
            contrast value
        '''
        if(type(detectID) is int):
            if (detectID not in self.__cont):
                self.__cont.update({detectID:0})
            if (detectID not in self.__brt):
                self.__brt.update({detectID:0})            
            return [self.__brt[detectID], self.__cont[detectID]]
        return #typeError
        
        
#### Ver.1.2
    def GetScreen(self):
        """
        Summary:
            Screen control.
        Return: int
            0:0degree/1:7degree/2:90degree
        """
        return self.__screen
        
        
        
        
        
        
        
        
        
        
        
        
        
        