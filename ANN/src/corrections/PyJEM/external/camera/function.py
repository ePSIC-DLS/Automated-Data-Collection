# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 10:55:56 2021

@author: jeol
"""
from ... import base
from ... import _image

name = "gatan"
base.initialize(name,"172.17.41.3", 49230, "CameraStationService/GATAN")



@base.request(name, "/GetAttachedDetector", "GET")
def get_attached_detector():
    """
    Summary:
        Acquisition of detector names currently available in Gatan camera.

    Args:
        None

    Return: list
        List of available detector names. 
    """
    return 


class Camera:
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
        
    def snapshot(self, ext):
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
            
            |  File stream saved with the selected extension. (If there is 
            an input in an argument other than 'extention', None is returned.)
        """  
        uri = "/{}/Snapshot/{}".format(self.detector, ext)
        cont = base.run(name, uri, "GET", cast="image")
        ac = _image.AcquireSetting(cont)
        return ac.method(ext)

    def livesnapshot(self, ext):
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
        return ac.method(ext)
        
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
        body = {"ExposureTime":value}
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

    def open_shutter(self):
        '''
        Summary:
            retract a select detector.
        Return: dict
            {"status":...}
        '''   
        uri = "/{}/Shutter/0/Open".format(self.detector)
        return base.run(uri, "POST")
        
    def close_shutter(self):
        '''
        Summary:
            retract a select detector.
        Return: dict
            {"status":...}
        '''   
        uri = "/{}/Shutter/0/Close".format(self.detector)
        return base.run(uri, "POST")




