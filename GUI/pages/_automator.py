"""
Module to handle reading and writing PAL automation scripts.
"""
import os.path
import typing
from modular_qt import microscope, validators
from . import base, extra_widgets, PAL
from .base import widgets


class AutomationPage(base.Page):
    """
    Concrete subclass to wrap reading and writing of .GUIAS files into a GUI page.

    :var _panel FilePrompt: The front end panel for choosing a file.
    :var _log PyQt5.QWidgets.QTextEdit: A large region for displaying errors and contents of written files.
    :var _compilation Callable[[], str]: The function to compile all steps down into a string.
    """

    def __init__(self, compilation: typing.Callable[[], str], **function_space: typing.Callable[..., None]):
        super().__init__()
        self._panel = extra_widgets.FilePrompt("GUIAS", date_important=False)
        self._log = widgets.QTextEdit()
        self._log.setReadOnly(True)
        self._compilation = compilation
        self._panel.dialog().open.connect(self._execute)
        self._panel.dialog().save.connect(self._save)
        self._layout.addWidget(self._panel, 0, 0)
        self._layout.addWidget(self._log, 1, 0)
        self._mic = microscope.Microscope.get_instance()
        self._keywords: dict[PAL.grammar.KeywordType, typing.Callable[..., None]] = {}
        self._functions: dict[str, typing.Callable[..., None]] = {}
        self._setters: dict[str, typing.Callable[[typing.Any], None]] = {}
        for name, func in function_space.items():
            if name in PAL.KEYWORDS:
                self._keywords[PAL.KEYWORDS[name]] = func
            elif name in PAL.FUNCTIONS:
                self._functions[name] = func
            elif name in PAL.VARIABLES:
                self._setters[name] = func

    def compile(self) -> str:
        return ""

    def _set_mic_var(self, key: str) -> typing.Callable[[typing.Any], None]:
        def _inner(value):
            hardware, target = key.split(".")
            try:
                validation = PAL.KEYS[hardware][target]
            except KeyError:
                validation = validators.ValidationPipeline(validators.ValidationStep(validators.BlankValidator()))
            validation.validate(value)
            self._mic[key] = value

        return _inner

    def _execute(self, path: str):
        """
        Read and execute PAL code.

        :param path: The filepath to execute.
        """
        self._populate(path)
        if not os.path.exists(path):
            self._log.setText(f"No such file: {path}")
            return
        with open(path) as file:
            lex = PAL.Lexer(file.read())
            tokens = list(lex.run())
            par = PAL.Parser(*tokens)
            try:
                nodes = list(par.run())
            except PAL.ParsingError as err:
                self._log.setText(f"SyntaxError: {err.node.message}")
                return
            exe = PAL.Interpreter(*nodes, mic_setter=self._set_mic_var, keywords=self._keywords,
                                  variables=self._setters, functions=self._functions)
            try:
                exe.run()
            except Exception as err:
                if isinstance(err, KeyError):
                    err = f"Unknown key: {err}"
                self._log.setText(f"{err} at {exe.location}")
                return
        self._log.setText("Run completed")

    def _save(self, path: str):
        """
        Write a PAL script (a .GUIAS file).

        :param path: The filepath to write to.
        """
        return
        self._populate(path)
        comp_text = self._compilation()
        with open(path, "w") as file:
            file.write(comp_text)
        dash = '-' * 10
        self._log.setText(f"Write Successful!\n{dash}Contents Begin{dash}\n{comp_text}\n{dash}Contents End{dash}")

    def _populate(self, path: str):
        self._panel.file_path().setText(path.replace("\\", "/"))

    def run(self, btn_state: bool):
        pass

    def stop(self):
        super().stop()
        self.setEnabled(False)

    def start(self):
        super().start()
        self.setEnabled(True)
