# -*- coding: utf-8 -*-

from ..base import run



@run("detector", "detectors", "GET")
def get_attached_detector():
    '''
    Summary:
        Acquisition of detector names currently available in TEMCenter.
    Return: list
        Available detector names.
    '''
    return# self.raw["detectors"]

@run("detector", "assign", "SET")
def assign_channel(detectorName, channel = None):
    """
    Summary:
        Set the specified detector to Active.
    Args        detectorName: Detector name, string
        channel: Selection of channel to assign detectors (Only multiple channles), int
    Return: dict
        Assigned detector names
    """   
    if (channel == None):
        channel = str(1)
    if  (type(channel) == int):
        channel = str(channel)
        print({detectorName : channel})
    return {detectorName : channel}

@run("detector", "status", "GET")
def snapshotall():
    '''
    Summary:
        All images of the selected STEM detector are taken.
    Return: dict
        key: 
            status
        value:
            "OK" or "Failed"
    '''    
    return

@run("detector", "status", "GET")
def imageselector_kind(selector):
    '''
    Summary:
        Change ImageSelector mode (only JEM-2800)
    Args:
        selector: 0= , 1=SEI, 2= , 3=BEI, 4=DF, 5=TEM, 6=DIFF
    Return: dict
        key: 
            status
        value:
            "OK" or "Failed"
    '''
    return 

detectors = get_attached_detector()
class Detector:
    '''
    It is able to get the information, acquire image data,
    execute automatic function, etc. about enter camera. 
    Selectable camera can be obtained with "cameras" or "detector.get_attached_detector()".
    '''

    def __init__(self, detectorName):
        """
        Summary：
                Detector class         
        Args：
            detectorName:
                Detector name to be set
        """
        try:
            #detector名での判断はいらない気もする。Offlineだし
            self.detector = detectorName
            if(type(detectorName) is str):
                if(detectorName in detectors):
                    print(detectorName + " is Correct!")
                else:
                    print(detectorName + " is not Correct.")
                
            elif(type(detectorName) is int):
                if (detectorName < len(detectors)):
                    print(detectors[detectorName] + " is Correct!")
                else:
                    print(detectorName + " is not Correct.")
        except:
            raise "Except make Detector instance"

    @run("detector", "status", "GET")
    def livestart(self):
        """
        Summary:
            Start live.
            
        Return: dict
            Execution result
        """
        return

    @run("detector", "status", "GET")
    def livestop(self):
        """
        Summary:
            Stop live.
            
        Return: dict
            Execution result
        """
        return

    def snapshot(self, extention, save=False, filename=None, show=False):
        """
        Summary:
            Acquire image about the args "extension". 
            The captured image is returned as a file stream.
            
        Args: 
            extention: str
                "jpg", "bmp", "tiff"
            save:  bool
                'True' is save capture file.
            filename: str
                Name of file to save. It is possible to include an absolute path. (Only available when 'save' is True.)
            show: bool
                show the Image file.

        Return: bytes or str
            if enter argument is only "extention", return value is image data stream (bytes).
            else return value is saved file name.
            
            File stream saved with the selected extension. (If there is 
            an input in an argument other than 'extention', None is returned.)
        """  
        return self.__captrue_method(extention, save, filename, show)

    def snapshotframe(self, extention):
        """
        Summary:
            Take an image with the specified extension. The captured image is returned as a file stream.
        
        Args: 
            extention: 
                "jpg", "bmp", "tiff"
            save:  bool
                'True' is save capture file.
            filename: str
                Name of file to save. It is possible to include an absolute path. (Only available when 'save' is True.)
            show: bool
                show the Image file.
                
        Return: bytes or str
            if enter argument is only "extention", return value is image data stream (bytes).
            else return value is saved file name.

        |  File stream saved with the selected extension
        |  type   : Stream
        """
        return self.__captrue_method(extention)

    def snapshot_rawdata(self):
        """
        Summary:
            Raw data of the image acquired by the specified detector. the raw data is returned as a byte array.

        Args: 
            None

        Return: bytes
            2 dimensional byte array of acquired image data.
        """        
        img = self.__captrue_method("jpg")
        return img

    def livesnapshot(self, extention):
        '''
        Summary:
            Take an image with the specified extension. Obtaining images faster than "snapshot".

        Args: 
            extention: 
                "jpg", "bmp", "tiff"
            save:  bool
                'True' is save capture file.
            filename: str
                Name of file to save. It is possible to include an absolute path. (Only available when 'save' is True.)
            show: bool
                show the Image file.
                
        Return: bytes or str
            if enter argument is only "extention", return value is image data stream (bytes).
            else return value is saved file name.

        |  File stream saved with the selected extension
        |  type   : Stream
        '''
        return self.__captrue_method(extention)

    @staticmethod
    @run("detector", "capture", "image")
    def __captrue_method(args, **kw):
        return args


    @run("detector", "settings", "GET")
    def get_detectorsetting(self):
        '''
        Summary:
            Obtaining setting information of selected detector.
        
        Return: dict
            (ex) {
            "ExposureTimeValue":100,
            "GainIndex":100, ...
            }
        '''
        return

