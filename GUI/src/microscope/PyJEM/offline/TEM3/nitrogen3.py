# -*- coding: utf-8 -*-
"""
Created on Mon Jun 21 15:35:58 2021

@author: dmaekawa
"""
import time

import os
import json

offline_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
nitro_file = str(offline_path) + r"\resources\nitrogen3_data.json"


class Nitrogen3:

    def __init__(self):
        self.__timer = 5
        self.__refill = [0, 1]
        self.__plevel = [0, 30]
        self.__pmin = [0, 2]
        self.__ismoving = 0
        self.__holder_count = 5

        try:
            if not os.path.exists(nitro_file):
                print(nitro_file)
                with open(nitro_file, "w+", encoding="utf_8_sig") as f:
                    f.seek(0)
                    data = [_MagazineInfo(i, 0, 0).__dict__ for i in range(self.__holder_count)]
                    f.write(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False, separators=(",", ": ")))
                    f.truncate()

            with open(nitro_file, "r", encoding="utf_8_sig") as f:
                self.__magazinelist = json.load(f)
        except:
            self.__magazinelist = [_MagazineInfo(0, 0, 0).__dict__]

    def GetRefillStatus(self, target):
        '''
        Summary:
            Get the supply status of liquid nitrogen.
        Args: int
            * target-> 1=Stage ACD Tank, 2=Transfer ACD Tank
        Return: int
            0=Stop, 1=Supply
        '''
        if target < len(self.__refill):
            return self.__refill[target]
        return

    def ExecRefill(self, target, status):
        '''
        Summary:
            Set the supply status of liquid nitrogen.
        Args: (int)target, (int)status
            * target-> 1=Stage ACD Tank, 2=Transfer ACD Tank
            * status-> 0=Stop, 1=Supply
        Return: NoneType
            None
        '''
        if target < len(self.__refill):
            self.__refill[target] = status

    def GetSampleInformation(self, no):
        '''
        Summary:
            Get sample information
        Args: int
            * no-> Holder number (0-)
        Return: list((int)id,(int)station,(int)port,(int)angle,(int)cartridge,(str)name)
            * id->holder id.
            * station-> 1=Magazine, 2=SampleStorage, 3=Transfer ACD Tank
            * port-> port
            * angle-> 0=no rotation, 1=0(deg), 2=90(deg)
            * cartridge->
            * name-> holder name.
        '''
        if 0 <= no and no < len(self.__magazinelist):
            __ = self.__magazinelist[no]
            res = [
                __["id"],
                __["station"],
                __["port"],
                __["angle"],
                __["cartridge"],
                __["name"]]
            return res
        return

    def GetCurrentScenarioStatus(self):
        '''
        Summary:
            Acquisition of transport scenario status .
        Args:
            no argument.
        Return: int
            0=Stop, 1=Execute
        '''
        return self.__ismoving

    def GetMagazineExistStatus(self):
        '''
        Summary:
            Get the presence or absence of a magazine
        Args:
            no argument.
        Return: int
            1=Exist magazine, 2=No magazine
        '''
        data = [i["station"] for i in self.__magazinelist]
        return 1 in data

    def TransferCartridge(self, _id, station, angle):
        '''
        Summary:
            Transport the sample specified by id to the specified station
        Args: (int)_id, (int)station, (int)angle
            * _id-> holder id
            * station-> 1=Magazine, 2=SampleStrorage, 3=Stage
            * angle-> 0=no rotation, 1=0(deg), 2=90(deg)
        Return: NoneType
            None
        '''
        for data in self.__magazinelist:
            if data["id"] == _id:
                data["station"] = station
                data["angle"] = angle

        self.__ismoving = 1
        time.sleep(self.__timer)
        self.__ismoving = 0
        return

    def GetLiquidLevel(self, target):
        '''
        Summary:
            Get the level level of liquid nitrogen
        Args: (int)target
            * target-> 1=Stage ACD Tank, 2=Transfer ACD Tank
        Return: list((int)level, (int)refill)
            level= liquid level(%)
            refill= 0=Stop, 1=Execute
        '''
        if target < len(self.__plevel) and target < len(self.__pmin):
            return [self.__plevel[target], self.__pmin[target]]
        return

    def __update_magazine_list(self, no, station, angle):
        __flag = True
        for data in self.__magazine_list:
            if data.no == no:
                data.station = station
                data._angle = angle
                __flag = False
        if __flag:
            self.__magazine_list.append(_MagazineInfo(no, station, angle).__dict)


class _MagazineInfo:

    def __init__(self, _id, station, angle):
        self.id = _id
        self.station = station
        self.angle = angle
        self.port = 0
        self.cartridge = 0
        self.name = "No. {}".format(_id)
