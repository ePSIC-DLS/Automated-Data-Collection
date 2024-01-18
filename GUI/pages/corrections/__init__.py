"""
Subpackage to represent corrections that can be performed on the microscope.
"""
from .base import BaseCorrection
from .beam_blank import Beam
from .beam_flash import Emission
from .autofocus import Focus
