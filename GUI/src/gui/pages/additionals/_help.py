import typing

from ... import utils
from ..._base import SettingsPage, widgets


class WhatsThis(SettingsPage):
    """
    Concrete settings page for displaying help on specified items.

    Attributes
    ----------
    _help_text: QTextEdit
        The widget displaying the help text.
    _choices: tuple[QRadioButton, ...]
        The various available items to get help on.
    """

    def __init__(self, **items: str):
        def _display(c: str) -> typing.Callable[[], None]:
            return lambda: self.prompt(items[c])

        super().__init__(utils.SettingsDepth.REGULAR)
        self._help_text = widgets.QTextEdit()
        self._help_text.setReadOnly(True)
        self._help_text.setFontPointSize(9)
        self._choices = tuple(widgets.QRadioButton(subject.replace("_", " ")) for subject in items)
        for choice in self._choices:
            choice.clicked.connect(_display(choice.text().replace(" ", "_")))
            self._regular.addWidget(choice)
        self._layout.addWidget(self._help_text, 0, 0)
        self.setLayout(self._layout)

    def compile(self) -> str:
        return ""

    def run(self):
        pass

    def clear(self):
        self._help_text.clear()

    def prompt(self, text: str):
        """
        Function to set the display text.

        Parameters
        ----------
        text: str
            The text to display.
        """
        self._help_text.setText(text)

    def all_settings(self) -> typing.Iterator[str]:
        yield from ()
