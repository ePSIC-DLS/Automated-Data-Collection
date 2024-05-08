#
##以下の書き方だと、function内のメソッドを利用できる。
"""
offline detector package
"""
from . import function
from .function import *

from .. import base

# def setup_offlineData(name):
#     path = Path(__file__).parents[1]
#     # path = os.path.dirname(__file__).rsplit(r'\', 1)[0]
#     file = "{}\resources\offline_{}_data.json".format(path, name)
    
    
base.setup_offlineData("sightx")