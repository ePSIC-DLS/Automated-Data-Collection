import json
import os
import typing

from ..pipeline import Clusters
from ... import utils
from ..._base import ProcessPage, SettingsPage, core, widgets
from .... import validation
from ..._errors import *


class DiffractionFilter(ProcessPage, SettingsPage):
    fileExecuted = core.pyqtSignal(str)
    settingChanged = SettingsPage.settingChanged

    def __init__(self, previous: Clusters):
        ProcessPage.__init__(self)
        SettingsPage.__init__(self, utils.SettingsDepth.REGULAR)
        self._clusters = previous
        self._filter = widgets.QPushButton("C&ollect diffraction data from clusters")
        self._filter.clicked.connect(lambda: self.run())
        self._in_path = utils.LabelledWidget("Data Analysis File", utils.FilePrompt("py"), utils.LabelOrder.SUFFIX)
        self._out_path = utils.LabelledWidget("JSON Path", utils.FilePrompt("JSON"), utils.LabelOrder.SUFFIX)
        self._regular.addWidget(self._filter)
        self._regular.addWidget(self._in_path)
        self._regular.addWidget(self._out_path)
        self._in_path.focus.setEnabled(False)
        self._in_path.focus.dialog().openFile.connect(self._open)
        self.fileExecuted.connect(self._read)
        self.setLayout(self._layout)
        self._automate = False

    @utils.Thread.decorate(manager=ProcessPage.MANAGER)
    def _open(self, path: str):
        with open(path) as code:
            exec(code.read(), {}, {})
        self.fileExecuted.emit(os.path.dirname(path))

    def _read(self, path: str):
        with open(path) as input_json:
            print(json.load(input_json))

    def clear(self):
        ProcessPage.clear(self)
        SettingsPage.clear(self)

    def start(self):
        ProcessPage.start(self)
        SettingsPage.start(self)

    def stop(self):
        ProcessPage.stop(self)
        SettingsPage.stop(self)

    def compile(self) -> str:
        return ""

    @utils.Tracked
    def run(self):
        self.runStart.emit()
        regions = self._clusters.get_clusters()
        if not regions:
            raise StagingError("run data analysis filters", "segmenting pre-processed image")
        if not self._automate:
            self._search()
        else:
            self._search.py_func(None)

    @utils.Stoppable.decorate(manager=ProcessPage.MANAGER)
    def _search(self, progress: typing.Optional[int]):
        self._in_path.setEnabled(True)
        self.runEnd.emit()

    def automate(self):
        self._automate = True
        try:
            self.run.py_func()
        finally:
            self._automate = False

    def all_settings(self) -> typing.Iterator[str]:
        yield from ()

    def help(self) -> str:
        s = f"""This page allows for collecting diffraction data on the clusters.
        This allows for filtering of which clusters to accept based on the output of some analysis.
        
        The diffraction data collection will modify (or create if non-existent) the JSON file provided to specify the;
        data file and cluster label for each found cluster. 
        Then the data analysis is expected to read this and modify the file such that it now contains a 'chosen' flag. 
        The page will then filter all clusters who's flag is False. 

        Settings
        --------
        Data Analysis File:
            No Validation

            The chosen file to use for data analysis. This control is locked until the collection has been performed.
        JSON Path:
            No Validation

            The json file to use.
        """
        return s
