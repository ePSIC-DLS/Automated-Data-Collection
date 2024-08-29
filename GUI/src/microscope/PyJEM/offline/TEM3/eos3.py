# -*- coding: utf-8 -*-


import os 
import json

offline_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
eosdata_file = str(offline_path) + r"\resources\offline_tem3eos_data.json"

try:
    f = open(eosdata_file, "r")
    offlinedata = json.load(f)
    f.close()
except:
    print("Fail") 
    
tem_funcmodelist = ["MAG", "MAG2", "LowMAG", "SAMAG", "DIFF"]
stem_funcmodelist = ["Align", "SM-LMAG", "SM-MAG", "AMAG", "uuDIFF", "Rocking"]
listnamelist = ["MagList", "SpctrList", "StemCamList"]  


class EOS3:
    def __init__(self):
        self.__alpha_list = ["TEM-S", "1", "2", "3", "4", "5","6","7","8"]
        self.__probemode_list = ["TEM","EDS","NBD","CBD"]
        self.__mag_index = 0
        self.__spctr_index = 0
        self.__stemcam_index = 0
        self.__alpha_index = 0
        self.__funcmode_index_tem = 0
        self.__funcmode_index_stem = 0
        self.__temstemmode = 0    # 0:TEM, 1:STEM
        self.__probemode = 0
        self.__spctrmode = 0
        self.__spotsize = 0
        self.__brightness = 0
        self.__difffocus = 0
        self.__gifmode = 0    #Get無いからいらない?
        self.__objfocus = 0
        self.__brightness_zoom_sw = 0
            
    
    def DownSelector(self):
        '''
        Summary:
            Decrement Magnification/Camera length/Rocking angle number. 
            Down the magnification selector.
        '''
        if (self.__mag_index != 0):
            self.__mag_index -= 1
        return 
        
    def DownSpctrSelector(self):
        '''
        Summary:
            Decrement spectrum magnification number. 
            Down the energy spectrometer selector.
        '''
        if (self.__spctr_index != 0):
            self.__spctr_index -= 1
        return 

    def DownStemCamSelector(self):
        '''
        Summary:
            Decrement imaging side camera length(magnification) number for STEM. 
            Down the camera length selector.
        '''
        if (self.__stemcam_index != 0):
            self.__stemcam_index -= 1
        return 
        
    def GetAlpha(self):
        '''
        Summary:
            Get alpha number.

        Return: int
            alpha number.
        '''
        return self.__alpha_index
        
    def GetAlphaSelectorEx(self):
        '''
        Summary:
            Get alpha number and string.

        Return: list [int, string]
            [alpha number, alpha name]           
        '''
        return [self.__alpha_index, self.__alpha_list[self.__alpha_index]]
        
    def GetCurrentMagSelectorID(self):
        '''
        Summary:
            Get MAG selector UD and Magnification value.

        Return: list [int, int]
            [Mag id, Mag value]
        '''
        return self.__mag_index 
        
    def GetFunctionMode(self):
        '''
        Summary:
            Get imaging FUNCTION mode.

        Return: list
            [0]: int
                * On TEM Observation:  
                    0=MAG, 1=MAG2, 2=LowMAG, 3=SAMAG, 4=DIFF 
                
                * On STEM Observation: 
                    0=Align, 1=SM-LMAG, 2=SM-MAG, 3=AMAG, 4=uuDIFF, 5=Rocking
            [1]: str
                FUNCTION mode explanation string. string
        '''
        if (self.__temstemmode == 0):
            _index = self.__funcmode_index_tem
            return [_index, tem_funcmodelist[_index]]
        elif (self.__temstemmode == 1):
            _index = self.__funcmode_index_stem
            return [_index, stem_funcmodelist[_index]]
        return
        
    def GetMagValue(self):
        #まだ
        '''
        Summary:
            Get Magnification/Camera length/Rocking angle. 

        Return: list
            [0]: str
                Magnification value.(Magnification of scanning image for ASID)
            [1]: str
                Unit string
            [2]: str:
                Magnification label
        '''
        if(self.__temstemmode == 0):
            ret = get_offlinedata(self.__temstemmode, self.__funcmode_index_tem, "MagList", self.__mag_index)
            return ret
        elif(self.__temstemmode == 1):
            ret = get_offlinedata(self.__temstemmode, self.__funcmode_index_stem, "MagList", self.__mag_index)
            return ret            
        return 
        
    def GetProbeMode(self):
        '''
        Summary:
            Get irradiative PROBE mode.

        Return: int
            0=TEM, 1=EDS, 2=NBD, 3=CBD
        '''
        return [self.__probemode, self.__probemode_list[self.__probemode]]
        
    def GetSpctrMode(self):
        '''
        Summary:
            Get spectrum mode status.

        Return: int
            0=OFF, 1=ON
        '''
        return self.__spctrmode 
        
    def GetSpctrValue(self):
        #まだ
        '''
        Summary:
            Get spectrum magnification.

        Return: list
            [0]: int
                Magnification value (um/V)
            [1]: str
                Unit string
            [2]: str
                Magnification label
        '''
        if(self.__temstemmode == 0):
            ret = get_offlinedata(self.__temstemmode, self.__funcmode_index_tem, "SpctrList", self.__spctr_index)
            return ret
        elif(self.__temstemmode == 1):
            ret = get_offlinedata(self.__temstemmode, self.__funcmode_index_stem, "SpctrList", self.__spctr_index)
            return ret            
        return 
        
    def GetSpotSize(self):
        '''
        Summary:
            Get SPOTSIZE number.

        Return: int
            spot size.
        '''
        return self.__spotsize
        
    def GetStemCamValue(self):
        #まだ
        '''
        Summary:
            Get imaging side camera length(magnification) for STEM. 

        Return: list
            [0]: int
                Camera length value (cm)
            [1]: str
                Unit string.
            [2]: str
                Camera length string.
        '''
        if(self.__temstemmode == 0):
            ret = get_offlinedata(self.__temstemmode, self.__funcmode_index_tem, "StemCamList", self.__stemcam_index)
            return ret
        elif(self.__temstemmode == 1):
            ret = get_offlinedata(self.__temstemmode, self.__funcmode_index_stem, "StemCamList", self.__stemcam_index)
            return ret            
        return self.position
        
    def GetTemStemMode(self):
        '''
        Summary:
            Get TEM/ASID mode.
            
        Return: int
            0=TEM, 1=ASID
        '''
        return self.__temstemmode
  
    def SelectFunctionMode(self, mode):
        '''
        Summary:
            Set imaging FUNCTION mode.

        Args:
            mode: 
                * On TEM Observation:
                    0=MAG, 1=MAG2, 2=LowMAG, 3=SAMAG, 4=DIFF
                * On STEM Observation:
                    0=Align, 1=SM-LMAG, 2=SM-MAG, 3=AMAG, 4=uuDIFF, 5=Rocking
        '''
        if (type(mode) is int):
            if(self.__temstemmode == 0):
                if((0 <= mode) and (mode <= len(tem_funcmodelist))):
                    self.__funcmode_index_tem = mode
            elif(self.__temstemmode == 1):
                if((0 <= mode) and (mode <= len(stem_funcmodelist))):
                    self.__funcmode_index_stem = mode                
        return
        
    def SelectProbMode(self, mode):
        '''
        Summary:
            Set irradiative PROBE mode.

        Args:
            mode: int
                0=TEM, 1=EDS, 2=NBD, 3=CBD
        '''
        if (type(mode) is int):
            if((0 <= mode) and (mode <= len(self.__probemode_list))):
                self.__probemode_list = mode
        return
        
    def SelectSpotSize(self, size):
        '''
        Summary:
            Set SPOTSIZE number.

        Args:
            size: int
                spot size. range(0-7)
        '''
        if(type(size) is int):
            self.__spotsize = size
        return
        
    def SelectTemStem(self, mode):
        '''
        Summary:
            Set TEM/ASID mode.

        Args:
            mode: int
                0=TEM, 1=ASID
        '''
        if (type(mode) is int):
            if(mode == 0 or mode == 1):
                self.__temstemmode = mode
        return
        
    def SetAlphaSelector(self, value):
        '''
        Summary:
            Set Alpha number.

        Args:
            value: int
                alpah number. range(0-8)
        '''
        if (type(value) is int):
            if((0 <= value) and (value <= len(self.__alpha_list))):
                self.__alpha_index = value
        return
                
    def SetBrightness(self, value):
        '''
        Summary:
            Increase of decrease Lens value for BRIGHTNESS(MAG link). Same as BRIGHTNESS knob. 
            Although full range of short type variable can be accepted. 
            the value around +-1 to 50 is suitable because the range corresponds to that of the knob on the operation panel. 

        Args:
            value:  int 
                brightness value
        '''
        if (type(value) is int):
            self.__brightness = value
        return 
        
    def SetDiffFocus(self, value):
        '''
        Summary:
            Increase of decrease Lens value for DIFFFOCUS(MAG link). Same as DIFFFOCUS knob.
            Although full range of short type variable can be accepted.
            the value around +-1 to 50 is suitable because the range corresponds to that of the knob on the operation panel. 

        Args:
            value:  int 
                difffocus value
        '''
        if (type(value) is int):
            self.__difffocus = value
        return 
        
    def SetGIF(self, mode):
        '''
        Summary:
            Set GIF-mode.

        Args:
            mode: int
                0=OFF, 1=ON
        '''
        if(type(mode) is int):
            self.__gifmode = mode
        return
        
    def SetObjFocus(self, value):
        '''
        Summary:
            Increase of decrease Lens value for OBJ Focus(MAG link). Same as OBJ Focus knob. 
            Although full range of short type variable can be accepted. 
            the value around +-1 to 50 is suitable because the range corresponds to that of the knob on the operation panel.

        Args:
            value:  int 
                objfocus value
        '''
        if (type(value) is int):
            self.__objfocus = value
        return 
        
    def SetSelector(self, value):
        '''
        Summary:
            Set Magnification/Camera length/Rocking angle number.

        Args:
            value: int
                mag index.
        '''
        if(type(value) is int):
            self.__mag_index = value
        return

    def SetSpctrMode(self, mode):
        '''
        Summary:
            ON/OFF spectrum mode.

        Args:
            mode: int
                0=OFF, 1=ON
        '''
        if(type(mode) is int):
            self.__spctrmode = mode
        return
        
    def SetSpctrSelector(self, value):
        '''
        Summary:
            Set spectrum magnification number.

        Args:
            value: int
                spectrum index
        '''
        if (type(value) is int):
            self.__spctr_index = value
        return 
        
    def SetStemCamSelector(self, value):
        '''
        Summary:
            Set imaging side camera length(magnification) number for STEM.
        Args:
            value: int 
                camera length
        '''
        if (type(value) is int):
            self.__stemcam_index = value
        return 
        
    def UpSelector(self):
        '''
        Summary:
            Increment Magnification/Camera length/Rocking angle number.
            Up the magnification selector.
        '''
        self.__mag_index += 1
        return 
        
    def UpSpctrSelector(self):
        '''
        Summary:
            Increment spectrum magnification number. 
            Up the energy spectrometer selector.
        '''
        self.__spctr_index += 1
        return 

    def UpStemCamSelector(self):
        '''
        Summary:
            Increment imaging side camer a length(magnification) number for STEM. Up the camera length selector.
        '''
        self.__stemcam_index += 1
        return
    

