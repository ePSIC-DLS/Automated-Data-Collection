# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 16:25:06 2021

@author: jeol
"""

from enum import Enum

from ...base import BaseClass, get_enum_list


class AreaParamsKey(Enum):
    X="X"
    Y="Y"
    Width="Width"
    Height="Height"

class AcquisitionSettingKey(Enum):
    AutoLock="AutoLock"
    IsAutoContrastBrightness="IsAutoContrastBrightness"
    CurrentSite="CurrentSite"
    IsAutoIncrementSiteNumber="IsAutoIncrementSiteNumber"
    IsResetAcquisitionNumberForEachSite="IsResetAcquisitionNumberForEachSite"
    MasterSiteNumber="MasterSiteNumber"
    SiteName="SiteName"
    SiteThickness="SiteThickness"
    StatusImageTypes="StatusImageTypes"
    CurrentProject="CurrentProject"
    Specimen="Specimen"
    
    
class AreaParam(BaseClass):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.key = get_enum_list(AreaParamsKey)
        self.param = {k:w for k,w in self._param.items() if k in self.key}
    
class AcquisitionSettingParam(BaseClass):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.key = get_enum_list(AcquisitionSettingKey)
        self.param = {k:w for k,w in self._param.items() if k in self.key}

