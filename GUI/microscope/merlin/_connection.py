import contextlib
import enum
import socket
import typing

from ._enums import *
from modular_qt import validators
from modular_qt.cv_oop import CMode

trigger = validators.Pipeline.enum(Trigger)
out_trigger = validators.Pipeline.enum(OutTrigger)


def make_stem_validator(validator: validators.Validator) -> validators.Pipeline:
    """
    Internal method to make a STEM validator, as these take first a STEMDetector and then validated data.

    :param validator: The validation for the last (second) element of the tuple.
    :return: The validation pipeline.
    """
    return validators.Pipeline(
        validators.Step(validators.ValueValidator(2), validators.SizeTranslator(), temporary_translation=True),
        validators.Step(validators.Pipeline.enum(STEMDetector), validators.PositionTranslator(0)),
        validators.Step(validator, validators.PositionTranslator(1))
    )


@contextlib.contextmanager
def connect(hostname: str, channel: ConnectionChannel) -> typing.ContextManager["Merlin"]:
    """
    A context manager to connect to the Merlin software.

    This is the safest way to connect to merlin as it guarantees closure of the connection.

    Example::

        with connect("localhost",ConnectionChannel.CMD) as merlin:
            merlin[Variable.COLOUR] = CMode.GREY
            merlin.exec(Command.START)

    :param hostname: The host name to connect to.
    :param channel: The type of connection.
    :return: The merlin connection itself.
    """
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.connect((socket.gethostbyname(hostname), channel.value))
    try:
        yield Merlin(connection)
    finally:
        connection.close()


