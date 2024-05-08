# -*- coding: utf-8 -*-
"""
"""
import os
import logging
from logging import handlers

_root = "{}\log".format(os.path.abspath(os.path.dirname(__file__)))

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances.keys():
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    
#Singleton
class Logger(object):
    """多重書き込み
    """
    __metaclass__ = None

    _loggers = {}

    def __init__(self, *args, **kwargs):
        if not os.path.exists(_root):
            os.mkdir(_root)
            
    def __new__(cls):
        if cls.__metaclass__ == None:
            cls.__metaclass__ = super().__new__(cls)
        return cls.__metaclass__

    @staticmethod
    def get_logger(name="common"):
        formatter = logging.Formatter('[%(levelname)s], %(asctime)s, %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
        log_map = {name:"{}\{}.log".format(_root, name)}  
        logger = logging.getLogger(name)  # 場所がここで正しいのか？
#        fh = logging.FileHandler(log_map[name])
        fh = handlers.RotatingFileHandler(log_map[name],
                                                  encoding="utf-8",
                                                  maxBytes=1024*1024,   # 1MB分
                                                  backupCount=2,delay=False)     # 1GB分
        logger.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)   
        return logger


class LogManager:
    def __init__(self):
        self.__base_log =Logger()
        self.__error_logger = self.__base_log.get_logger("Error")
        self.__info_logger = self.__base_log.get_logger("Info")
        
        # print("error: {}".format(hash(self.__error_logger)))
        # print("info: {}".format(hash(self.__info_logger)))
    
    def info(self, msg):
        __message = ", ".join(msg)
        self.__info_logger.log(logging.INFO, __message)
    
    def error(self, msg):
        __message = ", ".join(msg)
        self.__error_logger.log(logging.ERROR, __message)



