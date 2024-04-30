import typing
from typing import Dict as _dict

from ... import utils
from ..._base import core, Page, widgets
from .... import language, images


class Scripts(Page):
    L_NAME = "PAL"

    def __init__(self, variable_handler: typing.Callable[[str, object], None], variables: _dict[str, object],
                 keywords: _dict[language.grammar.KeywordType, typing.Callable],
                 **functions: typing.Callable):
        super().__init__()

        def _ready():
            self._output.clear()
            self._progress.setValue(0)
            self._progress.setMaximum(0)
            try:
                with open(self._path) as file:
                    program = file.read()
                tokens = list(language.formation.Lexer(program).run())
                nodes = list(language.formation.Parser(*tokens).run())
                max_line = nodes[-1].src.position[0]
                self._progress.setMaximum(max_line + 1)
                language.execution.Resolver(self._interpreter).resolve(*nodes)
                self._progress.setValue(1)
                for ln in self._interpreter.execute(*nodes):
                    self._progress.setValue(ln + 1)
                self._progress.setValue(max_line + 1)
            except (language.CompilationError, language.ResolutionError, language.InterpretationError) as err:
                self._output.setText(str(err))
                pos = self._interpreter.position
                ln = int(pos[:pos.find(":")]) + 1
                self._progress.setValue(ln)

        self._interpreter = ScriptInterpreter(variable_handler, variables, keywords,
                                              display=language.NativeFunction(self._output),
                                              **{k: language.NativeFunction(v) for k, v in functions.items()}
                                              )
        path = r"./assets"
        # path=utils.FileDialog.BASE
        self._prompt = utils.FilePrompt("GUIAS", block=False,
                                        path=path)
        self._output = widgets.QTextEdit()
        self._progress = widgets.QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setFormat("Executing statement #%v")
        self._output.setFontPointSize(12)
        self._output.setReadOnly(True)
        self._layout.addWidget(self._output, 0, 0)
        self._layout.addWidget(self._prompt, 0, 1)
        self._layout.addWidget(self._progress, 1, 0)
        self.setLayout(self._layout)
        self._prompt.dialog().openFile.connect(self._run_file)
        self._prompt.dialog().finished.connect(_ready)
        self._path = ""

    def interpreter(self) -> "ScriptInterpreter":
        return self._interpreter

    def _run_file(self, path: str):
        self._path = path

    def _output(self, pos: str, text):
        self._output.append(f"Output from line {pos[:pos.find(':')]}: {text!r}")

    def compile(self) -> str:
        return ""

    def run(self):
        pass

    def clear(self):
        pass

    def start(self):
        super().start()
        self.setEnabled(True)

    def stop(self):
        super().stop()
        self.setEnabled(False)

    def help(self) -> str:
        s = f"""This page allows for running automation scripts using the language designed for the GUI.
        This language ({self.L_NAME}) runs from files with the ".GUIAS" extension.
        
        {self.L_NAME} is a dynamically typed DSL (Domain-Specific Langauge) that automates certain aspects of the GUI.
        
        It supports number, string, path, collection, hexadecimal and binary literals;
        with limited unary and binary operations.
        
        For the grammar and builtin library, see the help page"""
        return s

    def advanced_help(self) -> str:
        s = f"""Glossary:
        Scan keyword
            "Scan"
            The scan keyword performs the same operation as the 'Scan' button on the GUI.
        Cluster keyword
            "Cluster"
            The cluster keyword performs the same operation as the 'Cluster' button on the GUI.
        Filter keyword
            "filter"
            The filter keyword will collect diffraction data from the 'Segmented Image/Analysis' page.
        Mark keyword
            "mark"
            The mark keyword will act like clicking on the 'Cluster Manager', except it will click *all* clusters found.
        Tighten keyword
            "Tighten"
            The tighten keyword will act like the 'Tighten' button on the 'Cluster Manager';
            it will also act the same as the 'Export' button on the 'Cluster Manager' after tightening.
        Search keyword
            "Search"
            The search keyword performs the same operation as the 'Search' button on the GUI.
        
        Drift keyword
            "drift"
            This keyword is an expression used in the 'correct_for' function. It represents the drift correction.
        Emission keyword
            "emission"
            This keyword is an expression used in the 'correct_for' function. It represents the emission correction.
        Focus keyword
            "focus"
            This keyword is an expression used in the 'correct_for' function. It represents the focus correction.
        Manhattan keyword
            "Manhattan"
            This keyword is an expression used as a possible value for the 'algorithm' variable.
            It represents the Manhattan algorithm.
        Euclidean keyword
            "Euclidean"
            This keyword is an expression used as a possible value for the 'algorithm' variable.
            It represents the Euclidean algorithm.
        Minkowski keyword
            "Minkowski"
            This keyword is an expression used as a possible value for the 'algorithm' variable.
            It represents the Minkowski algorithm.
        True keyword
            "true"
            This keyword is an expression representing a true value (or a ticked checkbox, or an 'on' state).
        False keyword
            "false"
            This keyword is an expression representing a false value (or an unticked checkbox, or an 'off' state).
        
        Var keyword
            "var <NAME> '=' <VALUE>"
            This keyword declares the variable <NAME> with initial variable <VALUE>;
            <VALUE> can be any valid {self.L_NAME} expression.
            
            {self.L_NAME} does not support a 'null' value or uninitialized variables;
            assigning a variable to any value that equates to python's None value is an error.
        Func keyword
            "func <NAME> '('[<NAME> (',' <NAME>)*]')' <BLOCK>"
            This keyword declares a function called <NAME>, which accepts any number of parameters;
            (parameters are specified by a comma-separated list of names).
            
            {self.L_NAME} does not support default values for parameters, and assumes all parameters are positional.
            Furthermore, as there is not a proper type system, there are no type hints. 
            In this documentation python-style type hints are used to express the expected type of builtin functions;
            as these are written in python. However, the type hints have been renamed to {self.L_NAME} names. 
            
            As assignment is a separate expression; 
            there is no 'global' or 'nonlocal' keyword for outer scope assignment.
        Repeat keyword
            "repeat [<VALUE>] <BLOCK>"
            This keyword begins a loop that repeats a block of code a certain number of times.
            If the amount is unspecified (when the <VALUE> is omitted), it will indefinitely repeat the code.
        Wait keyword
            "wait <VALUE>"
            This keyword delays for a certain amount of seconds.
        Return keyword
            "return [<VALUE>]"
            This keyword returns a value from a function. When the <VALUE> is omitted;
            it is an early termination from the function.
        
        ----------------------------------------------------------------------------------------------------------------
        
        <BLOCK> is defined as:
            " '{{' <STMT>* '}}' "
        <STMT> is defined as:
            "<VAR> | <FUNC> | <KEYSTMT> | <VALUE>"
        <KEYSTMT> is any keyword that is a statement.
        <VALUE> is defined as:
            <NAME> | <KEYEXPR> | <LITERAL> | <UNARY> | <GROUP> | <BINARY> | <CALL> | <ASSIGN> | <GET>
        <KEYEXPR> is any keyword that is an expression.
        
        To form each literal:
            A string is any character surrounded by double quotes;
            ('"' <CHARACTER>* '"').
            A path is any character surrounded by single quotes; 
            (''' <CHARACTER>* '''). This differs from a string in that quotes remain in the resulting string.
            A number is defined as expected. {self.L_NAME} does not support python's exp format;
            so 1e3 is interpreted as the number '1', followed by the variable 'e', followed by the number '3'.
            A hexadecimal number is defined using a preceding '\\x' marker and then any valid hexadecimal character;
            ('\\x'((0-9) | (A-F) | (a-f))+). This is evaluated to an integer.
            A binary number is defined using a preceding '\\b' marker and then any valid binary character;
            ('\\b'(0 | 1)+). This is evaluated to an integer.
            A collection is defined by putting any number of comma-separated expressions inside square brackets;
            ('[' ']' | '[' <VALUE> (',' <VALUE>)* ']'). This is immutable and cannot be changed later.
        
        The unary operators are:
            '-' which performs unary negation on the operand. Only valid for numerical operands.
        
        The binary operators are:
            '^' which performs an equivalent operation to python's exp format;
            it is only valid for numerical operands.
            The operator is such that "7 ^ 3" is 7000 but "7 ^ -3" is 0.007.
        
        Unlike python, assignment is a valid expression, and can be used anywhere an expression is expected."""
        return s

    def standard_library(self) -> str:
        s = f"""Functions:
        output:
            "output(arg)"
            Append the specified argument to the display. All calls to this function are newline separated.
        blur:
            "blur(arg1, arg2)"
            Perform the same operation as the preprocessing option 'blur'.
        gss_blur:
            "gss_blur(arg1, arg2, arg3, arg4)"
            Perform the same operation as the preprocessing option 'gss_blur'.
        sharpen:
            "sharpen(arg1, arg2, arg3)"
            Perform the same operation as the preprocessing option 'sharpen'.
        median:
            "median(arg)"
            Perform the same operation as the preprocessing option 'median'.
        edge:
            "edge(arg)"
            Perform the same operation as the preprocessing option 'edge'.
        threshold:
            "threshold()"
            Perform the same operation as the preprocessing option 'threshold'.
        open:
            "open(arg1, arg2, arg3, arg4, arg5)"
            Perform the same operation as the preprocessing option 'open'.
        close:
            "close(arg1, arg2, arg3, arg4, arg5)"
            Perform the same operation as the preprocessing option 'close'.
        gradient:
            "gradient(arg1, arg2, arg3, arg4, arg5)"
            Perform the same operation as the preprocessing option 'gradient'.
        i_gradient:
            "i_gradient(arg1, arg2, arg3, arg4, arg5)"
            Perform the same operation as the preprocessing option 'i_gradient'.
        e_gradient:
            "e_gradient(arg1, arg2, arg3, arg4, arg5)"
            Perform the same operation as the preprocessing option 'e_gradient'.
        Raster:
            "Raster(start: corner, coverage: collection, line_skip: number, stroke_orientation: str)"
            Emulates a raster pattern using the specified arguments. The 'coverage' should be two elements long.
        Snake:
            "Snake(start: corner, coverage: collection, line_skip: number, stroke_orientation: str)"
            Emulates a snake pattern using the specified arguments. The 'coverage' should be two elements long.
        Spiral:
            "Spiral(starting_length: number, x_order: string, y_order: string, growth_factor: number#
            , coverage: collection)"
            Emulates a square spiral pattern using the specified arguments. The 'coverage' should be two elements long.
        Grid:
            "Grid(gap: collection, coverage: collection, shift: collection)"
            Emulates a checkerboard pattern using the specified arguments. All arguments should be two elements long.
        Random:
            "Random(n: number, under_handler: underflow, over_handler: overflow, coverage: collection, type_: random#
            , scale: number, loc: number, lam: number, low: number, high: number)"
            Emulates a random pattern using the specified arguments. The 'coverage' should be two elements long.
        correct_for:
            "correct_for(correction: drift | focus | emission)"
            Runs the specified correction.
        
        ----------------------------------------------------------------------------------------------------------------
        
        Variables:
        num_groups
            Represents the 'Colour Groups' setting from the Survey Histogram.
        minima 
            Represents the 'Minima' setting from the Processed Image.
        maxima 
            Represents the 'Maxima' setting from the Processed Image.
        threshold_inversion 
            Represents the 'Threshold Inversion' setting from the Processed Image.
        epsilon 
            Represents the 'Epsilon' setting from the Segmented Image.
        minimum_samples 
            Represents the 'Minimum Samples' setting from the Segmented Image.
        algorithm 
            Represents the 'Distance Algorithm' setting from the Segmented Image.
        square 
            Represents the 'Square Distance' setting from the Segmented Image.
        power 
            Represents the 'Minkowski Power' setting from the Segmented Image.
        size 
            Represents the 'Cluster Size' setting from the Segmented Image.
        size_match 
            Represents the 'Size Match' setting from the Segmented Image.
        overlap 
            Represents the 'Overlap Percentage' setting from the Cluster Manager.
        overlap_directions 
            Represents the 'Overlap Directions' setting from the Cluster Manager.
            Note that the variable should be assigned a collection of elements that obey the validation specified.
        match 
            Represents the 'Match Percentage' setting from the Cluster Manager.
        padding 
            Represents the 'Padding Value' setting from the Cluster Manager.
            Note that the variable should be assigned a collection of elements that obey the validation specified.
        dir 
            Represents the 'Padding Direction' setting from the Cluster Manager.
            Note that the variable should be assigned a collection of elements that obey the validation specified.
        scan_resolution 
            Represents the 'Upscaled Resolution' setting from the Grid Search Pattern.
        selected 
            Represents the currently selected pattern from the Grid Search Pattern. 
            The only value it accepts is an emulated pattern from a relevant {self.L_NAME} function.
        scan_mode 
            Represents the 'Merlin Scan Mode' setting from the Grid Search Scan.
        session 
            Represents the 'Session' setting from the Grid Search Scan.
        sample 
            Represents the 'Sample' setting from the Grid Search Scan.
        scan_size 
            Represents the 'Scan Size' setting from the Grid Search Scan.
        exposure_time 
            Represents the 'Dwell Value' setting from the Grid Search Scan.
        bit_depth 
            Represents the 'Bit Depth' setting from the Grid Search Scan.
        save_path 
            Represents the 'Save Path' setting from the Grid Search Scan.
        checkpoints 
            Represents the 'Additional Files' setting from the Grid Search Scan.
        focus_change 
            Represents the 'Unit Change' setting from the Focus Correction.
        num_images 
            Represents the 'Images' setting from the Focus Correction.
        focus_scans 
            Represents the 'Scan Amount' setting from the Focus Correction.
        min_emission 
            Represents the 'Emission Value' setting from the Emission Correction.
        drift_scans 
            Represents the 'Scan Amount' setting from the Drift Correction.
        windowing 
            Represents the 'Windowing Types' setting from the Drift Correction.
        window_order 
            Represents the 'Windowing Order' setting from the Focus Correction.
            This should be a collection of 3 strings - each string should be 'Hanning', 'Sobel', or 'Median'.
        corner {images.AABBCorner.__doc__}
        underflow {utils.UnderflowHandler.__doc__}
        overflow {utils.OverflowHandler.__doc__}
        random {utils.RandomTypes.__doc__}
        kernel_shape {images.MorphologicalShape.__doc__}
        number_match {utils.Match.__doc__}
        axis {utils.Extreme.__doc__}
        staging {utils.Stages.__doc__}
        windows {utils.Windowing.__doc__}
        """
        return s


