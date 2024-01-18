"""
Package for working with cv2 images, but encapsulating the various methods into an OOP style.

Creates classes for Colours and Images, as well as functions for various transforms.
"""
from ._enums import *
from ._colours import Colour
from ._images import Image
from . import transforms
