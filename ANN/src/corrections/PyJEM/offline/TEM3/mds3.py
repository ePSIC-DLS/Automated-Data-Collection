# -*- coding: utf-8 -*-



class MDS3:
    def __init__(self):
        self.__mode = 0
    
    def EndMdsMode(self):
        '''
        Summary:
            Unset MDS mode. 
        '''
        self.__mode = 0
        return 
        
    def GetMdsMode(self):
        '''
        Summary:
            Get MDS mode.
        
        Return:
            0=OFF, 1=Search, 2=Focus, 3=Photoset
        '''
        return self.__mode
        
    def SetFocusMode(self):
        '''
        Summary:
            Set to MDS focus mode.
        '''
        self.__mode = 2
        return 

    def SetPhotosetMode(self):
        '''
        Summary:
            Set to MDS photoset mode.
        '''
        self.__mode = 3
        return 

    def SetSearchMode(self):
        '''
        Summary:
            Set to MDS search mode.
        '''
        self.__mode = 1
        return 
