# -*- coding: utf-8 -*-



class Lens3:
    _ins = None
    def __init__(self):
        self.__lensID_count = 26
        self.__value_range = [0, 65535]
        self.__flc_info = []  # [sw, value]
        for i in range(self.__lensID_count):
            self.__flc_info.append([0,8000])   
            
        self.__cl1 = 0
        self.__cl2 = 1
        self.__cl3 = 2
        self.__cm = 3
        self.__olc = 6
        self.__olf = 7
        self.__om = 8
        self.__om2 = 9
        self.__il1 = 10
        self.__il2 = 11
        self.__il3 = 12
        self.__il4 = 13
        self.__pl1 = 14
        self.__pl2 = 15
        self.__pl3 = 16
        self.__flc = 19
        self.__flf = 20
        self.__flc1 = 21
        self.__flc2 = 21
        self.__olsuperfine_sw = 0
        self.__olsuperfine_value = 0
        self.__om2_flag = 0
        self.__diff = 0

    def __new__(cls):
        if cls._ins == None:
            cls._ins = super().__new__(cls)
        return cls._ins

    def __set_method(self, kind, value):
        """
            Private method.
            target method is Set***()
        """
        if (type(value) is int):
            if(self.__value_range[0] <= value and value <= self.__value_range[1]):
                self.__flc_info[kind] = [self.__flc_info[kind][0],value]

    def __set_sw_method(self, kind , sw):
        if (type(sw) is int):               
            if(sw == 0 or sw == 1):
                for i in range(self.__lensID_count):
                    self.__flc_info[kind] = [sw,self.__flc_info[kind][1]]




################################ GET ##########################################

    def GetCL1(self):
        '''
        Summary:
            Get CL1 value. This returns I/O output value. 

        Return: int
            CL1 value.
        '''
        return self.__flc_info[self.__cl1][1]
        
    def GetCL2(self):
        '''
        Summary:
            Get CL2 value. This returns I/O output value. 

        Return: int
            CL2 value.
        '''
        return self.__flc_info[self.__cl2][1]

    def GetCL3(self):
        '''
        Summary:
            Get CL3 value. This returns I/O output value. 

        Return: int
            CL3 value.
        '''
        return self.__flc_info[self.__cl3][1]
        
    def GetCM(self):
        '''
        Summary:
            Get CM value. This returns I/O output value. 

        Return: int
            CM value.
        '''
        return self.__flc_info[self.__cm][1]

    def GetFLCInfo(self, lensID):
        '''
        Summary:
            Get Free Lens Control information. 

        Args: 
            lensID: int
                0=CL1,1=CL2,2=CL3,3=CM,4=reserve,5=reserve, 6=OL Coarse, 7=OLFine,
                8= OM1, 9=OM2,10=IL1,11=IL2,12=IL3,13=IL4,14=PL1,15=PL2,16=PL3,17=reserve,
                18=reserve,19=FLCoarse,20=FLFine,21=FLRatio,22=reserve,23=reserve,24=reserve,25=reserve

        Return: int
            0=OFF, 1=ON
        '''
        if(type(lensID) is int):
            if(lensID < len(self.__flc_info)):
                return self.__flc_info[lensID]
        return 
        
    def GetFLc(self):
        '''
        Summary:
            Get FL Coarse value. This returns I/O output value. 

        Return: int
            FLc value.
        '''
        return self.__flc_info[self.__flc][1]

    def GetFLcomp1(self):
        '''
        Summary:
            Get FL Compo1 value. This returns I/O output value. 

        Return: int
            FLcomp1 value
        '''
        return self.__flc_info[self.__flc1][1]
        
    def GetFLcomp2(self):
        '''
        Summary:
            Get FL Compo2 value. This returns I/O output value. 

        Return: int
            FLcomp2 value
        '''
        return self.__flc_info[self.__flc2][1]

    def GetFLf(self):
        '''
        Summary:
            Get FL Fine value. This returns I/O output value. 

        Return: int
            FL Fine value
        '''
        return self.__flc_info[self.__flf][1]
                
    def GetIL1(self):
        '''
        Summary:
            Get IL1 value. This returns I/O output value. 

        Return: int
            IL1 value
        '''
        return self.__flc_info[self.__il1][1]

    def GetIL2(self):
        '''
        Summary:
            Get IL2 value. This returns I/O output value. 

        Return: int
            IL2 value
        '''
        return self.__flc_info[self.__il2][1]
                
    def GetIL3(self):
        '''
        Summary:
            Get IL3 value. This returns I/O output value. 

        Return: int
            IL3 value
        '''
        return self.__flc_info[self.__il3][1]

    def GetIL4(self):
        '''
        Summary:
            Get IL4 value. This returns I/O output value. 

        Return: int
            IL4 value
        '''
        return self.__flc_info[self.__flc1][1]
                
    def GetOLSuperFineSw(self):
        '''
        Summary:
            Get OL Super fine status. 

        Return: int
            0=OFF, 1=ON
        '''
        return self.__olsuperfine_sw

    def GetOLSuperFineValue(self):
        '''
        Summary:
            Get OL Super fine value. 

        Return: int
            OL super fine value.
        '''
        return self.__olsuperfine_value

    def GetOLc(self):
        '''
        Summary:
            Get OL Coarse value. 

        Return: int
            OL Coarse value.        
        '''
        return self.__flc_info[self.__olc][1]

    def GetOLf(self):
        '''
        Summary:
            Get OL Fine value. 

        Return: int
            OL Fine value.        
        '''
        return self.__flc_info[self.__olf][1]

    def GetOM(self):
        '''
        Summary:
            Get OM value. 

        Return: int
            OM value.        
        '''
        return self.__flc_info[self.__om][1]

    def GetOM2(self):
        '''
        Summary:
            Get OM2 value. 

        Return: int
            OM2 value.        
        '''
        return self.__flc_info[self.__om2][1]

    def GetOM2Flag(self):
        '''
        Summary:
            Get OM2 polarity.

        Return: int
            0=The same polarity as OM1, 1=The contrary to OM1
        '''
        return self.__om2_flag

    def GetPL1(self):
        '''
        Summary:
            Get PL1 value. 

        Return: int
            PL1 value.        
        '''
        return self.__flc_info[self.__pl1][1]

    def GetPL2(self):
        '''
        Summary:
            Get PL2 value. 

        Return: int
            PL2 value.        
        '''
        return self.__flc_info[self.__pl2][1]

    def GetPL3(self):
        '''
        Summary:
            Get PL3 value. 

        Return: int
            PL3 value.        
        '''
        return self.__flc_info[self.__pl3][1]

    def GetLensInfo(self, lensID):
        '''
        Summary:
            Get the lens data.
        Args: (int)lensID
            lensID->
                0=CL1, 1=CL2, 2=CL3, 3=CM, 4=reserve, 5=reserve, 6=OL Coarse,
                7=OL Fine, 8=OM1, 9=OM2, 10=IL1, 11=IL2, 12=IL3, 13=IL4, 14=PL1, 15=PL2,
                16=PL3, 17=reserve, 18=reserve, 19=FL Coarse, 20=FL Fine, 21=FL Ratio,
                22=reserve, 23=reserve, 24=reserve, 25=reserve
        Return: (int)
            absolute value (dec)
        '''
        if(type(lensID) is int):
            if(lensID < len(self.__flc_info)):
                return self.__flc_info[lensID][1]
        return 


