import enum
import typing

try:
    import typing_extensions
except ModuleNotFoundError:
    typing_extensions = typing

from . import _guards as vs, _morphs as ts

Src = typing.TypeVar("Src")
Dst = typing.TypeVar("Dst")
NDst = typing.TypeVar("NDst")
Enum = typing.TypeVar("Enum", bound=enum.Enum)

ValidationError = vs.Error
TranslationError = ts.Error

__all__ = ["ValidationError", "TranslationError", "Step", "Pipeline"]


class Step(ts.Base[Src, Dst], vs.Base[Dst], typing.Generic[Src, Dst]):
    """
    A class representing a singular step in a processing pipeline.

    It is a validator and a translator.

    Bound Generics
    --------------
    T: Dst

    Attributes
    ----------
    _v: Validator
        The validation for the translated data to undergo.
    _t: Translator
        The translation for the input data to undergo. (The default is a blank translator).
    _temp: bool
        Whether the translation should be temporary (default is False).
    """

    @property
    def temporary(self) -> bool:
        """
        Public access to the permanent status of the step.

        Returns
        -------
        bool
            Whether the translation is temporary.
        """
        return self._temp

    def __init__(self, validation: vs.Base[Dst], translation: ts.Base[Src, Dst] = ts.Pass[Dst](), *, temporary=False,
                 desc: str = None):
        self._v = validation
        self._t = translation
        self._temp = temporary
        self._description = desc

    def __str__(self) -> str:
        return self._description or repr(self)

    def __repr__(self) -> str:
        temp = " (temporarily) " if self._temp else " "
        return f"v translates to '{self._t}'{temp}then gets tested such that '{self._v}' is true"

    def translate(self, data: Src) -> Dst:
        return self._t.translate(data)

    def validate(self, data: Src):
        self._v.validate(self._t.translate(data))

    @classmethod
    def type(cls, end: typing.Type[Dst], desc: str = None) -> "Step[typing.Any,Dst]":
        """
        Shortcut constructor to create a step that ensures the output is the expected type.

        Parameters
        ----------
        end: Type[Dst]
            The resulting dtype.
        desc: str
            The description string.

        Returns
        -------
        Step[Any, Dst]
            The step created such that any input is translated to the expected type, and then validated to make sure it
            is *strictly* that type.
        """
        return Step(vs.TypeValidator(end, strict=True), ts.TypeTranslator(end), desc=desc)

    @classmethod
    def morph(cls, translation: ts.Base[Src, Dst], desc: str = None) -> "Step[Src,Dst]":
        """
        Shortcut constructor to apply only a translation.

        Parameters
        ----------
        translation: Translator[Src, Dst]
            The translator to apply to the input data.
        desc: str
            The description string.

        Returns
        -------
        Step[Src, Dst]
            The step created using a blank validator and the specified translator.

        Raises
        ------
        TypeError
            If the translator is a blank translator.
        """
        if isinstance(translation, ts.Pass):
            raise TypeError("Cannot have a passing Translator and a passing Validator")
        return Step(vs.Pass[Dst](), translation, desc=desc)


