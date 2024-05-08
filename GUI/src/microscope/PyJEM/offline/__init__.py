# # -*- coding: utf-8 -*-
# """
# Offline code
# """
# import os

# from .. import _fileio

# class Data(_fileio.JsonFileIO):
#     """private offline class"""
#     _ins_dict = {}
#     _instance = None
    
#     def __init__(self, name):
#         self.name = name        
#         self.path = os.path.dirname(__file__)
#         file = "{}\{}.json".format(self.path, name)
#         super(Data, self).__init__(file)
#         if not os.path.exists(file):
#             self.write([])
#         self.datatable = self.read()
        
#     def __new__(cls, name):
#         "Singleton"       
#         if len(cls._ins_dict) == 0:
#             if not cls._instance:     # First instance
#                 cls._instance = super().__new__(cls)
#                 cls._ins_dict.update({name:cls._instance})       
#         else:
#             if not name in cls._ins_dict:        # instanceを1回も作成しておらずdictにない。
#                 cls._instance = super().__new__(cls)
#                 cls._ins_dict.update({name:cls._instance})
#             else:
#                 cls._instance = cls._ins_dict[name]    
#         return cls._instance   
   
#     def getter(self, name, key=""):
#         """
                
#         """
#         a_data = [name in i["name"] for i in self.datatable]
#         if True in a_data:
#             index = a_data.index(True)
#             current = self.datatable[index]
#             if key != "" and key in current["data"]:
#                 res = current["data"][key]
#             else:
#                 res = self.datatable[index]["data"]
#             # 単純なこの作りではうまくいかなくなると思うので、ある程度dictにアクセスできる必要がある
#             return res
        
#     def setter(self, name, data, key=""):
#         """
        
#         """
#         a_data = [name in i["name"] for i in self.datatable]
#         temp = _Format(name, data)
#         if True not in a_data:
#             self.datatable.append(temp.__dict__)           

#         else:
#             index = a_data.index(True)
#             current = self.datatable[index]
#             if key != "":
#                 for k in list(data.keys()):
#                     if k in current["data"]:
#                         self.datatable[index]["data"][k] = data[k]
#             else:
#                 self.datatable[index] = temp.__dict__
            
#         self.write(self.datatable)

#         return data

# #    def get_image(self, ext, outtype):
# #        """
# #        outtype: 
# #            0= bytes
# #            1= filename
# #        """                
# #        file = "{}\snapshot.{}".format(self.path, ext)
# #        img = file
# #        if outtype == 0:
# #            pass
# #        return img
    
#     def initialize(self,object):
#         """
#         initialize method
#         * make offline data.
#         """
#         if type(object) is list:
#             data = [i.__dict__ for i in object]
#             self.write(data)



# class _Format:
#     def __init__(self, name, data):
#         self.name = name
#         self.data = data
        
# #    def method(self, *args):
# #        return sys._getframe().f_code.co_name
        
        