################################## SET ########################################
        
    def SetFLCAbs(self, lensID, value):
        '''
        Summary:
            Set lens value for Free Lens Control.

        Args: 
            lensID:
                0=CL1, 1=CL2, 2=CL3, 3=CM, 4=reserve, 5=reserve, 6=OL Coarse,
                7=OL Fine, 8=OM1, 9=OM2, 10=IL1, 11=IL2, 12=IL3, 13=IL4, 14=PL1, 15=PL2,
                16=PL3, 17=reserve, 18=reserve, 19=FL Coarse, 20=FL Fine, 21=FL Ratio,
                22=reserve, 23=reserve, 24=reserve, 25=reserve
            value: 
                absolute value, 0-65535
        '''
        if 0 <= lensID and lensID < self.__lensID_count: 
            self.__set_method(lensID, value)
        # if (type(lensID) is int and type(value) is int):               
        #     if((self.__value_range[0] <= value and value <= self.__value_range[1])
        #     and (0 <= lensID and lensID <= self.__lensID_count)):
        #         self.__flc_info[lensID] = [self.__flc_info[lensID][0],value]
        return
        
    def SetFLCRel(self, lensID, value):
        '''
        Summary:
            Increase or decrease lens value for Free Lens Control.

        Args: 
            lensID:
                0=CL1, 1=CL2, 2=CL3, 3=CM, 4=reserve, 5=reserve, 6=OL Coarse,
                7=OL Fine, 8=OM1, 9=OM2, 10=IL1, 11=IL2, 12=IL3, 13=IL4, 14=PL1, 15=PL2,
                16=PL3, 17=reserve, 18=reserve, 19=FL Coarse, 20=FL Fine, 21=FL Ratio,
                22=reserve, 23=reserve, 24=reserve, 25=reserve
            value: 
                absolute value, 0-65535
        '''
        if (type(lensID) is int and type(value) is int):              
            if (0 <= lensID and lensID <= self.__lensID_count):
                value = self.__flc_info[lensID][1] + value
                self.__set_method(lensID, value)
                # if(self.__value_range[0] <= temp_value and temp_value <= self.__value_range[1]):
                #     self.__flc_info[lensID] = [self.__flc_info[lensID][0],temp_value]
        return
        
    def SetFLCSw(self, lensID, sw):
        '''
        Summary:
            Set lens switch for Free lens Control.

        Args: 
            lensID:
                0=CL1, 1=CL2, 2=CL3, 3=CM, 4=reserve, 5=reserve, 6=OL Coarse,
                7=OL Fine, 8=OM1, 9=OM2, 10=IL1, 11=IL2, 12=IL3, 13=IL4, 14=PL1, 15=PL2,
                16=PL3, 17=reserve, 18=reserve, 19=FL Coarse, 20=FL Fine, 21=FL Ratio,
                22=reserve, 23=reserve, 24=reserve, 25=reserve
            sw: 
                0=OFF, 1=ON
        '''
        if (type(lensID) is int and type(sw) is int):               
            if((sw == 0 or sw == 1)
            and (0 <= lensID and lensID <= self.__lensID_count)):
                self.__flc_info[lensID] = [sw,self.__flc_info[lensID][1]]
        return
        
    def SetFLCSwAllLens(self, sw):
        '''
        Summary:
            Set Lens switch for Free Lens Control.

        Args: 
            sw: 
                0=OFF, 1=ON
        '''
        for kind in range(self.__lensID_count):
            self.__set_sw_method(kind, sw)
        # if (type(sw) is int):               
        #     if(sw == 0 or sw == 1):
        #         for i in range(self.__lensID_count):
        #             self.__flc_info[i] = [sw,self.__flc_info[i][1]]
        return


    def SetCL3(self, value):
        '''
        Summary:
            Set CL3 value(without MAG link).
            
        Args: 
            value: int 
                range (0-65535)
        '''
        self.__set_method(self._cl3, value)
        return
        
    def SetDiffFocus(self, value):
        '''
        Summary:
            Increase or decrease value for DIFF Focus(without MAG link). 
            
        Args: 
            value: int 
                range (0-65535)
        '''
        if(type(value) is int):
            if(self.__value_range[0] <= value and value <= self.__value_range[1]):
                self.__diff = value
        return
    
    def SetFLc(self, value):
        '''
        Summary:
            Increase or decrease value for FLC(without MAG link). 
            
        Args: 
            value: int 
                range (0-65535)
        '''
        self.__set_method(self.__flc, value)
        return
      
    def SetFLf(self, value):
        '''
        Summary:
            Increase or decrease value for FLF(without MAG link). 
            
        Args: 
            value: int 
                range (0-65535)
        '''
        self.__set_method(self.__flf, value)
        return     
    
    def SetILFocus(self, value):
        '''
        Summary:
            Increase or decrease value for IL Focus(without MAG link). 
            
        Args: 
            value: int 
                range (0-65535)
        '''
        self.__set_method(self.__il1, value)
        return     
    
    def SetNtrl(self, value):
        '''
        Summary:
            NTRL within only value range. 
            
        Args: 
            value: int 
                0=Brightness, 1=OBJ Focus, 2=DIFF Focus, 3=IL Focus, 4=PL Focus, 5=FL Focus
        '''
        if (type(value) is int):
            if(value == 5):
                self.__flc_info[self.__flf] = [self.__flc_info[self.__flf][0], 0]
            if(value == 2):
                self.__diff = 0
        return     
    
    def SetOLSuperFineNeutral(self):
        '''
        Summary:
            Set Neutral of OL Super Fine. 
                * Neutral:800(H)
        
        Args:
            None
        '''
        self.__olsuperfine_value = 0
        return     
    
    def SetOLSuperFineSw(self, sw):
        '''
        Summary:
            Set OL Super fine status. 
        
        Args:
            sw:
                0=OFF, 1=ON
        '''
        if (type(sw) is int):
            if(sw == 0 or sw == 1):
                self.__olsuperfine_sw = sw
        return     
    
    def SetOLSuperFineValue(self, value):
        '''
        Summary:
            Set OL Super fine value. 
        
        Args:
            value:
                range(0-65535)
        '''
        if (type(value) is int):
            if(self.__value_range[0] <= value and value <= self.__value_range[1]):
                self.__olsuperfine_value= value
        return     
    
    def SetOLc(self, value):
        '''
        Summary:
            Set OLC value(without MAG link).
        
        Args:
            value:
                range(0-65535)
        '''
        self.__set_method(self.__olc, value)
        return     
    
    def SetOLf(self, value):
        '''
        Summary:
            Set OLF value(without MAG link).
        
        Args:
            value:
                range(0-65535)
        '''
        self.__set_method(self.__olf, value)
        return     
    
    def SetPLFocus(self, value):
        '''
        Summary:
            Increase or decrease value for PL Focus(without MAG link). 
        
        Args:
            value:
                range(0-65535)
        '''
        self.__set_method(self.__pl1, value)
        return     
    

### Ver.1.2

    def SetOM(self, value):
        '''
        Summary:
            Set OM value(without MAG link).
        
        Args:
            value:
                range(0-65535)
        '''
        self.__set_method(self.__om, value)
        return     

    def SetStdFocus(self):
        """
        Summary:
            Execute Load Standard Focus value.
        """
        value = 8000
        self.__set_method(self.__olc, value)
        self.__set_method(self.__olf, value)
        self.__set_method(self.__om, value)
        self.__set_method(self.__om2, value)
        return  


