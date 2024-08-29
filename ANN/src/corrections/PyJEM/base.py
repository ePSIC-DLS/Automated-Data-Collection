# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 13:42:38 2021

@author: dmaekawa
"""
import os
import json
import httplib2
from functools import wraps

from . import _log
from . import filesystem as fs
from . import config as setting

PYJEM_URI_FILE = "{}/uri.json".format(os.path.dirname(__file__))

class Connect(fs.JsonFileIO):
    def __init__(self):
        super().__init__(PYJEM_URI_FILE)
        
        if not self.is_exists:
            self.write(list())
        self._config = self.read()
        
    def __new__(cls):
        return super().__new__(cls, PYJEM_URI_FILE)

    ## ipythonで実行するとエラーとなるためコメントアウト
    # def __del__(self):
        # fileベースにすると複数装置に接続ができなくなるので、
        #　インスタンス削除時にfileの更新の方が無難な気がする
        # self.upload()
        
    def initialize(self, name, ip, port, uri):
        _format = {"name":name, 
                    "ip":ip, 
                    "port":port,
                    "uri":uri}
        if not self.exist(name):
            self.setter(_format)
    
    def parse(self, url):
        return httplib2.urllib.parse.quote(url, safe=":/")
    
    def get_url(self, name):
        match = [c for c in self.config if c.get("name") == name]
        if not match:
            return # config無し
        match = match[0]
        url = "http://{}:{}/{}".format(match["ip"], match["port"], match["uri"])
        return self.parse(url)

    
    def exist(self,name):
        if not [c for c in self._config if c["name"] == name]:
            return False
        return True

    def upload(self):
        self.write(self.config)
        
    def setter(self, data):
        name = data["name"]        
        if self.exist(name):
            self.update(name, data)
        else:
            self.add(data)
    
    def getter(self, name):
        check = [c for c in self._config if c["name"] == name]
        if len(check) == 0:
            return None
        elif len(check) == 1:
            return check[0]
        else:
            raise "複数の設定が存在します"
    
    def update(self, name, data):
        conf = self.getter(name)
        self.config[self.config.index(conf)] = data
        self.upload()

    def add(self, data):
        temp = self.config
        temp.append(data)
        self.config = temp

    @property
    def config(self):
        return self._config
    
    @config.setter
    def config(self, data):
        self._config = data
        # configが更新されたら、ファイルも更新
        self.upload()

        

con = Connect()
log = _log.LogManager()

def initialize(name, ip, port, uri):
    con.initialize(name, ip, port, uri)
    return 

def change_ip(name, ip):
    temp = con.getter(name)
    temp["ip"] = ip
    con.update(name, temp)

def change_port(name, port):
    temp = con.getter(name)
    temp["port"] = port
    con.update(name, temp)

def get_config(name):
    return con.getter(name)


client = httplib2.Http(os.path.dirname(__file__) + "/.cache")
header = {'connection':'close'}

def request(*d_args):
    """
    d_args[0] = name, 
    d_args[1] = Uri, 
    d_args[2] = Method, 
    
    kw is post's key, value.
    f_args is override data. ex) uri ...
    """
    name = d_args[0]
    uri = d_args[1]
    method = d_args[2]
    cast=None
    if len(d_args) == 4:
        cast = d_args[3]
    def _request(func):
        @wraps(func)
        def wrapper(*f_args, **kw):
            # print(kw, f_args)
            url = con.get_url(name)
            url += uri
            message = make_list(name, func.__name__, method, url)
            try:
                if not kw and not f_args:
                    res, cont = client.request(url, method, headers=header)                                  
                elif not kw:
                    body = func(*f_args)
                    body = _filter(body)
                    body = json.dumps(body)
                    res, cont = client.request(url, method,body=body, headers=header)
                    message.append(body)
                else:
                    body = func(kw)
                    body = _filter(body)
                    body = json.dumps(body)
                    res, cont = client.request(url, method,body=body, headers=header)
                    message.append(body)
                if setting.get_config("log"):
                    log.info(message)
                    
                # 戻りのHttp Statusのチェック
                check(res)
                    
                if cast == "image":
                    return cont
                # return json.loads(cont.decode("utf-8"))
                
                return decode(cont)
            except:
                import traceback
                msg = traceback.format_exc()
                message.append("\n{}".format(msg))
                if setting.get_config("log"):
                    log.error(message)
                raise
        return wrapper
    return _request


def make_list(*args):
    return list(args)

def _filter(data):
    for k in list(data):
        if type(data[k]) is dict:
            _filter(data[k])
        if data[k] == None:
            del data[k]
    return data



def decode(output):
    try:
        res= output.decode("utf-8")
        if res == "":
            return res
        return json.loads(res)
    except:
        return output


# URiの文字列の変更踏まえて変更
def overlap(func):
    def wrapper(*args, **kw):
        result = func(**kw)
        return result

    return wrapper

def run(name, uri, method, body=None, cast=None):        
    
    @overlap
    @request(name, uri, method)
    def executer(*args, **body):
        return args[0]

    @overlap
    @request(name, uri, method, cast)
    def executer_image(**body):
        return 
    
    if cast is None:
        if not body:
            return executer()
        else:
            return executer(**body)
    else:
        if not body:
            return executer_image()
        else:
            return executer_image(**body)

    
class UriFormat:
    def __init__(self):
        """
        name: サービス名
        ip: ipaddress
        port: port番号
        service: RESTService名
        connect: online, offline        
        """
        self.name = ""
        self.ip = ""
        self.port = ""
        self.service = ""
        self.connect = ""


class HTTPStatus:
    """
    https://developer.mozilla.org/ja/docs/Web/HTTP/Status
    """
    _instance = None
    def __new__(cls):
        if cls._instance == None:
            code = {}
            code.update({200:"OK"})
            code.update({201:"Created"})
            code.update({300:"Multiple Choice"})
            code.update({400:"Bad Request"})
            code.update({401:"Unauthorized"})
            code.update({402:"Payment Required"})
            code.update({403:"Forbidden"})
            code.update({404:"Not Found"})
            code.update({405:"Method Not Allowed"})
            code.update({500:"Internal Server Error"})
            
            cls._instance = code
        return cls._instance

def check(response):
    statusDict = HTTPStatus()
    
    if not type(response) == httplib2.Response:                
        raise 

    if 200 <= response.status and response.status <300:
        return statusDict[response.status]
    else:
        raise Exception("Http status error has occured. Http status= {}, message= {}".format(response.status, statusDict[response.status]))
        
    
            



class BaseClass:
    def __init__(self, *args, **kw):
        if args != ():
            self._param = args[0]
        elif kw != {}:
            self._param = kw
        else:
            self._param = {}               
    
    
    def __new__(cls, *args, **kw):
        if args != ():
            para = args[0]
        elif kw != {}:
            para = kw
        else:
            para = {}
        return para               
        
    
    def setter(self, data):
        self.param = {k:w for k,w in data.items() if k in self.key}

def get_enum_list(object):
    return [e.value for e in object]





