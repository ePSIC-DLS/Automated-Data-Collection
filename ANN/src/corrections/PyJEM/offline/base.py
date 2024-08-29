# -*- coding: utf-8 -*-
"""
Created on Wed Sep 29 13:48:41 2021

@author: dmaekawa
"""
from pathlib import Path
import os
import cv2
import matplotlib.pyplot as plt


from .. import filesystem as fs
from .. import _image


class __OfflineData(fs.JsonFileIO):
    __metaclass__ = None
    __metadict__ = {}
    def __init__(self, file):
        super().__init__(file)
        self.raw = self.read()
        self.current = self.raw.copy()
            
    def __new__(cls, file):
        if not file in cls.__metadict__:
            cls.__metadict__[file] = super().__new__(cls, file)
        return cls.__metadict__[file]
    
    def __del__(self):
        self.write(self.current)
        
    def __iter__(self):
        return self.__dict__.iteritems()

    def __repr__(self):
        return str(self.__dict__)
    
    def __str__(self):
        return str(self.__dict__)

    def __getitem__(self, key):
        return self.__dict__[key] 

    def __setitem__(self, key, value):
        self.__dict__[key] = value


def setup_offlineData(name):
    path = Path(__file__).parents[0]
    # path = os.path.dirname(__file__).rsplit(r'\', 1)[0]
    file = "{}\\resources\offline_{}_data.json".format(path, name)
    capfile = "{}\snapshot.".format(path)
    of = __OfflineData(file)
    offdata = of.read()
    cap = offdata["capture"]
    for k in offdata["capture"]:
        if cap[k] == "":
            cap[k] = capfile + k
    of.write(offdata)
    del of
    


resource_path = os.path.dirname(__file__) + r"\resources"
    
def run(*d_args):
    "[0]=name, [1]= method"
    fname = d_args[0]
    name = d_args[1]
    method = d_args[2].lower()
   
    _data = __OfflineData(resource_path + r"\offline_{}_data.json".format(fname))
    def _offline(func):
        def wrapper(*f_args, **kw):
            if name in _data.current:
                if method == "get":
                    return _data.current[name] 
                elif method == "set":
                    if not f_args:
                        _data.current[name].update(kw)
                        return kw
                    else:
                        val = func(*f_args)
                        _data.current[name].update(val)
                        return val
                elif method == "image":
                    ext = f_args[0]
                    ref_file = _data.current[name][ext]
                    img = cv2.imread(ref_file, cv2.IMREAD_GRAYSCALE)
                    _i = _image.AcquireSetting(img.tobytes())
                    return _i.method(*f_args)
        return wrapper
    return _offline

    

