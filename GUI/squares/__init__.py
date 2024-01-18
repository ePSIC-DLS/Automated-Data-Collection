"""
Package for handling images and performing detection for a grid of squares, given a known square size

Adds the ROIS, transforms, all colour data, the Image and Pyramid class to the "SquareDetection" namespace

Allows image processing through the usage of an Image class (which is a wrapper for the image being represented as a
numpy ndarray). This allows for blending, merging, getting pixel data, setting pixel data and more. For full information
use help(SquareDetection.Image).

Also has a series of Regions Of Interest (ROIs) for highlighting key points of an image

The package also adds in a colour class for creating simple colours using an RGB code. It also provides an alternative
constructor in the form of the static method "from_colour", from creating a colour using a known colour flag, a strength
of the colour, and a lightness of the colour.

There are also transformations that can be applied to both images and regions of interest.
"""
from .image import Image
from . import ROIs
from . import transforms
from .colour import Colour
from .pyramid import Pyramid
from .enums import *

