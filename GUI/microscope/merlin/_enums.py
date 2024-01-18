import enum as _enum


class ConnectionChannel(_enum.Enum):
    """
    Enumeration to represent different connection types to use to connect to merlin.

    The value of each member is the communication port.
    :cvar CMD:
    :cvar DATA:
    """
    CMD = 6341
    DATA = 6342


class MerlinStatus(_enum.Enum):
    """
    Enumeration to represent the different status codes for merlin communication.

    :cvar UNDERSTOOD:
    :cvar BUSY:
    :cvar UNKNOWN_COMMAND:
    :cvar VALUE_OUT_OF_RANGE:
    """
    UNDERSTOOD = 0
    BUSY = 1
    UNKNOWN_COMMAND = 2
    VALUE_OUT_OF_RANGE = 3


class Command(_enum.Enum):
    """
    Enumeration to represent the different *executable* commands that merlin can perform.

    :cvar START: Start an acquisition for internal triggers. For external triggers, wait for trigger to fire.
    :cvar STOP: Stop any running acquisition, but finish sending any buffer.
    :cvar ABORT: Stop any running acquisition and clear the buffers.
    :cvar START_SOFT_TRIGGER: Fire any soft triggers configured.
    :cvar THRESHOLD: Perform a threshold scan using the configured threshold settings.
    :cvar DAC: Perform a DAC scan using the configured DAC settings.
    :cvar SHUTDOWN: Remove power to chips.
    :cvar RESTART: Restore power to chips. Command will also perform limited re-initialisation.
    :cvar EQUALISE_NOISE: Performs a noise equalisation using default values.
    :cvar RESET: Restores default values to all variables.
    :cvar CLEAR_ERRORS: Clears the error flag. Allows for running further commands.
    :cvar SINGLE_STEM: Begin a single 2D STEM scan.
    :cvar CONTINUOUS_STEM: Begin a continuous 2D STEM scan.
    """
    START = "STARTAQUISITION"
    STOP = "STOPAQUISITION"
    ABORT = "ABORT"
    START_SOFT_TRIGGER = "SOFTTRIGGER"
    THRESHOLD = "THSCAN"
    DAC = "DACSCAN"
    SHUTDOWN = "STANDBY"
    RESTART = "RESTART"
    EQUALISE_NOISE = "NOISEEQUALISATION"
    RESET = "RESET"
    CLEAR_ERRORS = "CLEARERROR"
    SINGLE_STEM = "SCANSTARTRECORD"
    CONTINUOUS_STEM = "SCANSTARTSEARCH"


class CommandType(_enum.Enum):
    """
    Enumeration to represent different permissions for a variable.

    :cvar GET:
    :cvar SET:
    :cvar CMD:
    """
    GET = _enum.auto()
    SET = _enum.auto()
    CMD = _enum.auto()