class Merlin:
    """
    An interface to the merlin software using TCP protocol.

    Has a connection to the merlin software and will send commands via the 'exec' method, change data using index
    notation ([] = ), as well as retrieve data using the index notation ([]).

    As a command may be unsuccessful, the status code and its associated command can be retrieved at any point.

    :var socket.socket _connectio: The software link.
    :var tuple[Variable | Command, CommandType, MerlinStatus] | None _last: The last command and its status.
    """

    @property
    def status_code(self) -> MerlinStatus:
        """
        Public access to the status code of the last command.

        :return: The MerlinStatus representing the success of the last tried command.
        :raises ValueError: If no command has been sent.
        """
        if self._last is None:
            raise ValueError("No command sent")
        return self._last[-1]

    @property
    def command(self) -> tuple[typing.Union[Variable, Command], CommandType]:
        """
        Public access to the last command.

        :return: The Variable (or Command) and CommandType that represents the last tried command.
        :raises ValueError: If no command has been sent.
        """
        if self._last is None:
            raise ValueError("No command sent")
        return self._last[0], self._last[1]

    def __init__(self, connection: socket.socket):
        self._connection = connection
        self._last: typing.Optional[tuple[typing.Union[Variable, Command], CommandType, MerlinStatus]] = None

    def __getitem__(self, item: Variable) -> typing.Optional[typing.Any]:
        """
        Retrieve a variable from the MERLIN connection.

        :param item: The variable to retrieve.
        :return: The value of the variable. It will be None if the command wasn't successful
        """
        # <editor-fold desc="Handle Edge Cases">
        if item == Variable.STARTING_TRIGGER_MODIFIER:
            self._send(f",GET,{Variable.STARTING_TRIGGER.value}")
            trigger_type, code = self._recv()
            if code != MerlinStatus.UNDERSTOOD:
                self._last = (item, CommandType.GET, code)
                return
            trigger_type = int(trigger_type)
            answer = TriggerModifier(int(trigger_type > 5) + 1)
            self._last = (item, CommandType.GET, MerlinStatus.UNDERSTOOD)
            return answer if code == MerlinStatus.UNDERSTOOD else None
        elif item == Variable.PATH:
            cmds = item.value.split("/")
            answers = []
            for cmd in cmds:
                self._send(f",GET,{cmd}")
                value, code = self._recv()
                answers.append(value)
                if code != MerlinStatus.UNDERSTOOD:
                    self._last = (item, CommandType.GET, code)
                    return
            overall = "/".join(answers)
            self._last = (item, CommandType.GET, MerlinStatus.UNDERSTOOD)
            return overall
        elif item == Variable.ENABLED_DETECTORS:
            answers = []
            for cmd in (1, 2):
                self._send(f",GET,{item.value.replace('<>', cmd)}")
                value, code = self._recv()
                answers.append(value)
                if code != MerlinStatus.UNDERSTOOD:
                    self._last = (item, CommandType.GET, code)
                    return
            answer = STEMDetector.ONE & STEMDetector.TWO  # mutually exclusive
            if answers[0]:
                answer |= STEMDetector.ONE
            if answers[1]:
                answer |= STEMDetector.TWO
            self._last = (item, CommandType.GET, MerlinStatus.UNDERSTOOD)
            return answer
        elif item in {Variable.DETECTOR_TYPE, Variable.DETECTOR_MIDDLE_H, Variable.DETECTOR_MIDDLE_V,
                      Variable.DETECTOR_OUTER_R, Variable.DETECTOR_INNER_R}:
            def _modify(v: str):
                v = int(v)
                if item == Variable.DETECTOR_TYPE:
                    return DetectorType(v)
                return v

            def _replace(num: int):
                self._send(f",GET,{item.value.replace('<>', num)}")
                r_value, r_code = self._recv()
                if r_code != MerlinStatus.UNDERSTOOD:
                    self._last = (item, CommandType.GET, r_code)
                    return
                answers.append(_modify(r_value))

            enabled = self[Variable.ENABLED_DETECTORS]
            if enabled is None:
                self._last = (item, CommandType.GET, self.status_code)
                return
            answers: list = []
            if enabled & STEMDetector.ONE:
                _replace(1)
            if enabled & STEMDetector.TWO:
                _replace(2)
            self._last = (item, CommandType.GET, MerlinStatus.UNDERSTOOD)
            if len(answers) == 2:
                return enabled, tuple(answers)
            return enabled, answers[0]
        elif item == Variable.CHIP_TEMP:
            self._send(f",CMD,READCHIPTEMPS")
            _, code = self._recv()
            if code != MerlinStatus.UNDERSTOOD:
                self._last = (item, CommandType.GET, code)
                return
        # </editor-fold>
        self._send(f",GET,{item.value}")
        # return
        value, code = self._recv()
        self._last = (item, CommandType.GET, code)
        if code != MerlinStatus.UNDERSTOOD:
            return
        # <editor-fold desc="Handle Conversion">
        if item == Variable.COLOUR:
            value = CMode(int(value) + 1)
        elif item == Variable.GAIN:
            value = GainType(int(value))
        elif item == Variable.WRITE_BUFFER:
            value = value == "0"
        elif item == Variable.COUNTERS:
            value = Counters(int(value) + 1)
        elif item == Variable.FILL_MODE:
            value = GapFill(value)
        elif item in {Variable.STARTING_TRIGGER, Variable.ENDING_TRIGGER}:
            value = int(value)
            value = Trigger(value - (5 * int(value > 5)))
        elif item in {Variable.OUT_TRIGGER_TTL, Variable.OUT_TRIGGER_LVDS}:
            value = OutTrigger(int(value))
        elif item == Variable.CHIP_MODE:
            value = Chips(int(value))
        elif item == Variable.TRIGGER_MODE:
            value = STEMTrigger(int(value))
        elif item == Variable.STATUS:
            value = DetectorStatus(int(value))
        elif item in {Variable.THRESHOLD_0, Variable.THRESHOLD_1, Variable.THRESHOLD_2, Variable.THRESHOLD_3,
                      Variable.THRESHOLD_4, Variable.THRESHOLD_5, Variable.THRESHOLD_6, Variable.THRESHOLD_7,
                      Variable.THRESHOLD_START, Variable.THRESHOLD_STOP, Variable.THRESHOLD_STEP, Variable.ENERGY}:
            value = float(value)
        elif item in {Variable.FLAT_FIELD_FILE, Variable.DAC_FILE, Variable.INPUT_CONFIG, Variable.OUTPUT_CONFIG}:
            pass  # no fall through for else branch, but no external processing
        elif item in {Variable.SUM, Variable.VERBOSE, Variable.MASK, Variable.TTL_INVERSION, Variable.LVDS_INVERSION,
                      Variable.USE_DELAY, Variable.USE_TTL_OUT, Variable.USE_LVDS_OUT, Variable.TRACK_DAC,
                      Variable.DO_SAVE, Variable.SAVE_ALL_TO_ONE, Variable.TIMESTAMP, Variable.USE_TTL_IN,
                      Variable.USE_LVDS_IN}:
            value = value == "1"
        else:
            invert = False
            if value[0] == "-":
                invert = True
                value = value[1:]
            value = int(value)
            if invert:
                value = -value
        # </editor-fold>

        return value

    def __setitem__(self, key: Variable, value: typing.Any):
        """
        Change a variable from the MERLIN connection.

        :param key: The variable to update.
        :param value: The new value of the variable.
        :raises AttributeError: If the variable can't be set.
        """
        self._last = (key, CommandType.SET, MerlinStatus.VALUE_OUT_OF_RANGE)
        validation = self.validation()
        if (validator := validation.get(key)) is None:
            raise AttributeError(f"Cannot set attribute '{key.name}'")
        validator.validate(value)
        if isinstance(value, enum.Enum):
            value = value.value
        elif isinstance(value, bool):
            value = int(value)
        # <editor-fold desc="Handle Edge Cases">
        if key == Variable.COLOUR:
            value -= 1
        elif key == Variable.WRITE_BUFFER:
            value = int(not value)
        elif key == Variable.COUNTERS:
            value -= 1
        elif key == Variable.STARTING_TRIGGER:
            value += (self[Variable.STARTING_TRIGGER_MODIFIER].value - 1) * 5
        elif key == Variable.STARTING_TRIGGER_MODIFIER:
            return
        elif key == Variable.PATH:
            *root, node = value.split("/")
            root_path = "/".join(root)
            self._send(f",SET,FILEDIRECTORY,{root_path}")
            self._send(f",SET,FILENAME,{node}")
            return
        elif key == Variable.TRIGGER_COUNT:
            if self[Variable.TRIGGER_MODE] != STEMTrigger.CUSTOM:
                raise ValueError(f"Cannot send trigger count when not using custom trigger mode")
        elif key == Variable.ENABLED_DETECTORS:
            self._send(f",SET,{key.value.replace('<>', 1)},{int(bool(STEMDetector(value) & STEMDetector.ONE))}")
            self._send(f",SET,{key.value.replace('<>', 2)},{int(bool(STEMDetector(value) & STEMDetector.TWO))}")
            return
        elif key in {Variable.DETECTOR_TYPE, Variable.DETECTOR_MIDDLE_H, Variable.DETECTOR_MIDDLE_V,
                     Variable.DETECTOR_OUTER_R, Variable.DETECTOR_INNER_R}:
            detector, value = value
            if detector & STEMDetector.ONE:
                self._send(f",SET,{key.value.replace('<>', 1)},{value}")
            if detector & STEMDetector.TWO:
                self._send(f",SET,{key.value.replace('<>', 2)},{value}")
            return
        # </editor-fold>
        self._send(f",SET,{key.value},{value}")
        # return
        _, code = self._recv()
        self._last = (key, CommandType.SET, code)
        if key == Variable.FLAT_FIELD_FILE:
            self._send(f",SET,FLATFIELDCORRECTION,{int(bool(value))}")

    def exec(self, cmd: Command):
        """
        Tell the merlin software to execute a command.

        :param cmd: The command to execute.
        """
        self._send(f",CMD,{cmd.value}")
        _, code = self._recv()
        self._last = (cmd, CommandType.CMD, code)

    def _send(self, command: str):
        length = len(command)
        message = f"MPX,{length:0<10}{command}"
        print(f"Sending {message}")
        self._connection.send(message.encode("UTF-8"))

    def _recv(self) -> tuple[str, MerlinStatus]:
        message = self._connection.recv(1024).decode("UTF-8", "ignore").split(",")
        print(f"Received {message} - splitting into {message[-2]} and {MerlinStatus(int(message[-1]))}")
        return message[-2], MerlinStatus(int(message[-1]))

    @staticmethod
    def validation() -> dict[Variable, validators.Pipeline]:  # PTS: Prior To Sending, DNS: Do Not Send
        """
        Access the validation pipelines for each modifiable variable.

        :return: A mapping of variable to pipeline.
        """
        return {
            # <editor-fold desc="Acquisition Settings">
            Variable.COLOUR: validators.Pipeline.enum(CMode),  # -1 PTS
            Variable.SUM: validators.xmpls.any_bool,
            Variable.GAIN: validators.Pipeline.enum(GainType),
            Variable.CONTINUOUS: validators.xmpls.any_bool,
            Variable.WRITE_BUFFER: validators.xmpls.any_bool,  # invert PTS
            Variable.COUNTERS: validators.Pipeline.enum(Counters),  # -1 PTS
            Variable.THRESHOLD_0: validators.xmpls.threshold,
            Variable.THRESHOLD_1: validators.xmpls.threshold,
            Variable.THRESHOLD_2: validators.xmpls.threshold,
            Variable.THRESHOLD_3: validators.xmpls.threshold,
            Variable.THRESHOLD_4: validators.xmpls.threshold,
            Variable.THRESHOLD_5: validators.xmpls.threshold,
            Variable.THRESHOLD_6: validators.xmpls.threshold,
            Variable.THRESHOLD_7: validators.xmpls.threshold,
            Variable.ENERGY: validators.xmpls.threshold,
            Variable.BIT_DEPTH: validators.xmpls.bit_depth,
            Variable.FILL_MODE: validators.Pipeline.enum(GapFill),
            Variable.FLAT_FIELD_FILE: validators.xmpls.merlin_path,  # also set correction dependent on truthiness
            Variable.VERBOSE: validators.xmpls.any_bool,
            Variable.MASK: validators.xmpls.any_bool,
            Variable.FRAME_AMOUNT: validators.xmpls.long_int,
            Variable.FRAME_TIME: validators.xmpls.any_int,
            # </editor-fold>
            # <editor-fold desc="Trigger Settings">
            Variable.STARTING_TRIGGER: trigger,  # + (modifier - 1) PTS
            Variable.ENDING_TRIGGER: trigger + validators.Pipeline(validators.Step(
                validators.RangeValidator(0, 4),
                validators.PropertyTranslator("value"))
            ),
            Variable.STARTING_TRIGGER_MODIFIER: validators.Pipeline.enum(TriggerModifier),  # DNS
            Variable.FRAME_AMOUNT_PER_PULSE: validators.xmpls.long_int,
            Variable.OUT_TRIGGER_TTL: out_trigger,
            Variable.OUT_TRIGGER_LVDS: out_trigger + validators.Pipeline(validators.Step(
                validators.RangeValidator(0, 9),
                validators.PropertyTranslator("value"))
            ),
            Variable.TTL_INVERSION: validators.xmpls.any_bool,
            Variable.LVDS_INVERSION: validators.xmpls.any_bool,
            Variable.TTL_DELAY: validators.xmpls.delay,
            Variable.LVDS_DELAY: validators.xmpls.delay,
            Variable.USE_DELAY: validators.xmpls.any_bool,
            Variable.USE_TTL_OUT: validators.xmpls.any_bool,
            Variable.USE_LVDS_OUT: validators.xmpls.any_bool,
            # </editor-fold>
            # <editor-fold desc="Set-Up">
            Variable.DAC_FILE: validators.xmpls.merlin_path,
            Variable.DAC_VALUES: validators.xmpls.dac,
            Variable.INPUT_CONFIG: validators.xmpls.merlin_path,
            Variable.OUTPUT_CONFIG: validators.xmpls.merlin_path,
            Variable.TRIM_MODE: validators.Pipeline.bound_int(validators.RangeValidator(0, 1)),
            Variable.TRIM_VALUE: validators.Pipeline.bound_int(validators.RangeValidator(-31, 31)),
            Variable.CHIP_MODE: validators.Pipeline.enum(Chips),
            Variable.TRACK_DAC: validators.xmpls.any_bool,
            # </editor-fold>
            # <editor-fold desc="Threshold Scan">
            Variable.USE_THRESHOLD: validators.Pipeline.bound_int(validators.RangeValidator(0, 7)),
            Variable.THRESHOLD_START: validators.xmpls.threshold,
            Variable.THRESHOLD_STOP: validators.xmpls.threshold,
            Variable.THRESHOLD_STEP: validators.xmpls.threshold,
            Variable.THRESHOLD_STEPS: validators.xmpls.dac,
            # </editor-fold>
            # <editor-fold desc="DAC Scan">
            Variable.USE_DAC: validators.Pipeline.bound_int(validators.RangeValidator(0, 27)),
            Variable.DAC_START: validators.xmpls.dac,
            Variable.DAC_STOP: validators.xmpls.dac,
            Variable.DAC_STEP: validators.Pipeline.bound_int(validators.RangeValidator(-255, 255)),
            # </editor-fold>
            # <editor-fold desc="File Control">
            Variable.PATH: validators.xmpls.merlin_path,  # split into root and node PTS
            Variable.DO_SAVE: validators.xmpls.any_bool,
            Variable.SAVE_ALL_TO_ONE: validators.xmpls.any_bool,
            Variable.IMAGES_PER_FILE: validators.xmpls.any_int,
            Variable.TIMESTAMP: validators.xmpls.any_bool,
            # </editor-fold>
            # <editor-fold desc="STEM Control">
            Variable.HORIZONTAL_POINTS: validators.xmpls.stem_limit,
            Variable.VERTICAL_POINTS: validators.xmpls.stem_limit,
            Variable.TRIGGER_MODE: validators.Pipeline.enum(STEMTrigger),
            Variable.TRIGGER_COUNT: validators.xmpls.any_int,  # only accept if in custom mode
            Variable.LINE_SKIP: validators.xmpls.stem_limit,
            Variable.START_SKIP: validators.xmpls.stem_limit,
            Variable.END_SKIP: validators.xmpls.stem_limit,
            Variable.ENABLED_DETECTORS: validators.Pipeline.enum(STEMDetector),  # split into two commands
            Variable.DETECTOR_TYPE: make_stem_validator(validators.Pipeline.enum(DetectorType)),
            Variable.DETECTOR_MIDDLE_H: make_stem_validator(validators.RangeValidator(*validators.xmpls.dac.bounds)),
            Variable.DETECTOR_MIDDLE_V: make_stem_validator(validators.RangeValidator(*validators.xmpls.dac.bounds)),
            Variable.DETECTOR_OUTER_R: make_stem_validator(validators.RangeValidator(*validators.xmpls.dac.bounds)),
            Variable.DETECTOR_INNER_R: make_stem_validator(validators.RangeValidator(*validators.xmpls.dac.bounds)),
            # </editor-fold>
        }
