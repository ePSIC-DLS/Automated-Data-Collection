# -*- coding: utf-8 -*-

"""
** detector ID **

0	--	
1	SEI	(Second electron detector)
2	EDS	(EDS detector)
3	BI-PRISM	(electron beam Bi-prism)
4	DFI-EF	(Scanning dark field electron detector for FEF)
5	TVCAM-U	(TV camera [Diff chamber])
6	SSCAM-U	(Slow scan camera [Diff chamber])
7	FARADAY-CAGE	(Faraday cage)
8	BS	(Beam stopper)
9	HRD	(High resolution electron diffraction holder)
10	DFI-U	(Scanning dark field electron detector [Observation chamber])
11	BFI-U	(Scanning bright field electron detector [Observation chamber])
12	SCR-F	(Small screen)
13	SCR-L	(Large screen)
14	DFI-B	(Scanning dark field electron detector [below camera chamber])
15	BFI-B	(Scanning bright field electron detector [below camera chamber])
16	SSCAM-B	(Slow scan camera [below camera chamber])
17	TVCAM-B	(TV camera [below camera chamber])
18	EELS	(Electron energy loss spectrometer)
19	TVCAM-GIF	(TV camera [GATAN energy filter])
20	SSCAM-GIF	(Slow scan camera [GATAN energy filter])
21	BEI-TOPO	
22	BEI-COMPO	
23	SEI-TOPO	
24	SEI-COMPO	
"""


class Def3:
    def __init__(self):
        self.__defID_count = 25
        self.__value_range = [0, 65535]
        self.__def_info = []
        for i in range(self.__defID_count):
            self.__def_info.append([32768,32768])   
            
        self.__gun1 = 0
        self.__gun2 = 1
        self.__cla1 = 2
        self.__cla2 = 3
        self.__cmp_s = 4
        self.__cmp_t = 5
        self.__cmt_a = 6
        self.__cls = 7
        self.__isc1 = 8
        self.__isc2 = 9
        self.__spa = 10
        self.__pla = 11
        self.__ols = 12
        self.__ils = 13
        self.__fls1 = 14
        self.__fls2 = 15
        self.__fla1 = 16
        self.__fla2 = 17
        self.__scan1 = 18
        self.__scan2 = 19
        self.__is_asid = 20
        self.__mag_adj = 21
        self.__rotation = 22
        self.__correction = 23
        self.__offset = 24
        
        self.__beambalnking = 0
        self.__detectalign = [0,0]
        self.__stema1c = [0,0]
        self.__stembeamtilt = [0,0]
        self.__stemstiga1 = [0,0]
        self.__stemstigb2 = [0,0]
        self.__stemuserbshift = [0,0]
        self.__tema1c = [0,0]
        self.__temdshift = [0,0]
        self.__temdistig = [0,0]
        self.__temstiga1 = [0,0]