class Variable(_enum.Enum):
    """
    Enumeration of all different variables controlled by merlin.

    :cvar COLOUR: Change between monochrome and colour mode.
    :cvar SUM: Whether to enable charge summing.
    :cvar GAIN: The gain level.
    :cvar CONTINUOUS: Whether to continuously read and write data.
    :cvar WRITE_BUFFER: Whether to write to the image buffer.
    :cvar COUNTERS: The counters that are enabled.
    :cvar THRESHOLD_0: The zeroth preset threshold in keV.
    :cvar THRESHOLD_1: The first preset threshold in keV.
    :cvar THRESHOLD_2: The second preset threshold in keV.
    :cvar THRESHOLD_3: The third preset threshold in keV.
    :cvar THRESHOLD_4: The fourth preset threshold in keV.
    :cvar THRESHOLD_5: The fifth preset threshold in keV.
    :cvar THRESHOLD_6: The sixth preset threshold in keV.
    :cvar THRESHOLD_7: The seventh preset threshold in keV.
    :cvar ENERGY: The operating energy in keV.
    :cvar BIT_DEPTH: The bit depth of the scan. Note that it is two-channel, and so 24-bit isn't allowed.
    :cvar FILL_MODE: The gap-filling mode of the scan.
    :cvar FLAT_FIELD_FILE: The file path to the flat field correction. If blank, correction is disabled.
    :cvar VERBOSE: Whether the system saves a text header file of set-up and status information.
    :cvar MASK: Whether to apply a pixel mask at image processing stage.
    :cvar FRAME_AMOUNT: The number of frames to acquire from the scan. Zero runs until a STOP command.
    :cvar FRAME_TIME: The milliseconds over which a frame is acquired.
    :cvar STARTING_TRIGGER: The trigger to use to denote a start.
    :cvar ENDING_TRIGGER: The trigger to use to denote a stop.
    :cvar STARTING_TRIGGER_MODIFIER: Allows using multi triggers for the starting trigger.
    :cvar FRAME_AMOUNT_PER_PULSE: The number of frames to acquire per pulse of trigger.
    :cvar OUT_TRIGGER_TTL: The type of "out trigger" to use for the TTL trigger.
    :cvar OUT_TRIGGER_LVDS: The type of "out trigger" to use for the LVDS trigger.
    :cvar TTL_INVERSION: Whether to invert the TTL trigger.
    :cvar LVDS_INVERSION: Whether to invert the LVDS trigger.
    :cvar TTL_DELAY: The amount of delay to use for the TTL trigger.
    :cvar LVDS_DELAY: The amount of delay to use for the LVDS trigger.
    :cvar USE_DELAY: Whether to use the specified delay.
    :cvar USE_TTL_OUT: Whether to use the specified TTL trigger.
    :cvar USE_LVDS_OUT: Whether to use the specified LVDS trigger.
    :cvar USE_TTL_IN: Whether to use the specified TTL trigger for input (read-only).
    :cvar USE_LVDS_IN: Whether to use the specified LVDS trigger for input (read-only).
    :cvar DAC_FILE: Filepath to load the DAC values from.
    :cvar DAC_VALUES: Hardcoded DAC values.
    :cvar INPUT_CONFIG: The filepath to load pixel configuration from.
    :cvar OUTPUT_CONFIG: The filepath to save pixel configuration to.
    :cvar TRIM_MODE: Which trim to use.
    :cvar TRIM_VALUE: The adjustment to use for the trim.
    :cvar CHIP_MODE: Which chips to use for processing.
    :cvar TRACK_DAC: Whether to enable active tracking of DAC.
    :cvar USE_THRESHOLD: The threshold preset to use.
    :cvar THRESHOLD_START: The starting energy of the scan.
    :cvar THRESHOLD_STOP: The ending energy of the scan.
    :cvar THRESHOLD_STEP: The change in energy of the scan.
    :cvar THRESHOLD_STEPS: The discrete number of steps for the scan.
    :cvar USE_DAC: The DAC value to use.
    :cvar DAC_START: The starting energy of the scan.
    :cvar DAC_STOP: The ending energy of the scan.
    :cvar DAC_STEP: The change in energy of the scan.
    :cvar PATH: The filepath to save data to.
    :cvar DO_SAVE: Whether to enable saving the data.
    :cvar SAVE_ALL_TO_ONE: Whether to save all frames to a single file.
    :cvar IMAGES_PER_FILE: The number of images to save into a single file.
    :cvar TIMESTAMP: Whether to create a new time-stamped directory for each acquisition.
    :cvar HORIZONTAL_POINTS: The number of scan points in the x-direction.
    :cvar VERTICAL_POINTS: The number of scan points in the y-direction.
    :cvar TRIGGER_MODE: The trigger mode to use for STEM acquisition.
    :cvar TRIGGER_COUNT: The number of frames per trigger for custom STEM trigger mode (raises error mode isn't CUSTOM).
    :cvar LINE_SKIP: The number of frames to skip at the end of each line.
    :cvar START_SKIP: The number of frames to skip at the start of each scan.
    :cvar END_SKIP: The number of frames to skip at the end of each scan.
    :cvar ENABLED_DETECTORS: The STEM detectors that are enabled.
    :cvar DETECTOR_TYPE: The type of the enabled STEM detector(s) (can be different per detector).
    :cvar DETECTOR_MIDDLE_H: The horizontal centre of the enabled STEM detector(s) (can be different per detector).
    :cvar DETECTOR_MIDDLE_V: The vertical centre of the enabled STEM detector(s) (can be different per detector).
    :cvar DETECTOR_OUTER_R: The outer radius of the enabled STEM detector(s) (can be different per detector).
    :cvar DETECTOR_INNER_R: The inner radius of the enabled STEM detector(s) (can be different per detector).
    :cvar STATUS: The detector status.
    :cvar TEMP: The temperature of the chipboard.
    :cvar CHIP_TEMP: The temperature of the selected chips.
    """
    # <editor-fold desc="Acquisition Settings">
    COLOUR = "COLOURMODE"
    SUM = "CHARGESUMMING"
    GAIN = "GAIN"
    CONTINUOUS = "CONTINUOUSRW"
    WRITE_BUFFER = "RUNHEADLESS"
    COUNTERS = "ENABLECOUNTER1"
    THRESHOLD_0 = "THRESHOLD0"
    THRESHOLD_1 = "THRESHOLD1"
    THRESHOLD_2 = "THRESHOLD2"
    THRESHOLD_3 = "THRESHOLD3"
    THRESHOLD_4 = "THRESHOLD4"
    THRESHOLD_5 = "THRESHOLD5"
    THRESHOLD_6 = "THRESHOLD6"
    THRESHOLD_7 = "THRESHOLD7"
    ENERGY = "OPERATINGENERGY"
    BIT_DEPTH = "COUNTERDEPTH"
    FILL_MODE = "FILLMODE"
    FLAT_FIELD_FILE = "FLATFIELDFILE"
    VERBOSE = "USEAQUISITIONHEADERS"
    MASK = "S/WMASKIMAGEDATA"
    FRAME_AMOUNT = "NUMFRAMESTOACQUIRE"
    FRAME_TIME = "ACQUISITIONTIME"
    # </editor-fold>

    # <editor-fold desc="Trigger Settings">
    STARTING_TRIGGER = "TRIGGERSTART"
    ENDING_TRIGGER = "TRIGGERSTOP"
    STARTING_TRIGGER_MODIFIER = ""
    FRAME_AMOUNT_PER_PULSE = "NUMFRAMESPERTRIGGER"
    OUT_TRIGGER_TTL = "TriggerOutTTL"
    OUT_TRIGGER_LVDS = "TriggerOutLVDS"
    TTL_INVERSION = "TriggerOutTTLInvert"
    LVDS_INVERSION = "TriggerOutLVDSInvert"
    TTL_DELAY = "TriggerInTTLDelay"
    LVDS_DELAY = "TriggerInLVDSDelay"
    USE_DELAY = "TriggerUseDelay"
    USE_TTL_OUT = "SoftTriggerOutTTL"
    USE_LVDS_OUT = "SoftTriggerOutLVDS"
    USE_TTL_IN = "TriggerInTTL"
    USE_LVDS_IN = "TriggerInLVDS"
    # </editor-fold>

    # <editor-fold desc="Set-Up">
    DAC_FILE = "DACFILE"
    DAC_VALUES = "DACS"
    INPUT_CONFIG = "PIXELMATRIXLOADFILE"
    OUTPUT_CONFIG = "PIXELMATRIXSAVEFILE"
    TRIM_MODE = "SELECTTRIM"
    TRIM_VALUE = "ADJUSTTRIM"
    CHIP_MODE = "SELECTCHIPS"
    TRACK_DAC = "TRACKVFBK"
    # </editor-fold>

    # <editor-fold desc="Threshold Scan">
    USE_THRESHOLD = "THSCAN"
    THRESHOLD_START = "THSTART"
    THRESHOLD_STOP = "THSTOP"
    THRESHOLD_STEP = "THSTEP"
    THRESHOLD_STEPS = "THNUMSTEPS"
    # </editor-fold>

    # <editor-fold desc="DAC Scan">
    USE_DAC = "DACSCANDAC"
    DAC_START = "DACSCANSTART"
    DAC_STOP = "DACSCANSTOP"
    DAC_STEP = "DACSCANSTEP"
    # </editor-fold>

    # <editor-fold desc="File Control">
    PATH = "FILEDIRECTORY/FILEPATH"
    DO_SAVE = "FILEENABLE"
    SAVE_ALL_TO_ONE = "SAVEALLTOFILE"
    IMAGES_PER_FILE = "IMAGESPERFILE"
    TIMESTAMP = "USETIMESTAMPING"
    # </editor-fold>

    # <editor-fold desc="STEM control">
    HORIZONTAL_POINTS = "SCANX"
    VERTICAL_POINTS = "SCANY"
    TRIGGER_MODE = "SCANTRIGGERMODE"
    TRIGGER_COUNT = "SCANTRIGGERFRAMECOUNT"
    LINE_SKIP = "SCANLINESKIP"
    START_SKIP = "SCANSTARTSKIP"
    END_SKIP = "SCANENDSKIP"
    ENABLED_DETECTORS = "SCANDETECTOR<>ENABLE"
    DETECTOR_TYPE = "SCANDETECTOR<>TYPE"
    DETECTOR_MIDDLE_H = "SCANDETECTOR<>CENTREX"
    DETECTOR_MIDDLE_V = "SCANDETECTOR<>CENTREY"
    DETECTOR_OUTER_R = "SCANDETECTOR<>OUTERRADIUS"
    DETECTOR_INNER_R = "SCANDETECTOR<>INNERRADIUS"
    # </editor-fold>

    # <editor-fold desc="Status Reads">
    STATUS = "DETECTORSTATUS"
    TEMP = "TEMPERATURE"
    CHIP_TEMP = "CHIPTEMPS"
    # </editor-fold>


