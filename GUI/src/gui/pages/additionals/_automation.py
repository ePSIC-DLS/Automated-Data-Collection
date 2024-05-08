import typing

from ... import utils
from ..._base import Page, widgets
from .... import images, language as language


class Scripts(Page):
    L_NAME = "PAL"

    def __init__(self, compilation: typing.Callable[[], str],
                 variable_handler: typing.Callable[[str, language.vals.Value], None],
                 keyword_handler: typing.Callable[[int], None], **variables: language.vals.Value):
        super().__init__()

        def _output(content: str):
            self._output.append(content)

        def _ready():
            self._output.clear()
            self._progress.setValue(0)
            self._progress.setMaximum(0)
            with open(self._path) as file:
                program = file.read()
            self._interpreter.run(program)

        self._interpreter = language.Interpreter(variable_handler, keyword_handler, _output, **variables)
        path = r"./assets"
        # path=utils.FileDialog.BASE
        self._prompt = utils.FilePrompt("GUIAS", block=False,
                                        path=path)
        self._output = widgets.QTextEdit()
        self._progress = widgets.QProgressBar()
        self._progress.setRange(0, 0)
        self._output.setFontPointSize(12)
        self._output.setReadOnly(True)
        self._layout.addWidget(self._output, 0, 0)
        self._layout.addWidget(self._prompt, 0, 1)
        self.setLayout(self._layout)
        self._prompt.dialog().openFile.connect(self._run_file)
        self._prompt.dialog().saveFile.connect(self._compile(compilation))
        self._prompt.dialog().finished.connect(_ready)
        self._path = ""

    def interpreter(self) -> language.Interpreter:
        return self._interpreter

    def _run_file(self, path: str):
        self._path = path

    def _compile(self, compilation: typing.Callable[[], str]) -> typing.Callable[[str], None]:
        def _inner(path: str):
            self._run_file(path)
            with open(path, "w") as script:
                script.write(compilation())

        return _inner

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
        Void keyword
            "void"
            This keyword is an expression representing a null value.
        
        Var keyword
            "var <NAME> '=' <VALUE>"
            This keyword declares the variable <NAME> with initial variable <VALUE>;
            <VALUE> can be any valid {self.L_NAME} expression.
        Func keyword
            "func <NAME> '('[<NAME> (',' <NAME>)*]')' <BLOCK>"
            This keyword declares a function called <NAME>, which accepts any number of parameters;
            (parameters are specified by a comma-separated list of names).
            
            {self.L_NAME} does not support default values for parameters, and assumes all parameters are positional.
            
            As assignment is a separate expression; 
            there is no 'global' or 'nonlocal' keyword for outer scope assignment.
        Iter keyword
            "iter <NAME> '('[<NAME> (',' <NAME>)*]')' <BLOCK>"
            This keyword creates a generator called <NAME>, which accepts any number of parameters;
            (parameters are specified by a comma-separated list of names).
            
            Generators differ from functions in that when a return statement is encountered; 
            it actually yields the value and can be resumed from that point.
            Furthermore, when called they are primed, and <BLOCK> is not run.
        Namespace keyword
            "namespace <NAME> '{{' <NAME> (',' <NAME>)* '}}'
            This keyword creates an enumeration with the members described between the braces.
        For keyword
            "for '(' <Var> ',' <VALUE> ',' <VALUE> ')' <BLOCK>"
            This keyword is used like a C-style for loop. The middle <VALUE> is usually a condition; 
            when this evaluates to true, the loop exits;
            The last <VALUE> is usually an assignment expression to mutate the variable (defined by <Var>)
        Foreach keyword
            "foreach '(' <Var> ')' <BLOCK>
            This keyword is used like a python-style for loop. The value of <Var> should equate to a primed generator.
            This then sets the <Var> to be the yielded value from the generator.
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
                -3 = -3, -8 = -8
            '!' which performs unary inversion on the operand. Valid for boolean and collection operands.
                !true = false, !false = true
                ![1, 2, 3] = [3, 2, 1], !["a", true] = [true, "a"]
            '?' which prints (and returns) the result. This is a postfix expression.
                1? = 1, (!((7 ^ 3) - (5 ^ 3) == (20000 ^ -1)))? = false
            
        
        The binary operators are:
            '^' which performs place-shifting on the operands. Only valid for numerical operands.
                7 ^ 3 = 7000, 70 ^ -2 = 0.7
            '+' which performs addition on operands. Valid for numerical and string operands.
                7 + 3 = 10, -2 + 70 = 68
                "a" + "b" = "ab", "aa" + "c" = "aac"
            '-' which performs subtraction on operands. Only valid for numerical operands.
                3 - 7 = -4, 70 - -2 = 72
            '|' which performs bitwise or on operands. Valid for numerical and collection operands.
                3 | 7 = 7, -2 | 70 = -2
                [1, 2] | [true, false] = [1, 2, true, false], ["a"] | ["b"] = ["a", "b"]
        
        The comparison operators are:
            '==' for equality
            '!=' for inequality
            '<' for less-than
            '>' for greater-than
            '<=' for less-than-or-equal
            '>=' for greater-than-or-equal
            
        '.' is used to access properties from enumerations. The right hand side is always an identifier.
        '(' is used to call functions and generators.
        
        Unlike python, assignment is a valid expression, and can be used anywhere an expression is expected."""
        return s

    def standard_library(self) -> str:
        s = f"""Functions:
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
            "Raster(skip, start, orientation, coverage)"
            Emulates a raster pattern using the specified arguments. 
            Note that the parameter names match up with the pattern configuration.
        Snake:
            "Snake(skip, start, orientation, coverage)"
            Emulates a snake pattern using the specified arguments. 
            Note that the parameter names match up with the pattern configuration.
        Spiral:
            "Spiral(skip, start, orientation, coverage)"
            Emulates a spiral pattern using the specified arguments. 
            Note that the parameter names match up with the pattern configuration.
        Grid:
            "Grid(gap, shift, order, coverage)"
            Emulates a grid pattern using the specified arguments. 
            Note that the parameter names match up with the pattern configuration.
        Random:
            "Random(r_type, n, coverage, scale, loc, lam, low, high)"
            Emulates a random pattern using the specified arguments. 
            Note that the parameter names match up with the pattern configuration.
        correct_for:
            "correct_for(correction)"
            Runs the specified correction. The correction should use one of the correction keywords.
        
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
        dwell_time
            Represents the exposure time in seconds for the microscope.
        flyback
            Represents the additional time to dwell on each pixel in seconds. Most important in patterns.
        Corner {images.AABBCorner.__doc__}
        Randoms {utils.RandomTypes.__doc__}
        KernelShape {images.MorphologicalShape.__doc__}
        NumberMatch {utils.Match.__doc__}
        Axis {utils.Extreme.__doc__}
        Staging {utils.Stages.__doc__}
        
        """
        return s

# class ScriptInterpreter(language.execution.Interpreter, core.QObject,
#                         metaclass=utils.make_meta(core.QObject, language.execution.Interpreter)):
#
#     def __init__(self, variable_handler: typing.Callable[[str, object], None], variables: _dict[str, object],
#                  keyword_handlers: _dict[language.grammar.KeywordType, typing.Callable[[], None]],
#                  **functions: language.NativeFunction):
#         core.QObject.__init__(self)
#         language.execution.Interpreter.__init__(self)
#         for k, v in functions.items():
#             self._globals.set_at(k, v, create=True)
#         for k, v in variables.items():
#             self._globals.set_at(k, v, create=True)
#         self._keys = keyword_handlers
#         self._var = variable_handler
#         self._failed: typing.Optional[Exception] = None
#
#     def fail(self, exc: Exception):
#         self._failed = exc
#
#     def execute(self, *stream: language.grammar.Node):
#         self._failed = None
#         try:
#             for node in stream:
#                 if self._token is not None:
#                     pos = self.position
#                     yield int(pos[:pos.find(":")])
#                 self.evaluate(node)
#                 if self._failed:
#                     raise self._failed
#         except Exception as err:
#             if isinstance(err, language.InterpretationError):
#                 raise
#             raise language.InterpretationError(self._token, str(err))
#
#     def visit_keyword_stmt(self, node: language.grammar.KeywordStmt) -> None:
#         self._keys[node.keyword_type]()
#
#     def visit_set_expr(self, node: language.grammar.SetExpr) -> object:
#         obj = super().visit_set_expr(node)
#         self._var(node.sink.src.src, obj)
#         return obj
