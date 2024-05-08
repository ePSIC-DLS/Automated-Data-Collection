# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 10:55:56 2021

@author: EM
"""
# import base
from .. import base
from . import interface
# from .interface import *

name = "femtus_eds"
base.initialize(name, "localhost", 49306, "EDSService/JED")


@base.request(name, "/CheckCommunication", "GET")
def check_communication():
    """
    Summary:
        This interface is for checking the HTTP connection.

    Args:
        None

    Return:
        {
            "Version": "---",
            "Result": "OK"
        }
    """
    return


@base.request(name, "/Specification", "GET")
def get_specification():
    """
    Summary:
        This interface can get the specfication of EDS system.

    Args:
        None

    Return:
        {
            "Version": "---",
            "ProcessTimeList":
                {
                    "FirstDetector" : ["T1", "T2", "T3", "T4"],
                    "SecondDetector" : ["T1", "T2", "T3", "T4"],
                    "ThirdDetector" : ["T1", "T2", "T3", "T4"],
                    "FourthDetector" : ["T1", "T2", "T3", "T4"]
                }
        }
    """
    return


@base.request(name, "/Analyzer/Settings", "GET")
def get_analyzer_settings():
    """
    Summary:
        This interface can get the settings of EDS analyzer.

    Args:
        None

    Return:
        {
            ProcessTime":["T1", "T1", "T1", "T1"],
            "Version": "---"
        }
    """
    return


def set_analyzer_settings(param):
    """
    Summary:
        This interface can set the settings of EDS analyzer.

    Args: dictionary
        {"ProcessTime" : ["T1","T1","T1","T1"]}

    Return:
        {"ProcessTime" : ["T1","T1","T1","T1"]}
    """
    return base.run(name, "/Analyzer/Settings",
                    "POST", interface.Analyzer(param))


@base.request(name, "/Analyzer/Status", "GET")
def get_analyzer_status():
    """
    Summary:
        This interface can get the status of EDS analyzer.

    Args:
        None

    Return:
        {
            "InputCountRate" : [21, 21, 21, 21, 21],
            "OutputCountRate" : [21, 21, 21, 21, 21],
            "DeadTime" : [21, 21, 21, 21, 21]
        }
    """
    return


@base.request(name, "/Detector/Configuration", "GET")
def get_detector_configuration():
    """
    Summary:
        This interface can get the configuration of EDS system.

    Args:
        None

    Return:
        {
            "Enabled" : [True, True, True, True],
            "Retractable" : [True, True, False, False],
            "Version" : "---"
        }
    """
    return


@base.request(name, "/Detector/Status", "GET")
def get_detector_status():
    """
    Summary:
        This interface can get the status of EDS detectors.

    Args:
        None

    Return:
        {
            "Position" : [1, 1, 0, 0],
            "MovingPosition" : [1, 1, 0, 0],
            "DetectorErrorCode": "E01",
            "Version": "---"
        }
    """
    return


def set_detector_status(param):
    """
    Summary:
        This interface can set the status of EDS detectors.

    Args: dictionary
        {"Position" : [2, 2, 3, 3]}

    Return:
        {"Result": "---"}
    """
    return base.run(name, "/Detector/Status",
                    "POST", interface.DetectorStatus(param))


@base.request(name, "/Detector/Reset", "POST")
def reset_detector():
    """
    Summary:
        This interface can reset a harware of detector.

    Args:
        None

    Return:
        {"Result": "---"}
    """
    return


@base.request(name, "/Acquisition/Settings", "GET")
def get_acquisition_settings():
    """
    Summary:
        This interface can get the settings of EDS acquisition.

    Args:
        None

    Return:
        {
            "ProcessTime": "T1",
            "DwellTime": 10.0,
            "CollectionMode": 3,
            "SweepCount": 1,
            "EnableScanSync": True,
            "Version": "---"
        }
    """
    return


def set_acquisition_settings(param):
    """
    Summary:
        This interface can set the settings of EDS acquisition.

    Args: dictionary
        {
            "ProcessTime" : "T1",
            "DwellTime" : 10.0,
            "CollectionMode" : 3,
            "SweepCount" : 1,
            "SelectedDetector" : [True,False,False,False],
            "EnableScanSync" : True
        }

    Return: dictionary
        {
            "ProcessTime": "T1",
            "DwellTime": 10.0,
            "CollectionMode": 3,
            "SweepCount": 1,
            "EnableScanSync": True,
            "Version": "---"
        }
    """
    return base.run(name, "/Acquisition/Settings",
                    "POST", interface.AcquisitionSettingParam(param))


# def set_acquisition_processtime(val):
#     return set_acquisition_settings(ProcessTime=val)


# def set_acquisition_dwelltime(val):
#     return set_acquisition_settings(DwellTime=val)


# def set_acquisition_collectionmode(val):
#     return set_acquisition_settings(CollectionMode=val)


# def set_acquisition_sweepcount(val):
#     return set_acquisition_settings(SweepCount=val)


# def set_acquisition_SelectedDetector(val):
#     return set_acquisition_settings(SelectedDetector=val)


# def set_acquisition_EnableScanSync(val):
#     return set_acquisition_settings(EnableScanSync=val)


@base.request(name, "/Acquisition/Start", "POST")
def start_acquisition():
    """
    Summary:
        This interface start an acquisition of EDS signals.
        If EnableScanSync is true, the scan generator should
        be started after this is called.

    Args:
        None

    Return:
        {
            "Message" : "This is a free text from EDS system.",
            "DataID" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        }
    """
    return


@base.request(name, "/Acquisition/Stop", "POST")
def stop_acquisition():
    """
    Summary:
        This interface stop the acquisition of EDS signals.

    Args:
        None

    Return:
        {
            "Message" : "This is a free text from EDS system.",
            "Result" : "OK"
        }
    """
    return


@base.request(name, "/Acquisition/Status", "GET")
def get_acquisition_status():
    """
    Summary:
        This interface can get the status of EDS acquisition.

    Args:
        None

    Return:
        {
            "Version": "---",
            "AcquisitionRunning" : False,
            "ElapsedLiveTime" : 12,
            "ElapsedRealTime" : 12,
            "SweepCount" : 2
        }
    """
    return


def get_spectrum_data(param):
    """
    Summary:
        This interface can get spectrum data that is acquiring or opened.

    Args: dictionary
        {"TargetDataID" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}

    Return:
        {
            "Version": "---",
            "SpectrumData": [0, 0, 0, ・・・]
        }
    """
    return base.run(name, "/Analysis/SpectrumData",
                    "POST", interface.SpectrumData(param))


def get_multiple_spectrum_data(param):
    """
    Summary:
        This interface can get acquiring spectrum data that specifying the position of line analysis data.

    Args: dictionary
    {
        "TargetDataID" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "StartPosition" : 2,
        "EndPosition" : 10
    }

    Return: dictionary
    """
    return base.run(name, "/Analysis/MultipleSpectrumData",
                    "POST", interface.SpectrumData(param))


@base.request(name, "/Analysis/MultipleLineData", "POST")
def get_multiple_line_data(TargetDataID, StartLine=None, EndLine=None):
    """
    Summary:
        This interface can get acquiring spectrum data that specifying the line position of spectrum imaging data. This is available for opend spectrum data.

    Args: dictionary
        {
            "TargetDataID" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "StartLine" : 2,
            "EndLine" : 5
        }

    Return: dictionary
    """
    return {"TargetDataID": TargetDataID,
            "StartLine": StartLine, "EndLine": EndLine}


def get_map_data(param):
    """
    Summary:
        This interface can get binary data of the elemental map. This is available for opend map data.

    Args: dictionary
        {
            "TargetDataID" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        }

    Return: dictionary
    """
    return base.run(name, "/Analysis/MapData",
                    "POST", interface.SpectrumData(param))


@base.request(name, "/Analysis/Settings", "GET")
def get_analysis_settings():
    """
    Summary:
        This interface can get the settings of analysis.

    Args:
        None

    Return:
        {
            "LengthOfSpectrum" : 4096,
            "UserCategories" : [
                "This is a list of standard data that the user create their own standard data. This string can be used for UserCategoryName for some analysis."
            ],
            "DisableElements" : [
                ["ElementalNumber", 8],
                ["ElementalNumber", 10]
            ],
            "QualitativeSensitivity" : "Middle",
            "ZAFEnable" : True,
            "PRZEnable" : True,
            "CliffLorimerEnable" : True
        }
    """
    return


@base.request(name, "/Analysis/Status", "GET")
def get_analysis_status():
    """
    Summary:
        This interface can get the status of analysis.

    Args:
        None

    Return:
        {
            "ExecutingAnalysis" : True,
            "Version" : "1.0",
        }
    """
    return


def execute_autoqualitative_analysis(param):
    """
    Summary:
        This interface execute auto qualitative analysis.
        This interface search the elements by peak of spectrum.
        This return the searched elements.

    Args: dictionary
        {
            "TargetDataID" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        }

    Return:
        {
            "Message" : "This is a free text from EDS system.",
            "Elements" : [
                ["ElementalNumber", 8],
                ["ElementalNumber", 10]
            ],
            "Result" : "OK"
        }
    """
    return base.run(name, "/Analysis/ExecuteAutoQualitativeAnalysis",
                    "POST", interface.SpectrumData(param))


@base.request(name, "/Analysis/QuantitativeSpectrumSettings", "GET")
def get_quantitative_spectrum_analysis_settings():
    """
    Summary:
        This interface can get the settings of quantitative analysis for spectrum.

    Args:
        None

    Return:
        {
            "StandardDataType" : 0,
            "UserCategoryName" : "USER",
            "CorrectionType" : 0,
            "EnableAbsorptionCorrection" : True,
            "Thickness" : 0,
            "Density" : 0,
            "EnableFluorescenceCorrection" : True,
            "ConversionType" : False,
            "OxideCation" : 0
        }
    """
    return


def set_quantitative_spectrum_analysis_settings(param):
    """
    Summary:
        This interface can set the settings of quantitative analysis for spectrum.

    Args: dictionary
        {
            "ProcessingMethod" : 0,
            "StandardDataType" : 0,
            "UserCategoryName" : "USER",
            "CorrectionType" : 3,
            "EnableAbsorptionCorrection" : True,
            "Thickness" : 5,
            "Density" : 0.01,
            "EnableFluorescenceCorrection" : True,
            "ConversionType" : 1,
            "OxideCation" : 24,
        }

    Return:
        {
            "ProcessingMethod" : 0,
            "StandardDataType" : 0,
            "UserCategoryName" : "USER",
            "CorrectionType" : 0,
            "EnableAbsorptionCorrection" : True,
            "Thickness" : 0,
            "Density" : 0,
            "EnableFluorescenceCorrection" : True,
            "ConversionType" : 1,
            "OxideCation" : 0
        }
    """
    return base.run(name, "/Analysis/QuantitativeSpectrumSettings",
                    "POST", interface.SpectrumSettings(param))


# def set_quantitative_spectrum_ProcessingMethod(val):
#     return set_quantitative_spectrum_analysis_settings(ProcessingMethod=val)


# def set_quantitative_spectrum_StandardDataType(val):
#     return set_quantitative_spectrum_analysis_settings(StandardDataType=val)


# def set_quantitative_spectrum_CorrectionType(val):
#     return set_quantitative_spectrum_analysis_settings(CorrectionType=val)


# def set_quantitative_spectrum_ConversionType(val):
#     return set_quantitative_spectrum_analysis_settings(ConversionType=val)


# @base.request(name, "/Analysis/ExecuteQuantitativeSpectrumAnalysis", "POST")
def execute_quantitative_spectrum_analysis(param):
    """
    Summary:
        This interface execute quantitative analysis for spectrum.

    Args: dictionary
        {
            "TargetDataID" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "Elements" : [
                {"ElementalNumber" : 8, "Line" : "K"},
                {"ElementalNumber" : 14, "Line" : "L"},
                {"ElementalNumber" : 18, "Line" : "M"},
            ],
            "TargetDetector" : 0
        }

    Return:
        {
            "Message" : "This is a free text from EDS system.",
            "Quantities" :[10.0, 20.0, 70.0],
            "Result": "OK"
        }
    """
    return base.run(name, "/Analysis/ExecuteQuantitativeSpectrumAnalysis",
                    "POST", interface.SpectrumAnalysis(param))


# @base.request(name, "/Analysis/ExtractLineSpectrum", "POST")
def extract_line_spectrum(param):
    """
    Summary:
        This interface can create an integrated spectrum that extracted from line analysis data.

    Args: dictionary
        {
            "TargetDataID" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        }

    Return:
        {
            "Message" : "This is a free text from EDS system.",
            "SpectrumDataID" : "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "Result" : "OK"
        }
    """
    return base.run(name, "/Analysis/ExtractLineSpectrum",
                    "POST", interface.SpectrumData(param))


# @base.request(name, "/Analysis/ExtractAreaSpectrum", "POST")
def extract_area_spectrum(param):
    """
    Summary:
        This interface can create an integrated spectrum that extracted from spectrum imaging data.

    Args: dictionary
        {
             "TargetDataID" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        }

    Return:
        {
            "Message" : "This is a free text from EDS system.",
            "SpectrumDataID" : "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "Result" : "OK"
        }
    """
    return base.run(name, "/Analysis/ExtractAreaSpectrum",
                    "POST", interface.SpectrumData(param))


# @base.request(name, "/Analysis/CreateCountLine", "POST")
def execute_count_line_analysis(param):
    """
    Summary:
        This interface create gross count data of line analysis.

    Args: dictionary
        {
            "TargetDataID" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "Elements" : [
                {"ElementalNumber" : 8, "Line" : "K"},
                {"ElementalNumber" : 14, "Line" : "L"},
                {"ElementalNumber" : 18, "Line" : "M"},
            ],
            "TargetDetector" : 0
        }

    Return: dictionary
    """
    return base.run(name, "/Analysis/CreateCountLine",
                    "POST", interface.SpectrumAnalysis(param))


@base.request(name, "/Analysis/NetCountLineSettings", "GET")
def get_net_count_line_analysis_settings():
    """
    Summary:
        This interface can get the settings of net count line analysis.

    Args:
        None

    Return: dictionary
    """
    return


# @base.request(name, "/Analysis/NetCountLineSettings", "POST")
def set_net_count_line_analysis_settings(param):
    """
    Summary:
        This interface can set the settings of net count line analysis.

    Args: dictionary
        {
            "ProcessingMethod" : 0,
            "StandardDataType" : 0,
        }

    Return: dictionary
    """
    return base.run(name, "/Analysis/NetCountLineSettings",
                    "POST", interface.SpectrumSettings(param))


# @base.request(name, "/Analysis/CreateNetCountLine", "POST")
def execute_net_count_line_analysis(param):
    """
    Summary:
        This interface create net count data of line analysis.

    Args: dictionary
        {
            "TargetDataID" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "Elements" : [
                {"ElementalNumber" : 8, "Line" : "K"},
                {"ElementalNumber" : 14, "Line" : "L"},
                {"ElementalNumber" : 18, "Line" : "M"},
            ],
            "TargetDetector" : 0
        }

    Return: dictionary
    """
    return base.run(name, "/Analysis/CreateNetCountLine",
                    "POST", interface.SpectrumAnalysis(param))


@base.request(name, "/Analysis/QuantitativeLineSettings", "GET")
def get_quantitative_line_analysis_settings():
    """
    Summary:
        This interface can get the settings of quantitative line analysis.

    Args:
        None

    Return: dictionary
    """
    return


@base.request(name, "/Analysis/QuantitativeLineSettings", "POST")
def set_quantitative_line_analysis_settings(dic):
    """
    Summary:
        This interface can set the settings of quantitative line analysis.

    Args: dictionary
        {
            "ProcessingMethod" : 0,
            "StandardDataType" : 0,
            "CorrectionType" : 3,
            "ConversionType" : 1,
            "EnableSumPeakRemoval " : True,
        }

    Return: dictionary
    """
    return dic


# @base.request(name, "/Analysis/CreateQuantitativeLine", "POST")
def execute_quantitative_line_analysis(param):
    """
    Summary:
        This interface create quantitative data of line analysis.

    Args: dictionary
        {
            "TargetDataID" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "Elements" : [
                {"ElementalNumber" : 8, "Line" : "K"},
                {"ElementalNumber" : 14, "Line" : "L"},
                {"ElementalNumber" : 18, "Line" : "M"},
            ],
            "TargetDetector" : 0
        }

    Return: dictionary
    """
    return base.run(name, "/Analysis/CreateQuantitativeLine",
                    "POST", interface.SpectrumAnalysis(param))


# @base.request(name, "/Analysis/CreateCountMap", "POST")
def create_count_map(param):
    """
    Summary:
        This interface create gross count mapping data.

    Args: dictionary
        {
            "TargetDataID" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "Elements" : [
                {"ElementalNumber" : 8, "Line" : "K"},
                {"ElementalNumber" : 14, "Line" : "L"},
                {"ElementalNumber" : 18, "Line" : "M"},
            ],
        "TargetDetector" : 0
        }

    Return: dictionary
    """
    return base.run(name, "/Analysis/CreateCountMap",
                    "POST", interface.SpectrumAnalysis(param))


@base.request(name, "/Analysis/NetCountMapSettings", "GET")
def get_net_count_map_settings():
    """
    Summary:
        This interface can get the settings of net count mapping.

    Args:
        None

    Return: dictionary
    """
    return


@base.request(name, "/Analysis/NetCountMapSettings", "POST")
def set_net_count_map_settings(dic):
    """
    Summary:
        This interface can set the settings of net count mapping.

    Args: dictionary
        {
            "PixelWidth" : 128,
            "PixelHeight" : 128,
            "ProcessingMethod" : 0,
            "StandardDataType" : 0,
        }

    Return: dictionary
    """
    return


# @base.request(name, "/Analysis/CreateNetCountMap", "POST")
def create_net_count_map(param):
    """
    Summary:
        This interface create net count mapping data.

    Args: dictionary
        {
            "TargetDataID" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "Elements" : [
                {"ElementalNumber" : 8, "Line" : "K"},
                {"ElementalNumber" : 14, "Line" : "L"},
                {"ElementalNumber" : 18, "Line" : "M"},
            ],
            "TargetDetector" : 0
        }

    Return: dictionary
    """
    return base.run(name, "/Analysis/CreateNetCountMap",
                    "POST", interface.SpectrumAnalysis(param))


@base.request(name, "/Analysis/QuantitativeMapSettings", "GET")
def get_quantitative_map_analysis_settings():
    """
    Summary:
        This interface can get the settings of quantitative mapping.

    Args:
        None

    Return: dictionary
    """
    return


@base.request(name, "/Analysis/QuantitativeMapSettings", "POST")
def set_quantitative_map_analysis_settings(dic):
    """
    Summary:
        This interface set the settings of quantitative mapping.

    Args: dictionary
        {
            "PixelWidth" : 128,
            "PixelHeight" : 128,
            "ProcessingMethod" : 0,
            "StandardDataType" : 0,
            "CorrectionType" : 3,
            "ConversionType" : 1,
            "EnableSumPeakRemoval" : True,
        }

    Return: dictionary
    """
    return dic


# @base.request(name, "/Analysis/CreateQuantitativeMap", "POST")
def create_quantitative_map(param):
    """
    Summary:
        This interface create quantitative mapping data.

    Args: dictionary
        {
            "TargetDataID" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "Elements" : [
                {"ElementalNumber" : 8, "Line" : "K"},
                {"ElementalNumber" : 14, "Line" : "L"},
                {"ElementalNumber" : 18, "Line" : "M"},
            ],
            "TargetDetector" : 0
        }

    Return: dictionary
    """
    return base.run(name, "/Analysis/CreateQuantitativeMap",
                    "POST", interface.SpectrumAnalysis(param))