class DetectorStatus(_enum.Enum):
    """
    Enumeration to represent the different status codes a detector can be in.

    :cvar IDLE:
    :cvar BUSY:
    :cvar STANDBY:
    :cvar ERROR:
    :cvar ARMED:
    :cvar INITIALISING:
    """
    IDLE = 0
    BUSY = 1
    STANDBY = 2
    ERROR = 3
    ARMED = 4
    INITIALISING = 5


class DetectorType(_enum.Enum):
    """
    Enumeration to represent the different types of STEM detectors.

    :cvar STANDARD:
    :cvar DPC:
    :cvar COM: Centre Of Mass
    """
    STANDARD = 0
    DPC = 1
    COM = 2


class STEMDetector(_enum.Flag):
    """
    Enumeration to represent the different STEM detectors that can be enabled. They can be combined with |.

    :cvar ONE:
    :cvar TWO:
    """
    ONE = _enum.auto()
    TWO = _enum.auto()


class STEMTrigger(_enum.Enum):
    """
    Enumeration to represent the different types of STEM triggers.

    :cvar PIXEL:
    :cvar LINE:
    :cvar CUSTOM: This is the only mode that allows changing the TRIGGER_COUNT variable.
    """
    PIXEL = 0
    LINE = 1
    CUSTOM = 2


