# -*- coding: utf-8 -*-
"""
Created on Wed Dec  8 19:28:38 2021

@author: jeol
"""
from enum import Enum

from ..base import BaseClass, get_enum_list


class AnalyzerKey(Enum):
    ProcessTime = "ProcessTime"


class AcquisitionSettingKey(Enum):
    ProcessTime = "ProcessTime"
    DwellTime = "DwellTime"
    CollectionMode = "CollectionMode"
    SweepCount = "SweepCount"
    SelectedDetector = "SelectedDetector"
    EnableScanSync = "EnableScanSync"


class SpectrumDataKey(Enum):
    TargetDataID = "TargetDataID"
    StartPosition = "StartPosition"
    EndPosition = "EndPosition"
    StartLine = "StartLine"
    EndLind = "EndLind"


class ElementsKey(Enum):
    ElementalNumber = "ElementalNumber"
    Line = "Line"


class AnalysisKey(Enum):
    Elements = "Elements"
    TargetDetector = "TargetDetector"
    TargetDataID = "TargetDataID"


class SpectrumSettingsKey(Enum):
    ProcessingMethod = "ProcessingMethod"
    StandardDataType = "StandardDataType"
    CorrectionType = "CorrectionType"
    ConversionType = "ConversionType"


class DetectorStatusKey(Enum):
    Position = "Position"


class SpectrumAnalysisKey(Enum):
    TargetDataID = "TargetDataID"
    Elements = "Elements"
    TargetDetector = "TargetDetector"


class __FormatTemplate(BaseClass):
    def __init__(self, obj, *args, **kw):
        super().__init__(*args, **kw)
        key = get_enum_list(obj)
        self.param = {k: w for k, w in self._param.items() if k in key}


class Analyzer(__FormatTemplate):
    def __init__(self, *args, **kw):
        super().__init__(AnalyzerKey, *args, **kw)


class AcquisitionSettingParam(__FormatTemplate):
    def __init__(self, *args, **kw):
        super().__init__(AcquisitionSettingKey, *args, **kw)


class SpectrumData(__FormatTemplate):
    def __init__(self, *args, **kw):
        super().__init__(SpectrumDataKey, SpectrumDataKey*args, **kw)


class Elements(__FormatTemplate):
    def __init__(self, *args, **kw):
        super().__init__(ElementsKey, *args, **kw)


class Analysis(__FormatTemplate):
    def __init__(self, *args, **kw):
        super().__init__(AnalysisKey, *args, **kw)


class SpectrumSettings(__FormatTemplate):
    def __init__(self, *args, **kw):
        super().__init__(SpectrumSettingsKey, *args, **kw)


class DetectorStatus(__FormatTemplate):
    def __init__(self, *args, **kw):
        super().__init__(DetectorStatusKey, *args, **kw)


class SpectrumAnalysis(__FormatTemplate):
    def __init__(self, *args, **kw):
        super().__init__(SpectrumAnalysisKey, *args, **kw)
