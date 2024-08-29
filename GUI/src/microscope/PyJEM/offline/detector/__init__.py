#
##以下の書き方だと、function内のメソッドを利用できる。
"""
offline detector package
"""
from . import function
from .function import *

from .. import base

    
    
base.setup_offlineData("detector")