class Chips(_enum.Flag):
    """
    Enumeration to represent the different chips that can be selected for processing. Can be combined with |.

    :cvar ONE:
    :cvar TWO:
    :cvar THREE:
    :cvar FOUR:
    """
    ONE = _enum.auto()
    TWO = _enum.auto()
    THREE = _enum.auto()
    FOUR = _enum.auto()


class OutTrigger(_enum.Enum):
    """
    Enumeration to represent the different types of "out triggers" that can be selected.

    These are controlled by OUT_TRIGGER_TTL and OUT_TRIGGER_LVDS.

    :cvar TTL:
    :cvar LVDS:
    :cvar TTL_DELAYED:
    :cvar LVDS_DELAYED:
    :cvar FOLLOW_SHUTTER:
    :cvar ONE_PER_BURST:
    :cvar SHUTTER_AND_SENSOR:
    :cvar BUSY:
    :cvar SOFT:
    :cvar CLOCK:
    :cvar FRAME:
    """
    TTL = 0
    LVDS = 1
    TTL_DELAYED = 2
    LVDS_DELAYED = 3
    FOLLOW_SHUTTER = 4
    ONE_PER_BURST = 5
    SHUTTER_AND_SENSOR = 6
    BUSY = 7
    SOFT = 8
    CLOCK = 9
    FRAME = 10


class Trigger(_enum.Enum):
    """
    Enumeration to represent the different starting and stopping triggers.

    :cvar INTERNAL:
    :cvar RISING_TTL:
    :cvar FALLING_TTL:
    :cvar RISING_LVDS:
    :cvar FALLING_LVDS:
    :cvar SOFT:
    """
    INTERNAL = 0
    RISING_TTL = 1
    FALLING_TTL = 2
    RISING_LVDS = 3
    FALLING_LVDS = 4
    SOFT = 5


class TriggerModifier(_enum.Enum):
    """
    Enumeration to represent modifiers that can affect a starting trigger.

    :cvar SINGLE:
    :cvar MULTI:
    """
    SINGLE = _enum.auto()
    MULTI = _enum.auto()


class GapFill(_enum.Enum):
    """
    Enumeration to represent different ways filling gaps.

    :cvar NONE:
    :cvar ZERO:
    :cvar DISTRIBUTE:
    :cvar INTERPOLATE:
    """
    NONE = 0
    ZERO = 1
    DISTRIBUTE = 2
    INTERPOLATE = 3


class Counters(_enum.Flag):
    """
    Enumeration to represent the different counters that can be activated. They can be combined with |.

    :cvar ZERO:
    :cvar ONE:
    """
    ZERO = _enum.auto()
    ONE = _enum.auto()


class GainType(_enum.Enum):
    """
    Enumeration to represent the different levels of gain.

    :cvar SUPER_LOW:
    :cvar LOW:
    :cvar HIGH:
    :cvar SUPER_HIGH:
    """
    SUPER_LOW = 0
    LOW = 1
    HIGH = 2
    SUPER_HIGH = 3