#### Ver.1.2
    def GetBrightnessZoom(self):
        """
        Summary:
            Get Brightness Zoom ON/OFF.
        Return:
            0:OFF, 1:ON
        """
        return self.__brightness_zoom_sw
    
    def SetBrightnessZoom(self, sw):
        """
        Summary:
            Set Brightness Zoom ON/OFF.
        Args:
            0:OFF, 1:ON
        """
        self.__brightness_zoom_sw = sw

        
        

def get_offlinedata(temstemmode, funcmode, listname, index=None):
    '''
    this method is only here.
    online package dont have.
    '''
    if(type(funcmode) is int and type(temstemmode) is int):
        if((temstemmode == 0) and (listname in listnamelist)):
            if((0 <= funcmode and funcmode <= len(tem_funcmodelist))):
                ret = offlinedata["TEM"+ tem_funcmodelist[funcmode]][listname]
                if(index != None and type(index) is int and index <= len(ret)):
                    return ret[index]
                return ret
        elif((temstemmode == 0) and (listname in listnamelist)):
           if((0 <= funcmode and funcmode <= len(stem_funcmodelist))):
                ret = offlinedata["STEM"+ stem_funcmodelist[funcmode]][listname]
                if(index != None and type(index) is int and index <= len(ret)):
                    return ret[index]
                return ret       
    return
        
        