# -*- coding: utf-8 -*-
"""
Created on Mon Nov  8 14:17:40 2021

@author: EM
"""

import os

from . import filesystem as fs


PYJEM_CONFIG_FILE = "{}\\config.json".format(os.path.dirname(__file__))


class Configer(fs.JsonFileIO):
    _ins = None
    def __init__(self):
        super().__init__(PYJEM_CONFIG_FILE)
        
        if not self.is_exists:
            self.write(ConfigFormat().__dict__)
        self._config = self.read()
        # print("hash: {}".format(self.__hash__))
        
    def __new__(cls):
        return super().__new__(cls, PYJEM_CONFIG_FILE)

    def getter(self, name):
        if name in self.config:
            return self.config[name]
        return

    def setter(self, name, val):
        if name in self.config:
            temp = self.config
            temp[name] = val
            self.config = temp
        else:
            temp = self.config
            temp.update({name:val})
            self.config = temp
        
    @property
    def config(self):
        return self._config
    
    @config.setter
    def config(self, dic):
        self._config = dic
        self.update()
    
    def update(self):
        self.write(self.config)


class ConfigFormat:
    def __init__(self):
        self.record_path = "{}\\image".format(os.path.dirname(__file__))
        self.log = True
        
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


con = Configer()  
      
def get_config(name=None):
    if name != None and name in con.config:
        return con.config[name]
    return con.config


def set_record_path(path):
    """
    Save image file path.
    """
    con.setter("record_path", path)
    
def log_enable():
    con.setter("log",True)    


def log_disable():
    con.setter("log",False)


            

            
