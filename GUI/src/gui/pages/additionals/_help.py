import typing
from typing import Dict as _dict

from ... import utils
from ..._base import SettingsPage, widgets


class WhatsThis(SettingsPage):

    def __init__(self, **items: str):
        def _display(c: str) -> typing.Callable[[], None]:
            return lambda: self.prompt(items[c])

        super().__init__(utils.SettingsDepth.REGULAR)
        self._help_text = widgets.QTextEdit()
        self._help_text.setReadOnly(True)
        self._help_text.setFontPointSize(9)
        self._choices = [widgets.QRadioButton(subject.replace("_", " ")) for subject in items]
        for choice in self._choices:
            choice.clicked.connect(_display(choice.text().replace(" ", "_")))
            self._regular.addWidget(choice)
        self._layout.addWidget(self._help_text, 0, 0)
        self.setLayout(self._layout)
        self._items = items.copy()

    def items(self) -> _dict[str, str]:
        return self._items

    def compile(self) -> str:
        return ""

    def run(self):
        pass

    def clear(self):
        self._help_text.clear()

    def prompt(self, text: str):
        self._help_text.setText(text)

    def all_settings(self) -> typing.Iterator[str]:
        yield from ()