################################## GET #######################################

    def GetAngBal(self):
        '''
        Summary:
            Get AngleBalance value. this returns I/O output value. 
                * Range: 0-65535

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__cmt_a]
        
    def GetBeamBlank(self):
        '''
        Summary:
            Get Beam branking status, 1:ON. 
            Branking method is defined on machine side.

        Return: int
            0=OFF, 1=ON
        '''
        return self.__beambalnking
        
    def GetCLA1(self):
        '''
        Summary:
            Get CLAlignment1 value. this returns I/O output value. 
                * Range: 0-65535

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__cla1]
        
    def GetCLA2(self):
        '''
        Summary:
            Get CLAlignment2 value. this returns I/O output value.
                * Range: 0-65535

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__cla2]

    def GetCLs(self):
        '''
        Summary:
            Get CLStig value. this returns I/O output value.
                * Range: 0-65535

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__cls]
        
    def GetCorrection(self):
        '''
        Summary:
            Get Collection value. this returns I/O output value.
                * Range: 0-65535

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__correction]        
        
    def GetDetAlign(self, arg1):
        '''
        Summary:
            Get Alignment value for detector. It is necessary input target detector. this returns the variable corresponds to IS value overlapped to CLA.
                * Range: 0-65535

        Return: list
            [x, y]
        '''
        if type(arg1) is int:
            if 0 <= arg1 <= self.__defID_count:
                return self.__def_info[arg1]    
        return 
#        return self.__detectalign
        
    def GetFLA1(self):
        '''
        Summary:
            Get FLAlignment1 value. this returns I/O output value.
                * Range: 0-65535

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__fla1]
        
    def GetFLA2(self):
        '''
        Summary:
            Get FLAlignment2 value. this returns I/O output value.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__fla2]
        
    def GetFLs1(self):
        '''
        Summary:
            Get FLStig1 value. this returns I/O output value.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__fls1]

    def GetFLs2(self):
        '''
        Summary:
            Get FLStig2 value. this returns I/O output value.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__fls2]
        
    def GetGunA1(self):
        '''
        Summary:
            Get GunAlignment1 value. this returns I/O output value.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__gun1]
              
    def GetGunA2(self):
        '''
        Summary:
            Get GunAlignment2 value. this returns I/O output value.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__gun2]
        
    def GetILs(self):
        '''
        Summary:
            Get ILStig value. this returns I/O output value.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__ils]
        
    def GetIS1(self):
        '''
        Summary:
            Get ImageShift1 value. this returns I/O output value.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__isc1]
        
    def GetIS2(self):
        '''
        Summary:
            Get ImageShift2 value. this returns I/O output value.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__isc2]

    def GetMagAdjust(self):
        '''
        Summary:
            Get MagAdjust value. this returns I/O output value.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__mag_adj]
        
    def GetOLs(self):
        '''
        Summary:
            Get OLStig value. this returns I/O output value.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__ols]
        
    def GetOffset(self):
        '''
        Summary:
            Get Offset value. this returns I/O output value.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__offset]
        
    def GetPLA(self):
        '''
        Summary:
            Get PLAlign value. this returns I/O output value.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__pla]
        
    def GetRotation(self):
        '''
        Summary:
            Get Rotation value. this returns I/O output value.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__rotation]

    def GetScan1(self):
        '''
        Summary:
            Get Scan1 value. this returns I/O output value.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__scan1]
        
    def GetScan2(self):
        '''
        Summary:
            Get Scan2 value. this returns I/O output value.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__scan2]      
         
    def GetShifBal(self):
        '''
        Summary:
            Get ShiftBalance value. this returns I/O output value.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__cmp_s]      
        
    def GetSpotA(self):
        '''
        Summary:
            Get SpotAlignment value. this returns I/O output value.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__spa]

    def GetStemIS(self):
        '''
        Summary:
            Get IS value for ASID. The variable corresponds to IS value overlapped to CLA.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__is_asid]
        
    def GetTiltBal(self):
        '''
        Summary:
            Get TiltBalance value for ASID. The variable corresponds to IS value overlapped to CLA.
                * Range: 0-65535       

        Return: list
            [x, y]
        '''
        return self.__def_info[self.__cmp_t]
       