############################# Set ####################################

    def set_frameintegration(self, value):
        '''
        Summary:
            Set the accumulation count.

        Args:
            value: 
                0-255 (It depends on TEM model)

        Return: dict
            The value set to TEM.
        '''
        return self.set_detector_setting(frameIntegration=value)

    def set_exposuretime_index(self, value):
        '''
        Summary:
            Set the exposure time as index.
        Args:
            value: 
                0 - 65535 (It depends on TEM model)

        Return: dict
            The value set to TEM.
            {"ExposureTimeIndex":...}
        '''
        return self.set_detector_setting(ExposureTimeIndex=value)
    
    def set_gainindex(self, value):
        '''
        Summary:
            Set the gain value as index.
        Args:
            value: 
                0- 4095 (It depends on TEM model)
        Return: dict
            The value set to TEM.
        '''
        return self.set_detector_setting(GainIndex=value)

    def set_offsetindex(self, value):
        '''
        Summary:
            Set the offset value as index.
        Args:
            value: 
                0- 4095 (It depends on TEM model)
        Return: dict
            The value set to TEM.
        '''
        return self.set_detector_setting(OffsetIndex=value)

#    def set_horizontal_lineNo(self, value):
#        """
#        [Offline] 
#        Summary: Set the Horizontal Line number.
#                 Can not be executed at present.(2017/11)
#        arg    : value -
#        return : The value set to TEM.
#        type   : json.Dict
#        Except :
#        """
#        return {"HorizontalLineNo":value}
#
#    def set_vertical_lineNo(self, value):
#        """
#        [Offline] 
#        Summary: Set the Vertical Line number.
#                 Can not be executed at present.(2017/11)
#        arg    : value -
#        return : The value set to TEM.
#        type   : json.Dict
#        Except :
#        """
#        return {"VerticalLineNo":value}

    def set_exposuretime_value(self, value):
        '''
        Summary:
            Set the exposure time as usec value.
        Args:
            value: 
                0-1000(μsec) (It depends on TEM model)
        Return: dict
            The value set to TEM.
        '''
        return self.set_detector_setting(ExposureTimeValue=value)

    def set_scanrotation(self, value):
        '''
        Summary:
            Set the scanRotation angle as absolute value.
        Args:
            value:
                0-360
        Return: dict
            The value set to TEM.
        '''
        return self.set_detector_setting(ScanRotation=value)

    def set_scanrotation_step(self, value):
        '''
        Summary:
            Set the minimum variation of scanRotation.
        Args:
            value:
                0-20
        Return: dict
            The value set to TEM.
        '''
        return self.set_detector_setting(scanRotationStep=value)

    def set_imaging_area(self, Width, Height, X=0, Y=0):
        '''
        Summary:
            Set the number of pixels of the live image. 
            x and y are the coordinates of the starting pixel of the read image. 
            width and height are the coordinates of the end pixel of the read image.
            If no value is entered for the argument, the value is not changed.
        Args:
            x: 0-4096
            y: 0-4096
            Width: 0-4096
            Height: 0-4096
        Return: dict
            The value set to TEM.
        '''
        return self.set_detector_setting(ImagingArea={"X":X, "Y":Y, "Width":Width, "Height":Height})

    def set_spotposition(self, X=0, Y= 0):
        '''
        Summary:
            Set the number of pixels of the live image. 
            x and y are the coordinates of the starting pixel of the read image. 
            width and height are the coordinates of the end pixel of the read image.
            If no value is entered for the argument, the value is not changed.
        Args:
            x: 0-4096
            y: 0-4096
            Width: 0-4096
            Height: 0-4096
        Return: dict
            The value set to TEM.
        '''
        return self.set_detector_setting(SpotPosition={"X":X, "Y":Y})

    def set_areamode_imagingarea(self, Width, Height, X=0, Y=0):
        '''
        Summary:
            Set the beam position when ScanMode is "Area".
            Sets which part of the scanning range set by ImagingArea is scanned.
            The top left vertex is (0, 0).
            If no value is entered for the argument, the value is not changed.
        Args:
            x: 0-4096
            y: 0-4096
            Width: 0-4096
            Height: 0-4096
        Return: dict
            The value set to TEM.
        '''
        return self.set_detector_setting(AreaModeImagingArea={"X":X, "Y":Y, "Width":Width, "Height":Height})

    def set_scanmode(self, value):
        '''
        Summary:
            Set the scanMode.
        Args:
            value: 
                0:Scan, 1:Area, 3:Spot
        Return: dict
            The value set to TEM.
        '''
        return self.set_detector_setting(scanMode=value)

    def set_binningindex(self, value):
        '''
        Summary:
            Set the Binning value as index.
            (This function corresponds to camera only.)
        Args:
            value: 
                0-4 (It depends on TEM model)
        Return: dict
            The value set to TEM.
        '''
        return self.set_detector_setting(BinningIndex=value)

    @staticmethod
    @run("detector", "settings", "SET")
    def set_detector_setting(args, **kw):
        return kw    

