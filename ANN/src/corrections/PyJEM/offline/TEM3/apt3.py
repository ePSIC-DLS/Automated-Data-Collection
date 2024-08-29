# -*- coding: utf-8 -*-


class Apt3:
    class __Data:
        def __init__(self, pos, size):
            self.position = pos
            self.size = size
            
        
    def __init__(self):
        self.__count = 7
        self.__count_exp = 10

        position = [128, 128]
        size = 0
        
        self.__kind = 0
        self.__normal = []
        for i in range(self.__count):
            self.__normal.append(self.__Data(position, size))

        self.__expkind = 0
        self.__exp = []
        for i in range(self.__count_exp):
            self.__exp.append(self.__Data(position, size))
    
    def GetKind(self):
        '''
        Summary:
            Get the type of selected Aperture. Below is the Aperture indicated by the Return.
        
        Return: int
            0=Nothing, 1=CLA, 2=OLA, 3=HCA, 4=SAA, 5=ENTA, 6=EDS
        '''
        return self.__kind 
        
    def GetPosition(self):
        '''
        Summary:
            Get Aperture position. The Selected Aperture is the Reading Target.
        
        Return: list
            [x, y]
        '''
#        return self.__position
        return self.__normal[self.__kind].position
        
    def GetSize(self, kind):
        '''
        Summary:
            Get aperture hole number.

        Return: int
            0=Open, 1-4= hole number
        '''
#        return self.__size
        return self.__normal[kind].size
        
    def SelectKind(self, kind):
        '''
        Summary:
            Select aperture kind to operate.

        Args: int
            kind: 
                0=Nothing 1=CLA, 2=OLA, 3=HCA, 4=SAA, 5=ENTA, 6=EDS
        '''
        if (type(kind) is int):
            if (kind < self.__count):
                self.__kind = kind
        return 
        
    def SetPosition(self, x, y):
        '''
        Summary:
            Set aperture position. 
            The selected aperture is the operation target.

        Args: 
            x: int
                0-4095
            y: int
                0-4095 
        '''
        if((type(x) is int) and (type(y) is int)):
            self.__normal[self.__kind].position = [x, y]
#            self.__position = [x, y]
        return 
        
    def SetSize(self, size):
        '''
        Summary:
            Set aperture hole number.
            The selected aperture is the operation target.
        
        Args: 
            size: int
                0=Open, 1-4= hole number
        '''
        if(type(size) is int):
            self.__normal[self.__kind].size = size            
#            self.__size = size
        return
        
    #### aperture ex ### 
    def GetExpKind(self):
        '''
        Summary:
            Get the type of selected Aperture. Below is the Aperture indicated by the Return.
        
        Return: int
            0=CL1, 1=CL2, 2=OL, 3=HC, 4=SA, 5=ENT, 6=HX, 7=BF
        '''
        return self.__expkind 

    def GetExpSize(self, kind):
        '''
        Summary:
            Get aperture hole number.

        Return: int
            0=Open, 1-4= hole number
        '''
        return self.__exp[self.__expkind].size

    def SelectExpKind(self, kind):
        '''
        Summary:
            Select aperture kind to operate.

        Args: int
            kind: 
                0=CL1, 1=CL2, 2=OL, 3=HC, 4=SA, 5=ENT, 6=HX, 7=BF
        '''
        if (type(kind) is int):
            if (kind < self.__count_exp):
                self.__expkind = kind
        return 

    def SetExpSize(self, kind, size):
        '''
        Summary:
            Set aperture hole number.
            The selected aperture is the operation target.
        
        Args: 
            kind: 
                0=CL1, 1=CL2, 2=OL, 3=HC, 4=SA, 5=ENT, 6=HX, 7=BF
            size: int
                0=Open, 1-4= hole number
        '''
        if((type(size) is int) and (type(kind) is int)):
#            if (0 <= size and size <= len(self.__size)):
            self.__expkind = kind
            self.__exp[self.__expkind].size = size
        return        
    
    def SetPhasePlateToNext():
        '''
        Summary:
            Move to next position.
            * only Cryo ARM.
        
        Return: None
        '''        
        return
    
    def GetPhasePlateState():
        '''
        Summary:
            Get plate move state.
            * only Cryo ARM.
        
        Return: int 
            0=Stop, 1=Moving
        '''
        sw = 0
        return sw
    
