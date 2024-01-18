"""
Subpackage for holding each section of the program.
"""
from modular_qt.microscope import __online__

__pyjem__ = __online__

from ._scan import ScanPage
from ._hist import HistPage
from ._preprocess import PreprocessPage
from ._cluster import SegmentationPage
from ._search import FocusScanPage
from ._automator import AutomationPage
from ._controller import MicroscopePage
from ._help import HelpPage
from . import base as pages, corrections, page_utils, extra_widgets
