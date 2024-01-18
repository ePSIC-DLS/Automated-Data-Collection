"""
Module to get help on certain prompts
"""
import typing

from . import base
from .base import widgets


class HelpPage(base.Page):
    """
    Concrete subclass to get help on specified materials.

    Prompts are controlled from radiobuttons, and messages are displayed in the field.

    :var _help dict[str, str]: The prompt names and relevant help.
    :var _btns list[PyQt5.QtWidgets.QRadioButton]: The radio buttons with available help topics.
    :var _log PyQt5.QtWidgets.QTextEdit: The help message for the appropriate feature.
    """

    def __init__(self, **record: str):
        limit = 9
        super().__init__()
        self._help = {}

        def _digits(key: str) -> str:
            for old_new in "one 1, two 2, three 3, four 4, five 5, six 6, seven 7, eight 8, nine 9, zero 0".split(","):
                o, n = old_new.split()
                key = key.replace(o, n)
            return key.replace("one", "1")

        for k, v in record.items():
            k = _digits(k.replace("_", " ").replace(" " * 2, "_")).replace("dot", ".")
            v_k = repr(k.replace(".", ""))
            self._help[k] = v.replace("{k}", v_k).replace("{K}", v_k.title())
        self._btns = [widgets.QRadioButton(name, self) for name in self._help]
        self._log = widgets.QTextEdit()
        self._log.setReadOnly(True)
        for i, btn in enumerate(self._btns):
            self._layout.addWidget(btn, i // limit, i % limit)
            btn.pressed.connect(self._show(btn.text()))
        self._layout.addWidget(self._log, len(record) // limit + 1, 0, 1, limit - 1)

    def compile(self) -> str:
        return ""

    def run(self, btn_state: bool):
        pass

    def _show(self, key: str) -> typing.Callable[[], None]:
        def _inner():
            self._log.setText(self._help[key])

        return _inner
