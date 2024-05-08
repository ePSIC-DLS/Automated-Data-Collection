# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 15:19:27 2021

@author: EM
"""
#import sys
import os
import shutil
import json
from pathlib import Path


class JsonFileIO:
    _ins = {}
    def __init__(self, file):
        self.json_file = file
        self.is_exists = False
        # 選択したファイルが何らからのエラーで版損している場合
        if os.path.exists(self.json_file):
            if os.path.getsize(self.json_file) == 0:
                os.remove(self.json_file)
            else:
                self.is_exists = True
        self.dirpath = os.path.dirname(file)
        
    def __new__(cls, file):
        if cls._ins == None:
            cls._ins = {}
        if cls._ins == {}  or file not in cls._ins:
            cls._ins[file] = super().__new__(cls)
        
        return cls._ins[file]


    def read(self):        
        with open(self.json_file, "r", encoding="utf_8_sig") as f:
            return json.load(f)
                
    def write(self, data):
        if not self.is_exists and not os.path.exists(self.dirpath):
            make_dir(self.dirpath)
            
        with open(self.json_file, "w+", encoding="utf_8_sig") as f:
            f.seek(0)
            if type(data) == type(""):
                data = json.loads(data)
            f.write(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False, separators=(",",": ")))
            f.truncate()
        
class FileIO():
    def __init__(self, file):
        self.file = Path(file)
#        self.file.is_file()
#        self.file.is_dir()
#        self.file.exists()
        

def copy_file(src_path, dest_path):
    if not os.path.exists(dest_path):
        dir_name = os.path.dirname(dest_path)
        make_dir(dir_name)
        
    shutil.copyfile(src_path, dest_path)

def make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def make_file():
    print(os.getcwd())




















