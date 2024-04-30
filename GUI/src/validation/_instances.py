"""
Defines concrete instances of the pipelines.

Attributes
----------
any_str: Pipeline[Any, str]
    Converts its input to a string.
any_float: Pipeline[Any, float]
    Converts its input to a float.
any_int: Pipeline[Any, int]
    Converts its input to a float, checks it's a valid integer (has no decimal component), then converts it to an int.
any_bool: Pipeline[Any, bool]
    Converts its input to a string, checks it's a correct boolean (true or false), then converts it to a bool.
kernel: Pipeline[Any, int]
    Checks for an odd integer that is between 1 and 15.
sigma: Pipeline[Any, int]
    Checks for an integer between -15 and 15.
morph: Pipeline[Any, int]
    Checks for an integer between 1 and 15.
epsilon: Pipeline[Any, float]
    Checks for a float between 0.1 and 30.1
minimum_samples: Pipeline[Any, int]
    Checks for an integer in percentage range (0-100), that is also higher than 0.
power: Pipeline[Any, int]
    Checks for an integer being between 3 and 15.
size: Pipeline[Any, int]
    Checks for an integer between 1 and 20.
match: Pipeline[Any, int]
    Checks for a float in percentage range (0-1).
overlap: Pipeline[Any, int]
    Checks for a float in percentage range (0-1) excluding the endpoints, then checks for a multiple of 0.05.
    This makes sure the percentage can never be 0% or 100%, and is always a multiple of 5%.
pad: Pipeline[Any, int]
    Checks for an integer between -1 and 20.
coverage: Pipeline[Any, float]
    Checks for a float in percentage range, excluding 0.
natural_int: Pipeline[Any, int]
    Checks for any integer that is larger than 0.
natural_float: Pipeline[Any, int]
    Checks for any decimal that is larger than 0.
positive_float: Pipeline[Any, float]
    Checks for any decimal that is larger than or equal to 0.
seed: Pipeline[Any, str]
    Converts a positive integer to a decimal.
save_path: Pipeline[Any, str]
    Checks for a string that starts and ends with a speech mark.
    Then checks that all contents of the string is alphanumeric, or in the following set: {"_", "/", ".", "-", ":"}
file_path: Pipeline[Any, str]
    Checks for a string that starts and ends with a percentage sign.
int12: Pipeline[Any, int]
    Checks for an integer larger than -1 that can fit into a 12-bit binary number.
int16: Pipeline[Any, int]
    Checks for an integer larger than -1 that can fit into a 16-bit binary number.
apt_size: Pipeline[Any, int]
    Checks for an integer between 0 and 4.
obj_focus: Pipeline[Any, int]
    Checks for an integer with an absolute value between 1 and 50.
stage_pos: Pipeline[Any, int]
    Checks for an integer with an absolute value less than or equal to 100 thousand (10 ^ 5)
stage_tilt: Pipeline[Any, int]
    Checks for an integer with an absolute value less than or equal to 90
focus: Pipeline[Any, int]
    Checks for an integer between 2 and 30.
emission: Pipeline[Any, float]
    Checks for a float between 0.1 and 5.1.
"""
import typing

from ._guards import *
from ._mixins import *
from ._morphs import *
from ._pipeline import *

any_str: Pipeline[typing.Any, str] = Pipeline(
    Step.type(str, "convert any value to a string"),
    in_type=typing.Any, out_type=str
)
any_float: Pipeline[typing.Any, float] = Pipeline(
    Step.type(float, "convert any value to a float"),
    in_type=typing.Any, out_type=float
)
any_int: Pipeline[typing.Any, int] = Pipeline(
    Step(IntegerValidator(), TypeTranslator(float),
         desc="convert any value to a float but ensure it's equivalent to an integer"),
    Step.morph(TypeTranslator(int), "convert the float value to an integer"),
    in_type=typing.Any, out_type=int
)
any_bool = any_str + Pipeline(
    Step(ContainerValidator("True", "False", "true", "false"), desc="ensure the string is a valid boolean"),
    Step.morph(BoolTranslator(), "convert the string to a boolean"),
    in_type=str, out_type=bool
)

colours = any_int + Pipeline(
    Step(RangeValidator.known((2, 255)), desc="ensure the integer is between 2 and 255"),
    in_type=int, out_type=int
)

kernel = any_int + Pipeline(
    Step(RangeValidator.known((1, 15)), desc="ensure the integer is between 1 and 15"),
    Step(VInverseMixin(FactorValidator(2)), desc="ensure the integer is even"),
    in_type=int, out_type=int
)
sigma = any_int + Pipeline(
    Step(RangeValidator.known((-15, 15)), desc="ensure the integer is between -15 and 15"),
    in_type=int, out_type=int
)
morph = any_int + Pipeline(
    Step(RangeValidator.known((0, 15), l_bound=False), desc="ensure the integer is between 1 and 15"),
    in_type=int, out_type=int
)

epsilon = any_float + Pipeline(
    Step(RangeValidator.known((0.1, 30.1)), desc="ensure the float is between 0.1 and 30.1"),
    in_type=float, out_type=float
)
minimum_samples = any_int + Pipeline(
    Step(RangeValidator.known((1, 100)), desc="ensure the integer is between 1 and 100"),
    in_type=int, out_type=int
)
power = any_int + Pipeline(
    Step(RangeValidator.known((3, 15)), desc="ensure the integer is between 3 and 15"),
    in_type=int, out_type=int
)
size = any_int + Pipeline(
    Step(RangeValidator.known((1, 50)), desc="ensure the integer is between 1 and 50"),
    in_type=int, out_type=int
)