############################## Auto機能 #####################################
    @run("detector", "status", "GET")
    def AutoFocus(self):
        '''
        Summary:
            Start AutoFocus function.
        Return: dict
            {"status":...}
        '''
        return 

    @run("detector", "status", "GET")
    def AutoContrastBrightness(self):
        '''
        Summary:
            Start AutoContrastBrightness function.
        Return: dict
            {"status":...}
        '''
        return 

    @run("detector", "status", "GET")
    def AutoStigmator(self):
        '''
        Summary:
            Start AutoStigmator function.
        Return: dict
            {"status":...}
        '''
        return 

    @run("detector", "status", "GET")
    def AutoOrientation(self):
        '''
        Summary:
            Start AutoOrientation function.
        Return: dict
            {"status":...}
        '''
        return 

    @run("detector", "status", "GET")
    def AutoZ(self):
        '''
        Summary:
            Start AutoZ function.
        Return: dict
            {"status":...}
        '''
        return 
                

### Ver.1.1.0 ###

    @run("detector", "insert", "GET")
    def get_insert_state(self):
        '''
        Summary:
            Get detector in/out status. 
        Return: dict
            {"status":...}
        '''   
        return 

    @run("detector", "insert", "SET")
    def insert(self):
        '''
        Summary:
            Insert a select detector.
        Return: dict
            {"status":...}
        '''   
        return {"status": True}

    @run("detector", "insert", "SET")
    def retract(self):
        '''
        Summary:
            retract a select detector.
        Return: dict
            {"status":...}
        '''   
        return {"status": False}



@run("detector", "status", "GET")
def start_accumulate_image_cache():
    """
    Summary:
        Turn on the flag to keep the cached image of the Live image. 
        
    Return: dict
        Execution result
        
    Example:
        {"status":"OK"}
    """
    return 

@run("detector", "status", "GET")
def stop_accumulate_image_cache():
    """
    Summary:
        Turn off the flag to keep the cached image of the Live image 
        
    Return: dict
        Execution result
        
    Example:
        {"status":"OK"}
    """
    return 







