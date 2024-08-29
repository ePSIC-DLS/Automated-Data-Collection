# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 15:16:38 2021

@author: jeol
"""

# from . import function
from .function import *
from ... import base




def set_ip(val):
    base.change_ip(function.name, val)
    
def get_config():
    return base.get_config(function.name)
    

