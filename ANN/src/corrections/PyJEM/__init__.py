# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 15:28:11 2021

@author: EM
"""
import os

from .config import get_config, set_record_path



def __read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()



__version__ = __read("VERSION")


def get_record_path():
    """
    You can get the root path where the image will be saved.
    * The relevant ones are detector, sightx, and camera .
    """
    return get_config("record_path")

def set_record_path(path):
    """
    You can change the root path to save the image.
    * The relevant ones are detector, sightx, and camera .
    """
    return set_record_path(path)