############################### SET #########################################

    def SetNtrl(self, def_id):
        '''
        Summary:
            NTRL of the region which is being accessed.

        Args:
            def_id: int 
                0=GUN1, 1=GUN2, 2=CLA1, 3=CLA2, 4=CMP-S, 5=CMP-T. 6=CMT-A, 7=CLS, 8=ISC1, 9=ISC2, 10=SPA,
                11=PLA, 12=OLS, 13=ILS, 14=FLS1, 15=FLS2, 16=FLA1, 17=FLA2, 18=SCAN1, 19=SCAN2,
                20=IS-ASID, 21=MAG-ADJ, 22=ROTATION, 23=CORRECTION, 24=OFFSET
        '''
        if(type(def_id) is int):
            if(self.__defID_count <= def_id and def_id <= self.__defID_count):
                self.__def_info[self.__cmt_a] = [0, 0]
        return

    def SetAngBal(self, arg1, arg2):
        '''
        Summary:
            Set AngleBalance value. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__cmt_a] = [arg1, arg2]
        return

    def SetBeamBlank(self, sw):
        '''
        Summary:
            ON/OFF Beam branking. Branking method is defined on machine side.

        Args:
            sw: int
                0=OFF, 1=ON
        '''
        if (type(sw) is int):
            if (sw == 0 or sw == 1):
                self.__beambalnking = sw
        return
 
    def SetCLA1(self, arg1, arg2):
        '''
        Summary:
            Set CLAlignment1 value. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__cla1] = [arg1, arg2]
        return
  
    def SetCLA2(self, arg1, arg2):
        '''
        Summary:
            Set CLAlignment2 value. The variable corresponds to I/O output value.
            
        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__cla2] = [arg1, arg2]
        return
 
    def SetCLs(self, arg1, arg2):
        '''
        Summary:
            Set CLStig value. The variable corresponds to I/O output value.
            
        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__cls] = [arg1, arg2]
        return
 
    def SetDetAlign(self, arg1, arg2, arg3):
        '''
        Summary:
            Set Alignment value for detector. The variable corresponds to I/O output value.
            
        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        
        if (type(arg1) is int and type(arg2) is int and type(arg3) is int):
            if arg1 <= self.__defID_count:
                def_index = arg1
            if((self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])
            and (self.__value_range[0] <= arg3 and arg3 <= self.__value_range[1])):
                self.__def_info[def_index]  = [arg1, arg2]
        return
#        if (type(arg1) is int and type(arg2) is int):
#            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
#            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
#                self.__detectalign = [arg1, arg2]
#        return
 
    def SetFLA1(self, arg1, arg2):
        '''
        Summary:
            Set FLAlignment1 value for detector. The variable corresponds to I/O output value.
        
        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__fla1] = [arg1, arg2]
        return
 
    def SetFLA2(self, arg1, arg2):
        '''
        Summary:
            Set FLAlignment2 value for detector. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__fla2] = [arg1, arg2]
        return
 
    def SetFLs1(self, arg1, arg2):
        '''
        Summary:
            Set FLStig1 value for detector. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__fls1] = [arg1, arg2]
        return
 
    def SetFLs2(self, arg1, arg2):
        '''
        Summary:
            Set FLStig2 value for detector. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__fls2] = [arg1, arg2]
        return
 
    def SetGunA1(self, arg1, arg2):
        '''
        Summary:
            Set GunAlignment1 value for detector. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__gun1] = [arg1, arg2]
        return
 
    def SetGunA2(self, arg1, arg2):
        '''
        Summary:
            Set GunAlignment2 value for detector. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__gun2] = [arg1, arg2]
        return
 
    def SetILs(self, arg1, arg2):
        '''
        Summary:
            Set ILStig value for detector. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__ils] = [arg1, arg2]
        return
 
    def SetIS1(self, arg1, arg2):
        '''
        Summary:
            Set ImageShift1 value for detector. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__isc1] = [arg1, arg2]
        return
 
    def SetIS2(self, arg1, arg2):
        '''
        Summary:
            Set ImageShift2 value for detector. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__isc2] = [arg1, arg2]
        return
 
    def SetOLs(self, arg1, arg2):
        '''
        Summary:
            Set OLStig value for detector. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__ols] = [arg1, arg2]
        return
 
    def SetPLA(self, arg1, arg2):
        '''
        Summary:
            Set PLAlign value for detector. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__pla] = [arg1, arg2]
        return
    
    def SetSpotA(self, arg1, arg2):
        '''
        Summary:
            Set SpotAlign value for detector. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__spa] = [arg1, arg2]
        return   
 
    def SetScan1(self, arg1, arg2):
        '''
        Summary:
            Set Scan1 value for detector. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__scan1] = [arg1, arg2]
        return
 
    def SetScan2(self, arg1, arg2):
        '''
        Summary:
            Set Scan2 value for detector. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__scan2] = [arg1, arg2]
        return
 
    def SetShifBal(self, arg1, arg2):
        '''
        Summary:
            Set ShiftBalance value for detector. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__cmp_s] = [arg1, arg2]
        return
 
    def SetStemA1CoarseRel(self, arg1, arg2):
        '''
        Summary:
            Increase or decrease A1 Coarse value for STEM. This works for ARM200F

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__stema1c = [self.__stema1c[0] + arg1, self.__stema1c[1] + arg2]
        return
 
    def SetStemBeamTiltRel(self, arg1, arg2):
        '''
        Summary:
            Increase or decrease Beam Tilt value for STEM. This works for ARM200F

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__stembeamtilt = [self.__stembeamtilt[0] + arg1, self.__stembeamtilt[1] + arg2]
        return
 
    def SetStemIS(self, arg1, arg2):
        '''
        Summary:
            Set IS value for detector. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__is_asid] = [arg1, arg2]
        return
 
    def SetStemStigA1Rel(self, arg1, arg2):
        '''
        Summary:
            Increase or decrease Stig A1 value for STEM. This works for ARM200F

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__stemstiga1 = [self.__stemstiga1[0] + arg1, self.__stemstiga1[1] + arg2]
        return
 
    def SetStemStigB2Rel(self, arg1, arg2):
        '''
        Summary:
            Increase or decrease Stig B2 value for STEM. This works for ARM200F

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__stemstigb2 = [self.__stemstigb2[0] + arg1, self.__stemstigb2[1] + arg2]
        return
 
    def SetStemUserBShiftRel(self, arg1, arg2):
        '''
        Summary:
            Increase or decrease User B Shift value for STEM. This works for ARM200F

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__stemuserbshift = [self.__stemuserbshift[0] + arg1, self.__stemuserbshift[1] + arg2]
        return
 
    def SetTemA1CoarseRel(self, arg1, arg2):
        '''
        Summary:
            Increase or decrease A1 Coarse value for TEM. This works for ARM200F

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__tema1c = [self.__tema1c[0] + arg1, self.__tema1c[1] + arg2]
        return
 
    def SetTemDShiftRel(self, arg1, arg2):
        '''
        Summary:
            Increase or decrease D Shift value for TEM. This works for ARM200F

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__temdshift = [self.__temdshift[0] + arg1, self.__temdshift[1] + arg2]
        return
 
    def SetTemDiStigRel(self, arg1, arg2):
        '''
        Summary:
            Increase or decrease D Stig value for TEM. This works for ARM200F

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__temdistig = [self.__temdistig[0] + arg1, self.__temdistig[1] + arg2]
        return
 
    def SetTemStigA1Rel(self, arg1, arg2):
        '''
        Summary:
            Increase or decrease A1 Stig value for TEM. This works for ARM200F

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__temstiga1 = [self.__temstiga1[0] + arg1, self.__temstiga1[1] + arg2]
        return
 
    def SetTiltBal(self, arg1, arg2):
        '''
        Summary:
            Set Tilt Balance value for detector. The variable corresponds to I/O output value.

        Args:
            arg1: int
                x value range(0-65535)
            arg2: int
                y value range(0-65535)
        '''
        if (type(arg1) is int and type(arg2) is int):
            if((self.__value_range[0] <= arg1 and arg1 <= self.__value_range[1])
            and (self.__value_range[0] <= arg2 and arg2 <= self.__value_range[1])):
                self.__def_info[self.__cmp_t] = [arg1, arg2]
        return
 
      
##### Ver.1.0.3
      
    def GetDefInfo(self, index):
        """
        * Summary:
            Get Def information. args2 is deflector id.        
        """
        return self.__def_info[index]





