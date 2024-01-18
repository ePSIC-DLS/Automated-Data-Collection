import enum as _enum


class ScanMode(_enum.Enum):
    """
    An enumeration to represent the different scan modes

    :cvar FULL:
    :cvar SPOT:
    :cvar AREA:
    """
    FULL = 0
    SPOT = 1
    AREA = 3


class Detector(_enum.Enum):
    """
    An enumeration to represent the detectors on the microscope

    :cvar ADF1:
    :cvar ADF2:
    :cvar BF:
    :cvar ABF:
    """
    ADF1 = 10
    ADF2 = 14
    BF = 11
    ABF = 18


class Wobbler(_enum.Enum):
    """
    An enumeration to represent the wobblers on the microscope.

    :cvar ANODE:
    :cvar HT:
    """
    ANODE = _enum.auto()
    HT = _enum.auto()


class Shift(_enum.Enum):
    """
    An enumeration to represent the types of shifts that a value can take.

    :cvar RELATIVE:
    :cvar ABSOLUTE:
    """
    RELATIVE = _enum.auto()
    ABSOLUTE = _enum.auto()


class Driver(_enum.Enum):
    """
    An enumeration to represent the drivers of the stage.

    :cvar MOTOR:
    :cvar PIEZO:
    """
    MOTOR = 0
    PIEZO = 1


class Axis(_enum.Flag):
    """
    An enumeration to represent the different axes the stage can move in. They can be combined with |.

    :cvar X:
    :cvar Y:
    :cvar Z:
    """
    X = _enum.auto()
    Y = _enum.auto()
    Z = _enum.auto()


class ImagingMode(_enum.Enum):
    """
    An enumeration to represent the different imaging modes the microscope can be in.

    :cvar TEM:
    :cvar STEM:
    """
    TEM = 0
    STEM = 1


class ProbeMode(_enum.Enum):
    """
    An enumeration to represent the different probe modes the microscope can be in.

    :cvar TEM:
    :cvar EDS:
    :cvar NBD:
    :cvar CBD:
    """
    TEM = 0
    EDS = 1
    NBD = 2
    CBD = 3


class TEMFunction(_enum.Enum):
    """
    An enumeration to represent the different functions that can be performed in TEM mode.

    :cvar MAG:
    :cvar MAG2:
    :cvar LOWMAG:
    :cvar SAMAG:
    :cvar DIFF:
    """
    MAG = 0
    MAG2 = 1
    LOWMAG = 2
    SAMAG = 3
    DIFF = 4


class STEMFunction(_enum.Enum):
    """
    An enumeration to represent the different functions that can be performed in STEM mode.

    :cvar ALIGN:
    :cvar SM_LOWMAG:
    :cvar SM_MAG:
    :cvar AMAG:
    :cvar UUDIFF:
    :cvar ROCKING:
    """
    ALIGN = 0
    SM_LOWMAG = 1
    SM_MAG = 2
    AMAG = 3
    UUDIFF = 4
    ROCKING = 5


class Focus(_enum.Enum):
    """
    An enumeration to represent the different focus types to adjust.

    :cvar OBJ:
    :cvar DIFF:
    """
    OBJ = _enum.auto()
    DIFF = _enum.auto()


class ApertureKind(_enum.Enum):
    """
    An enumeration to represent the different groups of apertures.

    :cvar NONE:
    :cvar CLA:
    :cvar OLA:
    :cvar HCA:
    :cvar SAA:
    :cvar ENTA:
    :cvar ED:
    """
    NONE = 0
    CLA = 1
    OLA = 2
    HCA = 3
    SAA = 4
    ENTA = 5
    ED = 6


class Aperture(_enum.Enum):
    """
    An enumeration to represent the different apertures.

    :cvar CL1:
    :cvar CL2:
    :cvar OL:
    :cvar HC:
    :cvar SA:
    :cvar ENT:
    :cvar HX:
    :cvar BF:
    """
    CL1 = 0
    CL2 = 1
    OL = 2
    HC = 3
    SA = 4
    ENT = 5
    HX = 6
    BF = 7


class Lens(_enum.Enum):
    """
    An enumeration to represent the different lenses.

    :cvar CL1:
    :cvar CL2:
    :cvar CL3:
    :cvar CM:
    :cvar OL_COARSE:
    :cvar OL_FINE:
    :cvar OM1:
    :cvar OM2:
    :cvar IL1:
    :cvar IL2:
    :cvar IL3:
    :cvar IL4:
    :cvar PL1:
    :cvar PL2:
    :cvar PL3:
    :cvar FL_COARSE:
    :cvar FL_FINE:
    :cvar FL_RATIO:
    """
    CL1 = 0
    CL2 = 1
    CL3 = 2
    CM = 3
    OL_COARSE = 6
    OL_FINE = 7
    OM1 = 8
    OM2 = 9
    IL1 = 10
    IL2 = 11
    IL3 = 12
    IL4 = 13
    PL1 = 14
    PL2 = 15
    PL3 = 16
    FL_COARSE = 19
    FL_FINE = 20
    FL_RATIO = 21


class Deflector(_enum.Enum):
    """
    An enumeration to represent the different deflectors that can be controlled.

    :cvar GUN1:
    :cvar GUN2:
    :cvar CLA1:
    :cvar CLA2:
    :cvar CMP_S:
    :cvar CMP_T:
    :cvar CMT_A:
    :cvar CLS:
    :cvar ISC1:
    :cvar ISC2:
    :cvar SPA:
    :cvar PLA:
    :cvar OLS:
    :cvar ILS:
    :cvar FLS1:
    :cvar FLS2:
    :cvar FLA1:
    :cvar FLA2:
    :cvar SCAN1:
    :cvar SCAN2:
    :cvar IS_ASID:
    :cvar MAG_ADJUST:
    :cvar ROTATION:
    :cvar CORRECTION:
    :cvar OFFSET:
    """
    GUN1 = 0
    GUN2 = 1
    CLA1 = 2
    CLA2 = 3
    CMP_S = 4
    CMP_T = 5
    CMT_A = 6
    CLS = 7
    ISC1 = 8
    ISC2 = 9
    SPA = 10
    PLA = 11
    OLS = 12
    ILS = 13
    FLS1 = 14
    FLS2 = 15
    FLA1 = 16
    FLA2 = 17
    SCAN1 = 18
    SCAN2 = 19
    IS_ASID = 20
    MAG_ADJUST = 21
    ROTATION = 22
    CORRECTION = 23
    OFFSET = 24


class ProcessStatus(_enum.Enum):
    """
    An enumeration to represent the different stages a process can be in.

    :cvar ERR:
    :cvar IDLE:
    :cvar RUNNING:
    """
    ERR = -1
    IDLE = 0
    RUNNING = 1
