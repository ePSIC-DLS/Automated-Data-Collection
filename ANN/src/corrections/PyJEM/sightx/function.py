# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 10:55:56 2021

@author: jeol
"""
from .. import base
from .. import _image

name = "sightx"
base.initialize(name,"localhost", 49260, "DetectorRESTService/Detector")




@base.request(name, "/GetAttachedDetector", "GET")
def get_attached_detector():
    """
    Summary:
        Acquisition of detector names currently available in Sightx.

    Args:
        None

    Return: list
        List of available detector names. 
    """
    return 

def assign_channel(detectorName, channel=0):
    """
    Summary:
        Assign the selected detector to a channel.

    Args:
        detectorName: str
            Detector name
        channel: 
            Channel number to assign the detector. (Only multiple channles)
        
    Return: dict
        Execution result.
    """
    if not channel:
        channel=1
    uri = "/{0}/AssignChannel/{1}" .format(detectorName, channel)

    return base.run(uri,"GET")

@base.request(name, "/GetAssignChannels", "GET")
def get_assignChannels():
    '''
    Summary:
        Get activate detectors list.
        
    Return: dict
    '''   
    return

@base.request(name, "/SnapShotAll", "POST")
def snapshotall():
    '''
    Summary:
        acquire all available detectors.
        To get image data is use "snapshotframe()".
        "this function is only Scanning mode."
        
    Args: 
        None
        
    Return: dict
        Execution result
    '''
    return

@base.request(name, "/StartCreateRawDataCache", "POST")
def start_accumulate_image_cache(self):
    """
    Summary:
        Turn on the flag to keep the cached image of the Live image. 
        
    Return: dict
        Execution result
        
    Example:
        {"status":"OK"}
    """
    return

@base.request(name, "/StopCreateRawDataCache", "POST")
def stop_accumulate_image_cache(self):
    """
    Summary:
        Turn off the flag to keep the cached image of the Live image 
        
    Return: dict
        Execution result
        
    Example:
        {"status":"OK"}
    """
    return


class Detector:
    """
    detector instance
    """
    def __init__(self, det):
        self.detector = det
        
    def livestart(self):
        """
        Summary:
            Start live.
            
        Return: dict
            Execution result
        """
        uri = "/{}/LiveStart".format(self.detector)
        return base.run(uri, "POST")

    def livestop(self):
        """
        Summary:
            Stop live.
            
        Return: dict
            Execution result
        """
        uri = "/{}/LiveStop".format(self.detector)
        return base.run(uri, "POST")
        
    def snapshot(self, ext, save=False, filename=None, show=False):
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
        uri = "/{}/Snapshot/{}".format(self.detector, ext)
        cont = base.run(name, uri, "GET", cast="image")
        ac = _image.AcquireSetting(cont)
        return ac.method(ext, save, filename, show)

    def snapshotframe(self, ext, save=False, filename=None, show=False):
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
        uri = "/{}/SnapShotFrame/{}".format(self.detector, ext)
        cont = base.run(name, uri, "GET", cast="image")
        ac = _image.AcquireSetting(cont)
        return ac.method(ext, save, filename, show)

    def livesnapshot(self, ext, save=False, filename=None, show=False):
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
        uri = "/{}/LiveSnapShot/{}".format(self.detector, ext)
        cont = base.run(name, uri, "GET", cast="image")
        ac = _image.AcquireSetting(cont)
        return ac.method(ext, save, filename, show)
        
    def snapshot_rawdata(self):
        """
        Summary:
            Raw data of the image acquired by the specified detector. the raw data is returned as a byte array.

        Args: 
            None

        Return: bytes
            2 dimensional byte array of acquired image data.
        """        
        uri = "/{}/CreateRawData".format(self.detector)
        return base.run(uri, "GET")
        
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
        uri = "/{}/Setting".format(self.detector)
        return base.run(uri, "GET")
        
    def set_detectorsetting(self, body):
        '''
        Summary:
            Wild card method.

        Args:
            body: dict               
                 "key" is function name you want to use
                 "value" is to change value.
         
        Return: dict
            The value set to TEM.
        '''
        uri = "/{}/Setting".format(self.detector)
        return base.run(uri, "POST", body)

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
        body = {"frameIntegration":value}
        return self.set_detectorsetting(body)

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
        body = {"ExposureTimeIndex":value}
        return self.set_detectorsetting(body)

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
        body = {"ExposureTimeValue":value}
        return self.set_detectorsetting(body)

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
        body = {"GainIndex":value}
        return self.set_detectorsetting(body)

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
        body = {"OffsetIndex":value}
        return self.set_detectorsetting(body)

    def set_digitalrotation(self, value):
        '''
        Summary:
            Set the digital rotation angle as absolute value.
        Args:
            value:
                0-360
        Return: dict
            The value set to TEM.
        '''
        body = {"DigitalRotation":value}
        return self.set_detectorsetting(body)

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
        body = {"ScanRotation":value}
        return self.set_detectorsetting(body)

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
        body = {"scanRotationStep":value}
        return self.set_detectorsetting(body)

    def set_imaging_area(self, Width, Height, X=None, Y=None):
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
        body = {"ImagingArea":{"X":X, "Y":Y, "Width":Width, "Height":Height}}
        return self.set_detectorsetting(body)

    def set_spotposition(self, X, Y):
        '''
        Summary:
            Set the beam position when ScanMode is "Spot".
            Sets which part of the scanning range set by ImagingArea is scanned.
            The top left vertex is (0, 0).
            If no value is entered for the argument, the value is not changed.
        Args:
            x: 0-4096
            y: 0-4096
        Return: dict
            The value set to TEM.
        '''
        body = {"SpotPosition":{"X":X, "Y":Y}}
        return self.set_detectorsetting(body)

    def set_areamode_imagingarea(self, Width, Height, X=None, Y=None):
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
        body = {"AreaModeImagingArea":{"X":X, "Y":Y, "Width":Width, "Height":Height}}
        return self.set_detectorsetting(body)

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
        body = {"scanMode":value}
        return self.set_detectorsetting(body)

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
        body = {"BinningIndex":value}
        return self.set_detectorsetting(body)
        
    def AutoFocus(self):
        '''
        Summary:
            Start AutoFocus function.
        Return: dict
            {"status":...}
        '''
        uri = "/{}/AutoFocus".format(self.detector)
        return base.run(uri, "POST")

    def AutoContrastBrightness(self):
        '''
        Summary:
            Start AutoContrastBrightness function.
        Return: dict
            {"status":...}
        '''
        uri = "/{}/AutoContrastBrightness".format(self.detector)
        return base.run(uri, "POST")

    def AutoStigmator(self):
        '''
        Summary:
            Start AutoStigmator function.
        Return: dict
            {"status":...}
        '''
        uri = "/{}/AutoStigmatorAutoStigmator".format(self.detector)
        return base.run(uri, "POST")

    def AutoOrientation(self):
        '''
        Summary:
            Start AutoOrientation function.
        Return: dict
            {"status":...}
        '''
        uri = "/{}/AutoOrientation".format(self.detector)
        return base.run(uri, "POST")

    def AutoZ(self):
        '''
        Summary:
            Start AutoZ function.
        Return: dict
            {"status":...}
        '''
        uri = "/{}/AutoZ".format(self.detector)
        return base.run(uri, "POST")


    ## 使用する機種によって動かないものがある
    def get_insert_state(self):
        '''
        Summary:
            Get detector in/out status. 
        Return: dict
            {"status":...}
        '''   
        uri = "/{}/GetInserted".format(self.detector)
        return base.run(uri, "GET")
        
    def insert(self):
        '''
        Summary:
            Insert a select detector.
        Return: dict
            {"status":...}
        '''   
        uri = "/{}/Insert".format(self.detector)
        return base.run(uri, "GET")

    def retract(self):
        '''
        Summary:
            retract a select detector.
        Return: dict
            {"status":...}
        '''   
        uri = "/{}/Retract".format(self.detector)
        return base.run(uri, "GET")

    def get_image_cache(self):
        '''
        Summary:
            Returns a cached image of a Live image without using SnapShot. 
            Can only be used if the flag to leave the cache is ON 
        Return: bytes
            bytes array.
        '''   
        uri = "/{}/CreateRawDataCache".format(self.detector)
        return base.run(uri, "GET")
        



