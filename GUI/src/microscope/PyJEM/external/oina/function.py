# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 10:55:56 2021

@author: jeol
"""
# import base
from ... import base
from .interface import *

name = "oina"
base.initialize(name,"172.17.41.2", 49276, "OINAService")


@base.request(name, "/EDS/CheckCommunication", "GET")
def check_communication():
    return

@base.request(name, "/EDS/Connect", "GET")
def connect():
    return

@base.request(name, "/EDS/DisConnect", "GET")
def disconnect():
    return

@base.request(name, "/EDS/AcquisitionLock/Take", "GET")
def take_lock():
    return

@base.request(name, "/EDS/AcquisitionLock/Release", "GET")
def take_release():
    return


 
@base.request(name, "/EDS/Acquire/Setting", "GET")
def get_acquire_setting():
    return

def set_acquire_setting(**kw):
    return base.run(name, "/EDS/Acquire/Setting", "POST", kw)

@base.request(name, "/EDS/Image/StartAcquisition", "POST")
def start_image_acquisition():
    return

@base.request(name, "/EDS/Image/StopAcquisition", "POST")
def stop_image_acquisition():
    return

# @base.request(name, "/EDS/Map/StartAcquisition/Sync", "POST")
def start_map_acquisition(param):
    body = AreaParam(param).param
    return base.run(name, "/EDS/Map/StartAcquisition/Sync", "POST",body)

@base.request(name, "/EDS/Map/StopAcquisition", "POST")
def stop_map_acquisition():
    return

@base.request(name, "/EDS/Line/StartAcquisition/Sync", "POST")
def start_line_acquisition():
    return

@base.request(name, "/EDS/Line/StopAcquisition", "POST")
def stop_line_acquisition():
    return



@base.request(name, "/EDS/AcquireClient/Start", "GET")
def start_client():
    return

@base.request(name, "/EDS/AcquireClient/Stop", "GET")
def stop_client():
    return


# Profile

@base.request(name, "/EDS/Profile/Close", "POST")
def close_profile(value):
    return {"name":value}

@base.request(name, "/EDS/Profile/Create", "POST")
def create_profile(value):
    return 

@base.request(name, "/EDS/Profile/Load", "POST")
def load_profile(value):
    return

@base.request(name, "/EDS/Profile", "GET")
def get_profile():
    return


# Project

@base.request(name, "/EDS/Project", "GET")
def get_project():
    return 

# @base.request(name, "/EDS/Project/Close", "POST")
def close_project(value):
    body= {"name":value}
    return base.run(name, "/EDS/Project/Close", "POST", body)

# @base.request(name, "/EDS/Project/Create", "POST")
def create_project(value):
    body= {"name":value}
    return base.run(name, "/EDS/Project/Create", "POST", body)

# @base.request(name, "/EDS/Project/Load", "POST")
def load_project(value):
    body= {"name":value}
    return base.run(name, "/EDS/Project/Load", "POST", body)

# @base.request(name, "/EDS/Project/Select", "POST")
def select_project(value):
    body= {"name":value}
    return base.run(name, "/EDS/Project/Select", "POST", body)

# @base.request(name, "/EDS/Project/BatchExport", "POST")
def export_project(value):
    body= {"name":value}
    return base.run(name, "/EDS/Project/BatchExport", "POST", body)


# Specimen

@base.request(name, "/EDS/Specimen/Create", "POST")
def create_specimen():
    return

@base.request(name, "/EDS/Specimen/Select", "POST")
def select_specimen():
    return

@base.request(name, "/EDS/Specimens", "GET")
def get_specimen():
    return