class Pipeline(ts.Base[Src, Dst], vs.Base[Dst], typing.Generic[Src, Dst]):
    """
    A pipeline of steps to apply. Each step is a validator and a translator, as is this class.

    Bound Generics
    --------------
    T: Dst

    Attributes
    ----------
    _pipe: tuple[Step, ...]
        The steps to apply.
    _in: Type[Src]
        The input data dtype.
    _out: Type[Dst]
        The output data dtype.
    """

    @property
    def itype(self) -> typing.Type[Src]:
        """
        Public access to the input type.

        Returns
        -------
        Type[Src]
            The input data dtype.
        """
        return self._in

    @property
    def otype(self) -> typing.Type[Dst]:
        """
        Public access to the output type.

        Returns
        -------
        Type[Dst]
            The output data dtype.
        """
        return self._out

    def __init__(self, *stages: Step, in_type: typing.Type[Src], out_type: typing.Type[Dst]):
        self._pipe = stages
        self._in, self._out = in_type, out_type

    def __iter__(self) -> typing.Iterator[Step]:
        yield from self._pipe

    def __str__(self) -> str:
        mid = "; then ".join(map(str, self._pipe))
        return f"({mid})"

    def __add__(self, other: "Pipeline[Dst,NDst]") -> "Pipeline[Src,NDst]":
        """
        Combines two pipelines together such that the steps of the other pipeline come after the steps from this one.

        This requires the second pipeline having an input type of this pipeline's output type.

        Generics
        --------
        NDst: Any
            The new output data type of the second pipeline.

        Parameters
        ----------
        other: Pipeline[Dst, NDst]
            The other pipeline to add.

        Returns
        -------
        Pipeline[Src, NDst]
            The combined pipeline.

        Raises
        ------
        TypeError
            If the other pipeline's input dtype is not this pipeline's output type.
        """
        if not isinstance(other, Pipeline):
            return NotImplemented
        elif self._out != other.itype:
            raise TypeError(f"Expected other pipeline's source ({other.itype}) to match this pipeline's destination "
                            f"({self._out})")
        return Pipeline(*self, *other, in_type=self._in, out_type=other.otype)

    def translate(self, data: Src) -> Dst:
        for stage in self._pipe:
            if stage.temporary:
                continue
            data = stage.translate(data)
        return data

    def validate(self, data: Src) -> None:
        for stage in self._pipe:
            stage.validate(data)
            if not stage.temporary:
                data = stage.translate(data)

    @classmethod
    def surround(cls, prefix: str) -> "Pipeline[str,str]":
        """
        Shortcut constructor to create a pipeline that guarantees a string is surrounded with the single character.

        Parameters
        ----------
        prefix: str
            The prefix and suffix of the string.

        Returns
        -------
        Pipeline[str, str]
            The pipeline that combines a prefix and suffix pipeline.

        Raises
        ------
        ValueError
            If the prefix is not a single character.

        See Also
        --------
        Pipeline.prefix
        Pipeline.suffix
        """
        if len(prefix) != 1:
            raise ValueError(f"Expected a single character to surround with (got {prefix!r})")
        return cls.prefix(prefix) + cls.suffix(prefix)

    @classmethod
    def prefix(cls, prefix: str) -> "Pipeline[str,str]":
        """
        Shortcut constructor to create a pipeline that guarantees a string starts with a prefix.

        Parameters
        ----------
        prefix: str
            The starting character of the string.

        Returns
        -------
        Pipeline[str, str]
            A pipeline that makes sure its input string starts with the specified character.

        Raises
        ------
        ValueError
            If the prefix is not a single character.
        """
        if len(prefix) != 1:
            raise ValueError(f"Expected a single character prefix (got {prefix!r})")
        return cls(Step(vs.ValueValidator(prefix), ts.KeyTranslator(0, str), temporary=True,
                        desc=f"ensure the input string starts with {prefix!r}"),
                   Step.morph(ts.KeyTranslator(slice(1, None), str), "remove the prefix"),
                   in_type=str, out_type=str)

    @classmethod
    def suffix(cls, suffix: str) -> "Pipeline[str,str]":
        """
        Shortcut constructor to create a pipeline that guarantees a string ends with a suffix.

        Parameters
        ----------
        suffix: str
            The ending character of the string.

        Returns
        -------
        Pipeline[str, str]
            A pipeline that makes sure its input string ends with the specified character.

        Raises
        ------
        ValueError
            If the suffix is not a single character.
        """
        if len(suffix) != 1:
            raise ValueError(f"Expected a single character suffix (got {suffix!r})")
        return cls(Step(vs.ValueValidator(suffix), ts.KeyTranslator(-1, str), temporary=True,
                        desc=f"ensure the input string ends with {suffix!r}"),
                   Step.morph(ts.KeyTranslator(slice(None, -1), str), "remove the suffix"),
                   in_type=str, out_type=str)

    @classmethod
    def bitstream(cls, num_bits: int, *, allow_negative=True) -> "Pipeline[int,int]":
        """
        Shortcut constructor to create a pipeline that checks for an integer being represented by a bitstream.

        Useful for narrowing python's infinite precision ints down to an underlying C type.

        Parameters
        ----------
        num_bits: int
            The size of the bitstream.
        allow_negative: bool
            Whether the expected precision is signed. (default is True)

        Returns
        -------
        Pipeline[int, int]
            A pipeline that narrows the precision of an integer.
        """
        memory = vs.MemoryValidator(num_bits)
        if allow_negative:
            bounds = memory.min, 2 ** (num_bits - 1) - 1
        else:
            bounds = 0, memory.max
        return cls(Step(memory, desc=f"ensure the integer can only fit into {num_bits} bits"),
                   Step(vs.RangeValidator.known(bounds), desc=f"ensure the integer is within the range {bounds}"),
                   in_type=int, out_type=int)

    @classmethod
    def enum(cls, members: typing.Type[Enum]) -> "Pipeline[typing.Any, Enum]":
        """
        Shortcut constructor for creating a pipeline using an enumeration pipeline.

        Generics
        --------
        Enum: enum.Enum
            The enumeration class.

        Parameters
        ----------
        members: Type[Enum]
            The class which holds the members.

        Returns
        -------
        Pipeline[Any, Enum]
            The pipeline that uses an enumeration pipeline to validate data.
        """
        return cls(Step(vs.TypeValidator(members), desc=f"ensure the input is a valid {members}"), in_type=typing.Any,
                   out_type=members)
