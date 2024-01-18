from ._stages import *
from ._translators import *
from ._validators import *
from ._constants import _file_path_chars, _lowers, _uppers, _nums


class Examples:
    # <editor-fold desc="Generics">
    any_str = Pipeline(Step.type(str))
    any_float = Pipeline(Step.type(float))
    any_int = Pipeline.strict_int()
    any_bool = Pipeline(Step.type(str, ContainerValidator.bool()), Step.pure_translator(StrBoolTranslator()))
    two_elem_int = Pipeline.int_iterable(2)
    colour = Pipeline.bound_int(RangeValidator(0, 256, Include.LOW))
    angle = Pipeline.bound_int(RangeValidator(0, 360, Include.LOW))
    checkbox = any_bool + Pipeline(Step.pure_translator(QtCheckState()))
    file_path = Pipeline.prefixed_str("\"") + Pipeline(
        Step(IterableMixinValidator(ContainerValidator(*_file_path_chars, *_lowers, *_uppers, *_nums)))
    )
    # </editor-fold>

    # <editor-fold desc="Cluster variables">
    algorithm = Pipeline(Step.type(str, ContainerValidator("Manhattan", "Euclidean", "Minkowski")))
    power = Pipeline.bound_int(RangeValidator(3, 15))
    overlap = Pipeline.integer_percentage(end=0.5)
    padding = Pipeline.bound_int(RangeValidator(0, 10))
    match = Pipeline.integer_percentage()
    size = two_elem_int + Pipeline(
        Step(IterableMixinValidator(RangeValidator(5, 50)))
    )
    epsilon = Pipeline(Step.type(float, RangeValidator(0.1, 30.1)))
    minimum_samples = Pipeline.bound_int(RangeValidator(1, 100))
    # </editor-fold>

    # <editor-fold desc="Search variables">
    scan_size = Pipeline.bound_int(ContainerValidator(64, 128, 256, 512))
    exposure = any_int + Pipeline(Step(RangeValidator(100, 5000)), Step(FactorValidator(100)))
    bit_depth = Pipeline.bound_int(ContainerValidator(1, 6, 12))
    captures = Pipeline(Step(UniqueValidator()),
                        Step(IterableMixinValidator(ContainerValidator("scan", "threshold", "cluster", "search"))),
                        Step.type(set)
                        )
    save_path = Pipeline.prefixed_str("%") + Pipeline(Step.pure_translator(FStringTranslator("\"{}\"")))
    # </editor-fold>

    # <editor-fold desc="Microscope variables">
    apt_size = Pipeline.bound_int(RangeValidator(0, 4))
    low_int = Pipeline.bound_int(RangeValidator.bitstream(12))
    high_int = Pipeline.bound_int(RangeValidator.bitstream(16))
    magnification = Pipeline.bound_int(ContainerValidator(
        int(20e3), int(25e3), int(30e3), int(40e3), int(50e3), int(60e3), int(80e3), int(100e3), int(120e3), int(150e3),
        int(200e3), int(250e3), int(300e3), int(400e3), int(500e3), int(600e3), int(800e3), int(1e6), int(1.2e6),
        int(1.5e6), int(2e6), int(2.5e6), int(3e6), int(4e6), int(5e6), int(6e6), int(8e6), int(10e6), int(12e6),
        int(15e6), int(20e6), int(25e6), int(30e6), int(40e6), int(50e6), int(60e6), int(80e6), int(100e6), int(120e6),
        int(150e6)
    ))
    low_tuple = two_elem_int + Pipeline(Step(IterableMixinValidator(RangeValidator(*low_int.bounds, low_int.includes))))
    high_tuple = two_elem_int + Pipeline(
        Step(IterableMixinValidator(RangeValidator(*high_int.bounds, high_int.includes)))
    )
    # </editor-fold>

    # <editor-fold desc="Merlin variables">
    threshold = Pipeline(Step.type(float, RangeValidator(0.0, 1000.0, Include.LOW)))
    long_int = Pipeline.bound_int(RangeValidator.bitstream(32))
    delay = long_int + Pipeline(Step(FactorValidator(10)))
    dac = Pipeline.bound_int(RangeValidator.bitstream(9))
    merlin_path = Pipeline(Step.pure_translator(FStringTranslator("\"{}\""))) + file_path
    stem_limit = Pipeline.bound_int(RangeValidator.power(10, 4))
    # </editor-fold>
