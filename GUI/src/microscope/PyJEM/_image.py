# -*- coding: utf-8 -*-
"""
Created on Thu Nov  4 16:22:24 2021

@author: dmaekawa
"""
import os
import cv2
import time
import pathlib
import numpy as np
import matplotlib.pyplot as plt

from .config import get_config


class AcquireSetting:
    def __init__(self, img):
        self.ext_list = ["bmp", "tif", "jpg"]
        self.root_path = get_config("record_path")
        self.img = img
    
    def __del__(self):
        del self.img
    
    def save(self, filename, ext):
        file = self.get_record_file(filename,ext)
        with (open(file, "wb")) as f:
            f.write(self.img)
        return file
        
    def save_offline(self, filename, ext):
        file = self.get_record_file(filename,ext)
        cv2.imwrite(file, self.img)   
        return file
    
    def show(self,ext):
        # plt.gray()
        # img = cv2.imdecode(np.frombuffer(self.img, np.uint8), -1)
        file = self.save("temp", ext)
        return file
        img = cv2.imread(file)
        plt.imshow(img)
    
    def method(self, ext, save, filename, show,online=True):
        res = self.img
        if ext == None or ext not in self.ext_list:
            return 
        
        if online: 
            if save:
                filename = self.save(filename,ext)            
                res = filename
            if show:
                self.show(ext)
        else:
            if save:
                filename = self.save_offline(filename, ext)
                res = filename
            if show:
                file = self.get_record_file(filename,ext)

                self.show(file)
        return res

    def get_record_file(self, file, ext):
        if file is None:
            file = get_time_now_string()
        
        file = "{}.{}".format(file, ext)
            
        p = pathlib.Path(file)
        if p.is_absolute() == False:
            self.root_path = get_config("record_path")
            file = "{}\\{}".format(self.root_path,file)
        dir_path = os.path.dirname(file)
        if os.path.exists(dir_path) == False:
            os.makedirs(dir_path)
        return file

    def get_root_path(self):
        return self.root_path

    
    

def get_time_now_string():
    """
    現在時間の取得
    出力は文字列(YYYYMMDDhhmmss)
    """
    now_time = time.localtime()
    return get_time_string(now_time)

def get_time_string(time_value):
    """
    time_valueがtime.struct_time型
    time_valueから現在時間を文字列として出力する
    出力は文字列(YYYYMMDDhhmmss)
    """
    year_text = str(time_value.tm_year)
    month_text = str(time_value.tm_mon)
    if len(month_text) < 2:
        month_text = "0" + month_text
    day_text = str(time_value.tm_mday)
    if len(day_text) < 2:
        day_text = "0" + day_text
    hour_text = str(time_value.tm_hour)
    if len(hour_text) < 2:
        hour_text = "0" + hour_text
    minitue_text = str(time_value.tm_min)
    if len(minitue_text) < 2:
        minitue_text = "0" + minitue_text
    second_text = str(time_value.tm_sec)
    if len(second_text) < 2:
        second_text = "0" + second_text

    return year_text + month_text + day_text + hour_text + minitue_text + second_text 