class ScriptInterpreter(language.execution.Interpreter, core.QObject,
                        metaclass=utils.make_meta(core.QObject, language.execution.Interpreter)):

    def __init__(self, variable_handler: typing.Callable[[str, object], None], variables: _dict[str, object],
                 keyword_handlers: _dict[language.grammar.KeywordType, typing.Callable[[], None]],
                 **functions: language.NativeFunction):
        core.QObject.__init__(self)
        language.execution.Interpreter.__init__(self)
        for k, v in functions.items():
            self._globals.set_at(k, v, create=True)
        for k, v in variables.items():
            self._globals.set_at(k, v, create=True)
        self._keys = keyword_handlers
        self._var = variable_handler
        self._failed: typing.Optional[Exception] = None

    def fail(self, exc: Exception):
        self._failed = exc

    def execute(self, *stream: language.grammar.Node):
        self._failed = None
        try:
            for node in stream:
                if self._token is not None:
                    pos = self.position
                    yield int(pos[:pos.find(":")])
                self.evaluate(node)
                if self._failed:
                    raise self._failed
        except Exception as err:
            if isinstance(err, language.InterpretationError):
                raise
            raise language.InterpretationError(self._token, str(err))

    def visit_keyword_stmt(self, node: language.grammar.KeywordStmt) -> None:
        self._keys[node.keyword_type]()

    def visit_set_expr(self, node: language.grammar.SetExpr) -> object:
        obj = super().visit_set_expr(node)
        self._var(node.sink.src.src, obj)
        return obj