match = any_float + Pipeline(
    Step(RangeValidator.known((0.0, 1.0)), desc="ensure the float is between 0.0 and 1.0"),
    in_type=float, out_type=float
)
overlap = any_float + Pipeline(
    Step(RangeValidator.known((0.0, 1.0), l_bound=False, u_bound=False),
         desc="ensure the float is between 0.0 and 1.0 (not including either end)"),
    Step(FactorValidator(0.05), desc="ensure the float is a factor of 0.05"),
    in_type=float, out_type=float
)
pad = any_int + Pipeline(
    Step(RangeValidator.known((-1, 20)), desc="ensure the integer is between -1 and 20"),
    in_type=int, out_type=int
)

coverage = any_float + Pipeline(
    Step(RangeValidator.known((0.0, 1.0), l_bound=False), desc="ensure the float is between 0 and 1"),
    in_type=float, out_type=float
)
natural_int = any_int + Pipeline(
    Step(LowerBoundValidator(0, inclusive=False), desc="ensure the integer is larger than 0"),
    in_type=int, out_type=int
)
natural_float = any_float + Pipeline(
    Step(LowerBoundValidator(0, inclusive=False), desc="ensure the float is larger than 0"),
    in_type=float, out_type=float
)
positive_float = any_float + Pipeline(
    Step(LowerBoundValidator(0), desc="ensure the float is positive"),
    in_type=float, out_type=float
)
seed = any_int + Pipeline(
    Step(LowerBoundValidator(0), desc="ensure the integer is positive"),
    Step.type(str, desc="convert the integer to a string"),
    in_type=int, out_type=str
)

save_path = any_str + Pipeline.surround("\'") + Pipeline(
    Step(VIterableMixin(ContainerValidator(*"abcdefghijklmnopqrstuvwxyz", *"ABCDEFGHIJKLMNOPQRSTUVWXYZ", *"0123456789",
                                           "_", "/", ".", "-", ":", "\\")),
         desc="ensure all elements of the string are a valid file path character"),
    in_type=str, out_type=str
)
file_path = any_str + Pipeline.surround("\"")

int12 = any_int + Pipeline.bitstream(12, allow_negative=False)
int16 = any_int + Pipeline.bitstream(16, allow_negative=False)
apt_size = any_int + Pipeline(
    Step(RangeValidator.known((0, 4)), desc="ensure the integer is between 0 and 4"),
    in_type=int, out_type=int
)
obj_focus = any_int + Pipeline(
    Step(RangeValidator.known((-50, 50)), desc="ensure the integer is between -50 and 50"),
    Step(VInverseMixin(ValueValidator(0)), desc="ensure the integer is not 0"),
    in_type=int, out_type=int
)
stage_pos = any_int + Pipeline(
    Step(RangeValidator.known((-100_000, 100_000)), desc="ensure the integer is between -100000 and 100000"),
    in_type=int, out_type=int
)
stage_tilt = any_int + Pipeline(
    Step(RangeValidator.known((-90, 90)), desc="ensure the integer is between -90 and 90"),
    in_type=int, out_type=int
)

dwell_time = any_float + Pipeline(
    Step(RangeValidator.known((40e-9, 70)), desc="ensure the float is between 40 nanoseconds and 70 seconds"),
    in_type=float, out_type=float
)
ttl_input = any_int + Pipeline(
    Step(RangeValidator.known((0, 4)), desc="ensure the integer is between 0 and 4"),
    in_type=int, out_type=int
)
ttl_output = any_int + Pipeline(
    Step(RangeValidator.known((0, 7)), desc="ensure the integer is between 0 and 7"),
    in_type=int, out_type=int
)
ttl_index = any_int + Pipeline(
    Step(RangeValidator.known((0, 9)), desc="ensure the integer is between 0 and 9"),
    in_type=int, out_type=int
)

focus = any_int + Pipeline(
    Step(RangeValidator.known((2, 30)), desc="ensure the integer is between 2 and 30"),
    in_type=int, out_type=int
)
focus_runs = any_int + Pipeline(
    Step(RangeValidator.known((10, 50)), desc="ensure the integer is between 10 and 50"),
    Step(FactorValidator(10), desc="ensure the integer is a multiple of 10"),
    in_type=int, out_type=int
)
focus_bits = any_int + Pipeline(
    Step(RangeValidator.known((1, 16 ** 3)), desc="ensure the integer is between 1 and 4096"),
    in_type=int, out_type=int
)
emission = any_float + Pipeline(
    Step(RangeValidator.known((0.1, 5.1)), desc="ensure the float is between 0.1 and 5.1"),
    in_type=float, out_type=float
)
drift = any_int + Pipeline(
    Step(RangeValidator.known((2, 30)), desc="ensure the integer is between 2 and 30"),
    in_type=int, out_type=int
)
drift_radius = any_int + Pipeline(
    Step(RangeValidator.known((5, 15)), desc="ensure the integer is between 5 and 15"),
    in_type=int, out_type=int
)
