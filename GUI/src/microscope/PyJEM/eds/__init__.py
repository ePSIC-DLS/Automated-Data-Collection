# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 15:16:38 2021

@author: EM
"""

# from . import function
from .function import *
from .. import base


def set_ip(val):
    """
    Summary:
        This function can modify the IP Address which is URI of this package.

    Args:
        string val: IP Address.

    Return:
        None
    """
    base.change_ip(function.name, val)


def get_config():
    """
    Summary:
        This function returns the package's settings.

    Args:
        None

    Return:
        {'name': '---', 'ip': '---', 'port': ---, 'uri': '---'}
    """
    return base.get_config(function.name)
